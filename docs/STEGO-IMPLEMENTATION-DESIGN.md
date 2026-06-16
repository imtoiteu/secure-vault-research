# Secure Vault — Steganography Module Implementation Design (`sv-stego`)

**Status:** Design only. **No implementation authorized or written.** Companion to
[STEGO-ARCHITECTURE.md](STEGO-ARCHITECTURE.md). Evidence base:
[`steganography/EVALUATION.md`](../../steganography/EVALUATION.md) + the four built-and-read references
(`jsteg`, `auyer-steganography`, `dct-io`, `pnger`). Scope: **image-only**, PNG/BMP (LSB) first.

Code blocks below are **design pseudocode / signatures**, not implementation.

---

## 1. Crate structure

```
crates/sv-stego/
├── Cargo.toml          # deps: sv-types, sv-crypto-traits, sv-crypto (reused Argon2id+secretbox; in-crate sealer);
│                       #       image { default-features=false, features=["png","bmp"] }, getrandom, thiserror,
│                       #       zeroize, tempfile; dct-io (JPEG DCT coefficients, Phase 4 — pure-Rust, MIT/Apache).
│                       #       Phase 2 appended-data detection is IN-HOUSE (no `binwalk` dep — fallback taken).
│                       #       Dev-only: image `jpeg` feature, to mint baseline-JPEG test fixtures.
└── src/
    ├── lib.rs          # public re-exports; wires modules; crate-level docs
    ├── error.rs        # StegoError enum + `impl From<StegoError> for ApiError` (oracle-safe)
    ├── envelope.rs     # SVSTEG frame: build / parse / validate
    ├── capacity.rs     # required_sites(), max_plaintext_bytes(), fits() up-front validation
    ├── seal.rs         # `trait PayloadSealer` + in-crate `Argon2idSecretboxSealer` (reuses sv-crypto)
    ├── selector.rs     # `trait SiteSelector`: Sequential, PermutedSelector (BLAKE3 counter-mode seed)
    ├── embed.rs        # `trait Embedder` + LsbEmbedder (frame ↔ carrier sites)
    ├── carrier/
    │   ├── mod.rs      # `trait Carrier` (+ CarrierKind, is_jpeg format sniff)
    │   ├── spatial.rs  # SpatialCarrier (PNG/BMP) over `image`/`png`  ── Phase 1
    │   └── jpeg.rs     # JpegCarrier over `dct-io` (luma AC-coeff LSB)  ─ Phase 4 ✅
    └── detect/
        ├── mod.rs      # `trait Detector`, DetectionReport, format-dispatched panel + fusion
        ├── appended.rs # in-house "binwalk-lite" (PNG/BMP/JPEG logical-EOF)  ─ Phase 2 (+ JPEG EOI, Phase 4)
        ├── chi_square.rs   # spatial LSB chi-square (PNG/BMP)  ── Phase 2
        ├── jpeg_dct.rs     # DCT-coefficient LSB chi-square (JPEG)  ── Phase 4 ✅
        └── rs.rs           # RS analysis (PNG/BMP)  ── Phase 2
```

`Cargo.toml` dependency discipline (mirrors `crates/sv-platform/Cargo.toml`): **no** dependency on
`sv-core`, `sv-platform`, or `sv-age` — so `sv-stego` is **not vault-coupled**. It *does* depend on
`sv-crypto` to instantiate the in-crate `Argon2idSecretboxSealer` (Argon2id + `secretbox`), exactly as
`sv-platform` reuses `sv-crypto` for its Secret-Sharing engine — **reusing vetted primitives, not
introducing a new one**. The `PayloadSealer` trait remains the injection seam, so `sv-app` may still
substitute an implementation and tests inject a fast-parameter one.

> **Refinement vs. the original "ABI-only" sketch:** the first draft imagined the crypto impl arriving
> *only* at `sv-app`. Phase 1 must actually demonstrate encrypt-then-embed (round-trip + wrong-key +
> tamper), so the real sealer lives in-crate over `sv-crypto`. This is the same posture `sv-platform`
> already ships and keeps the peer-crate / no-new-primitive / not-vault-coupled invariants intact.

---

## 2. The SVSTEG envelope (the framed bytes embedded into carrier sites)

Fixed-layout header (54 bytes) + variable ciphertext. All multi-byte integers big-endian.

| Field | Bytes | Meaning |
|---|---|---|
| `magic` | 6 | ASCII `"SVSTEG"` |
| `version` | 1 | `0x01` |
| `flags` | 1 | bit0: carrier (0=spatial,1=jpeg); bit1: selector (0=seq,1=perm); bit2: bit-plane>0; rest reserved=0 |
| `kdf_alg` | 1 | `0x01` = Argon2id |
| `aead_alg` | 1 | `0x01` = XSalsa20-Poly1305 (`secretbox`) |
| `salt` | 16 | **public** per-image random — Argon2id salt **and** permutation-seed source |
| `nonce` | 24 | `secretbox` nonce (random) |
| `ct_len` | 4 | u32 length of `ciphertext` (incl. 16-byte Poly1305 tag) |
| `ciphertext` | `ct_len` | `secretbox_seal(key, nonce, plaintext)` |

**Placement:** the 54-byte header is written **sequentially** into the first `54·8 = 432` sites, so it
is recoverable *before* the permutation is known. The body (`ciphertext`) is written into the remaining
sites `[432 .. site_count)` in **`SiteSelector` order** (seeded permutation by default; seed =
`BLAKE3(salt)` — public, since placement is not a security boundary; see §6 rationale).

**`salt`/`nonce` are public framing, not secrets** — confidentiality is the AEAD over `key =
Argon2id(passphrase, salt)`. They are not DTO secrets and may appear in the stego file.

---

## 3. Encrypt-then-embed pipeline

### 3.1 Hide

```
stego_hide(cover_path, payload, output_path, passphrase, opts):
  1. bytes = read(cover_path); carrier = SpatialCarrier::decode(bytes)?      // not image → Malformed
  2. salt = random(16); nonce = random(24)                                   // getrandom
  3. key  = Argon2id(passphrase, salt, POLICY_FLOOR)         ┐ PayloadSealer.seal  (sv-crypto;
  4. ct   = secretbox_seal(key, nonce, payload); zeroize(key)┘ NO new primitive — confidentiality)
  5. frame = SVSTEG{ magic,version,flags,algs, salt, nonce, ct_len=len(ct) } ‖ ct
  6. required = 432 + len(ct)*8;  if required > carrier.site_count() → TooLarge{limit,actual}
  7. write frame.header bits 0..431 sequentially into carrier
  8. seed = BLAKE3(salt); perm = blake3_ctr_fisher_yates(sites[432..], seed)
     write ct bits into carrier in `perm` order   (or sequential if opts.selector == Sequential)
  9. out = carrier.serialize()?            // re-encode SAME format (PNG/BMP), lossless
 10. if exists(output_path) && !opts.allow_overwrite → OutputExists; else write(out)
 11. → StegoHideReport{ output_path, cover_format, payload_bytes, capacity_bytes, utilization_pct }
```

### 3.2 Extract (oracle-safe)

```
stego_extract(stego_path, output_path, passphrase):
  1. bytes = read(stego_path); carrier = SpatialCarrier::decode(bytes)?      // not image → Malformed
  2. header = read 432 bits sequentially; parse SVSTEG
       - bad magic OR unsupported flags/algs → Unauthorized   (DO NOT reveal "no payload here")
       - version unsupported               → IncompatibleVersion
  3. ct_len, salt, nonce from header
       - if 432 + ct_len*8 > site_count    → Unauthorized      (implausible length → treat as no-payload)
  4. seed = BLAKE3(salt); read ct_len bytes from sites[432..] in perm order → ct
  5. key = Argon2id(passphrase, salt); pt = secretbox_open(key, nonce, ct); zeroize(key)
       - AEAD open fails (wrong passphrase / tamper) → Unauthorized          (oracle-safe merge)
  6. if exists(output_path) && !allow_overwrite → OutputExists; else write(pt)
  7. → StegoExtractReport{ output_path, bytes_written }
```

**Oracle-safety rule (critical):** *every* "this image does not yield a payload for you" outcome —
no SVSTEG header, implausible length, **or** AEAD failure — collapses to the single
`SV-UNAUTHORIZED`. Only a genuinely un-decodable *image* (not about the secret) is `SV-MALFORMED`.
This prevents an attacker learning whether a given image carries an `sv-stego` payload. (Same
discipline as the vault unlock and Secret-Sharing recover paths.)

### 3.3 Detect

```
stego_detect(image_path):
  img = decode(image_path)?                                  // not image → Malformed
  signals = [ EmbeddedData(binwalk-scan), ChiSquare, SamplePair ].map(|d| d.analyze(img))   // bounded
  suspicion = fuse(signals)        // weighted; maps to NotObserved|Low|Elevated|High (never Clean)
  → StegoDetectReport{ suspicion, signals, caveat:"heuristic — absence of a signal is not proof" }
```

---

## 4. DTO definitions

All in `sv-types` (additive), `#[derive(Serialize/Deserialize)]`, `#[serde(rename_all="camelCase")]`.
**No DTO carries payload, key, or derived secret** — and unlike Secret Sharing there is **no**
`share_b64`-style exception (stego has no text-output workflow).

```rust
// ---- requests (cross the IPC boundary inbound) ----
struct StegoHideRequest {
    cover_path: String,
    payload_path: String,           // file to hide (kept off the DTO as bytes)
    output_path: String,
    passphrase: IpcPassphrase,      // zeroizing (existing type)
    options: StegoOptions,
}
struct StegoExtractRequest { stego_path: String, output_path: String, passphrase: IpcPassphrase }
struct StegoOptions { selector: SelectorKind /* Sequential|Random */, allow_overwrite: bool }

// ---- reports (outbound; secret-free) ----
struct StegoHideReport {
    output_path: String, cover_format: String /* "png"|"bmp" */,
    payload_bytes: u64, capacity_bytes: u64, utilization_pct: f32,
}
struct StegoExtractReport { output_path: String, bytes_written: u64 }

struct StegoDetectReport { suspicion: Suspicion, signals: Vec<StegoSignal>, caveat: String }
enum   Suspicion { NotObserved, Low, Elevated, High }      // NO "Clean"/"Safe" variant — by design
struct StegoSignal { name: String, score: f32 /* 0.0..1.0 */, detail: String }
```

---

## 5. Error model — `StegoError → ApiError`

`sv-stego/src/error.rs` defines `StegoError` and maps to the **existing** `ApiError` (no new code,
parity test stays green). Mirrors `crates/sv-platform/src/error.rs`.

| `StegoError` | → `ApiError` | code |
|---|---|---|
| `CoverUndecodable` / `UnsupportedCoverFormat` | `Malformed` | `SV-MALFORMED` |
| `CapacityExceeded { capacity, needed }` | `TooLarge { limit_bytes, actual_bytes }` | `SV-TOO-LARGE` |
| `NoPayload` / `BadFrame` / `AuthFailed` *(all merged)* | `Unauthorized` | `SV-UNAUTHORIZED` |
| `UnsupportedVersion` | `IncompatibleVersion { found, supported }` | `SV-INCOMPATIBLE-VERSION` |
| `OutputExists` | `OutputExists` | `SV-OUTPUT-EXISTS` |
| `Io(_)` | `ApiError::io_generic()` | `SV-IO` |
| `DetectorTimeout` | `Timeout` | `SV-TIMEOUT` |
| `InvalidOptions { detail }` | `InvalidInput { detail }` | `SV-INVALID-INPUT` |
| `Internal` | `Internal` | `SV-INTERNAL` |

The `NoPayload`/`BadFrame`/`AuthFailed` → single `Unauthorized` merge is the oracle-safety guarantee
and must be covered by a dedicated test (§6).

---

## 6. Testing strategy

| Layer | Tests |
|---|---|
| **Unit** | SVSTEG `build/parse` round-trip + rejection of truncated/!magic; capacity math (`capacity_bits`, `required_sites`); LSB `read_bit/write_bit`; selector permutation determinism (same seed ⇒ same order, disjoint from header sites) |
| **Randomized** (fixed-seed; no `proptest` dep) | a deterministic LCG sweep over (dims, format, payload, passphrase, selector): **embed→extract round-trips**; capacity boundary (`payload == capacity` ok, `+1` ⇒ `TooLarge`); **wrong passphrase ⇒ `Unauthorized`**; **single-bit tamper of stego ⇒ `Unauthorized`** (AEAD); non-image input ⇒ `Malformed`. (Hand-rolled with a fixed seed to keep the dependency tree minimal and the tests non-flaky.) |
| **Oracle-safety** | extract on {clean image, wrong key, tampered stego, truncated frame} ALL return `SV-UNAUTHORIZED` with no distinguishing message/variant; one test asserts the merge explicitly |
| **Detection** | known-positive corpus (images stego'd by `auyer`, `pnger`, **and our own embedder**) ⇒ detectors raise score; clean corpus ⇒ `NotObserved`/`Low` (never asserts "clean"); appended-data file ⇒ binwalk signal; agreement check vs **`zsteg`/`StegExpose` oracles** (dev/CI only, gated) |
| **No-secret-in-DTO** | a test serializes every report DTO and asserts no payload/key bytes appear (mirrors the spirit of the existing DTO discipline) |
| **Desktop parity** | the existing `ui_contract` test stays green **unchanged** — design adds no new `ApiError` code |

**Reference repos as oracles (not dependencies):** our envelope is *our own* (encrypt-then-embed), so
`auyer`/`pnger` cannot extract our output and vice-versa — **interop is a non-goal**. They serve to
(a) cross-check raw LSB mechanics and (b) generate positive samples for detector tests.

---

## 7. CI validation strategy

- **Automatic gate entry:** `sv-stego` is a workspace member ⇒ it joins `fmt --check`,
  `clippy --workspace -D warnings`, `build --workspace --locked`, `test --workspace --locked`, and
  `cargo deny check` across the **ubuntu/macos/windows** matrix + the **msrv 1.96** job, with **zero**
  workflow changes for Phases 1–3 (pure-Rust, no bundled runtime, no network). (CI is green and
  first-run-validated as of the prior cycle — see `docs/CI-VALIDATION.md`.)
- **`binwalk` supply-chain gate (Phase 2):** add it `default-features = false`; in CI assert via
  `cargo tree -p sv-stego` that **no** GPL CLI-wrapper crates and **no** entropy-plot/download path are
  pulled, and that `cargo deny` stays green (advisories + licenses + sources). If `binwalk`'s tree
  fails the gate, **drop the dependency** and re-implement the few magic-signature + Shannon-entropy
  checks in-house (small, public) — tracked fallback (§8).
- **Property tests** use fixed seeds (deterministic, non-flaky) and run inside the normal `test` gate.
- **Detection-oracle job (optional, non-gating):** a separate CI job installing `zsteg` (Ruby) /
  `StegExpose` (Java) to confirm detector agreement on a labelled corpus — modelled on the existing
  **`SV_AGE_BIN`-gated e2e** (kept off the blocking path).
- **Phase 4 (JPEG) — taken via `dct-io` (in-process), no subprocess:** because the JPEG carrier is a
  pure-Rust library dependency (not a bundled binary), it joins the **same** automatic gates as
  Phases 1–3 with **zero** workflow changes — no `SV_JSTEG_BIN` e2e, no `env_clear`/hash-pin/wall-clock
  harness, no bundled-binary signing burden. The only supply-chain delta is the `dct-io` crate itself,
  vetted by the existing `cargo deny` (advisories + licenses + sources) gate. (The `sv-age` subprocess
  pattern remains the template **if** a future adaptive-JPEG backend like `jsteg`/F5 is ever added.)

---

## 8. Phased delivery plan

| Phase | Status | Scope | Exit gate |
|---|---|---|---|
| **1 — Core (lossless hide/extract)** | ✅ **done** | `sv-stego` crate; `Carrier`/`Embedder`/`SiteSelector`/`PayloadSealer` traits; `SpatialCarrier` (PNG/BMP) over `image`; SVSTEG envelope (54-byte header → 432 sequential sites); **encrypt-then-embed** via in-crate Argon2id+`secretbox` sealer; capacity guard; unit + randomized + oracle-safety tests | full workspace gates green; round-trip + wrong-key + tamper + capacity tests pass |
| **2 — Detection** | ✅ **done** | `Detector` panel: **in-house** appended-data ("binwalk-lite": logical-EOF + entropy + magics) + chi-square (incomplete-gamma p-value) + RS analysis; `StegoDetectReport`; clean-vs-stego corpus tests | detectors flag positives, never assert "clean"; `cargo deny` green; **zero new deps** (binwalk fallback taken) |
| **3 — IPC + UI** | ✅ **done** | `sv-stego::io` file layer; `StegoSurface`/`StegoApp` in `src-tauri`; `StegoError→ApiError`; `StegoHideReport`/`StegoExtractReport`/`StegoDetectReport` DTOs in `sv-types`; third managed state; desktop `stego_hide`/`stego_extract`/`stego_detect` commands + Hide / Reveal / Detect UI screens; **`ui_contract` parity test unchanged + green** | oracle-safe errors verified (unit); desktop compiles + parity test passes; **manual GUI E2E still pending** |
| **4 — JPEG (DCT)** | ✅ **done** | `JpegCarrier` over `dct-io` (**in-process, pure-Rust** — chosen over a hash-pinned `jsteg` subprocess; see below); jsteg-rule LSB in luminance AC coefficients, lossless coefficient re-encode; pipeline dispatches on container format; JPEG detection panel (DCT-coefficient chi-square + `EOI`-trailer appended-data); UX flags JPEG detectability | JPEG round-trip (both selectors) + wrong-key + capacity; clean-vs-near-capacity DCT detection; full workspace gates green; **no new `ApiError` code → `ui_contract` still green** |

Phases 1–4 are implemented and gate-passing (the only item not machine-verified here is a manual GUI
walk-through, since the static frontend needs the running Tauri app). **Phase-4 backend decision
(`dct-io` vs `jsteg`):** the in-process `dct-io` crate won decisively over a bundled `jsteg`
subprocess — it slots into the existing `Carrier` trait so JPEG reuses the *exact* same SVSTEG
envelope, Argon2id+`secretbox` sealer, seeded-permutation selector, and oracle-safe error path
(whereas jsteg would fork all of that and add jsteg's own magic+length framing), it is permissive
(MIT OR Apache-2.0, in `cargo deny`'s allow-list), pulls zero production dependencies and is
`#![forbid(unsafe_code)]` + fuzzed, and it avoids adding an unsigned bundled binary to a product whose
distribution story (H5 signing/notarization) is already the blocker. JPEG embedding (LSB-in-DCT) is
inherently more detectable than lossless PNG/BMP LSB — the Hide UI says so and steers stealth-sensitive
users to PNG/BMP, and the new DCT chi-square detector flags near-capacity jsteg-style embedding.

**Phase-3 deviations from this design (reconciled):** the on-disk DTOs use **snake_case** serde (not
the `camelCase` the draft showed — matching the existing `sv-types` house style; Tauri converts JS
camelCase args automatically); selection is passed as a `randomize: bool` command arg rather than a
`StegoOptions` struct (mirrors `PlatformSurface`'s flat params); and overwrite is always refused
(no `allow_overwrite` flag) for parity with the Cryptography/Secret-Sharing commands' data-safety rule.

---

## 9. Assumptions, tradeoffs, and rejected alternatives

### Assumptions
1. **Image-only, PNG/BMP first** (owner-confirmed). JPEG is Phase 4; audio/text/network are out of scope.
2. Payloads fit in memory (consistent with the vault's current non-streaming H1 posture); large-file
   streaming is a later concern shared with H1.
3. The existing `sv-crypto` Argon2id + `secretbox` are the confidentiality primitives (already used by
   the Secret-Sharing engine to seal its DEK) — proven in-tree.

### Tradeoffs (chosen → rationale)
- **In-house pure-Rust LSB over the `image` crate** (vs. depending on `pnger` or sub-processing
  `auyer`): ~150 LOC, no new runtime/supply-chain/license risk, full control of the envelope and the
  oracle-safe error path. `pnger`/`auyer` remain **oracles**, not dependencies.
- **Randomized (seeded-permutation) placement by default**, sequential optional: spreads bits to reduce
  the most trivial sequential-LSB signatures. **Honest caveat:** placement is *not* a security boundary
  (the seed is public in the header); security is the AEAD only.
- **Public salt/permutation-seed in the header** (vs. deriving placement from the passphrase): keeps
  the confidentiality key and the placement schedule from sharing a secret, and lets extraction read
  the body without guessing. Placement secrecy buys nothing cryptographically.
- **No new `ApiError` code:** capacity → `TooLarge`, all extract failures → `Unauthorized`. Keeps the
  error taxonomy and the desktop parity test unchanged.
- **`binwalk` detection-only** (features stripped): gains embedded/appended-data detection without the
  GPL extraction CLIs or the build-time plot binary.

### Rejected alternatives
- **Trusting any tool's built-in crypto** (steghide unsalted-MD5, openstego DES, pnger XOR) — replaced
  by encrypt-then-embed with vetted primitives. *Non-negotiable for a security product.*
- **`stegano-rs`** (mature pure-Rust multi-media, would be ideal) — **GPL-3.0**, contagious for a
  permissive product. Rejected on license.
- **`openstego`/`ST3GG`/`stegcloak`** — heavy runtime (JRE/Python/Node) and/or AGPL; reject for an
  offline native app.
- **JPEG-LSB in spatial domain** — destroyed by JPEG re-quantization; JPEG needs DCT-domain (Phase 4).
- **ML steganalysis (Aletheia/StegoForge)** for detection — Python + model downloads, not offline-
  bundleable; kept as a dev oracle only.
- **Deriving the embedding key from the cover or filename** — no security value; the passphrase →
  Argon2id is the only key source.
- **Claiming undetectability / a "clean" verdict** — false assurance; the type system forbids it.

### Open risks (track, don't block)
- `binwalk` feature-split may not cleanly exclude the GPL/download paths → in-house signature+entropy
  fallback (small) is the contingency.
- Pure-Rust statistical steganalysis is heuristic and weaker than ML; we set expectations in the UI and
  validate against oracles rather than over-claim.
- Adaptive JPEG embedders (F5/J-UNIWARD) evade our LSB detectors; Phase 4 must say so explicitly.
