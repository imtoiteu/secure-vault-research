//! Integrity module services: Hash File (streaming BLAKE3) and Verify Signature (minisign).

use std::fs::File;
use std::io::Read;
use std::path::Path;

use sv_crypto_traits::{Hasher, MinisignSignature, Signer};

use crate::MAX_PLAINTEXT_BYTES;
use crate::{map_io, parse_pubkey_hex, read_capped, PlatformCrypto, PlatformError, SignatureCheck};

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
}

#[cfg(test)]
mod tests {
    use super::*;
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
}
