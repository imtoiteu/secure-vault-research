//! [`SpatialCarrier`] — lossless **PNG/BMP** covers, with sites = the LSB of each R/G/B colour
//! sample (the alpha channel is **skipped**: alpha LSB changes are unusually conspicuous, and
//! `auyer/steganography` skips alpha for the same reason).
//!
//! The cover is decoded to an in-memory RGBA8 buffer and re-encoded in its original container
//! format on [`Carrier::serialize`]. LSB embedding only survives lossless containers — JPEG is a
//! separate `JpegCarrier` (Phase 4), never spatial-LSB-in-JPEG.

use std::io::Cursor;

use image::{DynamicImage, ImageFormat, RgbaImage};

use crate::carrier::{Carrier, CarrierKind};
use crate::error::StegoError;

/// Bytes per pixel in the working RGBA8 buffer.
const CHANNELS_PER_PIXEL: usize = 4;
/// Colour channels actually used as sites (R, G, B); alpha (index 3) is skipped.
const EMBED_CHANNELS: usize = 3;

/// A decoded PNG/BMP cover exposing R/G/B sample LSBs as embedding sites.
#[derive(Debug, Clone)]
pub struct SpatialCarrier {
    /// The original container format (`Png` or `Bmp`); preserved on re-encode.
    format: ImageFormat,
    width: u32,
    height: u32,
    /// RGBA8 samples, length `width * height * CHANNELS_PER_PIXEL`.
    pixels: Vec<u8>,
}

impl SpatialCarrier {
    /// Decode `bytes` as a lossless PNG/BMP cover.
    ///
    /// - Not a decodable image at all → [`StegoError::CoverUndecodable`].
    /// - A decodable image in an unsupported (lossy/other) container → [`StegoError::UnsupportedCoverFormat`].
    ///
    /// Both map to `SV-MALFORMED` (a fact about the *file*, never an oracle about a secret).
    pub fn decode(bytes: &[u8]) -> Result<Self, StegoError> {
        let format = image::guess_format(bytes).map_err(|_| StegoError::CoverUndecodable)?;
        match format {
            ImageFormat::Png | ImageFormat::Bmp => {}
            _ => return Err(StegoError::UnsupportedCoverFormat),
        }
        let img = image::load_from_memory_with_format(bytes, format)
            .map_err(|_| StegoError::CoverUndecodable)?;
        let rgba = img.to_rgba8();
        let (width, height) = rgba.dimensions();
        Ok(Self {
            format,
            width,
            height,
            pixels: rgba.into_raw(),
        })
    }

    /// Byte offset of the colour sample backing `site` (skips the alpha lane).
    #[inline]
    fn byte_offset(site: usize) -> usize {
        let pixel = site / EMBED_CHANNELS;
        let channel = site % EMBED_CHANNELS;
        pixel * CHANNELS_PER_PIXEL + channel
    }
}

impl Carrier for SpatialCarrier {
    fn site_count(&self) -> usize {
        (self.pixels.len() / CHANNELS_PER_PIXEL) * EMBED_CHANNELS
    }

    fn read_bit(&self, site: usize) -> bool {
        self.pixels[Self::byte_offset(site)] & 1 == 1
    }

    fn write_bit(&mut self, site: usize, value: bool) {
        let off = Self::byte_offset(site);
        self.pixels[off] = (self.pixels[off] & !1) | u8::from(value);
    }

    fn serialize(&self) -> Result<Vec<u8>, StegoError> {
        let img = RgbaImage::from_raw(self.width, self.height, self.pixels.clone())
            .ok_or(StegoError::Internal)?;
        let mut cursor = Cursor::new(Vec::new());
        DynamicImage::ImageRgba8(img)
            .write_to(&mut cursor, self.format)
            .map_err(|e| StegoError::Io(e.to_string()))?;
        Ok(cursor.into_inner())
    }

    fn format_name(&self) -> &'static str {
        match self.format {
            ImageFormat::Png => "png",
            ImageFormat::Bmp => "bmp",
            _ => "unknown", // unreachable: `decode` admits only Png/Bmp
        }
    }

    fn kind(&self) -> CarrierKind {
        CarrierKind::Spatial
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn gradient(w: u32, h: u32) -> RgbaImage {
        let mut img = RgbaImage::new(w, h);
        for (x, y, px) in img.enumerate_pixels_mut() {
            *px = image::Rgba([
                (x.wrapping_mul(7)) as u8,
                (y.wrapping_mul(13)) as u8,
                (x.wrapping_add(y).wrapping_mul(3)) as u8,
                255,
            ]);
        }
        img
    }

    fn encode(img: &RgbaImage, format: ImageFormat) -> Vec<u8> {
        let mut cursor = Cursor::new(Vec::new());
        DynamicImage::ImageRgba8(img.clone())
            .write_to(&mut cursor, format)
            .unwrap();
        cursor.into_inner()
    }

    #[test]
    fn site_count_is_three_per_pixel() {
        let bytes = encode(&gradient(10, 4), ImageFormat::Png);
        let c = SpatialCarrier::decode(&bytes).unwrap();
        assert_eq!(c.site_count(), 10 * 4 * EMBED_CHANNELS);
        assert_eq!(c.format_name(), "png");
    }

    #[test]
    fn lsb_write_read_survives_png_and_bmp_reencode() {
        for format in [ImageFormat::Png, ImageFormat::Bmp] {
            let bytes = encode(&gradient(8, 8), format);
            let mut c = SpatialCarrier::decode(&bytes).unwrap();
            // Flip a pattern across the first 64 sites.
            for s in 0..64 {
                c.write_bit(s, s % 3 == 0);
            }
            let reencoded = c.serialize().unwrap();
            let c2 = SpatialCarrier::decode(&reencoded).unwrap();
            for s in 0..64 {
                assert_eq!(c2.read_bit(s), s % 3 == 0, "site {s} format {format:?}");
            }
        }
    }

    #[test]
    fn byte_offset_skips_alpha() {
        // Sites 0,1,2 are R,G,B of pixel 0; site 3 is R of pixel 1 (alpha at byte 3 is never a site).
        assert_eq!(SpatialCarrier::byte_offset(0), 0);
        assert_eq!(SpatialCarrier::byte_offset(1), 1);
        assert_eq!(SpatialCarrier::byte_offset(2), 2);
        assert_eq!(SpatialCarrier::byte_offset(3), 4); // pixel 1, channel R
    }

    #[test]
    fn non_image_is_undecodable() {
        assert!(matches!(
            SpatialCarrier::decode(b"definitely not an image"),
            Err(StegoError::CoverUndecodable)
        ));
    }
}
