# Standalone Secret Sharing — Product Scope (pre-implementation)

**Status:** Scope clarification. **No code.** Companion to [SECRET-SHARING-AUDIT.md](SECRET-SHARING-AUDIT.md) (the source-grounded technical audit); this doc decides *what to build* before the audit's "ships-first" slice is implemented.
**Evidence discipline:** Every load-bearing API claim is cited `file:line`, verified by direct source read. Design choices are labelled *recommendation*; nothing is presented as implemented.

---

## 1. User-facing workflows

**Recommendation: support both — "Split a secret" (text) and "Split a file" — as two task screens over one shared engine.**

Secret Sharing has two distinct real-world jobs, and they want different ergonomics:

| Workflow | Typical input | Who holds the pieces | Natural piece form |
|---|---|---|---|
| **Split a secret** (text) | a passphrase, recovery seed, private key, API token | people/trustees ("3 of 5 of us can restore it") | something each holder can keep/transcribe *on its own* |
| **Split a file** (file) | a keyfile, wallet backup, document, archive | drives/locations/custodians | tiny key fragments alongside the (non-secret) encrypted blob |

Both reduce to the **same hybrid engine** from the audit (§4a): a fresh random 32-byte **DEK** is Shamir-split; the input is encrypted under a key derived from the DEK with the artifact header folded in. They differ only in **how the encrypted payload is packaged** (§4 below). Building both is marginal extra surface over building one — the engine, the parsers, the error mapping, and the recover path are shared; only the input source (a text box vs a file picker) and the packaging flag differ.

*Text-only* would omit the headline large-secret case (encrypted backups); *file-only* would make the most common use (split a passphrase among trustees) awkward. Both, sharing one engine, is the lowest-regret scope.

---

## 2. Payload protection: `secretbox + Shamir(DEK)` vs `age + Shamir(DEK)`

**Recommendation: `secretbox + Shamir(DEK)` for v1. The `age` variant offers no advantage that is *realized in the current code*, and costs materially more — including changes to a vault-shared crate.**

The comparison below is corrected against source; two assumptions that would favor age (that it streams, and that it can take a symmetric key) are **false as the code stands today**.

| Dimension | **`secretbox` + Shamir(DEK)** *(recommended)* | **`age` + Shamir(DEK)** |
|---|---|---|
| **Does it even map onto the API?** | Yes, directly. `secretbox::seal(key, plaintext)` takes a symmetric 32-byte key ([secretbox.rs:22](../crates/sv-crypto/src/secretbox.rs#L22)); the DEK is that key (via a derived subkey). | **Not without new sv-age surface.** `FileCipher` exposes only `encrypt(.., recipient)` / `decrypt(.., identity)` — asymmetric age recipients/identities ([sv-crypto-traits/src/lib.rs:359-376](../crates/sv-crypto-traits/src/lib.rs#L359-L376)). There is **no symmetric/passphrase (`age -p`) mode** in `sv-age`. And an age identity is a bech32 `AGE-SECRET-KEY-1…` string, not 32 raw bytes, so the 32-byte `sss` splitter can't split it directly. "Shamir(DEK)" with age requires *adding* a symmetric mode or raw-scalar handling to sv-age. |
| **Security properties** | XSalsa20-Poly1305 (libsodium), authenticated; wrong/insufficient DEK fails the Poly1305 open ([secretbox.rs:29-33](../crates/sv-crypto/src/secretbox.rs#L29-L33)). Header bound by folding `(group_id,n,k)` into the BLAKE3 `derive_key` context (audit §4a / R2). Mature, in-process, constant-time libsodium. | ChaCha20-Poly1305 via age STREAM — equally sound. But age exposes **no AAD here either**, so binding *our* header needs the *same* derived-key trick anyway. No crypto advantage over secretbox for this use. |
| **Streaming support** | None. One-shot, buffers plaintext+ciphertext in memory. | The age *format* streams in 64 KiB chunks — **but the `sv-age` wrapper does not.** `encrypt`/`decrypt` `read_to_end` the whole input into a `Vec` before spawning, and `run()` drains stdout with `read_to_end` ([sv-age/src/lib.rs:179-182, 200-203, 124-128](../crates/sv-age/src/lib.rs#L179-L203)). **No streaming benefit today** without a non-trivial refactor of `run()` (which the vault also depends on). |
| **Large-file behavior** | In-memory, capped at `MAX_PLAINTEXT_BYTES` = 2 GiB via `read_capped` ([crypto.rs:28](../crates/sv-platform/src/crypto.rs#L28)); recover-side capped at `MAX_CIPHERTEXT_BYTES` ([crypto.rs:16,46](../crates/sv-platform/src/crypto.rs#L16)). | **Same in-memory 2 GiB-class ceiling as wrapped** (it buffers fully). True large-file handling only *after* sv-age is reworked to pipe `Read`→stdin and stdout→`Write` without `read_to_end`. That is a separate, tracked task touching shared code. |
| **Implementation complexity** | **Low.** One new `sv-platform` module; in-process calls to existing primitives; no subprocess; no new external dependency. | **High.** Needs a new sv-age symmetric/passphrase mode (or raw-scalar identities), subprocess lifecycle, the **pinned `age` binary present + resolvable** (`SV_AGE_BIN`) for the standalone tool to run at all, *and* the streaming refactor to gain anything — all on a vault-shared crate. |
| **Reuse of existing platform components** | **Maximal, zero new deps, no vault-shared code touched.** Reuses `secretbox` (re-exported by `sv-crypto`), `SssSharer`/`SecretSharer`, `Blake3Hasher::derive_key`, `getrandom`, and the `sv-platform` helpers `read_capped`/`write_atomic`/`refuse_existing` + `PlatformError → ApiError` projection. | **Partial and costly.** Reuses `AgeCipher`, but only by *extending* `sv-age` (a crate `sv-core`/the vault depend on) and by making the standalone tool depend on the bundled age toolchain at runtime. |
| **Operational footprint** | Self-contained, fully offline, no external binary. | Requires the hash-pinned `age` binary to be bundled/resolvable, or the feature fails closed. Heavier to ship and to run. |

**Bottom line.** secretbox is the only one of the two that is *expressible with today's components without modifying vault-shared code*, and age's headline advantage (streaming / unbounded files) is **not actually present in the current wrapper**. Use secretbox now. If a genuine streaming, multi-GB "split a huge file" need appears later, revisit age — but as a prerequisite it requires reworking `sv-age::run()` into true streaming (its own task, §R5 in the audit), not a drop-in.

---

## 3. Duplicate-share hazard — revisited, with a fix

**The hazard (confirmed in source).** `combine_keyshares` sets `k = shares.len()` and calls the C combiner with **no deduplication and no validation of the x-coordinates** ([sv-sys-sss/src/lib.rs:76-87](../crates/sv-sys-sss/src/lib.rs#L76-L87)). Each share self-describes its x-coordinate in **byte 0** ([:8](../crates/sv-sys-sss/src/lib.rs#L8)). Lagrange interpolation requires *distinct* x-coordinates; if two supplied shares share an x-coordinate (the common case: **the user selects the same share file twice**, or pads a too-small set by duplicating one), a basis term divides by `(x_i − x_j) = 0`. In GF(2⁸) that inverts zero rather than trapping, so the combiner returns a **wrong key silently** — no panic, no error — exactly like the documented below-threshold behavior ([:117-123](../crates/sv-sys-sss/src/lib.rs#L117-L123)). The vault's own `recover` does **not** guard this either (audit §4.5 / R8); it is a latent gap we will *not* fix in the vault (out of scope, do-not-touch), but we **must not inherit** it in the new module.

Why "the AEAD will catch it anyway" is insufficient: a duplicate-induced wrong key fails the `secretbox` open and surfaces as the *oracle-safe but unhelpful* `SV-UNAUTHORIZED` ("these pieces don't match / are corrupted"). For a user who simply picked the same file twice, that is a **misleading** error — it implies their pieces are bad when the real problem is a duplicate selection. A precise, non-secret pre-check gives a correct, actionable message and avoids even running the crypto.

**Proposed fix (recommendation) — a structural pre-check *before* `combine`, in the new `sv-platform` recover path only:**

After parsing the supplied share files and before calling `SecretSharer::combine`, in order:
1. **Agreement check** — all shares must carry the same `group_id`, `n`, `k`, and `payload_ref`; any disagreement → `SV-INVALID-INPUT` ("these pieces are from different splits"). (Non-secret; mirrors the vault's UUID check, [service.rs:623-627].)
2. **Distinct-x check (the duplicate fix)** — collect byte 0 (the x-coordinate) of every supplied share; if any value repeats → `SV-INVALID-INPUT` ("the same piece was supplied more than once"). This catches the same-file-twice case *and* any colliding-x mix, deterministically, with no crypto run.
3. **Non-zero-x check (defense in depth)** — reject any share whose x-coordinate is `0` as `SV-MALFORMED` (a genuine `sss` share never uses x=0; the secret sits at x=0). Cheap, catches corrupt/forged shares early.
4. **Count check** — distinct valid shares `< k` → `SV-INSUFFICIENT-SHARES { got, need }` (non-secret; mirrors [service.rs:612-618]). Run this on the *deduplicated* count so duplicates can't fake meeting the threshold.

Only after all four pass do we `combine` (all distinct shares), re-derive the payload key, and let the `secretbox` open be the **authoritative cryptographic gate** (wrong-but-distinct shares from a different split still fail there → `SV-UNAUTHORIZED`). This makes the standalone tool *stricter and clearer* than the vault without touching the vault.

The check is a handful of byte comparisons over ≤255 33-byte shares — negligible cost, and it runs entirely on attacker-/user-supplied *file* metadata, so none of it is a secret-bearing oracle.

---

## 4. Final user-facing workflow and file formats *(decided — see §5)*

**Decisions (locked):** both workflows · **uniform packaging** (always one payload file + `n` key pieces, for text *and* files) · text pieces additionally offered as **copy-paste Base64 strings**. One engine, three screens. Sizes carried from the audit (§4b) and re-verified; **all field sizes remain design proposals to review**, everything cited `file:line` is source-confirmed.

### 4.1 Workflow A — "Split a secret" (text)
1. User types/pastes the secret (UTF-8), chooses **total pieces `n`** and **pieces needed `k`** (`1 ≤ k ≤ n ≤ 255`), and an output folder.
2. Engine: fresh DEK → derive payload key bound to `(group_id,n,k)` → `secretbox`-seal the secret → Shamir-split the DEK → write **one payload file + `n` key-piece files** (uniform packaging).
3. **Copy-paste delivery:** each key-piece file is *also* surfaced as a Base64 string the holder can write down or paste. The Base64 string encodes the 92-byte key piece only — recovery still needs the (separate) payload file (see the ergonomic note below).
4. Result card: the payload path + the list of piece files (no secret bytes) + the per-piece Base64 strings, plus the `k`-of-`n` policy as plain text.

> **Ergonomic note (consequence of uniform packaging).** Because packaging is uniform, a text holder keeps **two things**: their key piece (file or Base64) *and* the shared payload file. The payload is **non-secret ciphertext** — it can be replicated, stored openly, or handed to every holder — but it must not be lost (lose it and even all `n` pieces can't recover). For a text secret the payload is tiny; a later enhancement could also emit it as a Base64 string so a fully copy-paste recovery is possible. Recorded as a deferred option, not v1.

### 4.2 Workflow B — "Split a file"
1. User picks a file, chooses `n`/`k`, and an output folder.
2. Engine: identical — **one payload file** (the encrypted file, non-secret) + **`n` tiny key-piece files**. (Same uniform format as A; duplicating a multi-GB ciphertext per piece is exactly what uniform packaging avoids.)
3. Recover needs `k` key pieces **and** the payload file. (Base64 piece strings are not offered for the file workflow — pieces there are about custody of drives/locations, not transcription.)
4. Result card: the payload path + the list of key-piece files.

### 4.3 Workflow C — "Recover from pieces" (shared by A and B)
1. User selects key pieces (files, or pasted Base64 strings for the text case) **and** the payload file, plus an output path.
2. Engine runs the §3 pre-checks → `combine` → re-derive payload key → `secretbox` open → write recovered output.
3. Errors map to: `SV-INSUFFICIENT-SHARES` ("you need at least *k* pieces"), `SV-INVALID-INPUT` ("pieces from different splits / a piece supplied twice"), `SV-MALFORMED` ("not a valid piece file"), `SV-UNAUTHORIZED` ("these pieces don't match or are corrupted").

### 4.4 File formats

**One uniform pair of framings** — a key-piece file and a payload file — used by *both* workflows. Both follow the `sv-platform/artifact.rs` conventions (6-byte `MAGIC`, LE `u16` version, fixed header, pre-auth bounds), are distinct from the vault's 4-byte `SVSH`, and are auto-detected on recover by `MAGIC`. (The self-contained `SVSSB\0` framing considered earlier is **dropped** — uniform packaging means there is no embedded-payload piece.)

**Key-piece file — `SVSSS\0`, fixed 92 bytes:**
```
off  len  field            notes
0    6    MAGIC=SVSSS\0     piece magic
6    2    format_version=1  LE u16
8    16   group_id          fresh random per split (replaces the vault UUID)
24   1    total (n)         1..=255
25   1    threshold (k)     1 <= k <= n
26   1    share_index       advisory; x-coord is byte 0 of key_share
27   32   payload_ref       BLAKE3 of the WHOLE payload file (binds piece↔payload)
59   33   key_share         [u8;33]; byte0 = x-coordinate, 1..33 = GF(2^8) y
```

**Payload file — `SVSSP\0`:**
```
off  len  field            notes
0    6    MAGIC=SVSSP\0
6    2    format_version=1
8    1    aead_alg=0        XSalsa20-Poly1305 secretbox
9    24   nonce             secretbox nonce
33   ..   ciphertext        secretbox output (includes the 16-byte Poly1305 tag)
```
Overhead = 33 header bytes + 16 tag = **49 bytes** over the plaintext. Recover slices `nonce = blob[9..33]`, `ciphertext = blob[33..]` (mirrors [artifact.rs:105-107]).

**Copy-paste piece string (text workflow):** the Base64 (standard alphabet, no wrapping) of the exact 92-byte `SVSSS\0` file. On recover, a pasted string is Base64-decoded back to the 92 bytes and validated identically to a piece file — same parser, same §3 pre-checks. No separate format; it is the same artifact in a transcribable encoding.

**Naming:** `{group_id_hex}.share{index}.svss` for pieces; `{group_id_hex}.payload.svss` for the payload. Header binding, caps, pre-auth DoS bounds, zeroization, and oracle-safe error mapping are exactly as the audit specifies (§4–§6) — unchanged here.

---

## 5. Decisions (resolved) and what remains settled

**Resolved by product owner:**
1. **Workflows in scope** — **both** ("Split a secret" + "Split a file"), one shared engine.
2. **Piece packaging** — **uniform**: always one `SVSSP\0` payload file + `n` `SVSSS\0` key pieces, for text and files alike. (Trade-off accepted: a text holder keeps two things; see §4.1 ergonomic note. No self-contained `SVSSB\0` framing.)
3. **Text-piece delivery** — **files + copy-paste Base64 strings** (the strings encode the key piece; the payload still travels as a file).

**Already settled (source-grounded, no further input needed):** the `secretbox + Shamir(DEK)` engine (§2), the header-binding fix via `derive_key` context (audit §4a / R2), the duplicate-share pre-`combine` check (§3), the oracle-safe error codes, the additive session-free `PlatformSurface` commands (`shares_split_secret` / `shares_recover_secret`), the new `PlatformError::InsufficientShares` variant, and **no changes to the vault / `SVSH` / `keys_*` path** (audit §8).

**Ready for the ships-first slice** (audit §5 steps 1–5) on your go-ahead: the `sv-platform` engine + the `SVSSS\0`/`SVSSP\0` artifacts + the error variant, behind the full cargo gate set, before any IPC/UI.
