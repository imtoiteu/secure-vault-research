# Secure Vault — H1–H7 Experimental Validation Results

Status: **evidence-based findings.** Each hypothesis was reproduced or falsified against the **real
production code path** (`VaultBackend` + `AgePayloadCipher` driving the actual `age`/`age-keygen`
subprocesses), not the in-memory test stub. *(Update: the H1/H2/H3/H6/H7 findings below were
subsequently fixed and re-validated — see "Re-validation after fixes"; **H4 was later validated green
on Windows CI**, 2026-06-15; H5 signing remains the only open distribution blocker.)*

## Method

- Host: macOS 14.6, arm64. `age`/`age-keygen` **v1.3.1** (Homebrew). Rust 1.96.
- A throwaway harness (outside the repo, `/tmp/hval`) constructed `VaultBackend::new(AgePayloadCipher::new(AgeCipher, age-keygen))`
  and exercised `create`/`unlock`/`add_item`/`list_items`/`extract_item` exactly as the Tauri
  commands do. Error codes were taken from `ApiError::from(VaultError)` (the real projection).
- This matters: the workspace unit suite uses `StubPayloadCipher`, so it never exercises the
  subprocess, the 120 s timeout, the in-memory buffering, `env_clear()`, or the identity temp file —
  exactly the surfaces under test here.

## Findings

### H1 — Large payloads → opaque failure · **CONFIRMED (mechanism reattributed)**
- **Throughput (release):** 512 MiB → encrypt 1.35 s (**379 MiB/s**), decrypt 1.69 s (**303 MiB/s**).
  ⇒ the 120 s wall-clock timeout only crosses at **~44 GiB (encrypt) / ~35 GiB (decrypt)** on a fast
  local disk. So the **timeout is a tail risk**, not the everyday failure (it *will* bite on slow/
  external/encrypted volumes, a loaded machine, or a vault holding tens of GiB).
- **Memory (release, `/usr/bin/time -l`):** adding a **1024 MiB** file peaked at **2,852,782,080 B
  ≈ 2.66 GiB RSS — ~2.7× the file size** (source read + archive copy + age stdin buffer + age stdout
  buffer, all `Vec<u8>` in memory at once). Extrapolated: 4 GiB add ≈ 10.6 GiB peak; 6 GiB ≈ OOM on a
  16 GB machine. Adding to a vault that **already** holds large items is worse (it decrypts and holds
  the entire existing payload too — see H9 in the plan).
- **Surfacing:** a forced timeout (`add_item` of 512 MiB with a 300 ms cap) returned
  `Err(Internal)` → **`SV-INTERNAL`** ("An internal error occurred"), with **the vault left
  byte-identical** (atomic write never reached). No size/timeout/OOM hint reaches the user.
- **Root cause:** fully in-memory buffering in `sv-age` `run()` (`input: Vec<u8>` → `Vec<u8>`) and
  `service.rs` (`read_file` + `pack_archive` hold whole copies); single-stream payload. Timeout/
  backend errors map `→ CryptoError::Backend → crypto_to_vault(_ ) → VaultError::Internal`.
- **Impact:** a "store my files" product OOMs/kills on multi-GB inputs and reports nothing useful.
  Not data loss (vault intact). **Severity: High.**

### H2 — No passphrase confirmation at create · **CONFIRMED**
- **Evidence:** `frontend/index.html` create form has **one** `#passphrase` field (line 35); the
  change-passphrase form has **two** (`#new-passphrase` + `#new-passphrase-2`) and `main.js`
  enforces `a !== b` → "Passphrases do not match." `vault_create` sends the single value directly.
- **Root cause:** missing confirm-match on the create path only.
- **Impact:** a single typo at create produces a vault that can **never** be opened (you cannot even
  mint recovery shares without first unlocking). Trivially hit by any user. **Severity: Critical
  (permanent data loss).**

### H3 — Extract silently overwrites an existing file · **CONFIRMED**
- **Evidence:** seeded `dest` with `USER-PRECIOUS-DATA-DO-NOT-DELETE`; `extract_item` replaced it
  with the vault item's bytes, no prompt. before≠after, after==item.
- **Root cause:** `extract_item` → `container::write_atomic(dest, …)` → `persist` replaces any file
  at `dest`; no existence check or confirmation.
- **Impact:** routine operation can destroy an unrelated file. **Severity: High (silent data loss).**

### H4 — `env_clear()` breaks `age` on Windows · **NOT REPRODUCED (macOS falsified; Windows untested at the time)** · *later RESOLVED — validated green on Windows CI, 2026-06-15*
- **Evidence (macOS):** the real pipeline runs fine under `Command::env_clear()`; an independent
  `env -i` (empty environment) keygen + encrypt + decrypt also succeeded. So `env_clear()` does
  **not** break macOS.
- **Windows:** could not be executed in this environment. The concern (a cleared env removing
  `SystemRoot` needed for the Windows CSPRNG/DLL load) is **plausible but unverified**; modern Go
  uses `ProcessPrng`, which may not require it. **Must be tested on a real Windows host before any
  fix.** **Severity: Unknown — Critical *if* confirmed on Windows (all crypto broken), otherwise
  none.**

### H5 — Bundled `age` blocked on a freshly installed app · **CONFIRMED on macOS (conditional on signing)**
- **Evidence:** a copy of `age` with the LaunchServices `com.apple.quarantine` xattr, exec'd via
  `posix_spawn` (the exact mechanism of Rust's `Command::new`), was **SIGKILLed — exit 137**;
  `spctl -a -t exec` reported **rejected**. The Homebrew `age` is only ad-hoc signed
  (`Identifier=a.out`), i.e. not Developer-ID-signed/notarized.
- **Root cause:** Gatekeeper kills a quarantined, non-notarized executable on exec. In the product
  this fails `generate_identity` (keygen `status.success() == false → Internal`) → vault create fails
  **`SV-INTERNAL`** on first run.
- **Impact:** any **non-notarized** distributed build (incl. test builds handed to others) breaks all
  crypto on first run. A **properly notarized app with signed nested binaries** is not affected
  (developer `cargo tauri dev` builds carry no quarantine, hence "works on my machine"). Ties
  directly to [DEPLOYMENT.md](DEPLOYMENT.md) §6. **Severity: High (release/distribution).**

### H6 — I/O, permission, disk-full, timeout all collapse to `SV-INTERNAL` · **CONFIRMED**
- **Evidence:** creating a vault in a `0o555` directory produced
  `Io("Permission denied (os error 13) …")` → **`ApiError::Internal` / `SV-INTERNAL`**. By the same
  `From` arm, disk-full and the H1 timeout map identically.
- **Root cause:** `error.rs` `From<VaultError>`: `Io(_) | Crypto(_) | Internal → ApiError::Internal`.
- **Impact:** users (and support) cannot distinguish "disk full / no permission / file locked / too
  large" from a genuine bug; it also masks H1 and H5, which all read as the same useless message.
  **Severity: High (diagnosability; amplifies Critical/High failures).**

### H7 — Concurrent writes lose data · **CONFIRMED (deterministic)**
- **Evidence:** two `add_item` calls on one session, run on two threads against a fresh vault,
  **lost an item in 8/8 trials** (final `item_count == 1`, expected 2).
- **Root cause:** `add_item` is a whole-vault read-modify-write (read container → decrypt → rebuild
  full item set → re-encrypt → atomic rewrite). The session `Mutex` guards only the session map, not
  the file RMW; `write_atomic` prevents a *torn file* but not a *lost update* (last full rewrite
  wins). Tauri dispatches commands on a thread pool, so concurrency is reachable.
- **Impact:** silent data loss. **Mitigation in the current UI:** `main.js` disables the button
  during an op (`withButton`), which debounces in-window double-clicks — so the *in-app* trigger is
  mostly **two app instances on the same vault** or rapid programmatic IPC. The backend/contract has
  no guard. **Severity: High at the backend; Medium in the current single-window UI.**

## Final table

| Hypothesis | Confirmed? | Root Cause | Severity | Recommended Action |
| --- | --- | --- | --- | --- |
| **H1** Large file → opaque fail | **Yes** (memory, not timeout) | Fully in-memory age pipeline (~2.7× RSS); 120 s wall-clock; timeout/backend → `Internal` | **High** | Stream payloads (avoid whole-file `Vec`s); make timeout proportional to size or idle-based; report a specific "too large / timed out" error |
| **H2** No create passphrase confirm | **Yes** | Single `#passphrase` field on create; confirm exists only on change | **Critical** | Add confirm-match (and ideally a strength hint) to the create form |
| **H3** Extract overwrites silently | **Yes** | `extract_item` → `write_atomic` `persist` replaces `dest`; no existence check | **High** | Refuse/confirm on existing `dest` (or write to a unique name); surface a distinct code |
| **H4** `env_clear()` breaks Windows | **No (macOS); later validated on Windows CI ✅** | `Command::env_clear()` on the age spawns; macOS unaffected; the `SystemRoot`/`SystemDrive` allow-list lets it start on Windows | **Resolved** (was Unknown; closed on CI 2026-06-15) | Done — `age_backed_lifecycle_roundtrips` ran green on `windows-latest` |
| **H5** Bundled age blocked on install | **Yes (macOS, non-notarized)** | Gatekeeper SIGKILLs quarantined, non-notarized exec'd binary (exit 137, `spctl` rejected) | **High** (distribution) | Notarize the app **and** sign the nested age binaries (or ship them as signed sidecars); verify with `spctl`/`stapler` |
| **H6** Errors collapse to `SV-INTERNAL` | **Yes** | `From<VaultError>`: `Io/Crypto/Internal → Internal` | **High** | Add actionable variants (e.g. `SV-IO`, `SV-PERMISSION`, `SV-TOO-LARGE`/`SV-TIMEOUT`); keep oracle-safe ones merged |
| **H7** Concurrent writes lose data | **Yes (8/8)** | Whole-vault read-modify-write with no per-vault write lock; thread-pool dispatch | **High** (backend) / **Medium** (current UI) | Serialize writes per vault path (mutex/file lock); reject concurrent writers; keep button-disable as defense-in-depth |

**Fix priority (when authorized):** H2 (Critical) → H1, H3, H6, H7 (High, user-facing) → confirm
H4 on Windows and H5 in the release-signing pipeline. No code was changed during this validation.

---

# Re-validation after fixes

The fixes for **H2, H7, H1, H3, H6** were implemented (correctness + data-safety only; no new
features) and re-validated against the **same real production path**. Gates after the change:
**fmt/clippy(-D warnings)/build --locked/`cargo deny` all clean; 80 tests pass (was 77)** — the 3
added are the H1/H3/H7 regression tests. *(Snapshot from this validation pass. The workspace suite
has since grown to **253 test functions — 249 passing, 4 `#[ignore]` env-gated `age`/ExifTool e2e** —
as the `sv-platform` crypto-services layer, Secret Sharing engine, and the stego/meta/qr/watermark
modules landed; the desktop crate adds 1 parity test — see
[RELEASE-READINESS-TOOLKIT.md](RELEASE-READINESS-TOOLKIT.md).)*

## What changed (by hypothesis)
- **H2** — the create form now has a **confirm-passphrase** field and refuses to create unless the
  two match (`desktop/frontend/{index.html,main.js}`). Unlock ignores the confirm field.
- **H7** — `VaultBackend` gained a **per-vault write lock**; `create`/`add_item`/`change_passphrase`
  hold it across the whole read-modify-write, so concurrent writers serialize instead of clobbering.
- **H1** — `add_item` now **rejects a source larger than `MAX_ITEM_BYTES` (2 GiB)** *before* reading
  it (`TooLarge`), and an `age` wall-clock timeout maps to a distinct `Timeout` instead of a generic
  backend error.
- **H3** — `extract_item` **refuses an existing destination** (`OutputExists`) rather than
  overwriting it.
- **H6** — new actionable, non-secret codes: `SV-IO`, `SV-TOO-LARGE`, `SV-TIMEOUT`,
  `SV-OUTPUT-EXISTS`; `Io` no longer collapses to `SV-INTERNAL` (and the path is *not* leaked in the
  surfaced detail). `CONTRACT_VERSION` stays `1` (additive variants).

## Experimental re-run (real `age` v1.3.1, harness over `VaultBackend`/`AgePayloadCipher`)
| Check | Before | After (this run) |
| --- | --- | --- |
| H3 extract onto existing file | overwrote silently | **refused, `SV-OUTPUT-EXISTS`; existing file preserved**; fresh path still works |
| H6 permission-denied create | `SV-INTERNAL` | **`SV-IO`** |
| H1 oversized add (2 GiB+1, sparse) | OOM risk / `SV-INTERNAL` | **`SV-TOO-LARGE`; vault unchanged** (rejected before read) |
| H1 timeout (256 MiB, 200 ms cap) | `SV-INTERNAL` | **`SV-TIMEOUT`; vault intact** |
| H7 two concurrent adds | lost 1 in 12/12 trials | **lost 0/12 trials** |
| H2 create typo | unopenable vault | confirm-match blocks creation (UI; verified by code + JS check) |

## Updated status table
| Hypothesis | Status after fix | Residual / follow-up |
| --- | --- | --- |
| **H2** | **Fixed** (UI confirm-match) | optional: passphrase strength hint; native secret entry (N1) |
| **H7** | **Fixed** in-process (0/12) | **multi-process** (two app instances on one vault) still unguarded — needs an OS file lock; tracked as a follow-up |
| **H1** | **Mitigated** (safe + clear failure) | true fix is **streaming** the payload (remove the ~2.7× in-memory copies); the 2 GiB cap is an interim guard |
| **H3** | **Fixed** (refuse overwrite) | optional: explicit "overwrite" affordance in the UI |
| **H6** | **Fixed** (distinct codes) | could split `SV-IO` into permission/disk-full if desired |
| **H4** | **Resolved — validated on CI (2026-06-15)** | the `age_backed_lifecycle_roundtrips` e2e ran and passed on a real `windows-latest` runner; the `SystemRoot`/`SystemDrive` allow-list lets `age` start under `env_clear()` (see [CI-VALIDATION.md](CI-VALIDATION.md)) |
| **H5** | **Open (release pipeline)** | notarize app + sign nested `age` binaries; verify `spctl`/`stapler` (see [DEPLOYMENT.md](DEPLOYMENT.md) §6) |

## Remaining before broader testing / release — H5 (distribution)
**H4 is now closed** — the Windows `env_clear()` e2e ran green on CI (2026-06-15), so the macOS-host
gap is resolved. The remaining open item is distribution signing:
1. **H4 (Windows `env_clear`) — RESOLVED.** Validated automatically on the `windows-latest` CI job
   (the allow-list predicted below was already applied in `sv-age`/`payload.rs`). A manual
   Windows-10/11 *desktop*-SKU spot-check remains a nice-to-have (the runner is Server-family).
2. **H5 (install-time quarantine)** — produce a signed+notarized macOS `.dmg` with the nested `age`
   binaries signed; install on a clean account and confirm crypto works on first run
   (`spctl -a -t exec`, `stapler validate`). Repeat for a signed Windows installer. **Blocker for
   distribution.**

No streaming rewrite (H1 deep fix) or multi-process lock (H7 residual) was attempted in this pass —
both are larger changes flagged for follow-up.
