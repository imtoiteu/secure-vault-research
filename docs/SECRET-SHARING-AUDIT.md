# Secret Sharing — Standalone Extraction Audit & Implementation Plan

**Project:** Secure Vault → Security & Privacy Toolkit
**Status of this document:** Plan to review before coding. Contains **no code**.
**Evidence discipline:** Every load-bearing claim cites `file:line`, verified by direct source read during this analysis. Where the source contradicts an earlier draft assertion, the correction is stated explicitly and the stale hedge removed. Items that remain genuine design choices (not facts) are labelled *design decision* or *proposal*; nothing intent-level is presented as implemented.

---

## 1. Executive summary

Secret Sharing is **implemented but vault-bound**. The cryptographic core (Shamir over GF(2⁸) via Daan Sprenkels' `sss` hazmat layer, wrapped by `sv-sys-sss`, adapted by `SssSharer`, and exposed through the vault-agnostic `SecretSharer` trait) is reusable as-is. What blocks naive reuse is a **triple coupling** baked into the layers above the primitive:

1. **32-byte-only split.** `SecretSharer::split` accepts *exactly* a `Key32` (32 bytes), never arbitrary bytes or files (`sv-crypto-traits/src/lib.rs:348-353`), enforced down to the C signature `const uint8_t key[32]` (`sv-sys-sss/vendor/hazmat.h:42-45`; the header comment is explicit: the key "should be randomly and uniformly generated string of 32 bytes," `hazmat.h:33-34`). You cannot "share a file" with this API.
2. **UUID-bound envelope.** The on-disk share (`.svshare`, magic `SVSH`) embeds the vault UUID at bytes `[6..22]` and recovery *rejects* any share whose UUID does not match the target container (`src-tauri/src/service.rs:623-627`). Shares are meaningless without a vault to bind to.
3. **Session / master-key orchestration.** `split_key` splits the **vault master key** retrieved from an *unlocked session* (`service.rs:577,580-586`); `recover` reconstructs that MK and gates it through an age-identity `secretbox` unwrap, then mints a new session (`service.rs:630-641`). The whole flow assumes a vault lifecycle.

**Recommended approach (consistent with the toolkit's hard constraints):** Do **not** modify `VaultBackend`, `keys_split`/`keys_recover`, or the `SVSH` path. Instead, build a **parallel, vault-free module** in the already-implemented `sv-platform` crypto-services layer (`sv-platform/src/lib.rs:1-18`) using a **hybrid scheme**: generate a fresh random 32-byte **DEK**, split *the DEK* with the existing `sss` primitive (the DEK is the only value that must be 32 bytes, so the limit is satisfied structurally), and encrypt the arbitrary-size secret/file under that DEK with the existing `secretbox` AEAD. Define a new **vault-free share artifact** that mirrors the `sv-platform/src/artifact.rs` framing pattern (6-byte `MAGIC` + LE version + fixed header + pre-auth ceiling) but **replaces the vault UUID with a fresh random group id and binds the DEK→payload key derivation to the share header** (see §4a, §6 — this is the single biggest correction over the prior draft). Expose it through two additive `PlatformSurface` methods, an additive command segment, and additive DTOs — reusing the frozen `SV-INSUFFICIENT-SHARES` / `SV-UNAUTHORIZED` codes and **adding** the missing `PlatformError::InsufficientShares` variant. The vault's existing path stays untouched.

**Classification:** **Significant refactor (new module, not an in-place extraction).** The *primitive* is standalone-ready; every user-facing capability is gated by the three couplings; delivering a usable tool requires a new hybrid scheme, a new artifact format, and a new command/DTO surface — none obtainable by merely re-exporting existing code.

> **Correction to the earlier draft.** The draft attributed this conclusion and a "P7 = Medium-High effort / leave vault SVSH untouched" recommendation to `docs/PLATFORM-AUDIT.md:262-269` (and `:122-146`). **No such file exists** in `secure-vault/docs/` (verified: the directory contains `DEPLOYMENT.md`, `M0-CONTRACTS.md`, `M5-SCHEMA-DECISIONS.md`, `M6-IPC-DECISIONS.md`, `M7-HARDENING.md`, `RELEASE-READINESS.md`, `TOOLKIT-PHASE1-DESIGN.md`, `UX-REVIEW-AND-REDESIGN.md`, `VALIDATION-PLAN.md`, `VALIDATION-RESULTS.md`), and `TOOLKIT-PHASE1-DESIGN.md` does **not** mention secret sharing, a hybrid scheme, or a DEK. Those citations are removed throughout; the effort classification and the design below stand on this document's own source-grounded analysis, not on a nonexistent audit.

---

## 2. Current-state audit

### 2.1 What exists (by layer)

| Layer | Component | File evidence | Role | Vault coupling |
|---|---|---|---|---|
| Hazmat FFI | `sv-sys-sss` (vendored `hazmat.c`/`.h`) | `sv-sys-sss/src/lib.rs:54-87`; `vendor/hazmat.h:18,42-45,65-67` | Splits a fixed 32-byte key into `n` 33-byte shares, threshold `k`; Lagrange-combine; **no** integrity check (`hazmat.h:53-57`) | **None** (pure key math) |
| Trait ABI | `SecretSharer` trait | `sv-crypto-traits/src/lib.rs:345-356` | `split(&Key32, n, k) → Vec<KeyShare>`; `combine(&[KeyShare]) → Key32` | **None** (vault-agnostic) |
| Impl adapter | `SssSharer` | `sv-crypto/src/lib.rs:143-173` | Wraps FFI, zeroizes scratch, maps errors to `CryptoError::InvalidParameter` | **None** (pluggable, zero-sized) |
| Orchestration | `VaultBackend::split_key` / `recover` | `service.rs:565-603`, `605-642` | Splits vault MK from session; rebuilds MK from shares; UUID check; credential gate; new session | **High** (MK + UUID + session) |
| Envelope | `build_share_envelope` / `parse_share_envelope` | `service.rs:735-751`, `753-770` | `SVSH` framing, UUID binding | **High** (UUID at `[6..22]`) |
| Command/DTO | `keys_split` / `keys_recover`, `ShareExportInfo`, `SharePolicy` | `src-tauri/src/lib.rs:87-98`; `sv-types/src/lib.rs:44-50,107-117` | IPC surface; no-secret-in-DTO | **High** (session-bound split; path+UUID recover) |

### 2.2 Capability / coupling summary

| Capability | Present today? | Where | Reusable standalone? |
|---|---|---|---|
| Split a **32-byte key** into `n`/`k` shares | Yes | `SecretSharer::split` (`sv-crypto-traits/src/lib.rs:348-353`) | **Yes, directly** (primitive is vault-agnostic) |
| Combine `≥k` shares → 32 bytes | Yes | `SecretSharer::combine` (`:354-355`) | **Yes, directly** |
| Split an **arbitrary-size** secret/file | **No** | — | Requires hybrid (DEK + AEAD) |
| Authenticated/integrity-checked shares | **No** at hazmat layer; authentication is one layer up | `vendor/hazmat.h:53-57`; `sv-sys-sss/src/lib.rs:9-11` | Reusable *if* a new artifact provides the auth layer **and binds the header** (§6) |
| Vault-free share artifact | **No** | only `SVSH` exists, UUID-bound | Must be designed (§4b) |
| `secretbox` over arbitrary payloads | Yes | `sv-crypto/src/secretbox.rs:20-34` (one-shot, in-memory, no size limit, no AAD) | Yes, with the header-binding caveat in §6 |
| Passphrase-sealed artifact framing w/ pre-auth ceiling | Yes | `sv-platform/src/artifact.rs:4-46,98-104` | Yes (template to mirror; the DEK path drops the Argon2 header) |
| `read_capped` / `refuse_existing` / `write_atomic` helpers | Yes | `sv-platform/src/lib.rs:93-128` | Yes (reused directly) |

### 2.3 EXACT `.svshare` (`SVSH`) byte layout — preserve verbatim, do not reuse

Total length: **58 bytes** (`SHARE_ENVELOPE_LEN = 4 + 2 + 16 + 1 + 1 + 1 + KEYSHARE_LEN`, `KEYSHARE_LEN = 33`; `service.rs:56`, with `KEYSHARE_LEN` canonical at `sv-crypto-traits/src/lib.rs:33`).

```
off  len  field
0    4    MAGIC               b"SVSH"            (service.rs:53)
4    2    envelope_version    u16 LE = 1         (service.rs:54)
6    16   vault_uuid                              (binds share to a specific vault)
22   1    index               share index
23   1    total               shares_total
24   1    threshold           k
25   33   key_share           [u8; KEYSHARE_LEN] (byte0 = x-coord, bytes1..33 = GF(2^8) y)
```

**Now fully source-confirmed (earlier "uncertain" hedge removed).** `build_share_envelope` writes the fields in the order `magic, version, uuid, index, total, threshold, share` at exactly these offsets (`service.rs:743-749`). `parse_share_envelope` reads `bytes[0..4]` magic, `bytes[4..6]` version, `bytes[6..22]` uuid, `bytes[24]` threshold, and `bytes[25..25+33]` share (`service.rs:754-768`).

**Real asymmetry worth recording:** `build_share_envelope` *writes* `index` at `[22]` and `total` at `[23]`, but `parse_share_envelope` **never reads them back** — it extracts only uuid (`[6..22]`), threshold (`[24]`), and the share bytes (`service.rs:764-768`). The vault's `recover` therefore does not consult per-share `index`/`total`; the x-coordinate it relies on is carried *inside* the 33-byte share (byte 0), not in the envelope index field. This is benign for the vault (combine self-describes from the share), but it means the envelope's `index`/`total` are advisory metadata, not load-bearing for recovery. The new module should not replicate write-but-never-read fields.

Filename scheme: `{vault_uuid_hyphenated}.share{index}.svshare` (`service.rs:591`). Not load-bearing for the new module (which uses its own naming, §4d), so no hedge is needed.

### 2.4 Security properties to preserve (in any standalone port)

These hold today and must hold in the new module:

- **Information-theoretic security below threshold.** `< k` shares reveal nothing about the secret — proven by `below_threshold_does_not_recover_key` (`sv-sys-sss/src/lib.rs:117-123`).
- **No integrity at the share layer; authentication is one layer up.** The hazmat library does *no* checking; a wrong/insufficient share set silently yields a wrong key, not an error (`vendor/hazmat.h:53-57`; `sv-sys-sss/src/lib.rs:74-76`). The vault supplies authentication via `secretbox` unwrap of the age identity (`service.rs:635-640`). The standalone module must supply an equivalent AEAD authentication layer **and bind the artifact header into it** (§6).
- **CSPRNG randomness.** Polynomial coefficients come from `getrandom` (OS CSPRNG) via the crate's C-ABI `randombytes` export (`sv-sys-sss/src/lib.rs:38-48`). The platform layer itself calls `getrandom::getrandom` directly for salts/nonces (`sv-platform/src/artifact.rs:54-55`; `sv-crypto/src/secretbox.rs:23-24` for the secretbox nonce via `sv_sys_sodium::random_bytes`).
- **Zeroization + no serialization of secrets.** `Key32` and `KeyShare` zeroize on drop and redact `Debug`; neither implements `Serialize` (`sv-crypto-traits/src/lib.rs:153-154,167-171,175-176,189-193`). `SssSharer` zeroizes scratch buffers after split/combine (`sv-crypto/src/lib.rs:157,169-170`).
- **Oracle-safe coded errors.** Insufficient-count is a *non-secret pre-check* (`SV-INSUFFICIENT-SHARES`, `sv-types/src/lib.rs:161-164`) distinct from authentication failure (`SV-UNAUTHORIZED`, `:157-160`), which merges wrong-shares with wrong-passphrase. The vault enforces the count pre-check *before* combine (`service.rs:612-618`).
- **No secret in DTO.** Shares are written to disk; `ShareExportInfo` carries only metadata + path, never share bytes (`sv-types/src/lib.rs:104-117`).

---

## 3. The three coupling layers

### 3.1 Coupling A — 32-byte-only split

**Evidence.** `SecretSharer::split(&self, key: &Key32, …)` takes only `Key32` (`sv-crypto-traits/src/lib.rs:348-353`). The sole impl calls `create_keyshares(key.expose_secret(), …)` where the FFI declares `const uint8_t key[32]` (`sv-crypto/src/lib.rs:154`; `vendor/hazmat.h:42-45`). A compile-time assertion pins the share length to 33 (`sv-sys-sss/src/lib.rs:24`).

**Why it blocks naive reuse.** A toolkit user wants to split a passphrase, a file, or a recovery seed of arbitrary length. The primitive cannot ingest any of these directly. Calling `split` on raw user bytes is impossible without a fixed-32-byte indirection.

### 3.2 Coupling B — UUID-bound envelope

**Evidence.** `build_share_envelope` writes the vault UUID into envelope bytes `[6..22]` (`service.rs:745`); `recover` extracts it and rejects mismatches with `InvalidInput("share belongs to a different vault")` (`service.rs:623-627`). The DTO `ShareExportInfo.vault_uuid` couples each artifact to a parent vault (`sv-types/src/lib.rs:108-117`).

**Why it blocks naive reuse.** A standalone tool has **no vault and no UUID**. Reusing this envelope would force fabricating a UUID and a vault container, and recovery would still demand a matching vault on disk. The binding identity must be replaced with something vault-free (a fresh random group id, §4b).

### 3.3 Coupling C — session / master-key orchestration

**Evidence.** `split_key` retrieves the MK from an unlocked session (`session_mk_path`, `service.rs:577`) and splits *that* MK (`service.rs:580-586`). `recover` reads the vault container by path, count-prechecks (`service.rs:613-618`), combines (`service.rs:630-633`), runs the **credential gate** — an age-identity `secretbox` unwrap whose failure surfaces as `AuthFailed` (`service.rs:634-640`) — and finally mints a new session (`service.rs:641`).

**Why it blocks naive reuse.** The "secret" here is definitionally the vault MK, the authentication oracle is the vault's age identity, and the output is a vault session. A standalone module shares none of these. It needs its own secret (the DEK), its own authentication (an AEAD tag over the payload, with the header bound in), and its own output (recovered plaintext), with **no** session lifecycle.

---

## 4. Target design — a vault-free Secret Sharing module

Design intent: a parallel module living entirely in `sv-platform`, reusing vetted primitives, additive everywhere, never touching the vault path. All byte layouts and sizes below are **design proposals to review**, not measured facts; everything cited `file:line` is source-confirmed.

### 4.1 (a) Hybrid scheme to lift the 32-byte limit — with explicit header binding

**Scheme.**
1. **Generate a fresh random 32-byte DEK** by calling `getrandom::getrandom(&mut dek)` directly (the same call site shape `artifact.rs:54-55` uses for the salt), mapping an `Err` to `PlatformError::Internal` (matching `artifact.rs:55`). Wrap it in `Key32` immediately (`sv-crypto-traits/src/lib.rs:156-160`). **Do not** call the `sv-sys-sss` `randombytes` FFI symbol (that is the C-ABI export the vendored C links against, `sv-sys-sss/src/lib.rs:38-48`); the platform layer uses the Rust `getrandom` API.
2. **Derive the payload key from the DEK *and the share header*** (this is the correction — see the binding subsection below) using BLAKE3 `derive_key`, then split the **DEK** with the existing primitive: `SecretSharer::split(&dek, total, threshold) → Vec<KeyShare>` (33 bytes each, `sv-crypto/src/lib.rs:148-159`). The DEK is the *only* value that must be exactly 32 bytes, so the 32-byte constraint is satisfied structurally, not worked around.
3. **Encrypt the arbitrary-size payload** under the derived payload key with `secretbox::seal(&payload_key, payload)` (`sv-crypto/src/secretbox.rs:20-27`, one-shot, no size limit). The returned `Wrapped { nonce, ciphertext }` carries a 24-byte nonce and a Poly1305-authenticated ciphertext (the ciphertext "includes the 16-byte MAC," `secretbox.rs:12`).

**`secretbox` vs `age` — choice and rationale (design decision).** Use **`secretbox`** for the payload, not `age`.
- *Why secretbox:* `sv-platform` already uses `secretbox` for its `.svenc`/`.svkey` artifacts via `artifact.rs:59,116`; it is in-process, libsodium-FFI only, and authenticated (XSalsa20-Poly1305). `sv-platform` already depends on `sv-crypto`, which re-exports `secretbox` as a public module (`sv-crypto/src/lib.rs:25`). Reusing it keeps the module self-contained and matches the established pattern (`sv-platform/src/lib.rs:15-18`).
- *Why not age here:* `age` is a bundled, hash-pinned **subprocess** driven by the `FileCipher` trait (`sv-crypto-traits/src/lib.rs:358-376`) — heavier, requires the `age` toolchain, and is designed for recipient/identity keypairs, not for a symmetric DEK we already hold. The `FileCipher`/`age` streaming path remains the right tool for a separate **Encrypt/Decrypt File** module and for a future *very large file* variant of secret sharing, but is unnecessary for the first cut.

**CRITICAL CORRECTION — the header MUST be bound to the ciphertext.** The earlier draft claimed "domain-separated key derivation binds the header to the ciphertext." **That is false as the primitives stand**, and the revision fixes it:
- `secretbox::seal` takes only `(key, plaintext)` and provides **no AAD** (`sv-crypto/src/secretbox.rs:20-27`; the module doc is explicit: M2 wraps "with a random nonce and **no associated data**," `secretbox.rs:4-5`). So nothing in `secretbox` binds the surrounding artifact header.
- `derive_context` in `artifact.rs` separates **only by the 6-byte MAGIC** (`artifact.rs:135-138`: `format!("secure-vault/platform/v1/{}", tag.trim_end_matches('\0'))`). It does **not** incorporate `group_id`, `n`, `k`, `payload_ref`, or the nonce.
- Therefore, if the payload were sealed with `secretbox::seal(dek, payload)` keyed by the raw DEK (as the draft proposed), an attacker could flip `group_id`/`n`/`k`/`payload_ref`/`share_index` bytes in the share artifact and `secretbox::open` would **still succeed** — the header would be unauthenticated. This is a real binding gap, exposed by the negative test in §5/§8.

**Fix (design decision):** derive the payload key as a BLAKE3 `derive_key` over the DEK **with a context string that includes the security-relevant header fields**, and feed *that* derived key to `secretbox`. Concretely:
- payload key = `Blake3Hasher.derive_key(&ctx, dek.expose_secret())` where `ctx = "secure-vault/platform/v1/SVSS|" + hex(group_id) + "|" + n + "|" + k` (`KeyDerivation::derive_key`, `sv-crypto-traits/src/lib.rs:297-299`; impl `sv-crypto/src/lib.rs:46-54`). `derive_key` returns a zeroizing `Key32` and wipes its scratch.
- Because the payload key now functionally depends on `group_id`, `n`, and `k`, any tamper of those header bytes changes the derived key, and `secretbox::open` fails as `AuthFailed` → `SV-UNAUTHORIZED`. The header is thereby *cryptographically bound* without needing AAD support.
- The `share_index` (x-coordinate) is **not** folded into the context (it legitimately differs per share while the payload key must be identical across shares); its integrity is covered by the combine step itself (a wrong x-coordinate yields a wrong DEK → wrong payload key → AEAD open fails).

**Do not rely on a future M5 to retrofit AAD here.** The M5 note in `secretbox.rs:4-7` is about binding **vault** wrapped-blobs to their `vault_uuid`/field-label/version for the *container* format — a vault concern. It does not promise a general AAD-capable AEAD that the standalone `SVSS` path would inherit. The header-binding-via-derived-key approach above is self-sufficient and does not wait on M5.

**Passphrase involvement (design decision).** The core split/recover flow is **passphrase-free**: the secret is protected purely by the *threshold* (you need `k` of `n` shares; below threshold reveals nothing, `sv-sys-sss/src/lib.rs:117-123`). This is the defining property of Shamir sharing and must not be diluted. A passphrase is **not** required and should not be mandatory — adding one would change the model from "k-of-n possession" to "k-of-n *and* a remembered secret," undermining the recovery use-case. Consequently the `SVSS` payload uses **no Argon2 header** (no salt, no KDF params): the payload key is derived from the DEK, not from a passphrase. The passphrase-sealed `artifact.rs` path (Argon2id, `seal_with_passphrase`, `artifact.rs:49-73`) is a *sibling* mechanism, not part of this flow. (An *optional* passphrase wrap of individual shares is recorded as a deferred open question, not a v1 feature; §7 R9.)

### 4.2 (b) Vault-free share-artifact format

Two artifacts per split: **one payload artifact** (shared by all shares) and **one share artifact per share**. Both mirror the `sv-platform/artifact.rs` conventions (6-byte `MAGIC`, LE `u16` version, fixed header, pre-auth bounds) but drop the Argon2 header (no passphrase) and replace the vault UUID with a fresh random group id. **All sizes are proposals to review.**

**MAGIC choice (design decision, bytes shown).** Use a **6-byte** MAGIC to match the platform convention `SVENC\0` / `SVKEY\0` (`sv-platform/src/lib.rs:41-43`), distinct from the vault's 4-byte `SVSH` (`service.rs:53`). Two distinct magics are needed (payload vs share). Proposal, shown as explicit bytes:
- Payload artifact: `b"SVSSP\0"` = `[0x53,0x56,0x53,0x53,0x50,0x00]` (5 letters + 1 null).
- Share artifact: `b"SVSSS\0"` = `[0x53,0x56,0x53,0x53,0x53,0x00]` (5 letters + 1 null).

These are unambiguous vs `SVENC\0`, `SVKEY\0`, and vs the 4-byte `SVSH` (different length and bytes 4–5). *(If a single name is preferred, `b"SVSS\0\0"` = `[…,0x00,0x00]` is the 4-letter form; but two magics cleanly separate the two file types and let `recover_secret` reject a payload supplied as a share and vice versa. The two-magic form is recommended.)* The `derive_context` convention trims trailing nulls (`artifact.rs:136-137`), so the share context tag is `SVSSS`.

**Share artifact (one file per share) — proposed layout:**

```
off  len  field                     notes
0    6    MAGIC = b"SVSSS\0"        share magic (proposal)
6    2    format_version u16 LE = 1  mirrors artifact.rs FORMAT_VERSION (artifact.rs:30)
8    16   group_id                   fresh random per split; binds the cohort (replaces vault_uuid)
24   1    total  (n)                 1..=255
25   1    threshold (k)              1 <= k <= n   (matches sv-sys-sss validation, lib.rs:59-60)
26   1    share_index                advisory metadata (x-coord lives in byte 0 of key_share)
27   32   payload_ref                BLAKE3 hash of the WHOLE sealed payload blob (content binding)
59   33   key_share                  [u8; KEYSHARE_LEN]; byte0 = x-coord, 1..33 = GF(2^8) y
```

**Exact share length = 6 + 2 + 16 + 1 + 1 + 1 + 32 + 33 = 92 bytes.** (The earlier draft was internally inconsistent — it stated both 92 and 98; the correct figure is **92**, and the pre-auth fixed-length check uses 92.)

**Payload artifact (one file, shared by all shares) — proposed layout.** The DEK-keyed payload has **no Argon2 header** (no salt, no KDF params), so it is *not* "structurally identical to `artifact.rs`'s tail" (that tail is preceded by a passphrase header). The concrete layout:

```
off  len  field                     notes
0    6    MAGIC = b"SVSSP\0"        payload magic (proposal)
6    2    format_version u16 LE = 1
8    1    aead_alg = 0               XSalsa20-Poly1305 secretbox (mirrors artifact.rs AEAD_ALG_SECRETBOX = 0)
9    24   nonce                      secretbox nonce (NONCE_LEN = 24, artifact.rs:34; = SECRETBOX_NONCEBYTES)
33   ..   ciphertext                 secretbox output; INCLUDES the 16-byte Poly1305 tag (secretbox.rs:12)
```

**DEK-keyed payload header overhead = 6 + 2 + 1 + 24 = 33 bytes, plus the 16-byte tag inside the ciphertext.** Do **not** carry over the `artifact.rs` `HEADER_OVERHEAD` figure (its `HEADER_LEN = 6+2+1+4+4+4+16+1+24 = 62`, so `HEADER_OVERHEAD = 62 + 16 = 78`, `artifact.rs:35-36,46`) — that includes the Argon2 fields this format omits. The `SVSS` payload's own overhead is `33 + 16 = 49` bytes over the plaintext. `SECRETBOX_KEYBYTES = 32` matches the DEK and the derived payload key (`sv-crypto/src/secretbox.rs:10,22`).

**`payload_ref` definition (design decision).** `payload_ref` is `Blake3Hasher.hash(whole_payload_blob)` — the BLAKE3 of the **entire** sealed payload artifact (MAGIC + version + aead_alg + nonce + ciphertext), **not** just the ciphertext, so it binds the nonce too. `Hasher::hash(&[u8]) -> Hash32` exists and is the right call (`sv-crypto-traits/src/lib.rs:289`; impl `sv-crypto/src/lib.rs:35-37`); take `.0` (or `.to_hex()` for display). This lets recovery reject a share cohort pointed at the wrong/tampered payload *before* combine. It is a **binding, not a MAC**: an attacker controlling both shares and payload can produce a self-consistent (wrong) bundle, which still fails the AEAD open — so `payload_ref` is only a cheap pre-auth gate (§6).

**Splitting nonce/ciphertext on recover (made explicit).** `secretbox::open` needs a `Wrapped { nonce, ciphertext }` (`sv-crypto/src/secretbox.rs:31`). Recovery reconstructs it by slicing the payload blob exactly as `artifact.rs` does for its own format (`artifact.rs:105-107`: salt `[21..37]`, nonce `[38..62]`, ciphertext `[62..]`). For the `SVSS` payload the slices are: `nonce = blob[9..33]` (24 bytes) and `ciphertext = blob[33..].to_vec()` (the rest, including the 16-byte tag). There is no length prefix; "rest of the blob" is the ciphertext, mirroring `artifact.rs:107`.

**Pre-auth DoS ceiling.** The header is attacker-influenceable before authentication, so recovery must validate structural bounds **before** any expensive work — the stance `artifact.rs:82-104` takes. For this format the cheap pre-checks are: MAGIC match, version match (`IncompatibleVersion` on mismatch, as `artifact.rs:85-91`), `1 <= k <= n <= 255`, **exact** per-share length (92 bytes), and a read cap on the payload artifact. No Argon2 runs (no passphrase), so the KDF ceiling (`MAX_KDF_*`, `artifact.rs:40-42`) does not apply; the DoS surface is bounded by the size cap and fixed-length parsing.

**Input caps (corrected — recover side too).** Split caps the plaintext at `MAX_PLAINTEXT_BYTES = 2 GiB` via `read_capped(input, MAX_PLAINTEXT_BYTES)` (`sv-platform/src/lib.rs:38,93-101`). On **recover**, the hostile input is the *payload artifact* (ciphertext); cap it at `MAX_CIPHERTEXT_BYTES = MAX_PLAINTEXT_BYTES + HEADER_OVERHEAD` — the exact constant already used by `decrypt_file` for the same reason (`sv-platform/src/crypto.rs:16,46`). Each 92-byte share file is read with a tiny fixed cap (e.g. `read_capped(share, 4096)`), making oversized "share" files cheap to reject. This closes the gap the draft left open (it capped split but not the recover-side payload read).

**Domain separation (hedge removed — convention confirmed).** `derive_context` is `format!("secure-vault/platform/v1/{}", tag.trim_end_matches('\0'))` (`artifact.rs:135-137`). The `SVSS` payload key context therefore begins `secure-vault/platform/v1/SVSSS` and is *extended* with the bound header fields as in §4a. A `SVSS` payload can never be cross-decrypted as a `SVENC`/`SVKEY` artifact because the MAGIC differs and feeds the context (the existing `distinct_artifact_types_do_not_cross_open` test demonstrates the property for the passphrase path, `artifact.rs:216-227`).

**Versioning.** `format_version = 1`, additive-only evolution (new optional trailing fields), mirroring the vault's frozen-envelope discipline and the additive `CONTRACT_VERSION` rule (`sv-types/src/lib.rs:14-15,21-23`).

### 4.3 (c) Where it lives

- **Crate:** `sv-platform` (the "vault-free crypto-services layer," `sv-platform/src/lib.rs:1-5`). No new crate needed; add a new module file (e.g. `sharing.rs`) alongside `crypto.rs`/`integrity.rs`/`artifact.rs` (declared in `lib.rs:22-25`).
- **New methods on `PlatformCrypto`:** `split_secret` and `recover_secret`, mirroring the `encrypt_file`/`decrypt_file` shape (`sv-platform/src/crypto.rs:21-52`): `refuse_existing` → `read_capped` → derive/seal/split → `write_atomic`, and the inverse for recover. No backend injection is required — `PlatformCrypto` holds only zero-sized unit adapters (`sv-platform/src/lib.rs:64-80`) and `sv-platform` already depends on `sv-crypto` (re-exports `secretbox`, `SecretSharer`, `SssSharer`, `Key32`, `KeyShare`, `Blake3Hasher`) and `getrandom` (`sv-platform/Cargo.toml:13-19`). **No new external dependencies.** (Note: `SssSharer` is the adapter to use; `PlatformCrypto` would either hold a `SssSharer` unit field or construct one inline, since it is `Default`/zero-sized, `sv-crypto/src/lib.rs:144-145`.)
- **New `PlatformError` variant (now confirmed required).** `PlatformError` today has exactly `NotFound, Malformed, IncompatibleVersion, AuthFailed, InvalidInput, TooLarge, OutputExists, Io, Internal` — and **no `InsufficientShares`** (`sv-platform/src/error.rs:12-50`). The earlier "uncertain" flag is resolved: the variant **must be added**, with a `From<PlatformError> for ApiError` arm mapping it to the frozen `ApiError::InsufficientShares { got, need }` (which *does* exist in the frozen contract, `sv-types/src/lib.rs:161-164,199`). Add it next to the other benign-but-distinct mappings (`error.rs:52-77`), preserving the existing `AuthFailed → Unauthorized` merge (`error.rs:60-61`). Structural mismatches reuse the existing `Malformed → ApiError::Malformed` arm (`error.rs:56`) or `InvalidInput → ApiError::InvalidInput` (`error.rs:62`) — both already exposed at the IPC boundary, so no new code is needed there.
- **Overwrite policy (was omitted — now specified).** `crypto.rs` calls `refuse_existing(output)` before work and returns `OutputExists` → `ApiError::OutputExists` (`crypto.rs:27,45`; `error.rs:39-41,70`). `split_secret` writes **multiple** files (n shares + 1 payload). Policy (design decision): call `refuse_existing` on **every** target path (each share path and the payload path) *up front*, before generating the DEK or writing anything; if any exists, return `OutputExists` and write nothing. On a mid-write I/O failure, follow the `generate_signing_keypair` precedent of cleaning up already-written siblings to avoid orphans (`crypto.rs:81-85`). `recover_secret` writes one plaintext file and `refuse_existing`-guards it (mirroring `decrypt_file`, `crypto.rs:45`).

### 4.4 (d) Additive command surface + DTOs

Two new commands, **additive to `PlatformSurface`** (the standalone, session-free platform trait that already hosts `hash_file`, `verify_signature`, `encrypt_file`, `decrypt_file`, `generate_signing_keypair`, `sign_file`; `src-tauri/src/platform.rs:18,20-64`) — **not** the vault `CommandSurface` (`src-tauri/src/lib.rs:87-98`, which is session-bound). The IPC contract is additive-only and `CONTRACT_VERSION` stays `1` (`sv-types/src/lib.rs:23`; `APP_CONTRACT_VERSION`, `src-tauri/src/lib.rs:102`).

| Command | Shape (proposal) | Session? |
|---|---|---|
| `shares_split_secret` | `(input_path: String, shares_total: u8, threshold: u8, out_dir: String) → Result<ShareSplitReport, ApiError>` | **No** (the platform surface is session-free) |
| `shares_recover_secret` | `(share_paths: Vec<String>, payload_path: String, out_path: String) → Result<RecoverReport, ApiError>` | **No** |

Both are **session-free**, unlike vault `keys_split`/`keys_recover` (`src-tauri/src/lib.rs:87-98`). This matches the platform surface, whose methods take no `SessionHandle` (`platform.rs:20-64`).

**DTOs (no-secret-in-DTO enforced, `sv-types/src/lib.rs:5-10`):**
- `ShareSplitReport` (mirrors `ShareExportInfo`, `sv-types/src/lib.rs:104-117`): per-share `share_index`, `group_id` (hex), `threshold`, `shares_total`, `format_version`, `output_path`, plus the single `payload_path`. **No share bytes, no DEK.** Shares are written to `.svss` files exactly as the vault writes `.svshare` files (`service.rs:591-600`).
- `RecoverReport`: `output_path`, `bytes_written` — **no recovered plaintext, no DEK**.
- These are new types added to `sv-types`; like every type there they derive `Serialize`/`Deserialize` and carry only non-secret fields (`sv-types/src/lib.rs:17-19`).

**Filename scheme (was unspecified — now defined, design decision).** Per-share files: `{group_id_hex}.share{index}.svss`; payload file: `{group_id_hex}.payload.svss` (analogous to the vault's `{uuid}.share{index}.svshare`, `service.rs:591`). This makes step-3's "n share files + 1 payload file" assertion (§5) concretely checkable.

**Error codes (reuse the frozen contract; one addition):**
- `SV-INSUFFICIENT-SHARES` — non-secret pre-check when `provided < threshold`, returned *before* any combine attempt (mirror `service.rs:612-618`). Requires the new `PlatformError::InsufficientShares` + `From` arm (§4c).
- `SV-UNAUTHORIZED` — merged failure for wrong/tampered shares **or** a tampered payload (the `secretbox::open` Poly1305 check fails → `AuthFailed`, `secretbox.rs:31-33`; `error.rs:60-61`). Preserves the oracle-safe merge already used by the vault (`sv-types/src/lib.rs:157-160`).
- `SV-MALFORMED` / `SV-INVALID-INPUT` — for structural failures (bad magic, wrong length, bad version, **group_id mismatch**, **payload_ref mismatch**); see the oracle discussion in §4.4-oracle below. Both already exist and are already exposed (`error.rs:56,62`; `sv-types/src/lib.rs:148-149,166-167`).

**Oracle handling for `group_id` / `payload_ref` mismatch (was ambiguous — now decided).** Align with the vault's own choice: the vault surfaces a cross-vault share as `InvalidInput("share belongs to a different vault")` → `SV-INVALID-INPUT` (`service.rs:623-627`; `error.rs:62`). The new module mirrors this: a `group_id` disagreement among supplied shares, or a `payload_ref` that does not match the supplied payload's BLAKE3, is a **non-secret correctness check on attacker-supplied *files*** (the user picked the wrong files) and is safe to surface as `SV-INVALID-INPUT` (or `SV-MALFORMED` for a structurally unparseable share). This is **not** an authentication oracle: it reveals only "these files don't belong together," a fact the user already controls, exactly as the vault's UUID check does. The genuine secret-bearing decision — "are these the *right* shares for the *right* payload" — remains merged into `SV-UNAUTHORIZED` via the AEAD open. So: pick one of `SV-MALFORMED` (unparseable) / `SV-INVALID-INPUT` (parseable but mismatched cohort/payload), consistently, and never let a *cryptographic* outcome split out of `SV-UNAUTHORIZED`. Recommendation: `SV-INVALID-INPUT` for cohort/payload mismatch (matches the vault), `SV-MALFORMED` for bad magic/length/version.

**`CONTRACT_VERSION` note:** remains `1`; the addition is purely additive (new commands, new DTOs, one new internal error variant mapped to an *existing* frozen code). No existing DTO changes shape. This honors the "additive evolution only" rule (`sv-types/src/lib.rs:14-15,21-23`).

### 4.5 Coupling detail the plan must honor — how `combine` is fed

`SecretSharer::combine(&[KeyShare])` (`sv-crypto-traits/src/lib.rs:354-355`) **does not take a threshold**: it infers `k` from the number of shares supplied and Lagrange-interpolates over whatever x-coordinates the shares carry (each share self-describes its x-coordinate in byte 0, `sv-sys-sss/src/lib.rs:8`). Confirmed behavior from the primitive's own tests:
- **Supplying more than `k` valid shares still recovers correctly** (`split_then_combine_roundtrips` combines all 5 of a 3-of-5 split and gets the key, `sv-sys-sss/src/lib.rs:107-113`).
- **Supplying `< k` shares silently yields a wrong key, not an error** (`below_threshold_does_not_recover_key`, `:117-123`) — there is no integrity check at this layer (`hazmat.h:53-57`).

Recover flow decisions (design decisions, grounded in the above):
1. **Which shares are passed to `combine`?** Pass **all** provided (and validated) shares, not exactly `k`. This matches the vault, which combines every supplied share (`service.rs:619-633`), and is safe because the AEAD open authenticates the result.
2. **Duplicate `share_index` (same x-coordinate) is a latent hazard.** Two shares with the same x-coordinate break Lagrange interpolation (a zero denominator / degenerate system), and **neither `sss` nor the vault's `recover` guards against it** (`service.rs:619-633` does not deduplicate). The new module **should** guard it explicitly: before `combine`, reject a set containing duplicate x-coordinates (byte 0 of each `key_share`, or the `share_index` field) as `SV-INVALID-INPUT`, *before* calling `combine`. This is a non-secret structural check on user-supplied files. (Worth flagging upstream as a latent vault bug, but **out of scope** here — do not modify the vault path.)
3. **A `k`-sized set from a *different* split** combines to garbage (different polynomial), which then fails the AEAD open → `SV-UNAUTHORIZED`. The `group_id`/`payload_ref` pre-checks catch the common "wrong files" case earlier as `SV-INVALID-INPUT`; the AEAD remains the authoritative gate.

### 4.6 (e) UI shape (brief)

Two task screens under a **"Back up & recover"** sidebar group, each following the frozen task-screen template:
- **Split into pieces** — pick a file/secret, choose *total pieces* and *how many are needed* (`n`, `k`), choose an output folder; on success show the per-share file list + the one payload file (from `ShareSplitReport`, no secrets).
- **Recover from pieces** — select `≥ k` share files + the payload file + an output path; on success show the recovered file path. Surface `SV-INSUFFICIENT-SHARES` as a plain "you need at least *k* pieces" message (non-secret), `SV-INVALID-INPUT` as "these pieces don't belong together / wrong payload file," and `SV-UNAUTHORIZED` as a generic "these pieces don't match / are corrupted" (oracle-safe).

*(UI specifics are deliberately thin; this is a planning doc, and no UI/code changes are authorized here.)*

---

## 5. Extraction roadmap (ordered, verifiable)

Each step is independently checkable and **never touches `VaultBackend`, `keys_split`/`keys_recover`, or the `SVSH` path.**

1. **Confirm the primitive is reusable as-is.** Re-read `SecretSharer` (`sv-crypto-traits/src/lib.rs:345-356`), `SssSharer` (`sv-crypto/src/lib.rs:143-173`), `secretbox` (`sv-crypto/src/secretbox.rs:20-34`), and `derive_key` (`sv-crypto/src/lib.rs:46-54`). *Verify:* a unit test that derives a payload key from a fresh random 32-byte DEK + header, seals/opens a payload, splits the DEK, and recombines `k` of `n` round-trips, with `< k` failing (mirrors `sv-sys-sss/src/lib.rs:117-123`).
2. **Define the `SVSS` artifact constants + parsers** (payload + share) in a new `sv-platform` module. *Verify:* fixed-length parse rejects short/long input and bad MAGIC/version *before* any crypto (pre-auth test, mirroring `artifact.rs:179-189,206-214`); share length asserted at **92 bytes**, payload-header overhead at **49 bytes** (33 + 16).
3. **Implement `split_secret`** on `PlatformCrypto`: `refuse_existing` on all targets → `read_capped(input, MAX_PLAINTEXT_BYTES)` → fresh DEK (`getrandom`) → derive payload key bound to `(group_id,n,k)` → `secretbox::seal` → BLAKE3 `payload_ref` over the whole payload blob → `SecretSharer::split(&dek, n, k)` → write payload artifact + per-share files atomically (`write_atomic`, `sv-platform/src/lib.rs:113-128`) → zeroize DEK/plaintext. *Verify:* exactly **n share files + 1 payload file** with the §4d names; DEK zeroized; returned `ShareSplitReport` contains no secret bytes.
4. **Implement `recover_secret`**: `refuse_existing(out)` → count pre-check (`< k` → `SV-INSUFFICIENT-SHARES`, **before** any combine, mirroring `service.rs:612-618`) → parse shares (`read_capped` small cap) → reject duplicate x-coordinates and mismatched `group_id` as `SV-INVALID-INPUT` → read payload (`read_capped(payload, MAX_CIPHERTEXT_BYTES)`) → verify `payload_ref` BLAKE3 matches (else `SV-INVALID-INPUT`) → `combine` all shares → re-derive payload key from recovered DEK + header → split nonce `blob[9..33]` / ciphertext `blob[33..]` → `secretbox::open` (failure → `AuthFailed`/`SV-UNAUTHORIZED`) → `write_atomic` plaintext → zeroize. *Verify:* wrong shares and tampered payload both yield `SV-UNAUTHORIZED`; tampered `group_id`/`n`/`k` bytes yield `SV-UNAUTHORIZED` (because the derived key changes); mismatched cohort/payload yields `SV-INVALID-INPUT` *before* combine.
5. **Add `PlatformError::InsufficientShares { got, need }` + `From` arm** to `ApiError::InsufficientShares` (`sv-platform/src/error.rs:12-50,52-77`), preserving `AuthFailed → Unauthorized`. *Verify:* `From` impl compiles and maps to the frozen code (`sv-types/src/lib.rs:163-164,199`); existing `error.rs` mapping test still passes (`error.rs:84-126`).
6. **Add the two commands + DTOs** additively to `PlatformSurface` and the Tauri wrapper layer (`src-tauri/src/platform.rs:18-64`; desktop command wrappers, `desktop/src/lib.rs`). *Verify:* `APP_CONTRACT_VERSION`/`CONTRACT_VERSION` unchanged (`src-tauri/src/lib.rs:102`; `sv-types/src/lib.rs:23`); existing command tests still pass (`platform.rs:182-…`).
7. **UI screens** (separate, after the surface lands).

**Ships first:** Steps 1–5 (the `sv-platform` core: `split_secret`/`recover_secret` + the `SVSS` artifacts + the error variant), gated by the standard product gates (`cargo fmt --all --check`, `cargo clippy --workspace --all-targets -- -D warnings`, `cargo build --workspace --locked`, `cargo test --workspace`, `cargo deny check`). This delivers a testable, vault-free splitting/recovery capability before any IPC/UI work.

---

## 6. Security review

**Properties carried over from today (must be preserved):**
- **Information-theoretic below threshold for the DEK.** The DEK is split with the same `sss` primitive proven to reveal nothing below `k` (`sv-sys-sss/src/lib.rs:117-123`). Because the payload is encrypted *only* under a key derived from the DEK, `< k` shares ⇒ no DEK ⇒ no payload key ⇒ no plaintext: information-theoretic for the key, computational (XSalsa20-Poly1305) for the payload.
- **Authenticated shares via the payload AEAD, with the header bound in.** The hazmat layer authenticates nothing (`vendor/hazmat.h:53-57`); authentication is supplied one layer up — here, `secretbox::open`'s Poly1305 tag (`sv-crypto/src/secretbox.rs:31-33`). A wrong reconstructed DEK fails to open the payload, exactly mirroring the vault's "wrong MK fails the secretbox unwrap" gate (`service.rs:634-640`). **Beyond the draft:** because the payload key is `derive_key(DEK, ctx=…|group_id|n|k)`, any tamper of those header bytes changes the key and also fails the open (§4a). This closes the unauthenticated-header gap.
- **CSPRNG.** DEK, `group_id`, and the secretbox nonce all come from OS CSPRNG: DEK/`group_id` via `getrandom::getrandom` (as `artifact.rs:54-55`), nonce via `sv_sys_sodium::random_bytes` inside `secretbox::seal` (`sv-crypto/src/secretbox.rs:23-24`); the `sss` polynomial coefficients via the crate's `randombytes`→`getrandom` export (`sv-sys-sss/src/lib.rs:38-48`).
- **Zeroization.** DEK and the derived payload key are `Key32` (zeroize on drop, `sv-crypto-traits/src/lib.rs:153-154`); shares are `KeyShare` (zeroize, `:175-176`); `SssSharer` zeroizes scratch (`sv-crypto/src/lib.rs:157,169-170`); `derive_key` wipes its scratch (`sv-crypto/src/lib.rs:50-53`); `split_secret`/`recover_secret` must `zeroize()` the in-memory plaintext after `write_atomic`, mirroring `decrypt_file` (`sv-platform/src/crypto.rs:48-50`).
- **Oracle-safety.** `SV-INSUFFICIENT-SHARES` is a non-secret count pre-check; `SV-UNAUTHORIZED` merges all *cryptographic* authentication failures (`sv-platform/src/error.rs:60-61`; `sv-types/src/lib.rs:157-160`). Non-secret "wrong files" conditions surface as `SV-INVALID-INPUT`/`SV-MALFORMED`, matching the vault's own UUID-mismatch choice (`service.rs:623-627`).
- **No-secret-in-DTO.** Reports carry paths/metadata only (`sv-types/src/lib.rs:5-10`).

**New surfaces and their risks:**
- **DEK handling.** A *new* transient secret (the DEK) exists in `split_secret`/`recover_secret`. Risk: leaking via logs, `Debug`, or serialization. Mitigation: type it as `Key32` (redacted `Debug`, no `Serialize`, zeroize-on-drop, `sv-crypto-traits/src/lib.rs:153-154,167-171`); never place it in a DTO; zeroize immediately after splitting/sealing (and after combining/opening on recover).
- **`group_id` binding is integrity-advisory, not a secret and not, by itself, an authentication boundary.** It prevents *accidental* cross-cohort mixing, but an attacker can forge it. Cohort integrity ultimately rests on the AEAD open of the *correct* payload (and, now, on the header being folded into the payload-key derivation). Mitigation: treat `group_id` as a non-secret correctness check (like the vault UUID, `service.rs:623-627`), surfaced as `SV-INVALID-INPUT`; document in code that it is advisory, so future maintainers don't mistake it for a security boundary.
- **`payload_ref` (BLAKE3) is a binding, not a MAC.** It detects a cohort pointed at the wrong payload pre-combine, but a sophisticated attacker controlling both shares and payload can produce a self-consistent (wrong) bundle — which still fails the AEAD at open. Mitigation: keep `payload_ref` as a cheap pre-auth integrity gate; never treat a passing `payload_ref` as authentication.
- **No AAD in `secretbox`.** `secretbox::seal` provides no associated data (`sv-crypto/src/secretbox.rs:4-5,20-27`). **Do not** assume the header is authenticated by the AEAD directly, and **do not** wait on M5 (its AAD note is a vault-header concern, `secretbox.rs:4-7`). Mitigation: bind the header by folding `(group_id, n, k)` into the BLAKE3 `derive_key` context that produces the payload key (§4a) — this makes any header tamper change the key and fail the open, achieving header binding without AAD.

---

## 7. Risk register

| ID | Risk | Evidence / source | Mitigation |
|---|---|---|---|
| **R1** | **Triple coupling** (32-byte split + UUID envelope + session/MK) blocks direct reuse | §3; `sv-crypto-traits/src/lib.rs:348-353`; `service.rs:623-627,577,580-586` | Build a parallel `sv-platform` module with hybrid DEK + vault-free `SVSS` artifacts; never touch `VaultBackend` |
| **R2** | **Unauthenticated header** — attacker flips `group_id`/`n`/`k`/`payload_ref` and the AEAD still opens | `secretbox.rs:4-5,20-27` (no AAD); `artifact.rs:135-137` (derive_context = MAGIC only) | **Bind the header into the payload-key derivation**: payload key = `derive_key(DEK, ctx incl. group_id,n,k)` (§4a); negative test in §8 |
| **R3** | **Mismatched cohorts** — user mixes shares from two different splits | New surface | 16-byte random `group_id` per split; recover rejects disagreeing `group_id`s as `SV-INVALID-INPUT` *before* combine (mirrors UUID check, `service.rs:623-627`); AEAD is the final gate |
| **R4** | **DEK reuse** would break confidentiality/independence | New surface | Generate a **fresh** DEK per `split_secret` from `getrandom`; never derive from inputs; zeroize after use (mirrors per-split coefficient freshness, `sv-sys-sss/src/lib.rs:138-147`) |
| **R5** | **Streaming / in-memory limits** — `secretbox` is one-shot and buffers; large files OOM | `sv-crypto/src/secretbox.rs:20-27` (one-shot); `MAX_PLAINTEXT_BYTES = 2 GiB`, `sv-platform/src/lib.rs:38` | Enforce 2 GiB on split (`read_capped`, `lib.rs:93-101`) **and** `MAX_CIPHERTEXT_BYTES` on the recover-side payload read (`crypto.rs:16,46`); route truly-large files to a future `age`/`FileCipher` streaming variant (`sv-crypto-traits/src/lib.rs:358-376`) — *out of scope for v1* |
| **R6** | **Pre-auth DoS** — attacker-crafted header/oversized share forces work | `artifact.rs:82-104` (the existing ceiling stance) | Validate MAGIC/version/`1<=k<=n<=255`/exact 92-byte share length and the ciphertext cap before any crypto; tiny cap on each share read; no Argon2 runs |
| **R7** | **Wrong/tampered payload silently recovered as garbage** (hazmat does no integrity check) | `vendor/hazmat.h:53-57`; `sv-sys-sss/src/lib.rs:74-76` | Authentication via `secretbox::open` Poly1305 tag → merged `SV-UNAUTHORIZED`; `payload_ref` BLAKE3 pre-check as cheap early reject |
| **R8** | **Duplicate `share_index`** (same x-coordinate) breaks Lagrange → silent garbage; vault doesn't guard it either | `service.rs:619-633` (no dedup); `sv-sys-sss/src/lib.rs:76-87` | Reject duplicate x-coordinates as `SV-INVALID-INPUT` *before* `combine`; note the vault's latent gap but do **not** modify the vault path |
| **R9** | **Oracle leak** — distinguishing "wrong shares" from "wrong payload" cryptographically | `sv-platform/src/error.rs:60-61` (merged mapping) | Keep all *cryptographic* authentication failures merged into `SV-UNAUTHORIZED`; only non-secret count/cohort/format checks use `SV-INSUFFICIENT-SHARES`/`SV-INVALID-INPUT`/`SV-MALFORMED` |
| **R10** | **Accidental modification of the vault path** during refactor | §8 | Touch only `sv-platform` + additive `PlatformSurface`/DTO/error; gate every change with the full `cargo` gate set; explicit "do-not-touch" list (§8) |
| **R11** | **Scope creep into passphrase-wrapping shares**, changing the threshold security model | §4a | Keep v1 passphrase-free; record optional per-share passphrase wrap as a deferred open question, not a feature |

---

## 8. What stays vault-private (do NOT touch)

The following remain exclusively the vault's and must be left **byte-for-byte unchanged** by this work:

- **The `SVSH` UUID-bound share path** — magic `b"SVSH"` (`service.rs:53`), the 58-byte envelope with `vault_uuid` at `[6..22]`, `build_share_envelope`/`parse_share_envelope` (`service.rs:735-770`), and the `.svshare` filename scheme (`service.rs:591`). The new module uses **distinct** magics (`SVSSP\0` / `SVSSS\0`) and a `group_id`, never a UUID. The vault's write-but-never-read `index`/`total` asymmetry (§2.3) is the vault's own format; the new module does not replicate it.
- **`keys_split` / `keys_recover`** commands, their session-bound/path-based shapes, and `ShareExportInfo` / `SharePolicy` DTOs (`src-tauri/src/lib.rs:87-98`; `sv-types/src/lib.rs:44-50,104-117`). The new commands are *separate* (`shares_split_secret` / `shares_recover_secret`), additive to the **`PlatformSurface`** trait (`src-tauri/src/platform.rs:18-64`).
- **The vault master key, session lifecycle, and the age-identity credential gate** (`service.rs:565-642`). The standalone module has its own DEK, no session, and its own AEAD authentication; it never reads or writes a vault container, header, or share policy.
- **`SHARE_ENVELOPE_VERSION = 1`** and the frozen `SVSH` layout (`service.rs:54-56`) — preserved as the vault's own format; the new module versions its own `SVSS` format independently.

The only shared assets are the **vetted primitives** (`SecretSharer`/`SssSharer`/`sss`, `secretbox`, `getrandom`, `Blake3Hasher` hash + `derive_key`, `Key32`/`KeyShare` types) and the **artifact-framing conventions and helpers** of `sv-platform` (`artifact.rs` layout discipline, `read_capped`/`refuse_existing`/`write_atomic`, the `MAX_*` caps, the `PlatformError`→`ApiError` projection) — all consumed, none of the vault's modified.

---

### Appendix: evidence-confidence notes

Every item the earlier draft flagged as "uncertain / not in the confirmed verdict set" was **resolved by direct source read** during this revision; the hedges are removed and the corrected facts are inlined above. For traceability:

- **`SVSH` bytes `[22]`/`[23]` semantics** — confirmed: `build_share_envelope` writes `index` then `total` (`service.rs:746-747`), and confirmed that `parse_share_envelope` **does not read them back** (it reads only uuid `[6..22]`, threshold `[24]`, share `[25..]`, `service.rs:764-768`). Recorded as a real write-but-never-read asymmetry (§2.3), not a hedge.
- **`PlatformError` lacks `InsufficientShares`** — confirmed (`error.rs:12-50` lists nine variants, none of them `InsufficientShares`). The variant **must** be added, with a `From` arm to the *existing* frozen `ApiError::InsufficientShares` (`sv-types/src/lib.rs:161-164,199`). (§4c, §5 step 5.)
- **`derive_context` convention** — confirmed exactly `format!("secure-vault/platform/v1/{}", tag.trim_end_matches('\0'))` (`artifact.rs:135-137`); the hedge is removed and the convention extended (with header fields) in §4a.
- **`.svshare` filename scheme** — confirmed `{uuid}.share{index}.svshare` (`service.rs:591`); not load-bearing for the new module, which defines its own `{group_id_hex}.share{index}.svss` + `{group_id_hex}.payload.svss` scheme (§4d).
- **`docs/PLATFORM-AUDIT.md`** — **does not exist**; the draft's citations to it (`:122-146`, `:262-269`) are removed. No doc in `secure-vault/docs/` covers secret-sharing extraction; this plan is the source-grounded analysis of record.

**Corrections of substantive draft errors, all source-verified:**
1. The "domain separation provides header binding" claim was **false** — `derive_context` keys only on MAGIC (`artifact.rs:135-137`) and `secretbox` has no AAD (`secretbox.rs:4-5,20-27`); fixed by folding `(group_id,n,k)` into the payload-key derivation (§4a, R2).
2. The payload artifact is **not** "structurally identical to `artifact.rs`'s tail" — that tail is preceded by an Argon2/passphrase header; the DEK-keyed payload has none. Exact layout (MAGIC 6 + version 2 + aead_alg 1 + nonce 24 + ciphertext) and overhead (33 + 16 = 49) given (§4b).
3. **Share length is 92 bytes**, not 98 (6+2+16+1+1+1+32+33); the draft contradicted itself (§4b).
4. **Recover-side payload read needs `MAX_CIPHERTEXT_BYTES`** (`crypto.rs:16`), which the draft omitted (§4b, R5).
5. **Overwrite policy** (`refuse_existing` per file, up-front, orphan cleanup) was entirely omitted; now specified (§4c).
6. **`combine` ignores threshold and infers from share count**; >k valid shares still recover; **duplicate x-coordinates are an unguarded hazard** in both `sss` and the vault — now guarded in the new module (§4.5, R8).
7. **`getrandom` call site** clarified: use the Rust `getrandom::getrandom` API, not the `sv-sys-sss` C-ABI `randombytes` symbol (§4a).
8. **Nonce/ciphertext split on open** made explicit (`nonce = blob[9..33]`, `ciphertext = blob[33..]`), mirroring `artifact.rs:105-107` (§4b).
9. **MAGIC bytes shown** (`SVSSP\0`/`SVSSS\0`, 6-byte platform convention), distinct from the 4-byte `SVSH` (§4b).
10. **`group_id`/`payload_ref` mismatch oracle** resolved to `SV-INVALID-INPUT` (matching the vault's UUID-mismatch choice), keeping cryptographic failures merged in `SV-UNAUTHORIZED` (§4.4-oracle, R9).
11. The standalone commands belong on the **session-free `PlatformSurface`** (`platform.rs:18-64`), not the session-bound vault `CommandSurface` (§4d).

All `SVSS` field sizes are design proposals to review; everything cited `file:line` was verified by direct source read during this analysis.
