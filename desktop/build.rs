//! Build script: embed BLAKE3 pins for the bundled `age` toolchain, then run `tauri-build`.
//!
//! For each binary we hash `binaries/<name>` (or the `SV_AGE_*_SRC` override) at build time and
//! emit it as a compile-time env var the runtime reads (`env!`). If the binary is absent we emit
//! the sentinel `dev-unpinned` and warn; the runtime then refuses to run unpinned in **release**
//! builds (fail-closed) while staying ergonomic for `cargo tauri dev`.

use std::path::PathBuf;

fn main() {
    emit_pin("age", "SV_AGE_BLAKE3_PIN", "SV_AGE_BIN_SRC");
    emit_pin(
        "age-keygen",
        "SV_AGE_KEYGEN_BLAKE3_PIN",
        "SV_AGE_KEYGEN_BIN_SRC",
    );
    tauri_build::build();
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
