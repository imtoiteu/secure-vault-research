//! # sv-crypto — concrete cryptographic adapters
//!
//! Thin crate over [`sv_crypto_traits`] (re-exported below, so existing `use sv_crypto::…`
//! paths keep working). It holds the **adapter implementations**.
//!
//! | Trait(s)                   | Adapter                  | Backend / Status |
//! |----------------------------|--------------------------|------------------|
//! | `Hasher` + `KeyDerivation` | [`Blake3Hasher`]         | `blake3` crate — **M1 done** |
//! | `Kdf`                      | [`Argon2Kdf`]            | `argon2` crate — **M1 done** |
//! | `Signer`                   | [`SodiumMinisignSigner`] | libsodium FFI — **M2 done** |
//! | `SecretSharer`             | [`SssSharer`]            | libsss FFI — **M2 done** |
//! | `FileCipher`               | `sv_age::AgeCipher`      | bundled `age` — **M3 done** |
//!
//! Also: [`secretbox`] (KEK/SWK wrapping) and [`policy`] (Argon2id strength floor).

#![forbid(unsafe_code)]

use argon2::{Algorithm, Argon2, Params, Version};
use zeroize::Zeroize;

pub use sv_crypto_traits::*;

mod minisign;
pub mod policy;
pub mod secretbox;

/// BLAKE3 hasher + key-derivation adapter (M1).
#[derive(Debug, Default, Clone, Copy)]
pub struct Blake3Hasher;

impl Hasher for Blake3Hasher {
    fn alg(&self) -> HashAlg {
        HashAlg::Blake3
    }
    fn hash(&self, input: &[u8]) -> Hash32 {
        Hash32(*blake3::hash(input).as_bytes())
    }
    fn keyed_hash(&self, key: &[u8; KEY_LEN], input: &[u8]) -> Hash32 {
        Hash32(*blake3::keyed_hash(key, input).as_bytes())
    }
    fn streaming(&self) -> Box<dyn StreamingHasher> {
        Box::new(Blake3Streaming(blake3::Hasher::new()))
    }
}

impl KeyDerivation for Blake3Hasher {
    fn derive_key(&self, context: &str, ikm: &[u8]) -> Key32 {
        // `blake3::derive_key` returns a fresh `[u8; 32]`; move it into the zeroizing
        // `Key32` and wipe the scratch copy.
        let mut out = blake3::derive_key(context, ikm);
        let key = Key32::new(out);
        out.zeroize();
        key
    }
}

/// Incremental BLAKE3 hasher returned by [`Blake3Hasher::streaming`].
#[derive(Debug, Clone)]
pub struct Blake3Streaming(blake3::Hasher);

impl StreamingHasher for Blake3Streaming {
    fn update(&mut self, input: &[u8]) {
        self.0.update(input);
    }
    fn finalize(self: Box<Self>) -> Hash32 {
        Hash32(*self.0.finalize().as_bytes())
    }
}

/// Argon2id password-based KDF adapter (M1).
#[derive(Debug, Default, Clone, Copy)]
pub struct Argon2Kdf;

impl Kdf for Argon2Kdf {
    fn alg(&self) -> KdfAlg {
        KdfAlg::Argon2id
    }

    fn derive(
        &self,
        passphrase: &[u8],
        salt: &Salt,
        params: &KdfParams,
    ) -> Result<Key32, CryptoError> {
        let KdfParams::Argon2id(p) = params;
        // Structural validation only; the OWASP *policy* floor lives in `policy` and is
        // applied at vault creation, not inside the primitive.
        let argon_params = Params::new(p.mem_kib, p.time_cost, p.parallelism, Some(KEY_LEN))
            .map_err(|e| CryptoError::InvalidParameter(e.to_string()))?;
        let argon = Argon2::new(Algorithm::Argon2id, Version::V0x13, argon_params);

        let mut out = [0u8; KEY_LEN];
        let result = argon
            .hash_password_into(passphrase, &salt.0, &mut out)
            .map_err(|e| CryptoError::Backend(e.to_string()));
        // Build the zeroizing key (or propagate the error), then wipe the scratch buffer
        // regardless of outcome.
        let key = result.map(|()| Key32::new(out));
        out.zeroize();
        key
    }
}

/// minisign-format Ed25519 signer over libsodium (M2).
#[derive(Debug, Default, Clone, Copy)]
pub struct SodiumMinisignSigner;

impl Signer for SodiumMinisignSigner {
    fn alg(&self) -> SigAlg {
        SigAlg::Ed25519Minisign
    }

    fn generate(&self) -> Result<(SecretBytes, Ed25519PublicKey), CryptoError> {
        let (pk, mut sk) = sv_sys_sodium::sign_keypair();
        let secret = SecretBytes::new(sk.to_vec());
        sk.zeroize(); // wipe the stack copy; the key now lives only in `secret`
        Ok((secret, Ed25519PublicKey(pk)))
    }

    fn sign(
        &self,
        message: &[u8],
        secret_key: &SecretBytes,
        trusted_comment: &str,
    ) -> Result<MinisignSignature, CryptoError> {
        let sk64: &[u8; 64] = secret_key
            .expose_secret()
            .try_into()
            .map_err(|_| CryptoError::InvalidParameter("secret key must be 64 bytes".into()))?;
        minisign::sign(message, sk64, trusted_comment)
    }

    fn verify(
        &self,
        message: &[u8],
        signature: &MinisignSignature,
        public_key: &Ed25519PublicKey,
    ) -> Result<(), CryptoError> {
        minisign::verify(message, signature, public_key)
    }
}

/// Shamir secret sharer over libsss hazmat (M2).
#[derive(Debug, Default, Clone, Copy)]
pub struct SssSharer;

impl SecretSharer for SssSharer {
    fn split(
        &self,
        key: &Key32,
        shares_total: u8,
        threshold: u8,
    ) -> Result<Vec<KeyShare>, CryptoError> {
        let mut raw = sv_sys_sss::create_keyshares(key.expose_secret(), shares_total, threshold)
            .map_err(|e| CryptoError::InvalidParameter(format!("{e:?}")))?;
        let out = raw.iter().map(|s| KeyShare::new(*s)).collect();
        raw.iter_mut().for_each(Zeroize::zeroize); // wipe the plaintext share scratch
        Ok(out)
    }

    fn combine(&self, shares: &[KeyShare]) -> Result<Key32, CryptoError> {
        if shares.is_empty() {
            return Err(CryptoError::InvalidParameter("no shares provided".into()));
        }
        let mut raw: Vec<[u8; KEYSHARE_LEN]> = shares.iter().map(|s| *s.expose_secret()).collect();
        let mut key = sv_sys_sss::combine_keyshares(&raw)
            .map_err(|e| CryptoError::InvalidParameter(format!("{e:?}")))?;
        let out = Key32::new(key);
        key.zeroize();
        raw.iter_mut().for_each(Zeroize::zeroize);
        Ok(out)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn adapters_report_their_algorithm_ids() {
        assert_eq!(Blake3Hasher.alg(), HashAlg::Blake3);
        assert_eq!(Argon2Kdf.alg(), KdfAlg::Argon2id);
        assert_eq!(SodiumMinisignSigner.alg(), SigAlg::Ed25519Minisign);
    }

    // ---- BLAKE3 (Hasher) --------------------------------------------------

    #[test]
    fn blake3_known_answer_empty_input() {
        // Official BLAKE3 test vector for the empty input.
        assert_eq!(
            Blake3Hasher.hash(b"").to_hex(),
            "af1349b9f5f9a1a6a0404dea36dcc9499bcb25c9adc112b7cc9a93cae41f3262"
        );
    }

    #[test]
    fn blake3_matches_reference_and_keyed() {
        assert_eq!(
            Blake3Hasher.hash(b"secure vault").0,
            *blake3::hash(b"secure vault").as_bytes()
        );
        let key = [42u8; KEY_LEN];
        assert_eq!(
            Blake3Hasher.keyed_hash(&key, b"data").0,
            *blake3::keyed_hash(&key, b"data").as_bytes()
        );
    }

    #[test]
    fn blake3_streaming_equals_one_shot() {
        let mut s = Blake3Hasher.streaming();
        s.update(b"hello ");
        s.update(b"world");
        assert_eq!(s.finalize(), Blake3Hasher.hash(b"hello world"));
    }

    // ---- BLAKE3 (KeyDerivation) ------------------------------------------

    #[test]
    fn derive_key_is_domain_separated_and_deterministic() {
        let h = Blake3Hasher;
        let a1 = h.derive_key("secure-vault v1 kek", b"master");
        let a2 = h.derive_key("secure-vault v1 kek", b"master");
        let b = h.derive_key("secure-vault v1 sign-wrap", b"master");
        // Same context+ikm → identical; different context → different.
        assert_eq!(a1.expose_secret(), a2.expose_secret());
        assert_ne!(a1.expose_secret(), b.expose_secret());
        // Cross-check against the reference function.
        assert_eq!(
            a1.expose_secret(),
            &blake3::derive_key("secure-vault v1 kek", b"master")
        );
    }

    // ---- Argon2id (Kdf) ---------------------------------------------------

    // Small, structurally-valid params keep the test fast (the OWASP floor is a policy
    // concern, asserted separately in `policy`).
    fn fast_params() -> KdfParams {
        KdfParams::Argon2id(Argon2idParams {
            mem_kib: 64,
            time_cost: 1,
            parallelism: 1,
        })
    }

    #[test]
    fn argon2_is_deterministic_and_binds_inputs() {
        let kdf = Argon2Kdf;
        let salt = Salt([1u8; SALT_LEN]);
        let p = fast_params();

        let k1 = kdf.derive(b"correct horse", &salt, &p).unwrap();
        let k2 = kdf.derive(b"correct horse", &salt, &p).unwrap();
        assert_eq!(k1.expose_secret(), k2.expose_secret()); // deterministic
        assert_eq!(k1.expose_secret().len(), KEY_LEN);

        // Different passphrase → different key.
        let k3 = kdf.derive(b"wrong horse", &salt, &p).unwrap();
        assert_ne!(k1.expose_secret(), k3.expose_secret());

        // Different salt → different key.
        let k4 = kdf
            .derive(b"correct horse", &Salt([2u8; SALT_LEN]), &p)
            .unwrap();
        assert_ne!(k1.expose_secret(), k4.expose_secret());
    }

    #[test]
    fn argon2_rejects_invalid_params() {
        let kdf = Argon2Kdf;
        let salt = Salt([0u8; SALT_LEN]);
        let bad = KdfParams::Argon2id(Argon2idParams {
            mem_kib: 64,
            time_cost: 1,
            parallelism: 0,
        });
        assert!(matches!(
            kdf.derive(b"x", &salt, &bad),
            Err(CryptoError::InvalidParameter(_))
        ));
    }

    #[test]
    fn policy_floor_distinguishes_recommended_from_fast() {
        assert!(policy::meets_recommended(&policy::recommended()));
        assert!(!policy::meets_recommended(&fast_params()));
    }

    // ---- Shamir (SecretSharer) -------------------------------------------

    #[test]
    fn sss_split_combine_roundtrips_via_key32() {
        let sharer = SssSharer;
        let key = Key32::new([0x5Au8; KEY_LEN]);
        let shares = sharer.split(&key, 5, 3).unwrap();
        assert_eq!(shares.len(), 5);
        assert_eq!(shares[0].expose_secret().len(), KEYSHARE_LEN);

        // Any 3 of 5 reconstruct the master key.
        let subset = vec![shares[0].clone(), shares[2].clone(), shares[4].clone()];
        let recovered = sharer.combine(&subset).unwrap();
        assert_eq!(recovered.expose_secret(), key.expose_secret());
    }

    #[test]
    fn sss_below_threshold_yields_wrong_key() {
        let sharer = SssSharer;
        let key = Key32::new([9u8; KEY_LEN]);
        let shares = sharer.split(&key, 5, 3).unwrap();
        let two = vec![shares[0].clone(), shares[1].clone()];
        assert_ne!(
            sharer.combine(&two).unwrap().expose_secret(),
            key.expose_secret()
        );
    }

    #[test]
    fn sss_rejects_bad_threshold_and_empty_combine() {
        let sharer = SssSharer;
        let key = Key32::new([0u8; KEY_LEN]);
        assert!(matches!(
            sharer.split(&key, 2, 5),
            Err(CryptoError::InvalidParameter(_))
        ));
        assert!(matches!(
            sharer.combine(&[]),
            Err(CryptoError::InvalidParameter(_))
        ));
    }

    // ---- minisign signer (Signer) ----------------------------------------

    #[test]
    fn minisign_sign_verify_roundtrip() {
        let signer = SodiumMinisignSigner;
        let (sk, pk) = signer.generate().unwrap();
        let msg = b"vault container hash";
        let sig = signer.sign(msg, &sk, "secure-vault v1").unwrap();
        // Output is the minisign text format.
        let text = String::from_utf8(sig.0.clone()).unwrap();
        assert!(text.starts_with("untrusted comment: "));
        assert!(text.contains("\ntrusted comment: secure-vault v1\n"));
        signer.verify(msg, &sig, &pk).unwrap();
    }

    #[test]
    fn minisign_rejects_tampered_message_comment_and_wrong_key() {
        let signer = SodiumMinisignSigner;
        let (sk, pk) = signer.generate().unwrap();
        let sig = signer.sign(b"original", &sk, "tc").unwrap();

        // Tampered message.
        assert!(signer.verify(b"changed", &sig, &pk).is_err());
        // Wrong public key.
        let (_, other_pk) = signer.generate().unwrap();
        assert!(signer.verify(b"original", &sig, &other_pk).is_err());
        // Tampered trusted comment → global signature fails.
        let mutated = String::from_utf8(sig.0.clone())
            .unwrap()
            .replace("trusted comment: tc", "trusted comment: evil");
        let bad = MinisignSignature(mutated.into_bytes());
        assert!(signer.verify(b"original", &bad, &pk).is_err());
    }

    #[test]
    fn minisign_rejects_newline_in_trusted_comment_and_bad_key_len() {
        let signer = SodiumMinisignSigner;
        let (sk, _) = signer.generate().unwrap();
        assert!(matches!(
            signer.sign(b"m", &sk, "line1\nline2"),
            Err(CryptoError::InvalidParameter(_))
        ));
        let short = SecretBytes::new(vec![0u8; 10]);
        assert!(matches!(
            signer.sign(b"m", &short, "tc"),
            Err(CryptoError::InvalidParameter(_))
        ));
    }
}
