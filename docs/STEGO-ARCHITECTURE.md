# Secure Vault — Steganography Module Architecture (`sv-stego`)

**Status:** Design only. **No implementation authorized or written.** Companion to
[STEGO-IMPLEMENTATION-DESIGN.md](STEGO-IMPLEMENTATION-DESIGN.md) (the "how") and the research evidence
in [`steganography/EVALUATION.md`](../../steganography/EVALUATION.md). Scope: **image covers only**
(PNG/BMP LSB first; JPEG DCT later).

This document defines *what* `sv-stego` is and *where* it sits. It preserves the existing Secure Vault
architecture patterns verbatim; every "mirror" below points at a real exemplar in the tree.

---

## 1. Position in the workspace — a peer domain crate, not vault-coupled

`sv-stego` is a **new peer domain crate**, structured exactly like `sv-core` (the vault) and
`sv-platform` (crypto-services): backend-free, generic over the shared trait ABI, with concrete
backends injected at the `sv-app` composition root. It does **not** depend on `sv-core`, and `sv-core`
does **not** depend on it.

```
            sv-crypto-traits  (ABI: traits + zeroizing value types — UNCHANGED)
                 ▲        ▲
   sv-crypto (impls) ─────┤        sv-types (DTOs + ApiError — +additive DTOs/errors only)
   sv-age   (impls) ──────┤             ▲
                 │         │             │
        ┌────────┴───┐  ┌──┴──────────┐  │
   sv-core (vault)   │  │ sv-platform │  │      ← existing peers (UNCHANGED)
        │            │  └─────────────┘  │
        │       ┌────┴───────────────────┴─┐
        │       │   sv-stego  (NEW peer)    │  depends on: sv-types + sv-crypto-traits + sv-crypto
        │       │   image (png/bmp)         │  (reuses Argon2id+secretbox; + image — pure-Rust). NOT
        │       └───────────┬───────────────┘  vault-coupled: no sv-core / sv-platform / sv-age dep.
        ▼                   ▼
   sv-app (src-tauri) ── composition root: injects sv-crypto/sv-age impls into sv-core, sv-platform,
        │                AND sv-stego (PayloadSealer); adds StegoSurface; maps StegoError → ApiError
        ▼
   desktop ── registers a managed Stego state + thin #[tauri::command] wrappers; "Hide & Detect" UI
```

**Mirror (verified exemplars):**
- *Backend-free domain crate depending only on `sv-types` + `sv-crypto-traits`* — `crates/sv-core/Cargo.toml`,
  `crates/sv-platform/Cargo.toml`. `sv-stego` copies this dependency discipline.
- *Impls injected at the root* — `src-tauri/src/platform.rs` (the `PlatformApp` holds `PlatformCrypto`)
  and the managed-state wiring in `src-tauri`. `sv-stego` gets the same treatment.
- *Additive-only `sv-types`* — `ShareSplitReport`/`RecoverReport` were added without touching existing
  DTOs; `sv-stego`'s DTOs are added the same way.

> **Why a peer crate, not a `sv-platform` sub-module?** `sv-platform` is *stateless file crypto-services*;
> steganography is a distinct domain (carriers, embedding, steganalysis) with its own traits and a
> pixel/coefficient data model. Keeping it a peer matches the "each new module is a peer domain crate"
> direction in `docs/ARCHITECTURE-AUDIT.md` and avoids bloating the platform layer. It **reuses** the
> platform's crypto for confidentiality (below), it does not fork it.

---

## 2. The governing principle — concealment ≠ confidentiality (encrypt-then-embed)

Every hide tool evaluated ships weak or no crypto (steghide unsalted-MD5; openstego static-salt/DES;
pnger XOR-obfuscation-only; auyer none). **`sv-stego` never relies on a carrier's crypto.** Two
strictly separated layers:

| Layer | Responsibility | Provided by | Security claim |
|---|---|---|---|
| **Confidentiality + integrity** | encrypt & authenticate the payload | **existing vetted crypto** — Argon2id KDF + XSalsa20-Poly1305 `secretbox` (the same primitives `sv-platform`'s Secret-Sharing engine already uses to seal its DEK) | **YES** — this is the security boundary |
| **Concealment** | hide ciphertext bytes in image LSBs/DCT coefficients | `sv-stego` carrier/embedder (pure-Rust) | **NONE** — an LSB/DCT codec makes no secrecy claim |

Consequences baked into the architecture:
- **No new cryptographic primitive is introduced.** `sv-stego` defines a `PayloadSealer` seam (§3)
  and ships its concrete `Argon2idSecretboxSealer` **in-crate over `sv-crypto`** (Argon2id +
  `secretbox`) — the same way `sv-platform` reuses `sv-crypto` for Secret-Sharing. (The seam is kept
  so `sv-app`/tests may substitute an implementation; the original "injected only at `sv-app`" sketch
  was relaxed so Phase 1 could actually exercise encrypt-then-embed.) The carrier code is
  non-cryptographic and is therefore allowed to live in-house (an LSB codec is not "rolling crypto").
- **Extraction is oracle-safe.** Recovery = de-embed → `secretbox::open`. A wrong passphrase, a tampered
  image, or *no payload at all* are indistinguishable from the outside — all collapse to
  `ApiError::Unauthorized` (`SV-UNAUTHORIZED`), exactly like the vault/Secret-Sharing recover paths.
- **Detection is honest.** Steganalysis is heuristic; the UI/report never says "clean" or "safe" (§5).

---

## 3. Trait hierarchy

All traits live in `sv-stego`; the crypto seam reuses `sv-crypto-traits`. Pseudocode (illustrative —
not final code):

```
// ---- concealment layer (pure-Rust, no security claim) ----------------------

/// An image cover viewed as an ordered sequence of mutable 1-bit "embedding sites".
/// Spatial carriers expose colour-sample LSBs; the JPEG carrier (Phase 4) exposes
/// eligible AC DCT-coefficient LSBs — the embedder is identical for both.
trait Carrier {
    fn site_count(&self) -> usize;              // total embeddable bits
    fn read_bit(&self, site: usize) -> bool;
    fn write_bit(&mut self, site: usize, b: bool);
    fn serialize(self) -> Result<Vec<u8>, StegoError>;   // back to PNG/BMP/JPEG bytes
}

/// Decides the order in which sites are written (sequential, or a seeded permutation).
trait SiteSelector {
    fn schedule(&self, site_count: usize, body_offset: usize) -> Vec<usize>;
}

/// Frames + writes / reads + unframes the bitstream over a Carrier via a SiteSelector.
trait Embedder {
    fn embed(&self, carrier: &mut dyn Carrier, framed: &[u8], sel: &dyn SiteSelector)
        -> Result<(), StegoError>;
    fn extract(&self, carrier: &dyn Carrier, sel: &dyn SiteSelector)
        -> Result<Vec<u8>, StegoError>;     // returns framed bytes (header still attached)
}

// ---- confidentiality seam (reuses existing vetted crypto; NO new primitive) -

/// Encrypt-then-embed boundary. Implemented at sv-app over sv-crypto:
/// seal = secretbox(key = Argon2id(passphrase, salt), nonce, plaintext).
trait PayloadSealer {
    fn seal(&self, passphrase: &IpcPassphrase, salt: &Salt, pt: &[u8])
        -> Result<Vec<u8>, StegoError>;     // returns nonce ‖ ciphertext+tag
    fn open(&self, passphrase: &IpcPassphrase, salt: &Salt, ct: &[u8])
        -> Result<Vec<u8>, StegoError>;     // AEAD failure -> oracle-safe error
}

// ---- detection layer (heuristic only) --------------------------------------

trait Detector {
    fn name(&self) -> &'static str;
    fn analyze(&self, image: &DecodedImage) -> Signal;   // {score 0..1, detail}
}
```

**Trait → existing pattern mapping:**

| `sv-stego` trait | Mirrors | Exemplar |
|---|---|---|
| `Carrier`/`Embedder`/`SiteSelector` | the "domain trait, impls injected" shape of the crypto traits | `crates/sv-crypto-traits/src/lib.rs` (Hasher/Kdf/FileCipher/…) |
| `PayloadSealer` | the `PayloadCipher` seam that confines the `age` backend to the root | `src-tauri/src/payload.rs` (`trait PayloadCipher`, `AgePayloadCipher`) |
| `Detector` panel | a small strategy set composed by the domain crate | `sv-platform` service decomposition |

`Salt`, `IpcPassphrase`, and the zeroizing value types come from the existing `sv-crypto-traits` /
`sv-types`; `sv-stego` introduces **no** new secret-bearing type.

---

## 4. Carrier abstraction model

The single abstraction that makes "PNG/BMP now, JPEG later" a *new Carrier* rather than a new module:

```
       cover bytes
           │  decode (image crate / png crate / dct-io)
           ▼
   ┌──────────────────────────────────────────────┐
   │ Carrier  =  ordered list of mutable 1-bit     │
   │            "embedding sites"                   │
   ├──────────────────────────────────────────────┤
   │ SpatialCarrier (Phase 1)                       │
   │   site = LSB of each R/G/B sample (skip alpha) │   PNG, BMP — lossless
   │   capacity_bits = W·H·channels(RGB)            │
   ├──────────────────────────────────────────────┤
   │ JpegCarrier (Phase 4 ✅, via dct-io)           │
   │   site = LSB of each *eligible* luminance AC   │   JPEG — lossy, in-process dct-io
   │   DCT coefficient (skip DC, skip |v|<2 —        │   (lossless coefficient re-encode)
   │   the jsteg rule, keeps the site set stable)   │
   └──────────────────────────────────────────────┘
           │  embedder writes framed bitstream over sites (in SiteSelector order)
           ▼  serialize
       stego bytes (re-encoded in the SAME container format)
```

Design choices (with rationale and the rejected alternative):
- **Skip the alpha channel** on spatial carriers — alpha LSB changes are unusually visible/contrived
  (auyer skips alpha too: `steganography.go` uses R/G/B only). *Rejected:* using alpha for +25% capacity.
- **Capacity is computed and checked up front** — `MaxEncodeSize`-style guard (auyer
  `steganography.go:218-223`). Embedding refuses if `framed_len > capacity` → `ApiError::TooLarge`.
- **Length-prefixed, validated frame** — never trust an extracted length blindly (auyer reads the
  4-byte length and then allocates; a crafted image could request a huge read). `sv-stego` validates
  the declared length against the carrier capacity *before* allocating (alloc-DoS guard).
- **Lossless first** — LSB only survives in lossless containers; JPEG requires DCT-domain embedding,
  hence the separate `JpegCarrier` (Phase 4 ✅, over the pure-Rust `dct-io`: embed in *quantized DCT
  coefficients*, re-encode entropy-only). *Rejected:* LSB-in-JPEG spatial domain (destroyed by re-quant).

---

## 5. Detection architecture

Detection is a **panel of independent heuristic `Detector`s** whose signals are fused into a
**suspicion level**, never a binary verdict. Two complementary regimes:

```
   image bytes
       │
       ├─► EmbeddedDataDetector   ── binwalk (scan-only): trailing/appended data after image EOF,
       │                              known-signature carving, Shannon entropy of regions
       │
       ├─► ChiSquareDetector      ── classic LSB chi-square attack on the pixel histogram
       ├─► SamplePairDetector     ── RS / sample-pair steganalysis (LSB-replacement estimate)
       │      (in-house; the published algorithms zsteg/StegExpose implement — NOT crypto)
       ▼
   DetectionReport {
     suspicion: NotObserved | Low | Elevated | High,   // NEVER "Clean"/"Safe"
     signals: [ { name, score 0..1, detail } ],
     caveat: "heuristic — absence of a signal is not proof of absence"
   }
```

- **Confidence/suspicion only.** Copy is fixed at the type level: the enum has no "Clean"/"Safe"
  variant; the lowest level is `NotObserved` ("no hidden data detected **by these tests**").
- **Detectors are pure-Rust + in-process** except `binwalk`, which is a crate dependency (§6).
- **Oracle validation, not shipped:** `zsteg` (Ruby), `StegExpose` (Java), `Aletheia` (Python) are run
  in **dev/CI** to validate our detectors' agreement on a labelled corpus; they are **never bundled**.

---

## 6. `binwalk` integration boundaries

`binwalk` v3 (Rust, MIT) is the one permissive, in-process detection dependency — but only a slice of
it is safe to consume. Hard boundaries:

| Allowed | Forbidden |
|---|---|
| The **detection/scan API only** (`Binwalk::scan`-style signature + entropy results) | The **extraction path** — it shells out to ~50 external (often GPL) CLIs |
| Consumed as a normal Cargo dependency | The **entropy-plot feature** — it downloads a binary at build time |
| Wrapped behind an `EmbeddedDataDetector` adapter in `sv-stego` | Auto-extraction of anything binwalk finds (we only *report*) |
| Run with a wall-clock bound on untrusted input | Passing user files to any external process |

Implementation note for the design: depend on `binwalk` with **`default-features = false`** and only
the scan feature(s) enabled; assert in CI (`cargo tree` / `cargo deny`) that no GPL CLI wrappers or
the plot/download path are pulled. If a clean feature split proves impossible, fall back to
re-implementing the handful of magic-signature + entropy checks we need (small, public) and drop the
dependency — recorded as a tracked risk in the implementation design.

---

## 7. IPC surface (overview; full contract in the implementation design)

Mirrors `PlatformSurface` exactly — session-free, coded errors, no secret in any DTO:

```
trait StegoSurface {                                   // additive to the command surface
    fn stego_hide(&self, req: StegoHideRequest)    -> Result<StegoHideReport,    ApiError>;
    fn stego_extract(&self, req: StegoExtractRequest) -> Result<StegoExtractReport, ApiError>;
    fn stego_detect(&self, image_path: String)     -> Result<StegoDetectReport,  ApiError>;
}
```

- `stego_hide` takes a zeroizing `IpcPassphrase`; `stego_extract` likewise. `stego_detect` takes no secret.
- `src-tauri` implements `StegoSurface`, mapping `StegoError → ApiError` (oracle-safe). `desktop`
  registers three thin `#[tauri::command]` wrappers in `generate_handler!` (snake_case Rust / camelCase JS),
  mirroring the Secret-Sharing commands added earlier this cycle.

---

## 8. Error model (overview; mapping in the implementation design)

**No new `ApiError` variant is required** — the existing 12 coded, oracle-safe variants cover stego:

| Condition | `ApiError` (existing code) |
|---|---|
| payload larger than cover capacity | `TooLarge { limit_bytes, actual_bytes }` (`SV-TOO-LARGE`) |
| wrong passphrase / tampered / **no payload found** | `Unauthorized` (`SV-UNAUTHORIZED`) — **merged, oracle-safe** |
| not a valid image / unsupported cover | `Malformed` (`SV-MALFORMED`) |
| unsupported stego envelope version | `IncompatibleVersion` (`SV-INCOMPATIBLE-VERSION`) |
| output file exists | `OutputExists` (`SV-OUTPUT-EXISTS`) |
| I/O / permission / disk | `Io` via `ApiError::io_generic()` (`SV-IO`) |
| detector wall-clock exceeded | `Timeout` (`SV-TIMEOUT`) |

Because no code is added, the desktop **`ui_contract` parity test stays green unchanged** (the
`MESSAGES` map already covers all 12 codes). This is a deliberate constraint, not a coincidence.

---

## 9. Architectural invariants (must hold)

1. `sv-stego` depends on `sv-types` + `sv-crypto-traits` + `sv-crypto` (+ pure-Rust `image`),
   mirroring `sv-platform` — **never** on `sv-core`, `sv-platform`, or `sv-age`, so it is not
   vault-coupled. Confidentiality reuses `sv-crypto`'s Argon2id + `secretbox` (no new primitive). The
   `PayloadSealer` trait stays as the seam for `sv-app`/test substitution; any Phase-4 subprocess
   backend (JPEG) is still injected at `sv-app`.
2. Confidentiality is **only** the `PayloadSealer` (in-crate `Argon2idSecretboxSealer`, Argon2id +
   `secretbox`); the carrier layer has zero security responsibility. No new cryptographic primitive anywhere.
3. Extraction failures are **oracle-safe** (single `SV-UNAUTHORIZED`).
4. No secret enters any DTO; passphrases are zeroizing `IpcPassphrase`.
5. Detection results are **heuristic suspicion**, type-level incapable of asserting "clean/safe".
6. `sv-stego` is a workspace member → it enters the existing CI gates (fmt/clippy `-D`/build
   `--locked`/test/deny) on every OS with no special handling; it stays **pure-Rust** (no bundled
   runtime, no network) so Phase 1–3 add no packaging burden.
