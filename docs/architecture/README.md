# Secure Vault — Architecture & Design Documentation Package

**Status:** Authoritative as of 2026-06-17. **Primary source of truth: the source code** under
`secure-vault/` (this directory's grandparent). Every structural claim below is cited to a
`file:line` location that was read directly; nothing here is inferred from marketing or roadmap
intent. Where documentation and implementation disagree, see
[09-discrepancies.md](09-discrepancies.md).

> **Scope note.** This package documents the **Secure Vault product** (the Tauri + Rust desktop
> application and its Cargo workspace), which today ships **six toolkit modules** over a shared
> cryptographic platform. It does **not** document the surrounding *research evidence base* (the
> `detection/`, `encryption/`, … topic clones two levels up), which is evaluation material, not
> shipped code.

## How this package is organized

| # | Document | Covers |
|---|----------|--------|
| 1 | [01-system-overview.md](01-system-overview.md) | What the system is, its modules, the technology stack, deployment posture |
| 2 | [02-requirements-analysis.md](02-requirements-analysis.md) | Functional + non-functional requirements, actors, constraints, traceability |
| 3 | [03-system-architecture.md](03-system-architecture.md) | Layered architecture, crate dependency graph, trust boundaries, composition root |
| 4 | [04-module-design.md](04-module-design.md) | Per-crate and per-feature design: vault core, platform services, the four standalone modules |
| 5 | [05-data-design.md](05-data-design.md) | On-disk formats (`.svault`, `SVENC`, `SVKEY`, `SVSSS`/`SVSSP`, `SVSTEG`), DTOs, key hierarchy |
| 6 | [06-security-design.md](06-security-design.md) | Threat model, trust boundaries, oracle-safety, zeroization, subprocess hardening, assumptions |
| 7 | [07-uml-diagrams.md](07-uml-diagrams.md) | Use-case, component, sequence, deployment, and data-flow diagrams (Mermaid) |
| 8 | [08-testing-and-validation.md](08-testing-and-validation.md) | Test inventory, CI gates, validation findings |
| 9 | [09-discrepancies.md](09-discrepancies.md) | Documentation-vs-implementation divergences found during this pass |

## One-paragraph summary

Secure Vault is an **offline-first desktop security toolkit** built as a **Tauri 2** shell over a
**Rust Cargo workspace**. A thin, backend-free crypto **ABI** (`sv-crypto-traits`) is implemented by
vetted adapters (`sv-crypto`: BLAKE3, Argon2id, libsodium `secretbox`/Ed25519-minisign, Shamir `sss`;
`sv-age`: the `age` CLI driven as a hardened subprocess). Domain crates are **generic over the ABI**
and stay FFI-free: `sv-core` is the encrypted-container vault; `sv-platform` is a vault-free
file-level crypto-services layer; and `sv-stego`, `sv-meta`, `sv-qr`, `sv-watermark` are the four
standalone modules. A single **application/IPC command surface** (`sv-app`, in `src-tauri/`) composes
these behind an **oracle-safe, coded `ApiError`** contract in which **no secret ever crosses the IPC
boundary** (the one documented residual being the passphrase string). The `desktop/` crate is the
Tauri runtime + static `withGlobalTauri` frontend; it bundles and **BLAKE3-hash-pins** the external
binaries (`age`, `age-keygen`, `exiftool`).

## Reading conventions

- **Implemented / Planned / Research** labels follow the repository's status discipline
  (`CLAUDE.md`). This package documents **implemented** code; planned/research items are called out
  as such.
- Citations are `path:line` relative to `secure-vault/` (e.g.
  [crates/sv-core/src/format.rs](../../crates/sv-core/src/format.rs)).
- Diagrams are **Mermaid**; they render in GitHub and most Markdown viewers.
