//! Payload encryption seam (the vault's single-stream age blob).
//!
//! The vault payload is one age ciphertext (M5 / H3). The service depends on this trait
//! rather than on `sv-age` directly, so the full vault lifecycle is testable with an in-memory
//! [`StubPayloadCipher`] while production uses [`AgePayloadCipher`] (the bundled, hash-pinned
//! `age` subprocess from M3 plus `age-keygen` for identity generation). Keeping the seam here
//! also confines the `age` toolchain dependency to the composition root.

use std::io::Cursor;
use std::path::PathBuf;
use std::process::Command;

use sv_core::VaultError;
use sv_crypto_traits::{AgeIdentity, AgeRecipient, CryptoError, FileCipher, SecretBytes};

/// Encrypts/decrypts the vault payload and generates the vault's age keypair.
pub trait PayloadCipher {
    /// Generate a fresh `(identity, recipient)` for a new vault.
    fn generate_identity(&self) -> Result<(AgeIdentity, AgeRecipient), VaultError>;
    /// Encrypt the payload plaintext to `recipient`.
    fn encrypt(&self, plaintext: &[u8], recipient: &AgeRecipient) -> Result<Vec<u8>, VaultError>;
    /// Decrypt the payload using `identity`.
    fn decrypt(&self, ciphertext: &[u8], identity: &AgeIdentity) -> Result<Vec<u8>, VaultError>;
}

/// Production payload cipher: the M3 `AgeCipher` for encrypt/decrypt + `age-keygen` for
/// identity generation (both bundled binaries; the cipher is BLAKE3-hash-pinned).
#[derive(Debug, Clone)]
pub struct AgePayloadCipher {
    cipher: sv_age::AgeCipher,
    keygen_bin: PathBuf,
}

impl AgePayloadCipher {
    /// `cipher` drives the pinned `age` binary; `keygen_bin` is the `age-keygen` path.
    #[must_use]
    pub fn new(cipher: sv_age::AgeCipher, keygen_bin: PathBuf) -> Self {
        Self { cipher, keygen_bin }
    }
}

impl PayloadCipher for AgePayloadCipher {
    fn generate_identity(&self) -> Result<(AgeIdentity, AgeRecipient), VaultError> {
        let mut command = Command::new(&self.keygen_bin);
        command.env_clear();
        // See `sv_age::AgeCipher::run`: Windows needs SystemRoot/SystemDrive (DLL loader) and
        // TEMP/TMP for the subprocess to start under a cleared environment (H4). No-op on Unix.
        #[cfg(windows)]
        for key in ["SystemRoot", "SystemDrive", "TEMP", "TMP"] {
            if let Ok(val) = std::env::var(key) {
                command.env(key, val);
            }
        }
        let out = command
            .output()
            .map_err(|e| VaultError::Io(e.to_string()))?;
        if !out.status.success() {
            return Err(VaultError::Internal);
        }
        // age-keygen prints `# public key: age1…` plus the `AGE-SECRET-KEY-1…` line; the full
        // stdout is a valid age identity file. The recipient is the `age1…` token.
        let recipient = String::from_utf8_lossy(&out.stdout)
            .lines()
            .find_map(|l| {
                l.split_whitespace()
                    .find(|w| w.starts_with("age1"))
                    .map(str::to_string)
            })
            .ok_or(VaultError::Internal)?;
        let identity = AgeIdentity::new(SecretBytes::new(out.stdout));
        Ok((identity, AgeRecipient(recipient)))
    }

    fn encrypt(&self, plaintext: &[u8], recipient: &AgeRecipient) -> Result<Vec<u8>, VaultError> {
        let mut ct = Vec::new();
        self.cipher
            .encrypt(&mut Cursor::new(plaintext), &mut ct, recipient)
            .map_err(crypto_to_vault)?;
        Ok(ct)
    }

    fn decrypt(&self, ciphertext: &[u8], identity: &AgeIdentity) -> Result<Vec<u8>, VaultError> {
        let mut pt = Vec::new();
        self.cipher
            .decrypt(&mut Cursor::new(ciphertext), &mut pt, identity)
            .map_err(crypto_to_vault)?;
        Ok(pt)
    }
}

/// Mobile payload cipher: the pure-Rust age adapter, in-process.
///
/// iOS forbids spawning executables and Android blocks exec of app-writable binaries, so the
/// desktop [`AgePayloadCipher`] (bundled, hash-pinned `age` + `age-keygen` subprocesses) cannot
/// run there. The wire format is identical age v1, so vaults interoperate across platforms —
/// proven bidirectionally against the real Go binary in `sv-age-rs`'s `interop` test.
///
/// Both ciphers share [`crypto_to_vault`], so a failed payload decryption is `Corrupted` here
/// too — never an authentication oracle.
#[derive(Debug, Clone, Copy, Default)]
pub struct RustAgePayloadCipher;

impl RustAgePayloadCipher {
    #[must_use]
    pub fn new() -> Self {
        Self
    }
}

impl PayloadCipher for RustAgePayloadCipher {
    fn generate_identity(&self) -> Result<(AgeIdentity, AgeRecipient), VaultError> {
        let (identity, recipient) =
            sv_age_rs::generate_identity().map_err(|_| VaultError::Internal)?;
        Ok((
            AgeIdentity::new(SecretBytes::new(identity)),
            AgeRecipient(recipient),
        ))
    }

    fn encrypt(&self, plaintext: &[u8], recipient: &AgeRecipient) -> Result<Vec<u8>, VaultError> {
        let mut ct = Vec::new();
        sv_age_rs::RustAgeCipher::new()
            .encrypt(&mut Cursor::new(plaintext), &mut ct, recipient)
            .map_err(crypto_to_vault)?;
        Ok(ct)
    }

    fn decrypt(&self, ciphertext: &[u8], identity: &AgeIdentity) -> Result<Vec<u8>, VaultError> {
        let mut pt = Vec::new();
        sv_age_rs::RustAgeCipher::new()
            .decrypt(&mut Cursor::new(ciphertext), &mut pt, identity)
            .map_err(crypto_to_vault)?;
        Ok(pt)
    }
}

/// Map a payload-cipher `CryptoError` to the vault taxonomy. A decryption that fails here is a
/// damaged/tampered payload (the signature already passed and the identity already unwrapped),
/// so it is `Corrupted`, never an auth oracle.
fn crypto_to_vault(e: CryptoError) -> VaultError {
    match e {
        CryptoError::VerificationFailed => VaultError::Corrupted,
        // A wall-clock timeout (e.g. an oversized payload) is actionable, not an internal bug
        // (validation H1/H6) — surface it distinctly so the UI can say "timed out".
        CryptoError::Timeout => VaultError::Timeout,
        _ => VaultError::Internal,
    }
}

/// Test-only payload cipher: deterministic, in-memory, no `age` binary. Encryption is a
/// reversible XOR keyed by the recipient string so wrong-identity decryption is observable;
/// this exercises the service's pack/encrypt/store/decode/decrypt/unpack pipeline end-to-end.
#[cfg(test)]
#[derive(Debug, Clone, Default)]
pub struct StubPayloadCipher;

#[cfg(test)]
impl StubPayloadCipher {
    /// The recipient deterministically derived from an identity blob (so encrypt-to-recipient
    /// and decrypt-with-identity agree). Mirrors how a real recipient corresponds to an identity.
    fn recipient_for(identity: &[u8]) -> String {
        let n = identity.len().min(16);
        format!("age1stub{}", hex::encode(&identity[..n]))
    }
    /// Deterministic, recipient-keyed keystream byte (reversible XOR; not real crypto).
    fn keystream_byte(recipient: &str, i: usize) -> u8 {
        let bytes = recipient.as_bytes();
        bytes[i % bytes.len()] ^ (i as u8)
    }
}

#[cfg(test)]
impl PayloadCipher for StubPayloadCipher {
    fn generate_identity(&self) -> Result<(AgeIdentity, AgeRecipient), VaultError> {
        // A unique identity per call (BLAKE3 of a fresh random seed), recipient derived from it.
        let mut seed = [0u8; 32];
        getrandom::getrandom(&mut seed).map_err(|_| VaultError::Internal)?;
        let identity = format!("AGE-SECRET-KEY-1STUB{}", hex::encode(seed)).into_bytes();
        let recipient = Self::recipient_for(&identity);
        Ok((
            AgeIdentity::new(SecretBytes::new(identity)),
            AgeRecipient(recipient),
        ))
    }

    fn encrypt(&self, plaintext: &[u8], recipient: &AgeRecipient) -> Result<Vec<u8>, VaultError> {
        Ok(plaintext
            .iter()
            .enumerate()
            .map(|(i, b)| b ^ Self::keystream_byte(&recipient.0, i))
            .collect())
    }

    fn decrypt(&self, ciphertext: &[u8], identity: &AgeIdentity) -> Result<Vec<u8>, VaultError> {
        // Reconstruct the recipient from the identity, then reverse the XOR. A wrong identity
        // yields the wrong keystream → garbage, but here it is only ever called with the
        // correct unwrapped identity, mirroring the real flow.
        let recipient = Self::recipient_for(identity.expose_secret());
        Ok(ciphertext
            .iter()
            .enumerate()
            .map(|(i, b)| b ^ Self::keystream_byte(&recipient, i))
            .collect())
    }
}

#[cfg(test)]
mod rust_cipher_tests {
    use super::*;

    #[test]
    fn round_trips_a_payload() {
        let cipher = RustAgePayloadCipher::new();
        let (identity, recipient) = cipher.generate_identity().unwrap();
        let plaintext = b"vault payload".to_vec();

        let ct = cipher.encrypt(&plaintext, &recipient).unwrap();
        assert_ne!(ct, plaintext, "ciphertext must not equal plaintext");

        let out = cipher.decrypt(&ct, &identity).unwrap();
        assert_eq!(out, plaintext);
    }

    #[test]
    fn generated_recipient_is_an_age_public_key() {
        let (_identity, recipient) = RustAgePayloadCipher::new().generate_identity().unwrap();
        assert!(recipient.0.starts_with("age1"), "got {}", recipient.0);
    }

    /// A foreign identity must surface as `Corrupted`, not `AuthFailed`. The payload is only
    /// reached after the binding signature and the identity unwrap have already succeeded, so
    /// a failure here is damage/tampering — reporting it as an auth failure would build the
    /// very oracle the error taxonomy exists to prevent.
    #[test]
    fn foreign_identity_is_corrupted_not_an_auth_oracle() {
        let cipher = RustAgePayloadCipher::new();
        let (_id_a, recipient_a) = cipher.generate_identity().unwrap();
        let (id_b, _recipient_b) = cipher.generate_identity().unwrap();

        let ct = cipher.encrypt(b"secret", &recipient_a).unwrap();
        let err = cipher.decrypt(&ct, &id_b).unwrap_err();
        assert!(matches!(err, VaultError::Corrupted), "got {err:?}");
    }

    /// The two production ciphers must agree on the error taxonomy, or the same failure would
    /// read differently depending on the platform the user is on.
    #[test]
    fn shares_the_error_mapping_with_the_desktop_cipher() {
        assert!(matches!(
            crypto_to_vault(CryptoError::VerificationFailed),
            VaultError::Corrupted
        ));
        assert!(matches!(
            crypto_to_vault(CryptoError::Timeout),
            VaultError::Timeout
        ));
    }
}
