//! Tauri 2 runtime shell for Secure Vault.
//!
//! This crate is the **only** place the GUI/runtime lives. It owns one
//! [`sv_app::AppVault`] (the tested command surface over the audited core) as managed Tauri
//! state and exposes its methods as `#[tauri::command]`s. All real logic — crypto, sessions,
//! the oracle-safe error taxonomy, passphrase hygiene — lives in the core crates; this file is
//! thin glue.
//!
//! Passphrases arrive as [`sv_app::IpcPassphrase`] (zeroizing, redacted), so even at the
//! command boundary they are never plain strings in our code. Errors are the coded,
//! oracle-safe [`sv_types::ApiError`]; the frontend localizes off `error.code`.

use sv_app::{
    CommandSurface, IpcPassphrase, MetaApp, MetaSurface, PlatformApp, PlatformSurface, StegoApp,
    StegoSurface, WatermarkApp, WatermarkSurface,
};
use sv_types::{
    ApiError, AppInfo, IntegrityReport, ItemInfo, MetadataDiffReport, MetadataReport,
    QrExportReport, RecoverReport, SanitizeReport, SessionHandle, ShareExportInfo, SharePolicy,
    ShareSplitReport, SigningKeypairInfo, StegoDetectReport, StegoExtractReport, StegoHideReport,
    VaultMeta, VerifyIntegrityReport, WatermarkEmbedReport, WatermarkVerifyReport,
};

mod compose;

/// The concrete vault backend, chosen per platform by the composition root.
use compose::Backend;

/// The vault-free Integrity + Cryptography services, a second managed state.
type Platform = PlatformApp;

/// The vault-free Steganography services (Hide / Extract / Detect), a third managed state.
type Stego = StegoApp;

/// The vault-free Analysis services (Metadata Inspect / Sanitize / Compare), a fourth managed
/// state. Backed by a hash-pinned ExifTool subprocess; disabled (fail-closed) if absent.
type Meta = MetaApp;

/// The vault-free Watermarking services (Embed / Verify a fragile tamper-evident mark), a fifth
/// managed state. Pure in-process Rust; needs no binary/session.
type Watermark = WatermarkApp;

// ===========================================================================
// Commands — 1:1 with `CommandSurface`. `tauri::State<Backend>` derefs to `&Backend`.
// ===========================================================================

#[tauri::command]
fn app_info(state: tauri::State<'_, Backend>) -> AppInfo {
    state.app_info()
}

#[tauri::command]
fn vault_create(
    state: tauri::State<'_, Backend>,
    path: String,
    passphrase: IpcPassphrase,
    policy: Option<SharePolicy>,
) -> Result<VaultMeta, ApiError> {
    state.vault_create(path, passphrase, policy)
}

#[tauri::command]
fn vault_unlock(
    state: tauri::State<'_, Backend>,
    path: String,
    passphrase: IpcPassphrase,
) -> Result<SessionHandle, ApiError> {
    state.vault_unlock(path, passphrase)
}

#[tauri::command]
fn vault_lock(state: tauri::State<'_, Backend>, session: SessionHandle) -> Result<(), ApiError> {
    state.vault_lock(session)
}

#[tauri::command]
fn vault_change_passphrase(
    state: tauri::State<'_, Backend>,
    session: SessionHandle,
    new_passphrase: IpcPassphrase,
) -> Result<(), ApiError> {
    state.vault_change_passphrase(session, new_passphrase)
}

#[tauri::command]
fn vault_meta(
    state: tauri::State<'_, Backend>,
    session: SessionHandle,
) -> Result<VaultMeta, ApiError> {
    state.vault_meta(session)
}

#[tauri::command]
fn export_signing_public_key(
    state: tauri::State<'_, Backend>,
    session: SessionHandle,
) -> Result<String, ApiError> {
    state.export_signing_public_key(session)
}

#[tauri::command]
fn item_list(
    state: tauri::State<'_, Backend>,
    session: SessionHandle,
) -> Result<Vec<ItemInfo>, ApiError> {
    state.item_list(session)
}

#[tauri::command]
fn item_add(
    state: tauri::State<'_, Backend>,
    session: SessionHandle,
    source: String,
    name: String,
) -> Result<ItemInfo, ApiError> {
    state.item_add(session, source, name)
}

#[tauri::command]
fn item_extract(
    state: tauri::State<'_, Backend>,
    session: SessionHandle,
    item_id: String,
    dest: String,
) -> Result<(), ApiError> {
    state.item_extract(session, item_id, dest)
}

#[tauri::command]
fn integrity_check(
    state: tauri::State<'_, Backend>,
    path: String,
) -> Result<IntegrityReport, ApiError> {
    state.integrity_check(path)
}

#[tauri::command]
fn integrity_hash(state: tauri::State<'_, Backend>, path: String) -> Result<String, ApiError> {
    state.integrity_hash(path)
}

#[tauri::command]
fn sign_file(
    state: tauri::State<'_, Backend>,
    session: SessionHandle,
    path: String,
) -> Result<String, ApiError> {
    state.sign_file(session, path)
}

#[tauri::command]
fn verify_file(
    state: tauri::State<'_, Backend>,
    path: String,
    signature_path: String,
    public_key_path: String,
) -> Result<IntegrityReport, ApiError> {
    state.verify_file(path, signature_path, public_key_path)
}

#[tauri::command]
fn keys_split(
    state: tauri::State<'_, Backend>,
    session: SessionHandle,
    shares_total: u8,
    threshold: u8,
    out_dir: String,
) -> Result<Vec<ShareExportInfo>, ApiError> {
    state.keys_split(session, shares_total, threshold, out_dir)
}

#[tauri::command]
fn keys_recover(
    state: tauri::State<'_, Backend>,
    path: String,
    share_paths: Vec<String>,
) -> Result<SessionHandle, ApiError> {
    state.keys_recover(path, share_paths)
}

// ===========================================================================
// Platform commands — Integrity + Cryptography modules (vault-free, session-free).
// Backed by the second managed state `Platform`; additive to the vault surface.
// ===========================================================================

#[tauri::command]
fn integrity_hash_file(
    platform: tauri::State<'_, Platform>,
    path: String,
) -> Result<String, ApiError> {
    platform.hash_file(path)
}

#[tauri::command]
fn integrity_verify_signature(
    platform: tauri::State<'_, Platform>,
    path: String,
    signature_path: String,
    public_key_path: String,
) -> Result<IntegrityReport, ApiError> {
    platform.verify_signature(path, signature_path, public_key_path)
}

#[tauri::command]
fn integrity_verify_integrity(
    platform: tauri::State<'_, Platform>,
    path: String,
    expected_hash_hex: Option<String>,
    signature_path: Option<String>,
    public_key_path: Option<String>,
) -> Result<VerifyIntegrityReport, ApiError> {
    platform.verify_integrity(path, expected_hash_hex, signature_path, public_key_path)
}

#[tauri::command]
fn crypto_encrypt_file(
    platform: tauri::State<'_, Platform>,
    input: String,
    output: String,
    passphrase: IpcPassphrase,
) -> Result<String, ApiError> {
    platform.encrypt_file(input, output, passphrase)
}

#[tauri::command]
fn crypto_decrypt_file(
    platform: tauri::State<'_, Platform>,
    input: String,
    output: String,
    passphrase: IpcPassphrase,
) -> Result<String, ApiError> {
    platform.decrypt_file(input, output, passphrase)
}

#[tauri::command]
fn crypto_generate_signing_keypair(
    platform: tauri::State<'_, Platform>,
    out_dir: String,
    name: String,
    passphrase: IpcPassphrase,
) -> Result<SigningKeypairInfo, ApiError> {
    platform.generate_signing_keypair(out_dir, name, passphrase)
}

#[tauri::command]
fn crypto_sign_file(
    platform: tauri::State<'_, Platform>,
    input: String,
    signing_key_path: String,
    passphrase: IpcPassphrase,
) -> Result<String, ApiError> {
    platform.sign_file(input, signing_key_path, passphrase)
}

// --- Secret Sharing (vault-free, session-free; standalone toolkit module) ---

#[tauri::command]
fn shares_split_secret(
    platform: tauri::State<'_, Platform>,
    secret: IpcPassphrase,
    shares_total: u8,
    threshold: u8,
    out_dir: String,
) -> Result<ShareSplitReport, ApiError> {
    platform.shares_split_secret(secret, shares_total, threshold, out_dir)
}

#[tauri::command]
fn shares_split_file(
    platform: tauri::State<'_, Platform>,
    input: String,
    shares_total: u8,
    threshold: u8,
    out_dir: String,
) -> Result<ShareSplitReport, ApiError> {
    platform.shares_split_file(input, shares_total, threshold, out_dir)
}

#[tauri::command]
fn shares_recover_secret(
    platform: tauri::State<'_, Platform>,
    share_paths: Vec<String>,
    share_strings: Vec<String>,
    payload_path: String,
    out_path: String,
) -> Result<RecoverReport, ApiError> {
    platform.shares_recover_secret(share_paths, share_strings, payload_path, out_path)
}

// --- Secure QR Transfer (Secret Sharing over QR images; vault-free, session-free) ------------

#[tauri::command]
fn shares_export_qr(
    platform: tauri::State<'_, Platform>,
    share_b64: Vec<String>,
    out_dir: String,
) -> Result<QrExportReport, ApiError> {
    platform.shares_export_qr(share_b64, out_dir)
}

#[tauri::command]
fn shares_recover_from_qr(
    platform: tauri::State<'_, Platform>,
    qr_paths: Vec<String>,
    payload_path: String,
    out_path: String,
) -> Result<RecoverReport, ApiError> {
    platform.shares_recover_from_qr(qr_paths, payload_path, out_path)
}

#[tauri::command]
fn copy_file(
    platform: tauri::State<'_, Platform>,
    from: String,
    to: String,
) -> Result<String, ApiError> {
    platform.copy_file(from, to)
}

// --- Steganography (vault-free, session-free; standalone toolkit module) -----
// Backed by the third managed state `Stego`; additive to the vault surface.

#[tauri::command]
fn stego_hide(
    stego: tauri::State<'_, Stego>,
    cover_path: String,
    payload_path: String,
    output_path: String,
    passphrase: IpcPassphrase,
    randomize: bool,
) -> Result<StegoHideReport, ApiError> {
    stego.stego_hide(cover_path, payload_path, output_path, passphrase, randomize)
}

#[tauri::command]
fn stego_extract(
    stego: tauri::State<'_, Stego>,
    stego_path: String,
    output_dir: String,
    passphrase: IpcPassphrase,
) -> Result<StegoExtractReport, ApiError> {
    stego.stego_extract(stego_path, output_dir, passphrase)
}

#[tauri::command]
fn stego_detect(
    stego: tauri::State<'_, Stego>,
    image_path: String,
) -> Result<StegoDetectReport, ApiError> {
    stego.stego_detect(image_path)
}

// --- Analysis (vault-free, session-free; standalone toolkit module) ----------
// Backed by the fourth managed state `Meta`; additive to the vault surface. No method takes a
// passphrase or session — metadata operations move no secret across the boundary.

#[tauri::command]
fn metadata_inspect(
    meta: tauri::State<'_, Meta>,
    path: String,
) -> Result<MetadataReport, ApiError> {
    meta.metadata_inspect(path)
}

#[tauri::command]
fn metadata_sanitize(
    meta: tauri::State<'_, Meta>,
    input: String,
    output: String,
) -> Result<SanitizeReport, ApiError> {
    meta.metadata_sanitize(input, output)
}

#[tauri::command]
fn metadata_diff(
    meta: tauri::State<'_, Meta>,
    path_a: String,
    path_b: String,
) -> Result<MetadataDiffReport, ApiError> {
    meta.metadata_diff(path_a, path_b)
}

/// Whether the Analysis module is usable in this build (its hash-pinned ExifTool resolved). The UI
/// probes this to disable/explain the metadata tools instead of letting a click fail with a generic
/// internal error when the binary isn't bundled (C4).
#[tauri::command]
fn metadata_available(meta: tauri::State<'_, Meta>) -> bool {
    meta.is_available()
}

// --- Watermarking (vault-free, session-free; standalone toolkit module) -------
// Backed by the fifth managed state `Watermark`; additive to the vault surface.

#[tauri::command]
fn watermark_embed(
    watermark: tauri::State<'_, Watermark>,
    input: String,
    output: String,
    passphrase: IpcPassphrase,
) -> Result<WatermarkEmbedReport, ApiError> {
    watermark.watermark_embed(input, output, passphrase)
}

#[tauri::command]
fn watermark_verify(
    watermark: tauri::State<'_, Watermark>,
    input: String,
    passphrase: IpcPassphrase,
) -> Result<WatermarkVerifyReport, ApiError> {
    watermark.watermark_verify(input, passphrase)
}


/// Build and run the Tauri application. Called by `main.rs`. The backend is constructed in the
/// `setup` hook so it can resolve bundled resources via the app handle.
///
/// # Panics
/// Panics if the Tauri runtime fails to start. Backend-init failures (missing/again-pinned
/// binaries) abort startup with a clear message via the `setup` error.
pub fn run() {
    use tauri::Manager;
    tauri::Builder::default()
        // Native file/folder/save dialogs for the UI (U1). No application command or contract
        // changes — the dialogs only help the user pick the path strings commands already take.
        .plugin(tauri_plugin_dialog::init())
        // "Show in folder" / "Open file" for result cards (U2). UI convenience only.
        .plugin(tauri_plugin_opener::init())
        .setup(|app| {
            let backend = compose::backend(app.handle())?;
            app.manage(backend);
            // The Integrity + Cryptography services need no binary/session — manage them directly.
            app.manage(PlatformApp::new());
            // The Steganography services likewise need no binary/session.
            app.manage(StegoApp::new());
            // The Analysis services drive a hash-pinned ExifTool; disabled (fail-closed) if absent.
            app.manage(compose::meta(app.handle()));
            // The Watermarking services are pure in-process Rust — manage them directly.
            app.manage(WatermarkApp::new());
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            app_info,
            vault_create,
            vault_unlock,
            vault_lock,
            vault_change_passphrase,
            vault_meta,
            export_signing_public_key,
            item_list,
            item_add,
            item_extract,
            integrity_check,
            integrity_hash,
            sign_file,
            verify_file,
            keys_split,
            keys_recover,
            integrity_hash_file,
            integrity_verify_signature,
            integrity_verify_integrity,
            crypto_encrypt_file,
            crypto_decrypt_file,
            crypto_generate_signing_keypair,
            crypto_sign_file,
            shares_split_secret,
            shares_split_file,
            shares_recover_secret,
            shares_export_qr,
            shares_recover_from_qr,
            copy_file,
            stego_hide,
            stego_extract,
            stego_detect,
            metadata_inspect,
            metadata_sanitize,
            metadata_diff,
            metadata_available,
            watermark_embed,
            watermark_verify
        ])
        .run(tauri::generate_context!())
        .expect("error while running Secure Vault");
}

#[cfg(test)]
mod ui_contract {
    //! Enforces the IPC↔UI error contract: the JS `MESSAGES` map in `frontend/main.js` must cover
    //! exactly the `ApiError` codes the backend can emit — no missing localizations, no orphans.
    //! The frontend is bundler-free (no codegen step is practical), so this Rust test is how the
    //! hand-maintained map stays in lockstep with `sv_types::ApiError`.
    use sv_types::ApiError;

    /// Extract the `"SV-…"` keys from the `const MESSAGES = { … };` block of `main.js`.
    fn message_keys(js: &str) -> Vec<String> {
        let start = js
            .find("const MESSAGES = {")
            .expect("MESSAGES map present in main.js");
        let rest = &js[start..];
        let end = rest.find("};").expect("MESSAGES map is closed");
        let mut keys = Vec::new();
        for line in rest[..end].lines() {
            // Entry lines look like:  "SV-NOT-FOUND": "That file could not be found.",
            if let Some(after_quote) = line.trim().strip_prefix('"') {
                if let Some(q) = after_quote.find('"') {
                    let key = &after_quote[..q];
                    if key.starts_with("SV-") {
                        keys.push(key.to_string());
                    }
                }
            }
        }
        keys
    }

    #[test]
    fn every_api_error_code_has_a_ui_message_and_no_orphans() {
        let js = include_str!("../frontend/main.js");
        let keys = message_keys(js);

        // 1) Every backend code is localized.
        for code in ApiError::ALL_CODES {
            assert!(
                keys.iter().any(|k| k == code),
                "frontend MESSAGES is missing a string for {code}"
            );
        }
        // 2) No orphan UI code the backend can never emit.
        for k in &keys {
            assert!(
                ApiError::ALL_CODES.contains(&k.as_str()),
                "frontend MESSAGES has orphan code {k} (not an ApiError)"
            );
        }
        // 3) Exact 1:1 (guards against duplicate keys / drift).
        assert_eq!(
            keys.len(),
            ApiError::ALL_CODES.len(),
            "MESSAGES has {} keys, ApiError::ALL_CODES has {}",
            keys.len(),
            ApiError::ALL_CODES.len()
        );
    }
}
