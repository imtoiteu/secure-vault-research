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

use std::path::PathBuf;

use sv_app::{
    AgePayloadCipher, AppVault, CommandSurface, IpcPassphrase, PlatformApp, PlatformSurface,
    VaultBackend,
};
use sv_types::{
    ApiError, AppInfo, IntegrityReport, ItemInfo, RecoverReport, SessionHandle, ShareExportInfo,
    SharePolicy, ShareSplitReport, SigningKeypairInfo, VaultMeta,
};

/// The concrete, thread-safe vault backend managed by Tauri.
type Backend = AppVault<AgePayloadCipher>;

/// The vault-free Integrity + Cryptography services, a second managed state.
type Platform = PlatformApp;

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

// ===========================================================================
// Backend wiring — production binary pinning + bundling
// ===========================================================================

/// BLAKE3 pins of the bundled `age` / `age-keygen`, embedded by `build.rs`. `"dev-unpinned"`
/// means the binary was absent at build time (dev convenience; release refuses to run unpinned).
const AGE_PIN: &str = env!("SV_AGE_BLAKE3_PIN");
const AGE_KEYGEN_PIN: &str = env!("SV_AGE_KEYGEN_BLAKE3_PIN");

/// Build the concrete backend, resolving the bundled `age` toolchain and **verifying its
/// BLAKE3 hash against the build-time pin** (M3 tamper-evidence). `AgeCipher::new_pinned`
/// pins the `age` binary; `age-keygen` is pinned here (the payload cipher drives it directly).
fn build_backend(app: &tauri::AppHandle) -> Result<Backend, String> {
    let age = resolve_binary(app, "age")?;
    let keygen = resolve_binary(app, "age-keygen")?;

    let cipher = if AGE_PIN == "dev-unpinned" {
        require_dev_build("age")?;
        eprintln!("secure-vault: WARNING — running with an UNPINNED age binary (dev build only)");
        sv_age::AgeCipher::new_unpinned(&age).map_err(|e| e.to_string())?
    } else {
        sv_age::AgeCipher::new_pinned(&age, AGE_PIN).map_err(|e| e.to_string())?
    };

    if AGE_KEYGEN_PIN == "dev-unpinned" {
        require_dev_build("age-keygen")?;
    } else {
        let actual = sv_age::binary_blake3_hex(&keygen).map_err(|e| e.to_string())?;
        if !actual.eq_ignore_ascii_case(AGE_KEYGEN_PIN) {
            return Err(format!(
                "age-keygen hash mismatch: expected {AGE_KEYGEN_PIN}, got {actual}"
            ));
        }
    }

    Ok(AppVault::new(VaultBackend::new(AgePayloadCipher::new(
        cipher, keygen,
    ))))
}

/// Fail closed: an unpinned binary is tolerated only in debug builds.
fn require_dev_build(what: &str) -> Result<(), String> {
    if cfg!(debug_assertions) {
        Ok(())
    } else {
        Err(format!(
            "refusing to run with an unpinned {what} in a release build; bundle the pinned binary (see desktop/binaries/README.md)"
        ))
    }
}

/// Resolve a bundled binary: `SV_AGE*` env override → Tauri **resource** dir → next to the
/// executable. On Unix, ensure it is executable (resource copies can lose the bit).
fn resolve_binary(app: &tauri::AppHandle, stem: &str) -> Result<PathBuf, String> {
    use tauri::Manager;
    let name = exe_name(stem);

    let env_key = match stem {
        "age" => "SV_AGE_BIN",
        "age-keygen" => "SV_AGE_KEYGEN_BIN",
        _ => "",
    };
    if !env_key.is_empty() {
        if let Ok(p) = std::env::var(env_key) {
            let p = PathBuf::from(p);
            if p.exists() {
                return ensure_executable(p);
            }
        }
    }

    if let Ok(p) = app.path().resolve(
        format!("binaries/{name}"),
        tauri::path::BaseDirectory::Resource,
    ) {
        if p.exists() {
            return ensure_executable(p);
        }
    }

    if let Some(dir) = std::env::current_exe()
        .ok()
        .and_then(|e| e.parent().map(PathBuf::from))
    {
        let p = dir.join(&name);
        if p.exists() {
            return ensure_executable(p);
        }
    }

    Err(format!(
        "{name} not found (looked at SV_AGE_* env, the bundled resource dir, and next to the executable)"
    ))
}

fn ensure_executable(path: PathBuf) -> Result<PathBuf, String> {
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        if let Ok(meta) = std::fs::metadata(&path) {
            let mut perm = meta.permissions();
            if perm.mode() & 0o111 == 0 {
                perm.set_mode(perm.mode() | 0o755);
                let _ = std::fs::set_permissions(&path, perm);
            }
        }
    }
    Ok(path)
}

fn exe_name(stem: &str) -> String {
    if cfg!(windows) {
        format!("{stem}.exe")
    } else {
        stem.to_string()
    }
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
            let backend = build_backend(app.handle())?;
            app.manage(backend);
            // The Integrity + Cryptography services need no binary/session — manage them directly.
            app.manage(PlatformApp::new());
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
            crypto_encrypt_file,
            crypto_decrypt_file,
            crypto_generate_signing_keypair,
            crypto_sign_file,
            shares_split_secret,
            shares_split_file,
            shares_recover_secret
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
