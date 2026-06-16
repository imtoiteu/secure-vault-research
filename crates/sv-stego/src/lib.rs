//! # sv-stego — steganography domain crate (Phase 1: lossless image hide/extract)
//!
//! A **peer domain crate** (structured like `sv-core` and `sv-platform`): it reuses the shared
//! cryptographic platform but is **not** vault-coupled — it does not depend on `sv-core`/`sv-age`,
//! and nothing in the vault depends on it.
//!
//! ## The governing principle — concealment ≠ confidentiality (encrypt-then-embed)
//! Two strictly separated layers:
//! - **Confidentiality + integrity** — the payload is encrypted and authenticated by the *existing
//!   vetted* `sv-crypto` primitives (Argon2id KDF + XSalsa20-Poly1305 `secretbox`), the same pair
//!   `sv-platform`'s Secret-Sharing engine uses. This is the **only** security boundary. **No new
//!   cryptographic primitive is introduced.** See [`seal`].
//! - **Concealment** — ciphertext bits are hidden in image-sample LSBs by the pure-Rust
//!   [`carrier`]/[`embed`] layer, which makes **no** secrecy claim.
//!
//! ## Consequences baked in
//! - **Extraction is oracle-safe.** A clean image, a wrong passphrase, a tampered carrier, and a
//!   truncated frame are indistinguishable — all collapse to `ApiError::Unauthorized`
//!   (`SV-UNAUTHORIZED`). See [`error`].
//! - **No secret enters a return value** beyond the recovered payload the caller asked for; the
//!   Argon2id key is a zeroizing `Key32` that never escapes [`seal`].
//! - **Scope: image covers only.** Lossless **PNG/BMP** spatial LSB ([`SpatialCarrier`]); **JPEG**
//!   DCT-coefficient LSB ([`JpegCarrier`], Phase 4, over the pure-Rust `dct-io` crate — concealment
//!   in the *quantized DCT coefficients*, re-encoded losslessly, never spatial-LSB-in-JPEG). The
//!   pipeline dispatches on container format; `JpegCarrier` reuses the same envelope, sealer, and
//!   oracle-safe error path. The `StegoSurface` IPC + UI are Phase 3.
//!
//! ## Phase 1 surface
//! [`hide`] and [`extract`] operate on in-memory bytes with an injected [`PayloadSealer`]
//! (production: [`Argon2idSecretboxSealer`]). File I/O, the zeroizing `IpcPassphrase`, and the IPC
//! contract are deliberately deferred to Phase 3.
//!
//! ## Phase 2 surface — detection ([`detect`])
//! [`detect`] runs a panel of **heuristic** steganalysis detectors and fuses them into a
//! `sv_types::Suspicion` level (`NotObserved`/`Low`/`Elevated`/`High`) — it **never** asserts an
//! image is clean. The detectors are pure-Rust and in-process.
//!
//! **Why not the `binwalk` crate?** The design evaluated `binwalk` v3 (Rust, MIT) for appended-data
//! detection but pre-authorized an in-house fallback if a clean feature split couldn't exclude its
//! GPL CLI-wrappers / build-time download path. To keep the dependency tree minimal, fully offline,
//! and trivially `cargo deny`-clean, this build takes that fallback: [`detect::appended`] is a small,
//! self-contained "binwalk-lite" (logical-EOF + entropy + magic-signature scan, **report-only, never
//! carves**). No new dependency was added for Phase 2.

#![forbid(unsafe_code)]

pub mod capacity;
pub mod carrier;
pub mod detect;
pub mod embed;
pub mod envelope;
pub mod error;
pub mod io;
pub mod pipeline;
pub mod seal;
pub mod selector;

pub use carrier::{Carrier, CarrierKind, JpegCarrier, SpatialCarrier};
pub use detect::{detect, DecodedImage, Detector};
pub use embed::{Embedder, LsbEmbedder};
pub use error::StegoError;
pub use io::{detect_file, extract_file, hide_file};
pub use pipeline::{extract, hide, HideOptions};
pub use seal::{Argon2idSecretboxSealer, PayloadSealer, Sealed};
pub use selector::{PermutedSelector, SelectorKind, SequentialSelector, SiteSelector};
