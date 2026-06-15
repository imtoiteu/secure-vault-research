//! Authenticated wrapping of stored secrets (age identity, signing key) under the
//! KEK/SWK, via libsodium `crypto_secretbox` (XSalsa20-Poly1305).
//!
//! M2 wraps with a random nonce and no associated data. **AAD binding** of each wrapped
//! blob to its `vault_uuid`/field-label/version is an M5 schema decision (H2) and will be
//! added when the container format is built; at that point this may move to an AEAD that
//! supports associated data.

use sv_crypto_traits::CryptoError;
use sv_sys_sodium::{SECRETBOX_KEYBYTES, SECRETBOX_NONCEBYTES};

/// A secretbox-wrapped secret: random nonce + ciphertext (includes the 16-byte MAC).
/// Non-secret as a whole (it is ciphertext), so it can live in the vault header.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Wrapped {
    pub nonce: [u8; SECRETBOX_NONCEBYTES],
    pub ciphertext: Vec<u8>,
}

/// Wrap `plaintext` under `key` (a KEK/SWK) with a fresh random nonce.
#[must_use]
pub fn seal(key: &[u8; SECRETBOX_KEYBYTES], plaintext: &[u8]) -> Wrapped {
    let mut nonce = [0u8; SECRETBOX_NONCEBYTES];
    sv_sys_sodium::random_bytes(&mut nonce);
    let ciphertext = sv_sys_sodium::secretbox_seal(plaintext, &nonce, key);
    Wrapped { nonce, ciphertext }
}

/// Unwrap a [`Wrapped`] secret. Returns [`CryptoError::VerificationFailed`] if the key is
/// wrong or the ciphertext was tampered with.
pub fn open(key: &[u8; SECRETBOX_KEYBYTES], wrapped: &Wrapped) -> Result<Vec<u8>, CryptoError> {
    sv_sys_sodium::secretbox_open(&wrapped.ciphertext, &wrapped.nonce, key)
        .ok_or(CryptoError::VerificationFailed)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn wrap_unwrap_roundtrip() {
        let key = [5u8; SECRETBOX_KEYBYTES];
        let secret = b"AGE-SECRET-KEY-1...";
        let w = seal(&key, secret);
        assert_eq!(open(&key, &w).unwrap(), secret);
    }

    #[test]
    fn wrong_key_and_tamper_are_rejected() {
        let key = [5u8; SECRETBOX_KEYBYTES];
        let w = seal(&key, b"identity");
        assert!(matches!(
            open(&[6u8; SECRETBOX_KEYBYTES], &w),
            Err(CryptoError::VerificationFailed)
        ));

        let mut tampered = w.clone();
        tampered.ciphertext[0] ^= 0xff;
        assert!(matches!(
            open(&key, &tampered),
            Err(CryptoError::VerificationFailed)
        ));
    }

    #[test]
    fn fresh_nonce_per_seal() {
        let key = [1u8; SECRETBOX_KEYBYTES];
        let a = seal(&key, b"x");
        let b = seal(&key, b"x");
        assert_ne!(a.nonce, b.nonce);
        assert_ne!(a.ciphertext, b.ciphertext);
    }
}
