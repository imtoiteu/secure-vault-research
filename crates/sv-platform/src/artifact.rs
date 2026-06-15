//! Passphrase-sealed artifact: the shared on-disk format behind Encrypt File (`.svenc`) and
//! the at-rest signing key (`.svkey`). One mechanism, two MAGICs.
//!
//! Layout (fixed binary, self-describing, versioned):
//! ```text
//! off  len  field
//! 0    6    MAGIC               (e.g. b"SVENC\0")
//! 6    2    format_version u16  LE
//! 8    1    kdf_alg             (0 = Argon2id)
//! 9    4    argon2 mem_kib u32  LE
//! 13   4    argon2 time_cost    LE
//! 17   4    argon2 parallelism  LE
//! 21   16   salt
//! 37   1    aead_alg            (0 = XSalsa20-Poly1305 secretbox)
//! 38   24   nonce
//! 62   ..   ciphertext (secretbox output; includes the 16-byte Poly1305 tag)
//! ```
//!
//! Security: the header (algorithm ids, params, salt, nonce) is non-secret — the same stance as
//! the vault header. The payload is authenticated; any header/byte tamper fails `secretbox::open`
//! and surfaces as the merged [`PlatformError::AuthFailed`]. Because the header is
//! attacker-influenceable *before* any authentication, the Argon2 cost parameters are validated
//! against fixed ceilings before the KDF runs (DoS guard; mirrors the vault's `validate_kdf`).

use sv_crypto::{secretbox, Argon2Kdf, Blake3Hasher};
use sv_crypto_traits::{Argon2idParams, Kdf, KdfParams, Key32, KeyDerivation, Salt};

use crate::error::PlatformError;

const FORMAT_VERSION: u16 = 1;
const KDF_ALG_ARGON2ID: u8 = 0;
const AEAD_ALG_SECRETBOX: u8 = 0;
const SALT_LEN: usize = 16;
const NONCE_LEN: usize = 24; // XSalsa20-Poly1305 (libsodium SECRETBOX_NONCEBYTES)
/// Bytes before the ciphertext: 6 + 2 + 1 + 4 + 4 + 4 + 16 + 1 + 24.
const HEADER_LEN: usize = 6 + 2 + 1 + 4 + 4 + 4 + SALT_LEN + 1 + NONCE_LEN;

// Pre-auth Argon2 ceilings (the header is attacker-influenceable). Generous — far above any honest
// configuration. Mirror of `sv_app::service`'s `MAX_KDF_*`.
const MAX_KDF_MEM_KIB: u32 = 4 * 1024 * 1024; // 4 GiB
const MAX_KDF_TIME_COST: u32 = 64;
const MAX_KDF_PARALLELISM: u32 = 64;

/// Encrypt-encoded payload length is the header plus the ciphertext. Exposed so callers can size
/// the decrypt read cap (ciphertext ≈ plaintext size).
pub(crate) const HEADER_OVERHEAD: u64 = HEADER_LEN as u64 + 16; // + Poly1305 tag

/// Seal `plaintext` under `passphrase` with a fresh salt, returning the full artifact bytes.
pub(crate) fn seal_with_passphrase(
    magic: &[u8; 6],
    passphrase: &[u8],
    plaintext: &[u8],
) -> Result<Vec<u8>, PlatformError> {
    let mut salt = [0u8; SALT_LEN];
    getrandom::getrandom(&mut salt).map_err(|_| PlatformError::Internal)?;

    let KdfParams::Argon2id(params) = sv_crypto::policy::recommended();
    let fek = derive_file_key(magic, passphrase, &salt, &params)?;
    let wrapped = secretbox::seal(fek.expose_secret(), plaintext);

    let mut out = Vec::with_capacity(HEADER_LEN + wrapped.ciphertext.len());
    out.extend_from_slice(magic);
    out.extend_from_slice(&FORMAT_VERSION.to_le_bytes());
    out.push(KDF_ALG_ARGON2ID);
    out.extend_from_slice(&params.mem_kib.to_le_bytes());
    out.extend_from_slice(&params.time_cost.to_le_bytes());
    out.extend_from_slice(&params.parallelism.to_le_bytes());
    out.extend_from_slice(&salt);
    out.push(AEAD_ALG_SECRETBOX);
    out.extend_from_slice(&wrapped.nonce);
    out.extend_from_slice(&wrapped.ciphertext);
    Ok(out)
}

/// Parse + authenticate an artifact, returning the recovered plaintext. A wrong passphrase or any
/// tamper fails identically as [`PlatformError::AuthFailed`] (oracle-safe).
pub(crate) fn open_with_passphrase(
    magic: &[u8; 6],
    passphrase: &[u8],
    blob: &[u8],
) -> Result<Vec<u8>, PlatformError> {
    if blob.len() < HEADER_LEN || &blob[0..6] != magic {
        return Err(PlatformError::Malformed);
    }
    let version = u16::from_le_bytes([blob[6], blob[7]]);
    if version != FORMAT_VERSION {
        return Err(PlatformError::IncompatibleVersion {
            found: version,
            supported: FORMAT_VERSION,
        });
    }
    if blob[8] != KDF_ALG_ARGON2ID || blob[37] != AEAD_ALG_SECRETBOX {
        return Err(PlatformError::Malformed);
    }
    let mem_kib = u32::from_le_bytes(four(blob, 9));
    let time_cost = u32::from_le_bytes(four(blob, 13));
    let parallelism = u32::from_le_bytes(four(blob, 17));
    // Pre-auth DoS guard: refuse hostile cost parameters before running Argon2.
    if mem_kib > MAX_KDF_MEM_KIB
        || time_cost > MAX_KDF_TIME_COST
        || parallelism > MAX_KDF_PARALLELISM
    {
        return Err(PlatformError::Malformed);
    }
    let salt: [u8; SALT_LEN] = blob[21..37].try_into().expect("checked length");
    let nonce: [u8; NONCE_LEN] = blob[38..62].try_into().expect("checked length");
    let ciphertext = blob[62..].to_vec();

    let params = Argon2idParams {
        mem_kib,
        time_cost,
        parallelism,
    };
    let fek = derive_file_key(magic, passphrase, &salt, &params)?;
    let wrapped = secretbox::Wrapped { nonce, ciphertext };
    secretbox::open(fek.expose_secret(), &wrapped).map_err(|_| PlatformError::AuthFailed)
}

/// Derive the file-encryption key: Argon2id(passphrase, salt) → BLAKE3 `derive_key` with a
/// per-artifact-type domain separator. Mirrors the vault's derive-then-wrap pattern (P3/P4).
fn derive_file_key(
    magic: &[u8; 6],
    passphrase: &[u8],
    salt: &[u8; SALT_LEN],
    params: &Argon2idParams,
) -> Result<Key32, PlatformError> {
    let mk = Argon2Kdf
        .derive(passphrase, &Salt(*salt), &KdfParams::Argon2id(*params))
        .map_err(|_| PlatformError::Internal)?;
    let context = derive_context(magic);
    Ok(Blake3Hasher.derive_key(&context, mk.expose_secret()))
}

/// Domain-separation context tied to the artifact type, e.g. `secure-vault/platform/v1/SVENC`.
fn derive_context(magic: &[u8; 6]) -> String {
    let tag = String::from_utf8_lossy(magic);
    format!("secure-vault/platform/v1/{}", tag.trim_end_matches('\0'))
}

#[inline]
fn four(b: &[u8], off: usize) -> [u8; 4] {
    b[off..off + 4].try_into().expect("checked length")
}

#[cfg(test)]
mod tests {
    use super::*;

    const M: &[u8; 6] = b"SVTST\0";

    #[test]
    fn seal_open_roundtrip() {
        let blob = seal_with_passphrase(M, b"pw", b"hello world").unwrap();
        assert_eq!(&blob[0..6], M);
        assert!(blob.len() > HEADER_LEN);
        assert_eq!(
            open_with_passphrase(M, b"pw", &blob).unwrap(),
            b"hello world"
        );
    }

    #[test]
    fn wrong_passphrase_is_auth_failed_not_distinguishable_from_tamper() {
        let mut blob = seal_with_passphrase(M, b"right", b"secret").unwrap();
        assert!(matches!(
            open_with_passphrase(M, b"wrong", &blob),
            Err(PlatformError::AuthFailed)
        ));
        // Flip a ciphertext byte → same AuthFailed.
        let last = blob.len() - 1;
        blob[last] ^= 0xff;
        assert!(matches!(
            open_with_passphrase(M, b"right", &blob),
            Err(PlatformError::AuthFailed)
        ));
    }

    #[test]
    fn wrong_magic_is_malformed() {
        let blob = seal_with_passphrase(M, b"pw", b"x").unwrap();
        assert!(matches!(
            open_with_passphrase(b"OTHER\0", b"pw", &blob),
            Err(PlatformError::Malformed)
        ));
        assert!(matches!(
            open_with_passphrase(M, b"pw", b"tooshort"),
            Err(PlatformError::Malformed)
        ));
    }

    #[test]
    fn bumped_version_is_incompatible() {
        let mut blob = seal_with_passphrase(M, b"pw", b"x").unwrap();
        blob[6] = 9; // format_version low byte → 9
        blob[7] = 0;
        assert!(matches!(
            open_with_passphrase(M, b"pw", &blob),
            Err(PlatformError::IncompatibleVersion {
                found: 9,
                supported: 1
            })
        ));
    }

    #[test]
    fn hostile_kdf_params_rejected_before_running() {
        let mut blob = seal_with_passphrase(M, b"pw", b"x").unwrap();
        // Set mem_kib to an absurd value → refused as Malformed (no Argon2 run).
        blob[9..13].copy_from_slice(&u32::MAX.to_le_bytes());
        assert!(matches!(
            open_with_passphrase(M, b"pw", &blob),
            Err(PlatformError::Malformed)
        ));
    }

    #[test]
    fn distinct_artifact_types_do_not_cross_open() {
        // Same passphrase, different MAGIC → different derive context → cannot open.
        let blob = seal_with_passphrase(b"SVENC\0", b"pw", b"payload").unwrap();
        // Rewrite the magic in place so structural checks pass but the context differs.
        let mut as_svkey = blob.clone();
        as_svkey[0..6].copy_from_slice(b"SVKEY\0");
        assert!(matches!(
            open_with_passphrase(b"SVKEY\0", b"pw", &as_svkey),
            Err(PlatformError::AuthFailed)
        ));
    }
}
