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
