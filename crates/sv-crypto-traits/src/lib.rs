//! # sv-crypto-traits — stable crypto contract layer
//!
//! The dependency-light ABI that the rest of the system (and future plugins/ciphers)
//! compiles against: cryptographic **traits**, the **value types** that flow across
//! them, and **algorithm identifiers**. It contains no backends (no blake3/argon2/FFI);
//! the `sv-crypto` crate provides the concrete adapters and re-exports this crate.
//!
//! ## Secret hygiene (M0.1)
//! Secret-bearing types are **growth-proof** and zeroize on drop, redact `Debug`, and are
//! never `Serialize`:
//! - [`Key32`] — fixed 32-byte key (KEK/SWK/MK/derived/recovered); no heap, in-place zeroize.
//! - [`KeyShare`] — fixed 33-byte authenticated Shamir share.
//! - [`SecretBytes`] — variable-length secret backed by `Box<[u8]>` (no spare capacity,
//!   no mutation API → cannot reallocate and leak).
//!
//! Non-secret types (hashes, public keys, salts, KDF params, signatures, algorithm ids)
//! are `Serialize` and may be embedded in the vault header / DTOs.

#![forbid(unsafe_code)]

use serde::{Deserialize, Serialize};
use std::io::{Read, Write};
use zeroize::{Zeroize, ZeroizeOnDrop};

/// BLAKE3 digest length and symmetric key length (bytes).
pub const HASH_LEN: usize = 32;
/// Derived/symmetric key length (bytes).
pub const KEY_LEN: usize = 32;
/// Argon2id salt length (bytes).
pub const SALT_LEN: usize = 16;
/// One authenticated Shamir key-share length (`sss_KEYSHARE_LEN`). **Canonical source**
/// of this constant; `sv-sys-sss` re-exports it and asserts it against the C header in M2.
pub const KEYSHARE_LEN: usize = 33;

// ===========================================================================
// Algorithm identifiers (the building blocks of the M5 header "suite" block)
// ===========================================================================

/// Password-based KDF algorithm id.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum KdfAlg {
    Argon2id,
}

/// Content-hash algorithm id.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum HashAlg {
    Blake3,
}

/// Authenticated-encryption algorithm id used to wrap stored secrets.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum AeadAlg {
    /// libsodium `crypto_secretbox` (XSalsa20-Poly1305).
    XSalsa20Poly1305,
}

/// File-encryption algorithm id.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum FileCipherAlg {
    /// age v1 (X25519 + ChaCha20-Poly1305).
    AgeV1,
}

/// Signature algorithm id.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum SigAlg {
    /// Ed25519 in minisign on-disk format.
    Ed25519Minisign,
}

// ===========================================================================
// Value types — non-secret
// ===========================================================================

/// A 32-byte BLAKE3 digest. Non-secret.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct Hash32(pub [u8; HASH_LEN]);

impl Hash32 {
    /// Lowercase hex rendering.
    #[must_use]
    pub fn to_hex(&self) -> String {
        hex_encode(&self.0)
    }
}

/// Argon2id cost parameters. Non-secret.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct Argon2idParams {
    pub mem_kib: u32,
    pub time_cost: u32,
    pub parallelism: u32,
}

impl Default for Argon2idParams {
    /// Conservative interactive default (open question Q5 — recalibrate in M7).
    /// 256 MiB / 3 passes / 1 lane.
    fn default() -> Self {
        Self {
            mem_kib: 262_144,
            time_cost: 3,
            parallelism: 1,
        }
    }
}

/// KDF parameters, tagged by algorithm so a second KDF can be added without a breaking
/// change to the type that the M5 header serializes.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum KdfParams {
    Argon2id(Argon2idParams),
}

impl KdfParams {
    /// The algorithm this params value selects.
    #[must_use]
    pub fn alg(&self) -> KdfAlg {
        match self {
            KdfParams::Argon2id(_) => KdfAlg::Argon2id,
        }
    }
}

impl Default for KdfParams {
    fn default() -> Self {
        KdfParams::Argon2id(Argon2idParams::default())
    }
}

/// Argon2id salt. Non-secret.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct Salt(pub [u8; SALT_LEN]);

/// A detached signature in minisign's on-disk format. Non-secret.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MinisignSignature(pub Vec<u8>);

/// An Ed25519 public (verification) key. Non-secret.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct Ed25519PublicKey(pub [u8; 32]);

/// An age recipient (public key, `age1…`). Non-secret.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AgeRecipient(pub String);

// ===========================================================================
// Value types — secret (growth-proof, zeroizing, redacted Debug, never Serialize)
// ===========================================================================

/// A fixed 32-byte secret key (master key, KEK, SWK, derived/recovered key). No heap, so
/// it cannot reallocate; zeroized in place on drop.
#[derive(Clone, Zeroize, ZeroizeOnDrop)]
pub struct Key32([u8; KEY_LEN]);

impl Key32 {
    #[must_use]
    pub fn new(bytes: [u8; KEY_LEN]) -> Self {
        Self(bytes)
    }
    #[must_use]
    pub fn expose_secret(&self) -> &[u8; KEY_LEN] {
        &self.0
    }
}

impl core::fmt::Debug for Key32 {
    fn fmt(&self, f: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
        write!(f, "Key32(<redacted>)")
    }
}

/// One opaque authenticated Shamir key-share (fixed `KEYSHARE_LEN` bytes). Secret: a
/// threshold of shares reconstructs the key.
#[derive(Clone, Zeroize, ZeroizeOnDrop)]
pub struct KeyShare([u8; KEYSHARE_LEN]);

impl KeyShare {
    #[must_use]
    pub fn new(bytes: [u8; KEYSHARE_LEN]) -> Self {
        Self(bytes)
    }
    #[must_use]
    pub fn expose_secret(&self) -> &[u8; KEYSHARE_LEN] {
        &self.0
    }
}

impl core::fmt::Debug for KeyShare {
    fn fmt(&self, f: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
        write!(f, "KeyShare(<redacted>)")
    }
}

/// Variable-length secret bytes (e.g. an age identity blob). Backed by `Box<[u8]>` with
/// no spare capacity and no mutation API, so it cannot grow/reallocate and leave an
/// un-zeroized copy. Zeroized on drop; `Debug` redacted; never `Serialize`.
#[derive(Clone)]
pub struct SecretBytes(Box<[u8]>);

impl SecretBytes {
    /// Take ownership of `bytes`, dropping any spare capacity.
    #[must_use]
    pub fn new(bytes: Vec<u8>) -> Self {
        Self(bytes.into_boxed_slice())
    }
    /// Borrow the secret bytes. Do not copy these into non-zeroizing buffers.
    #[must_use]
    pub fn expose_secret(&self) -> &[u8] {
        &self.0
    }
    #[must_use]
    pub fn len(&self) -> usize {
        self.0.len()
    }
    #[must_use]
    pub fn is_empty(&self) -> bool {
        self.0.is_empty()
    }
}

impl Drop for SecretBytes {
    fn drop(&mut self) {
        self.0.zeroize();
    }
}

impl core::fmt::Debug for SecretBytes {
    fn fmt(&self, f: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
        write!(f, "SecretBytes(<redacted {} bytes>)", self.0.len())
    }
}

/// An age identity (secret key, `AGE-SECRET-KEY-1…`). Secret; redacted; zeroizing via the
/// wrapped [`SecretBytes`].
#[derive(Clone)]
pub struct AgeIdentity(SecretBytes);

impl AgeIdentity {
    #[must_use]
    pub fn new(secret: SecretBytes) -> Self {
        Self(secret)
    }
    #[must_use]
    pub fn expose_secret(&self) -> &[u8] {
        self.0.expose_secret()
    }
}

impl core::fmt::Debug for AgeIdentity {
    fn fmt(&self, f: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
        write!(f, "AgeIdentity(<redacted>)")
    }
}

// ===========================================================================
// Errors
// ===========================================================================

/// Failure modes common to the crypto adapters. The vault layer maps these into its own
/// taxonomy (`sv_core::VaultError`) and ultimately into the oracle-safe `sv_types::ApiError`.
#[derive(Debug, thiserror::Error)]
pub enum CryptoError {
    #[error("invalid parameter: {0}")]
    InvalidParameter(String),
    #[error("authentication/verification failed")]
    VerificationFailed,
    #[error("backend failure: {0}")]
    Backend(String),
    /// A backend operation exceeded its wall-clock deadline (e.g. an `age` subprocess on an
    /// oversized payload, or a hung/slow binary). Distinct from [`CryptoError::Backend`] so
    /// callers can surface an actionable "timed out" instead of a generic internal error.
    #[error("operation timed out")]
    Timeout,
    #[error("operation not yet implemented (stub)")]
    NotImplemented,
}

// ===========================================================================
// Traits (the frozen Phase-1 crypto contracts)
// ===========================================================================

/// Content hashing (BLAKE3) — integrity (#4). Key derivation is a separate concern
/// ([`KeyDerivation`]) so a hash-only adapter need not provide it.
pub trait Hasher {
    /// Algorithm this adapter implements.
    fn alg(&self) -> HashAlg;
    /// One-shot unkeyed hash.
    fn hash(&self, input: &[u8]) -> Hash32;
    /// Keyed hash (MAC mode).
    fn keyed_hash(&self, key: &[u8; KEY_LEN], input: &[u8]) -> Hash32;
    /// An incremental hasher for streaming large inputs.
    fn streaming(&self) -> Box<dyn StreamingHasher>;
}

/// Domain-separated subkey derivation (`BLAKE3::derive_key`). Separated from [`Hasher`].
pub trait KeyDerivation {
    /// Derive a 32-byte subkey from `context` (domain separator) and input keying material.
    fn derive_key(&self, context: &str, ikm: &[u8]) -> Key32;
}

/// Incremental hashing handle (for inputs too large to buffer).
pub trait StreamingHasher {
    fn update(&mut self, input: &[u8]);
    fn finalize(self: Box<Self>) -> Hash32;
}

/// Password-based key derivation (Argon2id). The sole passphrase KDF in the system.
pub trait Kdf {
    /// Algorithm this adapter implements.
    fn alg(&self) -> KdfAlg;
    /// Derive a 32-byte master key from a passphrase.
    fn derive(
        &self,
        passphrase: &[u8],
        salt: &Salt,
        params: &KdfParams,
    ) -> Result<Key32, CryptoError>;
}

/// Ed25519 signatures in minisign's on-disk format (provenance/authenticity #5).
pub trait Signer {
    /// Algorithm this adapter implements.
    fn alg(&self) -> SigAlg;
    /// Generate a fresh keypair `(secret_key, public_key)`.
    fn generate(&self) -> Result<(SecretBytes, Ed25519PublicKey), CryptoError>;
    /// Sign `message`, embedding `trusted_comment` per the minisign format.
    fn sign(
        &self,
        message: &[u8],
        secret_key: &SecretBytes,
        trusted_comment: &str,
    ) -> Result<MinisignSignature, CryptoError>;
    /// Verify a detached signature. `Ok(())` on success, [`CryptoError::VerificationFailed`] otherwise.
    fn verify(
        &self,
        message: &[u8],
        signature: &MinisignSignature,
        public_key: &Ed25519PublicKey,
    ) -> Result<(), CryptoError>;
}

/// Shamir secret sharing over the vault master key (key recovery). Distinct from
/// Phase-2 file-splitting: shares protect a *secret*, not data redundancy.
pub trait SecretSharer {
    /// Split a 32-byte key into `shares_total` authenticated shares, any `threshold` of
    /// which reconstruct it.
    fn split(
        &self,
        key: &Key32,
        shares_total: u8,
        threshold: u8,
    ) -> Result<Vec<KeyShare>, CryptoError>;
    /// Reconstruct the key from `>= threshold` shares.
    fn combine(&self, shares: &[KeyShare]) -> Result<Key32, CryptoError>;
}

/// Streaming file encryption/decryption (age). Drives the bundled `age` subprocess.
pub trait FileCipher {
    /// Algorithm this adapter implements.
    fn alg(&self) -> FileCipherAlg;
    /// Encrypt `plaintext` → `ciphertext` for `recipient`.
    fn encrypt(
        &self,
        plaintext: &mut dyn Read,
        ciphertext: &mut dyn Write,
        recipient: &AgeRecipient,
    ) -> Result<(), CryptoError>;
    /// Decrypt `ciphertext` → `plaintext` using `identity`.
    fn decrypt(
        &self,
        ciphertext: &mut dyn Read,
        plaintext: &mut dyn Write,
        identity: &AgeIdentity,
    ) -> Result<(), CryptoError>;
}

// ===========================================================================
// Helper (kept local to avoid a hex dependency)
// ===========================================================================

fn hex_encode(bytes: &[u8]) -> String {
    const HEX: &[u8; 16] = b"0123456789abcdef";
    let mut out = String::with_capacity(bytes.len() * 2);
    for &b in bytes {
        out.push(HEX[(b >> 4) as usize] as char);
        out.push(HEX[(b & 0x0f) as usize] as char);
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn key32_debug_is_redacted() {
        let k = Key32::new([7; KEY_LEN]);
        let r = format!("{k:?}");
        assert!(r.contains("redacted"));
        assert!(!r.contains('7'));
        assert_eq!(k.expose_secret(), &[7; KEY_LEN]);
    }

    #[test]
    fn secretbytes_debug_redacted_and_growth_proof() {
        let s = SecretBytes::new(vec![1, 2, 3, 4]);
        let r = format!("{s:?}");
        assert!(r.contains("redacted"));
        assert!(!r.contains('1'));
        assert_eq!(s.len(), 4);
        // Backed by a boxed slice: exact length, no spare capacity to leak.
        assert_eq!(s.expose_secret().len(), 4);
    }

    #[test]
    fn keyshare_is_fixed_length() {
        let share = KeyShare::new([9; KEYSHARE_LEN]);
        assert_eq!(share.expose_secret().len(), KEYSHARE_LEN);
        assert!(format!("{share:?}").contains("redacted"));
    }

    #[test]
    fn kdf_params_tags_algorithm_and_defaults_are_conservative() {
        let p = KdfParams::default();
        assert_eq!(p.alg(), KdfAlg::Argon2id);
        let KdfParams::Argon2id(a) = p;
        assert!(a.mem_kib >= 19_456); // >= OWASP Argon2id floor
        assert!(a.time_cost >= 2);
        assert!(a.parallelism >= 1);
    }

    #[test]
    fn hash_hex_is_lowercase_and_full_width() {
        assert_eq!(Hash32([0xab; HASH_LEN]).to_hex(), "ab".repeat(HASH_LEN));
    }

    #[test]
    fn non_secret_types_serialize() {
        let v = serde_json::json!({
            "params": KdfParams::default(),
            "salt": Salt([7; SALT_LEN]),
            "pk": Ed25519PublicKey([9; 32]),
            "kdf_alg": KdfAlg::Argon2id,
            "sig_alg": SigAlg::Ed25519Minisign,
        });
        assert!(v.is_object());
    }
}
