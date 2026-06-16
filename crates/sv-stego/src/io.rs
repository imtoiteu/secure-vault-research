//! **File-I/O layer** (Phase 3) — path-in / path-out wrappers over the in-memory
//! [`pipeline`]/[`detect`] codec, returning the non-secret report DTOs. This is the home of the
//! size caps, refuse-overwrite guard, atomic writes, and secret-buffer zeroization, so the `sv-app`
//! IPC surface stays thin (mirrors how `sv-platform`'s `PlatformCrypto` owns the file handling).
//!
//! Secret hygiene: the payload buffer (hide) and the recovered-plaintext buffer (extract) are
//! [`Zeroize`]d after use. The Argon2id key never leaves [`crate::seal`].

use std::path::{Path, PathBuf};

use zeroize::Zeroize;

use sv_types::{StegoDetectReport, StegoExtractReport, StegoHideReport};

use crate::detect;
use crate::error::StegoError;
use crate::pipeline::{self, HideOptions};
use crate::seal::PayloadSealer;

/// Read cap for cover / stego / image files (alloc-DoS guard; the decoded RGBA is ~4× this).
pub const MAX_IMAGE_BYTES: u64 = 64 * 1024 * 1024;
/// Read cap for the payload file.
pub const MAX_PAYLOAD_BYTES: u64 = 64 * 1024 * 1024;

/// **Hide a file.** Read `cover_path` + `payload_path`, hide the payload, and write the stego image
/// to `output_path` (refused if it exists). Returns a secret-free [`StegoHideReport`].
pub fn hide_file(
    cover_path: &Path,
    payload_path: &Path,
    output_path: &Path,
    passphrase: &[u8],
    opts: &HideOptions,
    sealer: &dyn PayloadSealer,
) -> Result<StegoHideReport, StegoError> {
    refuse_existing(output_path)?;
    let cover = read_capped(cover_path, MAX_IMAGE_BYTES)?;
    let mut payload = read_capped(payload_path, MAX_PAYLOAD_BYTES)?;

    let result = pipeline::hide_detailed(&cover, &payload, passphrase, opts, sealer);
    payload.zeroize(); // wipe our copy of the (sensitive) payload regardless of outcome
    let (stego, meta) = result?;

    write_atomic(output_path, &stego)?;

    let utilization_pct = if meta.capacity_bytes == 0 {
        0.0
    } else {
        (meta.payload_bytes as f32 / meta.capacity_bytes as f32) * 100.0
    };
    Ok(StegoHideReport {
        output_path: path_str(output_path),
        cover_format: meta.cover_format.to_string(),
        payload_bytes: meta.payload_bytes,
        capacity_bytes: meta.capacity_bytes,
        utilization_pct,
    })
}

/// **Extract to a file.** Read `stego_path`, recover the payload, and write it to `output_path`
/// (refused if it exists). Wrong passphrase / tampered carrier / no payload → the oracle-safe
/// [`StegoError::AuthFailed`]/[`StegoError::NoPayload`] (both `SV-UNAUTHORIZED`).
pub fn extract_file(
    stego_path: &Path,
    output_path: &Path,
    passphrase: &[u8],
    sealer: &dyn PayloadSealer,
) -> Result<StegoExtractReport, StegoError> {
    refuse_existing(output_path)?;
    let stego = read_capped(stego_path, MAX_IMAGE_BYTES)?;
    let mut plaintext = pipeline::extract(&stego, passphrase, sealer)?;
    let bytes_written = plaintext.len() as u64;
    let written = write_atomic(output_path, &plaintext);
    plaintext.zeroize(); // wipe the recovered plaintext copy regardless of write outcome
    written?;
    Ok(StegoExtractReport {
        output_path: path_str(output_path),
        bytes_written,
    })
}

/// **Detect on a file.** Read `image_path` and run the heuristic detector panel. Not an image →
/// `SV-MALFORMED`.
pub fn detect_file(image_path: &Path) -> Result<StegoDetectReport, StegoError> {
    let bytes = read_capped(image_path, MAX_IMAGE_BYTES)?;
    detect::detect(&bytes)
}

// --- helpers (mirror sv-platform's path/read/write discipline) --------------

fn path_str(p: &Path) -> String {
    p.to_string_lossy().into_owned()
}

fn refuse_existing(p: &Path) -> Result<(), StegoError> {
    if p.exists() {
        Err(StegoError::OutputExists)
    } else {
        Ok(())
    }
}

fn io_err(e: &std::io::Error) -> StegoError {
    if e.kind() == std::io::ErrorKind::NotFound {
        StegoError::NotFound
    } else {
        StegoError::Io(e.to_string())
    }
}

/// Read a file, refusing it (before buffering) if it exceeds `max` bytes.
fn read_capped(path: &Path, max: u64) -> Result<Vec<u8>, StegoError> {
    let meta = std::fs::metadata(path).map_err(|e| io_err(&e))?;
    if meta.len() > max {
        return Err(StegoError::FileTooLarge {
            limit_bytes: max,
            actual_bytes: meta.len(),
        });
    }
    std::fs::read(path).map_err(|e| io_err(&e))
}

/// Write `data` to `path` atomically (same-dir temp file + rename), so a failed/partial write never
/// leaves a half-written output.
fn write_atomic(path: &Path, data: &[u8]) -> Result<(), StegoError> {
    use std::io::Write;
    let dir = path
        .parent()
        .filter(|p| !p.as_os_str().is_empty())
        .map_or_else(|| PathBuf::from("."), Path::to_path_buf);
    let mut tmp = tempfile::NamedTempFile::new_in(&dir).map_err(|e| io_err(&e))?;
    tmp.write_all(data).map_err(|e| io_err(&e))?;
    tmp.flush().map_err(|e| io_err(&e))?;
    tmp.persist(path).map_err(|e| io_err(&e.error))?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::seal::testing::fast_sealer;
    use image::{DynamicImage, ImageFormat, RgbaImage};
    use std::io::Cursor;

    fn tmp() -> tempfile::TempDir {
        tempfile::tempdir().unwrap()
    }

    fn write_png(path: &Path, w: u32, h: u32) {
        let mut img = RgbaImage::new(w, h);
        for (x, y, px) in img.enumerate_pixels_mut() {
            *px = image::Rgba([(x * 3) as u8, (y * 5) as u8, (x ^ y) as u8, 255]);
        }
        let mut cur = Cursor::new(Vec::new());
        DynamicImage::ImageRgba8(img)
            .write_to(&mut cur, ImageFormat::Png)
            .unwrap();
        std::fs::write(path, cur.into_inner()).unwrap();
    }

    #[test]
    fn hide_file_then_extract_file_roundtrips() {
        let dir = tmp();
        let cover = dir.path().join("cover.png");
        let payload = dir.path().join("secret.txt");
        let stego = dir.path().join("out.png");
        let recovered = dir.path().join("recovered.txt");
        write_png(&cover, 64, 64);
        std::fs::write(&payload, b"the launch codes are 0000").unwrap();

        let sealer = fast_sealer();
        let report = hide_file(
            &cover,
            &payload,
            &stego,
            b"pw",
            &HideOptions::default(),
            &sealer,
        )
        .unwrap();
        assert_eq!(report.cover_format, "png");
        assert_eq!(report.payload_bytes, 25);
        assert!(report.capacity_bytes > 25);
        assert!(report.utilization_pct > 0.0 && report.utilization_pct < 100.0);
        assert!(Path::new(&report.output_path).exists());

        let ex = extract_file(&stego, &recovered, b"pw", &sealer).unwrap();
        assert_eq!(ex.bytes_written, 25);
        assert_eq!(
            std::fs::read(&recovered).unwrap(),
            b"the launch codes are 0000"
        );
    }

    #[test]
    fn refuses_to_overwrite_output() {
        let dir = tmp();
        let cover = dir.path().join("c.png");
        let payload = dir.path().join("p.txt");
        let stego = dir.path().join("exists.png");
        write_png(&cover, 48, 48);
        std::fs::write(&payload, b"x").unwrap();
        std::fs::write(&stego, b"already here").unwrap();

        let err = hide_file(
            &cover,
            &payload,
            &stego,
            b"pw",
            &HideOptions::default(),
            &fast_sealer(),
        )
        .unwrap_err();
        assert!(matches!(err, StegoError::OutputExists));
    }

    #[test]
    fn missing_input_is_not_found() {
        let dir = tmp();
        let err = detect_file(&dir.path().join("nope.png")).unwrap_err();
        assert!(matches!(err, StegoError::NotFound));
    }

    #[test]
    fn wrong_passphrase_on_extract_is_oracle_safe() {
        let dir = tmp();
        let cover = dir.path().join("c.png");
        let payload = dir.path().join("p.txt");
        let stego = dir.path().join("s.png");
        let out = dir.path().join("o.txt");
        write_png(&cover, 64, 64);
        std::fs::write(&payload, b"secret").unwrap();
        let sealer = fast_sealer();
        hide_file(
            &cover,
            &payload,
            &stego,
            b"right",
            &HideOptions::default(),
            &sealer,
        )
        .unwrap();
        let err = extract_file(&stego, &out, b"wrong", &sealer).unwrap_err();
        assert!(matches!(err, StegoError::AuthFailed));
        assert!(!out.exists());
    }

    #[test]
    fn detect_file_reports_on_appended_data() {
        let dir = tmp();
        let img = dir.path().join("susp.png");
        write_png(&img, 32, 32);
        let mut bytes = std::fs::read(&img).unwrap();
        bytes.extend_from_slice(b"PK\x03\x04 a hidden zip");
        std::fs::write(&img, &bytes).unwrap();
        let report = detect_file(&img).unwrap();
        assert_eq!(report.suspicion, sv_types::Suspicion::High);
    }
}
