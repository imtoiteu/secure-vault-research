# Secure Vault — Pre-M5 Schema & Key-Hierarchy Freeze (H1–H6, V1, K1–K2)

**Status:** Decision review complete; **implemented** in M4 (key hierarchy — K1/K2/H2) and
M5 (`.svault` container — H1/H3/H4/H5/H6/V1). These nine items, left PROVISIONAL after M0.1
(see [`M0-CONTRACTS.md`](M0-CONTRACTS.md) §4–§5), are now resolved, frozen, and built. This
document remains the design authority; the code in `sv-core::{format, container, keys}` matches
it. One refinement landed during implementation: `ContentLayout` stores only `payload_len`
(the offset is derived from `HEADER_LEN`, avoiding a circular dependency).

**Method:** each decision lists options, then analyzes security, interoperability,
implementation complexity, and migration cost if changed after files exist, then
recommends. The grounding is the current source: `sv-crypto-traits` (frozen types),
`sv-core::format` / `sv-core::keys` (provisional schema), `sv-crypto::secretbox`
(no-AAD wrap). Evidence hierarchy and "verify before concluding" per `CLAUDE.md`.

---

## Cross-cutting primitives introduced here

Three new frozen constants/types the individual decisions build on:

- **`SUITE_VERSION: u8 = 1`** — the crypto-suite version (distinct from the container
  `FORMAT_VERSION` and from the IPC `CONTRACT_VERSION`). Single source of truth for the
  algorithm bundle and for every key-derivation context (K2).
- **`CipherSuite` (closed enum)** — names the whole algorithm bundle as one value
  (`CipherSuite::V1`), expanded by a compile-time table into the per-category `…Alg`
  ids that already exist in `sv-crypto-traits`. The header stores the suite **discriminant**,
  not five independently-selectable slots (H1).
- **Context grammar** `secure-vault/v<SUITE_VERSION>/<purpose>[/<qualifier>…]` — the
  domain-separation namespace for all `BLAKE3::derive_key` calls (K1).

> **Label namespace.** The decision IDs in this document — **H** (Header-schema), **V** (Version),
> **K** (Key-hierarchy) — are scoped to the schema/key freeze and are referenced by the same names in
> M7-HARDENING.md, M6-IPC-DECISIONS.md, and M0-CONTRACTS.md. They are a **separate namespace** from the
> **hardening-risk** series (H1–H14) in VALIDATION-PLAN.md / RELEASE-READINESS.md. In particular, this
> document's **H4 (provenance vs. integrity)** is unrelated to hardening **H4 (Windows `env_clear`)**.

---

## H1 — Ciphersuite block

**Current:** `VaultHeader` records only `kdf{algorithm: String, salt, params}`. The
file-cipher (age), wrap-AEAD (secretbox), signature (minisign), and hash (BLAKE3) are
**implicit** — fixed by `FORMAT_VERSION = 1`. The `KdfAlg/HashAlg/AeadAlg/FileCipherAlg/SigAlg`
enums exist as types but appear nowhere on disk.

**Options**
1. *Implicit suite keyed by `FORMAT_VERSION`.* No suite block; version N ⇒ fixed algorithms.
   A cipher swap is a whole-format version bump.
2. *Explicit, independently-selectable per-category slots.* Header carries five free fields
   `{kdf, wrap_aead, file_cipher, sig, hash}`, each a `…Alg`; reader checks each against
   what it supports.
3. *Closed `CipherSuite` enum, stored as one discriminant.* The suite expands to the five
   ids via a compile-time constant; the header stores `suite: CipherSuite`, never the slots.

**Security.** Option 2 reintroduces the classic *cryptographic-agility footgun*: independently
negotiable algorithm fields are the substrate for downgrade/confusion attacks (JWT `alg`,
TLS downgrade). Even though our header is integrity- and provenance-protected (BLAKE3 + signature),
the KDF parameters are consumed *before* unlock, so a self-describing-but-unconstrained suite
widens the pre-trust surface for nothing. Option 3 makes invalid algorithm combinations
**unrepresentable** — you cannot negotiate down what is not offered — while still being fully
self-describing. Option 1 is safe but opaque (tooling must infer crypto from a version number).

**Interoperability.** A stored, named suite lets an inspector (`svault inspect`) report the
exact crypto without a version lookup table. One discriminant is trivial to display and to
match against a supported set.

**Complexity.** Low: one `enum CipherSuite { V1 }` plus a `const fn expand(self) -> SuiteSpec`
returning the five ids. Reader gating is a single membership check.

**Migration cost if changed later.** If we ship M5 *without* a suite field, every v1 file is
"implicitly suite V1" and a future second suite needs special-case retrofitting of all existing
files. Adding the discriminant now (only `V1` exists) is nearly free and makes a future `V2`
purely additive. Cost rises sharply once real `.svault` files exist.

**Recommendation — Option 3.** Add `suite: CipherSuite` to `VaultHeader`, expanded by a
compile-time table to the existing `…Alg` ids. Readers gate on the *whole suite*
("do I support V1?"), not per-slot. This is self-describing **and** downgrade-proof. The suite
is the **single authority** for which algorithms a file uses — per-record algorithm tags (see H2)
are therefore unnecessary and are dropped.

---

## H2 — Wrapped-secret binding (transplant / field-confusion resistance)

**Current:** `WrappedSecret{nonce, ciphertext}` sealed with libsodium `crypto_secretbox`
(XSalsa20-Poly1305), **no associated data** (secretbox supports none). Two wrapped secrets
exist: the age identity (under KEK) and the signing key (under SWK). Field confusion is already
prevented by KEK ≠ SWK domain separation; cross-vault *transplant* of the same field is prevented
only because each vault has a random salt ⇒ a distinct KEK/SWK. Transplant therefore requires a
passphrase **and** salt collision — improbable, but not prevented by construction.

**Options**
1. *Keep secretbox, no binding.* Rely on per-vault random salt for transplant resistance.
2. *Switch wrap-AEAD to an AAD-capable AEAD* (e.g. `crypto_aead_xchacha20poly1305_ietf`, also
   24-byte nonce) and bind `AAD = vault_uuid ‖ field_label ‖ suite_version`.
3. *Bind in the derivation context.* Keep secretbox, but derive a **per-field, vault-bound**
   wrapping key: `derive_key("secure-vault/v1/wrap/<field>:<uuid_hex>", MK) → wrap_key`. The
   wrong context derives the wrong key ⇒ the MAC fails. Transplant, field confusion, and
   cross-suite reuse all become impossible because the *key itself* is unique per
   (vault, field, suite).

**Security.** Options 2 and 3 both achieve full binding. Option 3 reaches it **without adding a
new AEAD primitive** — it keeps the audited, nonce-misuse-resistant secretbox and removes no
property. It also unifies the binding with the K1/K2 namespace work we must do anyway. Option 2
introduces a second AEAD (new FFI surface, new nonce-management code) for an equivalent result —
contrary to the project's conservative "minimize unsafe surface" posture. Option 1 leaves the
narrow salt-collision gap.

**Interoperability.** Option 3 changes no on-the-wire AEAD; `WrappedSecret` stays
`{nonce, ciphertext}`. Option 2 would change the wrap algorithm id (still 24-byte nonce, so
framing is unaffected, but it is a suite change).

**Complexity.** Option 3 is a key-derivation change only (folds into M4's context work). Option 2
needs a new sodium binding plus AAD reconstruction that the writer and reader must compute
byte-identically.

**Migration cost if changed later.** Whatever binding we choose is baked into how every secret is
sealed. Changing it post-M5 means unwrap-with-old / re-wrap-with-new for every vault — the same
machinery as a passphrase change, but touching every file. Choose now.

**Recommendation — Option 3.** Bind via the derivation context: each wrapped field uses its own
key `derive_key("secure-vault/v<SUITE_VERSION>/wrap/<field>:<uuid_hex>", MK)`. `<field>` ∈
{`age-identity`, `signing-key`}. `WrappedSecret` keeps `{nonce, ciphertext}` only and carries
**no** per-record algorithm id — the suite (H1) is the single authority. This supersedes the
"add an AEAD id to `WrappedSecret`" sketch from the M0.1 plan: the binding goal is met by the key,
not by a stored tag, and avoids a tag-vs-suite confusion check. (If a future suite genuinely needs
mixed AEADs, that is a `CipherSuite::V2` decision.)

---

## H3 — Item model (the A1 contradiction)

**Current contradiction:** `VaultHeader.items: Vec<ItemEntry>` with per-item `enc_offset/enc_len`
into a payload region, *and* a single `content_layout{payload_offset, payload_len}`. But age
produces one self-framed AEAD stream per `encrypt` call — so "per-item ciphertext offsets" and
"one payload blob" cannot both be literally true. Two coherent readings exist, and a third axis
(where the item directory lives) determines metadata leakage.

**Options**
1. *Single-stream, directory in cleartext header.* One age blob over all items concatenated;
   `ItemEntry` records plaintext offsets; header still lists names/sizes/count in the clear.
2. *Per-item independent age blobs.* Each item is its own age ciphertext; `enc_offset/enc_len`
   locate each blob. Enables slice-and-decrypt of one item.
3. *Single-stream, directory inside the ciphertext.* One age blob whose plaintext is
   `[item directory ‖ item bytes]`; the header carries **no** plaintext item metadata.

**Security (metadata).** This is the decisive axis for a *secure* vault. Option 2 leaks per-item
ciphertext sizes (≈ plaintext + ~200 B age overhead) **and** exact item count. Option 1 leaks the
same (names/sizes/count sit in the cleartext header). Option 3 leaks only the single total
ciphertext length — names, sizes, and count are all encrypted. Content confidentiality is equal
across all three (age AEAD); the difference is entirely metadata exposure, where **Option 3 is
strictly strongest.**

**Interoperability.** age is a streaming, non-seekable format. Only Option 2 offers true partial
extraction without decrypting everything. But the container is **re-hashed and re-signed on every
save** (A2/A3) — so even Option 2 must rewrite + re-sign the whole file on any add/remove, which
negates most of its "partial update" advantage. Partial *read* of one item remains Option 2's only
real edge, and matters only for very large vaults.

**Complexity.** Option 3 = define one simple inner directory (a CBOR
`Vec<ItemEntry>` length-prefixed ahead of the concatenated item bytes) and encrypt once → one
subprocess spawn. Option 2 = N age spawns (our hardened spawn is heavyweight), N temp-identity
passes on decrypt, and offset bookkeeping. Option 3 is both simpler and cheaper per operation.

**Migration cost if changed later.** Highest-stakes layout decision: it fixes the payload bytes,
the meaning of `ItemEntry`, and the entire encrypt/decrypt flow for M5+M6. Changing it post-M5 is a
major `FORMAT_VERSION` bump with a full re-encrypt migration. Must freeze now.

**Recommendation — Option 3 (single-stream, encrypted directory).** The payload is **one** age blob
whose plaintext is a CBOR item directory followed by the concatenated item plaintexts.
`VaultHeader` **drops `items: Vec<ItemEntry>`**; the directory lives inside the ciphertext.
`ItemEntry` becomes `{item_id, name, plaintext_offset, plaintext_len, plaintext_blake3, added_unix}`
(offsets are *plaintext* positions inside the decrypted archive; `enc_offset/enc_len` are removed).
`content_layout` keeps locating the single age blob. `ItemInfo` DTOs are produced **after unlock**
from the decrypted directory.

**Accepted trade-off (the one product-reversible point in this review):** a locked vault exposes
*nothing* about its items — not even the count — and reading any item decrypts the whole payload.
For an offline secure vault this is the correct, stronger default (and matches how serious password
managers behave). If the product later *requires* listing items while locked, that is a deliberate
confidentiality downgrade to Option 1 and a `FORMAT_VERSION` bump — not a silent change.

---

## H4 — Provenance vs. integrity (what the signature means)

**Current:** the SIG_TRAILER is a minisign Ed25519 signature over the file hash, made with a signing
key that is **itself wrapped inside the same header**. The verification public key is also in the
header. This is a **self-signed** construction: it proves the file is internally consistent and
tamper-evident *after creation*, but it does **not** authenticate the author to a third party —
anyone who unlocks can re-sign, and a freshly forged vault carries its own valid self-signature.

**Options**
1. *Self-signed only (status quo).* Integrity + tamper-evidence; no external authenticity.
2. *External pinned anchor.* Verification requires an out-of-band minisign public key; the trailer
   must verify under *that* key → real provenance, at the cost of key distribution/management.
3. *Both, by mode, with honest reporting.* Always self-sign (cheap, always-on integrity);
   additionally support verify-against-a-pinned-key; report the two outcomes as **distinct**
   states, never conflated.

**Security.** The real risk is **overclaiming**: a UI that renders a green "signature valid ✓" for a
self-signed vault implies an authenticity it does not possess. The honest semantics: the in-header
signature = *integrity + "same signer across saves of this vault"*, **not** sender authentication.
Third-party provenance requires a key pinned out-of-band.

**Interoperability.** minisign signatures are independently checkable with the stock `minisign -V`
given the public key and trusted comment — good for transparency and for an external-anchor workflow
(distribute the pubkey, verify out-of-band).

**Complexity.** Option 3's *documented semantics + an optional verify parameter* is small. A real
trust store / PKI (Option 2 built out) is large and is **not** in scope now.

**Migration cost if changed later.** The *semantic* and the verify parameter cost nothing to add
later. The only format coupling is *what bytes the signature covers*, which H5 settles. So H4 imposes
**no on-disk freeze** beyond keeping `signing_public_key` in the header (already present).

**Recommendation — Option 3, documented now, enforcement deferred.** Keep the always-on
self-signature (integrity #5). Define `verify` / `IntegrityReport` to **distinguish**
"integrity verified (self-signed)" from "provenance verified (matched pinned external key)," and
never label self-signed as authentic origin. Make the model *anchor-ready* (the pubkey is already in
the header; `verify` gains an optional `expected_pubkey: Option<&Ed25519PublicKey>` — when `Some`, it
must equal the in-header key *and* the signature must verify; when `None`, integrity-only). Do **not**
build the external trust store in M5. Record the integrity-vs-provenance distinction in the threat
model. **Not an M4 or M5 byte-layout blocker.**

---

## H5 — Per-section digests & signature coverage

**Current:** one BLAKE3 over `MAGIC ‖ FORMAT_VERSION ‖ HEADER_LEN ‖ HEADER ‖ PAYLOAD`, then the
signature is over that single hash. Consequence: you cannot authenticate the header (and therefore
trust its KDF params / suite / wrapped-key ciphertexts) without reading the **entire** payload first.

**Options**
1. *Single whole-file digest (status quo).* One hash, one signature. Simple; no independent header
   verification; cannot localize which section changed.
2. *Two section digests, bound under one signature.* Compute `header_digest = BLAKE3(MAGIC ‖
   VERSION ‖ HEADER_LEN ‖ HEADER)` and `payload_digest = BLAKE3(PAYLOAD)`; sign a **binding root**
   `BLAKE3(header_digest ‖ payload_digest)`. The header can be verified independently of the
   (possibly large) payload, and the two sections are cryptographically bound so they cannot be
   mixed across files.
3. *Merkle / per-item tree.* Localized per-item integrity. Overkill for this product.

**Security.** Section digests let you **verify-then-trust the header** before acting on its KDF
params — a meaningful ordering improvement. The mandatory safeguard: the signature must cover a value
that binds *both* digests together (sign over `header_digest ‖ payload_digest`), or an attacker could
splice a valid header from file A onto a valid payload from file B. Per-*item* integrity is already
served by `plaintext_blake3` in the (now encrypted) directory, checked post-decrypt — no tree needed.

**Interoperability / complexity.** Two BLAKE3 calls plus a 64-byte concatenation; trivial. The signed
message changes from `BLAKE3(wholefile)` to `BLAKE3(header_digest ‖ payload_digest)`.

**Migration cost if changed later.** Hash/sign coverage is core format; changing it is a
`FORMAT_VERSION` break. Freeze now.

**Recommendation — Option 2.** Sign the binding root `BLAKE3(header_digest ‖ payload_digest)`. The
two section digests are **recomputed on read, not stored** (storing them would be redundant and invite
stored-vs-recomputed confusion); the only trailer payload remains the signature. Expose a
verify-header-only entry point that recomputes `header_digest` and checks it against the signed root
together with `payload_digest`. This keeps a single signature while enabling cheap, independent header
authentication and cross-file splice resistance.

---

## H6 — Header hygiene (typing & evolution)

**Current:** `KdfRecord.algorithm: String` (`"argon2id"`) — stringly-typed and redundant with
`KdfParams::alg()`. No typed evolution mechanism.

**Options**
1. *Status quo free-form string.* Allows typos / unknown values to parse; redundant.
2. *Enum-ize and drop the redundancy.* `KdfRecord` becomes `{salt, params}`; the algorithm is the
   `KdfParams` tag. No free-form strings anywhere in the security header.
3. *Enum + untyped extension map* (`BTreeMap<String, Value>`) for additive forward-compat.

**Security.** A stringly-typed algorithm is a minor footgun (whitespace, unknown values silently
accepted). An **untyped extension map in a security header is an anti-pattern**: unknown fields must
never influence crypto decisions, and because the header is **signed and re-signed on every save**,
forward-compat preservation of unknown fields is moot — an older reader cannot meaningfully edit and
re-sign a newer vault anyway (it would drop fields and break the signature). The extension map adds
attack surface for no real benefit in a signed, version-gated format.

**Interoperability / complexity.** Option 2 is the simplest and removes a redundant field. Evolution
is handled by the version axes (V1) plus typed additive fields gated on version — not by untyped bags.

**Migration cost if changed later.** Dropping the redundant string and enum-gating is a pre-M5
freeze; trivial now, a format change after files exist.

**Recommendation — Option 2.** Remove `KdfRecord.algorithm: String`; `KdfRecord = {salt, params}`,
with the algorithm carried by the `KdfParams` tag and cross-checked against the suite (H1). Use
**`#[serde(deny_unknown_fields)]`** on `VaultHeader` and its sub-structs so a malformed/extended header
is *rejected*, not silently accepted (defense-in-depth atop the signature). Evolve additively via the
V1 minor-version mechanism with typed fields — **no untyped extension map.**

---

## V1 — Version semantics

**Current:** `FORMAT_VERSION: u16 = 1` (on-disk), `CONTRACT_VERSION: u32 = 1` (IPC). No major/minor
split, no separate crypto-suite version; readers "reject unknown values."

**Options**
1. *Single monotonic `FORMAT_VERSION`.* Any change is a new number; coarse — cannot distinguish a
   safe additive change from a breaking one.
2. *Major.minor split on `FORMAT_VERSION`.* Semver-for-formats with forward-compatible minor parsing.
3. *Three independent axes:* container-structure version, crypto-suite version, and IPC contract
   version — decoupling "framing changed" from "algorithms changed" from "IPC changed."

**Security.** The properties that matter are **no silent downgrade** and **no ambiguous parse**. For a
security format the safest reader rule is *reject anything not fully recognized* — i.e. **no
best-effort parsing of an unknown newer minor** (Option 2's forward-compat parsing is a liability
here). Decoupling the suite from the structure version (with K2 binding the KDF contexts to the suite)
prevents "same version number, different crypto."

**Interoperability / complexity.** Three small declared values; the reader opens a file iff it supports
both the file's `FORMAT_VERSION` and its `CipherSuite`. This also sets up a clean E1 (pre-M6) split
later: "unsupported version" vs "unsupported suite" vs "corrupted" become distinguishable.

**Migration cost if changed later.** Declaring the axes now is free; retrofitting a suite axis after
files exist with an *implicit* suite is painful. Freeze now.

**Recommendation — Option 3 (three explicit axes), strict gating.**
- **`FORMAT_VERSION` (u16)** = container/structure version (framing: magic, field layout,
  digest/signature scheme). Reader accepts only versions in its **known set**; **no forward-compatible
  minor parsing** in v1. The major/minor *meaning* is documented for human planning, but the code
  checks membership, not ordering.
- **`CipherSuite` / `SUITE_VERSION`** = crypto-suite version, independent of structure; readers gate on
  it separately; it is the anchor for the K2 context binding.
- **`CONTRACT_VERSION` (IPC)** = fully independent; tracks the Tauri command/DTO surface. A file-format
  change need not bump IPC, and vice-versa.

A vault file declares `(FORMAT_VERSION, CipherSuite)`; the app declares
`(supported FORMAT_VERSIONs, supported CipherSuites, CONTRACT_VERSION)`. **Open iff both the version
and the suite are supported.**

---

## K1 — Key-derivation context namespacing

**Current:** `CTX_KEK = "secure-vault v1 kek"`, `CTX_SWK = "secure-vault v1 sign-wrap"` — ad-hoc strings
with an embedded, unmanaged `v1`.

**Options**
1. *Status quo ad-hoc strings.*
2. *Structured, reserved grammar* `secure-vault/v<SUITE_VERSION>/<purpose>[/<qualifier>…]`, with
   `…/plugin/<id>/<purpose>` reserved for future modules.

**Security.** BLAKE3 `derive_key` domain separation is only as strong as context **uniqueness**. A
structured, reserved grammar prevents accidental collisions (`sign-wrap` vs `signwrap`, or a future
plugin overlapping a core context) and embeds the suite version so a suite change *automatically*
re-keys everything (no cross-suite key reuse). This grammar is also where H2's per-field, vault-bound
wrap keys live.

**Interoperability / complexity.** Pure naming; trivial to implement. Reserving the plugin sub-namespace
now costs nothing and prevents a future collision.

**Migration cost if changed later.** Context strings are **baked into every vault's key derivation**.
Changing one after files exist re-keys the KEK/SWK/wrap keys → an unwrap/re-wrap migration of every
vault. Because **M4 hardcodes these strings**, settling K1 *before* M4 is mandatory — otherwise the
first vaults are bound to the ad-hoc strings forever.

**Recommendation — Option 2.** Adopt the grammar now and reserve the namespace, even though M4 only
needs the two wrap contexts:
- Wrap (per-field, vault-bound — H2): `secure-vault/v1/wrap/age-identity:<uuid_hex>` and
  `secure-vault/v1/wrap/signing-key:<uuid_hex>`. The **template** (everything before `:<uuid_hex>`) is a
  frozen constant; the `uuid_hex` suffix is the runtime binding.
- Reserved for the future: `secure-vault/v1/plugin/<id>/<purpose>`.

This **replaces** the current `CTX_KEK`/`CTX_SWK` strings. The KEK/SWK two-step (MK→KEK→wrap,
MK→SWK→wrap) collapses to **one wrap key per field derived directly from MK** with the field+uuid
context — KEK is the age-identity wrap key, SWK is the signing-key wrap key, now uuid-bound. The
`KeyHierarchy` trait (PROVISIONAL per `M0-CONTRACTS.md` §5) evolves from `derive_kek/derive_swk` to a
single `derive_wrap_key(master: &Key32, field: WrapField, vault_uuid: &[u8;16]) -> Key32`.

---

## K2 — Context ↔ suite-version binding

**Current:** the `v1` token is embedded ad-hoc in two string literals; nothing ties it to a single
constant or documents how a change migrates existing vaults.

**Options**
1. *Status quo (literal `v1` per string).*
2. *Single `SUITE_VERSION` constant drives the version token in all contexts*, with a frozen-string
   test and a documented unwrap/re-wrap migration for any change.

**Security.** Binding the context version to the suite prevents cross-suite key reuse: a v2 KEK and a
v1 KEK for the same passphrase+salt are different keys, so there is no confused-deputy across suites.
Freezing the exact strings in a test makes an accidental edit (which would brick existing vaults) fail
CI — extending the existing `derivation_contexts_are_distinct_and_stable` guard.

**Interoperability / complexity.** A constant plus a compile-time/test assertion; trivial.

**Migration cost if changed later.** Any context or suite change re-keys all wrap keys. The **only**
sanctioned change path is read-old / write-new: detect a file whose `CipherSuite` is older than current,
**unwrap with the old suite's keys and re-wrap with the new** (the same machinery as a passphrase
change, triggered by a suite upgrade). Settling this before M4 is mandatory because M4 implements the
derivation.

**Recommendation — Option 2.** Introduce `const SUITE_VERSION: u8 = 1`. Build every context's version
token from it (the wrap-context templates embed `v1` and a test asserts each template starts with
`secure-vault/v{SUITE_VERSION}/`, so a suite bump forces a deliberate context review). Document the
unwrap/re-wrap suite-migration as the sole way to change a context or suite. Freeze the exact context
templates in a CI test.

---

## Final deliverables

### 1. Final recommended schema direction

- **Suite block (H1):** add `suite: CipherSuite` (closed enum, only `V1`) to `VaultHeader`, expanded
  by a compile-time table to the existing `…Alg` ids. The suite is the **single authority** for
  algorithm identity; no per-record alg tags.
- **Wrapped secrets (H2):** `WrappedSecret = {nonce, ciphertext}` (secretbox, unchanged). Transplant /
  field-confusion / cross-suite resistance comes from **per-field, vault-bound wrap-key derivation**,
  not from AAD or stored tags.
- **Item model (H3):** **single-stream payload** — one age blob over a CBOR item directory followed by
  concatenated item plaintexts. `VaultHeader` **drops `items`** (the directory is encrypted);
  `ItemEntry` uses **plaintext** offsets; `content_layout` locates the single blob. Locked vaults
  reveal no item metadata (the one product-reversible trade-off, flagged).
- **Provenance (H4):** keep the always-on self-signature as **integrity**; report
  integrity-vs-provenance distinctly; add an optional `expected_pubkey` to `verify`; defer any external
  trust store. No byte-layout change beyond the already-present `signing_public_key`.
- **Digests & signature coverage (H5):** sign the binding root `BLAKE3(header_digest ‖ payload_digest)`;
  section digests are recomputed on read (not stored); expose verify-header-independently.
- **Header hygiene (H6):** drop `KdfRecord.algorithm: String` (`KdfRecord = {salt, params}`);
  `#[serde(deny_unknown_fields)]` on the header; evolve via typed additive fields, **no untyped
  extension map**.

Resulting `VaultHeader` (M5 target): `{format_version, suite, vault_uuid[16], created_unix,
modified_unix, kdf{salt, params}, wrapped_age_identity, wrapped_signing_key, signing_public_key[32],
share_policy?, content_layout, payload presence implied}` — **no `items` directory in the clear**.
File layout unchanged in framing (`MAGIC ‖ FORMAT_VERSION ‖ HEADER_LEN ‖ HEADER ‖ PAYLOAD ‖ SIG_TRAILER`);
the signed message changes to the binding root (H5).

### 2. Final key-derivation namespace strategy

Grammar: `secure-vault/v<SUITE_VERSION>/<purpose>[/<qualifier>…]`, `SUITE_VERSION = 1`.

| Purpose | Context | Notes |
|---|---|---|
| Wrap age identity | `secure-vault/v1/wrap/age-identity:<uuid_hex>` | template frozen; `uuid_hex` = per-vault binding (H2) |
| Wrap signing key | `secure-vault/v1/wrap/signing-key:<uuid_hex>` | template frozen; `uuid_hex` binding |
| Future modules (reserved) | `secure-vault/v1/plugin/<id>/<purpose>` | reserved now; unused in Phase 1 |

`MK = Argon2id(passphrase, salt, params)`. Each wrap key is derived **directly from MK** with its
field+uuid context (the old KEK/SWK intermediate names collapse into per-field wrap keys). `KeyHierarchy`
becomes `derive_master(...) -> Key32` and `derive_wrap_key(master, field, vault_uuid) -> Key32`. Context
templates are frozen by a CI test asserting the `secure-vault/v{SUITE_VERSION}/` prefix.

### 3. Final versioning strategy

Three independent axes, strict gating:
- **`FORMAT_VERSION: u16`** — container structure; known-set membership only, **no forward-minor
  parsing**.
- **`SUITE_VERSION: u8` / `CipherSuite`** — crypto bundle; gated separately; anchors the K2 context
  binding.
- **`CONTRACT_VERSION: u32`** — IPC/DTO surface; fully independent of the file format.

A file declares `(FORMAT_VERSION, CipherSuite)`; the app opens it iff it supports both. Suite/context
changes migrate by unwrap-old / re-wrap-new.

### 4. Remaining blockers

**M4 (key hierarchy) — must be frozen before implementation (all resolved above):**
- **K1** context grammar + reserved namespace — M4 hardcodes the contexts. ✅ resolved.
- **K2** `SUITE_VERSION` constant + frozen-template test + migration doc. ✅ resolved.
- **H2 binding mechanism** (per-field, vault-bound wrap-key derivation) — it *defines* the M4
  derivation API (`derive_wrap_key(master, field, vault_uuid)`). ✅ resolved.
- **`SUITE_VERSION = 1`** constant (from H1/V1) feeding the contexts. ✅ resolved.

→ **No remaining M4 blockers.** M4 may proceed against: `Argon2Kdf` (MK), `Blake3Hasher`
(`KeyDerivation` for wrap keys), `secretbox::seal/open` (wrap/unwrap), with the new `KeyHierarchy`
shape and the v1 contexts above.

**M5 (`.svault` container) — must be frozen before serialization (all resolved above):**
- **H1** suite field, **H3** single-stream payload + encrypted directory + reshaped `ItemEntry` +
  dropped `items`, **H4** verify semantics + optional `expected_pubkey`, **H5** binding-root signature
  + independent header verification, **H6** `KdfRecord` reshape + `deny_unknown_fields`, **V1** the
  three version axes in the header. ✅ all resolved.

→ **No remaining M5 schema blockers.** Residual M5 *implementation* items (not schema): atomic
write/rename, age-stream framing inside the single blob, and Argon2 parameter recalibration (A4, due
M7). The minisign-CLI byte-level interop CI gate (carried from M3) remains open but does not block M4/M5.

**Out of scope here (still gated):** E1–E3, N1 (pre-M6 IPC), and the M7 hardening set
(mlock, constant-time review, fuzzing, age streaming/timeout). The external trust store (H4 Option 2)
is a post-Phase-1 product decision.
