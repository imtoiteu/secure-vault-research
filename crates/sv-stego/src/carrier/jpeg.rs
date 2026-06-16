//! [`JpegCarrier`] — **JPEG (DCT-domain)** covers (Phase 4), with sites = the LSB of each *eligible*
//! luminance AC coefficient.
//!
//! ## Why this is not spatial-LSB-in-JPEG
//! JPEG is lossy: writing pixel LSBs and re-encoding would be destroyed by re-quantization. The only
//! place a JPEG can carry a bit losslessly is the **quantized DCT coefficient** itself, *before*
//! dequantization/IDCT, re-encoded with the original quantization + Huffman tables (entropy coding
//! only). [`dct_io`] is the in-process pure-Rust path to those coefficients (`read_coefficients` /
//! `write_coefficients`); we do not roll a JPEG entropy codec.
//!
//! ## Eligibility (the jsteg rule) — why the site set is stable across embed→extract
//! A site is the LSB of an AC coefficient `c` (zig-zag index `1..=63`, **DC excluded**) of the first
//! (**luminance**) component with `|c| >= 2`. Setting the LSB of such a coefficient maps its
//! magnitude within `{2,3}`, `{4,5}`, … — it can never reach `0` or `±1`. So the *set of eligible
//! positions* is identical before and after embedding, and extraction re-derives the exact same
//! ordered site list from the stego file. Coefficients with `|c| <= 1` are never touched (changing
//! them would shift zero-runs and desynchronize the schedule). Luminance-only matches the canonical
//! jsteg algorithm (and the DCT detector in [`crate::detect`] analyses the same component).
//!
//! Parity is sign-invariant (`-x` has the same LSB-parity as `x`), so [`Carrier::read_bit`] reads
//! `c & 1` directly for either sign. The carrier layer makes **no** secrecy claim; confidentiality
//! is the [`crate::seal`] layer over the cover.

use dct_io::{DctError, JpegCoefficients};

use crate::carrier::{Carrier, CarrierKind};
use crate::error::StegoError;

/// Zig-zag index of the DC coefficient (excluded — only AC coefficients carry bits).
const DC_INDEX: usize = 0;
/// A coefficient is an embedding site only if its absolute value is at least this (the jsteg rule:
/// skip `0` and `±1`, which keeps the eligible set invariant under LSB writes).
const MIN_ELIGIBLE_ABS: u16 = 2;

/// One embedding site = one eligible luminance AC coefficient, addressed by its block index (within
/// component 0) and zig-zag position. Compact (`u32 + u8`) so a large cover's site map stays small.
#[derive(Debug, Clone, Copy)]
struct CoeffSite {
    block: u32,
    zig: u8,
}

/// A decoded baseline JPEG exposing eligible luminance AC-coefficient LSBs as embedding sites.
///
/// Holds the original bytes (needed for the lossless [`Carrier::serialize`] re-encode), the decoded
/// quantized coefficients, and the precomputed ordered site map.
#[derive(Debug, Clone)]
pub struct JpegCarrier {
    /// The original JPEG bytes — passed back to `dct_io::write_coefficients` so all non-entropy
    /// segments (quantization/Huffman tables, APP markers) are preserved verbatim.
    original: Vec<u8>,
    /// Quantized DCT coefficients (mutated in place by [`Carrier::write_bit`]).
    coeffs: JpegCoefficients,
    /// Eligible sites in canonical (block, then zig-zag) order. `sites[i]` is site `i`.
    sites: Vec<CoeffSite>,
}

impl JpegCarrier {
    /// Decode `bytes` as a baseline JPEG and index its eligible luminance AC sites.
    ///
    /// - Not a JPEG / truncated / corrupt entropy / missing table → [`StegoError::CoverUndecodable`].
    /// - A JPEG using an unsupported feature (progressive, arithmetic, lossless) →
    ///   [`StegoError::UnsupportedCoverFormat`].
    ///
    /// Both map to `SV-MALFORMED` (a fact about the *file*, never an oracle about a secret).
    pub fn decode(bytes: &[u8]) -> Result<Self, StegoError> {
        let coeffs = dct_io::read_coefficients(bytes).map_err(map_read_err)?;
        let sites = build_sites(&coeffs);
        Ok(Self {
            original: bytes.to_vec(),
            coeffs,
            sites,
        })
    }

    /// Coefficient backing `site` (luminance component 0), as `(block, zig)`.
    #[inline]
    fn at(&self, site: usize) -> (usize, usize) {
        let s = self.sites[site];
        (s.block as usize, s.zig as usize)
    }
}

impl Carrier for JpegCarrier {
    fn site_count(&self) -> usize {
        self.sites.len()
    }

    fn read_bit(&self, site: usize) -> bool {
        let (block, zig) = self.at(site);
        // Parity is sign-invariant, so the raw coefficient's LSB is the magnitude's LSB.
        self.coeffs.components[0].blocks[block][zig] & 1 == 1
    }

    fn write_bit(&mut self, site: usize, value: bool) {
        let (block, zig) = self.at(site);
        let c = &mut self.coeffs.components[0].blocks[block][zig];
        // Set the LSB of the magnitude (preserving sign), so |c| stays >= 2 and the site remains
        // eligible. i32 intermediate avoids any negate-overflow at i16::MIN (unreachable for real
        // coefficients, but kept total).
        let neg = *c < 0;
        let mag = (i32::from(*c)).abs();
        let mag = (mag & !1) | i32::from(value);
        *c = if neg { -mag } else { mag } as i16;
    }

    fn serialize(&self) -> Result<Vec<u8>, StegoError> {
        // Re-encode entropy only; quantization/Huffman tables and markers come from `original`.
        // A failure here would be our own coefficient set being rejected → internal, not a file fact.
        dct_io::write_coefficients(&self.original, &self.coeffs).map_err(|_| StegoError::Internal)
    }

    fn format_name(&self) -> &'static str {
        "jpeg"
    }

    fn kind(&self) -> CarrierKind {
        CarrierKind::Jpeg
    }
}

/// Map a `dct_io` *read* failure to the oracle-neutral file-fact error (all → `SV-MALFORMED`).
fn map_read_err(e: DctError) -> StegoError {
    match e {
        // A feature we deliberately do not support (progressive/arithmetic/lossless) — distinct fact.
        DctError::Unsupported(_) => StegoError::UnsupportedCoverFormat,
        // Everything else is "this is not a (baseline) JPEG we can read".
        DctError::NotJpeg
        | DctError::Truncated
        | DctError::CorruptEntropy
        | DctError::Missing(_)
        | DctError::Incompatible(_) => StegoError::CoverUndecodable,
    }
}

/// Index the eligible luminance (component 0) AC-coefficient sites in canonical order.
fn build_sites(coeffs: &JpegCoefficients) -> Vec<CoeffSite> {
    let mut sites = Vec::new();
    let Some(luma) = coeffs.components.first() else {
        return sites;
    };
    for (block_idx, block) in luma.blocks.iter().enumerate() {
        // u32 is ample: the dct-io MCU cap bounds block counts well under u32::MAX.
        let Ok(block_u32) = u32::try_from(block_idx) else {
            break;
        };
        for (zig, &c) in block.iter().enumerate() {
            if zig == DC_INDEX {
                continue;
            }
            if c.unsigned_abs() >= MIN_ELIGIBLE_ABS {
                sites.push(CoeffSite {
                    block: block_u32,
                    zig: zig as u8,
                });
            }
        }
    }
    sites
}

#[cfg(test)]
mod tests {
    use super::*;

    /// A textured (high-frequency) baseline JPEG: noise gives many `|coeff| >= 2` AC coefficients,
    /// so the cover has real embedding capacity (a flat image would have almost none). Encoded with
    /// the same `ImageEncoder::write_image` path dct-io's own tests use.
    fn jpeg_cover(w: u32, h: u32, quality: u8) -> Vec<u8> {
        use image::{codecs::jpeg::JpegEncoder, ImageEncoder, RgbImage};
        let img = RgbImage::from_fn(w, h, |x, y| {
            let n =
                (x.wrapping_mul(131).wrapping_add(y.wrapping_mul(977)) ^ x.wrapping_mul(y)) as u8;
            image::Rgb([
                n,
                n.wrapping_mul(3).wrapping_add(7),
                n.wrapping_add(x as u8),
            ])
        });
        let mut buf = Vec::new();
        let enc = JpegEncoder::new_with_quality(&mut buf, quality);
        enc.write_image(img.as_raw(), w, h, image::ExtendedColorType::Rgb8)
            .unwrap();
        buf
    }

    #[test]
    fn decode_indexes_only_ac_luma_eligible_sites() {
        let bytes = jpeg_cover(64, 64, 90);
        let c = JpegCarrier::decode(&bytes).unwrap();
        assert_eq!(c.format_name(), "jpeg");
        assert_eq!(c.kind(), CarrierKind::Jpeg);
        assert!(c.site_count() > 0, "textured cover should expose sites");
        // No site addresses the DC coefficient.
        assert!(c.sites.iter().all(|s| s.zig as usize != DC_INDEX));
        // Every indexed coefficient is genuinely eligible (|c| >= 2).
        for s in &c.sites {
            let v = c.coeffs.components[0].blocks[s.block as usize][s.zig as usize];
            assert!(v.unsigned_abs() >= 2);
        }
    }

    #[test]
    fn lsb_write_read_survives_jpeg_reencode() {
        let bytes = jpeg_cover(96, 96, 90);
        let mut c = JpegCarrier::decode(&bytes).unwrap();
        let n = c.site_count().min(200);
        assert!(n >= 64, "need a few sites to test ({n})");
        let pattern: Vec<bool> = (0..n).map(|s| (s * 5 + 1) % 3 == 0).collect();
        for (s, &b) in pattern.iter().enumerate() {
            c.write_bit(s, b);
        }
        let reencoded = c.serialize().unwrap();
        // Re-decode the stego JPEG and confirm the eligible site map and the written bits survive.
        let c2 = JpegCarrier::decode(&reencoded).unwrap();
        assert_eq!(
            c2.site_count(),
            c.site_count(),
            "eligible set must be stable"
        );
        for (s, &b) in pattern.iter().enumerate() {
            assert_eq!(c2.read_bit(s), b, "site {s}");
        }
    }

    #[test]
    fn write_preserves_sign_and_eligibility() {
        // A coefficient stays |c| >= 2 (and keeps its sign) after either LSB value is written.
        let bytes = jpeg_cover(64, 64, 90);
        let mut c = JpegCarrier::decode(&bytes).unwrap();
        for s in 0..c.site_count().min(300) {
            let (b, z) = c.at(s);
            let before = c.coeffs.components[0].blocks[b][z];
            for v in [false, true] {
                c.write_bit(s, v);
                let after = c.coeffs.components[0].blocks[b][z];
                assert_eq!(after.signum(), before.signum(), "sign flipped at site {s}");
                assert!(after.unsigned_abs() >= 2, "became ineligible at site {s}");
                assert_eq!(after & 1 == 1, v, "LSB not set at site {s}");
            }
        }
    }

    #[test]
    fn non_jpeg_is_undecodable() {
        assert!(matches!(
            JpegCarrier::decode(b"not a jpeg at all"),
            Err(StegoError::CoverUndecodable)
        ));
    }
}
