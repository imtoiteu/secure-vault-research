//! # sv-qr — Secure QR Transfer codec
//!
//! A **generic, pure-Rust** QR-code codec: render a short text string to a QR **PNG** file, and
//! decode a QR code back out of an image file (PNG/JPEG/BMP photo or screenshot). It is
//! **transport-only** — it knows nothing about secret sharing or any payload semantics. The Secret
//! Sharing module ([`sv_platform`]) composes it to move its non-secret *piece strings*
//! (`share_b64`, 124 ASCII chars) as QR images; recovery decodes those images back to strings and
//! routes them through the **unchanged** Secret Sharing recover engine. See
//! `qr-transfer/EVALUATION.md` for the selection (`qrcode` encode + `rqrr` decode, both pure-Rust,
//! permissive, on the workspace's existing `image` 0.25).
//!
//! No bundled binary / subprocess / FFI (unlike the age/ExifTool external-binary modules): this is
//! in-process pure Rust (the steganography precedent). Hardening here is input-size/decompression
//! caps + **fail-closed decode** (a malformed image or absent QR is an honest error, never a wrong
//! result). Errors project onto the **existing** oracle-safe [`sv_types::ApiError`] taxonomy — no
//! new code; no secret ever enters this layer (a QR of a Shamir *piece* is non-secret ciphertext).

#![forbid(unsafe_code)]

use std::path::{Path, PathBuf};

use sv_types::ApiError;

/// Refuse input images larger than this before decoding (DoS guard; QR captures are small).
pub const MAX_IMAGE_BYTES: u64 = 64 * 1024 * 1024;

/// Decode-time pixel-dimension and allocation ceilings (decompression-bomb guard).
const MAX_DIM: u32 = 20_000;
const MAX_ALLOC_BYTES: u64 = 512 * 1024 * 1024;

/// Failures from the QR codec, mapped to oracle-safe [`ApiError`] at the boundary.
#[derive(Debug, thiserror::Error)]
pub enum QrError {
    #[error("input image not found")]
    NotFound,
    #[error("output already exists")]
    OutputExists,
    #[error("input image too large: {actual} bytes exceeds the {limit}-byte limit")]
    TooLarge { limit: u64, actual: u64 },
    /// The data does not fit in a QR code (capacity exceeded). Non-secret input fact.
    #[error("the data is too large to encode as a QR code")]
    TooLargeForQr,
    /// No QR code could be located/decoded in the image (or it was undecodable).
    #[error("no readable QR code was found in the image")]
    NoQrFound,
    /// The file is not a readable image.
    #[error("not a readable image")]
    NotAnImage,
    #[error("i/o error: {0}")]
    Io(String),
}

impl From<QrError> for ApiError {
    fn from(e: QrError) -> Self {
        match e {
            QrError::NotFound => ApiError::NotFound,
            QrError::OutputExists => ApiError::OutputExists,
            QrError::TooLarge { limit, actual } => ApiError::TooLarge {
                limit_bytes: limit,
                actual_bytes: actual,
            },
            // Capacity overflow is a non-secret, actionable input fact.
            QrError::TooLargeForQr => ApiError::InvalidInput {
                detail: "the data is too large to fit in a single QR code".into(),
            },
            // "no QR found" and "not an image" are both benign "wrong/unsuitable file" facts →
            // the existing oracle-safe SV-MALFORMED (matches Secret Sharing's "wrong file" semantics).
            QrError::NoQrFound | QrError::NotAnImage => ApiError::Malformed,
            QrError::Io(_) => ApiError::io_generic(),
        }
    }
}

/// **Encode** — render `text` as a QR code and write it to `output` as a **PNG** (refused if it
/// exists; never overwrites). Uses the highest error-correction level (`H`) for scan robustness and
/// a minimum raster size so the result is easy to scan or print. Returns the output path.
pub fn encode_text_to_png(text: &str, output: &Path) -> Result<PathBuf, QrError> {
    refuse_existing(output)?;
    let code = qrcode::QrCode::with_error_correction_level(text.as_bytes(), qrcode::EcLevel::H)
        .map_err(|_| QrError::TooLargeForQr)?;
    let image = code
        .render::<image::Luma<u8>>()
        .min_dimensions(512, 512)
        .quiet_zone(true)
        .build();
    image
        .save_with_format(output, image::ImageFormat::Png)
        .map_err(|e| QrError::Io(e.to_string()))?;
    Ok(output.to_path_buf())
}

/// **Decode** — locate and decode a QR code in `input` (PNG/JPEG/BMP) and return its text. Fails
/// closed: an absent/undecodable QR is [`QrError::NoQrFound`], an unreadable file is
/// [`QrError::NotAnImage`] — never a wrong result. Input size + decode allocation are capped.
pub fn decode_png(input: &Path) -> Result<String, QrError> {
    precheck(input)?;
    let gray = load_luma_bounded(input)?;
    let mut prepared = rqrr::PreparedImage::prepare(gray);
    let grids = prepared.detect_grids();
    let grid = grids.first().ok_or(QrError::NoQrFound)?;
    match grid.decode() {
        Ok((_meta, content)) => Ok(content),
        Err(_) => Err(QrError::NoQrFound),
    }
}

/// **Decode all** — locate and decode *every* QR code in `input`, returning each code's text in
/// detection order. When several piece QRs share one photo, none is silently dropped (M3). Fails
/// closed like [`decode_png`]: if no QR decodes, [`QrError::NoQrFound`].
pub fn decode_png_all(input: &Path) -> Result<Vec<String>, QrError> {
    precheck(input)?;
    let gray = load_luma_bounded(input)?;
    let mut prepared = rqrr::PreparedImage::prepare(gray);
    let grids = prepared.detect_grids();
    let mut out = Vec::with_capacity(grids.len());
    for grid in &grids {
        if let Ok((_meta, content)) = grid.decode() {
            out.push(content);
        }
    }
    if out.is_empty() {
        return Err(QrError::NoQrFound);
    }
    Ok(out)
}

/// Load an image as 8-bit grayscale with explicit width/height/allocation limits (bomb guard).
fn load_luma_bounded(input: &Path) -> Result<image::GrayImage, QrError> {
    let reader = image::ImageReader::open(input)
        .map_err(|e| io_or_notfound(&e))?
        .with_guessed_format()
        .map_err(|_| QrError::NotAnImage)?;
    let mut reader = reader;
    let mut limits = image::Limits::default();
    limits.max_image_width = Some(MAX_DIM);
    limits.max_image_height = Some(MAX_DIM);
    limits.max_alloc = Some(MAX_ALLOC_BYTES);
    reader.limits(limits);
    let dynimg = reader.decode().map_err(|_| QrError::NotAnImage)?;
    Ok(dynimg.to_luma8())
}

fn io_or_notfound(e: &std::io::Error) -> QrError {
    if e.kind() == std::io::ErrorKind::NotFound {
        QrError::NotFound
    } else {
        QrError::Io(e.to_string())
    }
}

fn refuse_existing(p: &Path) -> Result<(), QrError> {
    if p.exists() {
        Err(QrError::OutputExists)
    } else {
        Ok(())
    }
}

fn precheck(input: &Path) -> Result<(), QrError> {
    let meta = std::fs::metadata(input).map_err(|e| match e.kind() {
        std::io::ErrorKind::NotFound => QrError::NotFound,
        _ => QrError::Io(e.to_string()),
    })?;
    if meta.len() > MAX_IMAGE_BYTES {
        return Err(QrError::TooLarge {
            limit: MAX_IMAGE_BYTES,
            actual: meta.len(),
        });
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn tmp() -> tempfile::TempDir {
        tempfile::tempdir().unwrap()
    }

    /// A realistic Secret Sharing piece string: Base64 of a 92-byte SVSSS record = 124 chars.
    fn sample_piece() -> String {
        // Deterministic 124-char Base64-alphabet string (content is opaque to the codec).
        let alphabet = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
        (0..124)
            .map(|i| alphabet[(i * 7 + 3) % alphabet.len()] as char)
            .collect()
    }

    #[test]
    fn round_trip_encodes_and_decodes_a_piece_string() {
        let dir = tmp();
        let out = dir.path().join("piece.png");
        let text = sample_piece();
        let saved = encode_text_to_png(&text, &out).unwrap();
        assert_eq!(saved, out);
        assert!(out.exists());
        let decoded = decode_png(&out).unwrap();
        assert_eq!(decoded, text, "QR round-trip must be lossless");
    }

    #[test]
    fn decode_all_returns_each_code() {
        let dir = tmp();
        let out = dir.path().join("q.png");
        encode_text_to_png("PIECE-ONE", &out).unwrap();
        // A single-QR image yields a one-element vec; a plain (no-QR) image fails closed.
        assert_eq!(decode_png_all(&out).unwrap(), vec!["PIECE-ONE".to_string()]);
        let plain = dir.path().join("plain.png");
        image::GrayImage::from_pixel(40, 40, image::Luma([200u8]))
            .save(&plain)
            .unwrap();
        assert!(matches!(decode_png_all(&plain), Err(QrError::NoQrFound)));
    }

    #[test]
    fn round_trip_handles_short_and_longer_ascii() {
        let dir = tmp();
        for (i, text) in ["x", "secure-vault", &"A".repeat(400)].iter().enumerate() {
            let out = dir.path().join(format!("q{i}.png"));
            encode_text_to_png(text, &out).unwrap();
            assert_eq!(&decode_png(&out).unwrap(), text);
        }
    }

    #[test]
    fn encode_refuses_to_overwrite() {
        let dir = tmp();
        let out = dir.path().join("exists.png");
        std::fs::write(&out, b"already here").unwrap();
        assert!(matches!(
            encode_text_to_png("data", &out),
            Err(QrError::OutputExists)
        ));
        // The pre-existing file is untouched.
        assert_eq!(std::fs::read(&out).unwrap(), b"already here");
    }

    #[test]
    fn decode_missing_file_is_not_found() {
        let dir = tmp();
        assert!(matches!(
            decode_png(&dir.path().join("nope.png")),
            Err(QrError::NotFound)
        ));
    }

    #[test]
    fn decode_non_image_is_not_an_image() {
        let dir = tmp();
        let f = dir.path().join("notimg.png");
        std::fs::write(&f, b"this is not an image").unwrap();
        assert!(matches!(decode_png(&f), Err(QrError::NotAnImage)));
    }

    #[test]
    fn decode_image_without_qr_finds_nothing() {
        // A plain white PNG carries no QR → fail-closed NoQrFound (never a wrong result).
        let dir = tmp();
        let f = dir.path().join("blank.png");
        let img = image::GrayImage::from_pixel(64, 64, image::Luma([255u8]));
        img.save(&f).unwrap();
        assert!(matches!(decode_png(&f), Err(QrError::NoQrFound)));
    }

    #[test]
    fn errors_map_to_existing_api_codes() {
        assert_eq!(ApiError::from(QrError::NotFound), ApiError::NotFound);
        assert_eq!(
            ApiError::from(QrError::OutputExists),
            ApiError::OutputExists
        );
        assert_eq!(ApiError::from(QrError::NoQrFound), ApiError::Malformed);
        assert_eq!(ApiError::from(QrError::NotAnImage), ApiError::Malformed);
        assert_eq!(
            ApiError::from(QrError::TooLargeForQr).code(),
            "SV-INVALID-INPUT"
        );
        assert_eq!(
            ApiError::from(QrError::TooLarge {
                limit: MAX_IMAGE_BYTES,
                actual: MAX_IMAGE_BYTES + 1
            })
            .code(),
            "SV-TOO-LARGE"
        );
        assert_eq!(ApiError::from(QrError::Io("x".into())).code(), "SV-IO");
    }
}
