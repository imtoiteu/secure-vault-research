//! **RS detector** (Fridrich–Goljan–Du, "Regular/Singular" steganalysis). Pixels are grouped, a
//! discrimination function measures each group's roughness, and a flipping mask (`F1` / `F−1`) is
//! applied: groups whose roughness *increases* are **Regular**, those that *decrease* are
//! **Singular**. For a cover image the mask and its negation behave symmetrically
//! (`R_M ≈ R_{−M}`, `S_M ≈ S_{−M}`); LSB embedding breaks that symmetry, and the separation grows
//! with the embedding rate.
//!
//! The group classification is exact; the mapping from the four R/S fractions to a `[0,1]` score is
//! an explicitly **heuristic** asymmetry measure (this layer only ever produces a *suspicion*, not an
//! embedding-rate estimate). It is calibrated and regression-guarded by a clean-vs-fully-embedded
//! test below.

use sv_types::StegoSignal;

use crate::detect::{clamp01, DecodedImage, Detector};

/// Pixels per discrimination group (a short horizontal run within one channel/row).
const GROUP: usize = 4;
/// Flipping mask: apply `F1` at the ends, leave the middle (`-M` negates these to `F−1`).
const MASK: [i32; GROUP] = [1, 0, 0, 1];
/// Scales the raw R/S asymmetry into the reported `[0,1]` band (calibrated by the tests below).
const SCALE: f32 = 3.0;

/// Detects LSB embedding via the asymmetry of regular/singular group counts under `M` vs `−M`.
#[derive(Debug, Default, Clone, Copy)]
pub struct RsDetector;

impl Detector for RsDetector {
    fn name(&self) -> &'static str {
        "rs-analysis"
    }

    fn analyze(&self, image: &DecodedImage) -> StegoSignal {
        match rs_fractions(image) {
            Some(rs) => {
                let asym = (rs.r_m - rs.r_neg).abs() + (rs.s_m - rs.s_neg).abs();
                StegoSignal {
                    name: self.name().to_string(),
                    score: clamp01(SCALE * asym as f32),
                    detail: format!(
                        "RS asymmetry {asym:.3} (R_M={:.3}/R_-M={:.3}, S_M={:.3}/S_-M={:.3})",
                        rs.r_m, rs.r_neg, rs.s_m, rs.s_neg
                    ),
                }
            }
            None => StegoSignal {
                name: self.name().to_string(),
                score: 0.0,
                detail: "image too small for RS group analysis".into(),
            },
        }
    }
}

/// Regular/Singular fractions (of usable groups) under mask `M` and its negation `−M`.
#[derive(Debug, Clone, Copy)]
struct RsFractions {
    r_m: f64,
    s_m: f64,
    r_neg: f64,
    s_neg: f64,
}

fn rs_fractions(image: &DecodedImage) -> Option<RsFractions> {
    let (w, h) = (image.width as usize, image.height as usize);
    if w < GROUP || h == 0 {
        return None;
    }
    let neg_mask = [-MASK[0], -MASK[1], -MASK[2], -MASK[3]];
    let (mut rm, mut sm, mut rnm, mut snm, mut total) = (0u64, 0u64, 0u64, 0u64, 0u64);

    for ch in 0..3 {
        for y in 0..h {
            let row = y * w;
            let mut x = 0;
            while x + GROUP <= w {
                let mut g = [0i32; GROUP];
                for (i, slot) in g.iter_mut().enumerate() {
                    *slot = i32::from(image.rgba[(row + x + i) * 4 + ch]);
                }
                let f = variation(&g);
                let f_m = variation(&apply_mask(&g, &MASK));
                let f_neg = variation(&apply_mask(&g, &neg_mask));
                match f_m.cmp(&f) {
                    std::cmp::Ordering::Greater => rm += 1,
                    std::cmp::Ordering::Less => sm += 1,
                    std::cmp::Ordering::Equal => {}
                }
                match f_neg.cmp(&f) {
                    std::cmp::Ordering::Greater => rnm += 1,
                    std::cmp::Ordering::Less => snm += 1,
                    std::cmp::Ordering::Equal => {}
                }
                total += 1;
                x += GROUP;
            }
        }
    }
    if total == 0 {
        return None;
    }
    let t = total as f64;
    Some(RsFractions {
        r_m: rm as f64 / t,
        s_m: sm as f64 / t,
        r_neg: rnm as f64 / t,
        s_neg: snm as f64 / t,
    })
}

/// Discrimination function: total absolute variation within a group (higher = rougher).
fn variation(g: &[i32; GROUP]) -> i32 {
    (g[0] - g[1]).abs() + (g[1] - g[2]).abs() + (g[2] - g[3]).abs()
}

/// LSB flip (`F1`): 0↔1, 2↔3, …
fn f1(x: i32) -> i32 {
    x ^ 1
}

/// Dual flip (`F−1`): −1↔0, 1↔2, 3↔4, … (boundary values may step just outside `[0,255]`, which is
/// the known, benign RS boundary effect; `i32` keeps the variation well-defined).
fn f_neg1(x: i32) -> i32 {
    ((x + 1) ^ 1) - 1
}

fn apply_mask(g: &[i32; GROUP], mask: &[i32; GROUP]) -> [i32; GROUP] {
    let mut out = *g;
    for (slot, &m) in out.iter_mut().zip(mask.iter()) {
        *slot = match m {
            1 => f1(*slot),
            -1 => f_neg1(*slot),
            _ => *slot,
        };
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;
    use image::{DynamicImage, ImageFormat, RgbaImage};
    use std::io::Cursor;

    /// A smooth, textured cover (structured LSBs → low RS asymmetry).
    fn clean_cover(w: u32, h: u32) -> Vec<u8> {
        let mut img = RgbaImage::new(w, h);
        for (x, y, px) in img.enumerate_pixels_mut() {
            // Gentle ramps keep neighbouring samples correlated (cover-like).
            let r = ((x * 3 + y) % 200) as u8;
            let g = ((y * 2 + x / 2) % 200) as u8;
            let b = ((x + y) % 200) as u8;
            *px = image::Rgba([r, g, b, 255]);
        }
        let mut cur = Cursor::new(Vec::new());
        DynamicImage::ImageRgba8(img)
            .write_to(&mut cur, ImageFormat::Png)
            .unwrap();
        cur.into_inner()
    }

    /// The same cover with every R/G/B LSB overwritten by a pseudo-random bit (rate-1 LSB embed).
    fn fully_embedded(clean_png: &[u8]) -> DecodedImage {
        let mut img = DecodedImage::decode(clean_png).unwrap();
        let mut state: u64 = 0xDEAD_BEEF_1234_5678;
        for (i, byte) in img.rgba.iter_mut().enumerate() {
            if i % 4 == 3 {
                continue; // leave alpha
            }
            state = state.wrapping_mul(6364136223846793005).wrapping_add(1);
            let bit = ((state >> 33) & 1) as u8;
            *byte = (*byte & !1) | bit;
        }
        img
    }

    #[test]
    fn embedding_raises_rs_asymmetry_above_clean() {
        let png = clean_cover(96, 96);
        let clean = DecodedImage::decode(&png).unwrap();

        let clean_sig = RsDetector.analyze(&clean);
        let stego_sig = RsDetector.analyze(&fully_embedded(&png));

        // Full embedding must score clearly higher than the cover, and reach at least the "Low" band.
        assert!(
            stego_sig.score > clean_sig.score + 0.1,
            "stego {} should exceed clean {} by a margin",
            stego_sig.score,
            clean_sig.score
        );
        assert!(stego_sig.score >= 0.20, "stego score {}", stego_sig.score);
        assert!(clean_sig.score < 0.20, "clean score {}", clean_sig.score);
    }
}
