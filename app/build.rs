//! Build script: stage + BLAKE3-pin the bundled binaries, then run `tauri-build`.
//!
//! For each binary we hash `binaries/<name>` (or the `SV_*_BIN_SRC` override) at build time and
//! emit it as a compile-time env var the runtime reads (`env!`). If a binary is absent we emit the
//! sentinel `dev-unpinned` and warn; the runtime then refuses to run unpinned in **release** builds
//! (fail-closed) while staying ergonomic for `cargo tauri dev`. As an earlier, louder gate, a
//! **release** build (`PROFILE=release`) hard-fails when a *mandatory* binary (age / age-keygen) is
//! missing — so a packaged bundle that would only fail at first launch can never be produced
//! (debug/`cargo tauri dev` stays unpinned-tolerant).
//!
//! A pin proves byte-identity, not *runnability*: a binary staged for a different OS/CPU than the
//! build target would still pin "successfully" yet fail at first launch. [`check_staged_arch`]
//! reads each binary's executable header (no execution) and fails a release build of a mandatory
//! binary (warns otherwise) on a positively-identified OS/arch mismatch.
//!
//! The Analysis module's **ExifTool** is additionally *staged* here: so a packaged build is
//! self-contained with no env var / external setup, [`stage_exiftool`] copies the ExifTool
//! distribution into `binaries/` (which `tauri.conf.json` bundles into app resources) before
//! pinning it. The runtime then resolves it from the bundled resource dir — no repository-relative
//! path at runtime.

use std::path::{Path, PathBuf};

fn main() {
    // age + age-keygen are MANDATORY: the vault backend cannot start without them, so a release
    // build must not be allowed to produce a bundle that lacks them (see `emit_pin`).
    emit_pin("age", "SV_AGE_BLAKE3_PIN", "SV_AGE_BIN_SRC", Mandatory::Yes);
    emit_pin(
        "age-keygen",
        "SV_AGE_KEYGEN_BLAKE3_PIN",
        "SV_AGE_KEYGEN_BIN_SRC",
        Mandatory::Yes,
    );
    // Analysis module: make the bundled ExifTool self-staging, then hash-pin it. Staging is a no-op
    // when it is already present or when no source is available (→ dev-unpinned sentinel → the
    // runtime disables the Analysis module in release; fail-closed). ExifTool is OPTIONAL, so its
    // absence only warns — it never fails the build.
    stage_exiftool();
    emit_pin(
        "exiftool",
        "SV_EXIFTOOL_BLAKE3_PIN",
        "SV_EXIFTOOL_BIN_SRC",
        Mandatory::No,
    );
    tauri_build::build();
}

/// Whether a bundled binary is required for the app to function. A missing **mandatory** binary
/// fails a release build (the runtime would otherwise refuse to start); a missing **optional** one
/// only warns (its module degrades fail-closed).
#[derive(Clone, Copy, PartialEq, Eq)]
enum Mandatory {
    Yes,
    No,
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
/// * Windows: a real standalone `exiftool.exe` is the PAR-packed `exiftool(-k).exe` from the official
///   Windows ZIP. The in-repo clone ships only the ExifTool **Perl source** under `windows_exiftool`
///   (a `#!`-shebang script, not a PE) which Windows cannot execute — so we stage it **only if it is
///   actually a Windows executable (`MZ`)**, and otherwise refuse and warn (the operator must supply
///   the real exe). This keeps a non-functional Analysis module from silently shipping on Windows.
///
/// Never fails the build: if no usable source exists we simply skip (the pin step then warns and the
/// module stays disabled, fail-closed — ExifTool is optional).
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
            // Already staged or hand-placed: validate it is a real PE, else it would pin+ship a dead
            // Analysis module (the BLAKE3 pin "passes" but Windows cannot execute the file).
            if !looks_like_windows_exe(&dest) {
                println!(
                    "cargo:warning=secure-vault: binaries/exiftool.exe is not a Windows executable (PE) — \
                     Analysis will stay disabled at runtime. Replace it with the official PAR-packed \
                     exiftool(-k).exe (renamed to exiftool.exe)."
                );
            }
            return;
        }
        let from = src.join("windows_exiftool");
        if from.exists() {
            if looks_like_windows_exe(&from) {
                let _ = std::fs::create_dir_all(&bin_dir);
                if std::fs::copy(&from, &dest).is_ok() {
                    println!(
                        "cargo:warning=secure-vault: staged windows_exiftool -> binaries/exiftool.exe"
                    );
                }
            } else {
                // The in-repo metadata/exiftool clone ships the ExifTool Perl **source** under this
                // name, not the PAR-packed standalone .exe. Staging it would bundle a file Windows
                // cannot run → Analysis silently disabled. Refuse, and say how to supply the real exe.
                println!(
                    "cargo:warning=secure-vault: {} is the ExifTool Perl source, not a Windows .exe — \
                     refusing to stage it as exiftool.exe. Supply the official PAR-packed exiftool(-k).exe \
                     (rename to binaries/exiftool.exe) or point SV_EXIFTOOL_DIST_SRC at a dir whose \
                     windows_exiftool is a real PE. Analysis stays disabled until then.",
                    from.display()
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

/// True if the file at `path` begins with the `MZ` signature of a Windows PE executable. Guards
/// against staging/pinning the ExifTool **Perl source** (`#!/usr/bin/env perl`) as `exiftool.exe`,
/// which would bundle a file Windows cannot execute and silently disable the Analysis module.
fn looks_like_windows_exe(path: &Path) -> bool {
    use std::io::Read;
    match std::fs::File::open(path) {
        Ok(mut f) => {
            let mut magic = [0u8; 2];
            f.read_exact(&mut magic).is_ok() && &magic == b"MZ"
        }
        Err(_) => false,
    }
}

/// The (OS-family, CPU-arch) a bundled native binary will actually run on, recovered from its
/// executable header **without running it**. `os` matches `CARGO_CFG_TARGET_OS`
/// (`macos`/`linux`/`windows`) and `arch` matches `CARGO_CFG_TARGET_ARCH` (`x86_64`/`aarch64`).
/// `arch` is `None` for a multi-arch (fat/universal) Mach-O — it runs on every contained slice —
/// or when the concrete CPU isn't one we model.
struct StagedTarget {
    os: &'static str,
    arch: Option<&'static str>,
}

/// Recover [`StagedTarget`] from the leading bytes of an executable. Returns `None` for an
/// unrecognized format — notably the ExifTool Perl **script** (`#!…`), which is arch-independent and
/// must never be treated as a mismatch. Bounds-checked; never panics on a short/corrupt file.
fn detect_staged_target(bytes: &[u8]) -> Option<StagedTarget> {
    // ELF (Linux): 0x7F 'E' 'L' 'F'; e_machine is a u16 at offset 18 in EI_DATA byte order.
    if bytes.starts_with(b"\x7FELF") && bytes.len() >= 20 {
        let little_endian = bytes[5] != 2; // EI_DATA: 1=LE, 2=BE (x86_64/aarch64 are LE)
        let e_machine = if little_endian {
            u16::from_le_bytes([bytes[18], bytes[19]])
        } else {
            u16::from_be_bytes([bytes[18], bytes[19]])
        };
        let arch = match e_machine {
            62 => Some("x86_64"),   // EM_X86_64
            183 => Some("aarch64"), // EM_AARCH64
            _ => None,
        };
        return Some(StagedTarget { os: "linux", arch });
    }
    // Mach-O thin 64-bit (macOS): magic MH_MAGIC_64 (0xFEEDFACF) stored little-endian; cputype is a
    // u32 at offset 4. (Verified against the staged arm64 `age`: CF FA ED FE 0C 00 00 01.)
    if bytes.starts_with(&[0xCF, 0xFA, 0xED, 0xFE]) && bytes.len() >= 8 {
        let cputype = u32::from_le_bytes([bytes[4], bytes[5], bytes[6], bytes[7]]);
        let arch = match cputype {
            0x0100_0007 => Some("x86_64"),  // CPU_TYPE_X86_64
            0x0100_000C => Some("aarch64"), // CPU_TYPE_ARM64
            _ => None,
        };
        return Some(StagedTarget { os: "macos", arch });
    }
    // Mach-O thin 32-bit (CE FA ED FE) or fat/universal (CA FE BA BE / …BF): macOS, arch left as
    // `None` (32-bit desktop is out of scope; a universal binary runs on every slice).
    if bytes.starts_with(&[0xCE, 0xFA, 0xED, 0xFE])
        || bytes.starts_with(&[0xCA, 0xFE, 0xBA, 0xBE])
        || bytes.starts_with(&[0xCA, 0xFE, 0xBA, 0xBF])
    {
        return Some(StagedTarget {
            os: "macos",
            arch: None,
        });
    }
    // PE (Windows): 'MZ'; e_lfanew (u32 LE) at 0x3C points to the PE header; COFF Machine (u16 LE)
    // sits at PE+4.
    if bytes.starts_with(b"MZ") && bytes.len() >= 0x40 {
        let pe_off =
            u32::from_le_bytes([bytes[0x3C], bytes[0x3D], bytes[0x3E], bytes[0x3F]]) as usize;
        if pe_off.checked_add(6).is_some_and(|end| end <= bytes.len())
            && bytes[pe_off..].starts_with(b"PE\x00\x00")
        {
            let machine = u16::from_le_bytes([bytes[pe_off + 4], bytes[pe_off + 5]]);
            let arch = match machine {
                0x8664 => Some("x86_64"),  // IMAGE_FILE_MACHINE_AMD64
                0xAA64 => Some("aarch64"), // IMAGE_FILE_MACHINE_ARM64
                _ => None,
            };
            return Some(StagedTarget {
                os: "windows",
                arch,
            });
        }
        return Some(StagedTarget {
            os: "windows",
            arch: None,
        });
    }
    None
}

/// Guard against pinning+bundling a native binary built for a *different* OS/CPU than the build
/// target (`cargo build --target …`). A BLAKE3 pin proves byte-identity, not runnability, so without
/// this a release bundle could ship e.g. an arm64 `age` into an x86_64 app that fails at first launch
/// — the named M-4 risk, since the dev-host `binaries/age` is arm64. We read the header only (no
/// execution). A *positively identified* OS/arch mismatch **fails a release build of a mandatory
/// binary** (consistent with the missing-binary guard) and **warns** for debug builds or optional
/// binaries; an unrecognized format (the ExifTool Perl script) or an unmodeled target OS is left
/// untouched to avoid false positives.
fn check_staged_arch(name: &str, path: &Path, bytes: &[u8], mandatory: Mandatory) {
    let Ok(target_os) = std::env::var("CARGO_CFG_TARGET_OS") else {
        return;
    };
    let Ok(target_arch) = std::env::var("CARGO_CFG_TARGET_ARCH") else {
        return;
    };
    // Only reason about the desktop OSes whose executable format we model; skip anything else.
    if !matches!(target_os.as_str(), "macos" | "linux" | "windows") {
        return;
    }
    let Some(staged) = detect_staged_target(bytes) else {
        return; // arch-independent (e.g. a Perl script) or unrecognized — nothing to compare
    };

    let os_mismatch = staged.os != target_os;
    let arch_mismatch = !os_mismatch && staged.arch.is_some_and(|a| a != target_arch);
    if !os_mismatch && !arch_mismatch {
        return;
    }

    let detail = format!(
        "{name} at {} is a {}/{} binary but the build target is {target_os}/{target_arch}",
        path.display(),
        staged.os,
        staged.arch.unwrap_or("any"),
    );
    let is_release = std::env::var("PROFILE")
        .map(|p| p == "release")
        .unwrap_or(false);
    if mandatory == Mandatory::Yes && is_release {
        panic!(
            "secure-vault: release build would bundle a wrong-architecture binary — {detail}. The \
             BLAKE3 pin cannot catch this; the app would fail at first launch. Stage the \
             {target_os}/{target_arch} build of the binary (or build natively for the host)."
        );
    }
    println!(
        "cargo:warning=secure-vault: {detail} — the bundle would not run on the target. Place a \
         matching binary in binaries/ (or point the SV_*_BIN_SRC override at one)."
    );
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

fn emit_pin(stem: &str, out_env: &str, src_override: &str, mandatory: Mandatory) {
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
        Ok(bytes) => {
            // Catch a wrong-OS/arch staged binary before pinning it (the pin would otherwise
            // "pass" on a binary that can't run on the target — audit M-4).
            check_staged_arch(&name, &path, &bytes, mandatory);
            blake3::hash(&bytes).to_hex().to_string()
        }
        Err(_) => {
            // A *release* build with a *mandatory* binary missing would package an installable
            // bundle that refuses to start at first launch (the runtime rejects an unpinned age in
            // release). Fail the build now instead — loudly and at the right layer.
            let is_release = std::env::var("PROFILE")
                .map(|p| p == "release")
                .unwrap_or(false);
            if mandatory == Mandatory::Yes && is_release {
                panic!(
                    "secure-vault: release build is missing the mandatory `{name}` at {} — refusing \
                     to produce a bundle that would fail at first launch. Place the binary there or \
                     set {src_override} (for a non-shipping compile, build in debug / `cargo tauri dev`).",
                    path.display()
                );
            }
            println!(
                "cargo:warning=secure-vault: no {name} at {} — building DEV-UNPINNED (a release build will refuse to run unpinned). Place the binary there or set {src_override}.",
                path.display()
            );
            "dev-unpinned".to_string()
        }
    };
    println!("cargo:rustc-env={out_env}={pin}");
}
