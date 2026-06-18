//! **Detection** (Phase 2) — a panel of independent **heuristic** steganalysis detectors whose
//! signals are fused into a [`Suspicion`] level. By design this layer **never** asserts an image is
//! "clean": the lowest level is [`Suspicion::NotObserved`] ("nothing detected *by these tests*").
//!
//! Two complementary regimes (mirrors `docs/STEGO-ARCHITECTURE.md` §5):
//! - [`appended::AppendedDataDetector`] — raw-byte analysis: data trailing the image's logical EOF,
//!   its Shannon entropy, and embedded-file magic signatures (an in-house "binwalk-lite"; see the
//!   note in `lib.rs` on why `binwalk` itself is not a dependency).
//! - [`chi_square::ChiSquareDetector`] and [`rs::RsDetector`] — classic LSB steganalysis on the
//!   decoded pixels (the published statistics that `zsteg`/`StegExpose` implement — not crypto).
//!
//! **Honest scope.** These reliably flag *naive, high-rate* LSB/append steganography (the kind
//! `auyer`/`pnger`/“append a zip to a PNG” produce, and our own near-capacity sequential output).
//! A *low-rate, encrypted, permuted* `sv-stego` payload is close to undetectable by them — which is
//! the truth, and exactly why the verdict is a suspicion, not a guarantee.

pub mod appended;
pub mod chi_square;
pub mod jpeg_dct;
pub mod rs;

use image::ImageFormat;
use sv_types::{StegoDetectReport, StegoSignal, Suspicion};

use crate::carrier::{decode_bounded, is_jpeg};
use crate::error::StegoError;

/// The standing caveat attached to every report.
pub const CAVEAT: &str =
    "Heuristic steganalysis: a raised suspicion is not proof, and the absence of a signal is not \
     proof of absence.";

/// A decoded image plus its original bytes — the shared input to every detector. The raw bytes feed
/// container-level detectors ([`appended`]); the RGBA pixels feed statistical detectors.
#[derive(Debug, Clone)]
pub struct DecodedImage {
    /// Original file bytes (for trailing-data / container analysis).
    pub raw: Vec<u8>,
    /// Container format (`Png`/`Bmp`).
    pub format: ImageFormat,
    pub width: u32,
    pub height: u32,
    /// Decoded RGBA8 samples, length `width * height * 4`.
    pub rgba: Vec<u8>,
}

impl DecodedImage {
    /// Decode `bytes` as a lossless PNG/BMP image. Not decodable / unsupported →
    /// [`StegoError::CoverUndecodable`]/[`StegoError::UnsupportedCoverFormat`] (both `SV-MALFORMED`).
    pub fn decode(bytes: &[u8]) -> Result<Self, StegoError> {
        let format = image::guess_format(bytes).map_err(|_| StegoError::CoverUndecodable)?;
        match format {
            ImageFormat::Png | ImageFormat::Bmp => {}
            _ => return Err(StegoError::UnsupportedCoverFormat),
        }
        let img = decode_bounded(bytes, format).map_err(|_| StegoError::CoverUndecodable)?;
        let rgba_img = img.to_rgba8();
        let (width, height) = rgba_img.dimensions();
        Ok(Self {
            raw: bytes.to_vec(),
            format,
            width,
            height,
            rgba: rgba_img.into_raw(),
        })
    }

    /// Iterate the value of one colour channel (`0=R,1=G,2=B`) over every pixel, skipping alpha.
    pub(crate) fn channel_samples(&self, channel: usize) -> impl Iterator<Item = u8> + '_ {
        self.rgba.chunks_exact(4).map(move |px| px[channel])
    }
}

/// A heuristic steganalysis detector. `analyze` returns a non-secret [`StegoSignal`] with a score in
/// `[0.0, 1.0]` (higher = more suspicious).
pub trait Detector {
    fn name(&self) -> &'static str;
    fn analyze(&self, image: &DecodedImage) -> StegoSignal;
}

/// Run the detector panel matching `image_bytes`' container format and fuse the signals into a
/// [`StegoDetectReport`]. JPEG covers take a coefficient-domain panel (the spatial pixel statistics
/// are meaningless for JPEG); PNG/BMP covers take the spatial panel.
pub fn detect(image_bytes: &[u8]) -> Result<StegoDetectReport, StegoError> {
    if is_jpeg(image_bytes) {
        detect_jpeg(image_bytes)
    } else {
        detect_spatial(image_bytes)
    }
}

/// Spatial panel (PNG/BMP): raw-byte appended-data + LSB chi-square + RS analysis over decoded pixels.
fn detect_spatial(image_bytes: &[u8]) -> Result<StegoDetectReport, StegoError> {
    let image = DecodedImage::decode(image_bytes)?;
    let detectors: [&dyn Detector; 3] = [
        &appended::AppendedDataDetector,
        &chi_square::ChiSquareDetector,
        &rs::RsDetector,
    ];
    let signals: Vec<StegoSignal> = detectors.iter().map(|d| d.analyze(&image)).collect();
    Ok(report(signals))
}

/// JPEG panel: raw-byte appended-data (data trailing the `EOI` marker) + DCT-coefficient LSB
/// chi-square (the detector that flags jsteg-style / [`crate::carrier::JpegCarrier`] embedding). The
/// spatial pixel detectors are deliberately not run — a JPEG's decompressed LSBs are quantization
/// artefacts, not the embedding domain. Never hard-errors on an unreadable JPEG: each detector
/// degrades to a `0.0` "not analysed" signal, so a trailing-data find still surfaces.
fn detect_jpeg(image_bytes: &[u8]) -> Result<StegoDetectReport, StegoError> {
    let signals = vec![
        appended::jpeg_appended_signal(image_bytes),
        jpeg_dct::analyze(image_bytes),
    ];
    Ok(report(signals))
}

/// Build a fused report from a panel's signals (shared by both panels).
fn report(signals: Vec<StegoSignal>) -> StegoDetectReport {
    StegoDetectReport {
        suspicion: fuse(&signals),
        signals,
        caveat: CAVEAT.to_string(),
    }
}

/// Fuse per-detector scores into a suspicion level. The verdict is driven by the **strongest**
/// signal (any one detector firing is enough to warrant a closer look); thresholds are intentionally
/// conservative. Never returns "Clean" — the floor is [`Suspicion::NotObserved`].
fn fuse(signals: &[StegoSignal]) -> Suspicion {
    let max = signals.iter().map(|s| s.score).fold(0.0_f32, f32::max);
    if max >= 0.75 {
        Suspicion::High
    } else if max >= 0.45 {
        Suspicion::Elevated
    } else if max >= 0.20 {
        Suspicion::Low
    } else {
        Suspicion::NotObserved
    }
}

/// Clamp a raw score to the reported `[0.0, 1.0]` range.
pub(crate) fn clamp01(x: f32) -> f32 {
    x.clamp(0.0, 1.0)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fuse_maps_strongest_signal_to_levels_and_never_clean() {
        let sig = |score: f32| StegoSignal {
            name: "x".into(),
            score,
            detail: String::new(),
        };
        assert_eq!(fuse(&[sig(0.0), sig(0.1)]), Suspicion::NotObserved);
        assert_eq!(fuse(&[sig(0.3), sig(0.1)]), Suspicion::Low);
        assert_eq!(fuse(&[sig(0.5)]), Suspicion::Elevated);
        assert_eq!(fuse(&[sig(0.2), sig(0.9)]), Suspicion::High);
    }

    #[test]
    fn decode_rejects_non_image() {
        assert!(matches!(
            DecodedImage::decode(b"not an image"),
            Err(StegoError::CoverUndecodable)
        ));
    }

    // ---- panel-level corpus tests ----------------------------------------

    use image::{DynamicImage, RgbaImage};
    use std::io::Cursor;

    fn clean_png(w: u32, h: u32) -> Vec<u8> {
        // Blocky constant-colour regions (a cartoon/screenshot-like cover): the value histogram is
        // spiky and its value-pairs are strongly *uneven*, so the LSB statistics read low — unlike a
        // smooth full-range ramp, which is the known chi-square false-positive case.
        const COLORS: [[u8; 3]; 4] = [[40, 80, 120], [200, 60, 30], [14, 160, 90], [100, 100, 210]];
        let mut img = RgbaImage::new(w, h);
        for (x, y, px) in img.enumerate_pixels_mut() {
            let c = COLORS[((x / 16 + y / 16) % 4) as usize];
            *px = image::Rgba([c[0], c[1], c[2], 255]);
        }
        let mut cur = Cursor::new(Vec::new());
        DynamicImage::ImageRgba8(img)
            .write_to(&mut cur, ImageFormat::Png)
            .unwrap();
        cur.into_inner()
    }

    #[test]
    fn clean_cover_is_not_observed_or_low_never_high() {
        let report = detect(&clean_png(96, 96)).unwrap();
        assert!(
            matches!(report.suspicion, Suspicion::NotObserved | Suspicion::Low),
            "clean cover suspicion was {:?} (signals: {:?})",
            report.suspicion,
            report.signals
        );
        // The report must never claim the image is clean — only ever a suspicion level + caveat.
        assert!(report.caveat.to_lowercase().contains("not proof"));
    }

    #[test]
    fn appended_payload_raises_high_suspicion() {
        let mut bytes = clean_png(64, 64);
        bytes.extend_from_slice(b"PK\x03\x04 hidden archive contents here ...");
        let report = detect(&bytes).unwrap();
        assert_eq!(report.suspicion, Suspicion::High);
    }

    /// A textured cover whose channel values are all **even** (LSB plane all-zero). Clean, every
    /// detector reads ~0 (the chi-square sees maximally *uneven* value-pairs; RS sees a flat LSB
    /// plane). Near-capacity embedding randomizes the whole LSB plane, which RS analysis flags
    /// strongly and *deterministically* — the property this test pins. (Locally-correlated ramps,
    /// like the RS detector's own fixture, but with the LSB cleared so the chi-square also reads
    /// clean — a smooth full-range ramp would be the chi-square false-positive case.)
    fn detectable_cover(w: u32, h: u32) -> Vec<u8> {
        let mut img = RgbaImage::new(w, h);
        for (x, y, px) in img.enumerate_pixels_mut() {
            let r = (((x * 3 + y) % 200) as u8) & 0xFE;
            let g = (((y * 2 + x / 2) % 200) as u8) & 0xFE;
            let b = (((x + y) % 200) as u8) & 0xFE;
            *px = image::Rgba([r, g, b, 255]);
        }
        let mut cur = Cursor::new(Vec::new());
        DynamicImage::ImageRgba8(img)
            .write_to(&mut cur, ImageFormat::Png)
            .unwrap();
        cur.into_inner()
    }

    #[test]
    fn our_own_near_capacity_sequential_embed_is_detected() {
        use crate::seal::testing::fast_sealer;
        use crate::{capacity, hide, Carrier, HideOptions, SelectorKind, SpatialCarrier};

        let cover = detectable_cover(96, 96);
        let clean = detect(&cover).unwrap();

        let site_count = SpatialCarrier::decode(&cover).unwrap().site_count();
        let cap = capacity::max_plaintext_bytes(site_count);
        // Fill the cover to capacity with sequential placement (worst case for stealth).
        let payload: Vec<u8> = (0..cap).map(|i| (i * 7 + 1) as u8).collect();
        let opts = HideOptions {
            selector: SelectorKind::Sequential,
        };
        let stego = hide(&cover, &payload, b"pw", &opts, &fast_sealer()).unwrap();
        let report = detect(&stego).unwrap();

        let rs = |r: &StegoDetectReport| {
            r.signals
                .iter()
                .find(|s| s.name == "rs-analysis")
                .map_or(0.0, |s| s.score)
        };
        // The clean all-even cover reads NotObserved; the near-capacity embed is unmistakably flagged
        // (never "clean"). RS analysis is the sound full-rate detector — its asymmetry rises sharply
        // once the LSB plane is randomized, *deterministically*. The chi-square is deliberately NOT
        // pinned here: at embedding rate 1 its Westfeld p-value is ~uniform (the statistic equals its
        // dof), so a hard per-run threshold on it would be flaky by construction — the equalized-pairs
        // case is covered deterministically by chi_square's own unit test instead.
        assert_eq!(clean.suspicion, Suspicion::NotObserved);
        assert_ne!(
            report.suspicion,
            Suspicion::NotObserved,
            "near-capacity stego was not flagged (signals: {:?})",
            report.signals
        );
        assert!(
            rs(&report) > rs(&clean) + 0.2,
            "RS asymmetry should rise sharply: clean {} → stego {}",
            rs(&clean),
            rs(&report)
        );
        assert!(rs(&report) >= 0.20, "RS stego score {}", rs(&report));
    }

    // ---- JPEG panel tests -------------------------------------------------

    fn encode_jpeg(img: &image::RgbImage, quality: u8) -> Vec<u8> {
        use image::{codecs::jpeg::JpegEncoder, ImageEncoder};
        let mut buf = Vec::new();
        let enc = JpegEncoder::new_with_quality(&mut buf, quality);
        enc.write_image(
            img.as_raw(),
            img.width(),
            img.height(),
            image::ExtendedColorType::Rgb8,
        )
        .unwrap();
        buf
    }

    /// A smooth (low-AC-energy) baseline JPEG: its coefficient histogram is steeply decreasing, so
    /// the DCT chi-square reads low — the clean-JPEG counterpart to `clean_png`.
    fn smooth_jpeg(w: u32, h: u32) -> Vec<u8> {
        let mut img = image::RgbImage::new(w, h);
        for (x, y, px) in img.enumerate_pixels_mut() {
            let v = ((x * 200) / w) as u8;
            *px = image::Rgb([v, v.wrapping_add((y * 40 / h) as u8), 128]);
        }
        encode_jpeg(&img, 85)
    }

    /// A textured (high-AC-energy) baseline JPEG with genuine embedding capacity.
    fn noisy_jpeg(w: u32, h: u32) -> Vec<u8> {
        let mut img = image::RgbImage::new(w, h);
        for (x, y, px) in img.enumerate_pixels_mut() {
            let n =
                (x.wrapping_mul(131).wrapping_add(y.wrapping_mul(977)) ^ x.wrapping_mul(y)) as u8;
            *px = image::Rgb([
                n,
                n.wrapping_mul(3).wrapping_add(7),
                n.wrapping_add(x as u8),
            ]);
        }
        encode_jpeg(&img, 90)
    }

    #[test]
    fn clean_jpeg_takes_the_jpeg_panel_and_reads_low() {
        let report = detect(&smooth_jpeg(96, 96)).unwrap();
        assert!(
            matches!(report.suspicion, Suspicion::NotObserved | Suspicion::Low),
            "clean jpeg suspicion was {:?} (signals: {:?})",
            report.suspicion,
            report.signals
        );
        // The JPEG panel ran (DCT + appended), not the spatial one.
        assert_eq!(report.signals.len(), 2);
        assert!(report
            .signals
            .iter()
            .any(|s| s.name == "jpeg-dct-chi-square"));
        assert!(report.signals.iter().any(|s| s.name == "appended-data"));
        assert!(report.caveat.to_lowercase().contains("not proof"));
    }

    #[test]
    fn appended_data_after_jpeg_eoi_is_high() {
        let mut bytes = smooth_jpeg(64, 64);
        bytes.extend_from_slice(b"PK\x03\x04 a hidden archive smuggled after the JPEG EOI ...");
        assert_eq!(detect(&bytes).unwrap().suspicion, Suspicion::High);
    }

    #[test]
    fn our_own_near_capacity_jpeg_embed_is_detected() {
        use crate::seal::testing::fast_sealer;
        use crate::{capacity, carrier::JpegCarrier, hide, Carrier, HideOptions, SelectorKind};

        let cover = noisy_jpeg(128, 128);
        let cap = capacity::max_plaintext_bytes(JpegCarrier::decode(&cover).unwrap().site_count());
        assert!(cap > 32, "noisy jpeg should have capacity (cap {cap})");
        // Fill to capacity with sequential placement (worst case for stealth) — this randomizes the
        // LSBs of essentially every eligible AC coefficient, equalizing the value-pair histogram.
        let payload: Vec<u8> = (0..cap).map(|i| (i * 7 + 1) as u8).collect();
        let opts = HideOptions {
            selector: SelectorKind::Sequential,
        };
        let stego = hide(&cover, &payload, b"pw", &opts, &fast_sealer()).unwrap();

        let report = detect(&stego).unwrap();
        assert!(
            matches!(report.suspicion, Suspicion::Elevated | Suspicion::High),
            "near-capacity jpeg stego suspicion was {:?} (signals: {:?})",
            report.suspicion,
            report.signals
        );
        let dct = report
            .signals
            .iter()
            .find(|s| s.name == "jpeg-dct-chi-square")
            .unwrap();
        assert!(dct.score > 0.45, "jpeg dct chi-square score {}", dct.score);
    }
}
