//! # sv-age-rs — [`FileCipher`] over the pure-Rust `age` crate
//!
//! Mobile cannot spawn subprocesses (iOS forbids it; Android blocks exec of app-writable
//! binaries), so the vault payload cipher runs in-process here. The wire format is age v1,
//! identical to the Go `age` binary `sv-age` drives on desktop — vaults interoperate.
//!
//! Desktop deliberately keeps the hash-pinned subprocess (see `docs/M7-HARDENING.md`); this
//! adapter is the mobile composition root's cipher only.

#![forbid(unsafe_code)]

use std::io::{BufReader, Read, Write};
use std::iter;

use age::secrecy::ExposeSecret;
use sv_crypto_traits::{AgeIdentity, AgeRecipient, CryptoError, FileCipher, FileCipherAlg};
use zeroize::Zeroize;

/// Generate a fresh age keypair, returned as `(identity_file_bytes, recipient_string)`.
///
/// The identity bytes replicate `age-keygen`'s file format — comment lines then the secret key
/// — so the value stored in an [`AgeIdentity`] is byte-compatible with what the desktop
/// (`sv-age`) path produces and consumes.
///
/// # Errors
/// Currently infallible; the `Result` matches the fallible desktop path so the two payload
/// ciphers share one signature.
pub fn generate_identity() -> Result<(Vec<u8>, String), CryptoError> {
    let id = age::x25519::Identity::generate();
    let recipient = id.to_public().to_string();

    // `to_string()` hands back a SecretString; copy it out and zeroize the interim buffers so
    // the secret key does not linger in a stray allocation.
    let secret_string = id.to_string();
    let mut file = format!(
        "# created by SecureVault\n# public key: {recipient}\n{}\n",
        secret_string.expose_secret()
    );
    let bytes = file.as_bytes().to_vec();
    file.zeroize();
    Ok((bytes, recipient))
}

/// In-process age v1 cipher. Stateless.
#[derive(Debug, Clone, Copy, Default)]
pub struct RustAgeCipher;

impl RustAgeCipher {
    #[must_use]
    pub fn new() -> Self {
        Self
    }
}

impl FileCipher for RustAgeCipher {
    fn alg(&self) -> FileCipherAlg {
        FileCipherAlg::AgeV1
    }

    fn encrypt(
        &self,
        plaintext: &mut dyn Read,
        ciphertext: &mut dyn Write,
        recipient: &AgeRecipient,
    ) -> Result<(), CryptoError> {
        let rec: age::x25519::Recipient = recipient
            .0
            .parse()
            .map_err(|e| CryptoError::InvalidParameter(format!("recipient: {e}")))?;

        let encryptor = age::Encryptor::with_recipients(iter::once(&rec as &dyn age::Recipient))
            .map_err(|e| CryptoError::Backend(format!("age encryptor: {e}")))?;

        let mut writer = encryptor
            .wrap_output(ciphertext)
            .map_err(|e| CryptoError::Backend(format!("age wrap: {e}")))?;

        let mut buf = Vec::new();
        plaintext
            .read_to_end(&mut buf)
            .map_err(|e| CryptoError::Backend(format!("read plaintext: {e}")))?;
        let written = writer.write_all(&buf);
        buf.zeroize();
        written.map_err(|e| CryptoError::Backend(format!("age write: {e}")))?;

        writer
            .finish()
            .map_err(|e| CryptoError::Backend(format!("age finish: {e}")))?;
        Ok(())
    }

    fn decrypt(
        &self,
        ciphertext: &mut dyn Read,
        plaintext: &mut dyn Write,
        identity: &AgeIdentity,
    ) -> Result<(), CryptoError> {
        let ids = age::IdentityFile::from_buffer(BufReader::new(identity.expose_secret()))
            .map_err(|e| CryptoError::InvalidParameter(format!("identity file: {e}")))?
            .into_identities()
            .map_err(|e| CryptoError::InvalidParameter(format!("identity parse: {e}")))?;

        let decryptor = age::Decryptor::new(ciphertext)
            .map_err(|e| CryptoError::Backend(format!("age header: {e}")))?;

        // A wrong identity is an authentication failure, matching sv-age's contract exactly so
        // both ciphers surface the same coded error to the UI.
        let mut reader = decryptor
            .decrypt(ids.iter().map(|i| i.as_ref() as &dyn age::Identity))
            .map_err(|e| match e {
                age::DecryptError::NoMatchingKeys | age::DecryptError::DecryptionFailed => {
                    CryptoError::VerificationFailed
                }
                other => CryptoError::Backend(format!("age decrypt: {other}")),
            })?;

        let mut buf = Vec::new();
        reader
            .read_to_end(&mut buf)
            .map_err(|e| CryptoError::Backend(format!("age read: {e}")))?;
        let written = plaintext.write_all(&buf);
        buf.zeroize();
        written.map_err(|e| CryptoError::Backend(format!("write plaintext: {e}")))?;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use sv_crypto_traits::{AgeIdentity, AgeRecipient, CryptoError, FileCipher, SecretBytes};

    #[test]
    fn round_trips_a_payload() {
        let (id_bytes, recipient) = generate_identity().unwrap();
        let cipher = RustAgeCipher::new();

        let plaintext = b"secure vault payload".to_vec();
        let mut ct = Vec::new();
        cipher
            .encrypt(&mut plaintext.as_slice(), &mut ct, &AgeRecipient(recipient))
            .unwrap();
        assert_ne!(ct, plaintext, "ciphertext must not equal plaintext");

        let mut out = Vec::new();
        cipher
            .decrypt(
                &mut ct.as_slice(),
                &mut out,
                &AgeIdentity::new(SecretBytes::new(id_bytes)),
            )
            .unwrap();
        assert_eq!(out, plaintext);
    }

    #[test]
    fn decrypt_with_wrong_identity_fails_verification() {
        let (_id_a, recipient_a) = generate_identity().unwrap();
        let (id_b, _recipient_b) = generate_identity().unwrap();
        let cipher = RustAgeCipher::new();

        let mut ct = Vec::new();
        cipher
            .encrypt(&mut b"secret".as_slice(), &mut ct, &AgeRecipient(recipient_a))
            .unwrap();

        let mut out = Vec::new();
        let err = cipher
            .decrypt(
                &mut ct.as_slice(),
                &mut out,
                &AgeIdentity::new(SecretBytes::new(id_b)),
            )
            .unwrap_err();
        assert!(
            matches!(err, CryptoError::VerificationFailed),
            "wrong identity must be VerificationFailed, got {err:?}"
        );
    }

    #[test]
    fn rejects_a_malformed_recipient() {
        let cipher = RustAgeCipher::new();
        let mut ct = Vec::new();
        let err = cipher
            .encrypt(
                &mut b"x".as_slice(),
                &mut ct,
                &AgeRecipient("not-an-age-recipient".to_string()),
            )
            .unwrap_err();
        assert!(matches!(err, CryptoError::InvalidParameter(_)), "got {err:?}");
    }

    #[test]
    fn generated_identity_is_age_keygen_shaped() {
        let (id_bytes, recipient) = generate_identity().unwrap();
        let text = String::from_utf8(id_bytes).unwrap();
        assert!(text.contains("AGE-SECRET-KEY-1"), "missing secret key line");
        assert!(
            text.contains(&recipient),
            "identity file must carry its public key comment"
        );
        assert!(recipient.starts_with("age1"), "recipient must be bech32 age1…");
    }

    #[test]
    fn reports_the_age_v1_algorithm() {
        assert_eq!(RustAgeCipher::new().alg(), sv_crypto_traits::FileCipherAlg::AgeV1);
    }
}
