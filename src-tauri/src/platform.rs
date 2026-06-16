//! Platform command segment — the toolkit's **Integrity** and **Cryptography** modules.
//!
//! A vault-free, session-free peer to [`crate::CommandSurface`]. It wraps the stateless
//! [`sv_platform::PlatformCrypto`] services, converts IPC types (`IpcPassphrase`/`String`) to
//! domain types, and projects [`sv_platform::PlatformError`] → oracle-safe
//! [`sv_types::ApiError`]. It touches no vault, holds no session, and is exposed as a **second**
//! Tauri managed state, so Secure Vault's command surface is unchanged.

use std::path::{Path, PathBuf};

use sv_platform::{
    decode_share_string, IntegrityVerification, PlatformCrypto, ShareSplitOutput, SignatureCheck,
};
use sv_types::{
    ApiError, IntegrityReport, QrExportReport, RecoverReport, ShareSplitReport, SigningKeypairInfo,
    VerifyIntegrityReport,
};

use crate::passphrase::IpcPassphrase;

/// The Integrity + Cryptography command surface. Paths are plain `String`s (non-secret);
/// passphrases are [`IpcPassphrase`] (zeroizing). No method takes or returns a session.
pub trait PlatformSurface {
    /// **Hash File** — streaming BLAKE3 of an arbitrary file; returns lowercase hex.
    fn hash_file(&self, path: String) -> Result<String, ApiError>;

    /// **Verify Signature** — minisign verify of `path` against a detached signature + public key.
    /// A failed verification returns `signature_ok: false` (not an error).
    fn verify_signature(
        &self,
        path: String,
        signature_path: String,
        public_key_path: String,
    ) -> Result<IntegrityReport, ApiError>;

    /// **Verify Integrity** — check `path` against an expected BLAKE3 hash **and/or** a detached
    /// signature + public key (composes Hash File + Verify Signature). At least one check must be
    /// supplied. A hash mismatch or invalid signature is reported as `verified: false` (not an
    /// error); only missing/oversized/malformed inputs are errors.
    fn verify_integrity(
        &self,
        path: String,
        expected_hash_hex: Option<String>,
        signature_path: Option<String>,
        public_key_path: Option<String>,
    ) -> Result<VerifyIntegrityReport, ApiError>;

    /// **Encrypt File** — passphrase (Argon2id + secretbox) → `.svenc`; returns the output path.
    fn encrypt_file(
        &self,
        input: String,
        output: String,
        passphrase: IpcPassphrase,
    ) -> Result<String, ApiError>;

    /// **Decrypt File** — open a `.svenc` with the passphrase; returns the output path.
    fn decrypt_file(
        &self,
        input: String,
        output: String,
        passphrase: IpcPassphrase,
    ) -> Result<String, ApiError>;

    /// **Generate signing keypair** — writes `<name>.pub` + encrypted `<name>.svkey`.
    fn generate_signing_keypair(
        &self,
        out_dir: String,
        name: String,
        passphrase: IpcPassphrase,
    ) -> Result<SigningKeypairInfo, ApiError>;

    /// **Sign File** — minisign-sign with the passphrase-unwrapped `.svkey`; returns the sig path.
    fn sign_file(
        &self,
        input: String,
        signing_key_path: String,
        passphrase: IpcPassphrase,
    ) -> Result<String, ApiError>;

    /// **Split a secret** — split typed `secret` bytes into `shares_total` pieces (any `threshold`
    /// of which recover it), writing one payload file + `n` piece files into `out_dir`. The report
    /// includes per-piece copy-paste Base64 strings (the text-workflow deliverable). Session-free.
    fn shares_split_secret(
        &self,
        secret: IpcPassphrase,
        shares_total: u8,
        threshold: u8,
        out_dir: String,
    ) -> Result<ShareSplitReport, ApiError>;

    /// **Split a file** — the same engine over a file's bytes. Per-piece Base64 strings are
    /// **omitted** (file pieces are distributed as files, not transcribed). Session-free.
    fn shares_split_file(
        &self,
        input: String,
        shares_total: u8,
        threshold: u8,
        out_dir: String,
    ) -> Result<ShareSplitReport, ApiError>;

    /// **Recover from pieces** — reconstruct from piece files (`share_paths`) and/or pasted Base64
    /// piece strings (`share_strings`) plus the payload file; writes the recovered plaintext to
    /// `out_path`. Wrong/tampered inputs are the oracle-safe `SV-UNAUTHORIZED`. Session-free.
    fn shares_recover_secret(
        &self,
        share_paths: Vec<String>,
        share_strings: Vec<String>,
        payload_path: String,
        out_path: String,
    ) -> Result<RecoverReport, ApiError>;

    /// **Secure QR Transfer — export** — render each existing piece string (`share_b64`) as a QR
    /// **PNG** in `out_dir` (`piece-1.png`, …). Pure transport of an already-produced, non-secret
    /// piece; no re-split, no new crypto. Returns the written image paths. Session-free.
    fn shares_export_qr(
        &self,
        share_b64: Vec<String>,
        out_dir: String,
    ) -> Result<QrExportReport, ApiError>;

    /// **Secure QR Transfer — recover** — decode a QR code from each image in `qr_paths` to a piece
    /// string, then recover through the **unchanged** Secret Sharing engine (same `payload_path`
    /// requirement, same oracle-safe errors). Wrong/tampered pieces still merge to
    /// `SV-UNAUTHORIZED`; an unreadable image / absent QR is `SV-MALFORMED`. Session-free.
    fn shares_recover_from_qr(
        &self,
        qr_paths: Vec<String>,
        payload_path: String,
        out_path: String,
    ) -> Result<RecoverReport, ApiError>;

    /// **Copy a file** to a new path, refusing to overwrite. A non-crypto UI convenience used to save
    /// a recovered file under its restored original name. Returns the destination path. Session-free.
    fn copy_file(&self, from: String, to: String) -> Result<String, ApiError>;
}

/// Project the engine's [`ShareSplitOutput`] onto the IPC [`ShareSplitReport`] DTO (field-for-field;
/// the DEK never appears in either).
fn split_report(out: ShareSplitOutput) -> ShareSplitReport {
    ShareSplitReport {
        payload_path: out.payload_path,
        share_paths: out.share_paths,
        share_b64: out.share_b64,
        group_id_hex: out.group_id_hex,
        shares_total: out.shares_total,
        threshold: out.threshold,
    }
}

/// Concrete platform surface over [`PlatformCrypto`]. Holds no state beyond the (zero-sized)
/// service adapters, so it is trivially `Send + Sync` for Tauri managed state.
#[derive(Debug, Default)]
pub struct PlatformApp {
    crypto: PlatformCrypto,
}

impl PlatformApp {
    #[must_use]
    pub fn new() -> Self {
        Self {
            crypto: PlatformCrypto::new(),
        }
    }
}

impl PlatformSurface for PlatformApp {
    fn hash_file(&self, path: String) -> Result<String, ApiError> {
        self.crypto
            .hash_file(Path::new(&path))
            .map_err(ApiError::from)
    }

    fn verify_signature(
        &self,
        path: String,
        signature_path: String,
        public_key_path: String,
    ) -> Result<IntegrityReport, ApiError> {
        let SignatureCheck {
            valid,
            file_blake3_hex,
        } = self
            .crypto
            .verify_signature(
                Path::new(&path),
                Path::new(&signature_path),
                Path::new(&public_key_path),
            )
            .map_err(ApiError::from)?;
        Ok(IntegrityReport {
            // Verify Signature performs no expected-hash comparison, so no content-hash match is
            // established here — only `signature_ok` is meaningful on this surface. Reporting the
            // signature verdict in `blake3_ok` (whose contract is "BLAKE3 content hash matched")
            // would misrepresent it to any consumer that reads the field (M1).
            blake3_ok: false,
            signature_ok: valid,
            computed_hash_hex: file_blake3_hex,
        })
    }

    fn verify_integrity(
        &self,
        path: String,
        expected_hash_hex: Option<String>,
        signature_path: Option<String>,
        public_key_path: Option<String>,
    ) -> Result<VerifyIntegrityReport, ApiError> {
        let signature_path = signature_path.as_deref().map(Path::new);
        let public_key_path = public_key_path.as_deref().map(Path::new);
        let IntegrityVerification {
            hash_checked,
            hash_matched,
            signature_checked,
            signature_valid,
            computed_hash_hex,
            verified,
        } = self
            .crypto
            .verify_integrity(
                Path::new(&path),
                expected_hash_hex.as_deref(),
                signature_path,
                public_key_path,
            )
            .map_err(ApiError::from)?;
        Ok(VerifyIntegrityReport {
            hash_checked,
            hash_matched,
            signature_checked,
            signature_valid,
            computed_hash_hex,
            verified,
        })
    }

    fn encrypt_file(
        &self,
        input: String,
        output: String,
        passphrase: IpcPassphrase,
    ) -> Result<String, ApiError> {
        let secret = passphrase.into_secret();
        self.crypto
            .encrypt_file(
                Path::new(&input),
                Path::new(&output),
                secret.expose_secret(),
            )
            .map_err(ApiError::from)
    }

    fn decrypt_file(
        &self,
        input: String,
        output: String,
        passphrase: IpcPassphrase,
    ) -> Result<String, ApiError> {
        let secret = passphrase.into_secret();
        self.crypto
            .decrypt_file(
                Path::new(&input),
                Path::new(&output),
                secret.expose_secret(),
            )
            .map_err(ApiError::from)
    }

    fn generate_signing_keypair(
        &self,
        out_dir: String,
        name: String,
        passphrase: IpcPassphrase,
    ) -> Result<SigningKeypairInfo, ApiError> {
        let secret = passphrase.into_secret();
        let kp = self
            .crypto
            .generate_signing_keypair(Path::new(&out_dir), &name, secret.expose_secret())
            .map_err(ApiError::from)?;
        Ok(SigningKeypairInfo {
            public_key_path: kp.public_key_path,
            secret_key_path: kp.secret_key_path,
            public_key_hex: kp.public_key_hex,
        })
    }

    fn sign_file(
        &self,
        input: String,
        signing_key_path: String,
        passphrase: IpcPassphrase,
    ) -> Result<String, ApiError> {
        let secret = passphrase.into_secret();
        self.crypto
            .sign_file(
                Path::new(&input),
                Path::new(&signing_key_path),
                secret.expose_secret(),
            )
            .map_err(ApiError::from)
    }

    fn shares_split_secret(
        &self,
        secret: IpcPassphrase,
        shares_total: u8,
        threshold: u8,
        out_dir: String,
    ) -> Result<ShareSplitReport, ApiError> {
        let secret = secret.into_secret();
        let out = self
            .crypto
            .split_secret(
                secret.expose_secret(),
                shares_total,
                threshold,
                Path::new(&out_dir),
            )
            .map_err(ApiError::from)?;
        Ok(split_report(out))
    }

    fn shares_split_file(
        &self,
        input: String,
        shares_total: u8,
        threshold: u8,
        out_dir: String,
    ) -> Result<ShareSplitReport, ApiError> {
        let mut out = self
            .crypto
            .split_file(
                Path::new(&input),
                shares_total,
                threshold,
                Path::new(&out_dir),
            )
            .map_err(ApiError::from)?;
        // File pieces travel as files, not transcribed strings — don't surface the secret codes.
        out.share_b64.clear();
        Ok(split_report(out))
    }

    fn shares_recover_secret(
        &self,
        share_paths: Vec<String>,
        share_strings: Vec<String>,
        payload_path: String,
        out_path: String,
    ) -> Result<RecoverReport, ApiError> {
        let mut paths: Vec<PathBuf> = share_paths.iter().map(PathBuf::from).collect();

        // Bridge pasted Base64 piece codes → throwaway piece files for the unchanged, file-based
        // engine. `_staged` holds the TempDir until after recovery so cleanup is RAII (incl. on the
        // early `?` return), keeping the transient on-disk pieces short-lived.
        let _staged: Option<tempfile::TempDir> = {
            let pasted: Vec<&String> = share_strings
                .iter()
                .filter(|s| !s.trim().is_empty())
                .collect();
            if pasted.is_empty() {
                None
            } else {
                let dir = tempfile::tempdir().map_err(|_| ApiError::Io {
                    detail: "could not create a temporary working folder".into(),
                })?;
                for (i, s) in pasted.iter().enumerate() {
                    let bytes = decode_share_string(s).map_err(ApiError::from)?;
                    let p = dir.path().join(format!("pasted-{i}.svss"));
                    std::fs::write(&p, &bytes).map_err(|_| ApiError::Io {
                        detail: "could not stage a pasted piece".into(),
                    })?;
                    paths.push(p);
                }
                Some(dir)
            }
        };

        let rep = self
            .crypto
            .recover_secret(&paths, Path::new(&payload_path), Path::new(&out_path))
            .map_err(ApiError::from)?;
        Ok(RecoverReport {
            output_path: rep.output_path,
            bytes_written: rep.bytes_written,
            original_name: rep.original_name,
        })
    }

    fn shares_export_qr(
        &self,
        share_b64: Vec<String>,
        out_dir: String,
    ) -> Result<QrExportReport, ApiError> {
        if share_b64.is_empty() {
            return Err(ApiError::InvalidInput {
                detail: "no pieces were provided to export".into(),
            });
        }
        let dir = Path::new(&out_dir);
        let mut image_paths = Vec::with_capacity(share_b64.len());
        for (i, piece) in share_b64.iter().enumerate() {
            let out = dir.join(format!("piece-{}.png", i + 1));
            // sv_qr refuses to overwrite (OutputExists) and never trusts the content (transport only).
            let written = sv_qr::encode_text_to_png(piece, &out).map_err(ApiError::from)?;
            image_paths.push(written.to_string_lossy().into_owned());
        }
        Ok(QrExportReport { image_paths })
    }

    fn shares_recover_from_qr(
        &self,
        qr_paths: Vec<String>,
        payload_path: String,
        out_path: String,
    ) -> Result<RecoverReport, ApiError> {
        if qr_paths.is_empty() {
            return Err(ApiError::InvalidInput {
                detail: "no QR images were provided".into(),
            });
        }
        // Decode each QR image to its piece string (fail-closed: a bad image / absent QR is
        // SV-MALFORMED), then route the strings through the UNCHANGED recover bridge — identical
        // staging, identical oracle-safe error semantics as the pasted-codes path.
        // Decode *every* QR in each image (not just the first) so a photo containing more than one
        // piece QR contributes all of them, rather than silently dropping the rest (M3).
        let mut share_strings = Vec::with_capacity(qr_paths.len());
        for p in &qr_paths {
            let texts = sv_qr::decode_png_all(Path::new(p)).map_err(ApiError::from)?;
            share_strings.extend(texts);
        }
        self.shares_recover_secret(Vec::new(), share_strings, payload_path, out_path)
    }

    fn copy_file(&self, from: String, to: String) -> Result<String, ApiError> {
        self.crypto
            .copy_file(Path::new(&from), Path::new(&to))
            .map_err(ApiError::from)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn tmp() -> tempfile::TempDir {
        tempfile::tempdir().unwrap()
    }

    #[test]
    fn integrity_and_crypto_surface_roundtrip() {
        let dir = tmp();
        let app = PlatformApp::new();

        // Hash File.
        let f = dir.path().join("f.txt");
        std::fs::write(&f, b"hash me").unwrap();
        let h = app.hash_file(f.to_string_lossy().into_owned()).unwrap();
        assert_eq!(h.len(), 64);

        // Generate keypair → Sign File → Verify Signature (closed loop).
        let kp = app
            .generate_signing_keypair(
                dir.path().to_string_lossy().into_owned(),
                "id".into(),
                IpcPassphrase::new("pw".into()),
            )
            .unwrap();
        let sig = app
            .sign_file(
                f.to_string_lossy().into_owned(),
                kp.secret_key_path.clone(),
                IpcPassphrase::new("pw".into()),
            )
            .unwrap();
        let report = app
            .verify_signature(
                f.to_string_lossy().into_owned(),
                sig,
                kp.public_key_path.clone(),
            )
            .unwrap();
        // Verify Signature establishes signature validity only; it compares no expected hash, so
        // `blake3_ok` is `false` (no content-hash match was checked) — not the signature verdict (M1).
        assert!(report.signature_ok);
        assert!(!report.blake3_ok);

        // Encrypt File → Decrypt File.
        let enc = dir.path().join("f.svenc");
        let dec = dir.path().join("f.out");
        app.encrypt_file(
            f.to_string_lossy().into_owned(),
            enc.to_string_lossy().into_owned(),
            IpcPassphrase::new("pw".into()),
        )
        .unwrap();
        app.decrypt_file(
            enc.to_string_lossy().into_owned(),
            dec.to_string_lossy().into_owned(),
            IpcPassphrase::new("pw".into()),
        )
        .unwrap();
        assert_eq!(std::fs::read(&dec).unwrap(), b"hash me");
    }

    #[test]
    fn verify_integrity_surface_hash_and_signature() {
        let dir = tmp();
        let app = PlatformApp::new();
        let f = dir.path().join("f.txt");
        std::fs::write(&f, b"verify integrity over IPC").unwrap();
        let hash = app.hash_file(s(&f)).unwrap();

        // Mint a keypair + sign the file for the signature half (closed loop, no vault).
        let kp = app
            .generate_signing_keypair(s(dir.path()), "id".into(), IpcPassphrase::new("pw".into()))
            .unwrap();
        let sig = app
            .sign_file(
                s(&f),
                kp.secret_key_path.clone(),
                IpcPassphrase::new("pw".into()),
            )
            .unwrap();

        // Both checks requested and both pass.
        let r = app
            .verify_integrity(
                s(&f),
                Some(hash.clone()),
                Some(sig.clone()),
                Some(kp.public_key_path.clone()),
            )
            .unwrap();
        assert!(r.hash_checked && r.hash_matched);
        assert!(r.signature_checked && r.signature_valid);
        assert!(r.verified && r.computed_hash_hex == hash);

        // Wrong expected hash → a `verified: false` verdict, NOT an error.
        let r = app
            .verify_integrity(s(&f), Some("00".repeat(32)), None, None)
            .unwrap();
        assert!(r.hash_checked && !r.hash_matched && !r.verified && !r.signature_checked);

        // Neither check requested → SV-INVALID-INPUT (a coded error, no oracle).
        let err = app.verify_integrity(s(&f), None, None, None).unwrap_err();
        assert_eq!(err.code(), "SV-INVALID-INPUT");

        // Missing file → SV-NOT-FOUND.
        let err = app
            .verify_integrity(
                s(&dir.path().join("nope")),
                Some("ab".repeat(32)),
                None,
                None,
            )
            .unwrap_err();
        assert_eq!(err, ApiError::NotFound);
    }

    #[test]
    fn wrong_passphrase_is_oracle_safe_unauthorized() {
        let dir = tmp();
        let app = PlatformApp::new();
        let f = dir.path().join("f");
        std::fs::write(&f, b"data").unwrap();
        let enc = dir.path().join("f.svenc");
        app.encrypt_file(
            f.to_string_lossy().into_owned(),
            enc.to_string_lossy().into_owned(),
            IpcPassphrase::new("right".into()),
        )
        .unwrap();
        let dec = dir.path().join("f.out");
        let err = app
            .decrypt_file(
                enc.to_string_lossy().into_owned(),
                dec.to_string_lossy().into_owned(),
                IpcPassphrase::new("wrong".into()),
            )
            .unwrap_err();
        assert_eq!(err, ApiError::Unauthorized);
        assert_eq!(err.code(), "SV-UNAUTHORIZED");
    }

    fn s(p: &Path) -> String {
        p.to_string_lossy().into_owned()
    }

    #[test]
    fn shares_split_secret_then_recover_from_files() {
        let dir = tmp();
        let app = PlatformApp::new();
        let rep = app
            .shares_split_secret(
                IpcPassphrase::new("master passphrase".into()),
                5,
                3,
                s(dir.path()),
            )
            .unwrap();
        // One payload + n piece files; text workflow exposes the copy-paste codes.
        assert_eq!(rep.share_paths.len(), 5);
        assert_eq!(rep.share_b64.len(), 5);
        assert!(rep.payload_path.ends_with(".payload.svss"));

        // Recover from 3 of the 5 piece files (no pasted codes).
        let out = dir.path().join("recovered.txt");
        let three = rep.share_paths[0..3].to_vec();
        let rr = app
            .shares_recover_secret(three, vec![], rep.payload_path.clone(), s(&out))
            .unwrap();
        assert_eq!(rr.bytes_written, 17);
        assert_eq!(std::fs::read(&out).unwrap(), b"master passphrase");
    }

    #[test]
    fn shares_recover_tampered_piece_is_oracle_safe_unauthorized() {
        let dir = tmp();
        let app = PlatformApp::new();
        let rep = app
            .shares_split_secret(
                IpcPassphrase::new("integrity matters".into()),
                3,
                2,
                s(dir.path()),
            )
            .unwrap();
        // Corrupt a y-coordinate byte of one piece's key share (structure/x-coordinate intact, so
        // it clears the non-secret pre-checks): reconstruction yields a wrong key and the AEAD open
        // fails → merged, oracle-safe SV-UNAUTHORIZED (never a distinct "bad share" oracle).
        let victim = &rep.share_paths[0];
        let mut bytes = std::fs::read(victim).unwrap();
        bytes[70] ^= 0xff; // within key_share [59..92]; byte 59 (x-coordinate) untouched
        std::fs::write(victim, &bytes).unwrap();

        let out = dir.path().join("tampered.txt");
        let err = app
            .shares_recover_secret(
                rep.share_paths[0..2].to_vec(),
                vec![],
                rep.payload_path.clone(),
                s(&out),
            )
            .unwrap_err();
        assert_eq!(err, ApiError::Unauthorized);
        assert_eq!(err.code(), "SV-UNAUTHORIZED");
        assert!(!out.exists());
    }

    #[test]
    fn shares_recover_from_pasted_base64_codes() {
        let dir = tmp();
        let app = PlatformApp::new();
        let rep = app
            .shares_split_secret(
                IpcPassphrase::new("paste me back".into()),
                4,
                2,
                s(dir.path()),
            )
            .unwrap();
        // Recover using only pasted Base64 codes (no file paths) → exercises the temp-file bridge.
        let out = dir.path().join("from-codes.txt");
        let codes = rep.share_b64[1..3].to_vec();
        app.shares_recover_secret(vec![], codes, rep.payload_path.clone(), s(&out))
            .unwrap();
        assert_eq!(std::fs::read(&out).unwrap(), b"paste me back");
    }

    #[test]
    fn shares_split_file_omits_codes_and_roundtrips() {
        let dir = tmp();
        let app = PlatformApp::new();
        let input = dir.path().join("wallet.dat");
        let bytes: Vec<u8> = (0..3000u32).map(|i| (i % 251) as u8).collect();
        std::fs::write(&input, &bytes).unwrap();

        let rep = app
            .shares_split_file(s(&input), 3, 3, s(dir.path()))
            .unwrap();
        // File workflow must NOT surface per-piece secret strings.
        assert!(rep.share_b64.is_empty());
        assert_eq!(rep.share_paths.len(), 3);

        // Recover into a clean dir: the file is now saved under its recovered original name
        // (`wallet.dat`), which would otherwise collide with the still-present input.
        let outdir = dir.path().join("rec");
        std::fs::create_dir(&outdir).unwrap();
        let out = outdir.join("wallet.out");
        let rep2 = app
            .shares_recover_secret(
                rep.share_paths.clone(),
                vec![],
                rep.payload_path.clone(),
                s(&out),
            )
            .unwrap();
        assert_eq!(rep2.original_name.as_deref(), Some("wallet.dat"));
        assert!(rep2.output_path.ends_with("wallet.dat"));
        assert!(!out.exists(), "the literal (.out) output path is not used");
        assert_eq!(std::fs::read(&rep2.output_path).unwrap(), bytes);
    }

    #[test]
    fn shares_recover_too_few_is_insufficient_shares() {
        let dir = tmp();
        let app = PlatformApp::new();
        let rep = app
            .shares_split_secret(IpcPassphrase::new("need three".into()), 5, 3, s(dir.path()))
            .unwrap();
        let out = dir.path().join("nope.txt");
        let err = app
            .shares_recover_secret(
                rep.share_paths[0..2].to_vec(),
                vec![],
                rep.payload_path.clone(),
                s(&out),
            )
            .unwrap_err();
        assert_eq!(err, ApiError::InsufficientShares { got: 2, need: 3 });
        assert_eq!(err.code(), "SV-INSUFFICIENT-SHARES");
        assert!(!out.exists());
    }

    #[test]
    fn shares_recover_wrong_pieces_is_oracle_safe_unauthorized() {
        let dir = tmp();
        let app = PlatformApp::new();
        // Two independent splits; mix a piece from B into A's payload at sufficient count.
        let a = app
            .shares_split_secret(IpcPassphrase::new("secret A".into()), 3, 2, s(dir.path()))
            .unwrap();
        // A different cohort lands in a sub-folder to avoid filename collisions.
        let sub = dir.path().join("b");
        std::fs::create_dir(&sub).unwrap();
        let b = app
            .shares_split_secret(IpcPassphrase::new("secret B".into()), 3, 2, s(&sub))
            .unwrap();
        let out = dir.path().join("mixed.txt");
        // One A piece + one B piece, against A's payload → cohort mismatch (non-secret) before crypto.
        let err = app
            .shares_recover_secret(
                vec![a.share_paths[0].clone(), b.share_paths[0].clone()],
                vec![],
                a.payload_path.clone(),
                s(&out),
            )
            .unwrap_err();
        // "pieces from different splits" is a non-secret SV-INVALID-INPUT (matches the engine).
        assert_eq!(err.code(), "SV-INVALID-INPUT");
        assert!(!out.exists());
    }

    #[test]
    fn shares_split_export_qr_then_recover_from_qr() {
        let dir = tmp();
        let app = PlatformApp::new();
        // Split a secret → existing piece strings.
        let rep = app
            .shares_split_secret(
                IpcPassphrase::new("transfer me by QR".into()),
                4,
                2,
                s(dir.path()),
            )
            .unwrap();

        // Export the existing piece strings as QR PNGs (no re-split).
        let qr_dir = dir.path().join("qr");
        std::fs::create_dir(&qr_dir).unwrap();
        let qr = app
            .shares_export_qr(rep.share_b64.clone(), s(&qr_dir))
            .unwrap();
        assert_eq!(qr.image_paths.len(), 4);
        assert!(qr
            .image_paths
            .iter()
            .all(|p| std::path::Path::new(p).exists()));

        // Recover from 2 of the 4 QR images + the payload file → original secret.
        let out = dir.path().join("from-qr.txt");
        let two = qr.image_paths[0..2].to_vec();
        let rr = app
            .shares_recover_from_qr(two, rep.payload_path.clone(), s(&out))
            .unwrap();
        assert_eq!(rr.bytes_written, 17);
        assert_eq!(std::fs::read(&out).unwrap(), b"transfer me by QR");
    }

    #[test]
    fn shares_recover_from_qr_too_few_is_insufficient_shares() {
        let dir = tmp();
        let app = PlatformApp::new();
        let rep = app
            .shares_split_secret(IpcPassphrase::new("need two".into()), 3, 2, s(dir.path()))
            .unwrap();
        let qr_dir = dir.path().join("qr");
        std::fs::create_dir(&qr_dir).unwrap();
        let qr = app
            .shares_export_qr(rep.share_b64.clone(), s(&qr_dir))
            .unwrap();

        // Only one QR (< threshold) → the EXISTING insufficient-shares semantics, surfaced via QR.
        let out = dir.path().join("nope.txt");
        let err = app
            .shares_recover_from_qr(
                vec![qr.image_paths[0].clone()],
                rep.payload_path.clone(),
                s(&out),
            )
            .unwrap_err();
        assert_eq!(err, ApiError::InsufficientShares { got: 1, need: 2 });
        assert!(!out.exists());
    }

    #[test]
    fn shares_export_qr_rejects_empty_and_recover_rejects_non_qr_image() {
        let dir = tmp();
        let app = PlatformApp::new();
        // Empty export → coded SV-INVALID-INPUT (no silent success).
        let err = app.shares_export_qr(vec![], s(dir.path())).unwrap_err();
        assert_eq!(err.code(), "SV-INVALID-INPUT");

        // A non-QR image in the recover set → fail-closed SV-MALFORMED (never a wrong recovery).
        let blank = dir.path().join("blank.png");
        image::GrayImage::from_pixel(48, 48, image::Luma([255u8]))
            .save(&blank)
            .unwrap();
        let out = dir.path().join("x.txt");
        let err = app
            .shares_recover_from_qr(
                vec![s(&blank)],
                s(&dir.path().join("p.payload.svss")),
                s(&out),
            )
            .unwrap_err();
        assert_eq!(err, ApiError::Malformed);
        assert!(!out.exists());
    }
}
