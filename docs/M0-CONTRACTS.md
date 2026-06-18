# Secure Vault — M0 / M0.1 Contracts (Foundations)

**Status:** M0 + M0.1 complete, and **the full roadmap (M1–M7) is now implemented.** This document
remains the authoritative description of the *foundational* crate boundaries, DTOs, crypto traits,
`.svault` schema, IPC surface, verification gates, and the assumptions that could force a future
change — i.e. the frozen contracts the rest of the build targets. **The adapters are now real**
(BLAKE3, Argon2id, libsodium secretbox/Ed25519-minisign, Shamir, age — no `todo!()` stubs remain).
For the current end-to-end picture, see [`docs/architecture/`](architecture/README.md).

> **Freeze status (post-M0.1):**
> - **Crypto-trait layer (`sv-crypto-traits`) — FROZEN.** The M0.1 review fixes (C1, C2,
>   C3, C5, B1, B3) are applied; these contracts are now stable for M1+.
> - **`.svault` schema (§4) & key-hierarchy (§5) — RESOLVED & FROZEN** by the pre-M5
>   decision review ([`M5-SCHEMA-DECISIONS.md`](M5-SCHEMA-DECISIONS.md): H1–H6, V1, K1–K2).
>   M4/M5 implement against that document; §4–§5 below describe the *M0.1* shape and are
>   superseded where the decision record changes them (notably: header `suite` block,
>   single-stream payload with encrypted item directory, per-field vault-bound wrap keys,
>   binding-root signature).
> - **IPC error/passphrase contracts (§2, §6) — RESOLVED & FROZEN** by the pre-M6 decision
>   review ([`M6-IPC-DECISIONS.md`](M6-IPC-DECISIONS.md): E1–E3, N1). M6 implements against that
>   document; §2/§6 below describe the M0 shape and are superseded where the decision record
>   changes them (expanded error taxonomy + stable codes, `IncompatibleVersion`/`Malformed`/
>   `InsufficientShares`, `IpcPassphrase` boundary newtype, session/secret-lifetime rules).

> Scope reminder: this document specifies the **M0/M0.1 foundations**. The later milestones —
> M1 (BLAKE3+Argon2id), M2 (FFI), M3 (age), M4 (key hierarchy), M5 (container), M6
> (session/commands), M7 (hardening) — have **all since been implemented** against these contracts.

---

## 1. Crate boundaries (the dependency DAG)

```
sv-crypto-traits ◀───────────┬───────────┬─────────────┐   (stable ABI: traits + types, B1)
   ▲ (re-export)             │           │             │
sv-crypto (impls)        sv-age      sv-sys-sss     sv-core ◀── sv-types
   (real adapters)       (age)       (Shamir FFI)      ▲           ▲ (leaf: DTOs, no secrets)
                                                        │
                                          src-tauri (sv-app) ◀── sv-core, sv-types
                                          (IPC surface; no `tauri` dep yet)
```

| Crate | Responsibility | Depends on | May hold secrets? |
|---|---|---|---|
| `sv-types` | Public IPC/UI DTOs | serde | **No (enforced invariant)** |
| `sv-crypto-traits` | **Stable ABI**: crypto traits + value types + algorithm ids | serde, zeroize, thiserror | Yes (zeroizing types) |
| `sv-crypto` | Concrete adapters (BLAKE3, Argon2id, minisign, Shamir); re-exports `sv-crypto-traits` | sv-crypto-traits, sv-sys-* | Yes (zeroizing types) |
| `sv-core` | `.svault` schema, key hierarchy, service API, errors | sv-types, sv-crypto-traits, ciborium | Yes (in-memory only) |
| `sv-age` | `FileCipher` over the bundled, hash-pinned `age` subprocess | sv-crypto-traits | Yes (identity, transient) |
| `sv-sys-sss` | Shamir (`sss` hazmat) FFI; re-exports `KEYSHARE_LEN` | sv-crypto-traits | n/a (FFI) |
| `sv-sys-sodium` | libsodium FFI (secretbox, Ed25519, BLAKE2b) | — | n/a (FFI) |
| `src-tauri` (`sv-app`) | IPC command surface (contract) | sv-core, sv-types | No (wraps→zeroizes passphrase) |

**Why this shape (B1):** the trait/type **contracts** live in the tiny, backend-free
`sv-crypto-traits`, which `sv-core`/`sv-age`/`sv-sys-*` and future plugins compile against;
`sv-crypto` carries the heavy backends (blake3/argon2/FFI from M1) and re-exports the traits
so `use sv_crypto::…` keeps working. Secrets are confined to the crypto/core/age crates; the
UI-facing crates (`sv-types`, `sv-app`) never hold key material.

---

## 2. IPC DTOs (`sv-types`) — frozen, no secrets

`CONTRACT_VERSION = 1`. Types: `VaultMeta`, `SharePolicy`, `KdfDescriptor`, `ItemInfo`,
`SessionHandle`, `IntegrityReport`, `ShareExportInfo`, `AppInfo`, `ApiError`.

- **Invariant:** no passphrase, key, share-secret, or identity ever appears in this crate.
  Salts/public-keys/hashes/KDF *params* are non-secret and allowed.
- `SessionHandle` is an opaque id; the master key never crosses the boundary.
- `ApiError` (M6, E1/E2/E3): **oracle-safe** + **stably coded** (`#[serde(tag="code")]`,
  `SV-…`). `Unauthorized` merges wrong-passphrase with wrong-share; but `Malformed`
  ("not a vault"), `IncompatibleVersion{found,supported}`, `InsufficientShares{got,need}`
  are now distinct, non-secret, actionable variants. `AppInfo` is the version handshake (E1).
- Gate: every DTO round-trips through JSON (`sv-types` test) and the header through CBOR
  (`sv-core` test).

---

## 3. Crypto contracts (`sv-crypto-traits`) — **FROZEN (post-M0.1)**

Constants: `HASH_LEN=KEY_LEN=32`, `SALT_LEN=16`, `KEYSHARE_LEN=33` (**single source**, B3;
`sv-sys-sss` re-exports it).

**Algorithm ids (C3 — building blocks of the M5 header suite):** `KdfAlg::Argon2id`,
`HashAlg::Blake3`, `AeadAlg::XSalsa20Poly1305`, `FileCipherAlg::AgeV1`, `SigAlg::Ed25519Minisign`.

**Value types** — *non-secret* (serde): `Hash32`, `Salt`, `MinisignSignature`,
`Ed25519PublicKey`, `AgeRecipient`, the `…Alg` enums, and **`KdfParams`** (now an `enum
{ Argon2id(Argon2idParams) }`, C3 — extensible to a second KDF without a breaking change).
*Secret* (zeroizing, redacted `Debug`, **never** serde): **`Key32`** (C1/C5 — fixed 32-byte
key, no heap), **`KeyShare`** (C5 — fixed 33-byte array), `SecretBytes` (C5 — `Box<[u8]>`,
growth-proof), `AgeIdentity`.

**Traits → adapters (stubbed at M0, now all implemented; each adapter reports its `alg()`):**

| Trait | Methods | Adapter | Backend / Milestone |
|---|---|---|---|
| `Hasher` | `alg`, `hash`, `keyed_hash`, `streaming` | `Blake3Hasher` | `blake3` crate / M1 |
| `KeyDerivation` (C2, split out) | `derive_key → Key32` | `Blake3Hasher` | `blake3` crate / M1 |
| `Kdf` | `alg`, `derive → Key32` (C1) | `Argon2Kdf` | `argon2` crate / M1 |
| `Signer` | `alg`, `generate`, `sign`, `verify` | `SodiumMinisignSigner` | libsodium FFI, minisign format / M2 |
| `SecretSharer` | `split(&Key32,…)`, `combine → Key32` (C1) | `SssSharer` | libsss hazmat FFI / M2 |
| `FileCipher` | `alg`, `encrypt`, `decrypt` | `sv_age::AgeCipher` | bundled `age` subprocess / M3 |

`CryptoError`: `InvalidParameter`, `VerificationFailed`, `Backend`, `NotImplemented`.

**M0.1 changes applied here:** C1 (key outputs are zeroizing `Key32`), C2 (`KeyDerivation`
split from `Hasher`), C3 (`…Alg` ids + `KdfParams` enum + per-adapter `alg()`), C5
(growth-proof secret types), B1 (this crate exists), B3 (one `KEYSHARE_LEN`).

---

## 4. `.svault` container schema + framing (`sv-core::format` + `sv-core::container`) — **IMPLEMENTED (M5)**

`MAGIC = b"SVLT"`, `FORMAT_VERSION = 1`. H1–H6/V1 resolved per
[`M5-SCHEMA-DECISIONS.md`](M5-SCHEMA-DECISIONS.md) and implemented in M5.

**File layout:** `MAGIC(4) ‖ FORMAT_VERSION(u16 LE) ‖ HEADER_LEN(u32 LE) ‖ HEADER(CBOR) ‖
PAYLOAD ‖ SIG_TRAILER(minisign)`.
- **Binding-root signature (H5):** SIG_TRAILER = minisign Ed25519 over
  `BLAKE3(BLAKE3(MAGIC‖VERSION‖HEADER_LEN‖HEADER) ‖ BLAKE3(PAYLOAD))`. Section digests are
  recomputed on read (not stored) → integrity (#4) + provenance (#5) + splice resistance.
- **Integrity vs. provenance (schema decision H4):** `decode(.., None)` = self-signed integrity check;
  `decode(.., Some(pinned))` = provenance (in-header key must equal the pinned key). Reported
  distinctly; a self-signed vault is never labelled authentic-origin.
- **Single-stream payload (H3):** PAYLOAD is *one* age ciphertext whose plaintext is
  `DIR_LEN ‖ CBOR(ItemDirectory) ‖ item-bytes` (`container::pack_archive`). The item directory
  is therefore **encrypted** — a locked vault leaks no item names/sizes/count.
- **Verify-then-parse:** `container::verify_header` is a panic-free structural parse (read KDF
  params pre-unlock); `decode` authenticates. Header size capped (`MAX_HEADER_LEN = 1 MiB`).

**Header (`VaultHeader`, CBOR, `deny_unknown_fields`):** `format_version`, `suite`
(`CipherSuite::V1`, H1), `vault_uuid[16]`, timestamps, `kdf{salt, params}` (H6 — free-form
`algorithm` string dropped), `wrapped_age_identity`, `age_recipient` (non-secret `age1…`,
added in M6 so the single-stream payload can be re-encrypted on item changes),
`wrapped_signing_key`, `signing_public_key[32]`, `share_policy?`,
`content_layout{payload_len}` (H3 — **no `items`**).
Secrets stored **wrapped** (secretbox) only. `ItemEntry` (now inside the encrypted directory)
records `plaintext_blake3[32]` + plaintext `offset/len`. Three version axes (V1): `FORMAT_VERSION`
(structure) ⟂ `CipherSuite` (crypto) ⟂ `CONTRACT_VERSION` (IPC). Container framing/sign/verify is
**generic over injected `Hasher`+`Signer`**, keeping `sv-core` production deps backend-/FFI-free.

---

## 5. Key-hierarchy contract (`sv-core::keys`) — **IMPLEMENTED (M4)**, frozen per K1/K2

`passphrase ─Argon2id(salt,params)→ MK ─BLAKE3 derive_key(per-field, vault-bound)→ wrap key`.
All keys are zeroizing `Key32` (C1). The old `CTX_KEK`/`CTX_SWK` + `derive_kek`/`derive_swk`
two-step is **superseded** by per-field, uuid-bound wrap keys (H2/K1/K2 freeze):

- `SUITE_VERSION: u8 = 1` — crypto-suite version; single source of the context version token
  (distinct from `FORMAT_VERSION` and `CONTRACT_VERSION`).
- Context grammar (K1): `secure-vault/v1/wrap/<field>:<uuid_hex>`, `<field>` ∈
  {`age-identity`, `signing-key`}; `secure-vault/v1/plugin/<id>/<purpose>` reserved.
  Frozen by a CI test (K2); changing a template bricks existing vaults.
- `KeyHierarchy` trait: `derive_master(passphrase, salt, params) → Key32` and
  `derive_wrap_key(&Key32, WrapField, &[u8;16]) → Key32`. Implemented by the generic
  `StdKeyHierarchy<K: Kdf, D: KeyDerivation>` (concrete `Argon2Kdf`/`Blake3Hasher` injected by
  the service layer, so `sv-core`'s **production** deps stay backend-/FFI-free; tests use a
  dev-dependency on `sv-crypto`).

MK never touches disk; each wrap key wraps exactly one stored secret. The uuid+field binding
makes a wrapped blob non-transplantable between vaults and non-confusable between fields
(verified: a wrong-vault or wrong-field key fails the secretbox MAC). Passphrase change
re-derives MK and re-wraps only.

---

## 6. Service + IPC surface — **IMPLEMENTED (M6)** (E1–E3, N1 applied)

`sv-core::service::VaultService` (internal; passphrases as `SecretBytes`) is implemented by
`sv-app::VaultBackend<P: PayloadCipher>` — the composition root that wires `StdKeyHierarchy`
(M4) + `secretbox` wrap/unwrap (M2) + the `.svault` container (M5) + `SodiumMinisignSigner` +
`SssSharer` (M2) + an injected age `PayloadCipher` (M3). `sv-app::AppVault` wraps it 1:1 as
`CommandSurface` (the Tauri boundary), converting `IpcPassphrase`→`SecretBytes` (N1) and
projecting `VaultError`→`ApiError` (E1–E3). All 14 commands implemented + an `app_info()`
handshake. **Sessions:** opaque random `session_id` → table holding **only the zeroizing MK**
+ path; explicit `lock` zeroizes; the age identity / signing key are materialized transiently
per op. **Unlock hardening:** verify-then-parse (signature before credential), KDF-param
ceiling before Argon2. The literal `#[tauri::command]`/`tauri.conf.json` runtime shell now exists
in the workspace-excluded `desktop/` crate; the backend is complete and tested (a `StubPayloadCipher`
exercises the full lifecycle in unit tests, plus an `age`-gated e2e).

---

## 7. Verification gates (M0 acceptance) — all green locally

| Gate | Command | Result |
|---|---|---|
| Format | `cargo fmt --all --check` | ✅ |
| Lint | `cargo clippy --workspace --all-targets -- -D warnings` | ✅ no warnings |
| Build | `cargo build --workspace --locked` | ✅ |
| Tests | `cargo test --workspace` | ✅ 14 passed *(M0 acceptance snapshot; the suite is now **253** — 249 passing + 4 env-gated e2e — see [architecture/08](architecture/08-testing-and-validation.md))* |
| Supply chain | `cargo deny check` + `cargo audit` | ✅ deny ok locally; both in CI |
| SBOM stub | `scripts/sbom.sh` | ✅ emits dependency manifest |

CI matrix: ubuntu/macos/windows. Toolchain pinned (`rust-toolchain.toml`). `Cargo.lock`
committed for reproducibility. `RUSTFLAGS="-D warnings"`. Dependency versions are
single-sourced in `[workspace.dependencies]`. `sv-crypto-traits` confirmed backend-free
(`cargo tree`: only serde/zeroize/thiserror).

**Tests proving the contracts (14):** DTO JSON round-trip; CBOR header round-trip (with
`KdfParams` enum); magic/version frozen; KDF defaults ≥ OWASP floor + alg tag; `Key32` /
`KeyShare` / `SecretBytes` redaction + fixed-length / growth-proof; non-secret + alg-id
serializability; adapters report `alg()`; trait re-export resolves; oracle-safe error
projection; derivation-context distinctness/stability; app↔IPC version sync.

---

## 8. Assumptions that could force future contract changes

These are decisions taken to let M0 proceed; each maps to an open question from the
roadmap and the contract it would churn if revisited. **Recorded here so a later change is
a conscious, reviewed event.**

> **Update (post-implementation):** these assumptions have **all since been resolved** at the
> milestones shown — the schema decisions (A1–A3, A5, A8, A10) in
> [`M5-SCHEMA-DECISIONS.md`](M5-SCHEMA-DECISIONS.md), the IPC ones (A6, A7, A9) in
> [`M6-IPC-DECISIONS.md`](M6-IPC-DECISIONS.md), and the Argon2 default (A4) carried with a recalibration
> note into M7. The table is retained as the record of *why* each shape was chosen. (M0.1 itself only
> froze the crypto-trait layer; the schema/IPC were decided in their own pre-M5/M6 reviews.)

| # | Assumption (M0 default) | Risk if wrong | Contract(s) affected | Decide by |
|---|---|---|---|---|
| A1 | Vault is a **multi-item** container (`items: Vec<ItemEntry>`, per-item offsets) | Single-blob model would simplify the header | `VaultHeader`, `ContentLayout`, `ItemEntry`, `VaultService` item methods | M5 |
| A2 | Whole-container **re-hash + re-sign on every save** | Per-item signing would change trailer semantics | file layout, `sign`/integrity flow | M5 |
| A3 | Container signature is **always-on provenance** (mandatory per save) | If signing is user-opt-in, trailer becomes optional | file layout, `IntegrityReport` | M5 |
| A4 | KDF default **256 MiB / t=3 / p=1** | Too slow on low-end HW / too weak | `KdfParams::default`, `KdfRecord` (params already stored, so additive) | M1, recalibrate M7 |
| A5 | Secrets are stored **secretbox-wrapped** with libsodium (`WrappedSecret{nonce,ciphertext}`) | A different AEAD (e.g. XChaCha) changes nonce length | `WrappedSecret`, `sv-sys-sodium` consts | M2 |
| A6 | `ApiError` collapses auth vs. corruption into coarse variants (oracle-safe) | A product spec wanting granular errors reopens the enum | `sv_types::ApiError`, `VaultError`→`ApiError` | M6 |
| A7 | Share secret bytes are **never** returned via DTO; only `ShareExportInfo` metadata | If shares must transit IPC, a (sealed) secret DTO is needed | `ShareExportInfo`, `keys_split` | M6 |
| A8 | `KEYSHARE_LEN = 33` (libsss hazmat 32-byte key shares) | Using full-secret `sss_create_shares` (64B) instead would change share size | `KeyShare`, `SssSharer`, share-envelope format | M2 |
| A9 | `src-tauri` carries **no `tauri` dep** in M0; `CommandSurface` is a plain trait | Tauri's command macro constraints (arg types, async) may force signature tweaks | `sv-app::CommandSurface` | M6 |
| A10 | CBOR (`ciborium`) is the header encoding | A different codec changes nothing structurally but breaks existing files | `VaultHeader` on-disk bytes | M5 |
| A11 | Repo root for CI = `secure-vault/` (so `.github` is here) | Wrong root breaks Actions paths | `.github/workflows/ci.yml` | **done** — repo on GitHub, CI green ([CI-VALIDATION.md](CI-VALIDATION.md)) |

**Versioning safety net:** `FORMAT_VERSION` (on-disk) and `CONTRACT_VERSION` (IPC) exist
specifically so that A1–A10, if revisited after release, become version bumps with
migration rather than silent breakage.

---

## 9. Deferred at M0 — now done (status as of 2026-06-17)
These were explicitly out of scope for M0 and have **since been delivered** across M1–M7: crypto
logic (all adapters implemented — BLAKE3/Argon2id/secretbox/Ed25519-minisign/Shamir/age); FFI/`unsafe`
(the `sv-sys-*` crates wrap libsodium and the `sss` hazmat); the bundled, hash-pinned `age`
subprocess; the Tauri runtime/`tauri.conf.json` wiring (in the workspace-excluded `desktop/` crate);
and `git init` + first commit (the repo is on GitHub, CI green — see
[CI-VALIDATION.md](CI-VALIDATION.md)). **Still a stub:** the SBOM (`scripts/sbom.sh` emits a
dependency-manifest stub, not full CycloneDX).
