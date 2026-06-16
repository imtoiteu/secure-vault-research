//! Integrity module services: Hash File (streaming BLAKE3) and Verify Signature (minisign).

use std::fs::File;
use std::io::Read;
use std::path::Path;

use sv_crypto_traits::{Hasher, MinisignSignature, Signer};

use crate::MAX_PLAINTEXT_BYTES;
use crate::{
    map_io, parse_pubkey_hex, read_capped, IntegrityVerification, PlatformCrypto, PlatformError,
    SignatureCheck,
};

const HASH_CHUNK: usize = 64 * 1024;

impl PlatformCrypto {
    /// **Hash File.** Stream the file through BLAKE3 in fixed chunks and return lowercase hex.
    /// Streaming means arbitrarily large files hash without buffering (no size cap needed).
    pub fn hash_file(&self, path: &Path) -> Result<String, PlatformError> {
        let mut file = File::open(path).map_err(map_io)?;
        let mut hasher = self.hasher.streaming();
        let mut buf = [0u8; HASH_CHUNK];
        loop {
            let n = file
                .read(&mut buf)
                .map_err(|e| PlatformError::Io(e.to_string()))?;
            if n == 0 {
                break;
            }
            hasher.update(&buf[..n]);
        }
        Ok(hasher.finalize().to_hex())
    }

    /// **Verify Signature.** Verify a detached minisign signature of `file` against the hex
    /// Ed25519 public key in `public_key_path`. A failed verification is `Ok(valid: false)`, not
    /// an error — only malformed inputs / I/O are errors.
    pub fn verify_signature(
        &self,
        file: &Path,
        signature_path: &Path,
        public_key_path: &Path,
    ) -> Result<SignatureCheck, PlatformError> {
        let data = read_capped(file, MAX_PLAINTEXT_BYTES)?;
        let sig_bytes = read_capped(signature_path, MAX_PLAINTEXT_BYTES)?;
        let pk_text = std::fs::read_to_string(public_key_path).map_err(map_io)?;
        let public_key = parse_pubkey_hex(&pk_text)?;
        let signature = MinisignSignature(sig_bytes);
        let valid = self.signer.verify(&data, &signature, &public_key).is_ok();
        Ok(SignatureCheck {
            valid,
            file_blake3_hex: self.hasher.hash(&data).to_hex(),
        })
    }

    /// **Verify Integrity.** Check an arbitrary file against an expected BLAKE3 hash **and/or** a
    /// detached minisign signature + public key — composing [`Self::hash_file`] and
    /// [`Self::verify_signature`] (no new crypto). At least one of the two checks must be requested.
    ///
    /// Semantics (mirroring [`Self::verify_signature`]): a hash **mismatch** or an **invalid**
    /// signature is a `false` verdict returned as `Ok`, never an error. Errors are reserved for
    /// structural problems — missing file ([`PlatformError::NotFound`]), oversized signed input
    /// ([`PlatformError::TooLarge`]), or malformed inputs ([`PlatformError::InvalidInput`]: a
    /// non-hex / wrong-length expected hash or public key, an incomplete signature request, or
    /// neither check requested). The computed hash is always returned, even on a `false` verdict.
    ///
    /// Provenance vs. integrity: verifying against a caller-supplied external public key authenticates
    /// the file *against that key*; this performs no key management and trusts no key shipped with the
    /// artifact (key custody is the Sign File / Encrypt File concern).
    pub fn verify_integrity(
        &self,
        file: &Path,
        expected_hash_hex: Option<&str>,
        signature_path: Option<&Path>,
        public_key_path: Option<&Path>,
    ) -> Result<IntegrityVerification, PlatformError> {
        let hash_checked = expected_hash_hex.is_some();
        // A signature check needs the signature AND the public key together (partial → malformed).
        let signature_checked = match (signature_path, public_key_path) {
            (Some(_), Some(_)) => true,
            (None, None) => false,
            _ => {
                return Err(PlatformError::InvalidInput(
                    "signature verification needs both a signature file and a public key".into(),
                ))
            }
        };
        if !hash_checked && !signature_checked {
            return Err(PlatformError::InvalidInput(
                "verify integrity needs an expected hash and/or a signature + public key".into(),
            ));
        }

        // Compute the file's BLAKE3 (and the signature verdict, if requested). When a signature is
        // checked, reuse the hash it already computes over the same buffered bytes — one read, no skew.
        let (computed_hash_hex, signature_valid) = match (signature_path, public_key_path) {
            (Some(sig), Some(pk)) => {
                let check = self.verify_signature(file, sig, pk)?;
                (check.file_blake3_hex, check.valid)
            }
            _ => (self.hash_file(file)?, false),
        };

        // Compare against the expected hash (case-insensitive; both are canonical BLAKE3 hex).
        let hash_matched = match expected_hash_hex {
            Some(expected) => {
                parse_expected_blake3(expected)?.eq_ignore_ascii_case(&computed_hash_hex)
            }
            None => false,
        };

        let verified = (!hash_checked || hash_matched) && (!signature_checked || signature_valid);
        Ok(IntegrityVerification {
            hash_checked,
            hash_matched,
            signature_checked,
            signature_valid,
            computed_hash_hex,
            verified,
        })
    }
}

/// Validate a caller-supplied expected BLAKE3 hash and normalize it to canonical lowercase hex.
/// Anything that is not exactly 32 hex-encoded bytes → [`PlatformError::InvalidInput`] (mirrors
/// [`parse_pubkey_hex`]); a typo'd fingerprint is surfaced as an error, not silently treated as a
/// non-match.
fn parse_expected_blake3(text: &str) -> Result<String, PlatformError> {
    let bytes = hex::decode(text.trim())
        .map_err(|_| PlatformError::InvalidInput("expected hash must be hex".into()))?;
    let arr: [u8; 32] = bytes.as_slice().try_into().map_err(|_| {
        PlatformError::InvalidInput("expected hash must be 32 bytes (BLAKE3)".into())
    })?;
    Ok(hex::encode(arr))
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;
    use sv_crypto::Blake3Hasher;

    fn tmp() -> tempfile::TempDir {
        tempfile::tempdir().unwrap()
    }

    #[test]
    fn hash_file_matches_blake3_and_streams() {
        let dir = tmp();
        let f = dir.path().join("f");
        let data = vec![7u8; 200 * 1024]; // multi-chunk
        std::fs::write(&f, &data).unwrap();

        let pc = PlatformCrypto::new();
        let got = pc.hash_file(&f).unwrap();
        assert_eq!(got, Blake3Hasher.hash(&data).to_hex());
        assert_eq!(got.len(), 64);
    }

    #[test]
    fn hash_file_missing_is_not_found() {
        let dir = tmp();
        let pc = PlatformCrypto::new();
        assert!(matches!(
            pc.hash_file(&dir.path().join("nope")),
            Err(PlatformError::NotFound)
        ));
    }

    #[test]
    fn verify_signature_roundtrip_and_tamper() {
        let dir = tmp();
        let pc = PlatformCrypto::new();

        // Mint a keypair + sign a file via the crypto services (closed loop, no vault).
        let kp = pc.generate_signing_keypair(dir.path(), "k", b"pw").unwrap();
        let doc = dir.path().join("doc.txt");
        std::fs::write(&doc, b"verify me").unwrap();
        let sig = pc
            .sign_file(&doc, Path::new(&kp.secret_key_path), b"pw")
            .unwrap();

        let report = pc
            .verify_signature(&doc, Path::new(&sig), Path::new(&kp.public_key_path))
            .unwrap();
        assert!(report.valid);
        assert_eq!(
            report.file_blake3_hex,
            Blake3Hasher.hash(b"verify me").to_hex()
        );

        // Tamper the file → invalid (still Ok, not an error).
        std::fs::write(&doc, b"verify ME").unwrap();
        let bad = pc
            .verify_signature(&doc, Path::new(&sig), Path::new(&kp.public_key_path))
            .unwrap();
        assert!(!bad.valid);
    }

    #[test]
    fn verify_signature_rejects_bad_public_key() {
        let dir = tmp();
        let pc = PlatformCrypto::new();
        let doc = dir.path().join("d");
        std::fs::write(&doc, b"x").unwrap();
        let sig = dir.path().join("d.sig");
        std::fs::write(&sig, b"whatever").unwrap();
        let pk = dir.path().join("k.pub");
        std::fs::write(&pk, b"not-hex").unwrap();
        assert!(matches!(
            pc.verify_signature(&doc, &sig, &pk),
            Err(PlatformError::InvalidInput(_))
        ));
    }

    /// Closed-loop fixture: a file plus a valid detached signature + public key over it.
    fn signed_fixture(dir: &Path, pc: &PlatformCrypto, body: &[u8]) -> (PathBuf, PathBuf, PathBuf) {
        let kp = pc.generate_signing_keypair(dir, "k", b"pw").unwrap();
        let doc = dir.join("doc.bin");
        std::fs::write(&doc, body).unwrap();
        let sig = pc
            .sign_file(&doc, Path::new(&kp.secret_key_path), b"pw")
            .unwrap();
        (doc, PathBuf::from(sig), PathBuf::from(kp.public_key_path))
    }

    #[test]
    fn verify_integrity_hash_only_match_and_mismatch() {
        let dir = tmp();
        let pc = PlatformCrypto::new();
        let f = dir.path().join("f");
        std::fs::write(&f, b"the cake is a lie").unwrap();
        let good = pc.hash_file(&f).unwrap();

        // Correct expected hash, no signature → matched & verified; signature half untouched.
        let r = pc.verify_integrity(&f, Some(&good), None, None).unwrap();
        assert!(r.hash_checked && r.hash_matched && r.verified);
        assert!(!r.signature_checked && !r.signature_valid);
        assert_eq!(r.computed_hash_hex, good);

        // Hex-uppercased expected hash still matches (case-insensitive).
        let r = pc
            .verify_integrity(&f, Some(&good.to_uppercase()), None, None)
            .unwrap();
        assert!(r.hash_matched && r.verified);

        // Wrong expected hash → mismatch, not verified — but Ok (a verdict, not an error).
        let wrong = "00".repeat(32);
        let r = pc.verify_integrity(&f, Some(&wrong), None, None).unwrap();
        assert!(r.hash_checked && !r.hash_matched && !r.verified);
    }

    #[test]
    fn verify_integrity_signature_and_hash_together() {
        let dir = tmp();
        let pc = PlatformCrypto::new();
        let (doc, sig, pk) = signed_fixture(dir.path(), &pc, b"deploy at dawn");
        let good = pc.hash_file(&doc).unwrap();

        // Both checks requested and both pass → verified; one file read (sig path reuses its hash).
        let r = pc
            .verify_integrity(&doc, Some(&good), Some(&sig), Some(&pk))
            .unwrap();
        assert!(r.hash_checked && r.hash_matched);
        assert!(r.signature_checked && r.signature_valid);
        assert!(r.verified);
        assert_eq!(r.computed_hash_hex, good);

        // Tamper the file: the recomputed hash no longer matches AND the signature is now invalid —
        // both false, verified false, still Ok.
        std::fs::write(&doc, b"deploy at DAWN").unwrap();
        let r = pc
            .verify_integrity(&doc, Some(&good), Some(&sig), Some(&pk))
            .unwrap();
        assert!(!r.hash_matched && !r.signature_valid && !r.verified);
        // The computed hash is still reported (it is the *tampered* file's hash).
        assert_eq!(r.computed_hash_hex, pc.hash_file(&doc).unwrap());
    }

    #[test]
    fn verify_integrity_signature_only_no_expected_hash() {
        let dir = tmp();
        let pc = PlatformCrypto::new();
        let (doc, sig, pk) = signed_fixture(dir.path(), &pc, b"signed but no hash given");

        let r = pc
            .verify_integrity(&doc, None, Some(&sig), Some(&pk))
            .unwrap();
        assert!(r.signature_checked && r.signature_valid && r.verified);
        assert!(!r.hash_checked && !r.hash_matched);
        assert_eq!(r.computed_hash_hex, pc.hash_file(&doc).unwrap());
    }

    #[test]
    fn verify_integrity_requires_at_least_one_check() {
        let dir = tmp();
        let pc = PlatformCrypto::new();
        let f = dir.path().join("f");
        std::fs::write(&f, b"x").unwrap();
        assert!(matches!(
            pc.verify_integrity(&f, None, None, None),
            Err(PlatformError::InvalidInput(_))
        ));
    }

    #[test]
    fn verify_integrity_partial_signature_request_is_invalid_input() {
        let dir = tmp();
        let pc = PlatformCrypto::new();
        let f = dir.path().join("f");
        std::fs::write(&f, b"x").unwrap();
        let sig = dir.path().join("f.sig");
        std::fs::write(&sig, b"sig").unwrap();
        // Signature without a public key (and the mirror case) → malformed request, before any I/O.
        assert!(matches!(
            pc.verify_integrity(&f, None, Some(&sig), None),
            Err(PlatformError::InvalidInput(_))
        ));
        assert!(matches!(
            pc.verify_integrity(&f, Some(&"ab".repeat(32)), None, Some(&sig)),
            Err(PlatformError::InvalidInput(_))
        ));
    }

    #[test]
    fn verify_integrity_bad_expected_hash_is_invalid_input() {
        let dir = tmp();
        let pc = PlatformCrypto::new();
        let f = dir.path().join("f");
        std::fs::write(&f, b"x").unwrap();
        // Non-hex, and right-charset-but-wrong-length both reject as InvalidInput (not a silent miss).
        assert!(matches!(
            pc.verify_integrity(&f, Some("not a hash"), None, None),
            Err(PlatformError::InvalidInput(_))
        ));
        assert!(matches!(
            pc.verify_integrity(&f, Some("abcd"), None, None),
            Err(PlatformError::InvalidInput(_))
        ));
    }

    #[test]
    fn verify_integrity_missing_file_is_not_found() {
        let dir = tmp();
        let pc = PlatformCrypto::new();
        let missing = dir.path().join("nope");
        assert!(matches!(
            pc.verify_integrity(&missing, Some(&"ab".repeat(32)), None, None),
            Err(PlatformError::NotFound)
        ));
    }
}
