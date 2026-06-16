//! # sv-platform — vault-free crypto-services layer
//!
//! Stateless, file-level cryptographic operations over the shared [`sv_crypto`] primitives,
//! independent of Secure Vault. This is the home the toolkit's **Integrity** and **Cryptography**
//! modules consume (and, in a later phase, Secure Vault becomes a consumer too).
//!
//! | Capability | Method | Primitive |
//! |------------|--------|-----------|
//! | Hash File | [`PlatformCrypto::hash_file`] | BLAKE3 (streaming) |
//! | Verify Signature | [`PlatformCrypto::verify_signature`] | minisign / Ed25519 |
//! | Encrypt File | [`PlatformCrypto::encrypt_file`] | Argon2id + secretbox |
//! | Decrypt File | [`PlatformCrypto::decrypt_file`] | Argon2id + secretbox |
//! | Sign File | [`PlatformCrypto::generate_signing_keypair`] + [`PlatformCrypto::sign_file`] | minisign + Argon2id + secretbox |
//! | Split / Recover Secret | [`PlatformCrypto::split_secret`] / [`PlatformCrypto::split_file`] / [`PlatformCrypto::recover_secret`] | Shamir(`sss`) over a DEK + secretbox |
//!
//! Design: thin functions over per-concern adapters — no "engine" abstraction (audit R7). The
//! adapters are zero-sized unit structs, so [`PlatformCrypto`] needs no backend injection (unlike
//! the vault, which injects an `age` subprocess). Passphrase-based encryption keeps everything
//! pure-Rust + libsodium FFI; no external binary is involved.

#![forbid(unsafe_code)]

mod artifact;
mod crypto;
mod error;
mod integrity;
mod sharing;

pub use error::PlatformError;
pub use sharing::{decode_share_string, encode_share_string, RecoverOutput, ShareSplitOutput};

use std::io::Write;
use std::path::{Path, PathBuf};

use sv_crypto::{Blake3Hasher, SodiumMinisignSigner};
use sv_crypto_traits::Ed25519PublicKey;

/// In-memory size ceiling for whole-file operations (encrypt/decrypt/sign-input/verify-input).
/// secretbox is one-shot and the pipeline buffers in RAM, so refuse oversized inputs rather than
/// risk OOM (audit R5). Hashing streams and is **not** bound by this. Mirrors the vault's 2 GiB cap.
pub const MAX_PLAINTEXT_BYTES: u64 = 2 * 1024 * 1024 * 1024;

/// MAGIC for the passphrase-encrypted file artifact (Encrypt/Decrypt File).
const SVENC_MAGIC: [u8; 6] = *b"SVENC\0";
/// MAGIC for the passphrase-wrapped signing key at rest (Sign File).
const SVKEY_MAGIC: [u8; 6] = *b"SVKEY\0";

/// Result of a signature verification: the boolean outcome plus the file's BLAKE3 (informative).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SignatureCheck {
    /// The detached signature verified against the public key.
    pub valid: bool,
    /// Lowercase hex BLAKE3 of the verified file (shown for transparency).
    pub file_blake3_hex: String,
}

/// Outcome of [`PlatformCrypto::verify_integrity`] — a generic file check composing Hash File and
/// Verify Signature. Each half is opt-in; a half that was not requested is `*_checked: false` and its
/// result `false`. A mismatch / invalid signature is a `false` verdict (not an error). Engine-side
/// type; the IPC surface projects it onto `sv_types::VerifyIntegrityReport` (mirrors
/// [`SignatureCheck`] → `sv_types::IntegrityReport`).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct IntegrityVerification {
    /// An expected hash was supplied and compared.
    pub hash_checked: bool,
    /// The computed BLAKE3 equalled the supplied expected hash.
    pub hash_matched: bool,
    /// A signature + public key were supplied and verified.
    pub signature_checked: bool,
    /// The detached signature verified against the public key.
    pub signature_valid: bool,
    /// Lowercase hex BLAKE3 of the file (always computed).
    pub computed_hash_hex: String,
    /// Every requested check passed (and at least one was requested).
    pub verified: bool,
}

/// Paths + public key produced by [`PlatformCrypto::generate_signing_keypair`]. **No secret**:
/// the secret key is written, encrypted at rest, to `secret_key_path`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PlatformKeypair {
    pub public_key_path: String,
    pub secret_key_path: String,
    /// Lowercase hex of the Ed25519 public key (what [`PlatformCrypto::verify_signature`] parses).
    pub public_key_hex: String,
}

/// The file-level crypto services. Holds the (zero-sized) primitive adapters.
#[derive(Debug)]
pub struct PlatformCrypto {
    hasher: Blake3Hasher,
    signer: SodiumMinisignSigner,
}

impl PlatformCrypto {
    /// Construct the services. No I/O, no binary resolution — the adapters are unit structs.
    #[must_use]
    pub fn new() -> Self {
        Self {
            hasher: Blake3Hasher,
            signer: SodiumMinisignSigner,
        }
    }

    /// **Copy a file** to a new path, refusing to overwrite an existing destination. A non-crypto
    /// convenience: the UI uses it to save a just-recovered file under its restored *original* name
    /// (the recovered bytes were already written to a user-chosen path; this duplicates them under
    /// the correct name/extension). Returns the destination path string.
    pub fn copy_file(&self, from: &Path, to: &Path) -> Result<String, PlatformError> {
        refuse_existing(to)?;
        let meta = std::fs::metadata(from).map_err(map_io)?;
        if meta.len() > MAX_PLAINTEXT_BYTES {
            return Err(PlatformError::TooLarge {
                limit_bytes: MAX_PLAINTEXT_BYTES,
                actual_bytes: meta.len(),
            });
        }
        std::fs::copy(from, to).map_err(map_io)?;
        Ok(path_str(to))
    }
}

impl Default for PlatformCrypto {
    fn default() -> Self {
        Self::new()
    }
}

// ===========================================================================
// Shared file helpers (pub(crate) — used by the integrity/crypto modules)
// ===========================================================================

/// Read a file fully, refusing inputs larger than `limit` (size guard before the read).
pub(crate) fn read_capped(path: &Path, limit: u64) -> Result<Vec<u8>, PlatformError> {
    let meta = std::fs::metadata(path).map_err(map_io)?;
    if meta.len() > limit {
        return Err(PlatformError::TooLarge {
            limit_bytes: limit,
            actual_bytes: meta.len(),
        });
    }
    std::fs::read(path).map_err(map_io)
}

/// Refuse to overwrite an existing output (data-safety).
pub(crate) fn refuse_existing(path: &Path) -> Result<(), PlatformError> {
    if path.exists() {
        return Err(PlatformError::OutputExists);
    }
    Ok(())
}

/// Atomic write: same-directory temp file → fsync → rename (reuses the P13 pattern).
pub(crate) fn write_atomic(path: &Path, bytes: &[u8]) -> Result<(), PlatformError> {
    let dir = path.parent().filter(|p| !p.as_os_str().is_empty());
    let mut tmp = match dir {
        Some(dir) => tempfile::NamedTempFile::new_in(dir),
        None => tempfile::NamedTempFile::new_in("."),
    }
    .map_err(|e| PlatformError::Io(e.to_string()))?;
    tmp.write_all(bytes)
        .map_err(|e| PlatformError::Io(e.to_string()))?;
    tmp.as_file()
        .sync_all()
        .map_err(|e| PlatformError::Io(e.to_string()))?;
    tmp.persist(path)
        .map_err(|e| PlatformError::Io(e.error.to_string()))?;
    Ok(())
}

/// Disambiguate `target` so an existing file is **never overwritten**: returns `target` if it's
/// free, else `<stem> (2).<ext>`, `<stem> (3).<ext>`, … (common desktop "save" behaviour). Errors as
/// [`PlatformError::OutputExists`] only in the absurd case that thousands of variants all exist.
pub(crate) fn unique_path(target: PathBuf) -> Result<PathBuf, PlatformError> {
    if !target.exists() {
        return Ok(target);
    }
    let parent = target.parent();
    let stem = target
        .file_stem()
        .map_or_else(String::new, |s| s.to_string_lossy().into_owned());
    let ext = target.extension().map(|e| e.to_string_lossy().into_owned());
    for n in 2..=9999u32 {
        let fname = match &ext {
            Some(e) => format!("{stem} ({n}).{e}"),
            None => format!("{stem} ({n})"),
        };
        let candidate = match parent {
            Some(p) if !p.as_os_str().is_empty() => p.join(&fname),
            _ => PathBuf::from(&fname),
        };
        if !candidate.exists() {
            return Ok(candidate);
        }
    }
    Err(PlatformError::OutputExists)
}

/// Map an I/O error, distinguishing a missing file (`NotFound`) from other failures.
pub(crate) fn map_io(e: std::io::Error) -> PlatformError {
    match e.kind() {
        std::io::ErrorKind::NotFound => PlatformError::NotFound,
        _ => PlatformError::Io(e.to_string()),
    }
}

/// Parse a 64-char hex Ed25519 public key (the form written by `generate_signing_keypair`).
pub(crate) fn parse_pubkey_hex(text: &str) -> Result<Ed25519PublicKey, PlatformError> {
    let bytes = hex::decode(text.trim())
        .map_err(|_| PlatformError::InvalidInput("public key must be hex".into()))?;
    let arr: [u8; 32] = bytes
        .as_slice()
        .try_into()
        .map_err(|_| PlatformError::InvalidInput("public key must be 32 bytes".into()))?;
    Ok(Ed25519PublicKey(arr))
}

/// `path` with `.ext` appended (e.g. `doc.txt` → `doc.txt.minisig`).
pub(crate) fn append_extension(path: &Path, ext: &str) -> PathBuf {
    let mut s = path.as_os_str().to_os_string();
    s.push(".");
    s.push(ext);
    PathBuf::from(s)
}

pub(crate) fn path_str(path: &Path) -> String {
    path.to_string_lossy().into_owned()
}

pub(crate) fn now_unix() -> u64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0)
}
