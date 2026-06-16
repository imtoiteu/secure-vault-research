//! **Chi-square LSB detector** (Westfeld–Pfitzmann). For each colour channel it tests whether the
//! "pairs of values" `(2k, 2k+1)` in the value histogram have become equal — the signature of LSB
//! replacement. The test statistic is converted to a **probability of embedding** via the
//! regularized incomplete gamma function (the chi-square upper-tail), exactly as `zsteg`/`StegExpose`
//! compute it. The score is the max probability across R/G/B.
//!
//! Strong on **high-rate** LSB embedding (sequential near-capacity, and the `auyer`/`pnger`-style
//! plaintext-LSB tools). A low-rate, permuted, encrypted payload barely perturbs the histogram and
//! will read low — reported honestly, never as "clean".
//!
//! **Known limitation (documented, not hidden):** smooth full-range gradients visit consecutive
//! integer values, which equalizes value-pairs and can read as a false positive. This is an inherent
//! weakness of the chi-square attack; the fused verdict is a *suspicion*, and the panel pairs it with
//! independent detectors so no single statistic is decisive.

use sv_types::StegoSignal;

use crate::detect::{DecodedImage, Detector};

/// Detects LSB-replacement via the histogram pair-equalization chi-square test.
#[derive(Debug, Default, Clone, Copy)]
pub struct ChiSquareDetector;

impl Detector for ChiSquareDetector {
    fn name(&self) -> &'static str {
        "chi-square"
    }

    fn analyze(&self, image: &DecodedImage) -> StegoSignal {
        let mut best: Option<(f64, usize)> = None;
        for ch in 0..3 {
            let mut hist = [0u64; 256];
            for v in image.channel_samples(ch) {
                hist[v as usize] += 1;
            }
            if let Some(p) = channel_embedding_probability(&hist) {
                if best.is_none_or(|(b, _)| p > b) {
                    best = Some((p, ch));
                }
            }
        }

        match best {
            Some((p, ch)) => StegoSignal {
                name: self.name().to_string(),
                score: p as f32,
                detail: format!(
                    "LSB chi-square p(embedding)={p:.2} (max over RGB; strongest on the {} channel)",
                    ["red", "green", "blue"][ch]
                ),
            },
            None => StegoSignal {
                name: self.name().to_string(),
                score: 0.0,
                detail: "too few populated histogram pairs for a chi-square test".into(),
            },
        }
    }
}

/// Probability that the histogram arose from LSB embedding (pair-equalization chi-square upper-tail),
/// or `None` if too few populated pairs. Shared with the JPEG DCT detector
/// ([`crate::detect::jpeg_dct`]), which feeds a coefficient-magnitude histogram with the
/// non-embeddable bins (`0`/`1`) left empty so the `sum == 0` pairs are skipped.
pub(crate) fn channel_embedding_probability(hist: &[u64; 256]) -> Option<f64> {
    let mut stat = 0.0_f64;
    let mut categories = 0usize;
    for k in 0..128 {
        let even = hist[2 * k];
        let odd = hist[2 * k + 1];
        let sum = even + odd;
        if sum == 0 {
            continue;
        }
        let expected = sum as f64 / 2.0;
        // Require an adequate expected count for the chi-square approximation to hold.
        if expected < 4.0 {
            continue;
        }
        let diff = even as f64 - expected;
        stat += diff * diff / expected;
        categories += 1;
    }
    if categories < 2 {
        return None;
    }
    let df = (categories - 1) as f64;
    // p(embedding) = upper-tail of chi-square = Q(df/2, stat/2): small stat (equal pairs) ⇒ ~1.
    Some(gammq(df / 2.0, stat / 2.0))
}

// --- Regularized incomplete gamma (Numerical Recipes; public-domain algorithm) --------------

/// Complement of the regularized lower incomplete gamma, `Q(a, x) = 1 - P(a, x)`.
fn gammq(a: f64, x: f64) -> f64 {
    1.0 - gammp(a, x)
}

/// Regularized lower incomplete gamma `P(a, x)` for `a > 0`, `x >= 0`.
fn gammp(a: f64, x: f64) -> f64 {
    if x <= 0.0 || a <= 0.0 {
        return 0.0;
    }
    if x < a + 1.0 {
        gser(a, x)
    } else {
        1.0 - gcf(a, x)
    }
}

/// Series expansion for `P(a, x)`, valid for `x < a + 1`.
fn gser(a: f64, x: f64) -> f64 {
    let gln = ln_gamma(a);
    let mut ap = a;
    let mut sum = 1.0 / a;
    let mut del = sum;
    for _ in 0..300 {
        ap += 1.0;
        del *= x / ap;
        sum += del;
        if del.abs() < sum.abs() * 1e-13 {
            break;
        }
    }
    (sum * (-x + a * x.ln() - gln).exp()).clamp(0.0, 1.0)
}

/// Continued-fraction expansion for `Q(a, x)`, valid for `x >= a + 1` (modified Lentz).
fn gcf(a: f64, x: f64) -> f64 {
    const TINY: f64 = 1e-300;
    let gln = ln_gamma(a);
    let mut b = x + 1.0 - a;
    let mut c = 1.0 / TINY;
    let mut d = 1.0 / b;
    let mut h = d;
    for i in 1..300 {
        let an = -(i as f64) * (i as f64 - a);
        b += 2.0;
        d = an * d + b;
        if d.abs() < TINY {
            d = TINY;
        }
        c = b + an / c;
        if c.abs() < TINY {
            c = TINY;
        }
        d = 1.0 / d;
        let del = d * c;
        h *= del;
        if (del - 1.0).abs() < 1e-13 {
            break;
        }
    }
    (h * (-x + a * x.ln() - gln).exp()).clamp(0.0, 1.0)
}

/// Natural log of the gamma function (Lanczos approximation, `g = 7`). Valid for `x > 0`.
// The coefficients are the canonical published Lanczos `g = 7, n = 9` set, quoted verbatim at full
// precision for traceability; the trailing digits exceed f64's mantissa (harmless, and rounding them
// would only obscure the source), so the precision lint is suppressed deliberately.
#[allow(clippy::excessive_precision)]
fn ln_gamma(x: f64) -> f64 {
    const C: [f64; 9] = [
        0.999_999_999_999_809_93,
        676.520_368_121_885_1,
        -1_259.139_216_722_402_8,
        771.323_428_777_653_13,
        -176.615_029_162_140_59,
        12.507_343_278_686_905,
        -0.138_571_095_265_720_12,
        9.984_369_578_019_572e-6,
        1.505_632_735_149_311_6e-7,
    ];
    const G: f64 = 7.0;
    let x = x - 1.0;
    let mut a = C[0];
    let t = x + G + 0.5;
    for (i, &c) in C.iter().enumerate().skip(1) {
        a += c / (x + i as f64);
    }
    0.5 * (2.0 * std::f64::consts::PI).ln() + (x + 0.5) * t.ln() - t + a.ln()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn gamma_matches_known_values() {
        // ln(Γ(n)) = ln((n-1)!): Γ(5) = 24.
        assert!((ln_gamma(5.0) - 24.0_f64.ln()).abs() < 1e-9);
        // Regularized P(1, x) = 1 - e^-x  (exponential CDF).
        assert!((gammp(1.0, 1.0) - (1.0 - (-1.0_f64).exp())).abs() < 1e-9);
        // P(a, 0) = 0, and Q is its complement.
        assert_eq!(gammp(3.0, 0.0), 0.0);
        assert!((gammq(3.0, 0.0) - 1.0).abs() < 1e-12);
    }

    #[test]
    fn equal_pairs_read_as_embedding_unequal_as_not() {
        // Equalized pairs (embedding signature) ⇒ tiny statistic ⇒ probability ≈ 1.
        let mut embedded = [0u64; 256];
        for k in 0..128 {
            embedded[2 * k] = 100;
            embedded[2 * k + 1] = 100;
        }
        let p_embedded = channel_embedding_probability(&embedded).unwrap();
        assert!(p_embedded > 0.9, "embedded p={p_embedded}");

        // Strongly unequal pairs (all weight on the even value) ⇒ large statistic ⇒ probability ≈ 0.
        let mut clean = [0u64; 256];
        for k in 0..128 {
            clean[2 * k] = 200;
            clean[2 * k + 1] = 0;
        }
        let p_clean = channel_embedding_probability(&clean).unwrap();
        assert!(p_clean < 0.05, "clean p={p_clean}");
    }
}
