//! Confidentiality seam — **encrypt-then-embed** (the security boundary).
//!
//! Concealment (the carrier/embedder) makes **no** secrecy claim; *all* confidentiality and
//! integrity come from this layer, which reuses the **existing vetted `sv-crypto` primitives** —
//! Argon2id KDF + XSalsa20-Poly1305 `secretbox` (the same pair `sv-platform`'s Secret-Sharing
//! engine uses to seal its DEK). **No new cryptographic primitive is introduced here.**
//!
//! The [`PayloadSealer`] trait is the injection seam: `sv-app` (Phase 3) can supply any
//! implementation, and tests inject a fast-parameter sealer. The shipped implementation is
//! [`Argon2idSecretboxSealer`]. Because every extraction failure (wrong passphrase **or** tampered
//! carrier) returns the single [`StegoError::AuthFailed`], the open path is oracle-safe.

use sv_crypto::{policy, secretbox, Argon2Kdf};
use sv_crypto_traits::{Kdf, KdfParams, Salt};

use crate::error::StegoError;

/// `secretbox` (XSalsa20-Poly1305) nonce length, in bytes. Asserted equal to the backend's
/// `SECRETBOX_NONCEBYTES` at compile time by the field assignment in [`Argon2idSecretboxSealer::seal`]
/// (`Sealed.nonce: [u8; NONCE_LEN]` is assigned a `[u8; SECRETBOX_NONCEBYTES]`, so a mismatch fails
/// to compile).
pub const NONCE_LEN: usize = 24;

/// `secretbox` authentication tag (Poly1305) length, in bytes — the ciphertext expansion over the
/// plaintext. Used by [`crate::capacity`] to express capacity in plaintext terms.
pub const TAG_LEN: usize = 16;

/// The output of [`PayloadSealer::seal`]: a fresh random nonce plus the authenticated ciphertext
/// (which already includes the [`TAG_LEN`]-byte tag). **Not secret** — this is ciphertext + public
/// framing — so it derives `Debug` and may be embedded into the carrier and framed in the envelope.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Sealed {
    pub nonce: [u8; NONCE_LEN],
    pub ciphertext: Vec<u8>,
}

/// The encrypt-then-embed boundary. `seal` encrypts a payload under a key derived from
/// `passphrase` + `salt`; `open` reverses it. The `salt` is **public framing** carried in the
/// SVSTEG header (it is also the permutation-seed source); it is not a secret.
///
/// The passphrase is taken as raw `&[u8]`. At the IPC boundary (Phase 3) the caller holds it in a
/// zeroizing `IpcPassphrase` and passes its exposed bytes; this crate stays free of that
/// `sv-app`-level type.
pub trait PayloadSealer {
    /// Encrypt `plaintext`. Returns the nonce + authenticated ciphertext, or
    /// [`StegoError::Internal`] if key derivation fails on otherwise-valid inputs.
    fn seal(&self, passphrase: &[u8], salt: &Salt, plaintext: &[u8]) -> Result<Sealed, StegoError>;

    /// Decrypt `ciphertext` (produced by [`PayloadSealer::seal`] with the same `passphrase`/`salt`).
    /// A wrong passphrase **or** a tampered ciphertext both return the oracle-safe
    /// [`StegoError::AuthFailed`] — they are deliberately indistinguishable.
    fn open(
        &self,
        passphrase: &[u8],
        salt: &Salt,
        nonce: &[u8; NONCE_LEN],
        ciphertext: &[u8],
    ) -> Result<Vec<u8>, StegoError>;
}

/// The shipped sealer: Argon2id (passphrase → 32-byte key) + `secretbox` AEAD. Holds the Argon2id
/// cost parameters so production uses the [`policy::recommended`] floor while tests can inject a
/// fast profile via [`Argon2idSecretboxSealer::with_params`].
#[derive(Debug, Clone, Copy)]
pub struct Argon2idSecretboxSealer {
    params: KdfParams,
}

impl Argon2idSecretboxSealer {
    /// A sealer using the recommended (policy-floor) Argon2id parameters. Production default.
    #[must_use]
    pub fn new() -> Self {
        Self::with_params(policy::recommended())
    }

    /// A sealer with explicit Argon2id parameters (e.g. calibrated, or fast for tests).
    #[must_use]
    pub fn with_params(params: KdfParams) -> Self {
        Self { params }
    }
}

impl Default for Argon2idSecretboxSealer {
    fn default() -> Self {
        Self::new()
    }
}

impl PayloadSealer for Argon2idSecretboxSealer {
    fn seal(&self, passphrase: &[u8], salt: &Salt, plaintext: &[u8]) -> Result<Sealed, StegoError> {
        // Argon2id(passphrase, salt) → zeroizing 32-byte key; secretbox seals with a fresh nonce.
        let key = Argon2Kdf
            .derive(passphrase, salt, &self.params)
            .map_err(|_| StegoError::Internal)?;
        let wrapped = secretbox::seal(key.expose_secret(), plaintext);
        // `wrapped.nonce` is `[u8; SECRETBOX_NONCEBYTES]`; assigning it to `[u8; NONCE_LEN]` is the
        // compile-time assertion that the two constants agree. `key` zeroizes on drop.
        Ok(Sealed {
            nonce: wrapped.nonce,
            ciphertext: wrapped.ciphertext,
        })
    }

    fn open(
        &self,
        passphrase: &[u8],
        salt: &Salt,
        nonce: &[u8; NONCE_LEN],
        ciphertext: &[u8],
    ) -> Result<Vec<u8>, StegoError> {
        let key = Argon2Kdf
            .derive(passphrase, salt, &self.params)
            .map_err(|_| StegoError::Internal)?;
        let wrapped = secretbox::Wrapped {
            nonce: *nonce,
            ciphertext: ciphertext.to_vec(),
        };
        // Wrong key OR tamper → VerificationFailed → the single oracle-safe AuthFailed.
        secretbox::open(key.expose_secret(), &wrapped).map_err(|_| StegoError::AuthFailed)
    }
}

#[cfg(test)]
pub(crate) mod testing {
    use super::*;
    use sv_crypto_traits::Argon2idParams;

    /// Fast Argon2id params — keeps the crypto in the loop while staying fast enough for property
    /// tests. **Tests only**; production uses [`policy::recommended`].
    pub(crate) fn fast_sealer() -> Argon2idSecretboxSealer {
        Argon2idSecretboxSealer::with_params(KdfParams::Argon2id(Argon2idParams {
            mem_kib: 64,
            time_cost: 1,
            parallelism: 1,
        }))
    }
}

#[cfg(test)]
mod tests {
    use super::testing::fast_sealer;
    use super::*;

    #[test]
    fn seal_open_roundtrips() {
        let s = fast_sealer();
        let salt = Salt([7u8; 16]);
        for pt in [
            &b"hidden message"[..],
            &[][..],
            &[0u8, 255, 1, 254, 128][..],
        ] {
            let sealed = s.seal(b"correct horse", &salt, pt).unwrap();
            // Ciphertext is exactly plaintext + the 16-byte tag.
            assert_eq!(sealed.ciphertext.len(), pt.len() + TAG_LEN);
            let opened = s
                .open(b"correct horse", &salt, &sealed.nonce, &sealed.ciphertext)
                .unwrap();
            assert_eq!(opened, pt);
        }
    }

    #[test]
    fn wrong_passphrase_is_authfailed() {
        let s = fast_sealer();
        let salt = Salt([3u8; 16]);
        let sealed = s.seal(b"right", &salt, b"secret").unwrap();
        assert!(matches!(
            s.open(b"wrong", &salt, &sealed.nonce, &sealed.ciphertext),
            Err(StegoError::AuthFailed)
        ));
    }

    #[test]
    fn tampered_ciphertext_is_authfailed() {
        let s = fast_sealer();
        let salt = Salt([9u8; 16]);
        let sealed = s.seal(b"pw", &salt, b"secret payload").unwrap();
        let mut ct = sealed.ciphertext.clone();
        ct[0] ^= 0x01;
        assert!(matches!(
            s.open(b"pw", &salt, &sealed.nonce, &ct),
            Err(StegoError::AuthFailed)
        ));
    }

    #[test]
    fn salt_binds_the_key() {
        // The same passphrase under a different salt cannot open the ciphertext (salt feeds the KDF).
        let s = fast_sealer();
        let sealed = s.seal(b"pw", &Salt([1u8; 16]), b"x").unwrap();
        assert!(matches!(
            s.open(b"pw", &Salt([2u8; 16]), &sealed.nonce, &sealed.ciphertext),
            Err(StegoError::AuthFailed)
        ));
    }
}
