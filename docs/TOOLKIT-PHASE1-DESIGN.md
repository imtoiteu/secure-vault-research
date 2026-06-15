# Toolkit Phase 1 — Integrity + Cryptography modules: Implementation Design & Architecture Review

Status: **design only. No code.** Grounded in source inspection of the `secure-vault/` workspace
(verified against `sv-crypto-traits`, `sv-crypto`, `sv-age`, `sv-app/{lib,service,payload,passphrase}`,
`sv-types`, `sv-core/error`). Source of truth: [../docs/PLATFORM-AUDIT.md](../../docs/PLATFORM-AUDIT.md).

Scope of this phase (the user's order):
1. **Integrity** — Hash File, Verify Signature
2. **Cryptography** — Encrypt File, Decrypt File, Sign File (+ the keypair generation Sign File requires)

Hard constraints (from the request): reuse existing primitives; **keep Secure Vault unchanged**;
prefer additive architecture; keep existing security guarantees; keep API contracts additive;
maintain all current tests and gates.

---

## 0. The decision that shapes everything — **CONFIRMED**

> **Decisions locked (user-confirmed):**
> 1. **Encrypt/Decrypt File = Option A, passphrase mode (Argon2id + secretbox).** age recipient mode
>    is a deferred additive follow-up.
> 2. **Sign File = generate + passphrase-wrap.** Add `crypto_generate_signing_keypair`; the signing
>    secret key is stored encrypted at rest (`.svkey`) with the same Argon2id+secretbox mechanism.
>
> The rest of this document already specifies exactly this path. Implementation is unblocked.

**How does *Encrypt File / Decrypt File* protect the file?** There are two coherent, primitive-reusing
options, and they produce different builds:

| | **A — Passphrase mode** (recommended) | **B — age recipient mode** |
| --- | --- | --- |
| Mechanism | Argon2id (P4) → derive key → secretbox AEAD (P5) | age X25519 + ChaCha20-Poly1305 (P8) |
| Reuses | `Argon2Kdf` + `policy` + `secretbox` + `derive_key` (all gate-passing) | `AgeCipher` + bundled-binary pin harness |
| Key management | **none** — password in, password out | **required** — generate/store/import identities + recipients (audit **R6**, the biggest scope trap) |
| Headless? | yes | yes for recipients; **age `-p` passphrase mode cannot run without a TTY** — so "password" UX is impossible via the age subprocess |
| New on-disk format | yes — a small `.svenc` artifact | no — age's self-describing format |
| New dependency in the new crate | none (pure `sv-crypto`) | `sv-age` + injected pinned binary wiring |
| Product-identity cost | introduces a **second** file cipher (XSalsa20-Poly1305) alongside age | stays age-only |

**Recommendation: A (passphrase mode).** It is the "encrypt a file with a password" feature most
users expect, it carries **zero** key-management surface (R6), it reuses only already-hardened
in-tree primitives, and it keeps the new crate pure-Rust (no subprocess injection). Its one real cost
is a new, small, versioned on-disk format and a second AEAD in the product — a deliberate, contained
trade-off. age recipient mode is a clean **additive follow-up** (it reuses the same command surface).

The rest of this document specifies **Option A**. If the product must stay age-only, we switch
Encrypt/Decrypt to Option B and add a key-management sub-design (larger). **This is the one open
question to confirm before implementation.**

---

## 1. Architecture: a new `sv-platform` crate + a separate command segment

The audit (§5) and roadmap (Phase 1) call for a thin **platform crypto-services layer**, vault-free,
that Secure Vault later consumes. Phase 1 stands it up — used *only* by the new modules for now, so
the vault is untouched.

```
            sv-crypto-traits (ABI, unchanged)
                     ▲
            sv-crypto (impls, unchanged)         sv-types (DTOs; +1 additive struct)
                     ▲     ▲                              ▲
                     │     └──────────────┐               │
              sv-core (vault, UNCHANGED)  │   sv-platform (IMPLEMENTED, 38 tests)
                     ▲                    └── depends: sv-crypto-traits, sv-crypto, sv-types
                     │                                  (+ getrandom, zeroize)
            sv-app  ─┴── adds: PlatformSurface trait + PlatformApp (holds PlatformCrypto)
                     │            reuses IpcPassphrase (P11); maps PlatformError → ApiError
                     ▼
            desktop ─ registers a SECOND managed state + thin #[tauri::command] wrappers
```

### Why a separate segment, not edits to `CommandSurface`
`CommandSurface`/`AppVault`/`VaultBackend` are **not touched**. The new operations need no vault and
no session, so they live on their own `PlatformSurface` trait, implemented by a new `PlatformApp`
struct, exposed as a **second Tauri managed state**. This satisfies "keep Secure Vault unchanged"
*literally* — the 16 existing commands and every existing test stay byte-identical — while the toolkit
grows purely additively. (Mirrors how `sv-core`'s `VaultError`→`ApiError` projection lives in the
domain crate: `sv-platform` owns `PlatformError`→`ApiError` the same way, so there is no orphan-rule
problem and no change to `sv-types`' existing code.)

### Why `sv-platform` is thin (audit R7)
No "engine" trait. `PlatformCrypto` is a small struct holding the three unit-struct adapters
(`Blake3Hasher`, `Argon2Kdf`, `SodiumMinisignSigner`) and exposing free-standing methods. Because
Option A uses no subprocess, `PlatformCrypto::new()` takes **no arguments** and needs no binary
resolution — markedly simpler than the vault backend.

---

## 2. Per-capability design

All paths are non-secret `String`s at the IPC edge; all passphrases are `IpcPassphrase` (P11,
zeroizing, redacted). All keys flow as `Key32`/`SecretBytes` (zeroizing). No secret ever enters a DTO.

### 2.1 Hash File  (Integrity)
- **Reuses:** `Hasher`/`StreamingHasher` — BLAKE3 (P2).
- **Improvement over the vault's `hash_file`:** stream the file through `Blake3Streaming` in fixed
  chunks instead of `std::fs::read` (whole file into RAM). This sidesteps audit **R5** for hashing —
  no size cap needed, no OOM on large files. (The vault's own `hash_file` is left unchanged.)
- **Core method:** `PlatformCrypto::hash_file(path) -> Result<String, PlatformError>` (lowercase hex).
- **Command:** `integrity_hash_file(path: String) -> Result<String, ApiError>`.
- **Errors:** `Io` (read), `Internal`. No auth, no oracle.

### 2.2 Verify Signature  (Integrity)
- **Reuses:** `Signer::verify` — minisign/Ed25519 (P6), and the existing `parse_pubkey_hex` shape
  (64-char hex Ed25519 public key in a file), matching today's `verify_file`.
- **Core method:** `verify_signature(file, sig_path, pubkey_path) -> Result<bool, PlatformError>`.
- **Command:** `integrity_verify_signature(path, signature_path, public_key_path) -> IntegrityReport`.
  Reuses the existing `IntegrityReport` DTO (`signature_ok` = result; `blake3_ok` mirrors it;
  `computed_hash_hex` = BLAKE3 of the file, informative) — **zero new DTOs**, identical shape to
  `verify_file`.
- **Errors:** `InvalidInput` (pubkey/sig not parseable), `Io`, `Internal`. A *failed* verification is
  **`Ok(report{ signature_ok:false })`**, not an error — same contract as `verify_file`.

### 2.3 Encrypt File  (Cryptography) — Option A
- **Reuses:** `Argon2Kdf` (P4) + `policy::recommended()` + `KeyDerivation::derive_key` (P3) +
  `secretbox::seal` (P5). All in `sv-crypto`, all gate-passing.
- **Flow:**
  1. Refuse if output exists (`OutputExists`); enforce in-memory size cap (`MAX_PLAINTEXT_BYTES`,
     mirror of the vault's `MAX_ITEM_BYTES = 2 GiB` — secretbox is one-shot/in-memory, audit R5).
  2. `salt = random[16]`; `params = policy::recommended()` (256 MiB / t=3 / p=1).
  3. `mk = Argon2Kdf.derive(passphrase, salt, params)` → `Key32`.
  4. `fek = derive_key("secure-vault/platform/v1/file-encrypt", mk.expose_secret())` → `Key32`
     (domain separation + future agility, mirrors the vault's wrap-key derivation).
  5. `wrapped = secretbox::seal(fek.expose_secret(), plaintext)` → `{nonce[24], ciphertext}`.
  6. Write the `.svenc` artifact (below) via an atomic same-dir temp + rename (reuse the **pattern**
     of `write_atomic`, P13; `sv-platform` reimplements a tiny local helper rather than depend on
     `sv-core`).
- **Core method:** `encrypt_file(in, out, passphrase) -> Result<(), PlatformError>`.
- **Command:** `crypto_encrypt_file(input, output, passphrase: IpcPassphrase) -> String` (output path).

#### `.svenc` artifact (v1) — fixed binary layout, self-describing, versioned
```
offset  bytes  field
0       6      MAGIC            = b"SVENC\x00"
6       2      format_version   = u16 LE (1)
8       1      kdf_alg          = u8 (0 = Argon2id)
9       4      argon2 mem_kib   = u32 LE
13      4      argon2 time_cost = u32 LE
17      4      argon2 parallel  = u32 LE
21      16     salt
37      1      aead_alg         = u8 (0 = XSalsa20-Poly1305 secretbox)
38      24     nonce
62      ..     ciphertext (secretbox output; includes the 16-byte Poly1305 tag)
```
Non-secret header (algorithm ids + params + salt + nonce are not secret — same stance as the vault
header). The ciphertext is authenticated; any header/byte tamper fails `secretbox::open`.

### 2.4 Decrypt File  (Cryptography) — Option A
- **Reuses:** same primitives in reverse.
- **Flow:** refuse if output exists; read+size-cap the `.svenc`; validate MAGIC/version
  (`Malformed`/`IncompatibleVersion`); **validate KDF params against the same DoS ceilings the vault
  uses** (`MAX_KDF_MEM_KIB` etc. — the header is attacker-influenceable before any auth, audit lesson
  H-series); derive `mk`→`fek`; `secretbox::open` → plaintext; atomic write.
- **Oracle safety:** `secretbox::open` fails **identically** for a wrong passphrase or a tampered
  file. Both map to **one merged code** → `ApiError::Unauthorized` (`SV-UNAUTHORIZED`). No oracle.
- **Core method:** `decrypt_file(in, out, passphrase) -> Result<(), PlatformError>`.
- **Command:** `crypto_decrypt_file(input, output, passphrase: IpcPassphrase) -> String`.

### 2.5 Sign File  (Cryptography)
Signing needs a signing key that is **not** a vault. The minimal coherent set is *generate → sign*,
with the secret key wrapped at rest under a passphrase using the **same** Argon2id+secretbox machinery
as 2.3 (one mechanism, reused).

- **`crypto_generate_signing_keypair(out_dir, name, passphrase) -> SigningKeypairInfo`**
  - `Signer::generate()` → `(SecretBytes sk, Ed25519PublicKey pk)` (P6).
  - Write `name.pub` = 64-char hex of `pk` (non-secret; the exact form `verify_signature` parses).
  - Write `name.svkey` = the secret key sealed with the §2.3 passphrase mechanism, MAGIC `b"SVKEY\x00"`,
    same header layout, payload = `sk` bytes. Refuse overwrite on both files.
  - Returns the **one new DTO**: `SigningKeypairInfo { public_key_path, secret_key_path,
    public_key_hex }` — paths + **public** key only (no secret in the DTO).
- **`crypto_sign_file(input, signing_key_path, passphrase) -> String`** (the `.minisig` path)
  - Read `.svkey`; derive key from passphrase; `secretbox::open` → `sk` (wrong passphrase → merged
    `Unauthorized`); `Signer::sign(data, sk, trusted_comment)` (reuse the `"secure-vault signed <t>"`
    comment shape); write `input.minisig` (refuse overwrite, mirror existing `sign_file`).
- **Verify** is already covered by 2.2 (`integrity_verify_signature`) — generate→sign→verify is a
  closed loop with no vault.

---

## 3. Command surface (additive) and contract impact

New `PlatformSurface` methods (names chosen to **not collide** with the vault's `integrity_hash` /
`integrity_check` / `verify_file` / `sign_file`):

| Command | In | Out | Module |
| --- | --- | --- | --- |
| `integrity_hash_file` | `path` | `String` (hex) | Integrity |
| `integrity_verify_signature` | `path, signature_path, public_key_path` | `IntegrityReport` (reused) | Integrity |
| `crypto_encrypt_file` | `input, output, passphrase` | `String` (out path) | Cryptography |
| `crypto_decrypt_file` | `input, output, passphrase` | `String` (out path) | Cryptography |
| `crypto_generate_signing_keypair` | `out_dir, name, passphrase` | `SigningKeypairInfo` (new) | Cryptography |
| `crypto_sign_file` | `input, signing_key_path, passphrase` | `String` (sig path) | Cryptography |

**Contract additions (all additive):**
- `sv-types`: **one** new DTO `SigningKeypairInfo` (public fields only). No change to any existing DTO.
- `ApiError`: **no new variants** — every path reuses existing oracle-safe codes (`Io`, `TooLarge`,
  `InvalidInput`, `OutputExists`, `Unauthorized`, `Malformed`, `IncompatibleVersion`, `Timeout`,
  `Internal`).
- `CONTRACT_VERSION`: **stays 1.** Per the documented rule ("additive optional fields keep the same
  major; new DTOs/commands are additive"), nothing existing breaks. The handshake test
  `app_tracks_ipc_contract_version` is unaffected.

`PlatformError` (new, in `sv-platform`) is a small internal taxonomy projected to `ApiError`,
mirroring `VaultError`: `{ Io(String), TooLarge{limit,actual}, InvalidInput(String), OutputExists,
AuthFailed, Malformed, IncompatibleVersion{found,supported}, Internal }`. The `From<PlatformError>
for ApiError` impl lives in `sv-platform` (it depends on `sv-types`, exactly as `sv-core` does),
preserving the oracle-safe merge (`AuthFailed → Unauthorized`).

---

## 4. Security review (guarantees preserved + one added surface)

- **Zeroization** end-to-end: `IpcPassphrase` → `SecretBytes`; derived keys are `Key32`
  (zeroize-on-drop); signing secret key is `SecretBytes`; plaintext buffers zeroized after use
  (follow the `sv-age`/service pattern).
- **No secret in DTOs:** `SigningKeypairInfo` carries paths + the **public** key only. The secret key
  is encrypted at rest in `.svkey`.
- **Oracle safety:** decrypt / unwrap failures are indistinguishable (wrong passphrase vs tamper) and
  collapse to a single `SV-UNAUTHORIZED`. Verification *outcomes* are returned as data
  (`signature_ok: false`), never as a distinguishing error.
- **Pre-auth DoS guard:** `.svenc`/`.svkey` headers are validated against the same Argon2 ceilings the
  vault enforces (`validate_kdf`) **before** running the KDF — a hostile artifact can't request
  unbounded work.
- **Data safety:** refuse to overwrite any existing output (`OutputExists`), atomic same-dir temp +
  rename for every written file (reused `write_atomic` pattern, P13).
- **Memory bound:** encrypt/decrypt keep the 2 GiB in-memory cap (`TooLarge`) — secretbox is one-shot
  (audit R5). Hashing streams and is uncapped.
- **KDF strength:** `policy::recommended()` (OWASP-floor Argon2id) at encrypt time; params stored so
  decrypt reproduces them.
- **New surface (honest):** Option A introduces a second AEAD (XSalsa20-Poly1305) and two small
  on-disk formats (`.svenc`, `.svkey`). Both are versioned, fixed-layout, authenticated, and minimal.
  This is the deliberate cost of headless passphrase encryption (see §0).

---

## 5. Test plan (TDD; new tests only — existing suite is untouched)

`sv-platform` unit tests:
- Hash: matches `Blake3Hasher.hash`; streaming == one-shot for multi-chunk inputs; large input hashes
  without the size cap.
- Verify: generate→sign→verify `valid`; tamper file → `!valid`; bad pubkey/sig → `InvalidInput`.
- Encrypt/Decrypt: round-trip; **wrong passphrase → AuthFailed**; **tampered ciphertext/header →
  AuthFailed** (no distinguishability); `OutputExists` refusal; oversized input → `TooLarge`;
  bad MAGIC → `Malformed`; bumped version → `IncompatibleVersion`; pre-auth Argon2-ceiling rejection.
- Keypair + sign: generate → `.pub`/`.svkey` written, overwrite refused; sign with right passphrase →
  verifies; sign with wrong passphrase → `AuthFailed`; `.svkey` payload is ciphertext (no plaintext key).

`sv-app` tests:
- `PlatformError → ApiError` projection: every variant maps to the expected code; `AuthFailed`
  collapses to `SV-UNAUTHORIZED` (oracle-safe).
- `PlatformSurface` methods convert `IpcPassphrase`/`String` correctly and never log secrets.

**Gates (must stay green):** `cargo fmt --all --check`; `cargo clippy --workspace --all-targets -D
warnings`; `cargo build --workspace --locked` (new workspace member + regenerated `Cargo.lock`);
`cargo test --workspace`; `cargo deny check` (no new third-party deps beyond what `sv-crypto` already
pulls; `sv-platform` adds only internal crates + `getrandom`/`zeroize`, already in the graph). The
Tauri shell stays workspace-excluded; desktop changes are thin wrappers + a second `manage()` + the
`generate_handler!` additions.

---

## 6. Risk register (mapped to PLATFORM-AUDIT)

| Audit risk | How this design handles it |
| --- | --- |
| **R4** — don't inherit `AgePayloadCipher`'s single-stream/identity-per-call coupling | `sv-platform` consumes `sv-crypto` primitives **directly**; never touches `payload.rs`. |
| **R5** — in-memory buffering propagates | Hashing **streams** (uncapped); encrypt/decrypt keep the explicit 2 GiB `TooLarge` cap. |
| **R6** — standalone key management is the real new surface | Option A removes it from Encrypt/Decrypt entirely (passphrase). Sign File's key-at-rest reuses the **same** Argon2+secretbox wrap — one minimal mechanism, two small versioned formats. |
| **R7** — over-abstraction | `PlatformCrypto` = thin struct + free methods; no engine trait, no framework. |
| **R9** — keep the ABI a leaf / gates green | `sv-crypto-traits` untouched; `sv-platform` adds no heavy deps; new crate joins the audited workspace. |
| **R10** — contract drift | Additive only: +1 DTO, 0 new error codes, `CONTRACT_VERSION` unchanged, no-secret-in-DTO preserved. |
| **NEW** — second cipher + on-disk formats | Deliberate, contained: versioned fixed-layout `.svenc`/`.svkey`, authenticated, gated on the §0 sign-off. |

---

## 7. Build order (once §0 is confirmed)

1. Scaffold `sv-platform` (crate, workspace member, `PlatformError` + `ApiError` projection).
2. Hash File (streaming) — smallest, no new format. Tests + gates.
3. Verify Signature — reuse `IntegrityReport`. Tests + gates.
4. `.svenc` format + Encrypt File / Decrypt File (Argon2+secretbox). Tests + gates.
5. `.svkey` + generate-signing-keypair + Sign File. Tests + gates.
6. `sv-app`: `PlatformSurface` + `PlatformApp`; map errors; reuse `IpcPassphrase`. Tests.
7. `desktop`: thin `#[tauri::command]` wrappers + second managed state + `generate_handler!`.
8. Full workspace gate sweep; update `PRODUCT-VISION.md` status marks (Hash/Verify/Encrypt/Decrypt/Sign
   → ✅, standalone) only after green.

> This document is the design checkpoint. §0 is **confirmed**; implementation may proceed on the
> user's go-ahead, in the §7 build order.
```
