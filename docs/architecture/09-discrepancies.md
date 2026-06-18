# 9. Documentation ↔ Implementation Discrepancies

This pass cross-checked the existing docs against the source. The **code is the source of truth**;
items below are places where prose (in docs or code comments) lagged the implementation. None were
defects in the shipping behavior — they were documentation-currency issues. Severity is editorial
(does a reader get a wrong picture?), not security.

> **✅ Reconciled (2026-06-17).** All five items below were **fixed** in a subsequent
> documentation-reconciliation pass (the one that produced this note): stale milestone/CI/release
> claims were brought current across `Cargo.toml`, the crate manifests, `sv-core/src/lib.rs`,
> `CI-VALIDATION.md`, `DEPLOYMENT.md`, `RELEASE-READINESS.md`, `VALIDATION-RESULTS.md`,
> `RELEASE-READINESS-TOOLKIT.md`, and `M0-CONTRACTS.md`. The authoritative current test count is
> **253 functions (249 passing + 4 `#[ignore]` env-gated e2e)**, verified via `cargo test --workspace`.
> The table records what was found and how each was resolved.

| ID | Where | Claim (as found) | Resolution |
|----|-------|------------------|------------|
| D-1 | `RELEASE-READINESS-TOOLKIT.md` body | "not a git repo / CI has never run / H4 untested on Windows" | **Fixed** — added a read-first currency banner, brought §0 current, and rewrote the blocker list + assessment: CI ran green (commit `780444d`), H4 validated, repo on GitHub. |
| D-2 | `CI-VALIDATION.md` (127) vs current tree | "127 workspace tests" read as current | **Fixed** — measured **253 (249 pass + 4 env-gated e2e)**; CI-VALIDATION keeps its dated run figures with a currency note; DEPLOYMENT/RELEASE-READINESS/VALIDATION-RESULTS updated to the current count. |
| D-3 | `Cargo.toml` header + `todo` lint note | "Milestone M0 … no crypto logic … `todo!()` stubs for M1–M6" | **Fixed** — header rewritten to the Phase-1-complete state; the `todo`-lint comment notes the stubs are gone (lint value left unchanged — not a functionality change). |
| D-4 | `RELEASE-READINESS-TOOLKIT.md:125` + `DEPLOYMENT.md` | "299 B placeholder" / "placeholder PNGs" | **Fixed** — both now describe the real **interim** icon set. |
| D-5 | "H" namespace overload | Bare "H4"/"H1" across docs | **Mitigated** — `M0-CONTRACTS.md` §8 now routes assumptions to the `M5/M6` decision docs; the hardening-risk vs header-schema H-series distinction is stated in `RELEASE-READINESS.md`, `08-testing-and-validation.md`, and the §0 log. A full renumber remains deliberately declined. |

## Detail and recommendations

*The subsections below are the original analysis of each item. Their recommendations have since been
**applied** in the 2026-06-17 reconciliation pass (see the banner above); they are retained to record
the reasoning and the exact source locations.*

### D-1 — Stale "pre-CI / pre-git" narrative in RELEASE-READINESS-TOOLKIT.md

The document's **resolution log (§0)** is current — line 40 acknowledges CI/H4 status and line 42 the
icon swap — but the **assessment body and the prioritized-blocker list still read as if CI had never
run and the tree were not a git repo**:

- `:56` — *"untested on Windows … the only gap is that it has never executed (the tree is not a git
  repo and has no remote)."*
- `:115` — *"the single most consequential release fact is that CI has never run (the tree is not a
  git repo)."*
- `:125`, `:156`, `:162` — repeat "fully designed but has never executed (not a git repo)" / "No CI
  has ever run."

This contradicts: (a) the same file's §0; (b) [docs/CI-VALIDATION.md](../CI-VALIDATION.md) (all jobs
green on `780444d`, Windows H4 e2e passed); (c) [docs/RELEASE-READINESS.md](../RELEASE-READINESS.md)
(H4 marked resolved); and (d) the repository's own git/CI state. **Recommendation:** rewrite the §1/§3
narrative and blocker list to reference the green CI run and mark **H4 resolved**, leaving **H5
(signing)** as the lone distribution blocker — exactly as §0 and `RELEASE-READINESS.md` already state.
(This is a CI/git-status reconciliation, separate from the M-7 bundle/config reconciliation already
completed.)

### D-2 — Test-count currency

[docs/CI-VALIDATION.md](../CI-VALIDATION.md) reports 127 passing workspace tests for commit
`780444d`. A scan of the current tree finds ~253 `#[test]` functions (breakdown in
[08-testing-and-validation.md](08-testing-and-validation.md) §8.2). The figures are not in conflict
*as of their respective commits* — the tree simply grew (stego 74, platform 46, command-surface 39
dominate the delta), and some tests are environment-gated. **Recommendation:** when quoting a test
count, either re-run `cargo test --workspace` and cite the date/commit, or phrase it as "≥ 127 as of
`780444d`." This package uses the measured figure and flags the provenance.

### D-3 — Stale milestone comment in the workspace manifest

[Cargo.toml](../../Cargo.toml) opens with a comment fixing the workspace at "Milestone M0 …
**No crypto logic is implemented here (that begins in M1)**," and the clippy `todo = "allow"` note
says the workspace "ships `todo!()` stubs for M1–M6." Both describe the project's *starting* state;
M1–M7 are now implemented and the stubs are gone. The comment is harmless to the build but
misleading to a new reader who treats it as current. **Recommendation:** update the header comment to
describe the current multi-module workspace (or delete the M0-specific framing); the `todo = "allow"`
lint can stay or be reconsidered, but its rationale comment is obsolete.

### D-4 — Icon-size citation

The `:125` evidence cell still cites the original 299-byte placeholder for `128x128.png`; the file is
now a real interim icon (≈6.1 KB), and the §0 log already records the replacement. **Recommendation:**
remove the "(299 B placeholder)" parenthetical from the evidence cell.

### D-5 — "H" namespace overload

`docs/M5-SCHEMA-DECISIONS.md` uses **H1–H6** for *header-schema* decisions; `docs/VALIDATION-PLAN.md`
/ `RELEASE-READINESS*.md` use **H1–H14** for *hardening-risk* hypotheses (H4 = Windows `env_clear`,
H5 = signing). The frozen design docs scope these explicitly, but a casual reader can conflate, e.g.,
"H4" the schema decision with "H4" the Windows hardening. **Recommendation:** keep the explicit
"header-schema H<n>" / "hardening-risk H<n>" prefixes everywhere, including `M0-CONTRACTS.md`.

## Things that are correct (checked, not discrepancies)

These were verified to **match** the implementation and are recorded so they are not re-flagged:

- **`bundle.active: true`, `targets: "all"`, `resources: ["binaries/**/*"]`** in
  [desktop/tauri.conf.json](../../desktop/tauri.conf.json) — matches `SIGNING-REQUIREMENTS.md`,
  `DEPLOYMENT.md`, `CI-VALIDATION.md` after the M-7 reconciliation.
- **The Cryptography module's Encrypt/Decrypt File uses Argon2id + `secretbox` (`SVENC`), not `age`.**
  This matches `docs/TOOLKIT-PHASE1-DESIGN.md` ("Option A") and `PRODUCT-VISION.md`; `age` is a
  vault-only concern. A reader skimming "Cryptography — Encrypt/Decrypt File (age)" in older
  top-level summaries could misread this, but the design docs and code agree.
- **`KdfDescriptor.algorithm: String` (a non-secret display DTO) vs. the on-disk `KdfRecord` carrying
  the `KdfParams` enum tag** — these are deliberately two layers. The on-disk redundant free-form
  string was removed (header-schema H6, [crates/sv-core/src/format.rs:108](../../crates/sv-core/src/format.rs#L108));
  the DTO string is for UI transparency only. Not a divergence.
- **"The vault is not yet a consumer of `sv-platform`"** — accurately labeled as a planned step in
  `CLAUDE.md` and `PRODUCT-VISION.md`; the vault uses its own `sv-core` hash/sign/verify paths. Correct
  as documented.
- **`SV_*_BIN` runtime overrides are debug-only** — `DEPLOYMENT.md` and `binaries/README.md` match
  [desktop/src/lib.rs:513](../../desktop/src/lib.rs#L513) after the M-3 doc ripple.
