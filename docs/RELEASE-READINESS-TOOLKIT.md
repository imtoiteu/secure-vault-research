# Release-Readiness Review — Security & Privacy Toolkit

**Scope:** Currently implemented modules — Secure Vault, Cryptography, Integrity (see status note below), Secret Sharing.
**Out of scope (research-stage, not assessed for release):** Steganography, Watermarking, Analysis, Secure QR Transfer.
**Date:** 2026-06-15
**Method:** Produced by a multi-agent review (parallel security / UX / maintainability / consistency reviewers reading source, each finding adversarially verified against `file:line`). 44 findings raised, 44 kept after verification. One synthesized claim — the per-crate attribution in the test-count note — was **corrected during a final fact-check** (see the provenance note); the corrected figures are reproduced from local `cargo test` runs.

> **Doc-path convention used below.** This review is scoped to `secure-vault/`, so citations like `docs/RELEASE-READINESS.md` resolve under `secure-vault/docs/`. Two referenced docs live one directory up at the **repository top level**: `../docs/PRODUCT-VISION.md` and `../docs/PLATFORM-AUDIT.md`. They are cited with the `../docs/` prefix throughout. CI lives at `secure-vault/.github/workflows/ci.yml` (verified to exist).
>
> **Test count provenance (corrected).** The "126 workspace tests" figure was reproduced locally and breaks down **by crate** as `sv-age 6 + sv-app 25 + sv-core 22 + sv-crypto 20 + sv-crypto-traits 6 + sv-platform 38 + sv-sys-sodium 3 + sv-sys-sss 4 + sv-types 2 = 126`. The heaviest by count are **`sv-platform` (38)** and **`sv-app` (25)**; the longest-running by wall-clock are the **Argon2id-driven `sv-platform` tests (~33 s)** and **`sv-app`'s age-backed lifecycle e2e (~71 s, gated behind `SV_AGE_BIN`)** — exactly the work a never-executed CI must carry. (`sv-age` is only 6 fast tests; the age-backed lifecycle test lives in `sv-app`, not `sv-age`.) The count is asserted from a local run, not from CI.

---

## 0. Resolution log — release-engineering pass (2026-06-15, post-review)

The findings below are preserved **as originally raised** (point-in-time snapshot). A subsequent
release-engineering pass (P1–P4) closed several of them; recorded here for traceability:

- **#1 Home navigation** (the "Check a file" tile mis-routing) — **resolved**: tile routes to the
  integrity workflow; all Home/all-tools tiles audited and the two live tools that were missing
  (`intact`, `split-file`) added.
- **Desktop crate quality gates** — **resolved**: `desktop/` now runs fmt/clippy(-D warnings)/test
  in CI, with an `ApiError ↔ UI message` parity test (1:1 against `ApiError::ALL_CODES`); duplicated
  `SV-IO` message text deduplicated via `ApiError::io_generic()`.
- **#9 / doc drift — `sv-platform` "planned/NEW"** — **resolved**: CLAUDE.md, `../docs/PLATFORM-AUDIT.md`,
  and `TOOLKIT-PHASE1-DESIGN.md` now mark `sv-platform` **implemented (38 tests; vault not yet a consumer)**.
- **#9 / "H4" overloaded** — **resolved by namespace** (not renumber): the schema decision series
  (M5/M7/M6/M0) is now explicitly scoped as **Header-schema H1–H6**, distinct from the
  **hardening-risk H1–H14** (VALIDATION-PLAN/RELEASE-READINESS). A full renumber was deliberately
  declined — both series are internally coherent and woven across 4+ docs; a partial renumber leaves
  gaps and a full one risks drift in frozen design docs.
- **#6 / #8 stale test counts** — **resolved**: RELEASE-READINESS.md, DEPLOYMENT.md, VALIDATION-RESULTS.md
  now read **127** workspace tests. The figure is **+1 over this review's reproduced 126**: the
  release-engineering pass added the `sv-types` `ALL_CODES` completeness/tripwire test (so `sv-types`
  is now 3, not 2). The desktop crate carries 1 more (the parity test). Current per-crate:
  `sv-age 6 + sv-app 25 + sv-core 22 + sv-crypto 20 + sv-crypto-traits 6 + sv-platform 38 +
  sv-sys-sodium 3 + sv-sys-sss 4 + sv-types 3 = 127` (+1 desktop).
- **H4 Windows `env_clear` code fix** — **landed** (`SystemRoot`/`SystemDrive`/`TEMP`/`TMP` allow-list
  in `sv-age` + `payload.rs`); still **awaiting execution** on the `windows-latest` CI job (no git
  remote yet → CI has never run). **H5 signing/notarization remains the distribution blocker.**
- **Placeholder icons** — **resolved (interim)**: a real `.png`/`.icns`/`.ico` set replaces the
  299-byte placeholder and is wired into `bundle.icon`; final brand assets still pending.

---

## 1. Executive Summary & Recommendation

### Recommendation: **GO, with caveats (desktop-only; Windows gated out; see distribution rule below)**

The implemented core is releasable for the macOS/Linux desktop target. The cryptographic spine is well-constructed and its documented security claims are matched by the source: the oracle-safe error merge is applied identically at every boundary (`crates/sv-platform/src/error.rs:58-88`, `crates/sv-core/src/error.rs:68-103`), secret value types are zeroizing, redacted, growth-proof, and non-`Serialize` (`crates/sv-crypto-traits/src/lib.rs:151-254`), the secret-sharing header binding via `derive_key` is cryptographically sound and tested (`crates/sv-platform/src/sharing.rs:121-129,605-630`), the `age` subprocess is hash-pinned/env-cleared/no-shell/timeout-bounded and fails closed in release (`crates/sv-age/src/lib.rs:62-149`; `desktop/src/lib.rs:272-315`), and the Argon2id floor meets OWASP guidance (`crates/sv-crypto/src/policy.rs:15-22`). The architecture is unusually disciplined (dependency-inverted trait ABI, `crates/sv-crypto-traits` → impls → backend-free domain crates), 126 workspace tests pass locally, and the redesigned frontend delivers a consistent, plain-language, oracle-safe UX. **No security blocker was found in the code under review.**

**Secure Vault container core — separately reviewed, sound.** The flagship module was examined on its own merits, not only as the "older surface" the cross-module findings critique. The `.svault` format is a frozen, authenticated layout (`crates/sv-core/src/format.rs:4-23,78-108`): `MAGIC ‖ FORMAT_VERSION ‖ HEADER_LEN ‖ CBOR header ‖ payload ‖ minisign trailer`, signed over `BLAKE3(BLAKE3(MAGIC‖VERSION‖HEADER_LEN‖HEADER) ‖ BLAKE3(PAYLOAD))`, so any header or payload byte tamper breaks signature verification on read; section digests are recomputed, not stored. The header carries **only wrapped secrets, never plaintext keys**, and no item directory (the directory lives inside the single age-encrypted payload). CBOR uses `deny_unknown_fields` (`format.rs:245-256`). Master-key wrapping is domain-separated by field **and** vault UUID and is transplant-resistant by test (`crates/sv-core/src/keys.rs:52,192-233`). Session split/recover (`keys_split`/`keys_recover`, `src-tauri/src/service.rs:565-630`) is exercised by a count-precheck roundtrip test. The vault core is examined and sound; the §5 vault findings concern guard/naming gaps at its edges, not the container internals.

The caveats that qualify the GO:

- **Windows is a hard blocker and must be excluded from this release.** `env_clear()` (`crates/sv-age/src/lib.rs:107`, `src-tauri/src/payload.rs:45`) has no `SystemRoot`/`SystemDrive` allow-list and may *break* `age`/`age-keygen` on Windows; this is falsified on macOS but **untested on Windows**. Importantly, the Windows validation is **fully designed** — `.github/workflows/ci.yml:28-52` installs age on every OS, sets `SV_AGE_BIN`/`SV_AGE_KEYGEN_BIN`, and runs the real `age_backed_lifecycle_roundtrips` e2e (create → keygen → encrypt/decrypt, all through `env_clear`) inside the `windows-latest` job, with explicit PASS/FAIL criteria and the exact `SystemRoot`/`SystemDrive` fix pre-specified (`docs/RELEASE-READINESS.md:26-49`). The only gap is that **it has never executed** (the tree is not a git repo and has no remote). The gate is correct by inspection; running it is what remains.
- **Signing/notarization (H5) blocks _all_ distribution, including beta.** Per `docs/RELEASE-READINESS.md` (status: "blocked on H4 + H5"), H5 blocks any distribution incl. beta. A quarantined non-notarized nested binary is SIGKILLed on macOS (verified). Accordingly, this GO authorizes **macOS/Linux development/CI builds for the team**, not distribution of any kind (no beta, no public download) until H5's signed-artifact scripts and clean-machine launch pass.
- **Two UX defects mislead a first-time user** and should be fixed pre-release: the Home "Check a file" tile routes to signature-verify, not integrity-check (`index.html:69-73`), and two shipping tools are missing from the Home grid (`index.html:83-94`).

**Status discipline holds (verified).** `../docs/PRODUCT-VISION.md` is accurate: Verify Integrity is correctly marked partial; Steganography, Watermarking, Analysis, and Secure QR Transfer are all 🔬 *Research* with no product code. The implemented vs. planned vs. research labels match the code.

These caveats are bounded and have concrete, low-cost fixes. The release engineering — not the cryptography — is what is unfinished. Hence **go-with-caveats**, not no-go.

### Status note on "Integrity" as an in-scope module

"Integrity" is in scope but **partial**: `../docs/PRODUCT-VISION.md` marks **Verify Integrity** as 🟡 *Implemented (vault-bound)*. What ships is (a) `integrity_check`, which verifies a `.svault` container, and (b) the standalone `intact` hash-compare screen plus standalone Hash File / Verify Signature commands. The **generic** "file vs. expected hash/signature" verify (composing Hash File + Verify Signature for arbitrary files) is **not yet implemented**. Treat Integrity as released for the vault-container and hash-compare paths only.

---

## 2. Security

**Assessment:** Strong. Cryptographic correctness, secret hygiene, oracle-safety, the vault container's authenticated header/trailer binding, and DoS posture are all well-implemented and largely match the docs. Findings are positives or low-severity documentation/hygiene refinements. No blocker. The only release-relevant security item is the carry-forward Windows `env_clear` concern (tracked in §6 as a Windows-gating blocker, not a code defect on macOS/Linux).

| Severity | Finding | Evidence (file:line) | Recommendation |
|---|---|---|---|
| positive | Vault `.svault` container authenticated end-to-end: frozen layout signed over `BLAKE3(BLAKE3(header)‖BLAKE3(payload))`; header holds only wrapped secrets, no plaintext keys, no item directory; CBOR `deny_unknown_fields` | `crates/sv-core/src/format.rs:4-23,78-108,245-256` | No change. Any header/payload tamper fails signature verify on read. |
| positive | Master-key wrapping domain-separated by field **and** vault UUID; transplant-resistant by test | `crates/sv-core/src/keys.rs:52,192-233`; `src-tauri/src/service.rs:149-167` | No change. |
| positive | Oracle-safe error merge implemented end-to-end; wrong passphrase and tampered ciphertext both → `SV-UNAUTHORIZED` | `crates/sv-platform/src/error.rs:58-88`; `crates/sv-platform/src/artifact.rs:116`; `crates/sv-platform/src/sharing.rs:338`; `src-tauri/src/platform.rs:370-393,426-458` | No change. Keep: any future crypto failure must route to `AuthFailed`. |
| positive | Secret value types growth-proof, zeroizing, redacted, non-`Serialize`; `Serialize` boundary drawn around non-secrets only | `crates/sv-crypto-traits/src/lib.rs:151-254` | No change. |
| positive | Secret-sharing header binding `(group_id,n,k)` folded into derived key; duplicate-x/non-zero-x gates defend GF(2⁸) degeneracy | `crates/sv-platform/src/sharing.rs:121-129,269-339,605-630` | No change; matches threat-model doc. |
| positive | `age` subprocess hash-pinned, `env_clear`, no-shell, timeout-bounded; release fails closed on unpinned binary | `crates/sv-age/src/lib.rs:62-78,102-149,205-209`; `desktop/src/lib.rs:272-315` | No change (note H4 Windows carry-forward, §6). |
| positive | Pre-auth Argon2 cost ceiling (4 GiB / t≤64 / p≤64) guards attacker-supplied header before KDF runs | `crates/sv-platform/src/artifact.rs:38-42,98-104,205-214` | No change. |
| positive | Argon2id floor (19 MiB OWASP) + bounded calibration; verify-side intentionally omits floor so a weak device can open a strong-device vault | `crates/sv-crypto/src/policy.rs:15-22,38-68`; `crates/sv-crypto-traits/src/lib.rs:96-106` | No change. |
| positive | N1 passphrase IPC residual correctly scoped: zeroizes the copy it controls, honest about upstream serde buffers | `src-tauri/src/passphrase.rs:17-50`; `src-tauri/src/platform.rs:162,178,229` | No change. |
| positive | CSP restrictive, capabilities minimal; no fs/shell/http to webview; `withGlobalTauri` is the only loosening | `desktop/tauri.conf.json:22-24`; `desktop/capabilities/default.json:6-12` | No change; optionally drop style-src `'unsafe-inline'` later. |
| low | `.svenc`/`.svkey` header bound to artifact-type only via `derive_key`, not full header; the doc claim "any header/byte tamper fails secretbox::open" is slightly too strong (only 3 singleton-valued bytes are structurally- not AEAD-bound) | `crates/sv-platform/src/artifact.rs:121-138`; `crates/sv-crypto/src/secretbox.rs:20-34` | Tighten the doc comment, or pass full serialized header as AAD when the M5/H2 AAD-capable AEAD lands. No correctness change today. |
| low | Recover temp-file bridge writes secret piece bytes to disk; in-memory `Vec` not zeroized, temp file not overwritten before unlink (path is the new Secret-Sharing recover bridge) | `src-tauri/src/platform.rs:286-293`; contrast `crates/sv-age/src/lib.rs:254-266` | Zeroize `bytes` after write; reuse the `SecureIdentityFile` overwrite-before-unlink pattern. Low effort. |
| low | `secretbox` uses no AAD — sound for the chosen constructions, but header authentication depends on caller `derive_key` discipline (foot-gun for new consumers) | `crates/sv-crypto/src/secretbox.rs:1-7,20-34`; `crates/sv-sys-sodium/src/lib.rs:124-174` | On M5/H2 AAD migration, carry the header as AAD; until then document the `derive_key`-fold as a required step. |
| low | minisign verify is hand-rolled, self-consistent only; no cross-CLI interop gate (documented) | `crates/sv-crypto/src/minisign.rs:30-114`; `docs/M7-HARDENING.md:112-116` | Wire the planned CI step verifying against stock minisign before claiming interop in user copy. |
| low | `randombytes` FFI short-circuits `if buf.is_null() \|\| n == 0 { return 0; }`: a **null buffer with n>0 returns success (0) without filling**. Severity low because the sole caller is trusted vendored C that never passes null with n>0 | `crates/sv-sys-sss/src/lib.rs:39-48` | Optional hardening: split the conditions so a null buffer with n>0 returns -1. (Two getrandom versions in `Cargo.lock`: 0.2.x and 0.4.x — not load-bearing here.) |

---

## 3. UX (non-technical end-user lens)

**Assessment:** A large, genuine step forward. The consistent task-screen template, native pickers, drag-drop, inline field validation, plain-language coded-error mapping, and honest "Coming soon" placeholders all deliver the redesign's intent. Two items (the misrouted Home tile, and shipping tools missing from the Home grid) directly mislead or under-serve a first-time user and are worth fixing before release; the rest is cosmetic polish.

| Severity | Finding | Evidence (file:line) | Recommendation |
|---|---|---|---|
| positive | Coded-error mapping covers all 12 `SV-*` codes in plain English; oracle-safety preserved; `OUTPUT-EXISTS` becomes actionable | `desktop/frontend/main.js:20-33,39-62,309-318` | Keep. Optional: wrap `SV-INVALID-INPUT`/`SV-IO` `err.detail` with a friendly prefix. |
| positive | Inline validation at-field, focuses first offender, self-clears on edit; stakes-aware password-mismatch copy | `desktop/frontend/main.js:263-273,288-300,468-472` | Keep. Optional: move K-of-N policy error inline for consistency. |
| positive | Task-screen template uniform across all implemented screens; one reusable `.task` wrapper; smart output auto-fill | `index.html` task screens; `styles.css:244-280`; `desktop/frontend/main.js:386-396` | Keep; preserve as new modules are added. |
| medium | Home "Check a file" quick-start tile says "genuine and unchanged" but routes to signature-verify (`verify`), demanding a `.minisig`+`.pub` a checksum-only user lacks; the integrity screen (`intact`) matches the words | `index.html:69-73` (tile `data-goto="verify"`); verify vs `intact` screens | Retarget tile copy to its destination, or split into two tiles ("Check a signature" → verify, "Check a file is unchanged" → intact). **Fix pre-release.** |
| low | Two implemented tools (`intact`, `split-file`) are missing from the Home "All tools" grid, while coming-soon placeholders are shown there | `index.html:38,42` (sidebar) vs `index.html:83-94` (grid) | Add `intact` and `split-file` tiles to the grid; de-emphasize coming-soon tiles. (Both remain reachable via sidebar — discoverability gap, not unreachable.) |
| low | "Split a secret" and "Split a file" share the 🧩 icon and the button verb "Split into pieces"; adjacent in nav | `index.html:41-42` + the two split screens | Differentiate icon + button verb; or add a cross-link. (Screens already differ in heading/purpose/steps.) |
| low | Payload-file-must-be-kept risk under-surfaced; no in-app way to re-find the payload after closing; no always-visible "pieces alone are not enough" callout on Recover | split/recover handlers + screens | Add a persistent split-result callout and a standing Recover-screen hint; consider naming payload after the pieces' folder. |
| low | Copy/paste piece-code path is secrets-only (no codes for files) without an on-screen note; Recover success says "the secret was rebuilt" even for a recovered file | `desktop/frontend/main.js` recover handler | Add a one-line note on split-file; make recover-success copy object-neutral ("Recovered — saved to …"). |
| low | Coming-soon screens honest but uneven: 3 of 6 include "When you'd use it", 3 don't | `index.html` soon-* screens | Add a one-line "When you'd use it" to soon-qr/soon-detect/soon-analysis for parity. |
| low | Result-card containers use inconsistent initial classes (`note hidden` vs `result hidden`); cosmetic, overwritten on render | `index.html` task result divs | Normalize all task result containers to `class="result hidden"`. No behavior change. |

---

## 4. Maintainability & Architecture

**Assessment:** Unusually disciplined for this stage: clean dependency-inverted spine, 126 passing tests (reproduced locally; see provenance note), oracle-safe coded errors, zeroizing secret types, and a documented frozen-engine/additive-surface discipline. The principal risks are at the edges and in the docs, not the Rust core: the desktop crate is untested and outside every gate, the Tauri dependency tree escapes `cargo deny`, and there is meaningful doc drift. The single most consequential release fact is that **CI has never run** (the tree is not a git repo) — though the workflow itself (including the Windows e2e) is fully designed and correct by inspection.

| Severity | Finding | Evidence (file:line) | Recommendation |
|---|---|---|---|
| positive | Clean trait-ABI dependency inversion: `sv-core` production graph is backend-/FFI-free (`sv-crypto` dev-only); composition root injects impls | `crates/sv-crypto-traits/src/lib.rs:285-376`; `crates/sv-core/Cargo.toml:11-12,24`; `desktop/src/lib.rs:278-304` | Preserve. Keep new modules generic over `sv-crypto-traits`; inject at the root. |
| positive | Recover temp-file bridge correct, RAII-clean (cleanup across `?` early-return), well-tested (6 share/recover tests incl. oracle-safety) | `src-tauri/src/platform.rs:263-307` + share tests | No change; model for future paste/transcribe (QR) bridges. |
| medium | Desktop crate (large JS IPC + Tauri Rust) has zero tests and is workspace-excluded from fmt/clippy/test/deny; the 12-code `ApiError`↔`MESSAGES` contract is hand-duplicated with no parity test | `desktop/frontend/main.js:20-33,39-62`; `desktop/src/lib.rs`; `Cargo.toml` (excludes `desktop`); `crates/sv-types/src/lib.rs` | Add a JS unit test of `describe()` against a Rust-emitted fixture of every `ApiError` JSON; diff in CI. Generate `MESSAGES` keys from `sv-types`. Add `desktop/` to a CI clippy/fmt step. |
| medium | Tauri/webview tree (hundreds of extra packages) escapes `cargo deny`/`audit` because `desktop` is workspace-excluded | `Cargo.toml` (excludes `desktop`); `deny.toml`; desktop `Cargo.lock` vs workspace lock | Add a second `cargo-deny`/`cargo-audit` invocation inside `desktop/` in CI (enforce advisories+yanked, warn on licenses). Closes the supply-chain blind spot on the executed runtime. |
| medium | Doc drift — stale test counts across three release-gating docs (e.g. "77"/"80" vs reproduced 126) | `docs/RELEASE-READINESS.md`; `docs/VALIDATION-RESULTS.md`; `docs/DEPLOYMENT.md:276` | Update all three to 126 (by-crate breakdown in the provenance note above: `sv-platform` 38 and `sv-app` 25 are the heaviest; `sv-age` is 6, behind `SV_AGE_BIN`) or reference live CI output. `DEPLOYMENT.md`'s "expect 77 passing" would mislead a reviewer running the gate. |
| medium | Doc drift — CLAUDE.md and `../docs/PLATFORM-AUDIT.md` describe the crypto-services layer as "planned/NEW" when `sv-platform` is fully implemented and wired (38 tests); "H4" is used for two different items | `docs/M7-HARDENING.md` vs `docs/RELEASE-READINESS.md`; `CLAUDE.md` ("Planned clarifying move"); `../docs/PLATFORM-AUDIT.md` vs `crates/sv-platform/*` | Renumber one H4; update CLAUDE.md and `../docs/PLATFORM-AUDIT.md` to "implemented (`sv-platform`); vault not yet a consumer." Prevents a contributor rebuilding a shipped crate. |
| medium | Carry-forward items accurately tracked but genuinely unaddressed in code; the H4 Windows validation gate is **fully designed but has never executed** (not a git repo) | `crates/sv-age/src/lib.rs:107`, `src-tauri/src/payload.rs:45` (no Windows allow-list); `.github/workflows/ci.yml:28-52` (real `windows-latest` e2e); `docs/RELEASE-READINESS.md:26-49`; `desktop/icons/128x128.png` (299 B placeholder); H5 | Init git repo + remote so `ci.yml` runs the Windows env_clear e2e; pre-emptively add `SystemRoot`/`SystemDrive` allow-list. Treat H4/H5 as open blockers per docs. |
| low | Two parallel file-level crypto stacks (vault vs `sv-platform`) with divergent hashing: vault buffers whole file (uncapped `std::fs::read`), platform streams | `src-tauri/src/service.rs:71-72,520-523,685-687` vs `crates/sv-platform/src/integrity.rs:17-31`, `crates/sv-platform/src/lib.rs:70-71` | Track follow-up to delegate vault file ops to `sv-platform` once the engine can be un-frozen; until then document the intentional divergence at both `hash_file` sites. (Same digest; operational, not correctness, split.) |
| low | Stale workspace lint allowance (`todo = "allow"`) and stale M0 "no crypto logic" Cargo.toml header — no `todo!()` stubs remain | `Cargo.toml` header + lints | Remove `todo = "allow"` (or downgrade to warn); rewrite the header to the Phase-1-complete state. |
| low | Product version split: core 0.0.0 vs shell 0.1.0; `AppInfo.app_version` reports the 0.0.0 sv-app crate | `crates/sv-types/src/lib.rs:23`; `src-tauri/src/lib.rs:119-126`; `desktop/Cargo.toml`, `desktop/tauri.conf.json` | Keep FORMAT/SUITE/CONTRACT separation; pick one product-version source so `AppInfo.app_version` matches the user-visible shell version. |
| low | `rust-toolchain.toml` pins floating `channel = "stable"` despite a "reproducible" comment; MSRV 1.96 declared but there is **no `rust-version`-pinned CI job** | `rust-toolchain.toml`; `Cargo.toml` (`rust-version`); `.github/workflows/ci.yml` (uses `@stable` everywhere) | Add a dedicated **1.96 toolchain CI job** to enforce the declared MSRV; pin or soften the `rust-toolchain.toml` comment. |

---

## 5. Cross-Module Consistency (Secure Vault, Cryptography, Integrity, Secret Sharing)

**Assessment:** The four modules share a genuinely uniform spine — one frozen oracle-safe `ApiError` taxonomy, a strictly enforced no-secret-in-DTO rule with one documented exception, zeroizing `IpcPassphrase` at every handler, and a consistent command shape. The vault container core itself is sound (assessed in §1/§2); the real inconsistencies are between the older vault-bound surface and the newer `sv-platform` surface (missing data-safety guards on vault file ops, two secret-sharing formats, duplicated command names). None is a correctness/security blocker; they are the expected residue of a deliberately preserved older module plus a few naming/guard gaps worth tightening.

| Severity | Finding | Evidence (file:line) | Recommendation |
|---|---|---|---|
| positive | Single frozen oracle-safe `ApiError` taxonomy reused identically across modules; auth-merge and byte-identical `SV-IO` detail in both `From` impls | `crates/sv-types/src/lib.rs:169-237`; `crates/sv-core/src/error.rs:68-103`; `crates/sv-platform/src/error.rs:58-88` | Keep the two `From` impls in lockstep; add a doc-test asserting the `SV-IO` string is byte-identical. |
| positive | No-secret-in-DTO invariant uniform; one documented, correctly-scoped exception (`ShareSplitReport.share_b64`, text flow only; cleared for files) | `crates/sv-types/src/lib.rs:1-15,107-159`; `src-tauri/src/platform.rs:96-107,258-260` | No change. |
| positive | `PlatformError` omits `Timeout`/`Corrupted` — justified scoping (no subprocess / no signed container), both still collapse to the shared `ApiError` | `crates/sv-core/src/error.rs:28-29,49-52`; `crates/sv-platform/src/error.rs`; `crates/sv-platform/src/lib.rs:16-19` | No change; add a one-line comment noting the intentional absence. |
| positive | UI screen pattern uniform via shared `showScreen`/`runTask`/`renderResult`/coded-error pipeline; research modules consistently "soon"-tagged | `desktop/frontend/main.js:20-62,241-259,335-349`; `index.html` sidebar + soon screens | Keep; add an in-screen note that vault shares vs standalone pieces are not interchangeable. |
| positive | `../docs/PRODUCT-VISION.md` status labels accurate and trace to real, gate-shaped code (Implemented / vault-bound / Research) | `../docs/PRODUCT-VISION.md`; `desktop/src/lib.rs:174-230`; `crates/sv-platform/src/sharing.rs` | Keep command-name citations current so labels stay auditable. |
| low | Vault file ops lack the data-safety guards the platform module enforces: vault `sign_file` does `std::fs::write(&sig_path, …)` with **no `refuse_existing`** (silent `.minisig` overwrite); reads are uncapped/non-atomic | `src-tauri/src/service.rs:540-541,685-687` vs `crates/sv-platform/src/crypto.rs:114-116`, `crates/sv-platform/src/integrity.rs:42-43`, `crates/sv-platform/src/lib.rs:96-131` | Add `refuse_existing` + read cap (ideally `write_atomic`) to vault `sign_file`/`verify_file`/`hash_file`/`integrity_check`, or delegate to `sv-platform`. Blast radius bounded (regenerable sig / OOM). |
| low | Two parallel secret-sharing implementations diverge in magic (`SVSH` 4B vs `SVSSS/SVSSP` 6B), extension (`.svshare` vs `.svss`+`.payload.svss`), envelope, and DTO secret-handling; vault recover lacks the standalone duplicate-x/non-zero-x/payload-binding pre-checks | `src-tauri/src/service.rs:53-56,591,613-628` vs `crates/sv-platform/src/sharing.rs:58-60,296-329,465-467` | Intentional/documented; keep separate per policy. Surface non-interchangeability in-app; consider back-porting degeneracy pre-checks to vault recover. |
| low | Duplicated command names for identical operations across the two managed states (`integrity_hash` vs `integrity_hash_file`; `verify_file` vs `integrity_verify_signature`); paths can drift (platform caps reads, vault does not) | `desktop/src/lib.rs:124-127,139-146,173-189`; `src-tauri/src/service.rs:520-523`; `crates/sv-platform/src/integrity.rs:17-52` | Pick one home (the `sv-platform` pair, per the crypto-services direction) and retire/delegate the vault duplicates, or align names. |
| low | Magic-byte/extension conventions coherent within the platform layer (6-byte zero-padded + domain-separated derive) but the vault uses an older 4-byte `SVSH` convention | `crates/sv-platform/src/lib.rs:44-46`, `crates/sv-platform/src/sharing.rs:58-60`, `crates/sv-platform/src/artifact.rs:135-137` vs `src-tauri/src/service.rs:53` | Document a single magic/extension registry; migrate the vault format to the 6-byte convention if ever revised. |
| low | `IntegrityReport.blake3_ok` overloaded: in pure signature-verify paths it mirrors `signature_ok` rather than its documented "content hash matched" meaning (no path computes them independently) | `src-tauri/src/platform.rs:149-153`; `src-tauri/src/service.rs:512-516`; `crates/sv-platform/src/integrity.rs:48-51`; `crates/sv-types/src/lib.rs:96-101` | Add a dedicated 2-field result for pure signature verify, or update the docstring. UI reads only `signature_ok`, so no user-visible bug. |

---

## 6. Highest-Priority Remaining Gaps (ranked, all dimensions)

### A. Blocks release

1. **[BLOCKER — Windows] `env_clear()` may break `age`/`age-keygen` on Windows; untested; CI gate designed but never run.** `crates/sv-age/src/lib.rs:107`, `src-tauri/src/payload.rs:45` (no `SystemRoot`/`SystemDrive` allow-list). The validation gate is fully designed and correct by inspection — `.github/workflows/ci.yml:28-52` runs `age_backed_lifecycle_roundtrips` on `windows-latest` with explicit PASS/FAIL criteria (`docs/RELEASE-READINESS.md:26-49`); it has never executed (not a git repo).
   **Next action:** Ship **macOS/Linux only**. To enable Windows: init git repo + remote so `ci.yml` runs the Windows env_clear e2e, and pre-emptively add a `SystemRoot`/`SystemDrive` allow-list to `sv-age::run()` and `payload.rs`. Do not claim Windows support until that job passes.

2. **[BLOCKER — distribution, incl. beta] Signing/notarization (H5) unaddressed.** `docs/RELEASE-READINESS.md` status is "blocked on H4 + H5"; bundle is inactive and icons are 299-byte placeholders (`desktop/icons/128x128.png`); a quarantined non-notarized nested binary is SIGKILLed on macOS (verified).
   **Next action:** Provision signing/notarization credentials and real branding icons (`cargo tauri icon`); run the macOS + Windows signed-artifact validation scripts and a clean-machine launch green before **any** distribution. **No beta distribution may begin** until H5 passes — only internal/CI builds for the development team.

3. **[BLOCKER — gate credibility] No CI has ever run; the release gate hinges on it.** Tree is not a git repo. The heaviest tests (the Argon2id-driven `sv-platform` suite and `sv-app`'s age-backed lifecycle e2e) have never run in CI.
   **Next action:** Initialize repo + remote; run the full workflow (fmt/clippy/build --locked/test/deny + the OS matrix) and confirm green before declaring the gate passed. This also unblocks #1.

### B. High (fix before release; not strictly blocking)

4. **[HIGH — UX] Home "Check a file" tile misroutes a checksum-only user into a 3-field signature form.** `index.html:69-73` (`data-goto="verify"`).
   **Next action:** Retarget the tile to the `intact` screen (or split into two tiles) so wording matches destination.

5. **[HIGH — maintainability] Desktop crate untested and outside all gates; `ApiError`↔`MESSAGES` 12-code contract hand-duplicated.** `Cargo.toml` (excludes `desktop`); `desktop/frontend/main.js:20-33`; `crates/sv-types/src/lib.rs`.
   **Next action:** Add a CI clippy/fmt step for `desktop/`, plus a JS `describe()` test diffed against a Rust-emitted `ApiError` fixture; ideally generate `MESSAGES` keys from `sv-types`.

6. **[HIGH — supply chain] The Tauri/webview tree escapes `cargo deny`/`audit`.** `Cargo.toml` (excludes `desktop`); `deny.toml`.
   **Next action:** Add a second `cargo-deny`/`cargo-audit` invocation inside `desktop/` in CI (enforce advisories+yanked).

### C. Medium (fix soon; safe post-release)

7. **[MEDIUM — UX] Two shipping tools (`intact`, `split-file`) missing from Home grid; coming-soon placeholders shown instead.** `index.html:83-94` vs sidebar `index.html:38,42`. → Add `intact` and `split-file` tiles.

8. **[MEDIUM — docs] Stale test counts in three gating docs (77/80 vs reproduced 126).** `docs/RELEASE-READINESS.md`, `docs/VALIDATION-RESULTS.md`, `docs/DEPLOYMENT.md:276`. → Update to 126 (by-crate breakdown in the provenance note) or reference live CI output.

9. **[MEDIUM — docs] CLAUDE.md and `../docs/PLATFORM-AUDIT.md` call shipped `sv-platform` "planned/NEW"; "H4" overloaded.** → Renumber one H4; mark `sv-platform` implemented (vault not yet a consumer).

### D. Low (post-release hygiene)

| # | Item | Evidence (file:line) | Next action |
|---|---|---|---|
| 10 | Tighten `.svenc`/`.svkey` "any tamper fails" doc claim or adopt AAD | `crates/sv-platform/src/artifact.rs:121-138` | Document AEAD-bound vs structurally-validated fields; carry header as AAD on M5/H2 migration. |
| 11 | Zeroize recover-bridge `bytes`; overwrite temp file before unlink | `src-tauri/src/platform.rs:286-293` | Apply `zeroize` + `SecureIdentityFile` overwrite pattern. |
| 12 | Vault file ops missing `refuse_existing`/read-cap/atomic write (vault `sign_file` silently overwrites `.minisig`) | `src-tauri/src/service.rs:540-541,685-687` | Add guards or delegate to `sv-platform`; at minimum add `refuse_existing` to vault `sign_file`. |
| 13 | Two divergent secret-sharing formats; vault recover lacks degeneracy pre-checks | `src-tauri/src/service.rs:53-56,613-628`; `crates/sv-platform/src/sharing.rs:296-329` | Surface non-interchangeability in UI; back-port duplicate-x/non-zero-x pre-checks. |
| 14 | Duplicated/inconsistently-named integrity/verify commands | `desktop/src/lib.rs:124-127,173-189` | Consolidate onto the `sv-platform` pair or align names. |
| 15 | "Split a secret"/"Split a file" share icon + button verb | `index.html:41-42` + split screens | Differentiate icon and button verb. |
| 16 | Payload-file footgun under-surfaced; piece-code path asymmetric; recover says "secret" for files | `desktop/frontend/main.js` recover/split handlers | Persistent payload callout + standing recover hint; object-neutral success copy. |
| 17 | minisign cross-CLI interop gate not wired | `crates/sv-crypto/src/minisign.rs:30-114` | Wire planned stock-minisign CI verification before claiming interop. |
| 18 | Stale `todo = "allow"` + M0 Cargo.toml header | `Cargo.toml` header + lints | Remove allowance; update header to Phase-1-complete. |
| 19 | Floating `channel = "stable"` vs reproducibility claim; no `rust-version`-pinned CI job for MSRV 1.96 | `rust-toolchain.toml`; `.github/workflows/ci.yml` | Add a dedicated 1.96 toolchain CI job; pin a concrete toolchain or soften the comment. |
| 20 | Product-version split (0.0.0 core vs 0.1.0 shell) surfaced in About panel | `src-tauri/src/lib.rs:119-126`; `desktop/tauri.conf.json` | Single product-version source for `AppInfo.app_version`. |
| 21 | `IntegrityReport.blake3_ok` overloaded vs docstring (mirrors `signature_ok` in pure verify) | `crates/sv-types/src/lib.rs:96-101`; `src-tauri/src/platform.rs:149-153` | Split DTO for pure verify or fix docstring. |
| 22 | `secretbox` no-AAD foot-gun for future consumers | `crates/sv-crypto/src/secretbox.rs:1-7` | Document `derive_key`-fold as required; carry header as AAD post-migration. |
| 23 | `randombytes` `\|\|` short-circuit returns success for null-buffer-with-n>0 without filling | `crates/sv-sys-sss/src/lib.rs:39-48` | Split the conditions so null-with-n>0 returns -1 (sole caller is trusted vendored C). |
| 24 | Two parallel file-crypto stacks (buffered uncapped vs streaming hash) | `src-tauri/src/service.rs:520-523` vs `crates/sv-platform/src/integrity.rs:17-31` | Document intentional divergence; converge when engine un-frozen. |
| 25 | Inconsistent result-card initial classes; uneven coming-soon depth | `index.html` result divs + soon screens | Normalize to `result hidden`; add "When you'd use it" to 3 placeholders. |

---

**Bottom line:** The implemented modules — including the Secure Vault container core (authenticated CBOR header, master-key wrapping, session split/recover), reviewed on its own merits and found sound — are cryptographically and architecturally strong enough to release on macOS/Linux as a go-with-caveats. Integrity ships only for the vault-container and hash-compare paths; generic file-vs-expected verify is not yet implemented. Status discipline holds: research and QR features are correctly labeled 🔬. The gating work is release engineering — running the (already-designed) CI for the first time, resolving the Windows `env_clear` question, and provisioning signing — not core correctness. Per the cited H5 rule, **no distribution including beta** may begin until signing passes. Fix the misrouted Home tile and close the desktop test/audit gaps in parallel; everything else is post-release hygiene.
