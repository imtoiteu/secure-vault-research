//! The **carrier** abstraction: an image cover viewed as an ordered sequence of mutable 1-bit
//! "embedding sites". This is the single seam that makes "PNG/BMP now, JPEG later" a matter of a
//! *new `Carrier`*, not a new module — the [`crate::embed::Embedder`] and
//! [`crate::selector::SiteSelector`] are identical across carriers.
//!
//! The carrier layer is **purely non-cryptographic** and makes no secrecy claim (see
//! [`crate::seal`] for where confidentiality actually lives).

pub mod jpeg;
pub mod spatial;

pub use jpeg::JpegCarrier;
pub use spatial::SpatialCarrier;

use crate::error::StegoError;

/// Which family of cover a carrier embeds into. Recorded in the SVSTEG header's carrier flag
/// (see [`crate::envelope`]) and used to pick the right decoder on extract.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CarrierKind {
    /// Lossless spatial LSB (PNG/BMP) — [`SpatialCarrier`].
    Spatial,
    /// Lossy JPEG DCT-coefficient LSB — [`JpegCarrier`] (Phase 4).
    Jpeg,
}

/// An image cover as an ordered list of mutable 1-bit embedding sites.
pub trait Carrier {
    /// Total number of embeddable sites (one bit each).
    fn site_count(&self) -> usize;

    /// The current bit at `site`. Callers stay within `0..site_count()`.
    fn read_bit(&self, site: usize) -> bool;

    /// Set the bit at `site`. Callers stay within `0..site_count()`.
    fn write_bit(&mut self, site: usize, value: bool);

    /// Re-encode the (possibly modified) carrier back to its **original** container format,
    /// losslessly. `&self` so it is callable through a `&dyn Carrier`.
    fn serialize(&self) -> Result<Vec<u8>, StegoError>;

    /// Short lowercase container name for non-secret reports (`"png"` / `"bmp"` / `"jpeg"`).
    fn format_name(&self) -> &'static str;

    /// The carrier family, written into the SVSTEG header's carrier flag on hide.
    fn kind(&self) -> CarrierKind;
}

/// True if `bytes` begins with the JPEG Start-Of-Image marker (`FF D8 FF`). Codec-independent magic
/// sniff used to route between the spatial ([`SpatialCarrier`]) and JPEG ([`JpegCarrier`]) decoders
/// without decoding the file.
#[must_use]
pub fn is_jpeg(bytes: &[u8]) -> bool {
    bytes.starts_with(&[0xFF, 0xD8, 0xFF])
}
