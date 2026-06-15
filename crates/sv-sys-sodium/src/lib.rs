//! # sv-sys-sodium — safe wrappers over libsodium (via `libsodium-sys-stable`)
//!
//! Exposes the minimal libsodium surface the vault needs, as safe Rust functions:
//! - **Ed25519** detached signing/verification ([`sign_keypair`], [`sign_detached`],
//!   [`sign_verify_detached`]) — backs the minisign-format signer.
//! - **BLAKE2b** ([`blake2b`]) — minisign's prehash/checksum.
//! - **secretbox** (XSalsa20-Poly1305) ([`secretbox_seal`], [`secretbox_open`]) — wraps the
//!   stored age identity and signing key under the KEK/SWK.
//! - [`random_bytes`] — CSPRNG, used for nonces.
//!
//! `libsodium` is initialized lazily and idempotently before any operation.

#![allow(unsafe_code)] // FFI boundary crate

use std::sync::Once;

use libsodium_sys as sodium;

/// Ed25519 public key length.
pub const SIGN_PUBLICKEYBYTES: usize = 32;
/// Ed25519 secret key length (libsodium: seed ‖ public key).
pub const SIGN_SECRETKEYBYTES: usize = 64;
/// Ed25519 signature length.
pub const SIGN_BYTES: usize = 64;
/// secretbox key length.
pub const SECRETBOX_KEYBYTES: usize = 32;
/// secretbox nonce length.
pub const SECRETBOX_NONCEBYTES: usize = 24;
/// secretbox authentication-tag length.
pub const SECRETBOX_MACBYTES: usize = 16;

static INIT: Once = Once::new();

/// Initialize libsodium exactly once (idempotent, thread-safe). Panics only if the
/// library reports a fatal init failure, which indicates a broken build.
fn ensure_init() {
    INIT.call_once(|| {
        // SAFETY: documented as safe to call from a single thread before others; `Once`
        // guarantees exactly that.
        let rc = unsafe { sodium::sodium_init() };
        assert!(rc >= 0, "libsodium failed to initialize (rc={rc})");
    });
}

/// Fill `buf` with cryptographically secure random bytes.
pub fn random_bytes(buf: &mut [u8]) {
    ensure_init();
    // SAFETY: valid pointer/len for `buf`.
    unsafe { sodium::randombytes_buf(buf.as_mut_ptr().cast(), buf.len()) }
}

/// Generate an Ed25519 keypair `(public_key, secret_key)`.
#[must_use]
pub fn sign_keypair() -> ([u8; SIGN_PUBLICKEYBYTES], [u8; SIGN_SECRETKEYBYTES]) {
    ensure_init();
    let mut pk = [0u8; SIGN_PUBLICKEYBYTES];
    let mut sk = [0u8; SIGN_SECRETKEYBYTES];
    // SAFETY: output buffers are correctly sized for crypto_sign_keypair.
    let rc = unsafe { sodium::crypto_sign_keypair(pk.as_mut_ptr(), sk.as_mut_ptr()) };
    assert_eq!(rc, 0, "crypto_sign_keypair failed");
    (pk, sk)
}

/// Produce a detached Ed25519 signature of `message` under `secret_key`.
#[must_use]
pub fn sign_detached(message: &[u8], secret_key: &[u8; SIGN_SECRETKEYBYTES]) -> [u8; SIGN_BYTES] {
    ensure_init();
    let mut sig = [0u8; SIGN_BYTES];
    // SAFETY: sig is 64 bytes; null siglen is allowed; message/sk are valid.
    let rc = unsafe {
        sodium::crypto_sign_detached(
            sig.as_mut_ptr(),
            core::ptr::null_mut(),
            message.as_ptr(),
            message.len() as u64,
            secret_key.as_ptr(),
        )
    };
    assert_eq!(rc, 0, "crypto_sign_detached failed");
    sig
}

/// Verify a detached Ed25519 signature. Returns `true` iff valid.
#[must_use]
pub fn sign_verify_detached(
    signature: &[u8; SIGN_BYTES],
    message: &[u8],
    public_key: &[u8; SIGN_PUBLICKEYBYTES],
) -> bool {
    ensure_init();
    // SAFETY: all buffers correctly sized.
    let rc = unsafe {
        sodium::crypto_sign_verify_detached(
            signature.as_ptr(),
            message.as_ptr(),
            message.len() as u64,
            public_key.as_ptr(),
        )
    };
    rc == 0
}

/// BLAKE2b hash of `input` with the requested `out_len` (1..=64), unkeyed.
#[must_use]
pub fn blake2b(out_len: usize, input: &[u8]) -> Vec<u8> {
    ensure_init();
    assert!((1..=64).contains(&out_len), "blake2b out_len out of range");
    let mut out = vec![0u8; out_len];
    // SAFETY: out is out_len bytes; key is null/0 (unkeyed); input valid.
    let rc = unsafe {
        sodium::crypto_generichash(
            out.as_mut_ptr(),
            out_len,
            input.as_ptr(),
            input.len() as u64,
            core::ptr::null(),
            0,
        )
    };
    assert_eq!(rc, 0, "crypto_generichash failed");
    out
}

/// Seal `plaintext` under `key` with `nonce`; returns ciphertext (`plaintext.len() + 16`).
#[must_use]
pub fn secretbox_seal(
    plaintext: &[u8],
    nonce: &[u8; SECRETBOX_NONCEBYTES],
    key: &[u8; SECRETBOX_KEYBYTES],
) -> Vec<u8> {
    ensure_init();
    let mut c = vec![0u8; plaintext.len() + SECRETBOX_MACBYTES];
    // SAFETY: c is mlen+MAC bytes; nonce/key correctly sized.
    let rc = unsafe {
        sodium::crypto_secretbox_easy(
            c.as_mut_ptr(),
            plaintext.as_ptr(),
            plaintext.len() as u64,
            nonce.as_ptr(),
            key.as_ptr(),
        )
    };
    assert_eq!(rc, 0, "crypto_secretbox_easy failed");
    c
}

/// Open a secretbox ciphertext. Returns `None` on authentication failure.
#[must_use]
pub fn secretbox_open(
    ciphertext: &[u8],
    nonce: &[u8; SECRETBOX_NONCEBYTES],
    key: &[u8; SECRETBOX_KEYBYTES],
) -> Option<Vec<u8>> {
    ensure_init();
    if ciphertext.len() < SECRETBOX_MACBYTES {
        return None;
    }
    let mut m = vec![0u8; ciphertext.len() - SECRETBOX_MACBYTES];
    // SAFETY: m is clen-MAC bytes; nonce/key correctly sized.
    let rc = unsafe {
        sodium::crypto_secretbox_open_easy(
            m.as_mut_ptr(),
            ciphertext.as_ptr(),
            ciphertext.len() as u64,
            nonce.as_ptr(),
            key.as_ptr(),
        )
    };
    if rc == 0 {
        Some(m)
    } else {
        None
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn ed25519_sign_verify_roundtrip() {
        let (pk, sk) = sign_keypair();
        let msg = b"secure vault";
        let sig = sign_detached(msg, &sk);
        assert!(sign_verify_detached(&sig, msg, &pk));
        assert!(!sign_verify_detached(&sig, b"tampered", &pk));
        let (other_pk, _) = sign_keypair();
        assert!(!sign_verify_detached(&sig, msg, &other_pk));
    }

    #[test]
    fn blake2b_known_answer_and_length() {
        // BLAKE2b-512 of the empty input (RFC 7693 well-known vector, first 8 bytes).
        let h = blake2b(64, b"");
        assert_eq!(h.len(), 64);
        assert_eq!(&h[..4], &[0x78, 0x6a, 0x02, 0xf7]);
    }

    #[test]
    fn secretbox_seal_open_and_tamper() {
        let key = [3u8; SECRETBOX_KEYBYTES];
        let mut nonce = [0u8; SECRETBOX_NONCEBYTES];
        random_bytes(&mut nonce);
        let pt = b"wrapped identity";
        let mut ct = secretbox_seal(pt, &nonce, &key);
        assert_eq!(secretbox_open(&ct, &nonce, &key).as_deref(), Some(&pt[..]));
        // Tamper → None.
        ct[0] ^= 0xff;
        assert!(secretbox_open(&ct, &nonce, &key).is_none());
        // Wrong key → None.
        let ct2 = secretbox_seal(pt, &nonce, &key);
        assert!(secretbox_open(&ct2, &nonce, &[9u8; SECRETBOX_KEYBYTES]).is_none());
    }
}
