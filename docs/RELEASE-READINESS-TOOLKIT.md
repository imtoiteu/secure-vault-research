# Release-Readiness Review — Security & Privacy Toolkit

> **Path note (2026-09-04):** the Tauri shell directory `desktop/` was renamed `app/` when it
> became the shared desktop + Android + iOS crate. Paths cited below are the ones that existed
> when this document was written and are left unchanged, so the record stays accurate; read
> `desktop/...` as today's `app/...`.


**Scope:** Currently implemented modules — Secure Vault, Cryptography, Integrity (see status note below), Secret Sharing.
**Out of scope of *this* review (research-stage at review time, not assessed here):** Steganography, Watermarking, Analysis, Secure QR Transfer. *(Update 2026-06-17: all four have since been **implemented standalone** — see `../docs/PRODUCT-VISION.md` and [`docs/architecture/04-module-design.md`](architecture/04-module-design.md); they simply postdate this review's scope.)*
**Date:** 2026-06-15
**Method:** Produced by a multi-agent review (parallel security / UX / maintainability / consistency reviewers reading source, each finding adversarially verified against `file:line`). 44 findings raised, 44 kept after verification. One synthesized claim — the per-crate attribution in the test-count note — was **corrected during a final fact-check** (see the provenance note); the corrected figures are reproduced from local `cargo test` runs.

> **Doc-path convention used below.** This review is scoped to `secure-vault/`, so citations like `docs/RELEASE-READINESS.md` resolve under `secure-vault/docs/`. Two referenced docs live one directory up at the **repository top level**: `../docs/PRODUCT-VISION.md` and `../docs/PLATFORM-AUDIT.md`. They are cited with the `../docs/` prefix throughout. CI lives at `secure-vault/.github/workflows/ci.yml` (verified to exist).
>
> **Test count provenance (review-time figure — superseded; see Currency note).** At review time the suite was **126 workspace tests**, reproduced locally as `sv-age 6 + sv-app 25 + sv-core 22 + sv-crypto 20 + sv-crypto-traits 6 + sv-platform 38 + sv-sys-sodium 3 + sv-sys-sss 4 + sv-types 2 = 126`. **It has since grown to 253 (249 passing + 4 env-gated e2e)** as the stego/meta/qr/watermark modules and additional tests landed; the current per-crate breakdown is in §0. The longest-running remain the Argon2id-driven `sv-platform` tests and `sv-app`'s age-backed lifecycle e2e (gated behind `SV_AGE_BIN`). CI has since executed (commit `780444d`).

---

> ## ⚠️ Currency note (read first) — updated 2026-06-17
>
> This is a **dated, point-in-time review (2026-06-15)**; its findings below are **preserved as
> originally written**. Several are **now resolved** — do not read the body as current status:
> - **CI has run and is green** across the 3-OS matrix (commit `780444d`). The body's "CI has never
>   run / not a git repo / never executed" claims are **obsolete** — the repo is on GitHub.
> - **H4 (Windows `env_clear`) is validated**: the `age_backed_lifecycle_roundtrips` e2e ran green on
>   `windows-latest`. Windows is **no longer gated out** of the build/test gate; **H5 signing is the
>   sole remaining distribution blocker.**
> - **All Medium findings are fixed** (the release-readiness audit's M-series), including the
>   misrouted Home tile and the missing `intact`/`split-file` tiles; the **desktop crate is now
>   CI-gated** with an `ApiError ↔ UI` parity test.
> - **Generic file-vs-expected Verify Integrity is implemented** (`integrity_verify_integrity`,
>   `sv-platform`) — superseding the body's "not yet implemented" notes.
> - **Test count:** a local `cargo test --workspace` now reports **253 functions — 249 passing, 4
>   `#[ignore]` env-gated `age`/ExifTool e2e** (run in CI) — plus 1 desktop parity test. This replaces
>   every "126/127" figure below.
>
> See §0 (resolution log, updated) and **[`docs/architecture/`](architecture/README.md)** for the
> current authoritative picture.

---

## 0. Resolution log — release-engineering pass (2026-06-15; updated 2026-06-17)

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
- **#6 / #8 stale test counts** — **resolved + re-reconciled (2026-06-17)**: the suite has since
  grown well beyond the review's 126. A local `cargo test --workspace` now reports **253 test
  functions — 249 passing, 4 `#[ignore]` env-gated `age`/ExifTool e2e** (run in CI). Current
  per-crate (passing): `sv-stego 74 + sv-platform 46 + sv-app 37 + sv-core 22 + sv-crypto 20 +
  sv-watermark 11 + sv-meta 8 + sv-qr 8 + sv-age 6 + sv-crypto-traits 6 + sv-sys-sss 4 + sv-types 4 +
  sv-sys-sodium 3 = 249`; +4 ignored = 253; +1 desktop parity test. RELEASE-READINESS.md,
  DEPLOYMENT.md, VALIDATION-RESULTS.md, and CI-VALIDATION.md now carry these figures.
- **H4 Windows `env_clear`** — **resolved & validated on CI (2026-06-15)**: the
  `SystemRoot`/`SystemDrive`/`TEMP`/`TMP` allow-list landed in `sv-age` + `payload.rs`, and the
  `age_backed_lifecycle_roundtrips` e2e **ran green on the `windows-latest` job** (commit `780444d`).
  CI has executed (the repo is on GitHub). **H5 signing/notarization remains the sole distribution blocker.**
- **Placeholder icons** — **resolved (interim)**: a real `.png`/`.icns`/`.ico` set replaces the
  299-byte placeholder and is wired into `bundle.icon`; final brand assets still pending.

---

## 1. Executive Summary & Recommendation

### Recommendation: **GO, with caveats (desktop-only; Windows gated out; see distribution rule below)**

The implemented core is releasable for the macOS/Linux desktop target. The cryptographic spine is well-constructed and its documented security claims are matched by the source: the oracle-safe error merge is applied identically at every boundary (`crates/sv-platform/src/error.rs:58-88`, `crates/sv-core/src/error.rs:68-103`), secret value types are zeroizing, redacted, growth-proof, and non-`Serialize` (`crates/sv-crypto-traits/src/lib.rs:151-254`), the secret-sharing header binding via `derive_key` is cryptographically sound and tested (`crates/sv-platform/src/sharing.rs:121-129,605-630`), the `age` subprocess is hash-pinned/env-cleared/no-shell/timeout-bounded and fails closed in release (`crates/sv-age/src/lib.rs:62-149`; `desktop/src/lib.rs:272-315`), and the Argon2id floor meets OWASP guidance (`crates/sv-crypto/src/policy.rs:15-22`). The architecture is unusually disciplined (dependency-inverted trait ABI, `crates/sv-crypto-traits` → impls → backend-free domain crates), the workspace suite passes (now **249/253**, up from the 126 at review time — see Currency note), and the redesigned frontend delivers a consistent, plain-language, oracle-safe UX. **No security blocker was found in the code under review.**

**Secure Vault container core — separately reviewed, sound.** The flagship module was examined on its own merits, not only as the "older surface" the cross-module findings critique. The `.svault` format is a frozen, authenticated layout (`crates/sv-core/src/format.rs:4-23,78-108`): `MAGIC ‖ FORMAT_VERSION ‖ HEADER_LEN ‖ CBOR header ‖ payload ‖ minisign trailer`, signed over `BLAKE3(BLAKE3(MAGIC‖VERSION‖HEADER_LEN‖HEADER) ‖ BLAKE3(PAYLOAD))`, so any header or payload byte tamper breaks signature verification on read; section digests are recomputed, not stored. The header carries **only wrapped secrets, never plaintext keys**, and no item directory (the directory lives inside the single age-encrypted payload). CBOR uses `deny_unknown_fields` (`format.rs:245-256`). Master-key wrapping is domain-separated by field **and** vault UUID and is transplant-resistant by test (`crates/sv-core/src/keys.rs:52,192-233`). Session split/recover (`keys_split`/`keys_recover`, `src-tauri/src/service.rs:565-630`) is exercised by a count-precheck roundtrip test. The vault core is examined and sound; the §5 vault findings concern guard/naming gaps at its edges, not the container internals.

The caveats that qualify the GO:

- **Windows — RESOLVED (was a hard blocker at review time).** `env_clear()` (`crates/sv-age/src/lib.rs`, `src-tauri/src/payload.rs`) now carries a `SystemRoot`/`SystemDrive`/`TEMP`/`TMP` allow-list, and the `age_backed_lifecycle_roundtrips` e2e (create → keygen → encrypt/decrypt, all through `env_clear`) **ran green on the `windows-latest` CI job** (commit `780444d`, 2026-06-15; see [CI-VALIDATION.md](CI-VALIDATION.md)). The validation gate the review described as "designed but never executed" has executed and passed — Windows is **no longer excluded**.
- **Signing/notarization (H5) blocks _all_ distribution, including beta.** Per `docs/RELEASE-READINESS.md` (status: "blocked on H4 + H5"), H5 blocks any distribution incl. beta. A quarantined non-notarized nested binary is SIGKILLed on macOS (verified). Accordingly, this GO authorizes **macOS/Linux development/CI builds for the team**, not distribution of any kind (no beta, no public download) until H5's signed-artifact scripts and clean-machine launch pass.
- **Two UX defects mislead a first-time user** and should be fixed pre-release: the Home "Check a file" tile routes to signature-verify, not integrity-check (`index.html:69-73`), and two shipping tools are missing from the Home grid (`index.html:83-94`).

**Status discipline holds (verified).** `../docs/PRODUCT-VISION.md` is accurate and its labels match the code. *(At review time Steganography, Watermarking, Analysis, and Secure QR Transfer were 🔬 Research with no product code, and Verify Integrity was partial. Update 2026-06-17: all four modules are now ✅ Implemented (standalone) and generic Verify Integrity ships as `integrity_verify_integrity` — PRODUCT-VISION reflects this.)*

These caveats are bounded and have concrete, low-cost fixes. The release engineering — not the cryptography — is what is unfinished. Hence **go-with-caveats**, not no-go.

### Status note on "Integrity" as an in-scope module

"Integrity" was **partial** at review time: `integrity_check` (a `.svault` container) plus the standalone `intact` hash-compare screen and standalone Hash File / Verify Signature commands. *(Update 2026-06-17: the **generic** "file vs. expected hash/signature" verify — composing Hash File + Verify Signature for arbitrary files — is now **implemented** as `integrity_verify_integrity` (`sv-platform`), UI **Verify a download**; `../docs/PRODUCT-VISION.md` marks Verify Integrity ✅ Implemented (standalone). The "not yet implemented" note below is superseded.)*

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

**Assessment:** Unusually disciplined for this stage: clean dependency-inverted spine, a passing suite (249/253; 126 at review time), oracle-safe coded errors, zeroizing secret types, and a documented frozen-engine/additive-surface discipline. The principal risks the review flagged were at the edges and in the docs, not the Rust core. *(Update 2026-06-17: most are now closed — **CI has run green** (commit `780444d`), the **desktop crate is now CI-gated** (fmt/clippy/test + an `ApiError ↔ UI` parity test), and the doc drift is being reconciled. The Tauri dependency tree is still outside the workspace `cargo deny` *licenses* gate (a separate desktop advisory/bans/sources scan exists).)*

| Severity | Finding | Evidence (file:line) | Recommendation |
|---|---|---|---|
| positive | Clean trait-ABI dependency inversion: `sv-core` production graph is backend-/FFI-free (`sv-crypto` dev-only); composition root injects impls | `crates/sv-crypto-traits/src/lib.rs:285-376`; `crates/sv-core/Cargo.toml:11-12,24`; `desktop/src/lib.rs:278-304` | Preserve. Keep new modules generic over `sv-crypto-traits`; inject at the root. |
| positive | Recover temp-file bridge correct, RAII-clean (cleanup across `?` early-return), well-tested (6 share/recover tests incl. oracle-safety) | `src-tauri/src/platform.rs:263-307` + share tests | No change; model for future paste/transcribe (QR) bridges. |
| medium | Desktop crate (large JS IPC + Tauri Rust) has zero tests and is workspace-excluded from fmt/clippy/test/deny; the 12-code `ApiError`↔`MESSAGES` contract is hand-duplicated with no parity test | `desktop/frontend/main.js:20-33,39-62`; `desktop/src/lib.rs`; `Cargo.toml` (excludes `desktop`); `crates/sv-types/src/lib.rs` | Add a JS unit test of `describe()` against a Rust-emitted fixture of every `ApiError` JSON; diff in CI. Generate `MESSAGES` keys from `sv-types`. Add `desktop/` to a CI clippy/fmt step. |
| medium | Tauri/webview tree (hundreds of extra packages) escapes `cargo deny`/`audit` because `desktop` is workspace-excluded | `Cargo.toml` (excludes `desktop`); `deny.toml`; desktop `Cargo.lock` vs workspace lock | Add a second `cargo-deny`/`cargo-audit` invocation inside `desktop/` in CI (enforce advisories+yanked, warn on licenses). Closes the supply-chain blind spot on the executed runtime. |
| medium → **resolved (2026-06-17)** | Doc drift — stale test counts across the release-gating docs | `docs/RELEASE-READINESS.md`; `docs/VALIDATION-RESULTS.md`; `docs/DEPLOYMENT.md`; `docs/CI-VALIDATION.md` | **Done:** all reconciled to the current **253 (249 passing + 4 `#[ignore]` env-gated `age`/ExifTool e2e)**, plus 1 desktop parity test. |
| medium | Doc drift — CLAUDE.md and `../docs/PLATFORM-AUDIT.md` describe the crypto-services layer as "planned/NEW" when `sv-platform` is fully implemented and wired (38 tests); "H4" is used for two different items | `docs/M7-HARDENING.md` vs `docs/RELEASE-READINESS.md`; `CLAUDE.md` ("Planned clarifying move"); `../docs/PLATFORM-AUDIT.md` vs `crates/sv-platform/*` | Renumber one H4; update CLAUDE.md and `../docs/PLATFORM-AUDIT.md` to "implemented (`sv-platform`); vault not yet a consumer." Prevents a contributor rebuilding a shipped crate. |
| medium → **resolved** | The H4 Windows validation gate has executed; carry-forwards re-checked | `crates/sv-age/src/lib.rs`, `src-tauri/src/payload.rs` (allow-list landed); `.github/workflows/ci.yml` (real `windows-latest` e2e); `docs/RELEASE-READINESS.md`; `desktop/icons/` (real interim set) | **Done:** repo is on GitHub; the Windows `env_clear` e2e ran **green** (commit `780444d`); the `SystemRoot`/`SystemDrive` allow-list is in place; the 299-byte placeholder icons were replaced with a real interim set. **H5 (signing) is the only open distribution blocker.** |
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

> **Status (2026-06-17):** of the three review-time blockers, **#1 (Windows) and #3 (CI never run)
> are RESOLVED** — the repo is on GitHub and CI ran green across the matrix, including the Windows
> `env_clear` e2e (commit `780444d`). **Only #2 (H5 signing) remains** — and only for *distribution*;
> internal/CI/dev builds are unblocked.

1. **[RESOLVED — was Windows blocker] `env_clear()` on Windows.** The `SystemRoot`/`SystemDrive`/`TEMP`/`TMP` allow-list landed in `sv-age::run()` + `payload.rs`, and `age_backed_lifecycle_roundtrips` **ran green on `windows-latest`** (commit `780444d`, 2026-06-15; see [CI-VALIDATION.md](CI-VALIDATION.md)). Windows is no longer excluded.

2. **[BLOCKER — distribution, incl. beta] Signing/notarization (H5) unaddressed.** The bundle is **active** (`bundle.active: true`) and ships a real **interim** icon set (the 299-byte placeholders were replaced; final branding still pending), so the remaining distribution blocker is signing alone: no signing/notarization material exists, and a quarantined non-notarized nested binary is SIGKILLed on macOS (verified).
   **Next action:** Provision signing/notarization credentials and real branding icons (`cargo tauri icon`); run the macOS + Windows signed-artifact validation scripts and a clean-machine launch green before **any** distribution. **No beta distribution may begin** until H5 passes — only internal/CI builds for the development team. *(Out of scope for internal use per the internal-use mandate.)*

3. **[RESOLVED — was gate-credibility blocker] CI has run.** The repo is on GitHub and the full workflow (fmt/clippy/build --locked/test/deny + the 3-OS matrix) ran **green** (commit `780444d`), including the Argon2id-driven `sv-platform` suite and `sv-app`'s age-backed lifecycle e2e.

### B. High (fix before release; not strictly blocking)

4. **[RESOLVED — was HIGH UX] Home "Check a file" tile misroute.** The tile now routes to the integrity workflow; all Home/all-tools tiles were audited and the two live tools that had been missing (`intact`, `split-file`) were added (§0).

5. **[RESOLVED — was HIGH maintainability] Desktop crate untested and outside all gates.** `desktop/` now runs fmt/clippy(-D warnings)/test in CI, with an `ApiError ↔ UI message` parity test (`ui_contract`, 1:1 against `ApiError::ALL_CODES`); the duplicated `SV-IO` text was deduplicated via `ApiError::io_generic()` (§0).

6. **[MOSTLY RESOLVED — was HIGH supply chain] The Tauri/webview tree under `cargo deny`/`audit`.** CI now runs `cargo-deny` + `cargo-audit` over the desktop webview tree (advisories/bans/sources) in the supply-chain job (see [CI-VALIDATION.md](CI-VALIDATION.md)). **Residual:** the *licenses* gate is still not enforced on that tree — tracked as a Low item.

### C. Medium (fix soon; safe post-release)

7. **[RESOLVED — was MEDIUM UX] Two shipping tools (`intact`, `split-file`) missing from Home grid.** Both tiles were added to the Home grid (§0).

8. **[RESOLVED — was MEDIUM docs] Stale test counts in the gating docs.** Reconciled (2026-06-17) to the current **253 (249 passing + 4 env-gated e2e)** across RELEASE-READINESS.md, VALIDATION-RESULTS.md, DEPLOYMENT.md, and CI-VALIDATION.md.

9. **[RESOLVED — was MEDIUM docs] `sv-platform` mislabeled "planned/NEW"; "H4" overloaded.** CLAUDE.md and `../docs/PLATFORM-AUDIT.md` mark `sv-platform` implemented (vault not yet a consumer); the H-series namespaces are explicitly scoped (Header-schema H1–H6 vs hardening-risk H1–H14) (§0).

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

**Bottom line:** The implemented modules — including the Secure Vault container core (authenticated CBOR header, master-key wrapping, session split/recover), reviewed on its own merits and found sound — are cryptographically and architecturally strong enough to release on macOS/Linux as a go-with-caveats. *(Update 2026-06-17: generic file-vs-expected verify is now implemented (`integrity_verify_integrity`); the previously research-stage stego/watermark/analysis/QR modules now ship standalone. The release-engineering gaps the review flagged — running CI, the Windows `env_clear` question, the misrouted Home tile, the desktop test/audit gaps — are **closed**: CI ran green across the matrix (commit `780444d`), H4 is validated, and the desktop crate is CI-gated.)* The remaining gating work is **distribution signing (H5) only** — and per the H5 rule, **no distribution including beta** may begin until signing passes; internal/CI/dev builds are unblocked. (H5 is out of scope for internal use.)
