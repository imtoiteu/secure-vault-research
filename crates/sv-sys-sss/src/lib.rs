//! # sv-sys-sss — FFI to Daan Sprenkels' `sss` hazmat key-sharing
//!
//! Wraps the vendored `hazmat.c` (compiled by `build.rs`) exposing GF(2⁸) Shamir sharing
//! of a 32-byte key:
//! - [`create_keyshares`] → `sss_create_keyshares`
//! - [`combine_keyshares`] → `sss_combine_keyshares`
//!
//! Each share is `KEYSHARE_LEN` (33) bytes and self-describes its x-coordinate in byte 0,
//! so `combine` needs no external index bookkeeping. The hazmat layer does **no**
//! integrity checking — authentication happens one layer up (a reconstructed master key
//! that is wrong simply fails the authenticated secretbox unwrap of the vault identity).
//!
//! `randombytes` (used by `hazmat.c` to pick polynomial coefficients) is provided here
//! from Rust via [`getrandom`], exported with C ABI, so there is no platform-specific C
//! randomness code to maintain. It is exported as `sv_sss_randombytes` (and `hazmat.c` is
//! compiled to call that name — see `build.rs`) so the symbol does not collide with
//! libsodium's `randombytes`, which is also linked into the final binary.

#![allow(unsafe_code)] // this is the FFI boundary crate

pub use sv_crypto_traits::KEYSHARE_LEN;

/// Compile-time guarantee that the Rust-side `KEYSHARE_LEN` matches the value baked into
/// the vendored C header (`sss_KEYSHARE_LEN == 33`). If upstream ever changes it, this
/// fails the build instead of silently corrupting share layout (B3).
const _: () = assert!(KEYSHARE_LEN == 33);

const KEY_LEN: usize = 32;

extern "C" {
    fn sss_create_keyshares(out: *mut u8, key: *const u8, n: u8, k: u8);
    fn sss_combine_keyshares(key: *mut u8, shares: *const u8, k: u8);
}

/// C-ABI randomness shim that `hazmat.c` links against (compiled to call this name via the
/// `randombytes` → `sv_sss_randombytes` rename in `build.rs`, avoiding a clash with libsodium's
/// `randombytes`). Fills `buf[0..n]` with OS CSPRNG bytes; returns 0 on success, -1 on failure
/// (matching the sss/libsodium convention).
///
/// # Safety
/// `buf` must point to at least `n` writable bytes. Called only by the vendored C.
#[no_mangle]
pub unsafe extern "C" fn sv_sss_randombytes(
    buf: *mut core::ffi::c_void,
    n: usize,
) -> core::ffi::c_int {
    if buf.is_null() || n == 0 {
        return 0;
    }
    let slice = core::slice::from_raw_parts_mut(buf.cast::<u8>(), n);
    match getrandom::getrandom(slice) {
        Ok(()) => 0,
        Err(_) => -1,
    }
}

/// Split a 32-byte `key` into `n` authenticated-by-construction shares, any `k` of which
/// reconstruct it. Returns one `KEYSHARE_LEN`-byte share per requested share.
///
/// Returns `Err` for structurally invalid `(n, k)`: requires `1 <= k <= n`.
pub fn create_keyshares(
    key: &[u8; KEY_LEN],
    n: u8,
    k: u8,
) -> Result<Vec<[u8; KEYSHARE_LEN]>, ShareError> {
    if k == 0 || n == 0 || k > n {
        return Err(ShareError::InvalidThreshold { n, k });
    }
    let mut out = vec![[0u8; KEYSHARE_LEN]; n as usize];
    // SAFETY: `out` holds exactly `n * KEYSHARE_LEN` contiguous bytes (the C type is
    // `sss_Keyshare[n]`), `key` is 32 bytes, and `n`/`k` are validated public values.
    unsafe {
        sss_create_keyshares(out.as_mut_ptr().cast::<u8>(), key.as_ptr(), n, k);
    }
    Ok(out)
}

/// Reconstruct the 32-byte key from `shares` (must be at least the original threshold;
/// each share self-describes its x-coordinate). Returns `Err` if no shares are given.
///
/// No integrity check is performed: an incorrect or insufficient share set yields a
/// wrong key rather than an error (by design — verification is done by the caller).
pub fn combine_keyshares(shares: &[[u8; KEYSHARE_LEN]]) -> Result<[u8; KEY_LEN], ShareError> {
    let k = u8::try_from(shares.len()).map_err(|_| ShareError::TooManyShares)?;
    if k == 0 {
        return Err(ShareError::NoShares);
    }
    let mut key = [0u8; KEY_LEN];
    // SAFETY: `shares` is `k` contiguous `KEYSHARE_LEN`-byte shares; `key` is 32 bytes.
    unsafe {
        sss_combine_keyshares(key.as_mut_ptr(), shares.as_ptr().cast::<u8>(), k);
    }
    Ok(key)
}

/// Errors from the share API.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ShareError {
    /// `(n, k)` violated `1 <= k <= n`.
    InvalidThreshold { n: u8, k: u8 },
    /// No shares supplied to `combine`.
    NoShares,
    /// More than 255 shares supplied to `combine`.
    TooManyShares,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn split_then_combine_roundtrips() {
        let key = [7u8; KEY_LEN];
        let shares = create_keyshares(&key, 5, 3).unwrap();
        assert_eq!(shares.len(), 5);
        // Any 3 of 5 reconstruct.
        let subset = vec![shares[0], shares[2], shares[4]];
        assert_eq!(combine_keyshares(&subset).unwrap(), key);
        // All 5 also work.
        assert_eq!(combine_keyshares(&shares).unwrap(), key);
    }

    #[test]
    fn below_threshold_does_not_recover_key() {
        let key = [0xABu8; KEY_LEN];
        let shares = create_keyshares(&key, 5, 3).unwrap();
        // Only 2 shares (< k=3) → reconstructs *something*, but not the real key.
        let two = vec![shares[0], shares[1]];
        assert_ne!(combine_keyshares(&two).unwrap(), key);
    }

    #[test]
    fn invalid_threshold_rejected() {
        assert_eq!(
            create_keyshares(&[0; KEY_LEN], 3, 0),
            Err(ShareError::InvalidThreshold { n: 3, k: 0 })
        );
        assert_eq!(
            create_keyshares(&[0; KEY_LEN], 2, 5),
            Err(ShareError::InvalidThreshold { n: 2, k: 5 })
        );
    }

    #[test]
    fn randomness_makes_shares_unique_per_split() {
        let key = [1u8; KEY_LEN];
        let a = create_keyshares(&key, 3, 2).unwrap();
        let b = create_keyshares(&key, 3, 2).unwrap();
        // Same secret, but fresh random polynomials → different share bytes...
        assert_ne!(a[0], b[0]);
        // ...yet both still reconstruct the same key.
        assert_eq!(combine_keyshares(&a[..2]).unwrap(), key);
        assert_eq!(combine_keyshares(&b[..2]).unwrap(), key);
    }
}
