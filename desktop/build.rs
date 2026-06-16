//! Build script: stage + BLAKE3-pin the bundled binaries, then run `tauri-build`.
//!
//! For each binary we hash `binaries/<name>` (or the `SV_*_BIN_SRC` override) at build time and
//! emit it as a compile-time env var the runtime reads (`env!`). If the binary is absent we emit
//! the sentinel `dev-unpinned` and warn; the runtime then refuses to run unpinned in **release**
//! builds (fail-closed) while staying ergonomic for `cargo tauri dev`.
//!
//! The Analysis module's **ExifTool** is additionally *staged* here: so a packaged build is
//! self-contained with no env var / external setup, [`stage_exiftool`] copies the ExifTool
//! distribution into `binaries/` (which `tauri.conf.json` bundles into app resources) before
//! pinning it. The runtime then resolves it from the bundled resource dir — no repository-relative
//! path at runtime.

use std::path::{Path, PathBuf};

fn main() {
    emit_pin("age", "SV_AGE_BLAKE3_PIN", "SV_AGE_BIN_SRC");
    emit_pin(
        "age-keygen",
        "SV_AGE_KEYGEN_BLAKE3_PIN",
        "SV_AGE_KEYGEN_BIN_SRC",
    );
    // Analysis module: make the bundled ExifTool self-staging, then hash-pin it. Staging is a no-op
    // when it is already present or when no source is available (→ dev-unpinned sentinel → the
    // runtime disables the Analysis module in release; fail-closed).
    stage_exiftool();
    emit_pin("exiftool", "SV_EXIFTOOL_BLAKE3_PIN", "SV_EXIFTOOL_BIN_SRC");
    tauri_build::build();
}

/// Ensure the ExifTool distribution is present under `binaries/` so the Tauri bundler can package
/// it and the runtime can resolve it from app resources **with no env var or repo path**.
///
/// Source: `SV_EXIFTOOL_DIST_SRC` if set, else the in-repo `metadata/exiftool` clone (two levels up
/// from this crate). We copy **only when the destination is absent**, so a fresh checkout self-stages
/// on its first build while an already-staged tree (or a hand-placed binary) is left untouched —
/// delete `binaries/exiftool` (+ `binaries/lib/`) to re-stage from an updated clone.
///
/// * Unix: the distribution is the `exiftool` Perl script **plus a sibling `lib/` tree** it loads via
///   `$0`; we stage both (and mark the script executable). System Perl provides the interpreter.
/// * Windows: the standalone `windows_exiftool` PAR executable is self-contained (no `lib/`/Perl); we
///   stage it as `binaries/exiftool.exe`.
///
/// Never fails the build: if no source exists we simply skip (the pin step then warns and the module
/// stays disabled, fail-closed).
fn stage_exiftool() {
    let manifest = PathBuf::from(std::env::var("CARGO_MANIFEST_DIR").unwrap());
    let bin_dir = manifest.join("binaries");
    let target_windows = std::env::var("CARGO_CFG_TARGET_OS")
        .map(|os| os == "windows")
        .unwrap_or(false);

    println!("cargo:rerun-if-env-changed=SV_EXIFTOOL_DIST_SRC");
    let src = std::env::var("SV_EXIFTOOL_DIST_SRC")
        .map(PathBuf::from)
        .unwrap_or_else(|_| {
            manifest
                .join("..")
                .join("..")
                .join("metadata")
                .join("exiftool")
        });

    if target_windows {
        let dest = bin_dir.join("exiftool.exe");
        if dest.exists() {
            return;
        }
        let from = src.join("windows_exiftool");
        if from.exists() {
            let _ = std::fs::create_dir_all(&bin_dir);
            if std::fs::copy(&from, &dest).is_ok() {
                println!(
                    "cargo:warning=secure-vault: staged windows_exiftool -> binaries/exiftool.exe"
                );
            }
        }
        return;
    }

    let dest_script = bin_dir.join("exiftool");
    if dest_script.exists() {
        return; // already staged
    }
    let from_script = src.join("exiftool");
    let from_lib = src.join("lib");
    if !from_script.exists() || !from_lib.exists() {
        return; // no source — emit_pin will warn; module stays fail-closed
    }
    let _ = std::fs::create_dir_all(&bin_dir);
    if std::fs::copy(&from_script, &dest_script).is_ok() {
        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;
            let _ = std::fs::set_permissions(&dest_script, std::fs::Permissions::from_mode(0o755));
        }
        if copy_dir_recursive(&from_lib, &bin_dir.join("lib")).is_ok() {
            println!(
                "cargo:warning=secure-vault: staged ExifTool (exiftool + lib/) into binaries/ from {}",
                src.display()
            );
        }
    }
}

/// Recursively copy `src` into `dst` (used to stage ExifTool's `lib/` Perl module tree).
fn copy_dir_recursive(src: &Path, dst: &Path) -> std::io::Result<()> {
    std::fs::create_dir_all(dst)?;
    for entry in std::fs::read_dir(src)? {
        let entry = entry?;
        let from = entry.path();
        let to = dst.join(entry.file_name());
        if entry.file_type()?.is_dir() {
            copy_dir_recursive(&from, &to)?;
        } else {
            std::fs::copy(&from, &to)?;
        }
    }
    Ok(())
}

fn emit_pin(stem: &str, out_env: &str, src_override: &str) {
    let target_windows = std::env::var("CARGO_CFG_TARGET_OS")
        .map(|os| os == "windows")
        .unwrap_or(false);
    let name = if target_windows {
        format!("{stem}.exe")
    } else {
        stem.to_string()
    };

    let manifest = PathBuf::from(std::env::var("CARGO_MANIFEST_DIR").unwrap());
    println!("cargo:rerun-if-env-changed={src_override}");
    let path = std::env::var(src_override)
        .map(PathBuf::from)
        .unwrap_or_else(|_| manifest.join("binaries").join(&name));
    println!("cargo:rerun-if-changed={}", path.display());

    let pin = match std::fs::read(&path) {
        Ok(bytes) => blake3::hash(&bytes).to_hex().to_string(),
        Err(_) => {
            println!(
                "cargo:warning=secure-vault: no {name} at {} — building DEV-UNPINNED (a release build will refuse to run unpinned). Place the binary there or set {src_override}.",
                path.display()
            );
            "dev-unpinned".to_string()
        }
    };
    println!("cargo:rustc-env={out_env}={pin}");
}
