//! **File-I/O layer** (Phase 3) — path-in / path-out wrappers over the in-memory
//! [`pipeline`]/[`detect`] codec, returning the non-secret report DTOs. This is the home of the
//! size caps, refuse-overwrite guard, atomic writes, and secret-buffer zeroization, so the `sv-app`
//! IPC surface stays thin (mirrors how `sv-platform`'s `PlatformCrypto` owns the file handling).
//!
//! Secret hygiene: the payload buffer (hide) and the recovered-plaintext buffer (extract) are
//! [`Zeroize`]d after use. The Argon2id key never leaves [`crate::seal`].

use std::path::{Path, PathBuf};

use zeroize::Zeroize;

use sv_types::{nameframe, StegoDetectReport, StegoExtractReport, StegoHideReport};

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
    let mut raw = read_capped(payload_path, MAX_PAYLOAD_BYTES)?;
    let payload_bytes = raw.len() as u64;

    // Frame the payload behind its original basename (inside the encrypted region — never cleartext)
    // so extract can restore an openable, correctly-named file. The frame consumes a little capacity.
    let name = nameframe::basename(&payload_path.to_string_lossy());
    let mut framed = nameframe::frame(name.as_deref(), &raw);
    raw.zeroize(); // wipe our copy of the (sensitive) payload regardless of outcome

    let result = pipeline::hide_detailed(&cover, &framed, passphrase, opts, sealer);
    framed.zeroize();
    let (stego, meta) = result?;

    write_atomic(output_path, &stego)?;

    // `meta.payload_bytes` is the framed length (the bits actually consumed); utilization reflects
    // that, while the report's `payload_bytes` is the user's real payload size.
    let utilization_pct = if meta.capacity_bytes == 0 {
        0.0
    } else {
        (meta.payload_bytes as f32 / meta.capacity_bytes as f32) * 100.0
    };
    Ok(StegoHideReport {
        output_path: path_str(output_path),
        cover_format: meta.cover_format.to_string(),
        payload_bytes,
        capacity_bytes: meta.capacity_bytes,
        utilization_pct,
    })
}

/// **Extract into a directory.** Read `stego_path`, recover the payload, and write it into
/// `output_dir` **under the original filename stored at hide time** (re-sanitized to a bare basename
/// — a crafted carrier could embed path separators / `..`), so the recovered file opens by default.
/// The destination is a *folder*, not a filename: the payload's true name/type is unknowable until
/// decryption, so honouring a caller-chosen (image-extensioned) filename is exactly what produced an
/// unopenable file. An existing file is **never overwritten** — the name is disambiguated
/// (`report (2).docx`, …). A payload with no stored name (legacy frame) is written as
/// [`DEFAULT_RECOVERED_NAME`]. Wrong passphrase / tampered carrier / no payload → the oracle-safe
/// [`StegoError::AuthFailed`]/[`StegoError::NoPayload`] (both `SV-UNAUTHORIZED`).
pub fn extract_file(
    stego_path: &Path,
    output_dir: &Path,
    passphrase: &[u8],
    sealer: &dyn PayloadSealer,
) -> Result<StegoExtractReport, StegoError> {
    let stego = read_capped(stego_path, MAX_IMAGE_BYTES)?;
    let mut framed = pipeline::extract(&stego, passphrase, sealer)?;
    // Recover the original name (if framed at hide time) and the bare payload bytes.
    let (original_name, mut payload) = nameframe::unframe(&framed);
    framed.zeroize();
    let bytes_written = payload.len() as u64;
    let written = write_into_dir(output_dir, original_name.as_deref(), &payload);
    payload.zeroize(); // wipe the recovered plaintext copy regardless of write outcome
    let final_path = written?;
    Ok(StegoExtractReport {
        output_path: path_str(&final_path),
        bytes_written,
        original_name,
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

/// Default basename for a recovered payload that carries no stored name (legacy / raw frame). Rare;
/// the real extension is unknown, so a generic name is the honest choice.
const DEFAULT_RECOVERED_NAME: &str = "recovered.bin";

/// Write `data` into `dir` under the recovered `original_name` (re-sanitized to a bare basename —
/// path-traversal guard), disambiguating against existing files so nothing is overwritten. Returns
/// the path actually written.
fn write_into_dir(
    dir: &Path,
    original_name: Option<&str>,
    data: &[u8],
) -> Result<PathBuf, StegoError> {
    let name = original_name
        .and_then(nameframe::basename)
        .unwrap_or_else(|| DEFAULT_RECOVERED_NAME.to_string());
    let target = if dir.as_os_str().is_empty() {
        PathBuf::from(name)
    } else {
        dir.join(name)
    };
    let final_path = unique_path(target)?;
    write_atomic(&final_path, data)?;
    Ok(final_path)
}

/// Return `target` if it's free, else `<stem> (2).<ext>`, `<stem> (3).<ext>`, … so an existing file
/// is **never overwritten** (mirrors common desktop "save" disambiguation). Errors as
/// [`StegoError::OutputExists`] only in the absurd case that thousands of variants all exist.
fn unique_path(target: PathBuf) -> Result<PathBuf, StegoError> {
    if !target.exists() {
        return Ok(target);
    }
    let parent = target.parent();
    let stem = target
        .file_stem()
        .map_or_else(String::new, |s| s.to_string_lossy().into_owned());
    let ext = target.extension().map(|e| e.to_string_lossy().into_owned());
    for n in 2..=9999u32 {
        let fname = match &ext {
            Some(e) => format!("{stem} ({n}).{e}"),
            None => format!("{stem} ({n})"),
        };
        let candidate = match parent {
            Some(p) if !p.as_os_str().is_empty() => p.join(&fname),
            _ => PathBuf::from(&fname),
        };
        if !candidate.exists() {
            return Ok(candidate);
        }
    }
    Err(StegoError::OutputExists)
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
        // Extract into a destination *folder*; the backend names the file from the recovered frame.
        let outdir = dir.path().join("rec");
        std::fs::create_dir(&outdir).unwrap();
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

        let ex = extract_file(&stego, &outdir, b"pw", &sealer).unwrap();
        assert_eq!(ex.bytes_written, 25);
        // The original payload filename round-trips out of the encrypted frame, and the file is
        // SAVED under that name inside the chosen destination folder — so it opens by default.
        assert_eq!(ex.original_name.as_deref(), Some("secret.txt"));
        assert_eq!(ex.output_path, path_str(&outdir.join("secret.txt")));
        assert!(outdir.join("secret.txt").exists());
        assert_eq!(
            std::fs::read(&ex.output_path).unwrap(),
            b"the launch codes are 0000"
        );
    }

    #[test]
    fn extract_saves_under_original_name_for_real_file_types() {
        // The reported defect, end-to-end: hide a file of each real type inside a PNG, then extract
        // into a destination folder. The saved file must carry the ORIGINAL name+extension and the
        // exact original bytes (magic intact) so it opens — never the carrier's image extension.
        let sealer = fast_sealer();
        let cases: [(&str, &[u8]); 4] = [
            (
                "report.docx",
                b"PK\x03\x04\x14\x00 docx is a zip container ....",
            ), // ZIP/OOXML magic
            (
                "invoice.pdf",
                b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n1 0 obj <<>> ....",
            ),
            ("backup.zip", b"PK\x03\x04 plain zip archive body ........"),
            (
                "avatar.png",
                b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR payload ....",
            ),
        ];
        for (name, body) in cases {
            let dir = tmp();
            let cover = dir.path().join("cover.png");
            write_png(&cover, 96, 96); // ample capacity for these small bodies + the name frame
            let payload = dir.path().join(name);
            std::fs::write(&payload, body).unwrap();
            let stego = dir.path().join("cover.png.stego.png");
            hide_file(
                &cover,
                &payload,
                &stego,
                b"pw",
                &HideOptions::default(),
                &sealer,
            )
            .unwrap();

            // Extract into a destination folder; the backend names the file from the recovered
            // frame, restoring the original name + extension regardless of the carrier's type.
            let outdir = dir.path().join("rec");
            std::fs::create_dir(&outdir).unwrap();
            let ex = extract_file(&stego, &outdir, b"pw", &sealer).unwrap();

            assert_eq!(
                ex.original_name.as_deref(),
                Some(name),
                "name recovered for {name}"
            );
            assert_eq!(
                ex.output_path,
                path_str(&outdir.join(name)),
                "saved under original name for {name}"
            );
            let written = std::fs::read(&ex.output_path).unwrap();
            assert_eq!(written, body, "exact bytes for {name}");
            assert_eq!(&written[..4], &body[..4], "magic bytes intact for {name}");
        }
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
        let outdir = dir.path().join("rec");
        std::fs::create_dir(&outdir).unwrap();
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
        let err = extract_file(&stego, &outdir, b"wrong", &sealer).unwrap_err();
        assert!(matches!(err, StegoError::AuthFailed));
        assert_eq!(
            std::fs::read_dir(&outdir).unwrap().count(),
            0,
            "nothing is written on a failed extract"
        );
    }

    #[test]
    fn extract_disambiguates_existing_target_instead_of_overwriting() {
        let dir = tmp();
        let cover = dir.path().join("cover.png");
        let payload = dir.path().join("secret.txt");
        let stego = dir.path().join("stego.png");
        write_png(&cover, 80, 80);
        std::fs::write(&payload, b"second extraction").unwrap();
        let sealer = fast_sealer();
        hide_file(
            &cover,
            &payload,
            &stego,
            b"pw",
            &HideOptions::default(),
            &sealer,
        )
        .unwrap();

        // A file with the recovered name already exists in the destination folder.
        let outdir = dir.path().join("rec");
        std::fs::create_dir(&outdir).unwrap();
        std::fs::write(outdir.join("secret.txt"), b"do not clobber").unwrap();

        let ex = extract_file(&stego, &outdir, b"pw", &sealer).unwrap();
        assert_eq!(ex.original_name.as_deref(), Some("secret.txt"));
        assert_eq!(
            ex.output_path,
            path_str(&outdir.join("secret (2).txt")),
            "disambiguated to avoid overwrite: {}",
            ex.output_path
        );
        // The pre-existing file is untouched; the recovery is the new, disambiguated file.
        assert_eq!(
            std::fs::read(outdir.join("secret.txt")).unwrap(),
            b"do not clobber"
        );
        assert_eq!(
            std::fs::read(&ex.output_path).unwrap(),
            b"second extraction"
        );
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
