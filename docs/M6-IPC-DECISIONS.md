# Secure Vault — Pre-M6 IPC & Session-Boundary Freeze (E1, E2, E3, N1)

**Status:** Decision review complete; **implemented in M6.** E1–E3 (error taxonomy + stable
codes + `IncompatibleVersion`/`Malformed`/`InsufficientShares`) and N1 (`IpcPassphrase`) are
live in `sv-types`/`sv-core`/`sv-app`; the four-gate unlock order, session rules, and
secret-lifetime rules are realized in `sv-app::VaultBackend`. This document remains the design
authority; the code matches it. Companion to
[`M5-SCHEMA-DECISIONS.md`](M5-SCHEMA-DECISIONS.md); resolves the pre-M6 items left
PROVISIONAL in [`M0-CONTRACTS.md`](M0-CONTRACTS.md) §2 and §6.

**Grounding (current code):**
- `sv_types::ApiError` = `NotFound | Unauthorized | Corrupted | InvalidInput(String) | Internal`,
  serde `#[serde(tag="kind", content="detail")]`. `CONTRACT_VERSION = 1`.
- `sv_core::VaultError` = `NotFound | AuthFailed | Corrupted | UnsupportedVersion(u16) |
  InvalidInput(String) | Crypto(CryptoError) | Io(String) | Internal`, projected to `ApiError`
  via `From` (oracle-safe collapse).
- `sv_app::CommandSurface` takes `passphrase: String`; `sv_core::VaultService` already takes
  `SecretBytes` (the internal API is correct — only the IPC boundary is leaky).

**Pivotal observation that shapes E2.** The container is signed (M5, H5). A tampered
header/payload fails the **binding-root signature**, which is checked with the *public*
in-header key **before any passphrase is used**. So "tampered" is detected pre-credential and
is cleanly separable from "wrong passphrase/share" (a later secretbox-MAC failure). Corruption
and wrong-credential are therefore **sequential gates, not an oracle pair** — and, critically,
because the wrapped secret lives *inside the signed header*, a secretbox-MAC failure that
occurs *after* a passing signature can only be a wrong credential, never tampering.

---

## E1 — `IncompatibleVersion`

**Current design.** `VaultError::UnsupportedVersion(u16)` projects to `ApiError::Corrupted`. A
vault from a newer app version looks identical to a damaged/tampered file.

**Review concern.** Conflates a benign, actionable condition ("update the app") with an
alarming, non-actionable one ("this file is damaged/tampered"). It misleads the user, hides the
remediation, and muddies support diagnostics.

**Security impact.** Low — and *not* an oracle. The version is the raw `u16` at a fixed prefix
offset, readable by anyone without any key; surfacing it leaks nothing. The only security rule
is **fail closed**: reject unknown/newer versions, never best-effort-parse (consistent with the
V1 strict-gating decision; prevents downgrade/confusion). One subtlety surfaced below requires a
rule about *suite* changes.

**UX impact.** High positive — distinct dialog and remediation: "This vault was created by a
newer version of Secure Vault (format vN). Update to open it," vs. "This vault is damaged or has
been tampered with."

**Implementation impact.** Small: add a distinct variant carrying the version values. **Detect
via the raw FORMAT_VERSION prefix**, which an old app can always read — *not* via the in-header
`suite` enum (an old app's closed `CipherSuite` enum cannot even represent a future variant, so
a future-suite file would fail CBOR parse as `Malformed`/`Corrupted` rather than report a clean
incompatibility). This forces a companion rule.

**Recommendation — Adopt.** Add `VaultError::IncompatibleVersion { found: u16, supported: u16 }`
(replacing `UnsupportedVersion`'s semantics, keeping the value) → `ApiError::IncompatibleVersion`.
Drive it from the **raw prefix u16**. Freeze the rule: **any change an older reader cannot safely
handle — including a new `CipherSuite` — MUST bump `FORMAT_VERSION`**, so the raw-prefix gate
fires before CBOR parsing. The in-header `suite` cross-check stays defense-in-depth → `Corrupted`
(legitimately unreachable for honest version skew). Fail closed; never auto-upgrade-read.

---

## E2 — Recovery & failure clarity

**Current design.** `AuthFailed` merges wrong-passphrase with wrong/insufficient shares →
`Unauthorized`. `Corrupted` merges parse errors, signature failures, MAC failures, and version.
During recovery, "you gave 2 of 3 required shares," "wrong share bytes," and "this isn't a vault"
are indistinguishable.

**Review concern.** Two genuinely distinct, **non-secret** situations are hidden:
1. **Insufficient share *count*** (got 2, need 3) — a pre-check; the threshold is in the
   (readable) header and the count is what the user supplied. Surfacing it is essential UX and
   leaks nothing.
2. **"Not a vault / parse error" vs "tamper-evident corruption"** — selecting the wrong file
   ("this isn't a Secure Vault file") is benign and structural; a damaged/tampered real vault is
   alarming. Both are non-secret (magic bytes and signature-verifiability are public).

**Security impact.** Net positive **and** oracle-safe, given the sequential-gate structure:
1. Structural parse fails → **Malformed** (non-secret; "wrong file").
2. Binding-root signature fails → **Corrupted** (tamper/bit-rot; verifiable with the public
   in-header key, pre-credential; non-secret).
3. Recovery only: fewer shares than threshold → **InsufficientShares { got, need }** (counts are
   non-secret; no reconstruction attempted).
4. Signature passed, but secretbox-unwrap fails → **Unauthorized** (wrong passphrase OR wrong
   shares-of-sufficient-count — **stays merged**; since the signature passed, the wrapped bytes
   are intact, so this can only be a wrong credential).
   - Timing: within a single command the auth path is uniform (unlock always runs Argon2 +
     unwrap; recover always runs combine + unwrap), so there is no intra-command oracle. The
     passphrase-vs-share distinction across *different commands* is already known to the caller
     (they chose which to invoke).

**UX impact.** High positive — "you need 1 more share," "wrong file," and "damaged vault" become
distinct, correct messages while the credential check stays opaque.

**Implementation impact.** Add `VaultError::Malformed` and `VaultError::InsufficientShares
{ got, need }`; keep `AuthFailed`. Tighten the `Crypto`-error mapping: **map at the call site by
context** — secretbox-unwrap failure during unlock/recover → `AuthFailed`; signature-verify
failure → `Corrupted`; an unmapped `Crypto` is a logic bug → `Internal` (not the current blanket
`Crypto → Corrupted`).

**Recommendation — Adopt**, with the four-gate ordering above frozen as the unlock/recover
contract (parse → version → signature → [Argon2+unwrap | count+combine+unwrap]).

---

## E3 — Stable error codes

**Current design.** `ApiError` carries free-form `String` detail and a serde `kind`/`detail`
shape; no stable machine code. A UI must match Rust variant names or parse English strings.

**Review concern.** Free-form strings break i18n (can't localize a core-supplied English string),
are brittle (wording changes break UI matching), and are poor for telemetry/support.

**Security impact.** Low, with one rule: **codes are 1:1 with the (already oracle-safe)
variants, never finer.** No `AUTH_WRONG_PASSPHRASE` vs `AUTH_WRONG_SHARE` — that would re-open
the E2 merge. Free-form `detail` must be non-secret and never the source of user-facing text.

**UX impact.** High positive — localized, consistent messages and a stable support vocabulary;
structured fields (found/supported/got/need) feed localized templates.

**Implementation impact.** Moderate. Give each `ApiError` a stable string code via
`#[serde(tag = "code")]` + per-variant `#[serde(rename = "SV-…")]`, so the wire discriminant *is*
the stable code and Rust variants can be renamed freely. Add an optional non-secret `detail` for
logs/support only.

**Recommendation — Adopt.** Closed code set, 1:1 with variants; UI localizes off `code`; `detail`
is diagnostic-only, non-secret, non-localized.

---

## N1 — Passphrase across the Tauri boundary

**Current design.** `CommandSurface` takes `passphrase: String`; the doc says "immediately move
into `SecretBytes` and zeroize the incoming `String`."

**Review concern.** This is the **real no-secrets-invariant gap**. A `String` arriving over the
Tauri IPC bridge has already been materialized by the framework: the raw IPC message buffer and
serde_json's parse buffers are **upstream copies we never see and cannot zeroize**. Zeroizing
"the incoming `String`" wipes only the last copy; earlier copies linger in freed heap (and may
hit swap or a crash dump).

**Security impact.** Highest residual of the four — a memory-disclosure exposure (swap, core
dump, same-process read). Severity is bounded by threat model: for an offline single-user vault,
a live attacker with process-memory access has largely already won, and the at-rest guarantees
(the encrypted file) are the primary asset. It becomes serious with unencrypted swap or uploaded
crash dumps. Mitigations, ranked:
- **Must:** move into `SecretBytes` on the first handler line and drop/zeroize our copy; exclude
  passphrase-bearing commands from Tauri argument logging; redacted `Debug`; passphrase never
  enters any DTO, `ApiError`, `detail`, or log.
- **Should:** recommend OS full-disk + swap encryption and crash-dump suppression for the core
  process in the threat model; keep passphrase-bearing commands minimal and short-lived.
- **Evaluate (deferred):** a dedicated secret-input channel — a native OS passphrase prompt
  outside the webview, or OS-keychain integration — so the passphrase never crosses the JSON
  bridge. This is an M7/product item, **not an M6 blocker**.

**UX impact.** Low if transparent (in-app field retained for M6). A future native prompt/keychain
would change entry UX — a product decision, deferred.

**Implementation impact.** Moderate. Introduce an `IpcPassphrase` newtype as the command arg
type: implements `Deserialize`, `ZeroizeOnDrop`, redacted `Debug`; the handler converts it to
`SecretBytes` immediately and lets it drop. `VaultService` already takes `SecretBytes`, so the
boundary newtype is the only addition. The upstream framework copies remain the **documented
residual**.

**Recommendation — Accept the boundary with documented mitigations; do not block M6.** Add
`IpcPassphrase`, exclude from logging, document the residual in the threat model, defer the
dedicated channel.

---

## Final IPC & session-boundary design

### 1. Error taxonomy

**Internal — `sv_core::VaultError` (rich):**

| Variant | Meaning | Projects to |
|---|---|---|
| `NotFound` | vault/item/session missing | `NotFound` |
| `Malformed` *(new)* | not a vault / structural parse failure (bad magic, truncation, bad CBOR) | `Malformed` |
| `IncompatibleVersion { found: u16, supported: u16 }` *(new; replaces `UnsupportedVersion`)* | known framing, unsupported FORMAT_VERSION | `IncompatibleVersion` |
| `Corrupted` | real vault, **signature/integrity** failed (tamper/bit-rot) | `Corrupted` |
| `AuthFailed` | wrong passphrase **or** wrong shares (sufficient count) — merged | `Unauthorized` |
| `InsufficientShares { got: u8, need: u8 }` *(new)* | fewer shares than threshold (pre-check) | `InsufficientShares` |
| `InvalidInput(String)` | caller input structurally invalid (non-secret) | `InvalidInput` |
| `Crypto(CryptoError)` | **mapped at call site** (unwrap-fail→`AuthFailed`, sig-fail→`Corrupted`); unmapped→`Internal` | `Internal` |
| `Io(String)` | filesystem error (redacted) | `Internal` |
| `Internal` | unexpected | `Internal` |

**External — `sv_types::ApiError` (oracle-safe, coded):** `NotFound`, `Malformed`,
`IncompatibleVersion { found, supported }`, `Corrupted`, `Unauthorized`,
`InsufficientShares { got, need }`, `InvalidInput { detail }`, `Internal`.

**Unlock/recover gate order (frozen):** `parse → Malformed` · `version → IncompatibleVersion` ·
`signature → Corrupted` · *(recover only)* `count → InsufficientShares` ·
`Argon2 + secretbox-unwrap (unlock) / combine + unwrap (recover) → Unauthorized on failure`.
Because the wrapped secret is inside the signed header, a post-signature unwrap failure is
provably a wrong credential, not tampering — so the gates do not form an oracle.

### 2. Stable error codes

Closed set, **1:1 with `ApiError` variants** (never finer — preserves the oracle merges). Wire
form: `#[serde(tag = "code")]` so the discriminant *is* the code; structured fields ride
alongside.

| Code | Variant | UI intent |
|---|---|---|
| `SV-NOT-FOUND` | `NotFound` | missing vault/item/session |
| `SV-MALFORMED` | `Malformed` | "not a Secure Vault file" |
| `SV-INCOMPATIBLE-VERSION` | `IncompatibleVersion {found,supported}` | "update the app (format vN)" |
| `SV-CORRUPTED` | `Corrupted` | "damaged or tampered" |
| `SV-UNAUTHORIZED` | `Unauthorized` | "wrong passphrase or recovery shares" |
| `SV-INSUFFICIENT-SHARES` | `InsufficientShares {got,need}` | "need N more shares" |
| `SV-INVALID-INPUT` | `InvalidInput {detail}` | structural input error |
| `SV-INTERNAL` | `Internal` | redacted internal failure |

UI localizes off `code` (structured fields fill placeholders). `detail` is optional, non-secret,
non-localized, for logs/support only. **This is a `CONTRACT_VERSION` change**; since nothing
consumes the IPC contract pre-release, fold it into `CONTRACT_VERSION = 1` as the first-release
baseline and start bump discipline at first ship.

### 3. Version-incompatibility handling

- **Primary gate = raw `FORMAT_VERSION` prefix `u16`** — readable without CBOR parse by any app
  version. Strict known-set acceptance; reject unknown (**fail closed**, no best-effort parse).
- **Rule:** any change an older reader cannot safely handle — **including a new `CipherSuite`** —
  MUST bump `FORMAT_VERSION` so the raw gate fires before CBOR. (Suite stays a conceptually
  independent axis but never increments without a FORMAT_VERSION bump.)
- In-header `suite` mismatch = defense-in-depth → `Corrupted` (unreachable for honest skew).
- **IPC handshake:** expose `app_info() → { app_version, contract_version, max_format_version,
  suite_version }` so the UI can detect contract/format support. In a bundled Tauri app UI+core
  ship together (runtime skew shouldn't occur), but the handshake makes it detectable and
  supports future decoupled deployment.
- **Anti-downgrade:** never auto-upgrade-read a newer file; never rewrite an older
  FORMAT_VERSION without an explicit, reviewed migration.

### 4. Passphrase handling across the Tauri boundary

- Command arg type = **`IpcPassphrase`** newtype: `Deserialize`, `ZeroizeOnDrop`, redacted
  `Debug`. The handler converts to `SecretBytes` on its first line and drops the newtype
  (zeroizing our copy). `VaultService` already takes `SecretBytes`.
- **Forbid logging:** passphrase-bearing commands excluded from Tauri arg logging; redacted
  `Debug`; passphrase never enters a DTO, `ApiError`, `detail`, or log.
- **Documented residual (threat model):** Tauri/serde_json produce upstream passphrase copies
  (IPC buffer, JSON parse) we cannot zeroize. Recommend OS full-disk + swap encryption; suppress
  crash dumps for the core process. Full passphrase-entry memory hygiene through the JSON bridge
  is not achievable.
- **Deferred (not an M6 blocker):** dedicated secret channel — native OS prompt outside the
  webview, or OS keychain — so the passphrase never crosses the JSON bridge.

### 5. Session lifecycle rules

- `vault_unlock` / `keys_recover` mint a session: a **random, non-secret** `session_id` (never
  derived from any secret) → `SessionHandle { session_id }`. The UI only ever holds this opaque
  id; **no secret crosses the IPC boundary** (beyond the passphrase-entry residual above).
- Core keeps a mutex-guarded session table `session_id → SessionState { master_key: Key32,
  vault_path, opened_at, last_used }`. Secrets live only here, only in zeroizing types.
- `vault_lock(session)` removes the entry and **zeroizes** immediately.
- **Auto-lock:** sessions expire after a configurable inactivity window (zeroizing on expiry);
  default is a product setting (e.g. 15 min) — not a security-critical constant.
- **Process-scoped:** session ids are valid only within the running core process; they do not
  persist across restart (restart ⇒ re-unlock).
- **Capacity/DoS:** bound concurrent sessions; an unknown/expired id → `NotFound` (ids are
  non-secret opaque handles).
- `vault_change_passphrase(session, new)` re-derives MK′, re-derives wrap keys, **re-wraps** the
  stored secrets, atomically rewrites + re-signs the container; the old MK is zeroized.

### 6. Secret lifetime rules

- Secrets exist **only inside the core process**, only in zeroizing types (`Key32`, `SecretBytes`,
  `KeyShare`, `AgeIdentity`).
- **Session retains the MK only** (zeroizing). The unwrapped age identity and signing key are
  **materialized transiently per operation** (re-derive wrap key → secretbox-open → use →
  zeroize), minimizing the count and lifetime of live operational secrets. (M7 may `mlock` the
  session MK.)
- The age identity, when used, is written to a `0600` temp file by `AgeCipher` (M3) and
  overwritten+unlinked on drop — already handled.
- Passphrase: wrapped in `SecretBytes` at the boundary, consumed to derive MK, then dropped —
  **not** retained in the session.
- Payload plaintext (decrypted archive / item bytes) is user content: minimize lifetime; zeroize
  the archive buffer after encrypt/extract where feasible (full zeroization of arbitrary-size
  streamed content is best-effort → M7).
- No secret in: DTOs, `ApiError`, `detail`, logs, session handles, or the IPC bridge (beyond the
  documented passphrase-entry residual).

---

## Remaining blockers

**For M6 — design blockers: none.** All four decisions are resolved above. M6 may proceed to wire
`StdKeyHierarchy` + `secretbox` + `AgeCipher` + `container` into `VaultService`, add the session
table, and expose `CommandSurface` / Tauri commands with this taxonomy.

**Additive contract changes M6 will apply (pre-release, free now):**
- `sv_types::ApiError`: add `Malformed`, `IncompatibleVersion {found,supported}`,
  `InsufficientShares {got,need}`; switch to `#[serde(tag="code")]` stable codes; `InvalidInput`
  detail stays non-secret. (Folds into `CONTRACT_VERSION = 1`; bump discipline starts at ship.)
- `sv_core::VaultError`: add `Malformed`, `IncompatibleVersion`, `InsufficientShares`; revise the
  `From` mapping; tighten call-site `Crypto`-error translation.
- `sv_app`: `IpcPassphrase` newtype; logging exclusion; `app_info()` handshake.

**Notes M6 will encounter (not blockers):**
- **Tauri enters the workspace (A9):** command-macro constraints on arg/return types (serde +
  Tauri-compatible; `IpcPassphrase` must `Deserialize`; sync vs async commands). Current shapes
  are serde-friendly.
- **KDF-param DoS ceiling (deferred from M5):** before running Argon2 on header-supplied params
  during unlock, validate them against a sane **upper** bound (mem/time), since the header is
  attacker-influenceable pre-auth. M6 unlock-path hardening.

**Out of scope (later):** the dedicated passphrase channel (N1, M7/product), `mlock` and
constant-time review (M7), and the external provenance trust store (schema decision H4, post-Phase-1).

---

## Addendum — additive read-only commands (post-M6, UI shell)

Two **read-only** commands were added to `VaultService` / `CommandSurface` to support the desktop
UI. Both are additive, oracle-neutral, and mutate nothing on disk; they require a valid session
(invalid/locked → `NotFound`, identical to every other session op — no new oracle):

- **`vault_meta(session) -> VaultMeta`** — non-secret metadata (uuid, format version, timestamps,
  item count, recovery policy, KDF cost) for the unlocked vault. Counting items requires the MK
  (the item directory lives inside the encrypted payload), so it decrypts in-memory exactly like
  `list_items`; the returned DTO carries no secret (the `sv-types` invariant). The UI uses it for
  the post-unlock banner and to pre-fill the recovery-share `n`/`k` from the vault's policy.
- **`export_signing_public_key(session) -> String`** — the vault's Ed25519 **public** key as plain
  64-char hex, read from the signature-verified header (the MK is not needed and is dropped
  immediately). The format is exactly what `verify_file`'s `parse_pubkey_hex` consumes, so a user
  can export it, save it to a `.pub` file, and verify files this vault signed.

No DTO shapes changed (both reuse `VaultMeta` / `String`), so `CONTRACT_VERSION` stays `1`; the
additive-evolution discipline (new commands using existing DTOs ⇒ no major bump) holds. Covered by
`sv-app` tests `vault_meta_is_readonly_and_reports_policy_and_item_count` (asserts the on-disk
container is byte-identical before/after the call) and
`export_signing_public_key_matches_header_and_verifies_signatures`.
