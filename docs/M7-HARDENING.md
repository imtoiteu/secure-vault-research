# Secure Vault — M7 Hardening & Threat Model

**Status:** M7 applies the verifiable hardenings and records the threat model, a constant-time
audit, and the reasoned deferrals (each with rationale and the cheaper mitigation that stands
in for it). Phase 1 (M0–M6) delivered the functionality; M7 is about residual-risk reduction
and honest disclosure of what is *not* covered. Companion to
[`M5-SCHEMA-DECISIONS.md`](M5-SCHEMA-DECISIONS.md) and [`M6-IPC-DECISIONS.md`](M6-IPC-DECISIONS.md).

---

## 1. Threat model

**Assets.** (1) Vault contents (item plaintext). (2) The passphrase and everything derived
from it (MK, wrap keys, unwrapped age identity + signing key). (3) Recovery shares.

**Primary threats (in scope).**
- **At-rest disclosure.** An attacker who obtains the `.svault` file (theft, backup, cloud
  sync). Mitigation: age AEAD payload + Argon2id-gated, secretbox-wrapped keys; the file
  reveals only its size, timestamps, KDF params, and public keys — **no item names/sizes/count**
  (H3, encrypted directory).
- **Tampering / forgery.** An attacker who modifies the file. Mitigation: the binding-root
  minisign signature (H5) — any change to header or payload fails verification *before* the
  passphrase is used, and a header cannot be spliced onto another file's payload.
- **Malicious vault.** A hostile `.svault` crafted to exploit the opener. Mitigation:
  panic-free, bounds-checked parsing (fuzz-tested, §2.3); a **pre-auth KDF-parameter ceiling**
  (§2.4) so a hostile header cannot force unbounded Argon2 work.
- **Hostile/hung bundled binary.** Mitigation: `age` is BLAKE3-hash-pinned (M3) and run with a
  **wall-clock timeout** (§2.1), cleared env, no shell.
- **Error-oracle probing.** Mitigation: oracle-safe `ApiError` (E2) — wrong-passphrase and
  wrong-share are merged; tamper is a *separate, earlier* gate, not an oracle.

**Out of scope (documented residuals, §3).**
- A live attacker with **process-memory read** or arbitrary code execution on the unlocked
  host (they can read the MK regardless of our hygiene).
- Passphrase copies the **Tauri/serde IPC bridge** makes before our code runs (N1).
- **Side channels** beyond the constant-time primitives we rely on (cache/timing of the OS,
  the Go `age` process, etc.).
- The user's OS, swap, and crash-dump configuration (we *recommend*, cannot *enforce*).

**Trust boundaries.** UI (webview) ↔ core (Rust) over the IPC bridge — passphrase entry
crosses it (N1 residual). Core ↔ bundled `age` subprocess — hash-pinned, sandboxed args/env.
Core ↔ filesystem — atomic writes; integrity/authenticity via signature on read.

---

## 2. Hardenings applied in M7

### 2.1 `age` subprocess wall-clock timeout
`AgeCipher` now enforces a per-invocation deadline (`DEFAULT_TIMEOUT = 120s`, overridable via
`with_timeout`). stdin is fed and stdout/stderr drained on separate threads; the main thread
waits on the deadline and, on expiry, kills the child and returns `AgeError::TimedOut` instead
of blocking forever. A hung or wedged binary can no longer freeze a vault operation.
*Verified:* `run_aborts_a_hanging_binary_at_the_timeout` (a `sleep 30` script returns in
~200 ms under a 200 ms timeout).

### 2.2 Plaintext zeroization
Decrypted item plaintext is now wiped: `UnpackedArchive` zeroizes its `item_bytes` region on
drop, `pack_archive` wipes its plaintext scratch, and the service already zeroizes the
decrypted-payload buffer after unpacking and item buffers after a re-pack. Keys were already
zeroizing (`Key32`/`SecretBytes`/`KeyShare`, M0.1). **Best-effort:** arbitrary-size content
streamed through `age` is buffered (§3.5); full guarantee awaits streaming.

### 2.3 Parser robustness (fuzz-style)
The container parser's panic-free contract is now exercised by a deterministic sweep
(`decode_is_panic_free_on_truncations_mutations_and_random_input`): every truncation length,
4000 xorshift single-byte mutations, and random buffers — asserting no panic and that a mutated
container never authenticates as anything but the original payload. Complements the existing
malformed-input and share-envelope bounds tests. (A coverage-guided `cargo fuzz` target is a
natural CI add-on, §3.3.)

### 2.4 Pre-auth KDF-parameter ceiling
Carried in from M6 and part of the hardening surface: before running Argon2 on
header-supplied parameters, the service rejects values above a safe ceiling
(`MAX_KDF_MEM_KIB = 4 GiB`, `time ≤ 64`, `parallelism ≤ 64`), so a validly-signed but hostile
vault cannot force resource-exhaustion at unlock.

### 2.5 Adaptive KDF calibration (A4)
`policy::calibrate(target, mem_kib)` measures Argon2id on the current machine and picks a
`time_cost` meeting a target duration at a chosen memory budget, never below the OWASP floor
and bounded by `MAX_CALIBRATED_TIME_COST`. This lets vault creation (or a settings UI) track
real hardware instead of the fixed 256 MiB / t=3 guess. The fixed default remains the
deterministic fallback.

---

## 3. Reasoned deferrals (with standing mitigations)

### 3.1 `mlock` of in-memory secrets — **deferred**
*Why deferred:* reliable memory locking needs platform-specific `unsafe` (`mlock`/`VirtualLock`)
or a third-party crate doing the same, which conflicts with the `#![forbid(unsafe_code)]`
posture of the domain/app crates; and it must lock the *specific* pages backing the session MK,
which interacts poorly with a zeroizing value held in a `HashMap` (values move). The payoff is
also bounded: `mlock` only prevents swap-out, not in-process reads.
*Standing mitigation:* recommend **OS full-disk + swap encryption** (covers the swap threat
end-to-end) and crash-dump suppression for the core process; keep the MK the *only* long-lived
secret (the identity/signing key are transient, M6). *Revisit* behind a small, audited,
`unsafe`-isolated crate if the threat model elevates.

### 3.2 Dedicated passphrase channel (N1) — **deferred**
*Why deferred:* the JSON IPC bridge copies the passphrase before our code runs; eliminating that
needs a native OS prompt outside the webview or OS-keychain integration — a product/UX decision
that belongs with the frontend.
*Standing mitigation:* `IpcPassphrase` (zeroizing, redacted, excluded from logging) +
documented residual + OS swap/dump guidance.

### 3.3 Coverage-guided fuzzing in CI — **deferred**
*Why deferred:* `cargo fuzz` needs nightly + libFuzzer and a non-trivial cross-platform CI
setup; the value is incremental over §2.3.
*Standing mitigation:* the deterministic robustness sweep (§2.3) plus the bounds/malformed
tests. *Plan:* add a `fuzz/` target for `container::decode` and run it nightly.

### 3.4 minisign-CLI byte-level interop gate — **deferred (planned CI gate)**
We implement the minisign on-disk format by hand (`sv-crypto::minisign`) and round-trip it
internally; `verify_file` currently accepts a hex Ed25519 public key (our artifact) rather than
a minisign `.pub`. *Plan:* a CI step that installs stock `minisign`, signs/verifies across the
boundary, and parses `.pub`/`.minisig` for full interop. Tracked, not yet wired.

### 3.5 `age` streaming + bounded memory — **deferred**
Payloads are buffered in memory (M3). Large vaults should stream through `age` incrementally
and cap buffer growth. *Standing mitigation:* the timeout (§2.1) bounds *time*; memory is
bounded only by available RAM today.

### 3.6 External provenance trust store (schema decision H4) — **deferred (post-Phase-1)**

<!-- "H4" here is the M5 schema-decision (provenance vs. integrity), NOT hardening H4 (Windows env_clear). -->

The in-header signature is **integrity / tamper-evidence**, not third-party authorship; `decode`
already supports an optional pinned key for provenance, but a managed trust store / PKI is a
product feature beyond Phase 1.

---

## 4. Constant-time audit

Reviewed every place a *secret* participates in a comparison or branch:

- **Passphrase / wrong-credential check** — performed by **libsodium `crypto_secretbox_open`**
  (Poly1305 MAC), which is constant-time; we never compare derived keys or MACs in Rust.
- **Container signature** — **Ed25519 verification** (libsodium), constant-time.
- **Share reconstruction** — `sss` GF(2⁸) combine over fixed-size shares; the auth decision is
  the subsequent constant-time secretbox unwrap, not a share comparison.
- **`Key32` / `SecretBytes` equality** — appears **only in tests** (`assert_eq!` on
  `expose_secret`), never on a production credential path.
- **Non-secret comparisons** — the `age` binary hash pin (`eq_ignore_ascii_case` on a public
  BLAKE3 hex), the pinned-vs-header public key check, magic/version bytes, and `vault_uuid`
  matching are all over **public** values; their timing reveals nothing secret.

**Conclusion:** no secret-dependent branch or non-constant-time secret comparison on a
production path. If a future change compares secret bytes directly, route it through a
constant-time equality (e.g. `subtle::ConstantTimeEq`).

---

## 5. Residual-risk summary

| Risk | Status | Mitigation / note |
|---|---|---|
| At-rest file theft | **Mitigated** | age AEAD + Argon2id + wrapped keys; metadata hidden (H3) |
| Tamper / forgery | **Mitigated** | binding-root minisign signature (H5) |
| Malicious vault (parse) | **Mitigated** | panic-free bounds-checked parser, fuzz-swept (§2.3) |
| Malicious vault (KDF DoS) | **Mitigated** | pre-auth parameter ceiling (§2.4) |
| Hung/hostile `age` binary | **Mitigated** | hash-pin + wall-clock timeout (§2.1) |
| Error oracle | **Mitigated** | oracle-safe coded `ApiError`; tamper is a separate gate (E2) |
| Secret in swap | **Residual** | OS swap encryption recommended; `mlock` deferred (§3.1) |
| Passphrase IPC copies | **Residual** | `IpcPassphrase` + documented; native channel deferred (§3.2) |
| Live in-process attacker | **Out of scope** | already-compromised host |
| Large-payload memory | **Residual** | buffered; streaming deferred (§3.5) |
| Third-party provenance | **Deferred** | self-signed = integrity only; trust store post-Phase-1 (§3.6) |
| minisign CLI interop | **Deferred** | internal round-trip verified; cross-CLI gate planned (§3.4) |
