# 11 · SVG Architecture Package

Publication-quality, vector (SVG) architecture diagrams for the **Secure Vault — Security & Privacy
Toolkit**, suitable for a System Analysis & Design report, thesis, technical documentation, or project
defense. Five board-level figures, hand-curated for print (dark-on-light, no decorative effects),
each grounded strictly in the source code.

> **Primary source of truth is the source code under `secure-vault/`.** Every box, edge, and label in
> these diagrams maps to a real crate, file, command, or configuration value (see *Source files*
> below). Nothing is invented; assumptions and deliberate simplifications are listed explicitly.

## Files

| File | Diagram | Canvas |
|------|---------|--------|
| [ARCH-01-overall-system-architecture.svg](ARCH-01-overall-system-architecture.svg) | Overall system architecture | 1240 × 985 |
| [ARCH-02-security-trust-boundaries.svg](ARCH-02-security-trust-boundaries.svg) | Security & trust boundaries | 1240 × 1010 |
| [ARCH-03-secure-file-lifecycle.svg](ARCH-03-secure-file-lifecycle.svg) | Secure file lifecycle | 1500 × 880 |
| [ARCH-04-component-dependency-map.svg](ARCH-04-component-dependency-map.svg) | Component dependency map | 1280 × 1100 |
| [ARCH-05-deployment-architecture.svg](ARCH-05-deployment-architecture.svg) | Deployment architecture | 1240 × 880 |
| [generate-svgs.mjs](generate-svgs.mjs) | Deterministic generator (reproduces all five) | — |

The **SVGs are the deliverable**; `generate-svgs.mjs` is a dependency-free Node script that reproduces
them so typography and spacing stay consistent and the figures remain editable at source. Regenerate
with `node generate-svgs.mjs`. The SVGs are also directly editable in Inkscape / Illustrator / any text
editor (plain `<rect>` / `<text>` / `<line>`, a shared `<style>` block, one arrowhead `<marker>`).

## Purpose of each diagram

- **ARCH-01 — Overall system architecture.** The whole system in one picture: `User → Tauri WebView →
  IPC command surface → composition root (5 managed states) → six domain crates → shared crypto
  platform → bundled backends`. Establishes the major modules and how they relate. Use as the opening
  architecture figure.

- **ARCH-02 — Security & trust boundaries.** The trust zones (untrusted input → sandboxed WebView →
  trusted native backend → security-critical crypto core → hardened external subprocesses → file
  system) and the controls enforced at each boundary (IPC, process, I/O). Use in the security chapter.

- **ARCH-03 — Secure file lifecycle.** End-to-end data flow `file/secret → protect → store · hide ·
  transfer → recover → decrypt`, drawn as four independent lanes (Vault, File encryption,
  Steganography, Secret sharing) plus the optional QR transport. Makes the two distinct encryption
  mechanisms explicit. Use to explain the user-facing workflows.

- **ARCH-04 — Component dependency map.** The workspace crates and their **exact internal Cargo
  dependencies**, with security-critical components highlighted and external tool spawns (age,
  ExifTool) shown. Use in the module-design chapter.

- **ARCH-05 — Deployment architecture.** Runtime deployment: the application bundle, its bundled +
  hash-pinned resources, hardened subprocess execution, and interaction with the OS and the user's
  filesystem. Use in the deployment/packaging chapter.

## Source files used to derive the architecture

All paths are relative to `secure-vault/`. These were read directly during the audit that produced
this package (the same audit behind `docs/architecture/10-report-diagrams.md`).

- **Composition / IPC / deployment:** `app/src/lib.rs` (the real Tauri composition root — 5
  `.manage(...)` states, 38 `#[tauri::command]`s, `build_backend` / `build_meta` binary resolution +
  BLAKE3 pin), `app/tauri.conf.json` (`frontendDist`, `withGlobalTauri`, CSP, `bundle.resources:
  ["binaries/**/*"]`, `targets: all`), `app/build.rs` (`emit_pin` for `age` / `age-keygen`
  (mandatory) and `stage_exiftool` + pin (optional); release fail-closed), `app/capabilities/default.json`
  (the webview allowlist), `src-tauri/src/{lib,service,platform,meta,stego,watermark,payload,passphrase}.rs`.
- **Frontend:** `app/frontend/{index.html,main.js,i18n.js,styles.css}`.
- **Crypto platform:** `crates/sv-crypto-traits/src/lib.rs`, `crates/sv-crypto/src/{lib,minisign,secretbox,policy}.rs`,
  `crates/sv-sys-sodium/src/lib.rs`, `crates/sv-sys-sss/src/{lib.rs,build.rs}`, `crates/sv-age/src/lib.rs`.
- **Vault & services:** `crates/sv-core/src/{lib,container,format,keys,service,error}.rs`,
  `crates/sv-platform/src/{lib,crypto,integrity,sharing,artifact,error}.rs`.
- **Modules:** `crates/sv-stego/src/**`, `crates/sv-meta/src/lib.rs`, `crates/sv-qr/src/lib.rs`,
  `crates/sv-watermark/src/lib.rs`.
- **Contracts:** `crates/sv-types/src/lib.rs` (the coded `ApiError`), and **every crate's `Cargo.toml`**
  (the exact dependency edges in ARCH-04 were taken from the manifests, not inferred).
- **Cross-checked against:** the design package `docs/architecture/01`–`10` (notably `09-discrepancies.md`,
  including the 2026-06-18 audit addendum).

## Assumptions & deliberate simplifications

These are the only places the diagrams abstract or make a judgment; nothing else is added beyond what
the code shows.

1. **Package location.** Placed at `docs/11-svg-architecture/` (a sibling of the numbered design
   package `docs/architecture/`, which contains files `01`–`10`). The "11" continues that series'
   numbering.
2. **Security-critical classification (ARCH-01/04).** A component is marked *security-critical* (red)
   when it **handles key material, performs cryptography, links C/FFI, or executes an external
   binary**: `sv-crypto`, `sv-core`, `sv-platform`, `sv-sys-sodium`, `sv-sys-sss`, `sv-age`, and the
   bundled `age` / `libsodium` paths. This is an editorial classification using that stated criterion.
3. **ARCH-04 omitted edges (disclosed on-diagram).** For legibility, `sv-app`'s direct dependencies on
   `sv-crypto-traits` / `sv-crypto` / `sv-types`, and `app`'s dependencies on `sv-age` / `sv-meta`
   / `sv-types`, are **not drawn** — they exist in the manifests. Every other edge is exact.
4. **Two encryption mechanisms (ARCH-03).** The Vault payload uses **age**; standalone file encryption
   uses **Argon2id + secretbox (SVENC)**. They are drawn as separate lanes because they are separate
   pipelines (the prose vision sometimes blurs this — see `docs/architecture/09-discrepancies.md`).
5. **Vault ⇎ sv-platform.** The diagrams reflect the verified fact that **the vault does not route
   through `sv-platform`** today (it reaches the primitives directly); ARCH-01/04 show this.
6. **ARCH-05 is OS-agnostic.** Per-OS bundle internals (`.app` / `.msi` / AppImage) differ; the figure
   shows the **logical** structure (Tauri runtime + `frontendDist` + `bundle.resources`). Code
   signing / notarization (hardening item **H5**) and a public signed installer are **out of scope for
   internal use** and are labeled as such, not drawn as steps. Bundling itself (`bundle.active: true`,
   `targets: all`) is configured.
7. **ExifTool is optional.** Shown as fail-closed: a packaged build self-stages + pins it, but the
   Analysis module disables itself if no pinned ExifTool resolves.
8. **Screen count.** "22 screen sections (20 routable)" — two `soon-*` placeholder screens exist but
   are unwired (per the frontend audit / `09-discrepancies.md`).

No uncertainty remains about the structural facts drawn (crate graph, managed states, command count,
formats, key hierarchy, bundling) — each was verified against source this pass. The only judgment
calls are items 2 and 6 above.

## Relationship to the Mermaid and PlantUML diagrams

This package is a **hand-curated, print-styled re-expression** of the architecture already captured,
in finer grain, by the two notation sets in `docs/architecture/`:

- `docs/architecture/10-report-diagrams.md` — **Mermaid** (23 diagrams, `DIAG-01`…`DIAG-23`).
- `docs/architecture/10-report-diagrams.plantuml.md` — **PlantUML** (the same 23, syntax-checked + rendered).

The Mermaid/PlantUML sets are the **canonical, exhaustive reference** (one diagram per pipeline,
auto-renderable, diff-friendly in version control). This SVG package is a **small set of five
board-level figures** optimized for a printed report: consistent typography, legends, dark-on-light,
and a curated level of detail per page. The two are complementary — cite the SVGs in the report body
and reference the Mermaid/PlantUML set as the detailed appendix.

### SVG → Mermaid / PlantUML correspondence

| SVG | Consolidates these Mermaid / PlantUML diagrams (`DIAG-*`) | Notes |
|-----|-----------------------------------------------------------|-------|
| **ARCH-01** Overall system architecture | DIAG-02 (layered/container) · DIAG-01 (context) · DIAG-06 (IPC map) · DIAG-05 (primitive stack, backend tier) | A single figure spanning what DIAG-01/02/05/06 show across four. |
| **ARCH-02** Security & trust boundaries | DIAG-21 (trust boundaries) · DIAG-23 (secret lifecycle) · DIAG-22 (error oracle-safety) · DIAG-11 (signature-before-credential) | Adds the explicit boundary-control annotations from the security design. |
| **ARCH-03** Secure file lifecycle | DIAG-10 + DIAG-11 (vault seal/unseal) · DIAG-12 (file encrypt) · DIAG-15 (stego) · DIAG-17 (secret sharing) · DIAG-18 (QR) · DIAG-07/09 (format/keys) | Flattens six behavioral diagrams into one four-lane lifecycle. |
| **ARCH-04** Component dependency map | DIAG-03 (crate dependency graph) · DIAG-05 (primitive stack) · DIAG-04 (security-domain decomposition) | Same exact manifest edges as DIAG-03, with security highlighting + tool spawns. |
| **ARCH-05** Deployment architecture | DIAG-01 (context, bundled tools) · DIAG-21 (subprocess hardening) | Deployment/packaging is **new** here — not separately diagrammed in the Mermaid/PlantUML set. |

## Verification performed

- **Well-formedness:** all five pass `xmllint --noout`.
- **Visual render:** each SVG was rendered at its native pixel size with **Chrome headless** (which
  respects SVG dimensions) and inspected for overlaps, clipping, and label legibility.
- **Note on Quick Look:** macOS `qlmanage` clips SVGs wider than ~1240 px (a previewer viewport limit,
  not an SVG defect) — use a browser, Inkscape, or `rsvg-convert` to preview the wider figures
  (ARCH-03/04) at full width.

## Regenerating / editing

```sh
cd docs/11-svg-architecture
node generate-svgs.mjs        # rewrites the five ARCH-*.svg files
```

Edit colors, typography, or layout in `generate-svgs.mjs` (a single shared palette + `<style>` block
keeps all five consistent), or edit any `.svg` directly. To export for print:

```sh
# example (requires a renderer of your choice)
rsvg-convert -f pdf -o ARCH-01.pdf ARCH-01-overall-system-architecture.svg
```
