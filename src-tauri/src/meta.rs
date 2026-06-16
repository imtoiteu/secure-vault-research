//! Analysis command segment — the toolkit's **Analysis** module (Metadata Inspect / Sanitize / Compare).
//!
//! A vault-free, session-free peer to [`crate::CommandSurface`] (mirrors [`crate::PlatformSurface`]
//! and [`crate::StegoSurface`]). It wraps the hardened [`sv_meta::ExifTool`] subprocess driver,
//! converts IPC types (plain `String` paths — metadata ops take **no** secret), and projects
//! [`sv_meta::MetaError`] → oracle-safe [`sv_types::ApiError`] (reusing the existing taxonomy; no
//! new code). It touches no vault, holds no session, and is exposed as a **fourth** Tauri managed
//! state, so Secure Vault's command surface is unchanged.
//!
//! ## Fail-closed availability
//! The bundled ExifTool is **BLAKE3-hash-pinned** and resolved at the composition root
//! ([`crate::MetaApp::new`]). If the binary is absent, unpinned in a release build, or fails the
//! pin check, the composition root manages a [`MetaApp::disabled`] surface instead: every operation
//! then returns a fail-closed [`ApiError::Internal`] (the module is simply unavailable) rather than
//! silently running an unverified tool. The rest of the toolkit is unaffected.

use std::path::Path;

use sv_meta::ExifTool;
use sv_types::{ApiError, MetadataDiffReport, MetadataReport, SanitizeReport};

/// The Analysis command surface. Paths are plain `String`s (non-secret); **no method takes a
/// passphrase or a session** — metadata operations move no secret across the boundary.
pub trait MetaSurface {
    /// **Inspect / extract** — structured embedded metadata for an arbitrary file (read-only; works
    /// for every format ExifTool recognizes). Returns the format, MIME type, a total tag count, and
    /// the tags grouped by namespace (EXIF / XMP / IPTC / …).
    fn metadata_inspect(&self, path: String) -> Result<MetadataReport, ApiError>;

    /// **Sanitize / remove** — strip all writable metadata from `input`, writing a **new** file to
    /// `output` (refused if it exists; the input is never modified in place). The report's
    /// `guaranteed` flag is honest per format: `true` for a native rewrite (images, WAV/AVI/MOV/MP4),
    /// `false` for PDF (incremental update — prior metadata stays recoverable). Read-only families
    /// (Office, archives, MP3/FLAC/MKV) are refused with a coded `SV-INVALID-INPUT`, never a false
    /// "sanitized".
    fn metadata_sanitize(&self, input: String, output: String) -> Result<SanitizeReport, ApiError>;

    /// **Compare / diff** — embedded-metadata differences between two files. File-system pseudo-tags
    /// (name/size/timestamps) are excluded so only real metadata differences surface.
    fn metadata_diff(&self, path_a: String, path_b: String)
        -> Result<MetadataDiffReport, ApiError>;
}

/// Concrete Analysis surface over a resolved, hash-pinned [`ExifTool`]. Holds `Some(tool)` when the
/// bundled binary resolved and pinned, or `None` (disabled — fail-closed) otherwise. `ExifTool` is
/// `Send + Sync`, so this is sound as Tauri managed state.
#[derive(Debug, Default)]
pub struct MetaApp {
    tool: Option<ExifTool>,
}

impl MetaApp {
    /// An **enabled** Analysis surface over a resolved (and, in release, pinned) ExifTool.
    #[must_use]
    pub fn new(tool: ExifTool) -> Self {
        Self { tool: Some(tool) }
    }

    /// A **disabled** surface: the bundled ExifTool was absent, unpinned in release, or failed its
    /// pin check. Every operation returns a fail-closed [`ApiError::Internal`] — the module never
    /// runs an unverified tool, and the unverified-tool fact is an operator/config issue, not a user
    /// oracle.
    #[must_use]
    pub fn disabled() -> Self {
        Self { tool: None }
    }

    /// `true` if the bundled ExifTool resolved and the Analysis module is available.
    #[must_use]
    pub fn is_available(&self) -> bool {
        self.tool.is_some()
    }

    /// Borrow the pinned tool, or fail closed with an internal error if the module is disabled.
    fn tool(&self) -> Result<&ExifTool, ApiError> {
        self.tool.as_ref().ok_or(ApiError::Internal)
    }
}

impl MetaSurface for MetaApp {
    fn metadata_inspect(&self, path: String) -> Result<MetadataReport, ApiError> {
        self.tool()?
            .inspect(Path::new(&path))
            .map_err(ApiError::from)
    }

    fn metadata_sanitize(&self, input: String, output: String) -> Result<SanitizeReport, ApiError> {
        self.tool()?
            .sanitize(Path::new(&input), Path::new(&output))
            .map_err(ApiError::from)
    }

    fn metadata_diff(
        &self,
        path_a: String,
        path_b: String,
    ) -> Result<MetadataDiffReport, ApiError> {
        self.tool()?
            .diff(Path::new(&path_a), Path::new(&path_b))
            .map_err(ApiError::from)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;

    fn s(p: &Path) -> String {
        p.to_string_lossy().into_owned()
    }

    // ---- always-on (no exiftool binary needed) --------------------------

    #[test]
    fn disabled_surface_fails_closed_internal() {
        // A disabled module never runs a tool: every op is a fail-closed internal error, the same
        // coded value for every input (no oracle on which file exists / what format it is).
        let app = MetaApp::disabled();
        assert!(!app.is_available());
        assert_eq!(
            app.metadata_inspect("/any/path".into()).unwrap_err(),
            ApiError::Internal
        );
        assert_eq!(
            app.metadata_sanitize("/in".into(), "/out".into())
                .unwrap_err(),
            ApiError::Internal
        );
        assert_eq!(
            app.metadata_diff("/a".into(), "/b".into()).unwrap_err(),
            ApiError::Internal
        );
        assert_eq!(ApiError::Internal.code(), "SV-INTERNAL");
    }

    #[test]
    fn default_is_disabled() {
        assert!(!MetaApp::default().is_available());
    }

    // ---- end-to-end (requires SV_EXIFTOOL_BIN) --------------------------

    fn enabled_app() -> Option<MetaApp> {
        let bin = std::env::var("SV_EXIFTOOL_BIN").ok()?;
        let tool = ExifTool::new_unpinned(PathBuf::from(bin)).ok()?;
        Some(MetaApp::new(tool))
    }

    /// CRC-32 (PNG polynomial) — builds a valid test PNG without extra deps (mirrors sv-meta tests).
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

    /// A valid 1×1 grayscale PNG carrying a `Software` tEXt chunk (removable metadata).
    fn tiny_png_with_software(sw: &str) -> Vec<u8> {
        let mut p = vec![0x89, b'P', b'N', b'G', 0x0D, 0x0A, 0x1A, 0x0A];
        let mut ihdr = Vec::new();
        ihdr.extend_from_slice(&1u32.to_be_bytes());
        ihdr.extend_from_slice(&1u32.to_be_bytes());
        ihdr.extend_from_slice(&[8, 0, 0, 0, 0]);
        png_chunk(&mut p, b"IHDR", &ihdr);
        let mut t = b"Software\0".to_vec();
        t.extend_from_slice(sw.as_bytes());
        png_chunk(&mut p, b"tEXt", &t);
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
    #[ignore = "requires a real ExifTool via SV_EXIFTOOL_BIN; run with --ignored"]
    fn e2e_inspect_sanitize_diff_surface_roundtrip() {
        let Some(app) = enabled_app() else {
            eprintln!("skipping: set SV_EXIFTOOL_BIN to run the meta IPC e2e test");
            return;
        };
        let dir = tempfile::tempdir().unwrap();
        let img = dir.path().join("a.png");
        std::fs::write(&img, tiny_png_with_software("secure-vault-meta-ipc")).unwrap();

        // Inspect over the surface.
        let report = app.metadata_inspect(s(&img)).unwrap();
        assert_eq!(report.format, "PNG");
        assert!(report
            .groups
            .iter()
            .flat_map(|g| &g.tags)
            .any(|t| t.value.contains("secure-vault-meta-ipc")));

        // Sanitize (PNG → guaranteed native strip).
        let cleaned = dir.path().join("a.clean.png");
        let san = app.metadata_sanitize(s(&img), s(&cleaned)).unwrap();
        assert!(san.guaranteed);
        assert!(san.tags_after < san.tags_before);

        // Refuse to overwrite an existing output → coded SV-OUTPUT-EXISTS (no oracle).
        let err = app.metadata_sanitize(s(&img), s(&cleaned)).unwrap_err();
        assert_eq!(err, ApiError::OutputExists);

        // Diff: original vs cleaned → the Software tag is only-in-A.
        let d = app.metadata_diff(s(&img), s(&cleaned)).unwrap();
        assert!(d
            .only_in_a
            .iter()
            .any(|e| e.value.contains("secure-vault-meta-ipc")));

        // Missing input → coded SV-NOT-FOUND.
        let err = app
            .metadata_inspect(s(&dir.path().join("nope.png")))
            .unwrap_err();
        assert_eq!(err, ApiError::NotFound);
    }

    #[test]
    #[ignore = "requires a real ExifTool via SV_EXIFTOOL_BIN; run with --ignored"]
    fn e2e_read_only_format_is_refused_invalid_input() {
        let Some(app) = enabled_app() else {
            eprintln!("skipping: SV_EXIFTOOL_BIN not set");
            return;
        };
        let dir = tempfile::tempdir().unwrap();
        let zip = dir.path().join("x.zip");
        let mut bytes = b"PK\x03\x04".to_vec();
        bytes.extend_from_slice(&[0u8; 26]);
        std::fs::write(&zip, &bytes).unwrap();
        let out = dir.path().join("x.clean.zip");
        let err = app.metadata_sanitize(s(&zip), s(&out)).unwrap_err();
        assert_eq!(err.code(), "SV-INVALID-INPUT");
        assert!(!out.exists());
    }
}
