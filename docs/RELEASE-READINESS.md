# Secure Vault — Release Readiness Gate

> **Path note (2026-09-04):** the Tauri shell directory `desktop/` was renamed `app/` when it
> became the shared desktop + Android + iOS crate. Paths cited below are the ones that existed
> when this document was written and are left unchanged, so the record stays accurate; read
> `desktop/...` as today's `app/...`.


Status: **H4 PASSED on CI (2026-06-15); now blocked on H5 only.** This document is the gate: it
defines exactly what must turn green, how to produce that signal, and the decision rule for starting
beta.

> **Update 2026-06-15 — H4 validated.** The repo is now on GitHub and the full CI matrix has run
> (commit `780444d`, all 9 jobs green — see [CI-VALIDATION.md](CI-VALIDATION.md)). The Windows
> `check` job ran the `age_backed_lifecycle_roundtrips` e2e on a real `windows-latest` runner and it
> **passed**: `env_clear()` + the `SystemRoot`/`SystemDrive` allow-list does not break `age`. H4 is
> closed. **H5 (signing/notarization) remains** — it still requires Apple Developer ID / Windows
> Authenticode credentials the dev environment does not have; see [SIGNING-REQUIREMENTS.md](SIGNING-REQUIREMENTS.md).

## Where things stand
- **Fixed + validated (see [VALIDATION-RESULTS.md](VALIDATION-RESULTS.md)):** H2, H3, H6, H7, and
  the H1 safety-guard/error-clarity mitigation. Core gates: fmt / clippy(-D warnings) /
  build --locked / tests / `cargo deny` all green. The workspace suite is now **253 test functions
  (249 passing; 4 `#[ignore]` env-gated `age`/ExifTool e2e that run in CI)** — up from 80 at
  validation time as the `sv-platform` crypto-services layer, Secret Sharing engine, and the
  stego/meta/qr/watermark modules landed — plus 1 desktop-crate parity test.
- **H4 (Windows `env_clear`) — RESOLVED & validated on CI** (Windows `age` e2e green, 2026-06-15).
- **Open blocker (this document):** H5 (distribution signing).
  *(The H-numbers here are the hardening-risk series — H1–H14 in VALIDATION-PLAN.md — not the
  unrelated schema decision series H1–H6 in M5-SCHEMA-DECISIONS.md.)*
- **Known residuals, not release blockers but tracked:** H1 streaming rewrite; H7 multi-process
  (two app instances on one vault) file lock.

---

## H4 — Windows `env_clear()` — ✅ RESOLVED (validated on CI 2026-06-15)

> **Outcome:** `build+test (windows-latest)` is **green** and `age_backed_lifecycle_roundtrips`
> **ran and passed** (not skipped) on a real Windows runner — confirming the `SystemRoot`/`SystemDrive`/
> `TEMP`/`TMP` allow-list lets `age`/`age-keygen` start under `env_clear()`. The fix predicted in the
> **FAIL** branch below was already applied in `sv-age::run()` and `payload.rs`. See
> [CI-VALIDATION.md](CI-VALIDATION.md). The manual Windows-10/11-desktop spot-check below remains a
> nice-to-have (the runner is Server-family), but the blocker is cleared.

**Question:** does spawning `age`/`age-keygen` with `Command::env_clear()` break them on Windows
(cleared `SystemRoot` → CSPRNG/DLL load failure)? Falsified on macOS; **now also falsified on Windows CI**.

**Validation (automated, real Windows runner):** [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)
now installs `age` and sets `SV_AGE_BIN`/`SV_AGE_KEYGEN_BIN` on **all** OSes, so the
`age_backed_lifecycle_roundtrips` test runs inside the `windows-latest` job. That test calls
`create` → `generate_identity` (the `env_clear` keygen) → `encrypt`/`decrypt` (the `env_clear`
subprocess). If the cleared environment breaks age on Windows, **the Windows job fails on that
test**.

- **PASS:** the `build+test (windows-latest)` job is green and the test is **not** skipped (the job
  log shows it ran, not "skipping: set SV_AGE_BIN…").
- **FAIL:** the Windows job fails on `age_backed_lifecycle_roundtrips`, or it errors spawning age.
  → Fix is **not** to keep clearing the whole env: allow-list `SystemRoot` + `SystemDrive` (and
  `SystemRoot\System32` on PATH) on Windows in `sv-age`'s `run()` and `payload.rs`'s
  `generate_identity`, then re-run.

**Also do once (real hardware, belt-and-suspenders):** on a physical/VM **Windows 10** *and*
**Windows 11**, `cargo tauri dev`, create a vault, add a file, extract it — confirm no failure.
(GitHub's `windows-latest` is Server-family; the desktop SKUs are what users run.)

> ~~I cannot trigger CI from here (this is not a git repo and has no remote).~~ **Done:** the repo
> is on GitHub and the `windows-latest` job ran green (commit `780444d`).

---

## H5 — Distribution signing (BLOCKER for any distribution, incl. beta)

**Question:** does a downloaded/installed build run, or does the OS block the bundled `age`
subprocess? Confirmed on macOS that a **quarantined, non-notarized** nested binary is **SIGKILLed**
(`spctl` rejected, exit 137). The fix is signing + notarization; this validates the finished
artifact.

### Credentials you must supply (the sandbox has none of these)
- **macOS:** Apple Developer Program account; a **Developer ID Application** certificate; an
  app-specific password or App Store Connect API key for **notarization**.
- **Windows:** an **Authenticode** code-signing certificate (OV/EV, or Azure Trusted Signing).

### Build + sign (per [DEPLOYMENT.md](DEPLOYMENT.md) §5–§6), then verify:
- **macOS:** after `cargo tauri build` + sign + `notarytool submit` + `stapler staple`:
  ```sh
  scripts/validate-macos-signing.sh "…/Secure Vault.app" "…/Secure Vault_x.y.z_aarch64.dmg"
  ```
  Checks: deep/strict codesign, Developer ID authority, Hardened Runtime, `spctl -a -t exec`
  acceptance, **every nested age binary individually signed**, and stapled notarization tickets.
- **Windows:** after signing the installer **and** the bundled `age.exe`/`age-keygen.exe`:
  ```powershell
  scripts\validate-windows-signing.ps1 -Installer "…\Secure Vault_x.y.z_x64-setup.exe" `
      -AgeBinaries @("…\age.exe","…\age-keygen.exe")
  ```
  Checks: valid + timestamped Authenticode on the installer and the bundled binaries.

- **PASS:** both scripts exit 0, **and** the final manual check passes — install on a **clean**
  account/VM (macOS clean user; Windows 10 + 11 fresh VM), launch, create a vault + add a file with
  **no** Gatekeeper/SmartScreen/Defender block.
- **FAIL:** any script check red, or the bundled binaries are unsigned (the original H5 failure), or
  a clean-machine launch is blocked. → Sign the nested binaries too (or migrate them to Tauri
  **sidecars**, which Tauri signs as part of the app — note this needs a `resolve_binary` change in
  `desktop/src/lib.rs`; track separately).

---

## Decision gate (do not skip)

```
START BETA  ⇐  H4 PASS (Windows CI e2e green)  .................. ✅ MET (2026-06-15, run 27563728420)
            AND core gates green (fmt/clippy/build --locked/test/deny)  ✅ MET (all 3 OSes green)
            AND H5 PASS (macOS + Windows signed-artifact scripts green AND clean-machine launch OK)
                                                                .................. ❌ NOT MET (no certs)
```

**Current verdict:** the build/test/lint half of the gate is **fully met on all three desktop OSes**;
**H5 (signing/notarization) is the sole remaining gate** for a *distributed* beta. Internal/CI/dev
builds are unblocked. If H5 is red or unrun, **do not start a distributed beta.**

## When the gate is green — beta entry + release prep
1. **Version stamp:** bump and lock-step `desktop/Cargo.toml` and `desktop/tauri.conf.json`
   `version`; record the three internal axes (FORMAT / SUITE / CONTRACT) in the release notes.
2. **Artifacts:** per-OS/arch signed installers + `SHA256SUMS` (+ optional minisign over it); record
   the bundled `age` upstream version, its verified SHA-256, and the embedded BLAKE3 pins
   ([DEPLOYMENT.md](DEPLOYMENT.md) §2/§7).
3. **Smoke matrix:** run [VALIDATION-PLAN.md](VALIDATION-PLAN.md) §8.2 on each shipped platform.
4. **Beta scope + feedback:** a small, informed cohort; collect crash/▽error reports keyed by the
   `SV-…` codes (now actionable post-H6); known-limits note (2 GiB/item interim cap; single-instance
   per vault) from the residuals list.
5. **Tracked residuals to schedule before GA:** H1 streaming (lift the 2 GiB cap), H7 multi-process
   file lock, optional `SV-IO` sub-categorization, native passphrase entry (N1).

> This gate adds **no product features.** It is validation + release tooling only.
