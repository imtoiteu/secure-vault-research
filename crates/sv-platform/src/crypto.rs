//! Cryptography module services: Encrypt File / Decrypt File (passphrase) and Sign File
//! (generate keypair + sign), all reusing the shared [`crate::artifact`] passphrase-seal.

use std::path::Path;

use sv_crypto_traits::{SecretBytes, Signer};
use zeroize::Zeroize;

use crate::artifact::{self, HEADER_OVERHEAD};
use crate::{
    append_extension, now_unix, path_str, read_capped, refuse_existing, write_atomic,
    PlatformCrypto, PlatformError, PlatformKeypair, MAX_PLAINTEXT_BYTES, SVENC_MAGIC, SVKEY_MAGIC,
};

/// Decrypt input cap: ciphertext ≈ plaintext plus the small fixed header/tag overhead.
const MAX_CIPHERTEXT_BYTES: u64 = MAX_PLAINTEXT_BYTES + HEADER_OVERHEAD;

impl PlatformCrypto {
    /// **Encrypt File.** Seal `input` under `passphrase` (Argon2id → secretbox) into a `.svenc`
    /// artifact at `output`. Refuses to overwrite an existing output. Returns the output path.
    pub fn encrypt_file(
        &self,
        input: &Path,
        output: &Path,
        passphrase: &[u8],
    ) -> Result<String, PlatformError> {
        refuse_existing(output)?;
        let mut plaintext = read_capped(input, MAX_PLAINTEXT_BYTES)?;
        let blob = artifact::seal_with_passphrase(&SVENC_MAGIC, passphrase, &plaintext);
        plaintext.zeroize();
        let blob = blob?;
        write_atomic(output, &blob)?;
        Ok(path_str(output))
    }

    /// **Decrypt File.** Open a `.svenc` artifact under `passphrase` and write the recovered
    /// plaintext to `output`. A wrong passphrase or tampered artifact fails as `AuthFailed`
    /// (oracle-safe). Refuses to overwrite an existing output. Returns the output path.
    pub fn decrypt_file(
        &self,
        input: &Path,
        output: &Path,
        passphrase: &[u8],
    ) -> Result<String, PlatformError> {
        refuse_existing(output)?;
        let blob = read_capped(input, MAX_CIPHERTEXT_BYTES)?;
        let mut plaintext = artifact::open_with_passphrase(&SVENC_MAGIC, passphrase, &blob)?;
        let res = write_atomic(output, &plaintext);
        plaintext.zeroize();
        res?;
        Ok(path_str(output))
    }

    /// **Generate signing keypair.** Mint an Ed25519/minisign keypair; write `<name>.pub` (hex
    /// public key) and `<name>.svkey` (secret key encrypted at rest under `passphrase`, the same
    /// Argon2id+secretbox mechanism as Encrypt File). Refuses to overwrite either file.
    pub fn generate_signing_keypair(
        &self,
        out_dir: &Path,
        name: &str,
        passphrase: &[u8],
    ) -> Result<PlatformKeypair, PlatformError> {
        if name.is_empty() || name.contains('/') || name.contains('\\') {
            return Err(PlatformError::InvalidInput(
                "key name must be non-empty and contain no path separators".into(),
            ));
        }
        let pk_path = out_dir.join(format!("{name}.pub"));
        let sk_path = out_dir.join(format!("{name}.svkey"));
        refuse_existing(&pk_path)?;
        refuse_existing(&sk_path)?;

        let (sk, pk) = self
            .signer
            .generate()
            .map_err(|_| PlatformError::Internal)?;
        let pk_hex = hex::encode(pk.0);

        write_atomic(&pk_path, pk_hex.as_bytes())?;
        let blob = artifact::seal_with_passphrase(&SVKEY_MAGIC, passphrase, sk.expose_secret())?;
        if let Err(e) = write_atomic(&sk_path, &blob) {
            // Don't leave an orphan public key if the secret write fails.
            let _ = std::fs::remove_file(&pk_path);
            return Err(e);
        }

        Ok(PlatformKeypair {
            public_key_path: path_str(&pk_path),
            secret_key_path: path_str(&sk_path),
            public_key_hex: pk_hex,
        })
    }

    /// **Sign File.** Unwrap the `.svkey` signing key with `passphrase` and write a detached
    /// minisign signature next to `input` (`<input>.minisig`). Refuses to overwrite an existing
    /// signature. Returns the signature path. A wrong passphrase fails as `AuthFailed`.
    pub fn sign_file(
        &self,
        input: &Path,
        signing_key_path: &Path,
        passphrase: &[u8],
    ) -> Result<String, PlatformError> {
        let data = read_capped(input, MAX_PLAINTEXT_BYTES)?;
        let blob = read_capped(signing_key_path, MAX_CIPHERTEXT_BYTES)?;
        let sk_bytes = artifact::open_with_passphrase(&SVKEY_MAGIC, passphrase, &blob)?;
        let sk = SecretBytes::new(sk_bytes);

        let comment = format!("secure-vault signed {}", now_unix());
        let sig = self
            .signer
            .sign(&data, &sk, &comment)
            .map_err(|_| PlatformError::Internal)?;

        let sig_path = append_extension(input, "minisig");
        refuse_existing(&sig_path)?;
        write_atomic(&sig_path, &sig.0)?;
        Ok(path_str(&sig_path))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::SignatureCheck;

    fn tmp() -> tempfile::TempDir {
        tempfile::tempdir().unwrap()
    }

    #[test]
    fn encrypt_decrypt_roundtrip() {
        let dir = tmp();
        let pc = PlatformCrypto::new();
        let plain = dir.path().join("p.txt");
        std::fs::write(&plain, b"secret payload \x00\x01 end").unwrap();
        let enc = dir.path().join("p.svenc");
        let dec = dir.path().join("p.out");

        pc.encrypt_file(&plain, &enc, b"hunter2").unwrap();
        assert_eq!(&std::fs::read(&enc).unwrap()[0..6], b"SVENC\0");

        pc.decrypt_file(&enc, &dec, b"hunter2").unwrap();
        assert_eq!(std::fs::read(&dec).unwrap(), b"secret payload \x00\x01 end");
    }

    #[test]
    fn decrypt_wrong_passphrase_is_unauthorized() {
        let dir = tmp();
        let pc = PlatformCrypto::new();
        let plain = dir.path().join("p");
        std::fs::write(&plain, b"data").unwrap();
        let enc = dir.path().join("p.svenc");
        pc.encrypt_file(&plain, &enc, b"right").unwrap();

        let dec = dir.path().join("p.out");
        assert!(matches!(
            pc.decrypt_file(&enc, &dec, b"wrong"),
            Err(PlatformError::AuthFailed)
        ));
        // No partial output left behind.
        assert!(!dec.exists());
    }

    #[test]
    fn encrypt_refuses_to_overwrite_output() {
        let dir = tmp();
        let pc = PlatformCrypto::new();
        let plain = dir.path().join("p");
        std::fs::write(&plain, b"data").unwrap();
        let enc = dir.path().join("p.svenc");
        std::fs::write(&enc, b"PRECIOUS").unwrap();
        assert!(matches!(
            pc.encrypt_file(&plain, &enc, b"pw"),
            Err(PlatformError::OutputExists)
        ));
        assert_eq!(std::fs::read(&enc).unwrap(), b"PRECIOUS");
    }

    #[test]
    fn encrypt_rejects_oversized_input() {
        let dir = tmp();
        let pc = PlatformCrypto::new();
        let big = dir.path().join("big.bin");
        let f = std::fs::File::create(&big).unwrap();
        f.set_len(MAX_PLAINTEXT_BYTES + 1).unwrap();
        drop(f);
        let enc = dir.path().join("big.svenc");
        match pc.encrypt_file(&big, &enc, b"pw") {
            Err(PlatformError::TooLarge {
                limit_bytes,
                actual_bytes,
            }) => {
                assert_eq!(limit_bytes, MAX_PLAINTEXT_BYTES);
                assert_eq!(actual_bytes, MAX_PLAINTEXT_BYTES + 1);
            }
            other => panic!("expected TooLarge, got {other:?}"),
        }
        assert!(!enc.exists());
    }

    #[test]
    fn generate_keypair_writes_files_and_refuses_overwrite() {
        let dir = tmp();
        let pc = PlatformCrypto::new();
        let kp = pc
            .generate_signing_keypair(dir.path(), "id", b"pw")
            .unwrap();
        assert!(Path::new(&kp.public_key_path).exists());
        assert!(Path::new(&kp.secret_key_path).exists());
        assert_eq!(kp.public_key_hex.len(), 64);
        // The public key file is exactly the hex.
        assert_eq!(
            std::fs::read_to_string(&kp.public_key_path).unwrap(),
            kp.public_key_hex
        );
        // The secret key file is the sealed artifact, never the raw key.
        assert_eq!(
            &std::fs::read(&kp.secret_key_path).unwrap()[0..6],
            b"SVKEY\0"
        );
        // A second generation with the same name refuses to clobber.
        assert!(matches!(
            pc.generate_signing_keypair(dir.path(), "id", b"pw"),
            Err(PlatformError::OutputExists)
        ));
    }

    #[test]
    fn sign_then_verify_and_wrong_passphrase_fails() {
        let dir = tmp();
        let pc = PlatformCrypto::new();
        let kp = pc
            .generate_signing_keypair(dir.path(), "id", b"pw")
            .unwrap();
        let doc = dir.path().join("doc.bin");
        std::fs::write(&doc, b"sign this").unwrap();

        // Wrong passphrase to unwrap the signing key → AuthFailed.
        assert!(matches!(
            pc.sign_file(&doc, Path::new(&kp.secret_key_path), b"nope"),
            Err(PlatformError::AuthFailed)
        ));

        // Correct passphrase signs and the signature verifies.
        let sig = pc
            .sign_file(&doc, Path::new(&kp.secret_key_path), b"pw")
            .unwrap();
        let SignatureCheck { valid, .. } = pc
            .verify_signature(&doc, Path::new(&sig), Path::new(&kp.public_key_path))
            .unwrap();
        assert!(valid);

        // Signing again refuses to overwrite the existing .minisig.
        assert!(matches!(
            pc.sign_file(&doc, Path::new(&kp.secret_key_path), b"pw"),
            Err(PlatformError::OutputExists)
        ));
    }

    #[test]
    fn invalid_key_name_is_rejected() {
        let dir = tmp();
        let pc = PlatformCrypto::new();
        for bad in ["", "a/b", "a\\b"] {
            assert!(matches!(
                pc.generate_signing_keypair(dir.path(), bad, b"pw"),
                Err(PlatformError::InvalidInput(_))
            ));
        }
    }
}
