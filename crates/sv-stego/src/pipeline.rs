//! The **encrypt-then-embed** orchestration: `hide` and `extract`.
//!
//! These operate on in-memory bytes (cover image → stego image; stego image → recovered payload).
//! File I/O, the zeroizing `IpcPassphrase`, and the `StegoSurface` IPC contract are Phase 3 concerns
//! layered at `sv-app`; Phase 1 keeps the codec pure and directly testable.
//!
//! Layering (the security boundary is step 2, never the carrier):
//! 1. decode the cover into a [`SpatialCarrier`] and check capacity up front;
//! 2. **seal** the payload with the injected [`PayloadSealer`] (Argon2id + `secretbox`);
//! 3. frame it as an [`crate::envelope`] SVSTEG header + ciphertext;
//! 4. embed the header sequentially and the body in [`SiteSelector`] order;
//! 5. re-encode losslessly.

use sv_crypto_traits::Salt;

use crate::capacity;
use crate::carrier::{is_jpeg, Carrier, JpegCarrier, SpatialCarrier};
use crate::embed::{Embedder, LsbEmbedder};
use crate::envelope::{self, HEADER_LEN};
use crate::error::StegoError;
use crate::seal::PayloadSealer;
use crate::selector::{PermutedSelector, SelectorKind, SequentialSelector, SiteSelector};

/// Options controlling how a payload is hidden. The default uses a seeded **permutation** to spread
/// body bits (blunting the most trivial sequential-LSB signatures — *not* a security property).
#[derive(Debug, Clone, Copy)]
pub struct HideOptions {
    pub selector: SelectorKind,
}

impl Default for HideOptions {
    fn default() -> Self {
        Self {
            selector: SelectorKind::Permuted,
        }
    }
}

fn random_salt() -> Result<Salt, StegoError> {
    let mut salt = [0u8; 16];
    getrandom::getrandom(&mut salt).map_err(|_| StegoError::Internal)?;
    Ok(Salt(salt))
}

fn body_selector(kind: SelectorKind, salt: &Salt) -> Box<dyn SiteSelector> {
    match kind {
        SelectorKind::Sequential => Box::new(SequentialSelector),
        SelectorKind::Permuted => Box::new(PermutedSelector::from_salt(salt)),
    }
}

fn header_site_list() -> Vec<usize> {
    (0..capacity::HEADER_SITES).collect()
}

/// Decode `bytes` into the carrier matching its container format: JPEG (`FF D8 FF`) → DCT-coefficient
/// [`JpegCarrier`]; otherwise the lossless [`SpatialCarrier`] (PNG/BMP). The whole pipeline then runs
/// against `&dyn Carrier`, so hide/extract are carrier-agnostic. A non-image / unsupported file
/// surfaces as `SV-MALFORMED` from the chosen decoder (a fact about the file, never a secret oracle).
fn decode_carrier(bytes: &[u8]) -> Result<Box<dyn Carrier>, StegoError> {
    if is_jpeg(bytes) {
        Ok(Box::new(JpegCarrier::decode(bytes)?))
    } else {
        Ok(Box::new(SpatialCarrier::decode(bytes)?))
    }
}

/// **Hide** `payload` inside `cover_bytes`, returning the re-encoded stego image (same container
/// format). Refuses an over-capacity payload *before* doing any (expensive) key derivation.
///
/// `passphrase` is raw bytes (the IPC layer holds the zeroizing wrapper). `sealer` is injected so
/// `sv-app` supplies the production [`crate::Argon2idSecretboxSealer`] and tests a fast one.
pub fn hide(
    cover_bytes: &[u8],
    payload: &[u8],
    passphrase: &[u8],
    opts: &HideOptions,
    sealer: &dyn PayloadSealer,
) -> Result<Vec<u8>, StegoError> {
    hide_detailed(cover_bytes, payload, passphrase, opts, sealer).map(|(bytes, _)| bytes)
}

/// Non-secret metadata about a completed hide, for building a report (see [`hide_detailed`]).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct HideMeta {
    /// Cover container format (`"png"` / `"bmp"`).
    pub cover_format: &'static str,
    /// Maximum payload the cover could hold, in bytes.
    pub capacity_bytes: u64,
    /// Size of the payload that was hidden, in bytes.
    pub payload_bytes: u64,
}

/// Like [`hide`], but also returns non-secret [`HideMeta`] (cover format + capacity) so a caller can
/// build a report without re-decoding the cover.
pub fn hide_detailed(
    cover_bytes: &[u8],
    payload: &[u8],
    passphrase: &[u8],
    opts: &HideOptions,
    sealer: &dyn PayloadSealer,
) -> Result<(Vec<u8>, HideMeta), StegoError> {
    let mut carrier = decode_carrier(cover_bytes)?;
    let cover_format = carrier.format_name();
    let carrier_kind = carrier.kind();
    let site_count = carrier.site_count();
    let capacity_bytes = capacity::max_plaintext_bytes(site_count) as u64;

    // Up-front capacity guard (whole frame: header + tag + body), before any Argon2id work.
    if !capacity::fits(site_count, payload.len()) {
        return Err(StegoError::CapacityExceeded {
            capacity: capacity_bytes,
            needed: payload.len() as u64,
        });
    }

    let salt = random_salt()?;
    let sealed = sealer.seal(passphrase, &salt, payload)?;
    let ct_len = u32::try_from(sealed.ciphertext.len()).map_err(|_| StegoError::Internal)?;

    let header = envelope::build_header(carrier_kind, opts.selector, &salt, &sealed.nonce, ct_len);
    let embedder = LsbEmbedder;
    embedder.write_bits(&mut *carrier, &header_site_list(), &header)?;

    let selector = body_selector(opts.selector, &salt);
    let body_sites = selector.schedule(
        site_count,
        capacity::HEADER_SITES,
        sealed.ciphertext.len() * 8,
    );
    embedder.write_bits(&mut *carrier, &body_sites, &sealed.ciphertext)?;

    let bytes = carrier.serialize()?;
    Ok((
        bytes,
        HideMeta {
            cover_format,
            capacity_bytes,
            payload_bytes: payload.len() as u64,
        },
    ))
}

/// **Extract** a payload hidden by [`hide`] from `stego_bytes`.
///
/// Oracle-safe: a clean image, a wrong passphrase, a tampered carrier, and a truncated/implausible
/// frame all return one of [`StegoError::NoPayload`]/[`StegoError::BadFrame`]/[`StegoError::AuthFailed`],
/// which collapse to the single `SV-UNAUTHORIZED`. Only an undecodable *image* is `SV-MALFORMED`.
pub fn extract(
    stego_bytes: &[u8],
    passphrase: &[u8],
    sealer: &dyn PayloadSealer,
) -> Result<Vec<u8>, StegoError> {
    let carrier = decode_carrier(stego_bytes)?;
    let site_count = carrier.site_count();
    // Too small to even hold a header → "no payload" (oracle-safe), not a parse error.
    if site_count < capacity::HEADER_SITES {
        return Err(StegoError::NoPayload);
    }

    let embedder = LsbEmbedder;
    let header_bytes = embedder.read_bits(&*carrier, &header_site_list(), HEADER_LEN)?;
    let header = envelope::parse_header(&header_bytes)?;

    // A declared length that cannot fit the carrier is implausible → treat as no payload.
    if capacity::required_sites(header.ct_len) > site_count {
        return Err(StegoError::NoPayload);
    }

    let selector = body_selector(header.selector, &header.salt);
    let body_sites = selector.schedule(
        site_count,
        capacity::HEADER_SITES,
        header.ct_len as usize * 8,
    );
    let ciphertext = embedder.read_bits(&*carrier, &body_sites, header.ct_len as usize)?;

    sealer.open(passphrase, &header.salt, &header.nonce, &ciphertext)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::seal::testing::fast_sealer;
    use image::{DynamicImage, ImageFormat, RgbaImage};
    use std::io::Cursor;
    use sv_types::ApiError;

    fn cover(w: u32, h: u32, format: ImageFormat) -> Vec<u8> {
        let mut img = RgbaImage::new(w, h);
        for (x, y, px) in img.enumerate_pixels_mut() {
            *px = image::Rgba([
                (x.wrapping_mul(31).wrapping_add(y)) as u8,
                (y.wrapping_mul(17)) as u8,
                (x ^ y) as u8,
                255,
            ]);
        }
        let mut cursor = Cursor::new(Vec::new());
        DynamicImage::ImageRgba8(img)
            .write_to(&mut cursor, format)
            .unwrap();
        cursor.into_inner()
    }

    /// Flip one carrier bit at `site` (decode → invert → re-encode): a single-bit carrier tamper.
    /// NB: under *permuted* placement only `ct_len*8` of the body sites are actually used and are
    /// scattered across the whole body, so a fixed site is rarely a used one — tamper tests pick a
    /// site they know is used (the first body site under sequential placement, or a header site).
    fn flip_site(stego: &[u8], site: usize) -> Vec<u8> {
        let mut c = SpatialCarrier::decode(stego).unwrap();
        c.write_bit(site, !c.read_bit(site));
        c.serialize().unwrap()
    }

    /// A textured baseline JPEG cover with genuine capacity (noise → many `|coeff| >= 2` ACs; a flat
    /// JPEG would carry almost nothing). Encoded via the `image` jpeg *dev*-dependency.
    fn jpeg_cover(w: u32, h: u32) -> Vec<u8> {
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
        let enc = JpegEncoder::new_with_quality(&mut buf, 90);
        enc.write_image(img.as_raw(), w, h, image::ExtendedColorType::Rgb8)
            .unwrap();
        buf
    }

    #[test]
    fn round_trips_jpeg_with_both_selectors() {
        use crate::carrier::{is_jpeg, JpegCarrier};
        let sealer = fast_sealer();
        let cover = jpeg_cover(96, 96);
        assert!(is_jpeg(&cover));
        let cap = capacity::max_plaintext_bytes(JpegCarrier::decode(&cover).unwrap().site_count());
        assert!(
            cap >= 16,
            "textured jpeg should carry a small payload (cap {cap})"
        );
        let payload = b"jpeg dct carrier secret";
        assert!(payload.len() <= cap);
        for selector in [SelectorKind::Sequential, SelectorKind::Permuted] {
            let opts = HideOptions { selector };
            let stego = hide(&cover, payload, b"pw", &opts, &sealer).unwrap();
            // The stego artifact is itself a valid JPEG (DCT-domain embed, re-encoded losslessly).
            assert!(
                is_jpeg(&stego),
                "stego output must be a JPEG (selector {selector:?})"
            );
            let out = extract(&stego, b"pw", &sealer).unwrap();
            assert_eq!(out, payload, "selector {selector:?}");
        }
    }

    #[test]
    fn jpeg_wrong_passphrase_is_unauthorized() {
        let sealer = fast_sealer();
        let cover = jpeg_cover(96, 96);
        let stego = hide(
            &cover,
            b"meet at dawn",
            b"right",
            &HideOptions::default(),
            &sealer,
        )
        .unwrap();
        let err = extract(&stego, b"wrong", &sealer).unwrap_err();
        assert!(matches!(err, StegoError::AuthFailed));
        assert_eq!(ApiError::from(err), ApiError::Unauthorized);
    }

    #[test]
    fn jpeg_capacity_exceeded_is_too_large() {
        use crate::carrier::JpegCarrier;
        let sealer = fast_sealer();
        let cover = jpeg_cover(64, 64);
        let cap = capacity::max_plaintext_bytes(JpegCarrier::decode(&cover).unwrap().site_count());
        let over = vec![0x5Au8; cap + 1];
        let err = hide(&cover, &over, b"pw", &HideOptions::default(), &sealer).unwrap_err();
        assert!(matches!(
            err,
            StegoError::CapacityExceeded { capacity, needed }
                if capacity == cap as u64 && needed == (cap + 1) as u64
        ));
    }

    #[test]
    fn round_trips_png_with_both_selectors() {
        let sealer = fast_sealer();
        let cover = cover(64, 64, ImageFormat::Png);
        let payload = b"attack at dawn -- and bring coffee";
        for selector in [SelectorKind::Sequential, SelectorKind::Permuted] {
            let opts = HideOptions { selector };
            let stego = hide(&cover, payload, b"hunter2", &opts, &sealer).unwrap();
            let out = extract(&stego, b"hunter2", &sealer).unwrap();
            assert_eq!(out, payload, "selector {selector:?}");
        }
    }

    #[test]
    fn round_trips_bmp_and_empty_payload() {
        let sealer = fast_sealer();
        let cover = cover(48, 48, ImageFormat::Bmp);
        for payload in [&b""[..], &b"x"[..], &[0u8, 255, 7, 9][..]] {
            let stego = hide(&cover, payload, b"pw", &HideOptions::default(), &sealer).unwrap();
            assert_eq!(extract(&stego, b"pw", &sealer).unwrap(), payload);
        }
    }

    #[test]
    fn wrong_passphrase_is_unauthorized() {
        let sealer = fast_sealer();
        let cover = cover(64, 64, ImageFormat::Png);
        let stego = hide(
            &cover,
            b"top secret",
            b"right",
            &HideOptions::default(),
            &sealer,
        )
        .unwrap();
        let err = extract(&stego, b"wrong", &sealer).unwrap_err();
        assert!(matches!(err, StegoError::AuthFailed));
        assert_eq!(ApiError::from(err), ApiError::Unauthorized);
    }

    #[test]
    fn single_bit_body_tamper_is_unauthorized() {
        let sealer = fast_sealer();
        let cover = cover(64, 64, ImageFormat::Png);
        // Sequential placement so the first body site is a *used* ciphertext bit; flipping it must
        // break the Poly1305 tag → AEAD open fails.
        let opts = HideOptions {
            selector: SelectorKind::Sequential,
        };
        let stego = hide(&cover, b"integrity matters", b"pw", &opts, &sealer).unwrap();
        let tampered = flip_site(&stego, capacity::HEADER_SITES);
        let err = extract(&tampered, b"pw", &sealer).unwrap_err();
        assert!(matches!(err, StegoError::AuthFailed));
        assert_eq!(ApiError::from(err), ApiError::Unauthorized);
    }

    #[test]
    fn header_tamper_under_permuted_is_unauthorized() {
        // Default (permuted) placement. Flipping one salt bit (always present in the header) changes
        // both the derived key and the permutation seed, so extraction reads the wrong sites with the
        // wrong key → AEAD open fails. Reliable without knowing the body schedule.
        let sealer = fast_sealer();
        let cover = cover(64, 64, ImageFormat::Png);
        let stego = hide(
            &cover,
            b"msg in a permuted carrier",
            b"pw",
            &HideOptions::default(),
            &sealer,
        )
        .unwrap();
        // Salt occupies header bytes [10..26] → first salt bit is site 10*8.
        let tampered = flip_site(&stego, 10 * 8);
        let err = extract(&tampered, b"pw", &sealer).unwrap_err();
        assert!(matches!(err, StegoError::AuthFailed));
        assert_eq!(ApiError::from(err), ApiError::Unauthorized);
    }

    #[test]
    fn clean_image_yields_no_payload() {
        let sealer = fast_sealer();
        let clean = cover(64, 64, ImageFormat::Png);
        let err = extract(&clean, b"pw", &sealer).unwrap_err();
        // No SVSTEG frame → NoPayload, oracle-safe.
        assert!(matches!(err, StegoError::NoPayload));
        assert_eq!(ApiError::from(err), ApiError::Unauthorized);
    }

    #[test]
    fn all_extract_failures_share_one_code() {
        // The oracle-safety property end-to-end: clean / wrong-key / tampered are indistinguishable.
        let sealer = fast_sealer();
        let cover = cover(64, 64, ImageFormat::Png);
        let opts = HideOptions {
            selector: SelectorKind::Sequential,
        };
        let stego = hide(&cover, b"secret", b"pw", &opts, &sealer).unwrap();

        let clean_code = ApiError::from(extract(&cover, b"pw", &sealer).unwrap_err()).code();
        let wrong_code = ApiError::from(extract(&stego, b"nope", &sealer).unwrap_err()).code();
        let tamper_code = ApiError::from(
            extract(&flip_site(&stego, capacity::HEADER_SITES), b"pw", &sealer).unwrap_err(),
        )
        .code();

        assert_eq!(clean_code, "SV-UNAUTHORIZED");
        assert_eq!(wrong_code, "SV-UNAUTHORIZED");
        assert_eq!(tamper_code, "SV-UNAUTHORIZED");
    }

    #[test]
    fn capacity_boundary_is_exact() {
        let sealer = fast_sealer();
        let cover_bytes = cover(16, 16, ImageFormat::Png);
        let site_count = SpatialCarrier::decode(&cover_bytes).unwrap().site_count();
        let cap = capacity::max_plaintext_bytes(site_count);
        assert!(cap > 0);

        // Exactly at capacity → succeeds and round-trips.
        let at = vec![0xA5u8; cap];
        let stego = hide(&cover_bytes, &at, b"pw", &HideOptions::default(), &sealer).unwrap();
        assert_eq!(extract(&stego, b"pw", &sealer).unwrap(), at);

        // One byte over → CapacityExceeded → TooLarge, with the actionable counts.
        let over = vec![0xA5u8; cap + 1];
        let err = hide(&cover_bytes, &over, b"pw", &HideOptions::default(), &sealer).unwrap_err();
        assert!(matches!(
            err,
            StegoError::CapacityExceeded { capacity, needed }
                if capacity == cap as u64 && needed == (cap + 1) as u64
        ));
        assert_eq!(
            ApiError::from(err),
            ApiError::TooLarge {
                limit_bytes: cap as u64,
                actual_bytes: (cap + 1) as u64
            }
        );
    }

    #[test]
    fn non_image_cover_is_malformed() {
        let sealer = fast_sealer();
        let err = hide(
            b"not an image at all",
            b"x",
            b"pw",
            &HideOptions::default(),
            &sealer,
        )
        .unwrap_err();
        assert!(matches!(err, StegoError::CoverUndecodable));
        assert_eq!(ApiError::from(err), ApiError::Malformed);

        let err2 = extract(b"still not an image", b"pw", &sealer).unwrap_err();
        assert!(matches!(err2, StegoError::CoverUndecodable));
        assert_eq!(ApiError::from(err2), ApiError::Malformed);
    }

    #[test]
    fn randomized_round_trip_many_sizes_and_payloads() {
        // Deterministic pseudo-random sweep (fixed seed via a counter) over dims, payloads, and
        // passphrases — covers many shapes without a proptest dependency.
        let sealer = fast_sealer();
        let mut state: u64 = 0x9E37_79B9_7F4A_7C15;
        let mut nextu = || {
            state = state
                .wrapping_mul(6364136223846793005)
                .wrapping_add(1442695040888963407);
            state
        };
        for _ in 0..16 {
            let w = 16 + (nextu() % 24) as u32; // 16..40
            let h = 16 + (nextu() % 24) as u32;
            let format = if nextu() & 1 == 0 {
                ImageFormat::Png
            } else {
                ImageFormat::Bmp
            };
            let cover_bytes = cover(w, h, format);
            let cap = capacity::max_plaintext_bytes(
                SpatialCarrier::decode(&cover_bytes).unwrap().site_count(),
            );
            let plen = (nextu() as usize) % (cap + 1);
            let payload: Vec<u8> = (0..plen).map(|i| (nextu() as u8) ^ (i as u8)).collect();
            let pass: Vec<u8> = (nextu() as u32).to_le_bytes().to_vec();
            let selector = if nextu() & 1 == 0 {
                SelectorKind::Sequential
            } else {
                SelectorKind::Permuted
            };

            let stego = hide(
                &cover_bytes,
                &payload,
                &pass,
                &HideOptions { selector },
                &sealer,
            )
            .unwrap();
            assert_eq!(extract(&stego, &pass, &sealer).unwrap(), payload);
            // A different passphrase must never recover it.
            if plen > 0 {
                assert!(matches!(
                    extract(&stego, b"definitely-different", &sealer),
                    Err(StegoError::AuthFailed)
                ));
            }
        }
    }
}
