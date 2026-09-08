//! Desktop composition root — behaviour unchanged by the multi-platform split.
//!
//! Resolves the bundled `age`, `age-keygen` and `exiftool`, verifying each against its
//! build-time BLAKE3 pin (M3 tamper-evidence, `docs/M7-HARDENING.md`). A release build refuses
//! to run unpinned; a missing or mismatched ExifTool disables the Analysis module fail-closed
//! rather than failing the app.
//!
//! Moved verbatim out of `lib.rs` when the crate became the shared shell for desktop, Android
//! and iOS. The only edits are the module docs above and renaming `build_backend`/`build_meta`
//! to `backend`/`meta` to match the `compose` interface.

use std::path::PathBuf;

use sv_app::{AgePayloadCipher, AppVault, MetaApp, VaultBackend};

/// The concrete, thread-safe vault backend managed by Tauri on desktop.
pub type Backend = AppVault<AgePayloadCipher>;

// ===========================================================================
// Backend wiring — production binary pinning + bundling
// ===========================================================================

/// BLAKE3 pins of the bundled `age` / `age-keygen`, embedded by `build.rs`. `"dev-unpinned"`
/// means the binary was absent at build time (dev convenience; release refuses to run unpinned).
const AGE_PIN: &str = env!("SV_AGE_BLAKE3_PIN");
const AGE_KEYGEN_PIN: &str = env!("SV_AGE_KEYGEN_BLAKE3_PIN");

/// BLAKE3 pin of the bundled `exiftool` (Analysis module), embedded by `build.rs`.
/// `"dev-unpinned"` means the binary was absent at build time.
const EXIFTOOL_PIN: &str = env!("SV_EXIFTOOL_BLAKE3_PIN");

/// Build the concrete backend, resolving the bundled `age` toolchain and **verifying its
/// BLAKE3 hash against the build-time pin** (M3 tamper-evidence). `AgeCipher::new_pinned`
/// pins the `age` binary; `age-keygen` is pinned here (the payload cipher drives it directly).
pub fn backend(app: &tauri::AppHandle) -> Result<Backend, String> {
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

/// Build the Analysis surface, resolving the bundled ExifTool and **verifying its BLAKE3 hash
/// against the build-time pin**. Unlike the vault backend, a missing/unpinned/mismatched ExifTool
/// is **not** fatal: the Analysis module is an additive, optional toolkit module, so we manage a
/// **disabled** [`MetaApp`] (every metadata command then fails closed with `SV-INTERNAL`) and let
/// the rest of the toolkit run. A pin **mismatch** (tamper) and an unpinned **release** build both
/// disable the module rather than run an unverified tool (fail-closed).
pub fn meta(app: &tauri::AppHandle) -> MetaApp {
    let bin = match resolve_binary(app, "exiftool") {
        Ok(p) => p,
        Err(_) => return MetaApp::disabled(), // module simply unavailable (e.g. not bundled)
    };

    if EXIFTOOL_PIN == "dev-unpinned" {
        if !cfg!(debug_assertions) {
            eprintln!(
                "secure-vault: exiftool present but UNPINNED in a release build — Analysis module DISABLED (fail-closed)"
            );
            return MetaApp::disabled();
        }
        eprintln!(
            "secure-vault: WARNING — running with an UNPINNED exiftool binary (dev build only)"
        );
        match sv_meta::ExifTool::new_unpinned(&bin) {
            Ok(tool) => MetaApp::new(tool),
            Err(e) => {
                eprintln!("secure-vault: could not start exiftool: {e} — Analysis module disabled");
                MetaApp::disabled()
            }
        }
    } else {
        match sv_meta::ExifTool::new_pinned(&bin, EXIFTOOL_PIN) {
            Ok(tool) => MetaApp::new(tool),
            Err(e) => {
                eprintln!(
                    "secure-vault: exiftool pin check failed ({e}) — Analysis module DISABLED (fail-closed)"
                );
                MetaApp::disabled()
            }
        }
    }
}

/// Fail closed: an unpinned binary is tolerated only in debug builds.
fn require_dev_build(what: &str) -> Result<(), String> {
    if cfg!(debug_assertions) {
        Ok(())
    } else {
        Err(format!(
            "refusing to run with an unpinned {what} in a release build; bundle the pinned binary (see app/binaries/README.md)"
        ))
    }
}

/// Resolve a bundled binary: `SV_AGE*` env override (**debug builds only**) → Tauri **resource**
/// dir → next to the executable. On Unix, ensure it is executable (resource copies can lose the
/// bit). A release build ignores the env override and resolves only from the bundle (audit M-3).
fn resolve_binary(app: &tauri::AppHandle, stem: &str) -> Result<PathBuf, String> {
    use tauri::Manager;
    let name = exe_name(stem);

    // Dev-only path override. In a **release** build the binary must come from the bundled
    // resource dir (or next to the executable): an env var must not be able to redirect which
    // binary we launch. The BLAKE3 pin would still reject a non-matching one (so this is hardening,
    // not a hole), but closing the resolution surface in release keeps a shipped app from being
    // pointed at an out-of-bundle toolchain (audit M-3). `cargo tauri dev` (debug) still honors
    // `SV_AGE_BIN` / `SV_AGE_KEYGEN_BIN` / `SV_EXIFTOOL_BIN` for local iteration.
    if cfg!(debug_assertions) {
        let env_key = match stem {
            "age" => "SV_AGE_BIN",
            "age-keygen" => "SV_AGE_KEYGEN_BIN",
            "exiftool" => "SV_EXIFTOOL_BIN",
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
        "{name} not found (looked at the SV_* binary env override, the bundled resource dir, and next to the executable)"
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
