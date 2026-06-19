# 12 · Draw.io Architecture Package

Native, **editable Draw.io** (`.drawio`) versions of the five board-level architecture figures for
the **Secure Vault — Security & Privacy Toolkit**. Each file is built from real Draw.io shapes —
swimlanes, containers, boxes, connectors, labels, and legends — so it opens and edits natively in
[diagrams.net](https://app.diagrams.net) / the Draw.io VS Code or desktop app. **These are not
exported SVG/PNG**; they are the source diagrams.

> **Authoritative source = the architecture documents under [`../architecture/`](../architecture/)
> (files `01`–`10`).** The vector figures in [`../11-svg-architecture/`](../11-svg-architecture/) were
> used as a **visual-layout reference only**. Where the prose and the SVGs differed, the architecture
> documents won (see *Conflicts resolved in favour of the docs* below). Nothing here is invented; every
> box, edge, zone, and label traces to a cited document section.

## Files

| File | Diagram | Page (px) | Visual reference |
|------|---------|-----------|------------------|
| [ARCH-01-overall-system-architecture.drawio](ARCH-01-overall-system-architecture.drawio) | Overall system architecture (layered) | 1240 × 1024 | `ARCH-01-*.svg` |
| [ARCH-02-security-trust-boundaries.drawio](ARCH-02-security-trust-boundaries.drawio) | Security & trust boundaries | 1240 × 1052 | `ARCH-02-*.svg` |
| [ARCH-03-secure-file-lifecycle.drawio](ARCH-03-secure-file-lifecycle.drawio) | Secure file lifecycle (4 swimlanes) | 1500 × 902 | `ARCH-03-*.svg` |
| [ARCH-04-component-dependency-map.drawio](ARCH-04-component-dependency-map.drawio) | Component / crate dependency map | 1280 × 1140 | `ARCH-04-*.svg` |
| [ARCH-05-deployment-architecture.drawio](ARCH-05-deployment-architecture.drawio) | Deployment architecture | 1240 × 952 | `ARCH-05-*.svg` |
| [generate-drawio.py](generate-drawio.py) | Deterministic generator (reproduces all five) | — | — |

The `.drawio` files are the deliverable; `generate-drawio.py` is a dependency-free Python 3 (stdlib
only) script that reproduces them so the palette, typography, and spacing stay consistent and the
figures remain editable at source — the same convention as `../11-svg-architecture/generate-svgs.mjs`.
Regenerate with `python3 generate-drawio.py`.

## Source mapping — each file → the documents it was derived from

The five figures are a Draw.io re-expression of the same architecture captured, in finer grain, by the
Mermaid set in [`../architecture/10-report-diagrams.md`](../architecture/10-report-diagrams.md)
(`DIAG-01`…`DIAG-23`) and its PlantUML twin
[`10-report-diagrams.plantuml.md`](../architecture/10-report-diagrams.plantuml.md). Each ARCH figure
**consolidates** several `DIAG-*` views into one board-level page.

### ARCH-01 — Overall System Architecture
Layered swimlanes (User → WebView → IPC → composition root + 5 managed states → 6 domain crates →
shared platform → bundled backends), with the managed-state → crate mapping, the exact crate →
platform edges, and the `age` / ExifTool runtime spawns.

* **Primary:** [`01-system-overview.md`](../architecture/01-system-overview.md) §1.4–1.5 (system
  context, component map); [`03-system-architecture.md`](../architecture/03-system-architecture.md)
  §3.2 (layers), §3.5 (composition root); [`07-uml-diagrams.md`](../architecture/07-uml-diagrams.md)
  §7.2 (component diagram).
* **Consolidates:** `DIAG-02` (layered/container), `DIAG-01` (context), `DIAG-06` (IPC command/managed-state map),
  `DIAG-05` (primitive stack, backend tier).

### ARCH-02 — Security & Trust Boundaries
Zone bands (Untrusted → Sandboxed WebView → *IPC boundary* → Trusted backend → Critical crypto →
*Process boundary* → External tools → *I/O boundary* → Storage) with the per-boundary controls.

* **Primary:** [`06-security-design.md`](../architecture/06-security-design.md) §6.3 (boundaries &
  controls), §6.4 (oracle-safe errors), §6.5 (secret hygiene), §6.6 (subprocess hardening);
  [`03-system-architecture.md`](../architecture/03-system-architecture.md) §3.6 (trust boundaries).
* **Consolidates:** `DIAG-21` (trust boundaries & subprocess hardening), `DIAG-23` (secret lifecycle),
  `DIAG-22` (error oracle-safety), `DIAG-11` (signature-before-credential ordering).

### ARCH-03 — Secure File Lifecycle
Four independent protection lanes (Vault `sv-core` · File-encryption `sv-platform` · Steganography
`sv-stego` · Secret-sharing `sv-platform`/`sv-core`) across the stages *protect → store/hide/transfer
→ recover → decrypt*, sharing one input/output, plus the optional QR transport between *Shares* and
*Recover*.

* **Primary:** [`04-module-design.md`](../architecture/04-module-design.md) §4.2–4.7 (module
  behaviours); [`05-data-design.md`](../architecture/05-data-design.md) §5.2–5.5 (formats);
  [`07-uml-diagrams.md`](../architecture/07-uml-diagrams.md) §7.5–7.9 (sequences), §7.11 (DFD).
* **Consolidates:** `DIAG-10`/`DIAG-11` (vault seal/unseal), `DIAG-12` (file encrypt — Argon2id+secretbox),
  `DIAG-15` (steganography), `DIAG-17` (secret sharing), `DIAG-18` (QR), `DIAG-07`/`DIAG-09` (format/keys).

### ARCH-04 — Component Dependency Map
Workspace crates and their **exact internal Cargo dependencies** (`A → B` = "A depends on B"), with
security-critical components highlighted, `sv-core`'s `sv-crypto` dev-dependency dashed, and `age` /
ExifTool drawn as runtime subprocess spawns (not compile-time deps).

* **Primary:** [`03-system-architecture.md`](../architecture/03-system-architecture.md) §3.3 (crate
  inventory), §3.4 (production dependency graph);
  [`04-module-design.md`](../architecture/04-module-design.md) §4.1 (ABI + adapters).
* **Consolidates:** `DIAG-03` (crate dependency graph), `DIAG-05` (primitive stack), `DIAG-04`
  (security-domain decomposition).
* Edge set verified against [`09-discrepancies.md`](../architecture/09-discrepancies.md) (2026-06-18
  addendum): `sv-stego → {sv-crypto-traits, sv-crypto, sv-types}` and `sv-qr → sv-types` only;
  `sv-platform` is consumed solely by `sv-app`.

### ARCH-05 — Deployment Architecture
Nested deployment containers (OS → application bundle → bundled `bundle.resources` → hardened
subprocess), the runtime binary-resolution / BLAKE3-pin story, the OS-provided WebView, the user's
filesystem, and the explicit out-of-scope (H5 signing/notarization) note.

* **Primary:** [`01-system-overview.md`](../architecture/01-system-overview.md) §1.6 (deployment
  posture); [`07-uml-diagrams.md`](../architecture/07-uml-diagrams.md) §7.10 (deployment diagram);
  [`06-security-design.md`](../architecture/06-security-design.md) §6.6 (build → runtime resolution).
* **Consolidates:** `DIAG-01` (context, bundled tools), `DIAG-21` (subprocess hardening). Deployment
  packaging itself is **new** in this/the SVG package — it is not separately drawn in the Mermaid set.

### Coverage note
These five figures cover the architecture information the brief calls out — **components, trust
boundaries, data flows, security zones, deployment relationships, and component dependencies**. The
finer-grained behavioural figures (use-case `7.1`; class diagrams `7.3`/`7.4`/`DIAG-08`; per-pipeline
sequences `DIAG-10`…`DIAG-20`; the error-map `DIAG-22`; secret-lifecycle `DIAG-23`) already exist as
auto-renderable Mermaid + PlantUML in [`../architecture/`](../architecture/) and are referenced, not
duplicated, here.

## Conflicts resolved in favour of the docs

Per the brief, where the SVG visuals and the architecture documents differed, the **documents win**:

1. **Two distinct encryption mechanisms (ARCH-01/03).** The Vault payload uses **age**; standalone
   file encryption uses **Argon2id + `secretbox` (SVENC)** — different pipelines, drawn as separate
   lanes/labels. (`04-module-design.md` §4.3 note; `09-discrepancies.md` "Things that are correct".)
2. **Vault ⇎ `sv-platform` (ARCH-01/04).** The vault is **not yet a consumer** of `sv-platform`; it
   reaches the primitives via `sv-crypto-traits`/`sv-crypto`. Labelled accordingly. (`03` §3.3 notes;
   `09-discrepancies.md`.)
3. **`sv-core` → `sv-crypto` is a dev-dependency only (ARCH-04).** Drawn dashed; the production vault
   is generic over the ABI and FFI-free. (`03-system-architecture.md` §3.4.)
4. **38 IPC commands · 5 managed states.** Counts taken from the documents (`10-report-diagrams.md`
   `DIAG-02`/`DIAG-06`), not re-counted from source.
5. **Bundling configured, signing out of scope.** `bundle.active: true` / `targets: all`; H5
   signing/notarization is explicitly out of scope for internal use. (`01` §1.6; `06` §6.9.)

## Editing the diagrams

* **diagrams.net (web):** open <https://app.diagrams.net> → *File ▸ Open* → pick a `.drawio` file.
* **Draw.io desktop:** double-click the file (the `draw.io` app is registered for `.drawio`).
* **VS Code:** install the *Draw.io Integration* extension (`hediet.vscode-drawio`) and open the file
  in the editor — it edits the XML in place.

Shapes carry the shared palette (blue = presentation, amber = IPC, indigo = composition root, green =
domain crate, teal = shared platform, red = security-critical, purple = external tool, slate =
OS/filesystem). To restyle consistently, edit the `COL` palette / style helpers in
`generate-drawio.py` and regenerate, or edit shapes directly in the editor.

## Exporting for a report

From the editor: *File ▸ Export as ▸ PNG / SVG / PDF*. From the command line (drawio-desktop CLI):

```sh
# one file → PNG (transparent, 2× scale)
drawio -x -f png --scale 2 -o ARCH-01.png ARCH-01-overall-system-architecture.drawio

# one file → vector PDF for print
drawio -x -f pdf --crop -o ARCH-01.pdf ARCH-01-overall-system-architecture.drawio

# batch every diagram in this folder → SVG
drawio -x -f svg -o ./ *.drawio
```

## Regenerating

```sh
cd docs/12-drawio-architecture
python3 generate-drawio.py        # rewrites the five ARCH-*.drawio files
```

## Verification performed

* **Well-formedness:** all five pass `xmllint --noout`.
* **Native render:** each `.drawio` was exported to PNG with the `drawio` desktop CLI and inspected
  for overlaps, clipping, container nesting, swimlane labels, and edge routing. (Preview PNGs are not
  committed — the `.drawio` files are the deliverable.)

## Relationship to the other diagram packages

| Package | Notation | Role |
|---------|----------|------|
| [`../architecture/10-report-diagrams.md`](../architecture/10-report-diagrams.md) | Mermaid (23) | Canonical, exhaustive, diff-friendly reference |
| [`../architecture/10-report-diagrams.plantuml.md`](../architecture/10-report-diagrams.plantuml.md) | PlantUML (23) | Same 23, for LaTeX/PlantUML toolchains |
| [`../11-svg-architecture/`](../11-svg-architecture/) | SVG (5) | Hand-curated, print-styled, **read-only** vector figures |
| **`12-drawio-architecture/` (this)** | **Draw.io (5)** | The same five board-level figures as **editable** Draw.io source |

Use this package when you need to **edit** the board-level figures in a diagram tool; cite the SVGs for
a fixed print artifact and the Mermaid/PlantUML set for the exhaustive per-pipeline detail.
