//! Watermarking command segment — the toolkit's **Watermarking** module (Embed / Verify).
//!
//! A vault-free, session-free peer to [`crate::CommandSurface`] (mirrors [`crate::StegoSurface`]).
//! It wraps the stateless [`sv_watermark`] codec (an invisible, keyed, **fragile** tamper-evident
//! image watermark), converts IPC types (`IpcPassphrase`/`String`), and projects
//! [`sv_watermark::WatermarkError`] → oracle-safe [`sv_types::ApiError`] (no new code). It touches no
//! vault, holds no session, and is exposed as a **fifth** Tauri managed state, so Secure Vault's
//! command surface is unchanged.
//!
//! The watermark is non-secret (it certifies "unchanged since marked with this key", not secrecy of a
//! payload); the only secret is the zeroizing passphrase used to key the per-block MAC.

use std::path::Path;

use sv_types::{ApiError, WatermarkEmbedReport, WatermarkVerifyReport};

use crate::passphrase::IpcPassphrase;

/// The Watermarking command surface. Paths are plain `String`s (non-secret); the passphrase is an
/// [`IpcPassphrase`] (zeroizing). No method takes or returns a session.
pub trait WatermarkSurface {
    /// **Embed** — write a watermarked copy of `input` to `output` (PNG/BMP; refused if it exists;
    /// the input is never modified in place). Any later edit to the image breaks the mark.
    fn watermark_embed(
        &self,
        input: String,
        output: String,
        passphrase: IpcPassphrase,
    ) -> Result<WatermarkEmbedReport, ApiError>;

    /// **Verify** — check `input` against the key: `Intact` (unchanged since marked), `Tampered`
    /// (altered after marking; with a per-block count), or `NotWatermarked` (no mark / wrong key).
    fn watermark_verify(
        &self,
        input: String,
        passphrase: IpcPassphrase,
    ) -> Result<WatermarkVerifyReport, ApiError>;
}

/// Concrete watermarking surface over the stateless [`sv_watermark`] codec. Holds no state, so it is
/// trivially `Send + Sync` for Tauri managed state.
#[derive(Debug, Default)]
pub struct WatermarkApp;

impl WatermarkApp {
    #[must_use]
    pub fn new() -> Self {
        Self
    }
}

impl WatermarkSurface for WatermarkApp {
    fn watermark_embed(
        &self,
        input: String,
        output: String,
        passphrase: IpcPassphrase,
    ) -> Result<WatermarkEmbedReport, ApiError> {
        let secret = passphrase.into_secret();
        sv_watermark::embed(
            Path::new(&input),
            Path::new(&output),
            secret.expose_secret(),
        )
        .map_err(ApiError::from)
    }

    fn watermark_verify(
        &self,
        input: String,
        passphrase: IpcPassphrase,
    ) -> Result<WatermarkVerifyReport, ApiError> {
        let secret = passphrase.into_secret();
        sv_watermark::verify(Path::new(&input), secret.expose_secret()).map_err(ApiError::from)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use sv_types::WatermarkVerdict;

    fn tmp() -> tempfile::TempDir {
        tempfile::tempdir().unwrap()
    }

    fn s(p: &Path) -> String {
        p.to_string_lossy().into_owned()
    }

    fn write_cover(path: &Path) {
        use image::{Rgba, RgbaImage};
        let mut img = RgbaImage::new(96, 80);
        for (x, y, px) in img.enumerate_pixels_mut() {
            *px = Rgba([(x * 3) as u8, (y * 5) as u8, (x ^ y) as u8, 255]);
        }
        img.save(path).unwrap();
    }

    #[test]
    fn embed_verify_surface_roundtrip_and_tamper() {
        let dir = tmp();
        let app = WatermarkApp::new();
        let cover = dir.path().join("c.png");
        let marked = dir.path().join("c.wm.png");
        write_cover(&cover);

        let rep = app
            .watermark_embed(s(&cover), s(&marked), IpcPassphrase::new("pw".into()))
            .unwrap();
        assert!(rep.blocks >= 1);

        // Intact right after embedding.
        let v = app
            .watermark_verify(s(&marked), IpcPassphrase::new("pw".into()))
            .unwrap();
        assert_eq!(v.verdict, WatermarkVerdict::Intact);

        // Wrong key → NotWatermarked (no oracle on which is "right").
        let v = app
            .watermark_verify(s(&marked), IpcPassphrase::new("nope".into()))
            .unwrap();
        assert_eq!(v.verdict, WatermarkVerdict::NotWatermarked);

        // A content edit → Tampered (localized).
        let mut img = image::open(&marked).unwrap().to_rgba8();
        img.get_pixel_mut(10, 10).0[1] ^= 0x80;
        let edited = dir.path().join("edited.png");
        img.save(&edited).unwrap();
        let v = app
            .watermark_verify(s(&edited), IpcPassphrase::new("pw".into()))
            .unwrap();
        assert_eq!(v.verdict, WatermarkVerdict::Tampered);
        assert!(v.tampered_blocks >= 1 && v.tampered_blocks < v.total_blocks);
    }

    #[test]
    fn embed_refuses_overwrite_and_missing_is_not_found() {
        let dir = tmp();
        let app = WatermarkApp::new();
        let cover = dir.path().join("c.png");
        write_cover(&cover);
        let exists = dir.path().join("there.png");
        std::fs::write(&exists, b"x").unwrap();
        let err = app
            .watermark_embed(s(&cover), s(&exists), IpcPassphrase::new("pw".into()))
            .unwrap_err();
        assert_eq!(err, ApiError::OutputExists);

        let err = app
            .watermark_verify(
                s(&dir.path().join("nope.png")),
                IpcPassphrase::new("pw".into()),
            )
            .unwrap_err();
        assert_eq!(err, ApiError::NotFound);
    }
}
