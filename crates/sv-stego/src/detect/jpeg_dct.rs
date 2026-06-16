//! **JPEG DCT chi-square detector** (Phase 4) — the coefficient-domain analogue of the spatial
//! [`crate::detect::chi_square`]. It is the detector that actually flags jsteg-style embedding (what
//! [`crate::carrier::JpegCarrier`] produces): the spatial pixel statistics do **not** apply to JPEG,
//! because a JPEG's decompressed pixel LSBs are quantization artefacts, not the embedding domain.
//!
//! It builds the histogram of `|AC coefficient|` over the luminance component (the same component the
//! carrier embeds into) and runs the LSB pair-equalization chi-square on the embeddable pairs
//! `{2,3}, {4,5}, …`. Setting a coefficient's LSB equalizes the two halves of its pair, so a high
//! upper-tail probability is the signature of embedding. The non-embeddable values `0` and `±1` are
//! excluded (jsteg never touches them), so their pair contributes nothing to the test.
//!
//! **Honest scope.** Strong against high-rate LSB-in-AC embedding (near-capacity jsteg / our own
//! sequential output). A low-rate, permuted, encrypted payload barely perturbs the coefficient
//! histogram and reads low — reported as such, never as "clean". Adaptive embedders (F5 / J-UNIWARD)
//! evade this LSB test entirely.

use sv_types::StegoSignal;

use crate::detect::chi_square::channel_embedding_probability;

/// Detector display name.
const NAME: &str = "jpeg-dct-chi-square";

/// Analyse a JPEG's luminance AC-coefficient histogram for the LSB pair-equalization signature.
/// Never errors: a JPEG whose coefficients can't be read (e.g. progressive) yields a `0.0`
/// "not analysed" signal so the panel still reports the raw-byte [`super::appended`] result.
pub(crate) fn analyze(jpeg: &[u8]) -> StegoSignal {
    let Ok(coeffs) = dct_io::read_coefficients(jpeg) else {
        return signal(
            0.0,
            "JPEG coefficients could not be read; DCT test not run".into(),
        );
    };
    let Some(luma) = coeffs.components.first() else {
        return signal(0.0, "no luminance component; DCT test not run".into());
    };

    // Histogram of |AC coefficient| over luminance. Bins 0 and 1 are the non-embeddable values; left
    // empty, their pair (0,1) has sum 0 and is skipped, so only the embeddable pairs are tested.
    let mut hist = [0u64; 256];
    for block in &luma.blocks {
        for &c in &block[1..] {
            // skip DC (zig-zag index 0)
            let m = c.unsigned_abs();
            if (2..=255).contains(&m) {
                hist[m as usize] += 1;
            }
        }
    }

    match channel_embedding_probability(&hist) {
        Some(p) => signal(
            p as f32,
            format!("luminance AC-coefficient LSB chi-square p(embedding)={p:.2}"),
        ),
        None => signal(
            0.0,
            "too few populated coefficient-value pairs for a chi-square test".into(),
        ),
    }
}

fn signal(score: f32, detail: String) -> StegoSignal {
    StegoSignal {
        name: NAME.to_string(),
        score,
        detail,
    }
}
