//! **Appended-data detector** — an in-house "binwalk-lite" over the raw file bytes.
//!
//! It locates the image's *logical* end (PNG: the byte after the `IEND` chunk; BMP: the declared
//! `bfSize`), then reports on anything that trails it: how much, its Shannon entropy (high entropy ⇒
//! compressed/encrypted), and whether it begins with a recognizable embedded-file magic. This is the
//! single highest-value real-world check (appending a ZIP/file after a PNG is the most common naive
//! "steganography"). It only **reports** — it never carves or extracts (the design's binwalk
//! boundary), so it pulls no external tooling and stays offline + deny-clean.

use sv_types::StegoSignal;

use crate::detect::{clamp01, DecodedImage, Detector};
use image::ImageFormat;

/// Known embedded-file magic signatures (start-of-file markers). Reporting-only.
const MAGICS: &[(&[u8], &str)] = &[
    (b"PK\x03\x04", "ZIP / Office / JAR"),
    (&[0x89, b'P', b'N', b'G'], "PNG"),
    (&[0xFF, 0xD8, 0xFF], "JPEG"),
    (b"%PDF", "PDF"),
    (&[0x1F, 0x8B], "gzip"),
    (b"Rar!\x1A\x07", "RAR"),
    (&[0x37, 0x7A, 0xBC, 0xAF, 0x27, 0x1C], "7z"),
    (b"BZh", "bzip2"),
    (&[0xFD, b'7', b'z', b'X', b'Z', 0x00], "xz"),
    (b"OggS", "Ogg"),
    (b"ID3", "MP3/ID3"),
];

/// Detects data trailing the image's logical end.
#[derive(Debug, Default, Clone, Copy)]
pub struct AppendedDataDetector;

/// Detector display name (shared by the spatial [`Detector`] path and the JPEG entry point).
const NAME: &str = "appended-data";

impl Detector for AppendedDataDetector {
    fn name(&self) -> &'static str {
        NAME
    }

    fn analyze(&self, image: &DecodedImage) -> StegoSignal {
        let logical_end = match image.format {
            ImageFormat::Png => png_logical_end(&image.raw),
            ImageFormat::Bmp => bmp_logical_end(&image.raw),
            _ => None,
        };
        analyze_trailing(&image.raw, logical_end)
    }
}

/// Appended-data analysis for a **JPEG** (the spatial [`Detector`] path cannot decode one). Locates
/// the byte past the `EOI` marker and scores any trailer with the same rule as the PNG/BMP path.
pub(crate) fn jpeg_appended_signal(raw: &[u8]) -> StegoSignal {
    analyze_trailing(raw, jpeg_logical_end(raw))
}

/// Score whatever trails `logical_end` in `raw` (shared by the PNG/BMP and JPEG entry points).
fn analyze_trailing(raw: &[u8], logical_end: Option<usize>) -> StegoSignal {
    let total = raw.len();
    let Some(end) = logical_end else {
        return signal(
            0.0,
            "could not locate the image's logical end; not analysed".into(),
        );
    };
    if end >= total {
        return signal(0.0, "no data trailing the image's logical end".into());
    }

    let trailing = &raw[end..];
    let tlen = trailing.len();
    let entropy = shannon_entropy(trailing);
    let magic = find_magic(trailing);

    let (score, magic_note) = match magic {
        Some(name) => (0.9_f32, format!("; begins with a {name} signature")),
        None if tlen < 8 => (0.15, String::new()),
        None => (clamp01(0.3 + 0.5 * (entropy / 8.0) as f32), String::new()),
    };

    signal(
        score,
        format!("{tlen} byte(s) after the image; entropy {entropy:.2}/8.0 bits{magic_note}"),
    )
}

/// Build an appended-data signal.
fn signal(score: f32, detail: String) -> StegoSignal {
    StegoSignal {
        name: NAME.to_string(),
        score,
        detail,
    }
}

/// Byte offset just past the PNG `IEND` chunk, or `None` if the stream isn't a walkable PNG.
fn png_logical_end(raw: &[u8]) -> Option<usize> {
    const SIG: [u8; 8] = [0x89, b'P', b'N', b'G', 0x0D, 0x0A, 0x1A, 0x0A];
    if raw.len() < 8 || raw[0..8] != SIG {
        return None;
    }
    let mut off = 8usize;
    while off + 8 <= raw.len() {
        let len = u32::from_be_bytes(raw[off..off + 4].try_into().ok()?) as usize;
        let ctype = &raw[off + 4..off + 8];
        // chunk = 4 (length) + 4 (type) + len (data) + 4 (CRC).
        let chunk_end = off.checked_add(12)?.checked_add(len)?;
        if chunk_end > raw.len() {
            return None; // truncated chunk; refuse to guess
        }
        if ctype == b"IEND" {
            return Some(chunk_end);
        }
        off = chunk_end;
    }
    None
}

/// The BMP's declared file size (`bfSize`), or `None` if it isn't a usable BITMAPFILEHEADER.
fn bmp_logical_end(raw: &[u8]) -> Option<usize> {
    if raw.len() < 6 || &raw[0..2] != b"BM" {
        return None;
    }
    let bf_size = u32::from_le_bytes(raw[2..6].try_into().ok()?) as usize;
    // Reject implausible/over-claiming headers (some encoders write 0): can't trust them.
    if bf_size == 0 || bf_size > raw.len() {
        return None;
    }
    Some(bf_size)
}

/// Byte offset just past the JPEG `EOI` marker (`FF D9`), or `None` if the stream is not a walkable
/// JPEG. Walks marker segments, scanning over entropy-coded scan data (where a real `FF` is stuffed
/// as `FF 00` or is an `RSTn` restart marker) until `EOI`. Refuses to guess on any malformed
/// structure (returns `None`), mirroring [`png_logical_end`]/[`bmp_logical_end`].
fn jpeg_logical_end(raw: &[u8]) -> Option<usize> {
    if raw.len() < 2 || raw[0] != 0xFF || raw[1] != 0xD8 {
        return None; // no Start-Of-Image
    }
    let mut off = 2usize;
    loop {
        if off >= raw.len() || raw[off] != 0xFF {
            return None; // expected a marker's leading 0xFF
        }
        // Skip any 0xFF fill bytes before the marker id.
        let mut p = off + 1;
        while p < raw.len() && raw[p] == 0xFF {
            p += 1;
        }
        let marker = *raw.get(p)?;
        let after_id = p + 1;
        match marker {
            0xD9 => return Some(after_id), // EOI
            // Standalone markers carry no length payload: SOI, TEM, RST0..=RST7.
            0xD8 | 0x01 | 0xD0..=0xD7 => off = after_id,
            0xDA => {
                // Start-Of-Scan: a 2-byte segment length, then entropy data to the next marker.
                let len = segment_len(raw, after_id)?;
                let scan_start = after_id.checked_add(len)?;
                if scan_start > raw.len() {
                    return None;
                }
                off = scan_entropy(raw, scan_start)?;
            }
            _ => {
                // Variable-length segment; the 2-byte length includes its own bytes.
                let len = segment_len(raw, after_id)?;
                off = after_id.checked_add(len)?;
                if off > raw.len() {
                    return None;
                }
            }
        }
    }
}

/// Read a big-endian 2-byte JPEG segment length at `pos`, rejecting a length that can't include its
/// own length bytes.
fn segment_len(raw: &[u8], pos: usize) -> Option<usize> {
    let hi = *raw.get(pos)?;
    let lo = *raw.get(pos + 1)?;
    let len = u16::from_be_bytes([hi, lo]) as usize;
    (len >= 2).then_some(len)
}

/// From `start`, scan entropy-coded data and return the offset of the next marker's leading `FF` — an
/// `FF` followed by a byte that is neither `00` (stuffing) nor an `RSTn` marker (`D0..=D7`).
fn scan_entropy(raw: &[u8], start: usize) -> Option<usize> {
    let mut i = start;
    while i + 1 < raw.len() {
        if raw[i] == 0xFF {
            let next = raw[i + 1];
            if next == 0x00 || (0xD0..=0xD7).contains(&next) {
                i += 2; // byte-stuffed 0xFF or a restart marker — still entropy data
                continue;
            }
            return Some(i); // a real marker starts here
        }
        i += 1;
    }
    None
}

/// Shannon entropy of `data` in bits/byte (`0.0..=8.0`).
fn shannon_entropy(data: &[u8]) -> f64 {
    if data.is_empty() {
        return 0.0;
    }
    let mut counts = [0usize; 256];
    for &b in data {
        counts[b as usize] += 1;
    }
    let n = data.len() as f64;
    let mut h = 0.0;
    for &c in counts.iter() {
        if c > 0 {
            let p = c as f64 / n;
            h -= p * p.log2();
        }
    }
    h
}

/// First known magic that `trailing` begins with (scanning a short window from the start).
fn find_magic(trailing: &[u8]) -> Option<&'static str> {
    // Most appends place the file immediately; tolerate a tiny leading gap.
    let window = &trailing[..trailing.len().min(64)];
    for start in 0..window.len() {
        for (sig, name) in MAGICS {
            if window[start..].starts_with(sig) {
                return Some(name);
            }
        }
    }
    None
}

#[cfg(test)]
mod tests {
    use super::*;
    use image::{DynamicImage, RgbaImage};
    use std::io::Cursor;

    fn png_bytes() -> Vec<u8> {
        let img = RgbaImage::from_pixel(8, 8, image::Rgba([10, 20, 30, 255]));
        let mut cur = Cursor::new(Vec::new());
        DynamicImage::ImageRgba8(img)
            .write_to(&mut cur, ImageFormat::Png)
            .unwrap();
        cur.into_inner()
    }

    #[test]
    fn entropy_endpoints() {
        assert_eq!(shannon_entropy(&[]), 0.0);
        assert_eq!(shannon_entropy(&[7, 7, 7, 7]), 0.0); // single symbol
        let all = (0..=255u8).collect::<Vec<_>>();
        assert!((shannon_entropy(&all) - 8.0).abs() < 1e-9); // uniform 256 symbols
    }

    #[test]
    fn clean_png_has_no_trailing_data() {
        let img = DecodedImage::decode(&png_bytes()).unwrap();
        let s = AppendedDataDetector.analyze(&img);
        assert_eq!(s.score, 0.0);
        assert!(s.detail.contains("no data trailing"));
    }

    #[test]
    fn appended_zip_magic_scores_high() {
        let mut bytes = png_bytes();
        bytes.extend_from_slice(b"PK\x03\x04 and the rest of a zip payload...");
        let img = DecodedImage::decode(&bytes).unwrap();
        let s = AppendedDataDetector.analyze(&img);
        assert!(s.score >= 0.9, "score {}", s.score);
        assert!(s.detail.contains("ZIP"));
    }

    #[test]
    fn appended_high_entropy_blob_without_magic_is_elevated() {
        let mut bytes = png_bytes();
        // A pseudo-random (high-entropy) trailer with no known magic.
        let blob: Vec<u8> = (0..512u32)
            .map(|i| (i.wrapping_mul(2654435761) >> 16) as u8)
            .collect();
        bytes.extend_from_slice(&blob);
        let img = DecodedImage::decode(&bytes).unwrap();
        let s = AppendedDataDetector.analyze(&img);
        assert!(s.score > 0.45, "score {}", s.score);
    }

    fn jpeg_bytes() -> Vec<u8> {
        use image::{codecs::jpeg::JpegEncoder, ImageEncoder, RgbImage};
        let img = RgbImage::from_pixel(16, 16, image::Rgb([120, 80, 40]));
        let mut buf = Vec::new();
        let enc = JpegEncoder::new_with_quality(&mut buf, 80);
        enc.write_image(img.as_raw(), 16, 16, image::ExtendedColorType::Rgb8)
            .unwrap();
        buf
    }

    #[test]
    fn jpeg_logical_end_is_the_eoi_of_a_clean_jpeg() {
        let j = jpeg_bytes();
        let end = jpeg_logical_end(&j).expect("walkable jpeg");
        assert_eq!(
            end,
            j.len(),
            "EOI should be the last marker of a clean jpeg"
        );
        let s = jpeg_appended_signal(&j);
        assert_eq!(s.score, 0.0);
        assert!(s.detail.contains("no data trailing"));
    }

    #[test]
    fn jpeg_appended_zip_after_eoi_scores_high() {
        let mut j = jpeg_bytes();
        j.extend_from_slice(b"PK\x03\x04 a zip smuggled after the JPEG's EOI");
        let s = jpeg_appended_signal(&j);
        assert!(s.score >= 0.9, "score {}", s.score);
        assert!(s.detail.contains("ZIP"));
    }

    #[test]
    fn non_jpeg_has_no_jpeg_logical_end() {
        assert_eq!(jpeg_logical_end(b"not a jpeg"), None);
        assert_eq!(jpeg_logical_end(&png_bytes()), None);
    }
}
