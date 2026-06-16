//! # sv-meta — Analysis module: a hardened ExifTool subprocess
//!
//! Vault-free, session-free **metadata** services over a bundled **ExifTool** CLI, driven as a
//! hardened subprocess in the same spirit as [`sv-age`]'s `age` wrapper:
//! - the binary is **BLAKE3-hash-pinned** ([`ExifTool::new_pinned`]); construction fails if the
//!   on-disk binary does not match the expected hash (release path),
//! - spawned with a **cleared environment**, a **controlled (throwaway) working directory**, **no
//!   shell**, stdin closed, captured stdout/stderr, and a **wall-clock timeout** (fail-closed),
//! - configuration-as-code is **disabled**: every invocation passes `-config ""` as its first two
//!   argv tokens, which turns off ExifTool's executable-Perl config mechanism (the one
//!   attacker-controllable RCE surface; see `metadata/EVALUATION.md` §1.5).
//!
//! Operations (v1): [`ExifTool::inspect`] (read → structured report), [`ExifTool::sanitize`]
//! (strip-all to a **new** file; honest per-format semantics — native strip vs. PDF
//! incremental-update vs. read-only refusal), and [`ExifTool::diff`] (compare two files' embedded
//! metadata). No vault coupling; no secret crosses any boundary; errors are oracle-safe coded
//! [`sv_types::ApiError`]s reusing the existing taxonomy (no new code).

#![forbid(unsafe_code)]

use std::collections::BTreeMap;
use std::ffi::OsString;
use std::io::Read;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::time::Duration;

use serde_json::{Map, Value};
use sv_types::{
    ApiError, MetadataDiffReport, MetadataEntry, MetadataGroup, MetadataReport,
    MetadataValueChange, SanitizeReport,
};

/// Default per-invocation wall-clock limit. ExifTool has no internal timeout, so a hung or malicious
/// input cannot be allowed to block forever (fail-closed). Tune with [`ExifTool::with_timeout`].
const DEFAULT_TIMEOUT: Duration = Duration::from_secs(60);

/// Refuse inputs larger than this before spawning (alloc/DoS guard; ExifTool itself imposes no cap).
pub const MAX_INPUT_BYTES: u64 = 8 * 1024 * 1024 * 1024;

/// ExifTool groups that are *not* embedded metadata (file-system facts, the tool's own version, and
/// derived/composite values). Excluded from sanitize before/after counts and from diffs.
const PSEUDO_GROUPS: &[&str] = &["File", "ExifTool", "Composite", "System"];

/// File types ExifTool **natively rewrites** (a real strip, not an append). Derived from
/// `@writeTypes` (`ExifTool.pm`), restricted to the common image + A/V containers and raw types.
/// Conservative on purpose: a writable type *not* listed degrades to a refusal (fail-closed, never a
/// false "sanitized"). PDF is handled separately ([`SanitizeSupport::Incremental`]).
const NATIVE_STRIP: &[&str] = &[
    "JPEG", "TIFF", "PNG", "GIF", "WEBP", "PSD", "PSB", "MIE", "PPM", "PGM", "PBM", "EPS", "EPSF",
    "PS", "JP2", "JPX", "JXL", "X3F", "FLIF", "MOV", "MP4", "M4A", "M4V", "M4B", "QTIF", "AVI",
    "WAV", "CR2", "CR3", "NEF", "NRW", "ARW", "SR2", "SRF", "ORF", "RAF", "RW2", "PEF", "DNG",
    "CRW", "MRW", "3FR", "IIQ", "RWL", "MOS",
];

/// Failures from driving the ExifTool subprocess (mapped to oracle-safe [`ApiError`] at the boundary).
#[derive(Debug, thiserror::Error)]
pub enum MetaError {
    #[error("exiftool binary not found at {0}")]
    BinaryNotFound(PathBuf),
    #[error("exiftool binary hash mismatch: expected {expected}, got {actual}")]
    HashMismatch { expected: String, actual: String },
    #[error("failed to spawn exiftool: {0}")]
    Spawn(std::io::Error),
    #[error("i/o error talking to exiftool: {0}")]
    Io(String),
    #[error("input file not found")]
    NotFound,
    #[error("output already exists")]
    OutputExists,
    #[error("input too large: {actual} bytes exceeds the {limit}-byte limit")]
    TooLarge { limit: u64, actual: u64 },
    #[error("exiftool did not finish within the time limit")]
    Timeout,
    /// A format this tool will not sanitize (read-only family). Carries a user-facing reason.
    #[error("{0}")]
    Unsupported(String),
    #[error("exiftool failed: {0}")]
    ExifToolFailed(String),
    #[error("could not parse exiftool output: {0}")]
    BadOutput(String),
}

impl From<MetaError> for ApiError {
    fn from(e: MetaError) -> Self {
        match e {
            MetaError::NotFound => ApiError::NotFound,
            MetaError::OutputExists => ApiError::OutputExists,
            MetaError::Timeout => ApiError::Timeout,
            MetaError::TooLarge { limit, actual } => ApiError::TooLarge {
                limit_bytes: limit,
                actual_bytes: actual,
            },
            // A read-only format / explicit refusal is a (non-secret) coded input error.
            MetaError::Unsupported(detail) => ApiError::InvalidInput { detail },
            // ExifTool rejected the file (corrupt / unwritable): a non-secret input fact. The raw
            // stderr is NOT echoed (kept generic) so no internal path/detail leaks.
            MetaError::ExifToolFailed(_) => ApiError::InvalidInput {
                detail: "the metadata tool could not process this file".into(),
            },
            MetaError::Io(_) => ApiError::io_generic(),
            // Operator/config faults (missing or wrong-hash binary, spawn failure, garbled output)
            // are internal — never a user oracle.
            MetaError::BinaryNotFound(_)
            | MetaError::HashMismatch { .. }
            | MetaError::Spawn(_)
            | MetaError::BadOutput(_) => ApiError::Internal,
        }
    }
}

/// Drives a bundled ExifTool binary.
#[derive(Debug, Clone)]
pub struct ExifTool {
    binary: PathBuf,
    timeout: Duration,
}

impl ExifTool {
    /// Construct, verifying the binary's BLAKE3 hash equals `pinned_blake3_hex` (production path).
    pub fn new_pinned(
        binary: impl Into<PathBuf>,
        pinned_blake3_hex: &str,
    ) -> Result<Self, MetaError> {
        let binary = binary.into();
        let actual = binary_blake3_hex(&binary)?;
        if !actual.eq_ignore_ascii_case(pinned_blake3_hex) {
            return Err(MetaError::HashMismatch {
                expected: pinned_blake3_hex.to_ascii_lowercase(),
                actual,
            });
        }
        Ok(Self {
            binary,
            timeout: DEFAULT_TIMEOUT,
        })
    }

    /// Construct without pinning — only for dev (`SV_EXIFTOOL_BIN`) / tests.
    pub fn new_unpinned(binary: impl Into<PathBuf>) -> Result<Self, MetaError> {
        let binary = binary.into();
        if !binary.exists() {
            return Err(MetaError::BinaryNotFound(binary));
        }
        Ok(Self {
            binary,
            timeout: DEFAULT_TIMEOUT,
        })
    }

    /// Override the per-invocation wall-clock timeout.
    #[must_use]
    pub fn with_timeout(mut self, timeout: Duration) -> Self {
        self.timeout = timeout;
        self
    }

    /// **Inspect / extract** — structured metadata for an arbitrary file (read-only; works for every
    /// format ExifTool recognizes).
    pub fn inspect(&self, input: &Path) -> Result<MetadataReport, MetaError> {
        let obj = self.inspect_object(input)?;
        Ok(report_from_object(&obj))
    }

    /// **Sanitize / remove** — strip all writable metadata, writing a **new** file to `output`
    /// (refused if it exists; never in-place). Read-only families are refused; PDF is reported as a
    /// non-guaranteed (incremental) scrub. Returns before/after embedded-tag counts and a
    /// `guaranteed` flag.
    pub fn sanitize(&self, input: &Path, output: &Path) -> Result<SanitizeReport, MetaError> {
        precheck(input)?;
        refuse_existing(output)?;
        let before = self.inspect_object(input)?;
        let format = file_type(&before);
        let support = sanitize_support(&format);
        if matches!(support, SanitizeSupport::ReadOnly) {
            return Err(MetaError::Unsupported(format!(
                "{} files are inspect-only here; their metadata cannot be stripped",
                if format.is_empty() { "these" } else { &format }
            )));
        }
        // exiftool -config "" -all= -o OUTPUT INPUT  (writes a new file; never touches the input).
        self.run(&[
            os("-config"),
            os(""),
            os("-all="),
            os("-o"),
            output.as_os_str().to_os_string(),
            input.as_os_str().to_os_string(),
        ])?;
        if !output.exists() {
            return Err(MetaError::ExifToolFailed("no output produced".into()));
        }
        let after = self.inspect_object(output)?;
        Ok(SanitizeReport {
            output_path: path_str(output),
            format,
            tags_before: embedded_tag_count(&before),
            tags_after: embedded_tag_count(&after),
            guaranteed: matches!(support, SanitizeSupport::Native),
        })
    }

    /// **Compare / diff** — embedded-metadata differences between two files (file-system pseudo-tags
    /// like name/size/dates are excluded so only real metadata differences show).
    pub fn diff(&self, a: &Path, b: &Path) -> Result<MetadataDiffReport, MetaError> {
        let oa = self.inspect_object(a)?;
        let ob = self.inspect_object(b)?;
        Ok(diff_objects(&oa, &ob))
    }

    /// Run `exiftool -config "" -j -G -struct -fast2 INPUT` and return the parsed first JSON object.
    fn inspect_object(&self, input: &Path) -> Result<Map<String, Value>, MetaError> {
        precheck(input)?;
        let out = self.run(&[
            os("-config"),
            os(""),
            os("-j"),
            os("-G"),
            os("-struct"),
            os("-fast2"),
            input.as_os_str().to_os_string(),
        ])?;
        parse_first_object(&out)
    }

    /// Spawn the binary with `args`, hardened, and return captured stdout. No stdin, cleared env,
    /// throwaway cwd, wall-clock deadline (fail-closed).
    fn run(&self, args: &[OsString]) -> Result<Vec<u8>, MetaError> {
        // A fresh, wrapper-owned working directory: ExifTool searches cwd for a `.ExifTool_config`,
        // so never run in an attacker-influenced directory (belt-and-suspenders to `-config ""`).
        let cwd = tempfile::tempdir().map_err(|e| MetaError::Io(e.to_string()))?;

        let mut command = Command::new(&self.binary);
        command
            .args(args)
            .stdin(Stdio::null())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .current_dir(cwd.path())
            .env_clear();
        // Windows needs SystemRoot/SystemDrive to load system DLLs and TEMP/TMP for scratch; re-add
        // only those (still no PATH, no user/home/PERL* vars). No-op on Unix. Mirrors sv-age (H4).
        #[cfg(windows)]
        for key in ["SystemRoot", "SystemDrive", "TEMP", "TMP"] {
            if let Ok(val) = std::env::var(key) {
                command.env(key, val);
            }
        }

        let mut child = command.spawn().map_err(MetaError::Spawn)?;

        // Drain stdout/stderr on their own threads so neither pipe can fill and deadlock, and so the
        // main thread can enforce the deadline.
        let mut stdout = child.stdout.take().expect("stdout piped");
        let (tx, rx) = std::sync::mpsc::channel();
        let reader = std::thread::spawn(move || {
            let mut out = Vec::new();
            let res = stdout.read_to_end(&mut out);
            let _ = tx.send((res, out));
        });
        let mut stderr = child.stderr.take().expect("stderr piped");
        let stderr_reader = std::thread::spawn(move || {
            let mut err = Vec::new();
            let _ = stderr.read_to_end(&mut err);
            err
        });

        let (read_res, out) = match rx.recv_timeout(self.timeout) {
            Ok(v) => v,
            Err(_) => {
                let _ = child.kill();
                let _ = child.wait();
                // Detach (don't join): a killed process can leave the pipes held briefly.
                drop((reader, stderr_reader));
                return Err(MetaError::Timeout);
            }
        };
        let _ = reader.join();
        let err = stderr_reader.join().unwrap_or_default();
        let status = child.wait().map_err(|e| MetaError::Io(e.to_string()))?;
        read_res.map_err(|e| MetaError::Io(e.to_string()))?;
        drop(cwd); // remove the throwaway working dir now that the child is gone

        if !status.success() {
            return Err(MetaError::ExifToolFailed(
                String::from_utf8_lossy(&err).trim().to_string(),
            ));
        }
        Ok(out)
    }
}

/// Compute the lowercase BLAKE3 hex of a file (binary pinning).
pub fn binary_blake3_hex(path: &Path) -> Result<String, MetaError> {
    let bytes = std::fs::read(path).map_err(|e| match e.kind() {
        std::io::ErrorKind::NotFound => MetaError::BinaryNotFound(path.to_path_buf()),
        _ => MetaError::Io(e.to_string()),
    })?;
    Ok(blake3::hash(&bytes).to_hex().to_string())
}

// --- sanitize-support classification ----------------------------------------

/// How thoroughly ExifTool can remove metadata from a given file type.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SanitizeSupport {
    /// Native in-place rewrite → a real strip (`guaranteed: true`).
    Native,
    /// PDF: incremental update only — the prior metadata remains recoverable (`guaranteed: false`).
    Incremental,
    /// Read-only family (Office, archives, MP3/FLAC, MKV, …) — refuse, never claim a strip.
    ReadOnly,
}

/// Classify a file type (ExifTool `File:FileType`) for sanitization.
#[must_use]
pub fn sanitize_support(file_type: &str) -> SanitizeSupport {
    let ft = file_type.to_ascii_uppercase();
    if ft == "PDF" {
        SanitizeSupport::Incremental
    } else if NATIVE_STRIP.iter().any(|t| *t == ft) {
        SanitizeSupport::Native
    } else {
        SanitizeSupport::ReadOnly
    }
}

// --- JSON → report helpers (unit-tested without the binary) ------------------

fn parse_first_object(bytes: &[u8]) -> Result<Map<String, Value>, MetaError> {
    let v: Value =
        serde_json::from_slice(bytes).map_err(|e| MetaError::BadOutput(e.to_string()))?;
    let obj = v
        .as_array()
        .and_then(|a| a.first())
        .and_then(Value::as_object)
        .ok_or_else(|| MetaError::BadOutput("expected a non-empty JSON array of objects".into()))?;
    Ok(obj.clone())
}

/// `"Group:Tag"` → `("Group", "Tag")`; a key without a group → `("", key)`.
fn split_key(key: &str) -> (String, String) {
    match key.split_once(':') {
        Some((g, t)) => (g.to_string(), t.to_string()),
        None => (String::new(), key.to_string()),
    }
}

/// Render an ExifTool JSON value as a single display string.
fn value_to_string(v: &Value) -> String {
    match v {
        Value::String(s) => s.clone(),
        Value::Bool(b) => b.to_string(),
        Value::Number(n) => n.to_string(),
        Value::Null => String::new(),
        Value::Array(a) => a.iter().map(value_to_string).collect::<Vec<_>>().join(", "),
        Value::Object(_) => v.to_string(),
    }
}

fn report_from_object(obj: &Map<String, Value>) -> MetadataReport {
    let mut order: Vec<String> = Vec::new();
    let mut groups: BTreeMap<String, Vec<MetadataEntry>> = BTreeMap::new();
    let (mut format, mut mime) = (String::new(), String::new());
    let mut tag_count = 0u32;

    for (key, val) in obj {
        if key == "SourceFile" {
            continue;
        }
        let (group, name) = split_key(key);
        let value = value_to_string(val);
        if key == "File:FileType" {
            format = value.clone();
        } else if key == "File:MIMEType" {
            mime = value.clone();
        }
        if !groups.contains_key(&group) {
            order.push(group.clone());
        }
        groups
            .entry(group)
            .or_default()
            .push(MetadataEntry { name, value });
        tag_count += 1;
    }

    let group_list = order
        .into_iter()
        .map(|g| MetadataGroup {
            tags: groups.remove(&g).unwrap_or_default(),
            group: g,
        })
        .collect();
    MetadataReport {
        format,
        mime_type: mime,
        tag_count,
        groups: group_list,
    }
}

fn file_type(obj: &Map<String, Value>) -> String {
    obj.get("File:FileType")
        .map(value_to_string)
        .unwrap_or_default()
}

/// Count embedded metadata tags (exclude file-system/composite/tool pseudo-groups + `SourceFile`).
fn embedded_tag_count(obj: &Map<String, Value>) -> u32 {
    obj.keys().filter(|k| is_embedded(k)).count() as u32
}

fn is_embedded(key: &str) -> bool {
    if key == "SourceFile" {
        return false;
    }
    let (group, _) = split_key(key);
    !PSEUDO_GROUPS.iter().any(|g| *g == group)
}

fn diff_objects(a: &Map<String, Value>, b: &Map<String, Value>) -> MetadataDiffReport {
    // Embedded tags only, normalized to value strings, in deterministic key order.
    let flat = |o: &Map<String, Value>| -> BTreeMap<String, String> {
        o.iter()
            .filter(|(k, _)| is_embedded(k))
            .map(|(k, v)| (k.clone(), value_to_string(v)))
            .collect()
    };
    let (fa, fb) = (flat(a), flat(b));

    let mut only_in_a = Vec::new();
    let mut changed = Vec::new();
    for (k, va) in &fa {
        match fb.get(k) {
            None => only_in_a.push(MetadataEntry {
                name: k.clone(),
                value: va.clone(),
            }),
            Some(vb) if vb != va => changed.push(MetadataValueChange {
                key: k.clone(),
                value_a: va.clone(),
                value_b: vb.clone(),
            }),
            Some(_) => {}
        }
    }
    let only_in_b = fb
        .iter()
        .filter(|(k, _)| !fa.contains_key(*k))
        .map(|(k, v)| MetadataEntry {
            name: k.clone(),
            value: v.clone(),
        })
        .collect();

    MetadataDiffReport {
        only_in_a,
        only_in_b,
        changed,
    }
}

// --- small shared helpers ---------------------------------------------------

fn os(s: &str) -> OsString {
    OsString::from(s)
}

fn path_str(p: &Path) -> String {
    p.to_string_lossy().into_owned()
}

fn refuse_existing(p: &Path) -> Result<(), MetaError> {
    if p.exists() {
        Err(MetaError::OutputExists)
    } else {
        Ok(())
    }
}

fn precheck(input: &Path) -> Result<(), MetaError> {
    let meta = std::fs::metadata(input).map_err(|e| match e.kind() {
        std::io::ErrorKind::NotFound => MetaError::NotFound,
        _ => MetaError::Io(e.to_string()),
    })?;
    if meta.len() > MAX_INPUT_BYTES {
        return Err(MetaError::TooLarge {
            limit: MAX_INPUT_BYTES,
            actual: meta.len(),
        });
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    // ---- always-on (no exiftool binary needed) --------------------------

    #[test]
    fn hash_pin_matches_and_mismatches() {
        let me = std::env::current_exe().unwrap();
        let real = binary_blake3_hex(&me).unwrap();
        assert_eq!(real.len(), 64);
        assert!(ExifTool::new_pinned(&me, &real).is_ok());
        assert!(matches!(
            ExifTool::new_pinned(&me, &"00".repeat(32)),
            Err(MetaError::HashMismatch { .. })
        ));
    }

    #[test]
    fn missing_binary_is_reported() {
        assert!(matches!(
            ExifTool::new_unpinned(PathBuf::from("/no/such/exiftool")),
            Err(MetaError::BinaryNotFound(_))
        ));
    }

    #[cfg(unix)]
    #[test]
    fn run_aborts_a_hanging_binary_at_the_timeout() {
        use std::os::unix::fs::PermissionsExt;
        let dir = tempfile::tempdir().unwrap();
        let script = dir.path().join("hang.sh");
        std::fs::write(&script, b"#!/bin/sh\nsleep 30\n").unwrap();
        std::fs::set_permissions(&script, std::fs::Permissions::from_mode(0o755)).unwrap();
        let tool = ExifTool::new_unpinned(&script)
            .unwrap()
            .with_timeout(Duration::from_millis(200));
        let start = std::time::Instant::now();
        let err = tool.run(&[os("-ver")]).unwrap_err();
        assert!(start.elapsed() < Duration::from_secs(10));
        assert!(matches!(err, MetaError::Timeout));
    }

    #[test]
    fn sanitize_support_is_honest_per_format() {
        assert_eq!(sanitize_support("JPEG"), SanitizeSupport::Native);
        assert_eq!(sanitize_support("png"), SanitizeSupport::Native); // case-insensitive
        assert_eq!(sanitize_support("MOV"), SanitizeSupport::Native);
        assert_eq!(sanitize_support("WAV"), SanitizeSupport::Native);
        assert_eq!(sanitize_support("PDF"), SanitizeSupport::Incremental);
        assert_eq!(sanitize_support("DOCX"), SanitizeSupport::ReadOnly);
        assert_eq!(sanitize_support("ZIP"), SanitizeSupport::ReadOnly);
        assert_eq!(sanitize_support("MP3"), SanitizeSupport::ReadOnly);
        assert_eq!(sanitize_support("MKV"), SanitizeSupport::ReadOnly);
        assert_eq!(sanitize_support(""), SanitizeSupport::ReadOnly);
    }

    fn obj(pairs: &[(&str, &str)]) -> Map<String, Value> {
        pairs
            .iter()
            .map(|(k, v)| (k.to_string(), Value::String(v.to_string())))
            .collect()
    }

    #[test]
    fn report_groups_tags_and_counts_format() {
        let json = br#"[{
            "SourceFile": "x.jpg",
            "ExifTool:ExifToolVersion": 13.59,
            "File:FileType": "JPEG",
            "File:MIMEType": "image/jpeg",
            "EXIF:Make": "Canon",
            "EXIF:Model": "EOS",
            "XMP:Creator": "Alice"
        }]"#;
        let map = parse_first_object(json).unwrap();
        let r = report_from_object(&map);
        assert_eq!(r.format, "JPEG");
        assert_eq!(r.mime_type, "image/jpeg");
        // 6 tags shown (SourceFile excluded): version + 2 File + 2 EXIF + 1 XMP.
        assert_eq!(r.tag_count, 6);
        let exif = r.groups.iter().find(|g| g.group == "EXIF").unwrap();
        assert_eq!(exif.tags.len(), 2);
        // Embedded tags exclude File/ExifTool: EXIF(2) + XMP(1) = 3.
        assert_eq!(embedded_tag_count(&map), 3);
    }

    #[test]
    fn diff_reports_added_removed_and_changed_embedded_tags() {
        // File:* differs (size) but must be ignored; EXIF:Make changed; XMP added; EXIF:Lens removed.
        let a = obj(&[
            ("File:FileSize", "10"),
            ("EXIF:Make", "Canon"),
            ("EXIF:Lens", "50mm"),
        ]);
        let b = obj(&[
            ("File:FileSize", "20"),
            ("EXIF:Make", "Nikon"),
            ("XMP:Creator", "Bob"),
        ]);
        let d = diff_objects(&a, &b);
        assert_eq!(
            d.only_in_a,
            vec![MetadataEntry {
                name: "EXIF:Lens".into(),
                value: "50mm".into()
            }]
        );
        assert_eq!(
            d.only_in_b,
            vec![MetadataEntry {
                name: "XMP:Creator".into(),
                value: "Bob".into()
            }]
        );
        assert_eq!(
            d.changed,
            vec![MetadataValueChange {
                key: "EXIF:Make".into(),
                value_a: "Canon".into(),
                value_b: "Nikon".into(),
            }]
        );
    }

    #[test]
    fn value_to_string_handles_arrays_and_numbers() {
        assert_eq!(value_to_string(&serde_json::json!(["a", "b"])), "a, b");
        assert_eq!(value_to_string(&serde_json::json!(42)), "42");
        assert_eq!(value_to_string(&serde_json::json!("hi")), "hi");
    }

    #[test]
    fn meta_error_maps_to_existing_api_codes() {
        assert_eq!(ApiError::from(MetaError::NotFound), ApiError::NotFound);
        assert_eq!(ApiError::from(MetaError::Timeout), ApiError::Timeout);
        assert_eq!(
            ApiError::from(MetaError::OutputExists),
            ApiError::OutputExists
        );
        assert_eq!(
            ApiError::from(MetaError::Unsupported("ZIP files are inspect-only".into())).code(),
            "SV-INVALID-INPUT"
        );
        assert_eq!(
            ApiError::from(MetaError::ExifToolFailed("boom".into())).code(),
            "SV-INVALID-INPUT"
        );
        assert_eq!(
            ApiError::from(MetaError::Spawn(std::io::Error::other("x"))).code(),
            "SV-INTERNAL"
        );
    }

    // ---- end-to-end (requires SV_EXIFTOOL_BIN) --------------------------

    fn exiftool() -> Option<ExifTool> {
        let bin = std::env::var("SV_EXIFTOOL_BIN").ok()?;
        ExifTool::new_unpinned(PathBuf::from(bin)).ok()
    }

    /// CRC-32 (PNG/zlib polynomial) for building a valid test PNG without extra deps.
    fn crc32(bytes: &[u8]) -> u32 {
        let mut crc = 0xFFFF_FFFFu32;
        for &b in bytes {
            crc ^= u32::from(b);
            for _ in 0..8 {
                crc = if crc & 1 != 0 {
                    (crc >> 1) ^ 0xEDB8_8320
                } else {
                    crc >> 1
                };
            }
        }
        !crc
    }

    fn adler32(data: &[u8]) -> u32 {
        let (mut a, mut b) = (1u32, 0u32);
        for &x in data {
            a = (a + u32::from(x)) % 65521;
            b = (b + a) % 65521;
        }
        (b << 16) | a
    }

    fn png_chunk(out: &mut Vec<u8>, ctype: &[u8; 4], data: &[u8]) {
        out.extend_from_slice(&(data.len() as u32).to_be_bytes());
        out.extend_from_slice(ctype);
        out.extend_from_slice(data);
        let mut crc_in = ctype.to_vec();
        crc_in.extend_from_slice(data);
        out.extend_from_slice(&crc32(&crc_in).to_be_bytes());
    }

    /// A valid 1×1 grayscale PNG, optionally carrying a `Software` tEXt chunk (removable metadata).
    fn tiny_png(software: Option<&str>) -> Vec<u8> {
        let mut p = vec![0x89, b'P', b'N', b'G', 0x0D, 0x0A, 0x1A, 0x0A];
        let mut ihdr = Vec::new();
        ihdr.extend_from_slice(&1u32.to_be_bytes()); // width
        ihdr.extend_from_slice(&1u32.to_be_bytes()); // height
        ihdr.extend_from_slice(&[8, 0, 0, 0, 0]); // bit depth, grayscale, default compression/filter/interlace
        png_chunk(&mut p, b"IHDR", &ihdr);
        if let Some(s) = software {
            let mut t = b"Software\0".to_vec();
            t.extend_from_slice(s.as_bytes());
            png_chunk(&mut p, b"tEXt", &t);
        }
        // IDAT: one stored zlib block over the 1-pixel scanline (filter byte 0 + pixel 0).
        let raw = [0u8, 0u8];
        let mut idat = vec![0x78, 0x01, 0x01];
        let len = raw.len() as u16;
        idat.extend_from_slice(&len.to_le_bytes());
        idat.extend_from_slice(&(!len).to_le_bytes());
        idat.extend_from_slice(&raw);
        idat.extend_from_slice(&adler32(&raw).to_be_bytes());
        png_chunk(&mut p, b"IDAT", &idat);
        png_chunk(&mut p, b"IEND", b"");
        p
    }

    #[test]
    fn e2e_inspect_sanitize_diff_against_real_exiftool() {
        let Some(tool) = exiftool() else {
            eprintln!("skipping: set SV_EXIFTOOL_BIN to run the exiftool e2e tests");
            return;
        };
        let dir = tempfile::tempdir().unwrap();
        let with_meta = dir.path().join("a.png");
        std::fs::write(&with_meta, tiny_png(Some("secure-vault-research"))).unwrap();

        // Inspect: a PNG with a Software tEXt tag.
        let report = tool.inspect(&with_meta).unwrap();
        assert_eq!(report.format, "PNG");
        assert!(report.tag_count > 0);
        assert!(
            report
                .groups
                .iter()
                .flat_map(|g| &g.tags)
                .any(|t| t.value.contains("secure-vault-research")),
            "Software tEXt should be visible in the inspect report"
        );

        // Sanitize (PNG = native strip → guaranteed): the Software tag is removed.
        let cleaned = dir.path().join("a.clean.png");
        let san = tool.sanitize(&with_meta, &cleaned).unwrap();
        assert_eq!(san.format, "PNG");
        assert!(san.guaranteed, "PNG strip must be guaranteed");
        assert!(
            san.tags_after < san.tags_before,
            "embedded tags should drop"
        );
        assert!(cleaned.exists());

        // Refuse to overwrite an existing output.
        assert!(matches!(
            tool.sanitize(&with_meta, &cleaned),
            Err(MetaError::OutputExists)
        ));

        // Diff: original vs cleaned → the Software tag is "only_in_a".
        let d = tool.diff(&with_meta, &cleaned).unwrap();
        assert!(d
            .only_in_a
            .iter()
            .any(|e| e.value.contains("secure-vault-research")));

        // Missing input → NotFound.
        assert!(matches!(
            tool.inspect(&dir.path().join("nope.png")),
            Err(MetaError::NotFound)
        ));
    }

    #[test]
    fn e2e_read_only_format_is_refused() {
        let Some(tool) = exiftool() else {
            eprintln!("skipping: SV_EXIFTOOL_BIN not set");
            return;
        };
        let dir = tempfile::tempdir().unwrap();
        // A minimal ZIP (read-only family): exiftool detects "ZIP" by the PK magic.
        let zip = dir.path().join("x.zip");
        let mut bytes = b"PK\x03\x04".to_vec();
        bytes.extend_from_slice(&[0u8; 26]); // pad a plausible local file header
        std::fs::write(&zip, &bytes).unwrap();
        let out = dir.path().join("x.clean.zip");
        assert!(matches!(
            tool.sanitize(&zip, &out),
            Err(MetaError::Unsupported(_))
        ));
        assert!(
            !out.exists(),
            "must not produce output for a refused format"
        );
    }
}
