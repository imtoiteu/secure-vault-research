//! Capacity arithmetic and the up-front guard (alloc-DoS / overflow safe).
//!
//! One embedding site carries exactly one bit (the LSB of one colour sample). The SVSTEG header is
//! written into the first [`HEADER_SITES`] sites; the ciphertext body occupies
//! `ct_len * 8` further sites.
//!
//! Two guards use this module:
//! - **Hide** refuses a payload that does not fit ([`max_plaintext_bytes`]) *before* doing any
//!   (expensive) Argon2id work, surfacing the non-secret limit/actual pair.
//! - **Extract** validates a header's *declared* `ct_len` against the actual carrier capacity
//!   ([`required_sites`]) *before* allocating, so a crafted frame cannot request a huge read.

use crate::envelope::HEADER_LEN;
use crate::seal::TAG_LEN;

/// Bits carried per embedding site (LSB steganography).
pub const BITS_PER_SITE: usize = 1;

/// Sites consumed by the fixed SVSTEG header (written sequentially, ahead of the body).
pub const HEADER_SITES: usize = HEADER_LEN * 8;

const _: () = assert!(HEADER_SITES == 432);

/// Sites required to carry a complete frame whose ciphertext is `ct_len` bytes (header + body).
///
/// Saturating throughout: on a 32-bit target a maliciously huge `ct_len` saturates to `usize::MAX`
/// rather than wrapping, so the caller's `required_sites(..) > site_count` check rejects it.
#[must_use]
pub fn required_sites(ct_len: u32) -> usize {
    let body_sites = (ct_len as usize).saturating_mul(8 / BITS_PER_SITE);
    HEADER_SITES.saturating_add(body_sites)
}

/// Maximum **plaintext** bytes embeddable in a carrier exposing `site_count` sites. Accounts for
/// both the header sites and the `secretbox` tag expansion ([`TAG_LEN`]), so the value is expressed
/// in the units the user supplies (plaintext), not ciphertext.
#[must_use]
pub fn max_plaintext_bytes(site_count: usize) -> usize {
    let body_sites = site_count.saturating_sub(HEADER_SITES);
    let body_bytes = body_sites / (8 / BITS_PER_SITE);
    body_bytes.saturating_sub(TAG_LEN)
}

/// The authoritative hide-side guard: can a `plaintext_len`-byte payload be framed into a carrier of
/// `site_count` sites? Checks the **whole** frame (header + tag + body), so it correctly rejects even
/// an empty payload when the cover is too small to hold the header+tag — a case
/// [`max_plaintext_bytes`] alone (which saturates to 0) cannot distinguish. Overflow-safe (u64 math).
#[must_use]
pub fn fits(site_count: usize, plaintext_len: usize) -> bool {
    let ct_len = (plaintext_len as u64).saturating_add(TAG_LEN as u64);
    let body_sites = ct_len.saturating_mul(8 / BITS_PER_SITE as u64);
    let required = (HEADER_SITES as u64).saturating_add(body_sites);
    required <= site_count as u64
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn header_sites_is_one_bit_per_header_bit() {
        assert_eq!(HEADER_SITES, HEADER_LEN * 8);
        assert_eq!(HEADER_SITES, 432);
    }

    #[test]
    fn required_sites_counts_header_plus_body() {
        assert_eq!(required_sites(0), HEADER_SITES);
        assert_eq!(required_sites(10), HEADER_SITES + 80);
    }

    #[test]
    fn required_sites_saturates_on_huge_ct_len() {
        // Never panics / wraps; an absurd declared length is simply un-satisfiable.
        let r = required_sites(u32::MAX);
        assert!(r >= HEADER_SITES);
    }

    #[test]
    fn max_plaintext_accounts_for_header_and_tag() {
        // Too small to even hold the header → zero capacity.
        assert_eq!(max_plaintext_bytes(0), 0);
        assert_eq!(max_plaintext_bytes(HEADER_SITES), 0);
        // Header + room for exactly the tag → still zero plaintext.
        assert_eq!(max_plaintext_bytes(HEADER_SITES + TAG_LEN * 8), 0);
        // Header + tag + one byte of body → one plaintext byte.
        assert_eq!(max_plaintext_bytes(HEADER_SITES + (TAG_LEN + 1) * 8), 1);
    }

    #[test]
    fn fits_rejects_tiny_covers_even_for_empty_payloads() {
        // A cover smaller than header+tag cannot carry even an empty payload, though
        // max_plaintext_bytes saturates to 0 (which alone would wrongly admit a 0-byte payload).
        let tiny = HEADER_SITES + 8 * 10; // 10 body bytes < the 16-byte tag
        assert_eq!(max_plaintext_bytes(tiny), 0);
        assert!(!fits(tiny, 0));
        // A cover with room for the tag + one byte admits exactly one plaintext byte.
        let ok = HEADER_SITES + (TAG_LEN + 1) * 8;
        assert!(fits(ok, 1));
        assert!(!fits(ok, 2));
    }

    #[test]
    fn fits_matches_max_plaintext_at_the_boundary() {
        let site_count = HEADER_SITES + (TAG_LEN + 77) * 8;
        let cap = max_plaintext_bytes(site_count);
        assert_eq!(cap, 77);
        assert!(fits(site_count, cap));
        assert!(!fits(site_count, cap + 1));
    }

    #[test]
    fn capacity_and_required_are_consistent_at_the_boundary() {
        // If a payload of `cap` bytes is the max, then framing it must fit in `site_count` sites.
        let site_count = HEADER_SITES + (TAG_LEN + 50) * 8;
        let cap = max_plaintext_bytes(site_count);
        assert_eq!(cap, 50);
        let ct_len = (cap + TAG_LEN) as u32;
        assert!(required_sites(ct_len) <= site_count);
        // One more plaintext byte would overflow capacity.
        assert!(required_sites(ct_len + 1) > site_count);
    }
}
