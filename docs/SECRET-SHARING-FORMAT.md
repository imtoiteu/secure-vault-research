# Standalone Secret Sharing — Artifact Formats & Threat Model (as built)

**Status:** **Implemented** in `sv-platform` (engine only — no IPC/UI yet). Gate-passing
(`fmt`/`clippy -D warnings`/`build --locked`/`test`/`deny` green). This document is the
authoritative description of the **as-built** on-disk formats and the threat model they enforce.
It supersedes the "design proposals to review" framing in
[SECRET-SHARING-SCOPE.md](SECRET-SHARING-SCOPE.md) §4.4; the engine matches that design exactly.

Source of truth: [`crates/sv-platform/src/sharing.rs`](../crates/sv-platform/src/sharing.rs).
Construction rationale and the secretbox-vs-age decision: the scope doc; the source-grounded
audit: [SECRET-SHARING-AUDIT.md](SECRET-SHARING-AUDIT.md).

---

## 1. What the module does

Splits an arbitrary-size secret (typed text **or** a file) into `n` pieces such that any `k`
reconstruct it, and below `k` reveal nothing. **Vault-free**: it shares no code path, format, or
identity with Secure Vault's UUID-bound `SVSH`/`keys_*` flow, which is untouched.

The scheme is **hybrid**: a fresh random 32-byte **DEK** is Shamir-split (the DEK is the only value
that must be 32 bytes); the payload is encrypted under a key **derived from the DEK and the piece
header** using libsodium `secretbox` (XSalsa20-Poly1305). Packaging is **uniform** — one payload
file + `n` piece files, for both text and file inputs. A piece is also offered as a copy-paste
Base64 string.

---

## 2. On-disk formats

Both artifacts follow the platform convention: a 6-byte `MAGIC`, a little-endian `u16`
`format_version`, a fixed header, and pre-authentication structural bounds. The MAGICs are
distinct from each other, from the vault's 4-byte `SVSH`, and from `SVENC\0`/`SVKEY\0`, so files
are never confused and recovery auto-detects type by MAGIC.

`format_version = 1` for both. Evolution is additive-only (new optional trailing fields); an
unknown version is reported as `IncompatibleVersion { found, supported }` (a distinct, actionable
error — not a generic parse failure).

### 2.1 Piece file — `SVSSS\0`, fixed **92 bytes**

```text
off  len  field            notes
0    6    MAGIC = b"SVSSS\0"
6    2    format_version    u16 LE (= 1)
8    16   group_id          fresh random per split; binds the cohort (replaces the vault UUID)
24   1    total (n)         1..=255
25   1    threshold (k)     1 <= k <= n
26   1    share_index       advisory only; the real x-coordinate is byte 0 of key_share
27   32   payload_ref       BLAKE3 of the WHOLE payload file (binds piece -> payload)
59   33   key_share         [u8; KEYSHARE_LEN]; byte 0 = x-coordinate, bytes 1..33 = GF(2^8) y
```

Length is asserted at compile time (`SHARE_LEN == 92`) and offsets are cross-checked
(`S_KEYSHARE + KEYSHARE_LEN == SHARE_LEN`, `S_PAYLOAD_REF + 32 == S_KEYSHARE`). `KEYSHARE_LEN`
(33) is the canonical constant from `sv-crypto-traits`, asserted against the vendored C header in
`sv-sys-sss`.

Filename: `{group_id_hex}.share{i}.svss` (`i` = 1-based).

### 2.2 Payload file — `SVSSP\0`

```text
off  len  field            notes
0    6    MAGIC = b"SVSSP\0"
6    2    format_version    u16 LE (= 1)
8    1    aead_alg = 0      XSalsa20-Poly1305 secretbox
9    24   nonce             secretbox nonce (random per split)
33   ..   ciphertext        secretbox output; INCLUDES the 16-byte Poly1305 tag
```

Header overhead = 33 bytes; total expansion over plaintext = `33 + 16` (tag) = **49 bytes**. On
recover, `nonce = blob[9..33]` and `ciphertext = blob[33..]` (no length prefix; "the rest is
ciphertext"). Filename: `{group_id_hex}.payload.svss`.

### 2.3 Copy-paste piece string

The exact 92 piece bytes in standard RFC 4648 Base64 (padded). Decoding ignores ASCII whitespace
(so wrapped/spaced transcriptions paste cleanly) and is otherwise strict (rejects bad length, bad
alphabet, and misplaced padding). A decoded string is validated by the **same** `parse_share` path
as a piece file — it is the same artifact in a transcribable encoding, not a second format.

### 2.4 Payload-key derivation (the header binding)

```text
payload_key = BLAKE3::derive_key(
    context = "secure-vault/platform/v1/SVSS|" + hex(group_id) + "|" + n + "|" + k,
    ikm     = DEK
)
```

Because `(group_id, n, k)` are folded into the derivation context, any tamper of those header
bytes changes `payload_key`, so `secretbox::open` fails. This achieves header authentication
without an AAD-capable cipher (`secretbox` exposes no associated data). The per-piece
`share_index`/x-coordinate is deliberately **not** in the context (it differs per piece while the
payload key must be identical across pieces); its integrity is covered by reconstruction itself (a
wrong x yields a wrong DEK → wrong key → open fails).

---

## 3. Reconstruction pipeline (recover)

Order matters: every **non-secret** check runs *before* any reconstruction, and the AEAD open is
the final, authoritative gate.

1. **Parse** each piece (fixed 92-byte length, MAGIC, version, `1<=k<=n`) and the payload (MAGIC,
   version, `aead_alg`). Structural failures → `Malformed` / `IncompatibleVersion`.
2. **Agreement** — all pieces must share `group_id`, `n`, `k`, `payload_ref`; otherwise
   `InvalidInput("these pieces are from different splits")`.
3. **Duplicate x-coordinate** — any repeated x (byte 0 of a key share) →
   `InvalidInput("the same piece was supplied more than once")`. This is the duplicate-share fix
   (§4).
4. **Non-zero x** — any x = 0 → `Malformed` (a genuine `sss` share never uses x = 0).
5. **Count** — distinct pieces `< k` → `InsufficientShares { got, need }` (non-secret count).
6. **Payload binding** — BLAKE3 of the supplied payload must equal the pieces' `payload_ref`;
   otherwise `InvalidInput("the payload file does not match these pieces")`.
7. **Reconstruct + authenticate** — `combine` the DEK, re-derive the header-bound `payload_key`,
   `secretbox::open`. Any cryptographic failure → `AuthFailed` (oracle-safe).

---

## 4. Security properties (achieved)

- **Information-theoretic below threshold (for the DEK).** The DEK is split by the same `sss`
  primitive proven to reveal nothing below `k`. The payload is encrypted *only* under a key derived
  from the DEK, so `< k` pieces ⇒ no DEK ⇒ no payload key ⇒ no plaintext.
- **Authenticated payload with a bound header.** `secretbox`'s Poly1305 tag authenticates the
  ciphertext; the derived-key context binds `(group_id, n, k)`. A wrong reconstructed DEK or any
  header tamper fails the open.
- **Fresh randomness from the OS CSPRNG.** DEK, `group_id`, and the secretbox nonce each come from
  `getrandom`/libsodium; `sss` polynomial coefficients from the crate's `randombytes`→`getrandom`
  export. A fresh DEK per split (never derived from inputs) keeps splits independent.
- **Zeroization.** The DEK and derived payload key are zeroizing `Key32`; pieces are zeroizing
  `KeyShare`; the file-read buffers for the secret/pieces and the recovered plaintext are zeroized
  after use; piece blobs are zeroized after writing/encoding.
- **No secret in a result type.** `ShareSplitOutput`/`RecoverOutput` carry only paths, counts, the
  group-id hex, and the (intentionally public) copy-paste piece strings — never the DEK or the
  recovered plaintext.
- **Oracle-safe errors.** Counts and "wrong files" are distinct, actionable, non-secret
  (`InsufficientShares`, `InvalidInput`, `Malformed`); every *cryptographic* failure is merged into
  the single `AuthFailed` → `SV-UNAUTHORIZED`.
- **Data-safety.** Outputs never overwrite: split refuses if the payload or any piece path exists
  (checked up front) and cleans up siblings on a mid-write failure; recover refuses to overwrite
  its output path.
- **DoS bounds.** The secret/file is capped at 2 GiB (`MAX_PLAINTEXT_BYTES`); the recover-side
  payload read is capped at `MAX_CIPHERTEXT_BYTES`; each piece file read is capped at 1 KiB; piece
  length is a fixed 92 bytes; no passphrase/Argon2 is involved, so there is no KDF cost surface.

---

## 5. Threat model

### 5.1 Assets
The split secret (text or file). Below the threshold it must remain information-theoretically
hidden; at/above the threshold, only a holder of `k` genuine pieces **and** the payload file can
recover it.

### 5.2 What an attacker can do, and what happens

| Capability | Outcome |
|---|---|
| Holds `< k` pieces (even all but one) | Learns nothing about the secret (information-theoretic for the DEK; payload key unknowable). |
| Holds the payload file only | Learns nothing — it is ciphertext under a key that requires `k` pieces to derive. |
| Tampers with `payload_ref`/`group_id`/`n`/`k` in **one** piece | Rejected pre-crypto by the agreement check → `InvalidInput` (the odd piece disagrees). |
| Tampers consistently across **all** pieces (e.g. flips `k`) | Reconstruction yields a wrong key; `secretbox::open` fails → `AuthFailed`. (Header binding, R2.) |
| Tampers with the payload ciphertext/nonce | `payload_ref` mismatch (non-secret) → `InvalidInput`; and the Poly1305 tag would fail regardless. |
| Supplies the same piece twice to fake meeting the threshold | Rejected by the duplicate-x check → `InvalidInput`, before any reconstruction. |
| Mixes pieces from two different splits | `group_id`/`payload_ref` disagree → `InvalidInput`; a same-`group_id` collision is a 1-in-2^128 event. |
| Feeds an oversized/garbage "piece" or payload file | Bounded by the read caps and fixed-length parse → `TooLarge`/`Malformed`, cheaply. |
| Probes error responses as an oracle | Cryptographic outcomes are merged into a single `AuthFailed`; only non-secret facts (count, wrong-files, structure) are distinguishable. |

### 5.3 Residual risks / non-goals (v1)
- **`group_id`/`payload_ref` are bindings, not MACs.** An attacker who controls *both* all pieces
  and the payload can fabricate a self-consistent (wrong) bundle; it still fails the AEAD open. They
  are cheap pre-auth integrity gates, never treated as authentication. Documented as such in code.
- **Pieces are confidential by possession.** A piece on disk or as a Base64 string is secret
  material (a threshold of them reconstructs the secret). The module zeroizes in-memory copies, but
  **distribution and storage of pieces is the user's responsibility** — the tool does not encrypt
  pieces at rest (that would reintroduce a passphrase and change the k-of-n model).
- **Uniform packaging keeps a separate payload file.** A holder needs their piece **and** the
  payload file; the payload is non-secret ciphertext (replicate it freely) but must not be lost.
- **No streaming; 2 GiB ceiling.** `secretbox` is one-shot/in-memory. Larger inputs are refused
  rather than risking OOM. A future streaming variant (age STREAM) would require reworking
  `sv-age`'s buffered subprocess wrapper first; out of scope for v1.
- **Not yet exposed.** No IPC command or UI surface exists yet, so the capability is reachable only
  from Rust. (See the implementation audit's "remaining work".)
- **Inherited primitive caveats.** GF(2⁸) `sss` has no integrity at the share layer by design;
  authentication is supplied one layer up by the AEAD here, exactly as the vault does with its age
  identity. The 2 GiB cap and the no-AAD secretbox are properties of the chosen primitives.

---

## 6. Out of scope / unchanged

Secure Vault, the `SVSH` UUID-bound share format, `build/parse_share_envelope`,
`keys_split`/`keys_recover`, `ShareExportInfo`/`SharePolicy`, the vault master key / session
lifecycle, and `CONTRACT_VERSION` are **untouched**. The only shared assets are the vetted
primitives (`SssSharer`/`sss`, `secretbox`, `getrandom`, `Blake3Hasher`, `Key32`/`KeyShare`) and the
`sv-platform` framing helpers — all consumed, none modified.
