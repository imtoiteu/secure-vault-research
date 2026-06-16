//! Steganography command segment — the toolkit's **Steganography** module (Hide / Extract / Detect).
//!
//! A vault-free, session-free peer to [`crate::CommandSurface`] (mirrors [`crate::PlatformSurface`]).
//! It wraps the stateless [`sv_stego`] file-I/O layer, converts IPC types
//! (`IpcPassphrase`/`String`/`bool`) to domain types, and projects [`sv_stego::StegoError`] →
//! oracle-safe [`sv_types::ApiError`]. It touches no vault, holds no session, and is exposed as a
//! **third** Tauri managed state, so Secure Vault's command surface is unchanged.
//!
//! Confidentiality is the reused `sv-crypto` stack (Argon2id + `secretbox`) via the in-crate sealer;
//! the carrier is concealment-only. Extraction is oracle-safe: a wrong passphrase, a tampered
//! carrier, and an image with no payload are indistinguishable (`SV-UNAUTHORIZED`).

use std::path::Path;

use sv_stego::{Argon2idSecretboxSealer, HideOptions, SelectorKind};
use sv_types::{ApiError, StegoDetectReport, StegoExtractReport, StegoHideReport};

use crate::passphrase::IpcPassphrase;

/// The Steganography command surface. Paths are plain `String`s (non-secret); passphrases are
/// [`IpcPassphrase`] (zeroizing). No method takes or returns a session.
pub trait StegoSurface {
    /// **Hide** — encrypt `payload_path` (Argon2id + `secretbox`) and embed it into `cover_path`'s
    /// LSBs, writing the stego image to `output_path` (refused if it exists). `randomize` selects a
    /// seeded-permutation placement (vs. sequential). Returns a secret-free report.
    fn stego_hide(
        &self,
        cover_path: String,
        payload_path: String,
        output_path: String,
        passphrase: IpcPassphrase,
        randomize: bool,
    ) -> Result<StegoHideReport, ApiError>;

    /// **Extract** — recover a payload from `stego_path` into the destination directory `output_dir`,
    /// saved under the original filename stored at hide time (never overwriting; the name is
    /// disambiguated if a file with it already exists). Wrong passphrase / tampered carrier / no
    /// payload all return the oracle-safe `SV-UNAUTHORIZED`.
    fn stego_extract(
        &self,
        stego_path: String,
        output_dir: String,
        passphrase: IpcPassphrase,
    ) -> Result<StegoExtractReport, ApiError>;

    /// **Detect** — run the heuristic steganalysis panel on `image_path`. Reports a suspicion level
    /// + per-detector signals; **never** asserts an image is clean.
    fn stego_detect(&self, image_path: String) -> Result<StegoDetectReport, ApiError>;
}

/// Concrete steganography surface over the [`sv_stego`] file-I/O layer. Holds the production sealer
/// (recommended Argon2id parameters); trivially `Send + Sync` for Tauri managed state.
#[derive(Debug, Default)]
pub struct StegoApp {
    sealer: Argon2idSecretboxSealer,
}

impl StegoApp {
    /// A steganography surface using the recommended (policy-floor) Argon2id parameters.
    #[must_use]
    pub fn new() -> Self {
        Self {
            sealer: Argon2idSecretboxSealer::new(),
        }
    }

    /// Construct with an explicit sealer (e.g. a fast-parameter one for tests).
    #[must_use]
    pub fn with_sealer(sealer: Argon2idSecretboxSealer) -> Self {
        Self { sealer }
    }
}

impl StegoSurface for StegoApp {
    fn stego_hide(
        &self,
        cover_path: String,
        payload_path: String,
        output_path: String,
        passphrase: IpcPassphrase,
        randomize: bool,
    ) -> Result<StegoHideReport, ApiError> {
        let secret = passphrase.into_secret();
        let opts = HideOptions {
            selector: if randomize {
                SelectorKind::Permuted
            } else {
                SelectorKind::Sequential
            },
        };
        sv_stego::hide_file(
            Path::new(&cover_path),
            Path::new(&payload_path),
            Path::new(&output_path),
            secret.expose_secret(),
            &opts,
            &self.sealer,
        )
        .map_err(ApiError::from)
    }

    fn stego_extract(
        &self,
        stego_path: String,
        output_dir: String,
        passphrase: IpcPassphrase,
    ) -> Result<StegoExtractReport, ApiError> {
        let secret = passphrase.into_secret();
        sv_stego::extract_file(
            Path::new(&stego_path),
            Path::new(&output_dir),
            secret.expose_secret(),
            &self.sealer,
        )
        .map_err(ApiError::from)
    }

    fn stego_detect(&self, image_path: String) -> Result<StegoDetectReport, ApiError> {
        sv_stego::detect_file(Path::new(&image_path)).map_err(ApiError::from)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Cursor;
    use sv_crypto_traits::{Argon2idParams, KdfParams};

    fn tmp() -> tempfile::TempDir {
        tempfile::tempdir().unwrap()
    }

    fn s(p: &Path) -> String {
        p.to_string_lossy().into_owned()
    }

    /// A StegoApp with fast Argon2id params so the IPC tests stay quick.
    fn fast_app() -> StegoApp {
        StegoApp::with_sealer(Argon2idSecretboxSealer::with_params(KdfParams::Argon2id(
            Argon2idParams {
                mem_kib: 64,
                time_cost: 1,
                parallelism: 1,
            },
        )))
    }

    fn write_cover(path: &Path) {
        use image::{DynamicImage, ImageFormat, RgbaImage};
        let mut img = RgbaImage::new(64, 64);
        for (x, y, px) in img.enumerate_pixels_mut() {
            *px = image::Rgba([(x * 4) as u8, (y * 4) as u8, (x ^ y) as u8, 255]);
        }
        let mut cur = Cursor::new(Vec::new());
        DynamicImage::ImageRgba8(img)
            .write_to(&mut cur, ImageFormat::Png)
            .unwrap();
        std::fs::write(path, cur.into_inner()).unwrap();
    }

    #[test]
    fn hide_extract_detect_surface_roundtrip() {
        let dir = tmp();
        let app = fast_app();
        let cover = dir.path().join("cover.png");
        let payload = dir.path().join("secret.txt");
        let stego = dir.path().join("stego.png");
        // Extract into a destination *folder*; the backend names the file from the recovered frame.
        let outdir = dir.path().join("rec");
        std::fs::create_dir(&outdir).unwrap();
        write_cover(&cover);
        std::fs::write(&payload, b"meet at the bridge at noon").unwrap();

        let rep = app
            .stego_hide(
                s(&cover),
                s(&payload),
                s(&stego),
                IpcPassphrase::new("pw".into()),
                true,
            )
            .unwrap();
        assert_eq!(rep.cover_format, "png");
        assert_eq!(rep.payload_bytes, 26);

        let ex = app
            .stego_extract(s(&stego), s(&outdir), IpcPassphrase::new("pw".into()))
            .unwrap();
        assert_eq!(ex.bytes_written, 26);
        // Saved under the recovered original name (secret.txt) inside the chosen destination folder.
        assert_eq!(ex.original_name.as_deref(), Some("secret.txt"));
        assert!(ex.output_path.ends_with("secret.txt"));
        assert!(outdir.join("secret.txt").exists());
        assert_eq!(
            std::fs::read(&ex.output_path).unwrap(),
            b"meet at the bridge at noon"
        );

        // Detect on the (clean-ish) stego carrier returns a report, never a "clean" claim.
        let det = app.stego_detect(s(&stego)).unwrap();
        assert!(det.caveat.to_lowercase().contains("not proof"));
    }

    #[test]
    fn wrong_passphrase_is_oracle_safe_unauthorized() {
        let dir = tmp();
        let app = fast_app();
        let cover = dir.path().join("c.png");
        let payload = dir.path().join("p.txt");
        let stego = dir.path().join("s.png");
        let outdir = dir.path().join("rec");
        std::fs::create_dir(&outdir).unwrap();
        write_cover(&cover);
        std::fs::write(&payload, b"secret").unwrap();
        app.stego_hide(
            s(&cover),
            s(&payload),
            s(&stego),
            IpcPassphrase::new("right".into()),
            true,
        )
        .unwrap();

        let err = app
            .stego_extract(s(&stego), s(&outdir), IpcPassphrase::new("wrong".into()))
            .unwrap_err();
        assert_eq!(err, ApiError::Unauthorized);
        assert_eq!(err.code(), "SV-UNAUTHORIZED");
        assert_eq!(std::fs::read_dir(&outdir).unwrap().count(), 0);
    }

    #[test]
    fn detect_flags_appended_payload_high() {
        let dir = tmp();
        let app = fast_app();
        let img = dir.path().join("susp.png");
        write_cover(&img);
        let mut bytes = std::fs::read(&img).unwrap();
        bytes.extend_from_slice(b"PK\x03\x04 hidden archive");
        std::fs::write(&img, &bytes).unwrap();
        let det = app.stego_detect(s(&img)).unwrap();
        assert_eq!(det.suspicion, sv_types::Suspicion::High);
    }

    #[test]
    fn missing_cover_is_not_found() {
        let dir = tmp();
        let app = fast_app();
        let missing = dir.path().join("nope.png");
        let err = app
            .stego_extract(
                s(&missing),
                s(&dir.path().join("o.txt")),
                IpcPassphrase::new("pw".into()),
            )
            .unwrap_err();
        assert_eq!(err, ApiError::NotFound);
    }
}
