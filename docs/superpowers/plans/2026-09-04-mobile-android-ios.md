# SecureVault Mobile (Android + iOS) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship SecureVault on Android (built and verified here) and iOS (authored, unverified) reusing the existing audited Rust core, without changing desktop behaviour.

**Architecture:** One Tauri 2 crate (`app/`, renamed from `desktop/`) serves all platforms with `#[cfg(desktop)]` / `#[cfg(mobile)]` composition roots. Mobile swaps the vault payload cipher to a pure-Rust `age` implementation through the existing generic `VaultBackend<P: PayloadCipher>` seam, and brokers platform file URIs into sandbox paths in the shell so the frozen M0 contract and every `crates/` module stay untouched.

**Tech Stack:** Rust 1.96, Tauri 2, `age` 0.12.1 (pure Rust), Android NDK r28c + clang 19, Kotlin (`EncryptedSharedPreferences`), Swift (Keychain), vanilla JS/CSS frontend.

**Spec:** `docs/superpowers/specs/2026-09-04-mobile-android-ios-design.md`

## Global Constraints

- **Desktop must build and test green at the end of every task.** This is the standing regression gate for the whole port.
- Rust edition 2021, `rust-version = "1.96"`, workspace lints: `unsafe_code = "deny"`, `missing_debug_implementations = "warn"`.
- CI escalates warnings: `RUSTFLAGS="-D warnings"` and `cargo clippy -- -D warnings`. Code must be clippy-clean.
- New dependency licences must be on the `deny.toml` allowlist: MIT, Apache-2.0, Apache-2.0 WITH LLVM-exception, BSD-2-Clause, BSD-3-Clause, ISC, Unicode-3.0, Unicode-DFS-2016, CC0-1.0, Zlib, MPL-2.0.
- **No changes to `crates/sv-core`, `sv-crypto`, `sv-crypto-traits`, `sv-types`, `sv-platform`, `sv-stego`, `sv-qr`, `sv-watermark`.** The M0 contract is frozen.
- **Never** store passphrases, session keys, or age identities in Keystore/Keychain (spec D3).
- **Build host has 7.8 GB RAM, 4 CPUs, 2.1 GB swap, and no `/dev/kvm`.** `cargo test --workspace`
  at default parallelism was killed by the OOM killer. Every cargo invocation in this plan must
  cap jobs: `cargo … -j 2` (or `CARGO_BUILD_JOBS=2`). For the Gradle tasks, also set
  `org.gradle.jvmargs=-Xmx2g` and `org.gradle.daemon=false` in `app/gen/android/gradle.properties`,
  and do not run a cargo build concurrently with a Gradle build.
- Android NDK path: `/root/android/android-ndk-r28c`. API level 24.
- Android cross-compile env (every Android cargo invocation):
  ```
  TC=/root/android/android-ndk-r28c/toolchains/llvm/prebuilt/linux-x86_64/bin
  CC_aarch64_linux_android=$TC/aarch64-linux-android24-clang
  AR_aarch64_linux_android=$TC/llvm-ar
  CARGO_TARGET_AARCH64_LINUX_ANDROID_LINKER=$TC/aarch64-linux-android24-clang
  ```
- iOS deliverables are **authored, not verified** — this host has no Xcode. Never claim otherwise in code comments, docs, or commit messages.

---

## File Structure

| Path | Responsibility |
|---|---|
| `app/` | Renamed from `desktop/`. One Tauri crate, all platforms. |
| `app/src/lib.rs` | Shared `run()` + all 38 `#[tauri::command]` wrappers. Composition extracted out. |
| `app/src/compose/mod.rs` | `cfg` dispatch to the platform composition root. |
| `app/src/compose/desktop.rs` | `#[cfg(desktop)]` — today's pinned `age`/`exiftool` wiring, moved verbatim. |
| `app/src/compose/mobile.rs` | `#[cfg(mobile)]` — `RustAgePayloadCipher` + `MetaApp::disabled()`. |
| `app/src/broker/mod.rs` | `#[cfg(mobile)]` — URI ⇄ sandbox-path brokering, staging, shredding, space guard. |
| `app/plugins/svstore/` | First-party secure-storage plugin (Rust + Kotlin + Swift). |
| `crates/sv-age-rs/` | **New workspace crate.** `FileCipher` over the pure-Rust `age` crate. |
| `src-tauri/src/payload.rs` | Gains `RustAgePayloadCipher` alongside `AgePayloadCipher`. |
| `app/frontend/styles.css` | Gains a mobile layout block keyed off `data-platform="mobile"`. |
| `app/frontend/main.js` | Gains platform detection + drawer nav. No change to command logic. |
| `.github/workflows/ci.yml` | `desktop` job renamed `app`; new `android-core`, `ios-core`, `apk-verify` jobs. |

---

# PART A — Portable core

## Task 1: Rename `desktop/` → `app/`

**Files:**
- Modify: `Cargo.toml` (workspace `exclude`)
- Modify: `.github/workflows/ci.yml` (the `desktop` job)
- Modify: `README.md`, `desktop/README.md` → `app/README.md`
- Move: `desktop/` → `app/`

**Interfaces:**
- Consumes: nothing (first task)
- Produces: the `app/` crate path that every later task references. Crate name stays `secure-vault-desktop`, lib name stays `secure_vault_desktop_lib` — renaming the *crate* is out of scope and would churn `main.rs` and the Tauri config.

- [ ] **Step 1: Record the green baseline**

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research
cargo test --workspace 2>&1 | tail -5
cd desktop && cargo check 2>&1 | tail -3
```
Expected: workspace tests pass; `desktop` checks clean (3 pre-existing "DEV-UNPINNED" warnings about missing `age`/`age-keygen`/`exiftool` binaries are expected and fine).

- [ ] **Step 2: Move the directory**

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research
git mv desktop app
```

- [ ] **Step 3: Update the workspace exclude**

In `Cargo.toml`, change `exclude = ["desktop"]` to `exclude = ["app"]`, and update the comment above it that says "build it from `desktop/`" to say "build it from `app/`".

- [ ] **Step 4: Update path references**

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research
grep -rln "desktop/" --include="*.md" --include="*.yml" --include="*.toml" . | grep -v "^./docs/superpowers/" | grep -v "^./.git/"
```
Update each hit that refers to the crate directory (`desktop/src`, `desktop/frontend`, `cd desktop`, `working-directory: desktop`). **Do not** rewrite prose that legitimately means "the desktop platform", and do not touch `docs/superpowers/specs/` (that spec describes the rename and should keep reading as written).

- [ ] **Step 5: Rename the CI job**

In `.github/workflows/ci.yml`, rename the job key `desktop:` to `app:`, update its `name:` if present, and change every `working-directory: desktop` to `working-directory: app`.

- [ ] **Step 6: Verify nothing broke**

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research
cargo test --workspace 2>&1 | tail -5
cd app && cargo check 2>&1 | tail -3 && cargo clippy --all-targets -- -D warnings 2>&1 | tail -3
```
Expected: identical results to Step 1.

- [ ] **Step 7: Commit**

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research
git add -A
git commit -m "refactor: rename desktop/ to app/ for the shared multi-platform shell

The Tauri crate will serve desktop, Android and iOS from one codebase, so
the directory name no longer describes it. Mechanical move plus reference
updates; no behaviour change.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: `sv-age-rs` — pure-Rust `FileCipher`

**Files:**
- Create: `crates/sv-age-rs/Cargo.toml`
- Create: `crates/sv-age-rs/src/lib.rs`
- Modify: `Cargo.toml` (add workspace member)

**Interfaces:**
- Consumes: `sv_crypto_traits::{FileCipher, FileCipherAlg, AgeIdentity, AgeRecipient, CryptoError, SecretBytes}`
- Produces:
  - `sv_age_rs::RustAgeCipher` — unit struct, `RustAgeCipher::new() -> Self`, implements `FileCipher`
  - `sv_age_rs::generate_identity() -> Result<(Vec<u8>, String), CryptoError>` returning `(identity_file_bytes, recipient_string)`. The identity bytes are in `age-keygen` file format (comment lines plus one `AGE-SECRET-KEY-1…` line), byte-compatible with what `sv-age` writes to its temp file.

- [ ] **Step 1: Add the workspace member**

In the root `Cargo.toml`, add `"crates/sv-age-rs",` to `[workspace] members`, immediately after `"crates/sv-age",`.

- [ ] **Step 2: Create the crate manifest**

Create `crates/sv-age-rs/Cargo.toml`:

```toml
[package]
name = "sv-age-rs"
description = "FileCipher adapter over the pure-Rust `age` crate. In-process, no subprocess — the mobile payload cipher (desktop keeps the hash-pinned `age` binary)."
version.workspace = true
edition.workspace = true
rust-version.workspace = true
license.workspace = true
publish.workspace = true

[dependencies]
sv-crypto-traits = { path = "../sv-crypto-traits" }
# Pure-Rust reference implementation of the age spec, format-compatible with the Go binary
# `sv-age` drives on desktop. MIT OR Apache-2.0 (deny.toml allowlist).
age = { version = "0.12", default-features = false }
zeroize.workspace = true

[lints]
workspace = true
```

- [ ] **Step 3: Write the failing tests**

Create `crates/sv-age-rs/src/lib.rs` with only the test module first (so the crate compiles but the tests fail to resolve items):

```rust
//! # sv-age-rs — [`FileCipher`] over the pure-Rust `age` crate
//!
//! Mobile cannot spawn subprocesses (iOS forbids it; Android blocks exec of app-writable
//! binaries), so the vault payload cipher runs in-process here. The wire format is age v1,
//! identical to the Go `age` binary `sv-age` drives on desktop — vaults interoperate.
//!
//! Desktop deliberately keeps the hash-pinned subprocess (see `docs/M7-HARDENING.md`); this
//! adapter is the mobile composition root's cipher only.

#![forbid(unsafe_code)]

#[cfg(test)]
mod tests {
    use super::*;
    use sv_crypto_traits::{AgeIdentity, AgeRecipient, CryptoError, FileCipher, SecretBytes};

    #[test]
    fn round_trips_a_payload() {
        let (id_bytes, recipient) = generate_identity().unwrap();
        let cipher = RustAgeCipher::new();

        let plaintext = b"secure vault payload".to_vec();
        let mut ct = Vec::new();
        cipher
            .encrypt(
                &mut plaintext.as_slice(),
                &mut ct,
                &AgeRecipient(recipient),
            )
            .unwrap();
        assert_ne!(ct, plaintext, "ciphertext must not equal plaintext");

        let mut out = Vec::new();
        cipher
            .decrypt(
                &mut ct.as_slice(),
                &mut out,
                &AgeIdentity::new(SecretBytes::new(id_bytes)),
            )
            .unwrap();
        assert_eq!(out, plaintext);
    }

    #[test]
    fn decrypt_with_wrong_identity_fails_verification() {
        let (_id_a, recipient_a) = generate_identity().unwrap();
        let (id_b, _recipient_b) = generate_identity().unwrap();
        let cipher = RustAgeCipher::new();

        let mut ct = Vec::new();
        cipher
            .encrypt(&mut b"secret".as_slice(), &mut ct, &AgeRecipient(recipient_a))
            .unwrap();

        let mut out = Vec::new();
        let err = cipher
            .decrypt(
                &mut ct.as_slice(),
                &mut out,
                &AgeIdentity::new(SecretBytes::new(id_b)),
            )
            .unwrap_err();
        assert!(
            matches!(err, CryptoError::VerificationFailed),
            "wrong identity must be VerificationFailed, got {err:?}"
        );
    }

    #[test]
    fn rejects_a_malformed_recipient() {
        let cipher = RustAgeCipher::new();
        let mut ct = Vec::new();
        let err = cipher
            .encrypt(
                &mut b"x".as_slice(),
                &mut ct,
                &AgeRecipient("not-an-age-recipient".to_string()),
            )
            .unwrap_err();
        assert!(matches!(err, CryptoError::InvalidParameter(_)), "got {err:?}");
    }

    #[test]
    fn generated_identity_is_age_keygen_shaped() {
        let (id_bytes, recipient) = generate_identity().unwrap();
        let text = String::from_utf8(id_bytes).unwrap();
        assert!(text.contains("AGE-SECRET-KEY-1"), "missing secret key line");
        assert!(text.contains(&recipient), "identity file must carry its public key comment");
        assert!(recipient.starts_with("age1"), "recipient must be bech32 age1…");
    }
}
```

- [ ] **Step 4: Run the tests to verify they fail**

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research
cargo test -p sv-age-rs 2>&1 | tail -20
```
Expected: FAIL — `cannot find function generate_identity`, `cannot find type RustAgeCipher`.

- [ ] **Step 5: Write the implementation**

Insert this above the `#[cfg(test)] mod tests` block in `crates/sv-age-rs/src/lib.rs`:

```rust
use std::io::{BufReader, Read, Write};
use std::iter;

use sv_crypto_traits::{AgeIdentity, AgeRecipient, CryptoError, FileCipher, FileCipherAlg};
use zeroize::Zeroize;

/// Generate a fresh age keypair, returned as `(identity_file_bytes, recipient_string)`.
///
/// The identity bytes replicate `age-keygen`'s file format — two comment lines then the
/// secret key — so the value stored in an [`AgeIdentity`] is byte-compatible with what the
/// desktop (`sv-age`) path produces and consumes.
pub fn generate_identity() -> Result<(Vec<u8>, String), CryptoError> {
    let id = age::x25519::Identity::generate();
    let recipient = id.to_public().to_string();

    // `to_string()` returns a SecretString; copy it out, then zeroize the interim String.
    let mut secret = id.to_string().expose_secret().to_owned();
    let mut file = format!(
        "# created by SecureVault\n# public key: {recipient}\n{secret}\n"
    );
    secret.zeroize();

    let bytes = file.as_bytes().to_vec();
    file.zeroize();
    Ok((bytes, recipient))
}

/// In-process age v1 cipher. Stateless.
#[derive(Debug, Clone, Copy, Default)]
pub struct RustAgeCipher;

impl RustAgeCipher {
    #[must_use]
    pub fn new() -> Self {
        Self
    }
}

impl FileCipher for RustAgeCipher {
    fn alg(&self) -> FileCipherAlg {
        FileCipherAlg::AgeV1
    }

    fn encrypt(
        &self,
        plaintext: &mut dyn Read,
        ciphertext: &mut dyn Write,
        recipient: &AgeRecipient,
    ) -> Result<(), CryptoError> {
        let rec: age::x25519::Recipient = recipient
            .0
            .parse()
            .map_err(|e| CryptoError::InvalidParameter(format!("recipient: {e}")))?;

        let encryptor = age::Encryptor::with_recipients(iter::once(&rec as &dyn age::Recipient))
            .map_err(|e| CryptoError::Backend(format!("age encryptor: {e}")))?;

        let mut writer = encryptor
            .wrap_output(ciphertext)
            .map_err(|e| CryptoError::Backend(format!("age wrap: {e}")))?;

        let mut buf = Vec::new();
        plaintext
            .read_to_end(&mut buf)
            .map_err(|e| CryptoError::Backend(format!("read plaintext: {e}")))?;
        let write_result = writer.write_all(&buf);
        buf.zeroize();
        write_result.map_err(|e| CryptoError::Backend(format!("age write: {e}")))?;

        writer
            .finish()
            .map_err(|e| CryptoError::Backend(format!("age finish: {e}")))?;
        Ok(())
    }

    fn decrypt(
        &self,
        ciphertext: &mut dyn Read,
        plaintext: &mut dyn Write,
        identity: &AgeIdentity,
    ) -> Result<(), CryptoError> {
        let ids = age::IdentityFile::from_buffer(BufReader::new(identity.expose_secret()))
            .map_err(|e| CryptoError::InvalidParameter(format!("identity file: {e}")))?
            .into_identities()
            .map_err(|e| CryptoError::InvalidParameter(format!("identity parse: {e}")))?;

        let decryptor = age::Decryptor::new(ciphertext)
            .map_err(|e| CryptoError::Backend(format!("age header: {e}")))?;

        // A wrong identity is an authentication failure, matching sv-age's contract exactly.
        let mut reader = decryptor
            .decrypt(ids.iter().map(|i| i.as_ref() as &dyn age::Identity))
            .map_err(|e| match e {
                age::DecryptError::NoMatchingKeys | age::DecryptError::DecryptionFailed => {
                    CryptoError::VerificationFailed
                }
                other => CryptoError::Backend(format!("age decrypt: {other}")),
            })?;

        let mut buf = Vec::new();
        reader
            .read_to_end(&mut buf)
            .map_err(|e| CryptoError::Backend(format!("age read: {e}")))?;
        let write_result = plaintext.write_all(&buf);
        buf.zeroize();
        write_result.map_err(|e| CryptoError::Backend(format!("write plaintext: {e}")))?;
        Ok(())
    }
}
```

Note on `expose_secret()`: `age::secrecy::SecretString` exposes via `expose_secret()`. If the
compiler reports the trait is not in scope, add `use age::secrecy::ExposeSecret;` to the
imports — the `age` crate re-exports `secrecy`.

- [ ] **Step 6: Run the tests to verify they pass**

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research
cargo test -p sv-age-rs 2>&1 | tail -15
```
Expected: PASS, 4 tests.

- [ ] **Step 7: Clippy and licence gate**

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research
cargo clippy -p sv-age-rs --all-targets -- -D warnings 2>&1 | tail -5
cargo deny check licenses 2>&1 | tail -10
```
Expected: clippy clean; `cargo deny` reports no licence violations. If `cargo deny` is not installed, run `cargo install cargo-deny --locked` first.

- [ ] **Step 8: Commit**

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research
git add crates/sv-age-rs Cargo.toml Cargo.lock
git commit -m "feat(sv-age-rs): pure-Rust age FileCipher for the mobile payload path

Mobile cannot spawn subprocesses, so the vault payload cipher runs in
process there. age v1 wire format, so vaults interoperate with the
desktop path unchanged. Desktop keeps its hash-pinned age binary.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: Prove cross-implementation format compatibility

The whole design rests on the claim that a desktop-written vault opens on mobile. That claim
must be tested against the **real Go binary**, not asserted.

**Files:**
- Create: `app/binaries/README.md` is already present; place binaries alongside it
- Create: `crates/sv-age-rs/tests/interop.rs`

**Interfaces:**
- Consumes: `sv_age_rs::{RustAgeCipher, generate_identity}` from Task 2
- Produces: an ignored-by-default integration test `interop_go_to_rust` / `interop_rust_to_go`, run explicitly when the `age` binary is available.

- [ ] **Step 1: Fetch the real `age` binaries, and record what was fetched**

This project BLAKE3-pins these binaries as a documented tamper-evidence control
(`docs/M7-HARDENING.md`), so pulling an unverified executable off the network would
contradict its own threat model. age publishes **Sigsum transparency proofs** (`.proof`)
rather than plain checksums; full verification needs `sigsum-verify`, which is out of scope
here. The proportionate substitute: fetch the proof alongside the tarball, record the digest
of exactly what was downloaded, and keep both so a reviewer can verify independently later.

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research
mkdir -p app/binaries
BASE=https://github.com/FiloSottile/age/releases/download/v1.2.1
curl -sSL -o /tmp/age.tgz       "$BASE/age-v1.2.1-linux-amd64.tar.gz"
curl -sSL -o /tmp/age.tgz.proof "$BASE/age-v1.2.1-linux-amd64.tar.gz.proof"

# Record the digest of what actually arrived, before anything is extracted or executed.
sha256sum /tmp/age.tgz | tee app/binaries/DOWNLOADED-SHA256
cp /tmp/age.tgz.proof app/binaries/age-v1.2.1-linux-amd64.tar.gz.proof

tar -xzf /tmp/age.tgz -C /tmp
cp /tmp/age/age /tmp/age/age-keygen app/binaries/
chmod +x app/binaries/age app/binaries/age-keygen
app/binaries/age --version && app/binaries/age-keygen --version
sha256sum app/binaries/age app/binaries/age-keygen | tee -a app/binaries/DOWNLOADED-SHA256
```
Expected: both print `v1.2.1`, and `DOWNLOADED-SHA256` records the tarball and both extracted
binaries.

The authoritative control remains the project's own: `app/build.rs` BLAKE3-hashes these at
build time and embeds the pin, and a release build refuses to run unpinned. This step only
ensures we know precisely which bytes entered that process.

`app/binaries/` is already gitignored — confirm with `git check-ignore app/binaries/age`. The
binaries must never be committed, but **do** commit `DOWNLOADED-SHA256` and the `.proof` file
(add a negated ignore rule if needed): they are the provenance record, not the payload.

- [ ] **Step 2: Write the failing interop test**

Create `crates/sv-age-rs/tests/interop.rs`:

```rust
//! Cross-implementation format compatibility: the Go `age` binary and this pure-Rust adapter
//! must read each other's ciphertext. This is the test behind the design claim that a vault
//! written on desktop opens on mobile.
//!
//! Ignored by default because it needs the real `age` binary. Run with:
//!   SV_AGE_BIN=app/binaries/age SV_AGE_KEYGEN_BIN=app/binaries/age-keygen \
//!     cargo test -p sv-age-rs --test interop -- --ignored --nocapture

use std::io::Write;
use std::process::{Command, Stdio};

use sv_age_rs::{generate_identity, RustAgeCipher};
use sv_crypto_traits::{AgeIdentity, AgeRecipient, FileCipher, SecretBytes};

fn bin(var: &str) -> Option<String> {
    std::env::var(var).ok()
}

#[test]
#[ignore = "requires the real age binary; see module docs"]
fn rust_ciphertext_decrypts_with_go_age() {
    let age_bin = bin("SV_AGE_BIN").expect("SV_AGE_BIN not set");

    let (id_bytes, recipient) = generate_identity().unwrap();
    let plaintext = b"interop payload".to_vec();

    let mut ct = Vec::new();
    RustAgeCipher::new()
        .encrypt(&mut plaintext.as_slice(), &mut ct, &AgeRecipient(recipient))
        .unwrap();

    // Write the Rust-generated identity to a temp file and hand the ciphertext to Go age.
    let dir = std::env::temp_dir().join(format!("svinterop{}", std::process::id()));
    std::fs::create_dir_all(&dir).unwrap();
    let id_path = dir.join("id.txt");
    std::fs::write(&id_path, &id_bytes).unwrap();

    let mut child = Command::new(&age_bin)
        .args(["-d", "-i"])
        .arg(&id_path)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .spawn()
        .unwrap();
    child.stdin.as_mut().unwrap().write_all(&ct).unwrap();
    let out = child.wait_with_output().unwrap();
    std::fs::remove_dir_all(&dir).ok();

    assert!(out.status.success(), "go age failed: {}", String::from_utf8_lossy(&out.stderr));
    assert_eq!(out.stdout, plaintext, "Go age must decrypt Rust ciphertext");
}

#[test]
#[ignore = "requires the real age binary; see module docs"]
fn go_ciphertext_decrypts_with_rust() {
    let age_bin = bin("SV_AGE_BIN").expect("SV_AGE_BIN not set");
    let keygen_bin = bin("SV_AGE_KEYGEN_BIN").expect("SV_AGE_KEYGEN_BIN not set");

    // Generate the identity with the real age-keygen — the exact desktop production path.
    let kg = Command::new(&keygen_bin).output().unwrap();
    assert!(kg.status.success());
    let id_bytes = kg.stdout;
    let text = String::from_utf8_lossy(&id_bytes);
    let recipient = text
        .lines()
        .find_map(|l| l.strip_prefix("# public key: "))
        .expect("age-keygen must print the public key")
        .trim()
        .to_string();

    let plaintext = b"interop payload".to_vec();
    let mut child = Command::new(&age_bin)
        .args(["-r", &recipient])
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .spawn()
        .unwrap();
    child.stdin.as_mut().unwrap().write_all(&plaintext).unwrap();
    let enc = child.wait_with_output().unwrap();
    assert!(enc.status.success(), "go age encrypt failed");

    let mut out = Vec::new();
    RustAgeCipher::new()
        .decrypt(
            &mut enc.stdout.as_slice(),
            &mut out,
            &AgeIdentity::new(SecretBytes::new(id_bytes)),
        )
        .unwrap();
    assert_eq!(out, plaintext, "Rust must decrypt Go age ciphertext");
}
```

- [ ] **Step 3: Run the tests to verify they fail without the binary**

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research
cargo test -p sv-age-rs --test interop -- --ignored 2>&1 | tail -10
```
Expected: FAIL — `SV_AGE_BIN not set`. This proves the tests actually execute rather than silently skipping.

- [ ] **Step 4: Run them properly and verify they pass**

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research
SV_AGE_BIN=$PWD/app/binaries/age SV_AGE_KEYGEN_BIN=$PWD/app/binaries/age-keygen \
  cargo test -p sv-age-rs --test interop -- --ignored --nocapture 2>&1 | tail -12
```
Expected: PASS, 2 tests. **If either fails, stop.** The design's interoperability claim is false and the spec needs revisiting before any further work.

- [ ] **Step 5: Commit**

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research
git add crates/sv-age-rs/tests/interop.rs
git commit -m "test(sv-age-rs): prove Go/Rust age format interoperability

Bidirectional ciphertext exchange with the real age v1.2.1 binary. This
is the evidence behind the claim that a vault written on desktop opens on
mobile and vice versa.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: `RustAgePayloadCipher` in `sv-app`

**Files:**
- Modify: `src-tauri/src/payload.rs`
- Modify: `src-tauri/Cargo.toml` (add `sv-age-rs` dependency)
- Modify: `src-tauri/src/lib.rs` (re-export)

**Interfaces:**
- Consumes: `sv_age_rs::{RustAgeCipher, generate_identity}` (Task 2)
- Produces: `sv_app::RustAgePayloadCipher` — `RustAgePayloadCipher::new() -> Self`, implements the existing `PayloadCipher` trait (`generate_identity`, `encrypt`, `decrypt`). Usable as `AppVault<RustAgePayloadCipher>`.

- [ ] **Step 1: Add the dependency**

In `src-tauri/Cargo.toml`, under `[dependencies]`, after the `sv-age` line:

```toml
# Pure-Rust age adapter — the mobile payload cipher (no subprocess). Always compiled; the
# composition root chooses which cipher to instantiate per platform.
sv-age-rs = { path = "../crates/sv-age-rs" }
```

- [ ] **Step 2: Write the failing test**

Append to the `#[cfg(test)] mod tests` block at the bottom of `src-tauri/src/payload.rs` (create the block if absent):

```rust
#[test]
fn rust_payload_cipher_round_trips() {
    let cipher = RustAgePayloadCipher::new();
    let (identity, recipient) = cipher.generate_identity().unwrap();
    let plaintext = b"vault payload".to_vec();

    let ct = cipher.encrypt(&plaintext, &recipient).unwrap();
    assert_ne!(ct, plaintext);

    let out = cipher.decrypt(&ct, &identity).unwrap();
    assert_eq!(out, plaintext);
}

#[test]
fn rust_payload_cipher_rejects_a_foreign_identity() {
    let cipher = RustAgePayloadCipher::new();
    let (_id_a, recipient_a) = cipher.generate_identity().unwrap();
    let (id_b, _recipient_b) = cipher.generate_identity().unwrap();

    let ct = cipher.encrypt(b"secret", &recipient_a).unwrap();
    assert!(
        cipher.decrypt(&ct, &id_b).is_err(),
        "a foreign identity must not decrypt the payload"
    );
}
```

- [ ] **Step 3: Run to verify it fails**

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research
cargo test -p sv-app payload 2>&1 | tail -10
```
Expected: FAIL — `cannot find type RustAgePayloadCipher`.

- [ ] **Step 4: Implement**

Add to `src-tauri/src/payload.rs`, after the `AgePayloadCipher` implementation:

```rust
/// Mobile payload cipher: the pure-Rust age adapter, in-process.
///
/// iOS forbids spawning executables and Android blocks exec of app-writable binaries, so the
/// desktop `AgePayloadCipher` (bundled, hash-pinned `age` + `age-keygen` subprocesses) cannot
/// run there. The wire format is identical age v1, so vaults interoperate across platforms.
#[derive(Debug, Clone, Copy, Default)]
pub struct RustAgePayloadCipher;

impl RustAgePayloadCipher {
    #[must_use]
    pub fn new() -> Self {
        Self
    }
}

impl PayloadCipher for RustAgePayloadCipher {
    fn generate_identity(&self) -> Result<(AgeIdentity, AgeRecipient), VaultError> {
        let (id_bytes, recipient) =
            sv_age_rs::generate_identity().map_err(|_| VaultError::Internal)?;
        Ok((
            AgeIdentity::new(SecretBytes::new(id_bytes)),
            AgeRecipient(recipient),
        ))
    }

    fn encrypt(&self, plaintext: &[u8], recipient: &AgeRecipient) -> Result<Vec<u8>, VaultError> {
        let mut out = Vec::new();
        sv_age_rs::RustAgeCipher::new()
            .encrypt(&mut Cursor::new(plaintext), &mut out, recipient)
            .map_err(map_crypto_err)?;
        Ok(out)
    }

    fn decrypt(&self, ciphertext: &[u8], identity: &AgeIdentity) -> Result<Vec<u8>, VaultError> {
        let mut out = Vec::new();
        sv_age_rs::RustAgeCipher::new()
            .decrypt(&mut Cursor::new(ciphertext), &mut out, identity)
            .map_err(map_crypto_err)?;
        Ok(out)
    }
}

/// Project a [`CryptoError`] onto the vault's error taxonomy, preserving the
/// wrong-key/corrupt-payload distinction the UI relies on.
fn map_crypto_err(e: CryptoError) -> VaultError {
    match e {
        CryptoError::VerificationFailed => VaultError::AuthenticationFailed,
        _ => VaultError::Internal,
    }
}
```

Add `SecretBytes` to the existing `sv_crypto_traits` import line at the top of the file if it
is not already there. If `VaultError::AuthenticationFailed` is not the exact variant name,
run `grep -n "pub enum VaultError" -A 20 crates/sv-core/src/lib.rs` and use the variant that
`AgeCipher`'s wrong-identity path maps to — the two ciphers must agree.

- [ ] **Step 5: Re-export from the crate root**

In `src-tauri/src/lib.rs`, change:
```rust
pub use payload::{AgePayloadCipher, PayloadCipher};
```
to:
```rust
pub use payload::{AgePayloadCipher, PayloadCipher, RustAgePayloadCipher};
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research
cargo test -p sv-app 2>&1 | tail -10
cargo clippy -p sv-app --all-targets -- -D warnings 2>&1 | tail -5
```
Expected: all `sv-app` tests pass including the two new ones; clippy clean.

- [ ] **Step 7: Prove a desktop-written vault opens with the mobile cipher**

This is the claim the whole design rests on, at the level users care about: a `.svault`, not
an age blob. Create `src-tauri/tests/vault_interop.rs`:

```rust
//! A vault created through the desktop cipher (bundled `age` subprocess) must open through
//! the mobile cipher (in-process pure Rust), and vice versa. This is the user-visible form
//! of the format-compatibility claim in the design spec §3.1.
//!
//! Ignored by default — needs the real age binaries. Run with:
//!   SV_AGE_BIN=app/binaries/age SV_AGE_KEYGEN_BIN=app/binaries/age-keygen \
//!     cargo test -p sv-app --test vault_interop -- --ignored --nocapture

use std::path::PathBuf;

use sv_app::{AgePayloadCipher, IpcPassphrase, RustAgePayloadCipher, VaultBackend};

fn desktop_cipher() -> AgePayloadCipher {
    let age = PathBuf::from(std::env::var("SV_AGE_BIN").expect("SV_AGE_BIN not set"));
    let keygen = PathBuf::from(std::env::var("SV_AGE_KEYGEN_BIN").expect("SV_AGE_KEYGEN_BIN"));
    AgePayloadCipher::new(
        sv_age::AgeCipher::new_unpinned(&age).expect("age binary"),
        keygen,
    )
}

#[test]
#[ignore = "requires the real age binaries; see module docs"]
fn desktop_written_vault_opens_with_the_mobile_cipher() {
    let dir = tempfile::tempdir().unwrap();
    let path = dir.path().join("interop.svault");
    let pass = "correct horse battery staple";

    // Create and populate through the DESKTOP cipher.
    let desktop = VaultBackend::new(desktop_cipher());
    desktop
        .vault_create(
            path.to_string_lossy().into_owned(),
            IpcPassphrase::from(pass.to_string()),
            None,
        )
        .expect("create with desktop cipher");

    // Open the very same file through the MOBILE cipher.
    let mobile = VaultBackend::new(RustAgePayloadCipher::new());
    let session = mobile
        .vault_unlock(
            path.to_string_lossy().into_owned(),
            IpcPassphrase::from(pass.to_string()),
        )
        .expect("a desktop-written vault must open with the mobile cipher");

    let meta = mobile.vault_meta(session).expect("meta readable");
    assert_eq!(meta.item_count, 0);
}

#[test]
#[ignore = "requires the real age binaries; see module docs"]
fn mobile_written_vault_opens_with_the_desktop_cipher() {
    let dir = tempfile::tempdir().unwrap();
    let path = dir.path().join("interop2.svault");
    let pass = "correct horse battery staple";

    let mobile = VaultBackend::new(RustAgePayloadCipher::new());
    mobile
        .vault_create(
            path.to_string_lossy().into_owned(),
            IpcPassphrase::from(pass.to_string()),
            None,
        )
        .expect("create with mobile cipher");

    let desktop = VaultBackend::new(desktop_cipher());
    let session = desktop
        .vault_unlock(
            path.to_string_lossy().into_owned(),
            IpcPassphrase::from(pass.to_string()),
        )
        .expect("a mobile-written vault must open with the desktop cipher");

    assert!(desktop.vault_meta(session).is_ok());
}
```

Add `tempfile = "3"` to `src-tauri/Cargo.toml` `[dev-dependencies]` if not already present,
and `sv-age = { path = "../crates/sv-age" }` is already a dependency.

Adapt the constructor and method names to the real `VaultBackend` API — read
`src-tauri/src/service.rs` and `src-tauri/src/lib.rs` first and mirror the signatures exactly
rather than trusting the sketch above. `IpcPassphrase`'s constructor in particular may be
`IpcPassphrase::new(String)` rather than `From<String>`.

Run it:

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research
SV_AGE_BIN=$PWD/app/binaries/age SV_AGE_KEYGEN_BIN=$PWD/app/binaries/age-keygen \
  cargo test -p sv-app --test vault_interop -- --ignored --nocapture 2>&1 | tail -15
```
Expected: PASS, 2 tests. **If either fails, stop and revisit the spec** — cross-platform vault
portability is the central claim of the whole design.

- [ ] **Step 8: Commit**

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research
git add src-tauri Cargo.lock
git commit -m "feat(sv-app): add RustAgePayloadCipher for the mobile composition

Second implementation of the existing PayloadCipher seam, backed by
sv-age-rs. Desktop continues to use AgePayloadCipher unchanged; the
composition root selects per platform.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: Split the composition root

**Files:**
- Create: `app/src/compose/mod.rs`
- Create: `app/src/compose/desktop.rs`
- Create: `app/src/compose/mobile.rs`
- Modify: `app/src/lib.rs`

**Interfaces:**
- Consumes: `sv_app::{AppVault, AgePayloadCipher, RustAgePayloadCipher, MetaApp}` (Task 4)
- Produces:
  - `compose::backend(app: &tauri::AppHandle) -> Result<Backend, String>`
  - `compose::meta(app: &tauri::AppHandle) -> MetaApp`
  - `compose::Backend` — a platform-specific type alias: `AppVault<AgePayloadCipher>` on desktop, `AppVault<RustAgePayloadCipher>` on mobile. `app/src/lib.rs` refers to it only through this alias.

- [ ] **Step 1: Create the dispatch module**

Create `app/src/compose/mod.rs`:

```rust
//! Platform composition roots.
//!
//! The **only** place where desktop and mobile diverge. Desktop resolves and BLAKE3-verifies
//! the bundled `age`/`age-keygen`/`exiftool` binaries exactly as before; mobile cannot spawn
//! subprocesses at all, so it composes the in-process cipher and a disabled Analysis module.
//!
//! Everything below this boundary — the command surface, the vault format, the crypto, the
//! error taxonomy — is identical on every platform.

#[cfg(desktop)]
mod desktop;
#[cfg(mobile)]
mod mobile;

#[cfg(desktop)]
pub use desktop::{backend, meta, Backend};
#[cfg(mobile)]
pub use mobile::{backend, meta, Backend};
```

- [ ] **Step 2: Move the desktop composition verbatim**

Create `app/src/compose/desktop.rs` and move into it, **unchanged**, these items currently in
`app/src/lib.rs`: the `Backend` and `Meta` type aliases, `build_backend`, `build_meta`,
`resolve_binary`, and the `AGE_PIN` / `EXIFTOOL_PIN` constants. Rename `build_backend` to
`backend` and `build_meta` to `meta`, and make both `pub(crate)`. Add at the top:

```rust
//! Desktop composition root — unchanged behaviour.
//!
//! Resolves the bundled `age`, `age-keygen` and `exiftool`, verifying each against its
//! build-time BLAKE3 pin (M3 tamper-evidence, `docs/M7-HARDENING.md`). A missing or
//! mismatched ExifTool disables the Analysis module fail-closed rather than failing the app.
```

- [ ] **Step 3: Write the mobile composition**

Create `app/src/compose/mobile.rs`:

```rust
//! Mobile composition root.
//!
//! No subprocess is possible here: iOS forbids spawning executables, and Android blocks exec
//! of app-writable binaries. Consequences:
//!   • the vault payload cipher is the in-process `RustAgePayloadCipher` (same age v1 format,
//!     so vaults interoperate with desktop);
//!   • the Analysis module is composed **disabled** — `MetaApp::disabled()` is the same
//!     fail-closed state desktop uses when its pinned ExifTool is absent, so the frontend's
//!     existing `metadata_available` probe disables those screens with no new code.

use sv_app::{AppVault, MetaApp, RustAgePayloadCipher};

pub type Backend = AppVault<RustAgePayloadCipher>;

/// Compose the vault backend. Infallible on mobile — there is nothing to resolve or pin.
pub fn backend(_app: &tauri::AppHandle) -> Result<Backend, String> {
    Ok(AppVault::new(sv_app::VaultBackend::new(
        RustAgePayloadCipher::new(),
    )))
}

/// The Analysis module cannot exist on mobile (ExifTool is Perl). Fail closed.
pub fn meta(_app: &tauri::AppHandle) -> MetaApp {
    MetaApp::disabled()
}
```

If `AppVault::new` takes different arguments, mirror exactly what `compose/desktop.rs` does,
substituting `RustAgePayloadCipher::new()` for the `AgePayloadCipher::new(...)` expression.

- [ ] **Step 4: Wire it into `lib.rs`**

In `app/src/lib.rs`: add `mod compose;` near the other module declarations, delete the moved
items, and in the `setup` hook replace the calls to `build_backend(...)` / `build_meta(...)`
with `compose::backend(app.handle())` / `compose::meta(app.handle())`. Replace the local
`type Backend = ...` with `use compose::Backend;`.

- [ ] **Step 5: Verify desktop is unchanged**

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research/app
cargo check 2>&1 | tail -5
cargo clippy --all-targets -- -D warnings 2>&1 | tail -5
cargo test 2>&1 | tail -5
```
Expected: identical to the Task 1 baseline — same 3 DEV-UNPINNED warnings, tests green.

- [ ] **Step 6: Verify the mobile composition compiles**

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research/app
TC=/root/android/android-ndk-r28c/toolchains/llvm/prebuilt/linux-x86_64/bin
CC_aarch64_linux_android=$TC/aarch64-linux-android24-clang \
AR_aarch64_linux_android=$TC/llvm-ar \
CARGO_TARGET_AARCH64_LINUX_ANDROID_LINKER=$TC/aarch64-linux-android24-clang \
  cargo check --target aarch64-linux-android 2>&1 | tail -15
```
Expected: clean. Tauri sets the `mobile` cfg for Android/iOS targets, so `compose/mobile.rs`
is what compiles here. If the `mobile` cfg is not recognised, add to `app/build.rs`:
`println!("cargo:rustc-check-cfg=cfg(mobile)");` and confirm `tauri-build` emits it.

- [ ] **Step 7: Commit**

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research
git add app/src
git commit -m "refactor(app): split the composition root per platform

Desktop wiring moves verbatim into compose/desktop.rs; compose/mobile.rs
adds the subprocess-free composition. This is the only file where the
platforms diverge — everything below the command surface is identical.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

## Task 6: CI — Android cross-compile and ARM64 core tests

**Files:**
- Modify: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: the `app/` path from Task 1
- Produces: CI jobs `android-core` and `android-arm64-tests`. No code interface.

- [ ] **Step 1: Add the cross-compile job**

Append to `.github/workflows/ci.yml` under `jobs:`:

```yaml
  android-core:
    name: Android core cross-compile
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
        with:
          targets: aarch64-linux-android,x86_64-linux-android
      - uses: nttld/setup-ndk@v1
        id: ndk
        with:
          ndk-version: r28c
      - name: Cross-compile the audited core for Android
        env:
          NDK: ${{ steps.ndk.outputs.ndk-path }}
        run: |
          TC="$NDK/toolchains/llvm/prebuilt/linux-x86_64/bin"
          for t in aarch64-linux-android x86_64-linux-android; do
            case "$t" in
              aarch64*) CLANG="$TC/aarch64-linux-android24-clang" ;;
              x86_64*)  CLANG="$TC/x86_64-linux-android24-clang" ;;
            esac
            env \
              "CC_${t//-/_}=$CLANG" \
              "AR_${t//-/_}=$TC/llvm-ar" \
              "CARGO_TARGET_$(echo "$t" | tr 'a-z-' 'A-Z_')_LINKER=$CLANG" \
              cargo build --workspace --locked --target "$t"
          done
```

- [ ] **Step 2: Add the ARM64 test-execution job**

```yaml
  android-arm64-tests:
    name: Core test suite on ARM64 (QEMU)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
        with:
          targets: aarch64-unknown-linux-gnu
      - name: Install cross toolchain and QEMU
        run: |
          sudo apt-get update
          sudo apt-get install -y gcc-aarch64-linux-gnu qemu-user-static
      - name: Run the core suite on ARM64
        env:
          CARGO_TARGET_AARCH64_UNKNOWN_LINUX_GNU_LINKER: aarch64-linux-gnu-gcc
          CARGO_TARGET_AARCH64_UNKNOWN_LINUX_GNU_RUNNER: qemu-aarch64-static -L /usr/aarch64-linux-gnu
          CC_aarch64_unknown_linux_gnu: aarch64-linux-gnu-gcc
        run: cargo test --workspace --locked --target aarch64-unknown-linux-gnu
```

Note the deliberate choice of `aarch64-unknown-linux-gnu` rather than the Android triple:
Android binaries link against bionic, which QEMU user-mode cannot resolve without an Android
sysroot. The pure-Rust and C code under test is identical, so this still exercises real ARM64
codegen — which is what the job is for. State this in the report; do not claim it runs
Android binaries.

- [ ] **Step 3: Validate the workflow syntax**

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research
python3 -c "import yaml,sys; d=yaml.safe_load(open('.github/workflows/ci.yml')); print('jobs:', list(d['jobs'].keys()))"
```
Expected: the job list includes `android-core` and `android-arm64-tests`. If PyYAML is
missing, `pip install pyyaml` first.

- [ ] **Step 4: Reproduce the ARM64 test run locally**

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research
rustup target add aarch64-unknown-linux-gnu
apt-get update && apt-get install -y gcc-aarch64-linux-gnu qemu-user-static
CARGO_TARGET_AARCH64_UNKNOWN_LINUX_GNU_LINKER=aarch64-linux-gnu-gcc \
CARGO_TARGET_AARCH64_UNKNOWN_LINUX_GNU_RUNNER="qemu-aarch64-static -L /usr/aarch64-linux-gnu" \
CC_aarch64_unknown_linux_gnu=aarch64-linux-gnu-gcc \
  cargo test --workspace --target aarch64-unknown-linux-gnu 2>&1 | tail -25
```
Expected: the full workspace suite passes on emulated ARM64. **Record the pass/fail counts —
this is the evidence for the spec's verification matrix.** If libsodium fails to
cross-compile for this triple, fall back to `cargo test -p sv-core -p sv-platform -p sv-stego
-p sv-qr -p sv-watermark` (the pure-Rust crates) and record that reduced scope honestly.

- [ ] **Step 5: Commit**

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research
git add .github/workflows/ci.yml
git commit -m "ci: cross-compile the core for Android and run the suite on ARM64

android-core builds the workspace for two Android ABIs. android-arm64-tests
executes the real suite under QEMU on aarch64-unknown-linux-gnu — the
Android triple links bionic, which QEMU user-mode cannot resolve, so this
verifies ARM64 codegen rather than Android binaries.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

# PART B — Android shell

## Task 7: Android SDK and Tauri Android project

**Files:**
- Create: `app/gen/android/` (generated)
- Modify: `app/tauri.conf.json` if the generator requires it

**Interfaces:**
- Consumes: `app/` from Task 1, `compose::Backend` from Task 5
- Produces: a buildable Gradle project at `app/gen/android/`.

- [ ] **Step 1: Install the Android command-line tools and SDK**

```bash
mkdir -p /root/android/sdk/cmdline-tools
cd /root/android
curl -sSL -o cmdtools.zip https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip
unzip -q cmdtools.zip -d /root/android/sdk/cmdline-tools
mv /root/android/sdk/cmdline-tools/cmdline-tools /root/android/sdk/cmdline-tools/latest
export ANDROID_HOME=/root/android/sdk
export PATH="$ANDROID_HOME/cmdline-tools/latest/bin:$PATH"
yes | sdkmanager --licenses > /dev/null
sdkmanager "platform-tools" "platforms;android-34" "build-tools;34.0.0"
```
Expected: `sdkmanager --list_installed` shows platform-tools, android-34, build-tools.

- [ ] **Step 2: Install the Tauri CLI**

```bash
cargo install tauri-cli --version '^2' --locked
cargo tauri --version
```
Expected: prints a 2.x version.

- [ ] **Step 3: Add the remaining Android Rust targets**

```bash
rustup target add aarch64-linux-android armv7-linux-androideabi i686-linux-android x86_64-linux-android
rustup target list --installed | grep android
```
Expected: four Android targets listed.

- [ ] **Step 4: Initialise the Android project**

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research/app
export ANDROID_HOME=/root/android/sdk
export NDK_HOME=/root/android/android-ndk-r28c
export JAVA_HOME=$(dirname $(dirname $(readlink -f $(which java))))
cargo tauri android init 2>&1 | tail -20
```
Expected: `app/gen/android/` is created with a Gradle project. If it fails on a missing
`identifier`, confirm `app/tauri.conf.json` has `"identifier": "org.secure-vault.desktop"` —
it does — and re-run.

- [ ] **Step 5: Confirm desktop still builds**

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research/app
cargo check 2>&1 | tail -3
cargo test 2>&1 | tail -3
```
Expected: unchanged from baseline. `android init` must not have disturbed the desktop build.

- [ ] **Step 6: Commit**

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research
cat app/gen/android/.gitignore 2>/dev/null || true
git add app/gen/android app/tauri.conf.json
git commit -m "build(android): initialise the Tauri Android project

Generated Gradle project for the shared app crate. Desktop build and test
verified unchanged.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

## Task 8: First Android APK

**Files:**
- Modify: `app/gen/android/app/src/main/AndroidManifest.xml`
- Modify: `app/src/lib.rs` if the mobile entry point needs `#[cfg(mobile)] #[tauri::mobile_entry_point]`

**Interfaces:**
- Consumes: Task 7's Gradle project
- Produces: `app/gen/android/app/build/outputs/apk/universal/debug/app-universal-debug.apk`

- [ ] **Step 1: Add the mobile entry point**

Confirm `app/src/lib.rs` exposes a mobile entry point. If absent, add above `pub fn run()`:

```rust
/// Android/iOS entry point. Tauri's generated native shells call this symbol; desktop uses
/// `main.rs` → `run()` instead. Both funnel into the same builder.
#[cfg(mobile)]
#[tauri::mobile_entry_point]
fn mobile_entry_point() {
    run();
}
```

- [ ] **Step 2: Build the debug APK**

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research/app
export ANDROID_HOME=/root/android/sdk
export NDK_HOME=/root/android/android-ndk-r28c
export JAVA_HOME=$(dirname $(dirname $(readlink -f $(which java))))
cargo tauri android build --debug --target aarch64 2>&1 | tail -30
```
Expected: a debug APK is produced. Record its path.

- [ ] **Step 3: Verify the APK contains the ARM64 native library**

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research
APK=$(find app/gen/android -name "*.apk" | head -1)
echo "APK: $APK"
unzip -l "$APK" | grep -E "lib/.*\.so"
```
Expected: at least `lib/arm64-v8a/libsecure_vault_desktop_lib.so`. **This is the core
verification for Android**: the audited Rust core, libsodium and hazmat.c are inside the APK
as ARM64 code.

- [ ] **Step 4: Verify the manifest**

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research
$ANDROID_HOME/build-tools/34.0.0/aapt2 dump badging "$APK" 2>/dev/null | head -20
```
Expected: package `org.secure-vault.desktop`, and the permission list contains **no** network
permission. SecureVault is offline; if `android.permission.INTERNET` appears, find and remove
it from `AndroidManifest.xml` — an offline security tool must not request network access.

- [ ] **Step 5: Commit**

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research
git add app/src/lib.rs app/gen/android
git commit -m "feat(android): produce a debug APK carrying the ARM64 core

Verified: lib/arm64-v8a contains the native library, and the manifest
declares no INTERNET permission — the app stays offline.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

## Task 9: File broker

**Files:**
- Create: `app/src/broker/mod.rs`
- Modify: `app/src/lib.rs` (register the broker commands)

**Interfaces:**
- Consumes: `tauri::AppHandle`
- Produces: two `#[tauri::command]`s the frontend calls before/after any path-taking command:
  - `broker_import(app, uri: String) -> Result<String, String>` — stages a platform URI into the cache and returns a real filesystem path
  - `broker_export(app, staged: String, suggested_name: String) -> Result<(), String>` — hands a produced file to the platform share sheet
  - `broker_release(app, staged: String) -> Result<(), String>` — shreds a staged file

- [ ] **Step 1: Write the failing test**

Create `app/src/broker/mod.rs` with the test module only:

```rust
//! Mobile file broker.
//!
//! Android hands out `content://` URIs and iOS security-scoped URLs; neither is openable with
//! `std::fs`, and the whole command surface takes real paths. Rather than rewrite the frozen
//! M0 contract, the shell stages bytes into the app-private cache, runs the unchanged command
//! against that path, exports the result, then shreds the staging copy.
//!
//! The staged plaintext is a documented, accepted residual — see the design spec §6.3.

#![cfg(mobile)]

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn shred_overwrites_then_removes() {
        let dir = std::env::temp_dir().join("svbroker-test");
        std::fs::create_dir_all(&dir).unwrap();
        let p = dir.join("staged.bin");
        std::fs::write(&p, b"sensitive bytes").unwrap();

        shred(&p).unwrap();

        assert!(!p.exists(), "staged file must be removed");
        std::fs::remove_dir_all(&dir).ok();
    }

    #[test]
    fn space_guard_rejects_an_oversized_input() {
        // u64::MAX bytes can never fit; the guard must refuse before staging.
        assert!(check_space(u64::MAX).is_err());
    }

    #[test]
    fn space_guard_accepts_a_small_input() {
        assert!(check_space(1024).is_ok());
    }
}
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research/app
TC=/root/android/android-ndk-r28c/toolchains/llvm/prebuilt/linux-x86_64/bin
CC_aarch64_linux_android=$TC/aarch64-linux-android24-clang \
AR_aarch64_linux_android=$TC/llvm-ar \
CARGO_TARGET_AARCH64_LINUX_ANDROID_LINKER=$TC/aarch64-linux-android24-clang \
  cargo check --target aarch64-linux-android 2>&1 | tail -10
```
Expected: FAIL — `cannot find function shred`, `cannot find function check_space`.

- [ ] **Step 3: Implement**

Insert above the test module in `app/src/broker/mod.rs`:

```rust
use std::fs;
use std::io::{Seek, SeekFrom, Write};
use std::path::{Path, PathBuf};

use tauri::Manager;

/// Refuse to stage anything larger than this. Mobile storage is finite and a staging copy
/// doubles peak usage; a clear error beats a confusing ENOSPC from deep inside the core.
const MAX_STAGE_BYTES: u64 = 512 * 1024 * 1024;

/// Best-effort shred: overwrite the file's bytes with zeros, flush, then unlink.
///
/// Flash translation layers mean overwriting is not a guarantee of erasure on mobile storage.
/// It is a defence-in-depth measure on top of the real control, which is that the file lives
/// in app-private storage covered by platform file-based encryption.
fn shred(path: &Path) -> std::io::Result<()> {
    if let Ok(meta) = fs::metadata(path) {
        if let Ok(mut f) = fs::OpenOptions::new().write(true).open(path) {
            let zeros = vec![0u8; 64 * 1024];
            let mut remaining = meta.len();
            f.seek(SeekFrom::Start(0))?;
            while remaining > 0 {
                let n = remaining.min(zeros.len() as u64) as usize;
                f.write_all(&zeros[..n])?;
                remaining -= n as u64;
            }
            f.flush()?;
            f.sync_all()?;
        }
    }
    fs::remove_file(path)
}

/// Reject a staging request that cannot plausibly fit.
fn check_space(needed: u64) -> Result<(), String> {
    if needed > MAX_STAGE_BYTES {
        return Err(format!(
            "file is too large to process on this device ({needed} bytes; limit {MAX_STAGE_BYTES})"
        ));
    }
    Ok(())
}

/// Directory holding staged copies. App-private cache, cleared on release.
fn stage_dir(app: &tauri::AppHandle) -> Result<PathBuf, String> {
    let dir = app
        .path()
        .app_cache_dir()
        .map_err(|e| format!("no cache dir: {e}"))?
        .join("staged");
    fs::create_dir_all(&dir).map_err(|e| format!("create stage dir: {e}"))?;
    Ok(dir)
}

/// Stage a platform URI into the app cache and return a real filesystem path.
///
/// On Android the plugin layer resolves `content://` through `ContentResolver`; on iOS through
/// a security-scoped bookmark. Both deliver bytes, which land here under a random name.
#[tauri::command]
pub async fn broker_import(app: tauri::AppHandle, uri: String) -> Result<String, String> {
    let bytes = platform_read(&app, &uri).await?;
    check_space(bytes.len() as u64)?;

    let name = format!("{:016x}", rand_u64());
    let dest = stage_dir(&app)?.join(name);
    fs::write(&dest, &bytes).map_err(|e| format!("stage write: {e}"))?;
    Ok(dest.to_string_lossy().into_owned())
}

/// Hand a produced file to the platform share sheet so the user can save it where they like.
#[tauri::command]
pub async fn broker_export(
    app: tauri::AppHandle,
    staged: String,
    suggested_name: String,
) -> Result<(), String> {
    platform_share(&app, Path::new(&staged), &suggested_name).await
}

/// Shred a staged copy. Called by the frontend when an operation completes or fails.
#[tauri::command]
pub fn broker_release(_app: tauri::AppHandle, staged: String) -> Result<(), String> {
    shred(Path::new(&staged)).map_err(|e| format!("shred: {e}"))
}

fn rand_u64() -> u64 {
    let mut b = [0u8; 8];
    getrandom::getrandom(&mut b).expect("system RNG");
    u64::from_le_bytes(b)
}
```

Add `getrandom = "0.2"` to `app/Cargo.toml` `[dependencies]`.

`platform_read` and `platform_share` are the Kotlin/Swift bridge and are implemented in
Task 10 alongside the plugin. For this task, add temporary stubs so the crate compiles:

```rust
async fn platform_read(_app: &tauri::AppHandle, uri: &str) -> Result<Vec<u8>, String> {
    // Desktop-shaped fallback: a plain path. Replaced by the Kotlin/Swift bridge in Task 10.
    fs::read(uri).map_err(|e| format!("read {uri}: {e}"))
}

async fn platform_share(
    _app: &tauri::AppHandle,
    _path: &Path,
    _name: &str,
) -> Result<(), String> {
    Err("share sheet not yet wired".to_string())
}
```

- [ ] **Step 4: Register the module and commands**

In `app/src/lib.rs` add `#[cfg(mobile)] mod broker;`, and inside `generate_handler![...]` add,
guarded so desktop is unaffected — Tauri's macro cannot take `cfg` per entry, so declare a
second builder branch:

```rust
#[cfg(mobile)]
let builder = builder.invoke_handler(tauri::generate_handler![
    /* ...all 38 existing commands... */,
    broker::broker_import,
    broker::broker_export,
    broker::broker_release
]);
#[cfg(desktop)]
let builder = builder.invoke_handler(tauri::generate_handler![
    /* ...all 38 existing commands... */
]);
```

If duplicating the 38-entry list is unpalatable, define it once with a
`macro_rules! base_commands` that expands to the comma-separated list and invoke it in both
arms. Do not change the desktop command set.

- [ ] **Step 5: Verify both targets compile**

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research/app
cargo check 2>&1 | tail -5
TC=/root/android/android-ndk-r28c/toolchains/llvm/prebuilt/linux-x86_64/bin
CC_aarch64_linux_android=$TC/aarch64-linux-android24-clang \
AR_aarch64_linux_android=$TC/llvm-ar \
CARGO_TARGET_AARCH64_LINUX_ANDROID_LINKER=$TC/aarch64-linux-android24-clang \
  cargo test --target aarch64-linux-android broker 2>&1 | tail -10
```
Expected: desktop clean; the three broker tests compile. They cannot *run* on the Android
target here (no emulator) — run the same tests on the host by temporarily removing
`#![cfg(mobile)]` if you want local execution evidence, then restore it.

- [ ] **Step 6: Commit**

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research
git add app/src/broker app/src/lib.rs app/Cargo.toml Cargo.lock
git commit -m "feat(mobile): file broker staging platform URIs into the sandbox

Stages picked files into app-private cache, runs the unchanged command
surface against a real path, then shreds. Keeps the frozen M0 contract
and every crates/ module untouched. Platform bridge stubbed; wired next.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

## Task 10: `svstore` secure-storage plugin

**Files:**
- Create: `app/plugins/svstore/Cargo.toml`
- Create: `app/plugins/svstore/src/lib.rs`
- Create: `app/plugins/svstore/android/src/main/java/SvStorePlugin.kt`
- Create: `app/plugins/svstore/ios/Sources/SvStorePlugin.swift`

**Interfaces:**
- Consumes: `tauri::AppHandle`
- Produces: `#[tauri::command]`s `svstore_set(key: String, value: String)`, `svstore_get(key: String) -> Option<String>`, `svstore_delete(key: String)`, `svstore_list() -> Vec<String>`.
- **Contract:** callers may store SAF URI grants, iOS bookmarks and the recent-vault list. Storing passphrases, session keys or age identities here is a spec violation (D3).

- [ ] **Step 1: Create the Rust plugin binding**

Create `app/plugins/svstore/Cargo.toml`:

```toml
[package]
name = "tauri-plugin-svstore"
description = "Secure storage over Android Keystore / iOS Keychain. Non-vault secrets only."
version = "0.1.0"
edition = "2021"
rust-version = "1.96"
license = "MIT OR Apache-2.0"
publish = false

[dependencies]
tauri = { version = "2", features = [] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
thiserror = "1"
```

Create `app/plugins/svstore/src/lib.rs`:

```rust
//! Secure storage plugin — Android Keystore / iOS Keychain.
//!
//! **Contract (design spec D3):** this stores persisted SAF URI grants, iOS security-scoped
//! bookmarks, and the recent-vault list. It must NEVER store passphrases, session keys, or
//! age identities. The vault key hierarchy is out of scope for this plugin by design, which
//! is what keeps the M0 contract and the audited crates untouched.

#![forbid(unsafe_code)]

use serde::{Deserialize, Serialize};
use tauri::plugin::{Builder, TauriPlugin};
use tauri::{command, AppHandle, Runtime};

#[cfg(mobile)]
use tauri::plugin::PluginHandle;

#[derive(Debug, Serialize)]
struct SetArgs<'a> {
    key: &'a str,
    value: &'a str,
}

#[derive(Debug, Serialize)]
struct KeyArgs<'a> {
    key: &'a str,
}

#[derive(Debug, Deserialize)]
struct ValueReply {
    value: Option<String>,
}

#[derive(Debug, Deserialize)]
struct KeysReply {
    keys: Vec<String>,
}

#[cfg(mobile)]
fn handle<R: Runtime>(app: &AppHandle<R>) -> Result<&PluginHandle<R>, String> {
    app.try_state::<PluginHandle<R>>()
        .map(|s| s.inner())
        .ok_or_else(|| "svstore plugin not registered".to_string())
}

#[command]
async fn svstore_set<R: Runtime>(
    app: AppHandle<R>,
    key: String,
    value: String,
) -> Result<(), String> {
    #[cfg(mobile)]
    {
        handle(&app)?
            .run_mobile_plugin::<()>("set", SetArgs { key: &key, value: &value })
            .map_err(|e| e.to_string())
    }
    #[cfg(desktop)]
    {
        let _ = (app, key, value);
        Err("svstore is mobile-only".to_string())
    }
}

#[command]
async fn svstore_get<R: Runtime>(app: AppHandle<R>, key: String) -> Result<Option<String>, String> {
    #[cfg(mobile)]
    {
        handle(&app)?
            .run_mobile_plugin::<ValueReply>("get", KeyArgs { key: &key })
            .map(|r| r.value)
            .map_err(|e| e.to_string())
    }
    #[cfg(desktop)]
    {
        let _ = (app, key);
        Err("svstore is mobile-only".to_string())
    }
}

#[command]
async fn svstore_delete<R: Runtime>(app: AppHandle<R>, key: String) -> Result<(), String> {
    #[cfg(mobile)]
    {
        handle(&app)?
            .run_mobile_plugin::<()>("delete", KeyArgs { key: &key })
            .map_err(|e| e.to_string())
    }
    #[cfg(desktop)]
    {
        let _ = (app, key);
        Err("svstore is mobile-only".to_string())
    }
}

#[command]
async fn svstore_list<R: Runtime>(app: AppHandle<R>) -> Result<Vec<String>, String> {
    #[cfg(mobile)]
    {
        handle(&app)?
            .run_mobile_plugin::<KeysReply>("list", ())
            .map(|r| r.keys)
            .map_err(|e| e.to_string())
    }
    #[cfg(desktop)]
    {
        let _ = app;
        Err("svstore is mobile-only".to_string())
    }
}

/// Register the plugin. Only called from the mobile composition root.
pub fn init<R: Runtime>() -> TauriPlugin<R> {
    Builder::new("svstore")
        .invoke_handler(tauri::generate_handler![
            svstore_set,
            svstore_get,
            svstore_delete,
            svstore_list
        ])
        .setup(|_app, _api| {
            #[cfg(target_os = "android")]
            _app.manage(_api.register_android_plugin("org.securevault.svstore", "SvStorePlugin")?);
            #[cfg(target_os = "ios")]
            _app.manage(_api.register_ios_plugin(init_plugin_svstore)?);
            Ok(())
        })
        .build()
}

#[cfg(target_os = "ios")]
extern "C" {
    fn init_plugin_svstore() -> *const std::ffi::c_void;
}
```

Add to `app/Cargo.toml` `[dependencies]`:

```toml
# Mobile-only secure storage (Android Keystore / iOS Keychain). Registered only by the mobile
# composition root; its commands return an error on desktop.
tauri-plugin-svstore = { path = "plugins/svstore" }
```

and register it in `app/src/compose/mobile.rs`'s builder wiring, or in `app/src/lib.rs` under
`#[cfg(mobile)]`: `.plugin(tauri_plugin_svstore::init())`.

Tauri 2's mobile plugin API has changed across minor versions. If `run_mobile_plugin` or
`register_android_plugin` do not resolve, check the exact signatures with
`grep -rn "run_mobile_plugin\|register_android_plugin" ~/.cargo/registry/src/*/tauri-2*/src/plugin.rs`
and adapt — the shape above is the 2.x pattern, not a guess at an API that may not exist.

- [ ] **Step 2: Write the Kotlin implementation**

Create `app/plugins/svstore/android/src/main/java/SvStorePlugin.kt`:

```kotlin
package org.securevault.svstore

import android.app.Activity
import android.security.keystore.KeyProperties
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import app.tauri.annotation.Command
import app.tauri.annotation.InvokeArg
import app.tauri.annotation.TauriPlugin
import app.tauri.plugin.Invoke
import app.tauri.plugin.JSObject
import app.tauri.plugin.Plugin

@InvokeArg class SetArgs { lateinit var key: String; lateinit var value: String }
@InvokeArg class KeyArgs { lateinit var key: String }

/**
 * Secure storage backed by Android Keystore.
 *
 * Holds only non-vault secrets: persisted SAF URI grants and the recent-vault list. The vault
 * key hierarchy is never touched — see the design spec, decision D3.
 */
@TauriPlugin
class SvStorePlugin(private val activity: Activity) : Plugin(activity) {

    private val prefs by lazy {
        val masterKey = MasterKey.Builder(activity)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .setRequestStrongBoxBacked(true)   // hardware-backed where the device supports it
            .build()
        EncryptedSharedPreferences.create(
            activity,
            "securevault_svstore",
            masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
        )
    }

    @Command
    fun set(invoke: Invoke) {
        val args = invoke.parseArgs(SetArgs::class.java)
        prefs.edit().putString(args.key, args.value).apply()
        invoke.resolve()
    }

    @Command
    fun get(invoke: Invoke) {
        val args = invoke.parseArgs(KeyArgs::class.java)
        val out = JSObject()
        out.put("value", prefs.getString(args.key, null))
        invoke.resolve(out)
    }

    @Command
    fun delete(invoke: Invoke) {
        val args = invoke.parseArgs(KeyArgs::class.java)
        prefs.edit().remove(args.key).apply()
        invoke.resolve()
    }

    @Command
    fun list(invoke: Invoke) {
        val out = JSObject()
        out.put("keys", prefs.all.keys.toList())
        invoke.resolve(out)
    }
}
```

Add to `app/gen/android/app/build.gradle.kts` dependencies:
`implementation("androidx.security:security-crypto:1.1.0-alpha06")`

- [ ] **Step 3: Write the Swift implementation (authored, unverified)**

Create `app/plugins/svstore/ios/Sources/SvStorePlugin.swift`:

```swift
import Foundation
import Security
import Tauri

// Secure storage backed by the iOS Keychain.
//
// Holds only non-vault secrets: security-scoped bookmarks and the recent-vault list. The
// vault key hierarchy is never touched — see the design spec, decision D3.
//
// NOTE: authored on a Linux host with no Xcode. This code has never been compiled or run.

class SetArgs: Decodable { let key: String; let value: String }
class KeyArgs: Decodable { let key: String }

private let service = "org.secure-vault.svstore"

class SvStorePlugin: Plugin {
  @objc public func set(_ invoke: Invoke) throws {
    let args = try invoke.parseArgs(SetArgs.self)
    let data = Data(args.value.utf8)

    // Replace any existing item for this key.
    let query: [String: Any] = [
      kSecClass as String: kSecClassGenericPassword,
      kSecAttrService as String: service,
      kSecAttrAccount as String: args.key,
    ]
    SecItemDelete(query as CFDictionary)

    var add = query
    add[kSecValueData as String] = data
    // Never syncs to iCloud; unavailable until the device is first unlocked after boot.
    add[kSecAttrAccessible as String] = kSecAttrAccessibleWhenUnlockedThisDeviceOnly
    add[kSecAttrSynchronizable as String] = false

    let status = SecItemAdd(add as CFDictionary, nil)
    if status != errSecSuccess {
      invoke.reject("keychain add failed: \(status)")
      return
    }
    invoke.resolve()
  }

  @objc public func get(_ invoke: Invoke) throws {
    let args = try invoke.parseArgs(KeyArgs.self)
    let query: [String: Any] = [
      kSecClass as String: kSecClassGenericPassword,
      kSecAttrService as String: service,
      kSecAttrAccount as String: args.key,
      kSecReturnData as String: true,
      kSecMatchLimit as String: kSecMatchLimitOne,
    ]
    var item: CFTypeRef?
    let status = SecItemCopyMatching(query as CFDictionary, &item)
    if status == errSecItemNotFound {
      invoke.resolve(["value": nil as String?])
      return
    }
    guard status == errSecSuccess, let data = item as? Data,
          let value = String(data: data, encoding: .utf8) else {
      invoke.reject("keychain read failed: \(status)")
      return
    }
    invoke.resolve(["value": value])
  }

  @objc public func delete(_ invoke: Invoke) throws {
    let args = try invoke.parseArgs(KeyArgs.self)
    let query: [String: Any] = [
      kSecClass as String: kSecClassGenericPassword,
      kSecAttrService as String: service,
      kSecAttrAccount as String: args.key,
    ]
    SecItemDelete(query as CFDictionary)
    invoke.resolve()
  }

  @objc public func list(_ invoke: Invoke) throws {
    let query: [String: Any] = [
      kSecClass as String: kSecClassGenericPassword,
      kSecAttrService as String: service,
      kSecReturnAttributes as String: true,
      kSecMatchLimit as String: kSecMatchLimitAll,
    ]
    var items: CFTypeRef?
    let status = SecItemCopyMatching(query as CFDictionary, &items)
    if status == errSecItemNotFound {
      invoke.resolve(["keys": [String]()])
      return
    }
    guard status == errSecSuccess, let arr = items as? [[String: Any]] else {
      invoke.reject("keychain list failed: \(status)")
      return
    }
    invoke.resolve(["keys": arr.compactMap { $0[kSecAttrAccount as String] as? String }])
  }
}

@_cdecl("init_plugin_svstore")
func initPlugin() -> UnsafeMutableRawPointer {
  return Plugin.register(SvStorePlugin())
}
```

- [ ] **Step 4: Replace the broker's stubbed platform bridge**

Task 9 left `platform_read` and `platform_share` as stubs. Extend the Kotlin plugin with two
more commands and point the broker at them.

Add to `SvStorePlugin.kt` (same class):

```kotlin
    @Command
    fun readUri(invoke: Invoke) {
        val args = invoke.parseArgs(KeyArgs::class.java)   // reuses `key` as the URI
        val uri = android.net.Uri.parse(args.key)
        val bytes = activity.contentResolver.openInputStream(uri)?.use { it.readBytes() }
            ?: run { invoke.reject("cannot open $uri"); return }
        val out = JSObject()
        out.put("base64", android.util.Base64.encodeToString(bytes, android.util.Base64.NO_WRAP))
        invoke.resolve(out)
    }

    @Command
    fun shareFile(invoke: Invoke) {
        val args = invoke.parseArgs(KeyArgs::class.java)   // reuses `key` as the file path
        val file = java.io.File(args.key)
        val uri = androidx.core.content.FileProvider.getUriForFile(
            activity, "${activity.packageName}.fileprovider", file
        )
        val intent = android.content.Intent(android.content.Intent.ACTION_SEND).apply {
            type = "application/octet-stream"
            putExtra(android.content.Intent.EXTRA_STREAM, uri)
            addFlags(android.content.Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        activity.startActivity(android.content.Intent.createChooser(intent, "Share"))
        invoke.resolve()
    }
```

Declare the FileProvider in `app/gen/android/app/src/main/AndroidManifest.xml` inside
`<application>`:

```xml
<provider
    android:name="androidx.core.content.FileProvider"
    android:authorities="${applicationId}.fileprovider"
    android:exported="false"
    android:grantUriPermissions="true">
    <meta-data
        android:name="android.support.FILE_PROVIDER_PATHS"
        android:resource="@xml/file_paths" />
</provider>
```

and create `app/gen/android/app/src/main/res/xml/file_paths.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<paths>
    <cache-path name="staged" path="staged/" />
</paths>
```

Then in `app/src/broker/mod.rs` replace the two stubs with:

```rust
/// Read a `content://` URI through the Android ContentResolver (iOS: a security-scoped URL).
async fn platform_read(app: &tauri::AppHandle, uri: &str) -> Result<Vec<u8>, String> {
    // A plain filesystem path is passed through unchanged — useful for share-intent inputs
    // that Android has already materialised for us.
    if !uri.starts_with("content://") && Path::new(uri).exists() {
        return fs::read(uri).map_err(|e| format!("read {uri}: {e}"));
    }
    let b64: String = tauri_plugin_svstore::read_uri(app, uri).await?;
    use base64::Engine as _;
    base64::engine::general_purpose::STANDARD
        .decode(b64)
        .map_err(|e| format!("decode staged bytes: {e}"))
}

/// Hand a produced file to the platform share sheet.
async fn platform_share(
    app: &tauri::AppHandle,
    path: &Path,
    _name: &str,
) -> Result<(), String> {
    tauri_plugin_svstore::share_file(app, &path.to_string_lossy()).await
}
```

Add `base64 = "0.22"` to `app/Cargo.toml` (already in the workspace graph via `sv-crypto`, so
no new licence surface), and export `read_uri` / `share_file` from the plugin crate as thin
wrappers over `run_mobile_plugin("readUri", …)` and `run_mobile_plugin("shareFile", …)`
following the same shape as `svstore_get`.

- [ ] **Step 5: Verify the Android build picks up the plugin**

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research/app
export ANDROID_HOME=/root/android/sdk NDK_HOME=/root/android/android-ndk-r28c
export JAVA_HOME=$(dirname $(dirname $(readlink -f $(which java))))
cargo tauri android build --debug --target aarch64 2>&1 | tail -25
```
Expected: the APK builds with the Kotlin plugin compiled in. Kotlin compile errors surface
here; Swift errors cannot (no Xcode) and are accepted as unverified.

- [ ] **Step 6: Confirm desktop is untouched**

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research/app
cargo test 2>&1 | tail -3
```
Expected: green. The plugin is mobile-only and must not enter the desktop graph.

- [ ] **Step 7: Commit**

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research
git add app/plugins app/gen/android
git commit -m "feat(mobile): svstore plugin over Android Keystore and iOS Keychain

Stores SAF URI grants, iOS bookmarks and the recent-vault list only —
never passphrases, session keys or age identities (spec D3). Kotlin path
compiles in the APK; the Swift path is authored and unverified (no Xcode
on this host).

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

## Task 11: Auto-lock on background

**Files:**
- Modify: `app/src/lib.rs`

**Interfaces:**
- Consumes: the existing `vault_lock` command and `compose::Backend`
- Produces: no new command. A `RunEvent` hook that locks every open session when the app leaves the foreground.

- [ ] **Step 1: Write the failing test**

Add to `src-tauri/src/service.rs`'s test module (the behaviour belongs to the backend, which
is testable without Tauri):

```rust
#[test]
fn lock_all_closes_every_open_session() {
    let backend = VaultBackend::new(StubPayloadCipher::default());
    // Two independent vaults unlocked at once.
    let (_p1, s1) = crate::service::tests::open_temp_vault(&backend, "pass-one");
    let (_p2, s2) = crate::service::tests::open_temp_vault(&backend, "pass-two");

    backend.lock_all();

    assert!(backend.vault_meta(s1).is_err(), "session 1 must be closed");
    assert!(backend.vault_meta(s2).is_err(), "session 2 must be closed");
}
```

If a `open_temp_vault` helper does not already exist in that test module, write one following
the pattern of the existing vault-lifecycle tests in the same file.

- [ ] **Step 2: Run to verify it fails**

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research
cargo test -p sv-app lock_all 2>&1 | tail -10
```
Expected: FAIL — `no method named lock_all`.

- [ ] **Step 3: Implement `lock_all`**

In `src-tauri/src/service.rs`, add to `impl<P: PayloadCipher> VaultBackend<P>`:

```rust
/// Close every open session.
///
/// Mobile calls this when the app leaves the foreground: Android may kill a backgrounded
/// process at any time, which would destroy sessions silently and leave the UI holding a
/// stale handle. Locking deliberately makes that predictable and re-prompts on return.
pub fn lock_all(&self) {
    let mut sessions = self.sessions.lock().expect("session map poisoned");
    sessions.clear();
}
```

Match the actual field name and lock type used by the existing `vault_lock` implementation in
the same file — read it first and mirror it exactly.

- [ ] **Step 4: Run to verify it passes**

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research
cargo test -p sv-app 2>&1 | tail -8
```
Expected: PASS.

- [ ] **Step 5: Wire the lifecycle hook**

In `app/src/lib.rs`, on the Tauri builder, before `.run(...)`:

```rust
// Mobile: lock every session when the app leaves the foreground. Android can kill a
// backgrounded process at any moment, so make the resulting lock deliberate and predictable
// instead of a stale-handle failure on return.
#[cfg(mobile)]
let builder = builder.on_run_event(|app, event| {
    if matches!(event, tauri::RunEvent::Exit | tauri::RunEvent::ExitRequested { .. }) {
        if let Some(backend) = app.try_state::<compose::Backend>() {
            backend.lock_all();
        }
    }
});
```

If Tauri 2 exposes a dedicated pause/resume event for mobile, prefer it over `Exit` — check
`tauri::RunEvent`'s variants with `cargo doc -p tauri --open` or by grepping the tauri source
in `~/.cargo/registry`. Record which event you used in the commit message.

- [ ] **Step 6: Verify both platforms build**

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research/app
cargo test 2>&1 | tail -3
TC=/root/android/android-ndk-r28c/toolchains/llvm/prebuilt/linux-x86_64/bin
CC_aarch64_linux_android=$TC/aarch64-linux-android24-clang \
AR_aarch64_linux_android=$TC/llvm-ar \
CARGO_TARGET_AARCH64_LINUX_ANDROID_LINKER=$TC/aarch64-linux-android24-clang \
  cargo check --target aarch64-linux-android 2>&1 | tail -5
```
Expected: both clean.

- [ ] **Step 7: Commit**

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research
git add src-tauri/src/service.rs app/src/lib.rs
git commit -m "feat(mobile): lock all sessions when the app leaves the foreground

Android kills backgrounded processes, which destroyed sessions silently
and left the UI on a stale handle. Locking deliberately makes it
predictable. Desktop behaviour unchanged.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

## Task 12: Mobile frontend

**Files:**
- Modify: `app/frontend/styles.css`
- Modify: `app/frontend/main.js`
- Modify: `app/frontend/index.html`
- Modify: `app/frontend/i18n.js`

**Interfaces:**
- Consumes: nothing from earlier Rust tasks
- Produces: a `data-platform="mobile"` attribute on `<html>` and a drawer nav. **No change to any command invocation.**

- [ ] **Step 1: Set the platform attribute**

In `app/frontend/main.js`, inside `init()`, before the first `invoke` call:

```js
// Mobile layout is CSS-driven off this attribute; the command logic below is identical on
// every platform. Falls back to a width heuristic if the platform plugin isn't present.
try {
  const p = (window.__TAURI__?.os?.platform && (await window.__TAURI__.os.platform())) || "";
  if (p === "android" || p === "ios") document.documentElement.dataset.platform = "mobile";
} catch (_) {
  if (window.matchMedia("(max-width: 700px)").matches) {
    document.documentElement.dataset.platform = "mobile";
  }
}
```

- [ ] **Step 2: Add the drawer toggle to the header**

In `app/frontend/index.html`, as the first child of `<header>`:

```html
<button id="nav-toggle" class="nav-toggle" data-i18n-title="nav.menu" aria-label="Menu"
        aria-expanded="false" aria-controls="sidebar-nav">☰</button>
```

- [ ] **Step 3: Wire the drawer**

In `app/frontend/main.js`, inside `init()`:

```js
const navToggle = $("nav-toggle");
const shell = document.querySelector(".shell");
if (navToggle && shell) {
  const setDrawer = (open) => {
    shell.classList.toggle("drawer-open", open);
    navToggle.setAttribute("aria-expanded", open ? "true" : "false");
  };
  navToggle.addEventListener("click", () => {
    setDrawer(!shell.classList.contains("drawer-open"));
  });
  // Selecting a tool closes the drawer, so the user lands on the screen they picked.
  document.querySelectorAll("#sidebar-nav .navitem").forEach((b) => {
    b.addEventListener("click", () => setDrawer(false));
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") setDrawer(false);
  });
}
```

- [ ] **Step 4: Add the mobile stylesheet block**

Append to `app/frontend/styles.css`:

```css
/* ===================================================================
   Mobile layout. Keyed off data-platform="mobile" (set at runtime) so
   desktop rendering is byte-identical to before.
   =================================================================== */
.nav-toggle {
  display: none;
  background: transparent;
  border: 0;
  color: var(--fg);
  font-size: 1.3rem;
  padding: 0.3rem 0.5rem;
  cursor: pointer;
}

:root[data-platform="mobile"] .nav-toggle {
  display: block;
}

:root[data-platform="mobile"] body {
  padding: calc(0.9rem + env(safe-area-inset-top)) 1rem
           calc(0.9rem + env(safe-area-inset-bottom)) 1rem;
}

/* Sidebar becomes an off-canvas drawer. 19 tools do not fit a bottom tab bar. */
:root[data-platform="mobile"] .sidebar {
  position: fixed;
  inset: 0 auto 0 0;
  width: 78vw;
  max-width: 300px;
  z-index: 40;
  background: var(--card);
  border-right: 1px solid var(--border);
  padding: 1rem 0.6rem calc(1rem + env(safe-area-inset-bottom));
  overflow-y: auto;
  transform: translateX(-102%);
  transition: transform 0.22s ease;
}

:root[data-platform="mobile"] .shell.drawer-open .sidebar {
  transform: translateX(0);
}

:root[data-platform="mobile"] #main {
  max-width: none;
}

/* Touch targets: 44px minimum on every interactive control. */
:root[data-platform="mobile"] .navitem,
:root[data-platform="mobile"] .tile,
:root[data-platform="mobile"] button {
  min-height: 44px;
}

/* An opaque content:// URI is meaningless in a text box: show the chosen file's name and
   make the picker the primary control. The input still carries the broker's staged path,
   so main.js logic is unchanged. */
:root[data-platform="mobile"] .filefield {
  flex-direction: column;
  align-items: stretch;
}

:root[data-platform="mobile"] .filefield input {
  font-size: 0.85rem;
  text-overflow: ellipsis;
}

:root[data-platform="mobile"] .task,
:root[data-platform="mobile"] .card {
  padding: 1.15rem 1rem;
}
```

- [ ] **Step 5: Add the drawer label translations**

In `app/frontend/i18n.js`, add `"nav.menu": "Menu",` to the EN catalogue and
`"nav.menu": "Menu",` to the VI catalogue, both beside the existing `"header.about"` key.

- [ ] **Step 6: Verify desktop rendering is unchanged**

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research/app/frontend
node --check main.js && node --check i18n.js
python3 - <<'PY'
import re
from html.parser import HTMLParser
VOID={"br","img","input","meta","link","hr","source","area","base","col","embed","param","track","wbr"}
class V(HTMLParser):
    def __init__(self): super().__init__(convert_charrefs=True); self.st=[]; self.err=[]
    def handle_starttag(self,t,a):
        if t not in VOID: self.st.append(t)
    def handle_endtag(self,t):
        if t in VOID: return
        if not self.st or self.st.pop()!=t: self.err.append(t)
p=V(); p.feed(open("index.html",encoding="utf-8").read())
print("unclosed:",p.st,"errors:",p.err)
PY
```
Expected: both JS files parse; no unclosed tags or mismatches. Then screenshot the desktop
home and one task screen headlessly (as in the earlier UI work) and confirm they are visually
identical to before — `data-platform` is unset on desktop, so every new rule is inert.

- [ ] **Step 7: Commit**

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research
git add app/frontend
git commit -m "feat(mobile): drawer navigation and touch layout

Mobile layout keys off data-platform=\"mobile\" set at runtime, so every
new rule is inert on desktop. Sidebar becomes an off-canvas drawer, touch
targets reach 44px, safe-area insets respected. No command logic changed.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

# PART C — iOS and documentation

## Task 13: iOS project and CI

**Files:**
- Create: `app/gen/apple/` (hand-authored; `cargo tauri ios init` cannot run on Linux)
- Modify: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: `compose::Backend` (Task 5), the Swift plugin (Task 10)
- Produces: an `ios-core` CI job. No Rust interface.

- [ ] **Step 1: Confirm the generator cannot run here, and record it**

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research/app
cargo tauri ios init 2>&1 | tail -10
```
Expected: FAIL — Xcode/macOS required. **This is the expected outcome, not a problem to fix.**
Record the exact error text; it is the evidence for the spec's verification matrix.

- [ ] **Step 2: Add the iOS build instructions**

Create `app/gen/apple/README.md`:

```markdown
# iOS project — not generated on this host

`cargo tauri ios init` requires macOS and Xcode. It has never been run for this repository,
so this directory contains instructions rather than a generated project.

## To generate and build (on a Mac)

    rustup target add aarch64-apple-ios aarch64-apple-ios-sim
    cd app
    cargo tauri ios init
    cargo tauri ios dev

`cargo tauri ios init` will scaffold the Xcode project here. Then register the `svstore`
plugin by adding `app/plugins/svstore/ios` as a local Swift package dependency and calling
`init_plugin_svstore` from the generated plugin registry.

## What is already written

- `app/plugins/svstore/ios/Sources/SvStorePlugin.swift` — Keychain-backed secure storage.
  **Authored on Linux; never compiled.** Expect to fix compile errors on first build.
- `app/src/compose/mobile.rs` — the iOS composition root is shared with Android and is
  verified to compile for `aarch64-linux-android`. It is machine-verified for
  `aarch64-apple-ios` by the `ios-core` CI job.

## Required Info.plist entries

    NSPhotoLibraryUsageDescription   — reading images for steganography and QR transfer
    NSDocumentsFolderUsageDescription — importing and exporting vault files

SecureVault is offline: do **not** add any network-related entitlement.
```

- [ ] **Step 3: Add the `ios-core` CI job**

Append to `.github/workflows/ci.yml`:

```yaml
  ios-core:
    name: iOS core cross-compile
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
        with:
          targets: aarch64-apple-ios
      - name: Cross-compile the audited core for iOS
        run: cargo build --workspace --locked --target aarch64-apple-ios
```

This is the only machine verification iOS gets. It proves the shared core — including
libsodium and the vendored `hazmat.c` — compiles for Apple silicon devices. It does **not**
prove the app runs, and the README must not imply that it does.

- [ ] **Step 4: Validate the workflow**

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research
python3 -c "import yaml; d=yaml.safe_load(open('.github/workflows/ci.yml')); print(list(d['jobs'].keys()))"
```
Expected: includes `ios-core`.

- [ ] **Step 5: Commit**

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research
git add app/gen/apple/README.md .github/workflows/ci.yml
git commit -m "build(ios): author the iOS path and add macOS CI verification

cargo tauri ios init cannot run on Linux, so the project is documented
rather than generated. The ios-core job on macos-latest gives the shared
core machine-verified compilation for aarch64-apple-ios.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

## Task 14: Verification matrix and documentation

**Files:**
- Modify: `README.md`
- Modify: `app/README.md`
- Create: `docs/MOBILE.md`

**Interfaces:**
- Consumes: recorded evidence from Tasks 3, 6, 8
- Produces: no code interface.

- [ ] **Step 1: Write the mobile documentation**

Create `docs/MOBILE.md` covering: how to build for Android (exact env vars and commands from
Task 7/8), how to build for iOS on a Mac (pointing at `app/gen/apple/README.md`), the
architecture (one crate, two composition roots), what differs on mobile (payload cipher,
file brokering, no metadata module), and the accepted staged-plaintext residual from spec
§6.3 stated in full.

- [ ] **Step 2: Add the verification matrix to the README**

Add to `README.md` under a new `## Platform support` heading, filling in the **actual**
results recorded during Tasks 3, 6 and 8 — not the predictions written here:

```markdown
| | Desktop | Android | iOS |
|---|---|---|---|
| Core cross-compiles | ✅ verified | ✅ verified | ⚠️ CI (`macos-latest`) only |
| Core test suite | ✅ on host | ✅ ARM64 under QEMU | ❌ not run |
| App builds | ✅ verified | ✅ debug APK | ⚠️ requires a Mac |
| App runs, UI verified | ✅ verified | ⚠️ **not verified** — no KVM on the build host | ⚠️ **not verified** |
| Metadata tools (ExifTool) | ✅ | ❌ unavailable (fails closed) | ❌ unavailable (fails closed) |

**Read the ⚠️ rows literally.** Keystore, the SAF pickers and the share sheet are authored
but were never executed: the build host is a VM without `/dev/kvm`, so no Android emulator
could boot, and Apple's toolchain is macOS-only. Verify these on a real device before relying
on them.
```

- [ ] **Step 3: Verify every claim in the matrix**

Re-read each ✅ and confirm a command in this plan actually produced it. Downgrade anything
that did not. **A ✅ with no recorded evidence is a documentation bug.**

- [ ] **Step 4: Commit**

```bash
cd /root/imtoiteu/SecureVault/secure-vault-research
git add README.md app/README.md docs/MOBILE.md
git commit -m "docs: mobile build guide and platform verification matrix

States plainly which platforms are verified and which are authored but
unrun, and why: no KVM on the build host, and no macOS for iOS.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

## Final gate

- [ ] **Desktop regression**: `cargo test --workspace` and `cd app && cargo test` both green
- [ ] **Clippy**: `cargo clippy --workspace --all-targets -- -D warnings` clean
- [ ] **Supply chain**: `cargo deny check` passes with `age` and its transitive dependencies
- [ ] **Interop**: the Task 3 tests pass against the real `age` binary
- [ ] **APK**: contains `lib/arm64-v8a/*.so` and declares no `INTERNET` permission
- [ ] **Honesty**: every ⚠️/❌ in the README matrix reflects what was actually run
