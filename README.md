# Secure Vault

Offline, cross-platform desktop vault assembled from vetted OSS components
(age · BLAKE3 · minisign · sss, with later concealment/detection/transfer modules).

**Current state: Phase 1 complete (M0–M7) — a working, tested, hardened vault backend.**
Contracts, schema, and IPC/session design are frozen, and the threat model + hardening status
are documented (see [`docs/M5-SCHEMA-DECISIONS.md`](docs/M5-SCHEMA-DECISIONS.md),
[`docs/M6-IPC-DECISIONS.md`](docs/M6-IPC-DECISIONS.md), and
[`docs/M7-HARDENING.md`](docs/M7-HARDENING.md)).
- **M1:** `Blake3Hasher` (hash + key derivation), `Argon2Kdf` (Argon2id) — pure Rust.
- **M2:** `SssSharer` (Shamir, vendored `sss/hazmat.c` FFI), `SodiumMinisignSigner`
  (Ed25519 minisign-format over libsodium), plus `secretbox` secret wrapping.
- **M3:** `AgeCipher` — drives a bundled, **BLAKE3-hash-pinned** `age` binary as a
  hardened subprocess (recipient via args, identity via a 0600 temp file, cleared env).
- **M4:** `StdKeyHierarchy` — `passphrase →Argon2id→ MK →BLAKE3→` per-field, vault-bound
  wrap keys; generic over the adapters so the domain crate stays backend-free.
- **M5:** `sv-core::container` — `.svault` framing with a binding-root minisign signature
  (splice-resistant), single-stream payload with an **encrypted** item directory, atomic
  writes; generic over injected `Hasher`+`Signer`.
- **M6:** `sv-app::VaultBackend` — the composition root implementing the full
  `VaultService` (create/unlock/lock/change-passphrase, item add/list/extract, integrity,
  sign/verify, share split/recover) with an opaque-handle session table (zeroizing,
  MK-only), oracle-safe **coded** errors, and an `IpcPassphrase` boundary. The
  `#[tauri::command]` runtime shell is the only piece left for when the UI lands.
- **M7:** hardening — `age` subprocess **wall-clock timeout**, decrypted-plaintext
  zeroization, a **fuzz-style parser robustness** sweep, adaptive **Argon2 calibration**, a
  documented threat model + constant-time audit, and reasoned deferrals (mlock, dedicated
  passphrase channel, minisign-CLI interop gate).
- **App shell:** [`app/`](app/) is the Tauri 2 GUI over the command surface —
  scaffolded and isolated from the core workspace (it builds on a machine with the Tauri/webview
  toolchain via `cargo tauri dev`; see [`app/README.md`](app/README.md)). Named `app/` rather
  than `desktop/` because it is becoming the single shell for every platform.

FFI crates `sv-sys-sss`/`sv-sys-sodium` require a C toolchain to build; `sv-age`'s
end-to-end tests need an `age` binary (set `SV_AGE_BIN`/`SV_AGE_KEYGEN_BIN`; they skip
gracefully otherwise — CI installs age on Linux). See:

- [`docs/M0-CONTRACTS.md`](docs/M0-CONTRACTS.md) — authoritative contract/schema/boundary/assumption reference.
- Architecture & roadmap: the approved Phase-1 design and milestone plan (M0–M7).

## Layout
```
crates/sv-types       DTOs crossing the IPC/UI boundary (no secrets)
crates/sv-crypto-traits  stable crypto ABI: traits + value types + algorithm ids
crates/sv-crypto      crypto adapters (BLAKE3, Argon2id, Shamir, minisign, secretbox — all live)
crates/sv-core        .svault schema + container framing, key hierarchy, service API, errors
crates/sv-age         FileCipher over a bundled, hash-pinned age subprocess
crates/sv-sys-sss     libsss hazmat FFI (vendored hazmat.c; getrandom-backed randombytes)
crates/sv-sys-sodium  libsodium FFI (libsodium-sys-stable): sign/blake2b/secretbox
src-tauri (sv-app)    composition root: VaultBackend (VaultService) + CommandSurface
                      (IpcPassphrase, sessions, age PayloadCipher)
app/                  Tauri 2 GUI shell — #[tauri::command] wrappers + static frontend.
                      Workspace-EXCLUDED (keeps the webview dep tree out of the core gates).
```

## Develop
```sh
cargo fmt --all --check
cargo clippy --workspace --all-targets -- -D warnings
cargo build --workspace --locked
cargo test --workspace
```
A C toolchain is required (the FFI crates compile `hazmat.c` and build libsodium from
source). Supply-chain gates (`cargo deny check`, `cargo audit`) and a cross-OS matrix run
in [CI](.github/workflows/ci.yml) — the Windows/MSVC build of the two FFI crates is the
remaining cross-platform risk to watch there. Byte-level interop of `SodiumMinisignSigner`
output with the stock `minisign` CLI is a planned CI gate (the CLI isn't bundled locally).
To initialize the repo: `git init` with this directory as root.
