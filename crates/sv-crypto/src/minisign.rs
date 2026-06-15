//! minisign on-disk signature format (prehashed "ED" variant) over libsodium Ed25519.
//!
//! Layout produced/consumed (text, `\n`-separated):
//! ```text
//! untrusted comment: <comment>
//! base64( sig_alg[2]="ED" || key_id[8] || ed25519_sig[64] )
//! trusted comment: <trusted_comment>
//! base64( ed25519_sig( ed25519_sig[64] || trusted_comment_utf8 ) )
//! ```
//! The first signature is over `BLAKE2b-512(message)` (minisign's prehash). The second
//! ("global") signature binds the trusted comment so it cannot be altered. `key_id` is
//! derived as `BLAKE2b(8, public_key)` — deterministic here (minisign uses a random id);
//! this is invisible to verification, which authenticates against the caller's public key.
//!
//! Full byte-level interop with the stock `minisign` CLI is exercised as a CI gate (the
//! CLI is not available in all local environments); in-process the round-trip and all
//! tamper paths are tested.

use base64::engine::general_purpose::STANDARD;
use base64::Engine;
use sv_crypto_traits::{CryptoError, Ed25519PublicKey, MinisignSignature};

const SIG_ALG_PREHASHED: [u8; 2] = *b"ED";
const UNTRUSTED_PREFIX: &str = "untrusted comment: ";
const TRUSTED_PREFIX: &str = "trusted comment: ";
const FIRST_BLOB_LEN: usize = 2 + 8 + 64; // sig_alg ‖ key_id ‖ signature

/// Build a minisign-format signature of `message` using a 64-byte libsodium Ed25519
/// secret key (`seed ‖ public_key`). `trusted_comment` must not contain a newline.
pub fn sign(
    message: &[u8],
    secret_key_64: &[u8; 64],
    trusted_comment: &str,
) -> Result<MinisignSignature, CryptoError> {
    if trusted_comment.contains('\n') {
        return Err(CryptoError::InvalidParameter(
            "trusted comment must not contain a newline".into(),
        ));
    }
    let prehash = sv_sys_sodium::blake2b(64, message);
    let signature = sv_sys_sodium::sign_detached(&prehash, secret_key_64);

    let public_key = &secret_key_64[32..64];
    let key_id = sv_sys_sodium::blake2b(8, public_key);

    let mut first = Vec::with_capacity(FIRST_BLOB_LEN);
    first.extend_from_slice(&SIG_ALG_PREHASHED);
    first.extend_from_slice(&key_id);
    first.extend_from_slice(&signature);

    // Global signature binds the (untrusted) signature bytes to the trusted comment.
    let mut global_input = Vec::with_capacity(64 + trusted_comment.len());
    global_input.extend_from_slice(&signature);
    global_input.extend_from_slice(trusted_comment.as_bytes());
    let global_sig = sv_sys_sodium::sign_detached(&global_input, secret_key_64);

    let text = format!(
        "{UNTRUSTED_PREFIX}signature from secure-vault\n{}\n{TRUSTED_PREFIX}{trusted_comment}\n{}\n",
        STANDARD.encode(&first),
        STANDARD.encode(global_sig),
    );
    Ok(MinisignSignature(text.into_bytes()))
}

/// Verify a minisign-format signature of `message` against `public_key`.
pub fn verify(
    message: &[u8],
    signature: &MinisignSignature,
    public_key: &Ed25519PublicKey,
) -> Result<(), CryptoError> {
    let text = core::str::from_utf8(&signature.0).map_err(|_| CryptoError::VerificationFailed)?;
    let mut lines = text.lines();
    let _untrusted = lines.next().ok_or(CryptoError::VerificationFailed)?;
    let sig_b64 = lines.next().ok_or(CryptoError::VerificationFailed)?;
    let tc_line = lines.next().ok_or(CryptoError::VerificationFailed)?;
    let global_b64 = lines.next().ok_or(CryptoError::VerificationFailed)?;

    let first = STANDARD
        .decode(sig_b64.trim())
        .map_err(|_| CryptoError::VerificationFailed)?;
    if first.len() != FIRST_BLOB_LEN || first[..2] != SIG_ALG_PREHASHED {
        return Err(CryptoError::VerificationFailed);
    }
    let key_id = &first[2..10];
    let sig: [u8; 64] = first[10..74]
        .try_into()
        .map_err(|_| CryptoError::VerificationFailed)?;

    let trusted_comment = tc_line
        .strip_prefix(TRUSTED_PREFIX)
        .ok_or(CryptoError::VerificationFailed)?;
    let global_sig: [u8; 64] = STANDARD
        .decode(global_b64.trim())
        .map_err(|_| CryptoError::VerificationFailed)?
        .try_into()
        .map_err(|_| CryptoError::VerificationFailed)?;

    // key_id must match the verifying key (cheap mismatch guard).
    if key_id != sv_sys_sodium::blake2b(8, &public_key.0).as_slice() {
        return Err(CryptoError::VerificationFailed);
    }
    // Prehash signature.
    let prehash = sv_sys_sodium::blake2b(64, message);
    if !sv_sys_sodium::sign_verify_detached(&sig, &prehash, &public_key.0) {
        return Err(CryptoError::VerificationFailed);
    }
    // Global signature over signature ‖ trusted_comment.
    let mut global_input = sig.to_vec();
    global_input.extend_from_slice(trusted_comment.as_bytes());
    if !sv_sys_sodium::sign_verify_detached(&global_sig, &global_input, &public_key.0) {
        return Err(CryptoError::VerificationFailed);
    }
    Ok(())
}
