# Secure Vault — CI Cross-Platform Validation Report

**Date:** 2026-06-15
**Repository:** https://github.com/imtoiteu/secure-vault-research (public)
**Git root:** the `secure-vault/` product directory (the workflow at `.github/workflows/ci.yml`
assumes this; the outer research evidence base is *not* part of this repo).
**Validated commit:** `780444d` — workflow run
[`27563728420`](https://github.com/imtoiteu/secure-vault-research/actions/runs/27563728420):
**all 9 jobs green.**

> This was the first execution of CI (the project had not previously been a git repository).
> Cross-platform behaviour — Linux and Windows in particular — had been authored but not yet run.

> **Currency note.** The test counts below (127 Linux/macOS · 126 Windows) are the figures **for
> commit `780444d`**. The suite has since grown: a local `cargo test --workspace` now reports
> **253 test functions — 249 passing, 4 `#[ignore]` env-gated `age`/ExifTool e2e** (the gated ones
> run in CI, where `SV_AGE_BIN`/`SV_AGE_KEYGEN_BIN` are set) — plus the 1 desktop parity test. This
> document remains the record of that specific green run; re-run CI for the live total.

---

## 1. Result: every required job passes

| Job | ubuntu-latest | macos-latest | windows-latest |
| --- | :---: | :---: | :---: |
| **check** (fmt · clippy `-D warnings` · build `--locked` · test · age e2e) | ✅ | ✅ | ✅ |
| **desktop** (fmt · clippy `-D warnings` · test) | ✅ | ✅ | ✅ |
| **msrv (1.96)** | ✅ (ubuntu) | — | — |
| **cargo-deny + audit** (audited core **and** desktop webview tree) | ✅ (ubuntu) | — | — |
| **sbom (stub)** | ✅ (ubuntu) | — | — |

Run wall-clock: ~8 minutes. The long poles are the Argon2id-/age-driven suites
(`sv-app` ~3.5 min, `sv-platform` ~1.7 min) plus the per-OS `go install age` and MSVC compile.

## 2. Per-platform detail

### Linux (ubuntu-latest) — fully green
- `check`: **127 workspace tests pass**; `clippy -D warnings` clean; `build --locked` clean.
- `age_backed_lifecycle_roundtrips … ok` (the bundled-`age` encrypt/decrypt e2e).
- `desktop`: webview deps install (`libwebkit2gtk-4.1-dev` …); the `ApiError ↔ UI` parity test passes.

### Windows (windows-latest) — fully green  ← first-ever validation
- `check`: **126 workspace tests pass** (the 1-test delta vs. Linux is a `#[cfg(unix)]`-only test in
  `sv-age`: 6 on Unix, 5 on Windows — expected, not a failure); `clippy -D warnings` clean (incl. the
  `#[cfg(windows)]` `env_clear` allow-list code); MSVC build clean.
- **`age_backed_lifecycle_roundtrips … ok` on a real Windows runner** — this is the empirical
  validation of **H4**: spawning `age`/`age-keygen` under `Command::env_clear()` with the
  `SystemRoot`/`SystemDrive`/`TEMP`/`TMP` allow-list works (the cleared environment does *not* break
  the CSPRNG/DLL loader). H4 is no longer a hypothesis.
- `desktop`: MSVC build + clippy + parity test pass.

### macOS (macos-latest) — fully green
- `check`: **127 workspace tests pass**; `age_backed_lifecycle_roundtrips … ok`; clippy/build clean.
- `desktop`: native WebKit build + parity test pass.

## 3. Aggregate gate status

| Gate | Status |
| --- | --- |
| **rustfmt** (`--all --check`) | ✅ all OSes |
| **clippy** (`--workspace --all-targets -D warnings`) | ✅ all OSes (core + desktop) |
| **build** (`--workspace --locked`) | ✅ all OSes |
| **tests** | ✅ 127 (Linux/macOS) · 126 (Windows) workspace + 1 desktop parity test per OS |
| **MSRV** (Rust 1.96) | ✅ builds on the declared MSRV (gate now actually enforced — see §4) |
| **cargo-deny** (advisories/bans/sources/licenses) | ✅ audited core; ✅ desktop webview tree (advisories/bans/sources) |
| **cargo-audit** (RUSTSEC) | ✅ core; ✅ desktop tree |
| **SBOM** | ✅ stub generated + uploaded |

## 4. Failures found on the first runs and how each was fixed

The first push surfaced five distinct, real problems (all pre-existing; none specific to the
env_clear change). In order of discovery:

| # | Symptom | Root cause | Fix |
| --- | --- | --- | --- |
| 1 | `desktop` job: `cargo test --locked` fails on fresh checkout | `desktop/Cargo.lock` was git-ignored (Tauri scaffold default) | Un-ignore + commit it (`desktop/.gitignore`) |
| 2 | `msrv` job silently ineffective | `rust-toolchain.toml` pins `channel = "stable"`, overriding `dtolnay/rust-toolchain@1.96` | Force `RUSTUP_TOOLCHAIN: "1.96"` in the job (verified the workspace builds on 1.96) |
| 3 | **Linux** `check`+`desktop`: `rust-lld: error: duplicate symbol: randombytes` | `sv-sys-sss` exports a `randombytes` shim that collides with libsodium's `randombytes`; lld errors, macOS `ld` tolerated it | Rename the shim to `sv_sss_randombytes` + compile `hazmat.c` with `-Drandombytes=sv_sss_randombytes` |
| 4 | **Windows** `check`+`desktop`: MSVC `C2057/C2466/C2133` in `hazmat.c` | C99 variable-length arrays (`poly[k-1][8]`, `xs[k][8]`/`ys[k][8]`) — MSVC has no VLAs | Fixed-size `[255][8]` max buffers (k ≤ 255); random fill sized to `(k-1)*sizeof(poly[0])` — byte-identical |
| 5 | **macOS** `check`: `go: command not found` | `macos-latest` (arm64) has no Go on PATH | Add `actions/setup-go@v5` so `go install age` works on every OS |

**Crypto note (#3, #4):** both `sv-sys-sss` changes are *portability* fixes — no algorithm change.
Verified behaviour-preserving locally (`clang -Werror=vla` clean; `sv-sys-sss` 4/4 and `sv-platform`
38/38 tests pass) and on CI (same per-crate counts on every OS). No bespoke cryptography was written.

## 5. Remaining blockers (out of scope for CI validation)

CI proves the code **builds, lints, and tests green on all three desktop OSes**. It does **not**
clear the distribution blocker:

- **🔴 H5 — signing/notarization** still blocks any *distributed* beta (macOS Gatekeeper / Windows
  SmartScreen quarantine an unsigned bundle; the nested `age` binary is killed). No certificates
  exist yet. See [`SIGNING-REQUIREMENTS.md`](SIGNING-REQUIREMENTS.md). CI does not produce signed
  artifacts: no signing certificates exist (H5), so any bundle would be unsigned — and the pinned
  `age`/`age-keygen` binaries are git-ignored, so they are not present in a CI checkout to bundle.
- **🟡 Tracked, non-blocking:** H1 `age` streaming/memory bound; multi-process vault lock; generic
  `verify_integrity`; the vault is not yet a consumer of `sv-platform`; final brand assets.

## 6. Reproducing / watching

- Actions: https://github.com/imtoiteu/secure-vault-research/actions
- Re-run locally (audited core): `cargo fmt --all --check && cargo clippy --workspace --all-targets
  -- -D warnings && cargo build --workspace --locked && cargo test --workspace --locked && cargo deny check`
- The age e2e is gated behind `SV_AGE_BIN`/`SV_AGE_KEYGEN_BIN`; CI sets them via `setup-go` + `go install`.
