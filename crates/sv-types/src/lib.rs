//! # sv-types — public IPC / UI data-transfer objects
//!
//! These types cross the boundary between the Rust core and the UI (Tauri IPC).
//!
//! ## Hard invariant
//! **No secret material ever appears in this crate.** No passphrases, master keys,
//! derived keys, age identities, signing keys, or raw secret share bytes. Anything
//! secret lives behind [`sv-crypto`]'s zeroizing types inside the core process and is
//! never serialized into a DTO. This is asserted by review and by the
//! `no_secret_fields` documentation contract in `docs/M0-CONTRACTS.md`.
//!
//! Salts, public keys, hashes, and KDF *parameters* are NOT secret and may appear here.
//!
//! Status: **M0 frozen contract**. Field semantics are stable; additive evolution only
//! (see `CONTRACT_VERSION`).

#![forbid(unsafe_code)]

use serde::{Deserialize, Serialize};

/// Semantic version of the IPC contract. Bump the major component on any
/// breaking change to a DTO; additive (optional) fields keep the same major.
pub const CONTRACT_VERSION: u32 = 1;

/// Non-secret description of a vault, safe to render in the UI.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct VaultMeta {
    /// Canonical UUID (hyphenated string form).
    pub vault_uuid: String,
    /// On-disk container format version (see `sv_core::format::FORMAT_VERSION`).
    pub format_version: u16,
    pub created_unix: u64,
    pub modified_unix: u64,
    /// Number of items stored in the vault.
    pub item_count: u32,
    /// Recovery policy, if key-splitting has been configured.
    pub share_policy: Option<SharePolicy>,
    /// Non-secret KDF descriptor (algorithm + cost parameters; salt is omitted —
    /// the UI does not need it, and it stays in the header).
    pub kdf: KdfDescriptor,
}

/// Shamir recovery policy (metadata only).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct SharePolicy {
    /// Total shares minted (`n`).
    pub shares_total: u8,
    /// Shares required to recover (`k`).
    pub threshold: u8,
}

/// Non-secret KDF parameters, shown for transparency / auditing.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct KdfDescriptor {
    /// e.g. `"argon2id"`.
    pub algorithm: String,
    pub mem_kib: u32,
    pub time_cost: u32,
    pub parallelism: u32,
}

/// Metadata for one stored item. Never contains plaintext or ciphertext.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ItemInfo {
    /// Stable item identifier (hyphenated UUID string).
    pub item_id: String,
    pub name: String,
    pub size_bytes: u64,
    /// Hex BLAKE3 of the item plaintext, for integrity display.
    pub content_hash_hex: String,
    pub added_unix: u64,
}

/// Version handshake (E1) the UI fetches to confirm compatibility. All fields non-secret.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AppInfo {
    /// Application package version (semver string).
    pub app_version: String,
    /// IPC/DTO contract version (this crate's `CONTRACT_VERSION`).
    pub contract_version: u32,
    /// Highest `.svault` container format version this build can read/write.
    pub max_format_version: u16,
    /// Crypto-suite version this build writes.
    pub suite_version: u8,
}

/// Opaque handle to an unlocked session. Carries **no** key material — the actual
/// master key lives only in the core process's locked memory.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SessionHandle {
    pub session_id: String,
}

/// Outcome of a container integrity + authenticity check.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct IntegrityReport {
    /// BLAKE3 content hash matched.
    pub blake3_ok: bool,
    /// minisign Ed25519 signature verified.
    pub signature_ok: bool,
    pub computed_hash_hex: String,
}

/// Outcome of a generic **Verify Integrity** check over an arbitrary file (Cryptography module).
/// Composes Hash File (BLAKE3) and Verify Signature (minisign) without a vault or session.
///
/// Each check is **opt-in**: a caller may verify a hash, a signature, or both. A check that was not
/// requested has its `*_checked` flag `false` and its result flag `false` — absence is never a pass.
/// Unlike [`IntegrityReport`] (which collapses both halves into one verdict), the two checks are
/// reported independently so the UI can say "hash matched, no signature supplied" and similar.
///
/// Non-secret: only the (public) computed hash and booleans appear. A mismatch / invalid signature
/// is reported here as `verified: false` — it is **not** an error (mirrors Verify Signature, where a
/// failed check is `Ok(valid: false)`).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct VerifyIntegrityReport {
    /// A BLAKE3 hash comparison was requested (an expected hex hash was supplied).
    pub hash_checked: bool,
    /// The computed BLAKE3 matched the supplied expected hash. `false` if unchecked or mismatched.
    pub hash_matched: bool,
    /// A minisign signature verification was requested (a signature + public key were supplied).
    pub signature_checked: bool,
    /// The detached signature verified against the public key. `false` if unchecked or invalid.
    pub signature_valid: bool,
    /// Lowercase hex BLAKE3 of the file (always computed, for transparency/display).
    pub computed_hash_hex: String,
    /// Overall verdict: every requested check passed (and at least one check was requested).
    pub verified: bool,
}

/// One metadata tag (Analysis module). For an inspect report `name` is the tag name within its
/// group; for a diff entry `name` is the full `"Group:Tag"` key. Non-secret display values only.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MetadataEntry {
    pub name: String,
    pub value: String,
}

/// A group of metadata tags (e.g. `EXIF`, `XMP`, `File`) in an inspect report.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MetadataGroup {
    pub group: String,
    pub tags: Vec<MetadataEntry>,
}

/// **Metadata Inspection** result over an arbitrary file (Analysis module). Read-only; structured by
/// group. Carries only the (non-secret) metadata ExifTool extracted — no file contents.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MetadataReport {
    /// Detected file type (ExifTool `File:FileType`, e.g. `"JPEG"`), or empty if unknown.
    pub format: String,
    /// MIME type (`File:MIMEType`), or empty if unknown.
    pub mime_type: String,
    /// Total tags shown (excludes the synthetic `SourceFile`).
    pub tag_count: u32,
    pub groups: Vec<MetadataGroup>,
}

/// **Metadata Sanitization** result. The cleaned file is written to `output_path` (a new file).
///
/// `guaranteed` is the honest scrub verdict: `true` only for formats ExifTool natively rewrites
/// (images + WAV/AVI/MOV/MP4). For PDF it is **`false`** — ExifTool writes an incremental update and
/// the prior metadata remains recoverable. Read-only formats are refused before reaching this report.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SanitizeReport {
    pub output_path: String,
    pub format: String,
    /// Embedded metadata tags before (excludes file-system/composite pseudo-tags).
    pub tags_before: u32,
    /// Embedded metadata tags remaining in the output.
    pub tags_after: u32,
    /// `true` ⇒ a guaranteed strip; `false` ⇒ incremental/best-effort (e.g. PDF) — prior metadata
    /// may remain recoverable. The UI must surface this distinction.
    pub guaranteed: bool,
}

/// One changed tag in a metadata diff: present in both files with different values.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MetadataValueChange {
    /// Full `"Group:Tag"` key.
    pub key: String,
    pub value_a: String,
    pub value_b: String,
}

/// **Metadata Comparison** result between two files — embedded-metadata differences only
/// (file-system pseudo-tags like name/size/dates are excluded).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MetadataDiffReport {
    /// Embedded tags present only in the first file.
    pub only_in_a: Vec<MetadataEntry>,
    /// Embedded tags present only in the second file.
    pub only_in_b: Vec<MetadataEntry>,
    /// Tags present in both with differing values.
    pub changed: Vec<MetadataValueChange>,
}

/// Descriptor returned after exporting a recovery share. The secret share bytes are
/// written to a separate share artifact (file/QR in Phase 2) and are **never** placed
/// in this DTO.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ShareExportInfo {
    pub share_index: u8,
    pub vault_uuid: String,
    pub threshold: u8,
    pub shares_total: u8,
    /// Version of the share-envelope format (frozen at M6; see open question Q7).
    pub envelope_version: u16,
    /// Where the share artifact was written.
    pub output_path: String,
}

/// Result of generating a standalone signing keypair (Cryptography module). **No secret**: the
/// secret key is written to `secret_key_path` encrypted at rest; only paths and the **public**
/// key appear here (the no-secret-in-DTO invariant).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SigningKeypairInfo {
    /// Where the public key (hex Ed25519) was written.
    pub public_key_path: String,
    /// Where the passphrase-encrypted secret key was written.
    pub secret_key_path: String,
    /// The public key as lowercase hex (64 chars), for verification and sharing.
    pub public_key_hex: String,
}

/// Result of splitting a secret/file into recovery pieces (standalone **Secret Sharing** module).
/// The DEK and the input plaintext never appear here.
///
/// **Deliberate exception to no-secret-in-DTO:** for the *text* "Split a secret" workflow,
/// `share_b64` carries each piece as a copy-paste string so the user can distribute it — these
/// **are** secret material (a threshold of them reconstructs the secret) and must never be logged.
/// For the *file* workflow `share_b64` is empty (pieces are distributed as files, not transcribed).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ShareSplitReport {
    /// The single encrypted payload file (non-secret ciphertext; required to recover).
    pub payload_path: String,
    /// The `n` piece files written to disk.
    pub share_paths: Vec<String>,
    /// Per-piece copy-paste Base64 strings (text workflow only; empty for file splitting).
    pub share_b64: Vec<String>,
    /// Lowercase hex of the random group id binding this cohort.
    pub group_id_hex: String,
    pub shares_total: u8,
    pub threshold: u8,
}

/// Result of recovering a secret/file from pieces (**Secret Sharing** module). **No recovered
/// bytes**: the plaintext is written to `output_path`; only the path and byte count appear here.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RecoverReport {
    pub output_path: String,
    pub bytes_written: u64,
}

/// Result of exporting Secret Sharing pieces as QR images (**Secure QR Transfer**). Carries only
/// the written image paths — a QR of a Shamir *piece* is non-secret ciphertext (identical in
/// sensitivity to the piece file/string the module already writes), so no secret enters this DTO.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct QrExportReport {
    /// One QR PNG per piece string, in piece order.
    pub image_paths: Vec<String>,
}

/// Result of embedding an invisible, fragile tamper-evident watermark (**Watermarking** module).
/// The watermark is non-secret; this DTO carries only the output path and grid facts.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct WatermarkEmbedReport {
    /// The new, watermarked image (PNG/BMP; the input is never modified in place).
    pub output_path: String,
    pub width: u32,
    pub height: u32,
    /// Number of `16×16` tamper-check blocks the image was divided into.
    pub blocks: u32,
}

/// Verdict of verifying a fragile watermark. **Deliberately no "Authentic"/"Genuine" variant** — the
/// strongest positive is [`WatermarkVerdict::Intact`] ("unchanged since it was marked *with this key*"),
/// which is tamper-evidence, **not** a proof of origin. [`WatermarkVerdict::NotWatermarked`] covers a
/// clean unmarked image, a wrong key, or a wholly replaced one (indistinguishable, by design).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum WatermarkVerdict {
    /// Every block matched: the image is unchanged since it was watermarked with this key.
    Intact,
    /// Some blocks matched and some did not: the image was altered after watermarking (localized).
    Tampered,
    /// No block matched: not watermarked, wrong key, or wholly replaced.
    NotWatermarked,
}

/// Result of verifying a fragile watermark (**Watermarking** module). Counts are non-secret.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct WatermarkVerifyReport {
    pub verdict: WatermarkVerdict,
    pub total_blocks: u32,
    /// How many `16×16` blocks failed their tamper check (0 when `Intact`; all when `NotWatermarked`).
    pub tampered_blocks: u32,
}

/// Heuristic suspicion level from steganalysis (**Steganography** module). **There is deliberately
/// no `Clean`/`Safe` variant** — the lowest level is [`Suspicion::NotObserved`] ("no hidden data
/// detected *by these tests*"), never a guarantee of absence. The type system enforces that the
/// product cannot assert an image is clean.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Suspicion {
    /// No tested signal was raised. **Not** a clean bill of health.
    NotObserved,
    Low,
    Elevated,
    High,
}

/// One detector's contribution to a steganalysis verdict. Non-secret: scores and descriptions,
/// never payload bytes.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct StegoSignal {
    /// Detector name (e.g. `"appended-data"`, `"chi-square"`, `"rs-analysis"`).
    pub name: String,
    /// Heuristic score in `[0.0, 1.0]`; higher = more suspicious. **Not** a probability of guilt.
    pub score: f32,
    /// Human-readable, non-secret explanation of what the detector observed.
    pub detail: String,
}

/// Outcome of a steganalysis scan (**Steganography** module). Heuristic only — it reports a
/// [`Suspicion`] level and the per-detector [`StegoSignal`]s, and **never** asserts an image is
/// clean. `score`-bearing fields make this non-`Eq`.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct StegoDetectReport {
    pub suspicion: Suspicion,
    pub signals: Vec<StegoSignal>,
    /// Fixed caveat reminding the UI that absence of a signal is not proof of absence.
    pub caveat: String,
}

/// Result of hiding a payload in a cover image (**Steganography** module → *Hide*). **No secret
/// bytes**: the stego image is written to `output_path`; the payload and key never appear here.
/// `utilization_pct` makes this non-`Eq`.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct StegoHideReport {
    /// Where the stego image was written (same container format as the cover).
    pub output_path: String,
    /// Cover container format (`"png"` / `"bmp"`).
    pub cover_format: String,
    /// Size of the hidden payload, in bytes.
    pub payload_bytes: u64,
    /// Maximum payload the cover could hold, in bytes.
    pub capacity_bytes: u64,
    /// `payload_bytes / capacity_bytes`, as a percentage (0.0–100.0).
    pub utilization_pct: f32,
}

/// Result of extracting a payload from a stego image (**Steganography** module → *Extract*). **No
/// recovered bytes**: the plaintext is written to `output_path`; only the path and count appear here.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct StegoExtractReport {
    pub output_path: String,
    pub bytes_written: u64,
}

/// Uniform, **oracle-safe** error surface for the UI (pre-M6 taxonomy, E1/E2/E3). The
/// internal taxonomy (`sv_core::VaultError`) is collapsed here so callers cannot distinguish,
/// e.g., a wrong passphrase from a wrong recovery share — but distinct, **non-secret**
/// conditions (wrong file, incompatible version, too few shares) are surfaced for UX.
///
/// Wire form: `#[serde(tag = "code")]`, so the discriminant **is** the stable machine code
/// (`SV-…`). The UI localizes off the code; structured fields fill message placeholders.
/// Codes are 1:1 with variants — never finer than the oracle-safe merge.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "code")]
pub enum ApiError {
    /// Requested vault/item/session does not exist.
    #[serde(rename = "SV-NOT-FOUND")]
    NotFound,
    /// Structurally not a Secure Vault file (bad magic / parse failure). Non-secret; benign
    /// ("wrong file selected"). Distinct from [`ApiError::Corrupted`] (E2).
    #[serde(rename = "SV-MALFORMED")]
    Malformed,
    /// A real vault, but from an unsupported container format version — actionable
    /// ("update the app"), not corruption (E1). Version numbers are non-secret.
    #[serde(rename = "SV-INCOMPATIBLE-VERSION")]
    IncompatibleVersion { found: u16, supported: u16 },
    /// A real vault whose integrity/signature check failed (damaged or tampered). Merged.
    #[serde(rename = "SV-CORRUPTED")]
    Corrupted,
    /// Authentication failed — wrong passphrase OR incorrect recovery shares of sufficient
    /// count. Deliberately merged to avoid an oracle.
    #[serde(rename = "SV-UNAUTHORIZED")]
    Unauthorized,
    /// Fewer recovery shares supplied than the threshold requires. Counts are non-secret;
    /// surfaced so the UI can say "you need N more shares" (E2). A pre-check, not an attempt.
    #[serde(rename = "SV-INSUFFICIENT-SHARES")]
    InsufficientShares { got: u8, need: u8 },
    /// Caller-supplied input was structurally invalid. `detail` is **non-secret**, for logs.
    #[serde(rename = "SV-INVALID-INPUT")]
    InvalidInput { detail: String },
    /// A file could not be read or written (permission, disk-full, path problem). `detail` is a
    /// fixed, **non-secret** category — never the raw path/message (validation H6).
    #[serde(rename = "SV-IO")]
    Io { detail: String },
    /// The input exceeds the safe size limit; refusing rather than risking an out-of-memory crash
    /// (validation H1). Byte counts are non-secret and let the UI state the limit.
    #[serde(rename = "SV-TOO-LARGE")]
    TooLarge { limit_bytes: u64, actual_bytes: u64 },
    /// A crypto/back-end operation exceeded its time limit (e.g. a very large payload). Actionable,
    /// non-secret — distinct from [`ApiError::Internal`] (validation H1/H6).
    #[serde(rename = "SV-TIMEOUT")]
    Timeout,
    /// An extract/export destination already exists; refused to overwrite it (data-safety, H3).
    #[serde(rename = "SV-OUTPUT-EXISTS")]
    OutputExists,
    /// Unexpected internal failure (redacted).
    #[serde(rename = "SV-INTERNAL")]
    Internal,
}

impl ApiError {
    /// The fixed, **non-secret** detail used whenever a file read/write fails. Centralized so the
    /// `From<VaultError>` and `From<PlatformError>` boundaries stay byte-identical and never leak a
    /// path or raw OS message (validation H6). Both error layers construct `Io` via this.
    #[must_use]
    pub fn io_generic() -> Self {
        ApiError::Io {
            detail:
                "could not read or write a file — check the path, permissions, and free disk space"
                    .into(),
        }
    }

    /// Every machine code [`ApiError::code`] can emit — the complete UI-contract surface the
    /// frontend must localize. Kept exhaustive by the `all_api_error_codes_is_complete` test.
    pub const ALL_CODES: &'static [&'static str] = &[
        "SV-NOT-FOUND",
        "SV-MALFORMED",
        "SV-INCOMPATIBLE-VERSION",
        "SV-CORRUPTED",
        "SV-UNAUTHORIZED",
        "SV-INSUFFICIENT-SHARES",
        "SV-INVALID-INPUT",
        "SV-IO",
        "SV-TOO-LARGE",
        "SV-TIMEOUT",
        "SV-OUTPUT-EXISTS",
        "SV-INTERNAL",
    ];

    /// The stable machine code for this error (matches the serde `code` tag). The UI keys its
    /// localized messages off this; it is part of the IPC contract.
    #[must_use]
    pub fn code(&self) -> &'static str {
        match self {
            ApiError::NotFound => "SV-NOT-FOUND",
            ApiError::Malformed => "SV-MALFORMED",
            ApiError::IncompatibleVersion { .. } => "SV-INCOMPATIBLE-VERSION",
            ApiError::Corrupted => "SV-CORRUPTED",
            ApiError::Unauthorized => "SV-UNAUTHORIZED",
            ApiError::InsufficientShares { .. } => "SV-INSUFFICIENT-SHARES",
            ApiError::InvalidInput { .. } => "SV-INVALID-INPUT",
            ApiError::Io { .. } => "SV-IO",
            ApiError::TooLarge { .. } => "SV-TOO-LARGE",
            ApiError::Timeout => "SV-TIMEOUT",
            ApiError::OutputExists => "SV-OUTPUT-EXISTS",
            ApiError::Internal => "SV-INTERNAL",
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Every DTO must round-trip losslessly through JSON (UI transport) and through
    /// CBOR is covered in sv-core. This is the M0 serde contract gate.
    #[test]
    fn dtos_round_trip_json() {
        let meta = VaultMeta {
            vault_uuid: "00000000-0000-0000-0000-000000000000".into(),
            format_version: 1,
            created_unix: 1,
            modified_unix: 2,
            item_count: 3,
            share_policy: Some(SharePolicy {
                shares_total: 5,
                threshold: 3,
            }),
            kdf: KdfDescriptor {
                algorithm: "argon2id".into(),
                mem_kib: 262_144,
                time_cost: 3,
                parallelism: 1,
            },
        };
        let s = serde_json::to_string(&meta).unwrap();
        assert_eq!(meta, serde_json::from_str(&s).unwrap());

        let err = ApiError::InvalidInput {
            detail: "bad threshold".into(),
        };
        let s = serde_json::to_string(&err).unwrap();
        assert_eq!(err, serde_json::from_str::<ApiError>(&s).unwrap());

        // Verify Integrity report: independent opt-in checks, snake_case fields, round-trips.
        let vi = VerifyIntegrityReport {
            hash_checked: true,
            hash_matched: true,
            signature_checked: true,
            signature_valid: false,
            computed_hash_hex: "ab".repeat(32),
            verified: false,
        };
        let s = serde_json::to_string(&vi).unwrap();
        assert_eq!(
            vi,
            serde_json::from_str::<VerifyIntegrityReport>(&s).unwrap()
        );
        assert!(s.contains("\"hash_matched\"") && s.contains("\"signature_valid\""));

        // Analysis module DTOs: structured, snake_case, round-trip.
        let report = MetadataReport {
            format: "JPEG".into(),
            mime_type: "image/jpeg".into(),
            tag_count: 1,
            groups: vec![MetadataGroup {
                group: "EXIF".into(),
                tags: vec![MetadataEntry {
                    name: "Make".into(),
                    value: "Canon".into(),
                }],
            }],
        };
        let s = serde_json::to_string(&report).unwrap();
        assert_eq!(report, serde_json::from_str(&s).unwrap());

        let san = SanitizeReport {
            output_path: "/tmp/clean.jpg".into(),
            format: "JPEG".into(),
            tags_before: 12,
            tags_after: 0,
            guaranteed: true,
        };
        let s = serde_json::to_string(&san).unwrap();
        assert_eq!(san, serde_json::from_str(&s).unwrap());
        assert!(s.contains("\"guaranteed\""));

        let diff = MetadataDiffReport {
            only_in_a: vec![],
            only_in_b: vec![],
            changed: vec![MetadataValueChange {
                key: "EXIF:Make".into(),
                value_a: "Canon".into(),
                value_b: "Nikon".into(),
            }],
        };
        let s = serde_json::to_string(&diff).unwrap();
        assert_eq!(diff, serde_json::from_str(&s).unwrap());

        // Secure QR Transfer: the export report (paths only) round-trips.
        let qr = QrExportReport {
            image_paths: vec!["/tmp/piece-1.png".into(), "/tmp/piece-2.png".into()],
        };
        let s = serde_json::to_string(&qr).unwrap();
        assert_eq!(qr, serde_json::from_str::<QrExportReport>(&s).unwrap());
        assert!(s.contains("\"image_paths\""));

        // Watermarking: embed + verify reports round-trip; verdict has no "Authentic" variant.
        let wm = WatermarkEmbedReport {
            output_path: "/tmp/marked.png".into(),
            width: 640,
            height: 480,
            blocks: 1200,
        };
        let s = serde_json::to_string(&wm).unwrap();
        assert_eq!(
            wm,
            serde_json::from_str::<WatermarkEmbedReport>(&s).unwrap()
        );

        let wv = WatermarkVerifyReport {
            verdict: WatermarkVerdict::Tampered,
            total_blocks: 1200,
            tampered_blocks: 7,
        };
        let s = serde_json::to_string(&wv).unwrap();
        assert_eq!(
            wv,
            serde_json::from_str::<WatermarkVerifyReport>(&s).unwrap()
        );
        assert!(s.contains("\"Tampered\""));
    }

    #[test]
    fn stego_detect_report_round_trips_and_has_no_clean_variant() {
        let report = StegoDetectReport {
            suspicion: Suspicion::Elevated,
            signals: vec![StegoSignal {
                name: "chi-square".into(),
                score: 0.82,
                detail: "p(embedding)=0.82 over the green channel".into(),
            }],
            caveat: "heuristic — absence of a signal is not proof of absence".into(),
        };
        let s = serde_json::to_string(&report).unwrap();
        assert_eq!(
            report,
            serde_json::from_str::<StegoDetectReport>(&s).unwrap()
        );
        // The wire form of the lowest level is "NotObserved", never "Clean"/"Safe".
        let lowest = serde_json::to_string(&Suspicion::NotObserved).unwrap();
        assert_eq!(lowest, "\"NotObserved\"");
        assert!(!lowest.to_lowercase().contains("clean"));
        assert!(!lowest.to_lowercase().contains("safe"));
    }

    #[test]
    fn all_api_error_codes_is_complete() {
        // One value per variant. `code()` is already an exhaustive match (a new variant fails to
        // compile until given a code); this test additionally pins `ALL_CODES` to the full variant
        // set, so the UI-contract surface the frontend localizes can't silently drift. The desktop
        // crate's `every_api_error_code_has_a_ui_message` test consumes `ALL_CODES`.
        let samples = [
            ApiError::NotFound,
            ApiError::Malformed,
            ApiError::IncompatibleVersion {
                found: 2,
                supported: 1,
            },
            ApiError::Corrupted,
            ApiError::Unauthorized,
            ApiError::InsufficientShares { got: 1, need: 2 },
            ApiError::InvalidInput {
                detail: String::new(),
            },
            ApiError::Io {
                detail: String::new(),
            },
            ApiError::TooLarge {
                limit_bytes: 0,
                actual_bytes: 0,
            },
            ApiError::Timeout,
            ApiError::OutputExists,
            ApiError::Internal,
        ];
        // Distinct codes drawn from the samples == every code in ALL_CODES (set equality).
        let mut sample_codes: Vec<&str> = samples.iter().map(ApiError::code).collect();
        sample_codes.sort_unstable();
        sample_codes.dedup();
        assert_eq!(
            sample_codes.len(),
            ApiError::ALL_CODES.len(),
            "ALL_CODES is out of sync with the ApiError variants"
        );
        for c in &sample_codes {
            assert!(
                ApiError::ALL_CODES.contains(c),
                "{c} missing from ALL_CODES"
            );
        }
        // io_generic() is a real Io and never leaks a path.
        assert_eq!(ApiError::io_generic().code(), "SV-IO");
    }

    #[test]
    fn api_error_wire_code_matches_accessor() {
        // The serialized `code` tag must equal `code()` for every variant (stable contract).
        let cases = [
            (ApiError::NotFound, "SV-NOT-FOUND"),
            (ApiError::Malformed, "SV-MALFORMED"),
            (
                ApiError::IncompatibleVersion {
                    found: 2,
                    supported: 1,
                },
                "SV-INCOMPATIBLE-VERSION",
            ),
            (ApiError::Corrupted, "SV-CORRUPTED"),
            (ApiError::Unauthorized, "SV-UNAUTHORIZED"),
            (
                ApiError::InsufficientShares { got: 2, need: 3 },
                "SV-INSUFFICIENT-SHARES",
            ),
            (ApiError::Io { detail: "x".into() }, "SV-IO"),
            (
                ApiError::TooLarge {
                    limit_bytes: 10,
                    actual_bytes: 20,
                },
                "SV-TOO-LARGE",
            ),
            (ApiError::Timeout, "SV-TIMEOUT"),
            (ApiError::OutputExists, "SV-OUTPUT-EXISTS"),
            (ApiError::Internal, "SV-INTERNAL"),
        ];
        for (err, code) in cases {
            assert_eq!(err.code(), code);
            let json = serde_json::to_value(&err).unwrap();
            assert_eq!(json["code"], code);
            assert_eq!(err, serde_json::from_value(json).unwrap());
        }
        // Structured fields ride alongside the code on the wire.
        let v = serde_json::to_value(ApiError::InsufficientShares { got: 2, need: 3 }).unwrap();
        assert_eq!(v["got"], 2);
        assert_eq!(v["need"], 3);
    }
}
