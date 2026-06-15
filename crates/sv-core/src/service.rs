//! Vault service contract — the internal API that the IPC command surface
//! (`sv-app` / `src-tauri`) wraps 1:1. Implemented across M4–M6.
//!
//! Conventions:
//! - Passphrases arrive as [`SecretBytes`] (the IPC layer wraps the UI's `String`
//!   immediately and zeroizes it) — they are never plain DTO strings.
//! - Methods return `sv-types` DTOs (no secrets) or [`VaultError`].
//! - `session` is an opaque [`SessionHandle`]; the master key lives only in the
//!   service's locked memory, keyed by `session_id`.

use std::path::Path;

use sv_crypto_traits::SecretBytes;
use sv_types::{IntegrityReport, ItemInfo, SessionHandle, ShareExportInfo, SharePolicy, VaultMeta};

use crate::error::VaultError;

/// The full Phase-1 vault capability surface. All methods are part of the frozen M0
/// contract; bodies are implemented in later milestones.
pub trait VaultService {
    // --- lifecycle ---------------------------------------------------------
    /// Create a new vault at `path`, optionally provisioning a recovery policy.
    fn create(
        &self,
        path: &Path,
        passphrase: SecretBytes,
        policy: Option<SharePolicy>,
    ) -> Result<VaultMeta, VaultError>;

    /// Unlock an existing vault, returning a session handle.
    fn unlock(&self, path: &Path, passphrase: SecretBytes) -> Result<SessionHandle, VaultError>;

    /// Lock a session and zeroize its in-memory keys.
    fn lock(&self, session: &SessionHandle) -> Result<(), VaultError>;

    /// Change the passphrase: re-derive MK→KEK/SWK and re-wrap stored secrets only.
    fn change_passphrase(
        &self,
        session: &SessionHandle,
        new_passphrase: SecretBytes,
    ) -> Result<(), VaultError>;

    // --- read-only queries -------------------------------------------------
    /// Non-secret metadata (uuid, format, timestamps, item count, recovery policy, KDF cost)
    /// for the unlocked vault behind `session`. Read-only; mutates nothing.
    fn vault_meta(&self, session: &SessionHandle) -> Result<VaultMeta, VaultError>;

    /// Export the vault's Ed25519 signing **public** key as hex. Non-secret (it lives in the
    /// signed header); lets other parties verify files signed by this vault. Read-only.
    fn export_signing_public_key(&self, session: &SessionHandle) -> Result<String, VaultError>;

    // --- items -------------------------------------------------------------
    fn list_items(&self, session: &SessionHandle) -> Result<Vec<ItemInfo>, VaultError>;

    /// Encrypt `source` into the vault under `name` (capability: Encryption #1).
    fn add_item(
        &self,
        session: &SessionHandle,
        source: &Path,
        name: &str,
    ) -> Result<ItemInfo, VaultError>;

    /// Decrypt an item out to `dest`.
    fn extract_item(
        &self,
        session: &SessionHandle,
        item_id: &str,
        dest: &Path,
    ) -> Result<(), VaultError>;

    // --- integrity & signature (#4, #5) -----------------------------------
    /// Full container integrity + authenticity check (BLAKE3 + minisign).
    fn integrity_check(&self, path: &Path) -> Result<IntegrityReport, VaultError>;

    /// Standalone BLAKE3 of an arbitrary file (hex).
    fn hash_file(&self, path: &Path) -> Result<String, VaultError>;

    /// Sign `path`, writing a minisign-format `.minisig` next to it; returns its path.
    fn sign_file(&self, session: &SessionHandle, path: &Path) -> Result<String, VaultError>;

    /// Verify a detached signature against `public_key_path`.
    fn verify_file(
        &self,
        path: &Path,
        signature_path: &Path,
        public_key_path: &Path,
    ) -> Result<IntegrityReport, VaultError>;

    // --- recovery / secret sharing (#2) -----------------------------------
    /// Split the master key into `shares_total`/`threshold` shares, writing one share
    /// artifact per share into `out_dir`. Shares are never stored in the vault.
    fn split_key(
        &self,
        session: &SessionHandle,
        shares_total: u8,
        threshold: u8,
        out_dir: &Path,
    ) -> Result<Vec<ShareExportInfo>, VaultError>;

    /// Recover access from `>= threshold` share artifacts, returning a session.
    fn recover(&self, path: &Path, share_paths: &[&Path]) -> Result<SessionHandle, VaultError>;
}
