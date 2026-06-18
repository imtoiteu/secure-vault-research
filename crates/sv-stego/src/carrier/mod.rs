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

use std::io::Cursor;

use image::{DynamicImage, ImageFormat};

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

/// Upper bound on decoded width/height (px). A cover this large is absurd for LSB stego; the cap
/// exists only to reject a decompression bomb, not to constrain legitimate use.
const MAX_DECODE_DIM: u32 = 30_000;
/// Upper bound on bytes the decoder may allocate. The 64 MiB file-size cap ([`crate::io`]) bounds the
/// *compressed* input, but a crafted PNG can inflate ~1000:1; without this guard an in-spec file
/// could decode to a multi-GiB RGBA8 buffer (OOM). Mirrors the bomb guards in `sv-qr`/`sv-watermark`.
const MAX_DECODE_ALLOC_BYTES: u64 = 1024 * 1024 * 1024;

/// Decode in-memory `bytes` of known `format` to a [`DynamicImage`] with explicit dimension and
/// allocation limits, so a highly-compressed cover within the file-size cap cannot expand to an
/// unbounded buffer. Any failure (including a limit breach) is the caller's to map to
/// [`StegoError::CoverUndecodable`] (`SV-MALFORMED` — a fact about the file, never an oracle).
pub(crate) fn decode_bounded(
    bytes: &[u8],
    format: ImageFormat,
) -> Result<DynamicImage, image::ImageError> {
    let mut reader = image::ImageReader::new(Cursor::new(bytes));
    reader.set_format(format);
    let mut limits = image::Limits::default();
    limits.max_image_width = Some(MAX_DECODE_DIM);
    limits.max_image_height = Some(MAX_DECODE_DIM);
    limits.max_alloc = Some(MAX_DECODE_ALLOC_BYTES);
    reader.limits(limits);
    reader.decode()
}
