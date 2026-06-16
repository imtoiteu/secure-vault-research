//! # sv-app — application composition root + IPC command surface (M6)
//!
//! Wires the concrete crypto adapters (`sv-crypto`, `sv-age`) into a [`VaultBackend`]
//! (`sv_core::VaultService`) and exposes them through [`CommandSurface`], the boundary the UI
//! calls. Each method becomes a `#[tauri::command]` once the frontend lands; the trait keeps
//! the surface compiling and fully testable without the Tauri runtime.
//!
//! ## Boundary rules (frozen, `docs/M6-IPC-DECISIONS.md`)
//! - Passphrases arrive as [`IpcPassphrase`] (N1): zeroizing, redacted `Debug`, converted to
//!   `SecretBytes` on the first line of each handler. Never logged, never in a DTO/error.
//! - Every method returns the oracle-safe, **coded** [`sv_types::ApiError`] on failure (the
//!   projection of `sv_core::VaultError`).
//! - No secret crosses this boundary; sessions are opaque [`SessionHandle`]s.

#![forbid(unsafe_code)]

mod meta;
mod passphrase;
mod payload;
mod platform;
mod service;
mod stego;
mod watermark;

pub use meta::{MetaApp, MetaSurface};
pub use passphrase::IpcPassphrase;
pub use payload::{AgePayloadCipher, PayloadCipher};
pub use platform::{PlatformApp, PlatformSurface};
pub use service::VaultBackend;
pub use stego::{StegoApp, StegoSurface};
pub use watermark::{WatermarkApp, WatermarkSurface};

use sv_core::{VaultService, FORMAT_VERSION, SUITE_VERSION};
use sv_types::{
    ApiError, AppInfo, IntegrityReport, ItemInfo, SessionHandle, ShareExportInfo, SharePolicy,
    VaultMeta,
};

/// The IPC contract surface. One method per UI-invokable command. Paths are plain `String`s
/// (non-secret); passphrases are [`IpcPassphrase`] (N1).
pub trait CommandSurface {
    /// Version handshake (E1) — lets the UI detect format/contract incompatibility up front.
    fn app_info(&self) -> AppInfo;

    fn vault_create(
        &self,
        path: String,
        passphrase: IpcPassphrase,
        policy: Option<SharePolicy>,
    ) -> Result<VaultMeta, ApiError>;

    fn vault_unlock(
        &self,
        path: String,
        passphrase: IpcPassphrase,
    ) -> Result<SessionHandle, ApiError>;
    fn vault_lock(&self, session: SessionHandle) -> Result<(), ApiError>;
    fn vault_change_passphrase(
        &self,
        session: SessionHandle,
        new_passphrase: IpcPassphrase,
    ) -> Result<(), ApiError>;

    /// Read-only: non-secret metadata for the unlocked vault behind `session`.
    fn vault_meta(&self, session: SessionHandle) -> Result<VaultMeta, ApiError>;
    /// Read-only: export the vault's Ed25519 signing public key (hex), for verification.
    fn export_signing_public_key(&self, session: SessionHandle) -> Result<String, ApiError>;

    fn item_list(&self, session: SessionHandle) -> Result<Vec<ItemInfo>, ApiError>;
    fn item_add(
        &self,
        session: SessionHandle,
        source: String,
        name: String,
    ) -> Result<ItemInfo, ApiError>;
    fn item_extract(
        &self,
        session: SessionHandle,
        item_id: String,
        dest: String,
    ) -> Result<(), ApiError>;

    fn integrity_check(&self, path: String) -> Result<IntegrityReport, ApiError>;
    fn integrity_hash(&self, path: String) -> Result<String, ApiError>;
    fn sign_file(&self, session: SessionHandle, path: String) -> Result<String, ApiError>;
    fn verify_file(
        &self,
        path: String,
        signature_path: String,
        public_key_path: String,
    ) -> Result<IntegrityReport, ApiError>;

    fn keys_split(
        &self,
        session: SessionHandle,
        shares_total: u8,
        threshold: u8,
        out_dir: String,
    ) -> Result<Vec<ShareExportInfo>, ApiError>;
    fn keys_recover(
        &self,
        path: String,
        share_paths: Vec<String>,
    ) -> Result<SessionHandle, ApiError>;
}

/// The contract version this command surface implements (mirrors the IPC DTO contract).
pub const APP_CONTRACT_VERSION: u32 = sv_types::CONTRACT_VERSION;

/// Concrete command surface over a [`VaultBackend`]. Converts IPC types
/// (`IpcPassphrase`/`String`) to domain types and projects `VaultError` → `ApiError`.
#[derive(Debug)]
pub struct AppVault<P: PayloadCipher> {
    backend: VaultBackend<P>,
}

impl<P: PayloadCipher> AppVault<P> {
    #[must_use]
    pub fn new(backend: VaultBackend<P>) -> Self {
        Self { backend }
    }
}

impl<P: PayloadCipher> CommandSurface for AppVault<P> {
    fn app_info(&self) -> AppInfo {
        AppInfo {
            app_version: env!("CARGO_PKG_VERSION").to_string(),
            contract_version: APP_CONTRACT_VERSION,
            max_format_version: FORMAT_VERSION,
            suite_version: SUITE_VERSION,
        }
    }

    fn vault_create(
        &self,
        path: String,
        passphrase: IpcPassphrase,
        policy: Option<SharePolicy>,
    ) -> Result<VaultMeta, ApiError> {
        self.backend
            .create(path.as_ref(), passphrase.into_secret(), policy)
            .map_err(ApiError::from)
    }

    fn vault_unlock(
        &self,
        path: String,
        passphrase: IpcPassphrase,
    ) -> Result<SessionHandle, ApiError> {
        self.backend
            .unlock(path.as_ref(), passphrase.into_secret())
            .map_err(ApiError::from)
    }

    fn vault_lock(&self, session: SessionHandle) -> Result<(), ApiError> {
        self.backend.lock(&session).map_err(ApiError::from)
    }

    fn vault_change_passphrase(
        &self,
        session: SessionHandle,
        new_passphrase: IpcPassphrase,
    ) -> Result<(), ApiError> {
        self.backend
            .change_passphrase(&session, new_passphrase.into_secret())
            .map_err(ApiError::from)
    }

    fn vault_meta(&self, session: SessionHandle) -> Result<VaultMeta, ApiError> {
        self.backend.vault_meta(&session).map_err(ApiError::from)
    }

    fn export_signing_public_key(&self, session: SessionHandle) -> Result<String, ApiError> {
        self.backend
            .export_signing_public_key(&session)
            .map_err(ApiError::from)
    }

    fn item_list(&self, session: SessionHandle) -> Result<Vec<ItemInfo>, ApiError> {
        self.backend.list_items(&session).map_err(ApiError::from)
    }

    fn item_add(
        &self,
        session: SessionHandle,
        source: String,
        name: String,
    ) -> Result<ItemInfo, ApiError> {
        self.backend
            .add_item(&session, source.as_ref(), &name)
            .map_err(ApiError::from)
    }

    fn item_extract(
        &self,
        session: SessionHandle,
        item_id: String,
        dest: String,
    ) -> Result<(), ApiError> {
        self.backend
            .extract_item(&session, &item_id, dest.as_ref())
            .map_err(ApiError::from)
    }

    fn integrity_check(&self, path: String) -> Result<IntegrityReport, ApiError> {
        self.backend
            .integrity_check(path.as_ref())
            .map_err(ApiError::from)
    }

    fn integrity_hash(&self, path: String) -> Result<String, ApiError> {
        self.backend
            .hash_file(path.as_ref())
            .map_err(ApiError::from)
    }

    fn sign_file(&self, session: SessionHandle, path: String) -> Result<String, ApiError> {
        self.backend
            .sign_file(&session, path.as_ref())
            .map_err(ApiError::from)
    }

    fn verify_file(
        &self,
        path: String,
        signature_path: String,
        public_key_path: String,
    ) -> Result<IntegrityReport, ApiError> {
        self.backend
            .verify_file(
                path.as_ref(),
                signature_path.as_ref(),
                public_key_path.as_ref(),
            )
            .map_err(ApiError::from)
    }

    fn keys_split(
        &self,
        session: SessionHandle,
        shares_total: u8,
        threshold: u8,
        out_dir: String,
    ) -> Result<Vec<ShareExportInfo>, ApiError> {
        self.backend
            .split_key(&session, shares_total, threshold, out_dir.as_ref())
            .map_err(ApiError::from)
    }

    fn keys_recover(
        &self,
        path: String,
        share_paths: Vec<String>,
    ) -> Result<SessionHandle, ApiError> {
        let refs: Vec<&std::path::Path> = share_paths.iter().map(std::path::Path::new).collect();
        self.backend
            .recover(path.as_ref(), &refs)
            .map_err(ApiError::from)
    }
}

#[cfg(test)]
mod tests {
    #[test]
    fn app_tracks_ipc_contract_version() {
        assert_eq!(super::APP_CONTRACT_VERSION, sv_types::CONTRACT_VERSION);
    }
}
