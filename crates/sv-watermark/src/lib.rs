//! # sv-watermark — invisible, keyed, fragile (tamper-evident) image watermark
//!
//! A **pure-Rust** watermarking module that answers one question: *has this exact image been altered
//! since it was marked, by someone without the key?* It is **not** steganography (it hides no secret
//! payload) and **not** robust (it is *meant* to break on any edit) — it is a self-contained,
//! **keyed tamper-evidence** mark. See `watermark/EVALUATION.md` for why the robust DWT-DCT-SVD family
//! is deferred (no vetted pure-Rust 2D wavelet transform) and the visible family is deferred (cosmetic).
//!
//! ## Scheme (lossless covers only — PNG/BMP)
//! The image is divided into `16×16` blocks (the last row/column absorbs the remainder, so every block
//! spans ≥16 px per side). For each block a tag is computed:
//! `tag = BLAKE3::keyed_hash(K, "…block-v1" ‖ W ‖ H ‖ bx ‖ by ‖ content)`, where `content` is the
//! **upper 7 bits** of R,G,B of every pixel in the block (the LSB plane is excluded). The 256-bit tag
//! is **tiled across the block's blue-channel LSBs** — every blue LSB becomes a tag bit. Embedding
//! touches only blue LSBs, so the content (hence the tag) is unchanged → self-consistent.
//!
//! Verify recomputes each block's tag and checks every blue LSB; a block is *intact* iff all match.
//! Any change to visible content (upper-7 bits) or to a blue LSB makes ≥1 block fail → **Tampered**
//! (localized). A clean unmarked image / wrong key / wholly replaced image matches **zero** blocks →
//! **NotWatermarked**. The key is the toolkit's **Argon2id** (`sv_crypto::Argon2Kdf` at the OWASP
//! policy floor) — no new primitive. Errors are the existing oracle-safe [`sv_types::ApiError`].

#![forbid(unsafe_code)]

use std::path::Path;

use image::RgbaImage;
use sv_crypto::{policy, Argon2Kdf, Kdf, Salt};
use sv_types::{ApiError, WatermarkEmbedReport, WatermarkVerdict, WatermarkVerifyReport};

/// Tamper-check block edge (px). Each full block carries 256 blue-LSB tag bits.
const BLOCK: u32 = 16;

/// Refuse input images larger than this before decoding (DoS guard).
pub const MAX_IMAGE_BYTES: u64 = 256 * 1024 * 1024;
/// Decode-time dimension / allocation ceilings (decompression-bomb guard).
const MAX_DIM: u32 = 30_000;
const MAX_ALLOC_BYTES: u64 = 1024 * 1024 * 1024;

/// Fixed module salt for the Argon2id key derivation. The key is never stored, so the salt's role
/// here is domain-separation (so a watermark passphrase never collides with another module's key),
/// not anti-rainbow; the Argon2id work factor against passphrase guessing is unaffected.
const WATERMARK_SALT: Salt = Salt(*b"sv-watermark-slt");
/// Domain-separation tag for the per-block keyed MAC.
const BLOCK_CONTEXT: &[u8] = b"sv-watermark-block-v1";

/// Failures from the watermark codec, mapped to oracle-safe [`ApiError`] at the boundary.
#[derive(Debug, thiserror::Error)]
pub enum WatermarkError {
    #[error("input image not found")]
    NotFound,
    #[error("output already exists")]
    OutputExists,
    #[error("input image too large: {actual} bytes exceeds the {limit}-byte limit")]
    TooLarge { limit: u64, actual: u64 },
    /// A non-secret, actionable input fact (not a PNG/BMP, too small, lossy output, …).
    #[error("{0}")]
    InvalidInput(String),
    #[error("i/o error: {0}")]
    Io(String),
    /// Key derivation failed (operator/internal fault, never a user oracle).
    #[error("internal error")]
    Internal,
}

impl From<WatermarkError> for ApiError {
    fn from(e: WatermarkError) -> Self {
        match e {
            WatermarkError::NotFound => ApiError::NotFound,
            WatermarkError::OutputExists => ApiError::OutputExists,
            WatermarkError::TooLarge { limit, actual } => ApiError::TooLarge {
                limit_bytes: limit,
                actual_bytes: actual,
            },
            WatermarkError::InvalidInput(detail) => ApiError::InvalidInput { detail },
            WatermarkError::Io(_) => ApiError::io_generic(),
            WatermarkError::Internal => ApiError::Internal,
        }
    }
}

/// **Embed** — write a watermarked copy of `input` to `output` (PNG/BMP; refused if it exists; the
/// input is never modified in place). Any later edit to the image breaks the mark (see [`verify`]).
pub fn embed(
    input: &Path,
    output: &Path,
    passphrase: &[u8],
) -> Result<WatermarkEmbedReport, WatermarkError> {
    precheck(input)?;
    refuse_existing(output)?;
    require_lossless(output)?;
    let key = derive_key(passphrase)?;
    let mut img = load_rgba_bounded(input)?;
    let (w, h) = img.dimensions();
    require_min_size(w, h)?;

    let mut blocks = 0u32;
    for_each_block(w, h, |x0, y0, x1, y1| {
        let tag = block_tag(&img, w, h, x0, y0, x1, y1, &key);
        // Tile the 256-bit tag across this block's blue LSBs (row-major pixel order).
        let mut i = 0usize;
        for y in y0..y1 {
            for x in x0..x1 {
                let bit = tag_bit(&tag, i);
                let px = img.get_pixel_mut(x, y);
                px.0[2] = (px.0[2] & 0xFE) | bit;
                i += 1;
            }
        }
        blocks += 1;
    });

    save_lossless(&img, output)?;
    Ok(WatermarkEmbedReport {
        output_path: path_str(output),
        width: w,
        height: h,
        blocks,
    })
}

/// **Verify** — recompute every block's tag and check it against the embedded blue-LSB bits. Returns
/// a three-way verdict (Intact / Tampered / NotWatermarked) plus the per-block tamper count.
pub fn verify(input: &Path, passphrase: &[u8]) -> Result<WatermarkVerifyReport, WatermarkError> {
    precheck(input)?;
    let key = derive_key(passphrase)?;
    let img = load_rgba_bounded(input)?;
    let (w, h) = img.dimensions();
    require_min_size(w, h)?;

    let (mut total, mut tampered) = (0u32, 0u32);
    for_each_block(w, h, |x0, y0, x1, y1| {
        let tag = block_tag(&img, w, h, x0, y0, x1, y1, &key);
        let mut intact = true;
        let mut i = 0usize;
        'block: for y in y0..y1 {
            for x in x0..x1 {
                let expected = tag_bit(&tag, i);
                let actual = img.get_pixel(x, y).0[2] & 1;
                if expected != actual {
                    intact = false;
                    break 'block;
                }
                i += 1;
            }
        }
        total += 1;
        if !intact {
            tampered += 1;
        }
    });

    let verdict = if tampered == 0 {
        WatermarkVerdict::Intact
    } else if tampered == total {
        // No block validated: not watermarked, wrong key, or wholly replaced (a watermarked-untouched
        // block matches with overwhelming probability, so "zero matches" reliably means "no mark").
        WatermarkVerdict::NotWatermarked
    } else {
        WatermarkVerdict::Tampered
    };
    Ok(WatermarkVerifyReport {
        verdict,
        total_blocks: total,
        tampered_blocks: tampered,
    })
}

// --- key derivation (reuses the toolkit's Argon2id; no new primitive) --------

/// 32-byte zeroizing key material for the per-block MAC.
struct WmKey([u8; 32]);

impl Drop for WmKey {
    fn drop(&mut self) {
        use zeroize::Zeroize;
        self.0.zeroize();
    }
}

fn derive_key(passphrase: &[u8]) -> Result<WmKey, WatermarkError> {
    let key = Argon2Kdf
        .derive(passphrase, &WATERMARK_SALT, &policy::recommended())
        .map_err(|_| WatermarkError::Internal)?;
    Ok(WmKey(*key.expose_secret()))
}

// --- per-block tag -----------------------------------------------------------

/// `tag = BLAKE3::keyed_hash(K, ctx ‖ W ‖ H ‖ bx-ish ‖ by-ish ‖ upper7(R,G,B) over the block)`.
/// Block position is bound via `x0,y0` so a block cannot be moved/duplicated without detection.
#[allow(clippy::too_many_arguments)]
fn block_tag(
    img: &RgbaImage,
    w: u32,
    h: u32,
    x0: u32,
    y0: u32,
    x1: u32,
    y1: u32,
    key: &WmKey,
) -> [u8; 32] {
    let mut buf =
        Vec::with_capacity(BLOCK_CONTEXT.len() + 24 + ((x1 - x0) * (y1 - y0) * 3) as usize);
    buf.extend_from_slice(BLOCK_CONTEXT);
    buf.extend_from_slice(&w.to_le_bytes());
    buf.extend_from_slice(&h.to_le_bytes());
    buf.extend_from_slice(&x0.to_le_bytes());
    buf.extend_from_slice(&y0.to_le_bytes());
    for y in y0..y1 {
        for x in x0..x1 {
            let p = img.get_pixel(x, y).0;
            buf.push(p[0] & 0xFE);
            buf.push(p[1] & 0xFE);
            buf.push(p[2] & 0xFE);
        }
    }
    *blake3::keyed_hash(&key.0, &buf).as_bytes()
}

/// Bit `i mod 256` of the 256-bit tag (LSB-first within each byte).
fn tag_bit(tag: &[u8; 32], i: usize) -> u8 {
    let j = i % 256;
    (tag[j / 8] >> (j % 8)) & 1
}

/// Iterate the `16×16` block grid; the last row/column absorbs the remainder (so every block is
/// ≥16 px per side). Calls `f(x0, y0, x1, y1)` per block.
fn for_each_block(w: u32, h: u32, mut f: impl FnMut(u32, u32, u32, u32)) {
    let nbx = (w / BLOCK).max(1);
    let nby = (h / BLOCK).max(1);
    for by in 0..nby {
        let y0 = by * BLOCK;
        let y1 = if by == nby - 1 { h } else { (by + 1) * BLOCK };
        for bx in 0..nbx {
            let x0 = bx * BLOCK;
            let x1 = if bx == nbx - 1 { w } else { (bx + 1) * BLOCK };
            f(x0, y0, x1, y1);
        }
    }
}

// --- io helpers --------------------------------------------------------------

fn load_rgba_bounded(input: &Path) -> Result<RgbaImage, WatermarkError> {
    let reader = image::ImageReader::open(input)
        .map_err(|e| io_or_notfound(&e))?
        .with_guessed_format()
        .map_err(|_| WatermarkError::InvalidInput("the file is not a PNG or BMP image".into()))?;
    let mut reader = reader;
    let mut limits = image::Limits::default();
    limits.max_image_width = Some(MAX_DIM);
    limits.max_image_height = Some(MAX_DIM);
    limits.max_alloc = Some(MAX_ALLOC_BYTES);
    reader.limits(limits);
    let dynimg = reader.decode().map_err(|_| {
        WatermarkError::InvalidInput("the file is not a supported PNG or BMP image".into())
    })?;
    Ok(dynimg.to_rgba8())
}

fn save_lossless(img: &RgbaImage, output: &Path) -> Result<(), WatermarkError> {
    let fmt = lossless_format(output)?;
    img.save_with_format(output, fmt)
        .map_err(|e| WatermarkError::Io(e.to_string()))
}

/// PNG/BMP only — a fragile LSB watermark cannot survive lossy re-encoding.
fn lossless_format(output: &Path) -> Result<image::ImageFormat, WatermarkError> {
    match output
        .extension()
        .and_then(|e| e.to_str())
        .map(str::to_ascii_lowercase)
        .as_deref()
    {
        Some("png") => Ok(image::ImageFormat::Png),
        Some("bmp") => Ok(image::ImageFormat::Bmp),
        _ => Err(WatermarkError::InvalidInput(
            "the output must be a lossless .png or .bmp (a fragile watermark cannot survive JPEG)"
                .into(),
        )),
    }
}

fn require_lossless(output: &Path) -> Result<(), WatermarkError> {
    lossless_format(output).map(|_| ())
}

fn require_min_size(w: u32, h: u32) -> Result<(), WatermarkError> {
    if w < BLOCK || h < BLOCK {
        return Err(WatermarkError::InvalidInput(format!(
            "the image must be at least {BLOCK}×{BLOCK} pixels"
        )));
    }
    Ok(())
}

fn io_or_notfound(e: &std::io::Error) -> WatermarkError {
    if e.kind() == std::io::ErrorKind::NotFound {
        WatermarkError::NotFound
    } else {
        WatermarkError::Io(e.to_string())
    }
}

fn refuse_existing(p: &Path) -> Result<(), WatermarkError> {
    if p.exists() {
        Err(WatermarkError::OutputExists)
    } else {
        Ok(())
    }
}

fn precheck(input: &Path) -> Result<(), WatermarkError> {
    let meta = std::fs::metadata(input).map_err(|e| match e.kind() {
        std::io::ErrorKind::NotFound => WatermarkError::NotFound,
        _ => WatermarkError::Io(e.to_string()),
    })?;
    if meta.len() > MAX_IMAGE_BYTES {
        return Err(WatermarkError::TooLarge {
            limit: MAX_IMAGE_BYTES,
            actual: meta.len(),
        });
    }
    Ok(())
}

fn path_str(p: &Path) -> String {
    p.to_string_lossy().into_owned()
}

#[cfg(test)]
mod tests {
    use super::*;

    fn tmp() -> tempfile::TempDir {
        tempfile::tempdir().unwrap()
    }

    /// A deterministic gradient cover (no metadata), large enough for many blocks.
    fn write_cover(path: &Path, w: u32, h: u32) {
        let mut img = RgbaImage::new(w, h);
        for (x, y, px) in img.enumerate_pixels_mut() {
            *px = image::Rgba([(x * 3) as u8, (y * 5) as u8, (x ^ y) as u8, 255]);
        }
        img.save(path).unwrap();
    }

    #[test]
    fn embed_then_verify_is_intact() {
        let dir = tmp();
        let cover = dir.path().join("c.png");
        let marked = dir.path().join("c.wm.png");
        write_cover(&cover, 96, 80);
        let rep = embed(&cover, &marked, b"pw").unwrap();
        assert_eq!((rep.width, rep.height), (96, 80));
        assert!(rep.blocks >= 1);
        assert!(marked.exists());

        let v = verify(&marked, b"pw").unwrap();
        assert_eq!(v.verdict, WatermarkVerdict::Intact);
        assert_eq!(v.tampered_blocks, 0);
        assert_eq!(v.total_blocks, rep.blocks);
    }

    #[test]
    fn a_single_pixel_edit_is_detected_and_localized() {
        let dir = tmp();
        let cover = dir.path().join("c.png");
        let marked = dir.path().join("c.wm.png");
        write_cover(&cover, 96, 96); // 6×6 = 36 blocks
        embed(&cover, &marked, b"pw").unwrap();

        // Flip a high bit of one pixel in one block (a visible-content change).
        let mut img = image::open(&marked).unwrap().to_rgba8();
        let p = img.get_pixel_mut(40, 40);
        p.0[0] ^= 0x80;
        let edited = dir.path().join("edited.png");
        img.save(&edited).unwrap();

        let v = verify(&edited, b"pw").unwrap();
        assert_eq!(v.verdict, WatermarkVerdict::Tampered);
        assert_eq!(v.tampered_blocks, 1, "exactly the touched block fails");
    }

    #[test]
    fn a_single_blue_lsb_flip_is_detected() {
        let dir = tmp();
        let cover = dir.path().join("c.png");
        let marked = dir.path().join("c.wm.png");
        write_cover(&cover, 64, 64);
        embed(&cover, &marked, b"pw").unwrap();
        let mut img = image::open(&marked).unwrap().to_rgba8();
        let p = img.get_pixel_mut(5, 5);
        p.0[2] ^= 0x01; // flip a watermark LSB
        let edited = dir.path().join("edited.png");
        img.save(&edited).unwrap();
        assert_eq!(
            verify(&edited, b"pw").unwrap().verdict,
            WatermarkVerdict::Tampered
        );
    }

    #[test]
    fn wrong_key_reads_as_not_watermarked() {
        let dir = tmp();
        let cover = dir.path().join("c.png");
        let marked = dir.path().join("c.wm.png");
        write_cover(&cover, 80, 80);
        embed(&cover, &marked, b"correct horse").unwrap();
        let v = verify(&marked, b"battery staple").unwrap();
        assert_eq!(v.verdict, WatermarkVerdict::NotWatermarked);
        assert_eq!(v.tampered_blocks, v.total_blocks);
    }

    #[test]
    fn an_unmarked_image_reads_as_not_watermarked() {
        let dir = tmp();
        let plain = dir.path().join("plain.png");
        write_cover(&plain, 64, 64);
        assert_eq!(
            verify(&plain, b"pw").unwrap().verdict,
            WatermarkVerdict::NotWatermarked
        );
    }

    #[test]
    fn embed_refuses_overwrite_and_lossy_output() {
        let dir = tmp();
        let cover = dir.path().join("c.png");
        write_cover(&cover, 32, 32);
        // refuse overwrite
        let exists = dir.path().join("there.png");
        std::fs::write(&exists, b"x").unwrap();
        assert!(matches!(
            embed(&cover, &exists, b"pw"),
            Err(WatermarkError::OutputExists)
        ));
        // refuse lossy output
        let jpg = dir.path().join("out.jpg");
        assert!(matches!(
            embed(&cover, &jpg, b"pw"),
            Err(WatermarkError::InvalidInput(_))
        ));
        assert!(!jpg.exists());
    }

    #[test]
    fn too_small_and_missing_inputs_are_rejected() {
        let dir = tmp();
        let small = dir.path().join("small.png");
        write_cover(&small, 8, 8);
        assert!(matches!(
            embed(&small, &dir.path().join("o.png"), b"pw"),
            Err(WatermarkError::InvalidInput(_))
        ));
        assert!(matches!(
            verify(&dir.path().join("nope.png"), b"pw"),
            Err(WatermarkError::NotFound)
        ));
    }

    #[test]
    fn errors_map_to_existing_api_codes() {
        assert_eq!(ApiError::from(WatermarkError::NotFound), ApiError::NotFound);
        assert_eq!(
            ApiError::from(WatermarkError::OutputExists),
            ApiError::OutputExists
        );
        assert_eq!(
            ApiError::from(WatermarkError::InvalidInput("x".into())).code(),
            "SV-INVALID-INPUT"
        );
        assert_eq!(ApiError::from(WatermarkError::Internal), ApiError::Internal);
        assert_eq!(
            ApiError::from(WatermarkError::Io("x".into())).code(),
            "SV-IO"
        );
    }
}
