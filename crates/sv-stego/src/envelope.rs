//! The **SVSTEG envelope** — the framed bytes embedded into carrier sites.
//!
//! Fixed-layout header ([`HEADER_LEN`] bytes) + variable ciphertext. All multi-byte integers are
//! big-endian. The header is written **sequentially** into the first [`crate::capacity::HEADER_SITES`]
//! sites so it is recoverable *before* the body placement schedule (which the `salt` seeds) is known.
//!
//! | Field | Off | Len | Meaning |
//! |---|---|---|---|
//! | `magic`   | 0  | 6  | ASCII `"SVSTEG"` |
//! | `version` | 6  | 1  | [`VERSION`] (`0x01`) |
//! | `flags`   | 7  | 1  | bit0 carrier (0=spatial); bit1 selector (0=seq,1=perm); bit2 bit-plane>0 (reserved 0); rest reserved 0 |
//! | `kdf_alg` | 8  | 1  | [`KDF_ALG_ARGON2ID`] (`0x01`) |
//! | `aead_alg`| 9  | 1  | [`AEAD_ALG_SECRETBOX`] (`0x01`) |
//! | `salt`    | 10 | 16 | **public** per-image random — Argon2id salt **and** permutation-seed source |
//! | `nonce`   | 26 | 24 | `secretbox` nonce |
//! | `ct_len`  | 50 | 4  | u32 length of `ciphertext` (incl. the 16-byte tag) |
//!
//! `salt`/`nonce` are **public framing, not secrets**: confidentiality is the AEAD over
//! `key = Argon2id(passphrase, salt)` (see [`crate::seal`]). Placement is **not** a security boundary.

use sv_crypto_traits::{Salt, SALT_LEN};

use crate::carrier::CarrierKind;
use crate::error::StegoError;
use crate::seal::NONCE_LEN;
use crate::selector::SelectorKind;

/// Envelope magic.
pub const MAGIC: [u8; 6] = *b"SVSTEG";
/// Envelope format version this build writes and accepts.
pub const VERSION: u8 = 1;
/// `kdf_alg` value for Argon2id (the only KDF).
pub const KDF_ALG_ARGON2ID: u8 = 1;
/// `aead_alg` value for XSalsa20-Poly1305 `secretbox` (the only AEAD).
pub const AEAD_ALG_SECRETBOX: u8 = 1;

// ---- flags bits ------------------------------------------------------------
/// bit0 — carrier is JPEG DCT (Phase 4); clear ⇒ spatial PNG/BMP LSB.
const FLAG_CARRIER_JPEG: u8 = 0b0000_0001;
/// bit1 — body placement is a seeded permutation (clear ⇒ sequential).
const FLAG_SELECTOR_PERMUTED: u8 = 0b0000_0010;
/// bit2 — bit-plane > 0 (Phase 4+). Reserved (must be clear) in Phase 1.
const FLAG_BITPLANE_HIGH: u8 = 0b0000_0100;
/// Bits with no defined meaning yet; any of them set ⇒ a frame this build cannot honour.
const FLAGS_RESERVED_MASK: u8 = !(FLAG_CARRIER_JPEG | FLAG_SELECTOR_PERMUTED | FLAG_BITPLANE_HIGH);

// ---- field offsets (single source of truth, asserted contiguous) -----------
const O_MAGIC: usize = 0;
const O_VERSION: usize = 6;
const O_FLAGS: usize = 7;
const O_KDF: usize = 8;
const O_AEAD: usize = 9;
const O_SALT: usize = 10;
const O_NONCE: usize = O_SALT + SALT_LEN; // 26
const O_CTLEN: usize = O_NONCE + NONCE_LEN; // 50
/// Total fixed header length: 6 + 1 + 1 + 1 + 1 + 16 + 24 + 4 = 54.
pub const HEADER_LEN: usize = O_CTLEN + 4;

const _: () = assert!(O_MAGIC + 6 == O_VERSION);
const _: () = assert!(O_VERSION + 1 == O_FLAGS);
const _: () = assert!(O_FLAGS + 1 == O_KDF);
const _: () = assert!(O_KDF + 1 == O_AEAD);
const _: () = assert!(O_AEAD + 1 == O_SALT);
const _: () = assert!(O_SALT + SALT_LEN == O_NONCE);
const _: () = assert!(O_NONCE + NONCE_LEN == O_CTLEN);
const _: () = assert!(HEADER_LEN == 54);

/// A parsed, structurally-valid SVSTEG header. All fields are **non-secret** framing.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ParsedHeader {
    /// Carrier family (decoded from the carrier flag) — also implied by the stego file's format.
    pub carrier: CarrierKind,
    /// Body placement order (decoded from the selector flag).
    pub selector: SelectorKind,
    /// Argon2id salt and permutation-seed source.
    pub salt: Salt,
    /// `secretbox` nonce.
    pub nonce: [u8; NONCE_LEN],
    /// Declared ciphertext length (incl. tag), in bytes. **Not yet validated against capacity** —
    /// the caller must check it before allocating ([`crate::capacity::required_sites`]).
    pub ct_len: u32,
}

/// Serialize a header. `ct_len` must equal the length of the ciphertext that follows.
#[must_use]
pub fn build_header(
    carrier: CarrierKind,
    selector: SelectorKind,
    salt: &Salt,
    nonce: &[u8; NONCE_LEN],
    ct_len: u32,
) -> [u8; HEADER_LEN] {
    let mut out = [0u8; HEADER_LEN];
    out[O_MAGIC..O_VERSION].copy_from_slice(&MAGIC);
    out[O_VERSION] = VERSION;
    let mut flags = 0u8;
    if carrier == CarrierKind::Jpeg {
        flags |= FLAG_CARRIER_JPEG;
    }
    if selector == SelectorKind::Permuted {
        flags |= FLAG_SELECTOR_PERMUTED;
    }
    out[O_FLAGS] = flags;
    out[O_KDF] = KDF_ALG_ARGON2ID;
    out[O_AEAD] = AEAD_ALG_SECRETBOX;
    out[O_SALT..O_NONCE].copy_from_slice(&salt.0);
    out[O_NONCE..O_CTLEN].copy_from_slice(nonce);
    out[O_CTLEN..HEADER_LEN].copy_from_slice(&ct_len.to_be_bytes());
    out
}

/// Parse + structurally validate a header.
///
/// Error discipline (oracle-safety): a wrong/absent magic or an unhonourable flag/algorithm is a
/// "no payload for you" signal and collapses to [`StegoError::NoPayload`]/[`StegoError::BadFrame`]
/// (both → `SV-UNAUTHORIZED`). A correct magic with an unknown **version** is non-secret framing and
/// surfaces distinctly as [`StegoError::UnsupportedVersion`].
pub fn parse_header(bytes: &[u8]) -> Result<ParsedHeader, StegoError> {
    if bytes.len() != HEADER_LEN {
        return Err(StegoError::BadFrame);
    }
    if bytes[O_MAGIC..O_VERSION] != MAGIC {
        // No SVSTEG frame here → oracle-safe "no payload".
        return Err(StegoError::NoPayload);
    }
    if bytes[O_VERSION] != VERSION {
        // A genuine frame of another version — non-secret, actionable.
        return Err(StegoError::UnsupportedVersion {
            found: u16::from(bytes[O_VERSION]),
            supported: u16::from(VERSION),
        });
    }
    let flags = bytes[O_FLAGS];
    // Honoured carrier flags: spatial (clear) or JPEG (bit0). The high bit-plane bit and any
    // reserved bit denote a frame this build cannot interpret.
    if flags & FLAG_BITPLANE_HIGH != 0 || flags & FLAGS_RESERVED_MASK != 0 {
        return Err(StegoError::BadFrame);
    }
    if bytes[O_KDF] != KDF_ALG_ARGON2ID || bytes[O_AEAD] != AEAD_ALG_SECRETBOX {
        return Err(StegoError::BadFrame);
    }
    let carrier = if flags & FLAG_CARRIER_JPEG != 0 {
        CarrierKind::Jpeg
    } else {
        CarrierKind::Spatial
    };
    let selector = if flags & FLAG_SELECTOR_PERMUTED != 0 {
        SelectorKind::Permuted
    } else {
        SelectorKind::Sequential
    };
    let mut salt = [0u8; SALT_LEN];
    salt.copy_from_slice(&bytes[O_SALT..O_NONCE]);
    let mut nonce = [0u8; NONCE_LEN];
    nonce.copy_from_slice(&bytes[O_NONCE..O_CTLEN]);
    let ct_len = u32::from_be_bytes(
        bytes[O_CTLEN..HEADER_LEN]
            .try_into()
            .expect("checked length"),
    );
    Ok(ParsedHeader {
        carrier,
        selector,
        salt: Salt(salt),
        nonce,
        ct_len,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn sample(selector: SelectorKind) -> ([u8; HEADER_LEN], Salt, [u8; NONCE_LEN]) {
        let salt = Salt([0xABu8; SALT_LEN]);
        let nonce = [0xCDu8; NONCE_LEN];
        (
            build_header(CarrierKind::Spatial, selector, &salt, &nonce, 1234),
            salt,
            nonce,
        )
    }

    #[test]
    fn build_parse_roundtrips_both_selectors() {
        for sel in [SelectorKind::Sequential, SelectorKind::Permuted] {
            let (hdr, salt, nonce) = sample(sel);
            let p = parse_header(&hdr).unwrap();
            assert_eq!(p.carrier, CarrierKind::Spatial);
            assert_eq!(p.selector, sel);
            assert_eq!(p.salt, salt);
            assert_eq!(p.nonce, nonce);
            assert_eq!(p.ct_len, 1234);
        }
    }

    #[test]
    fn carrier_flag_roundtrips_for_both_families() {
        let salt = Salt([0x11u8; SALT_LEN]);
        let nonce = [0x22u8; NONCE_LEN];
        for (carrier, selector) in [
            (CarrierKind::Spatial, SelectorKind::Sequential),
            (CarrierKind::Jpeg, SelectorKind::Permuted),
            (CarrierKind::Jpeg, SelectorKind::Sequential),
        ] {
            let hdr = build_header(carrier, selector, &salt, &nonce, 99);
            let p = parse_header(&hdr).unwrap();
            assert_eq!(p.carrier, carrier);
            assert_eq!(p.selector, selector);
        }
    }

    #[test]
    fn wrong_length_is_badframe() {
        let (hdr, _, _) = sample(SelectorKind::Sequential);
        assert!(matches!(
            parse_header(&hdr[..HEADER_LEN - 1]),
            Err(StegoError::BadFrame)
        ));
        let mut longer = hdr.to_vec();
        longer.push(0);
        assert!(matches!(parse_header(&longer), Err(StegoError::BadFrame)));
    }

    #[test]
    fn bad_magic_is_nopayload() {
        let (mut hdr, _, _) = sample(SelectorKind::Sequential);
        hdr[0] = b'X';
        assert!(matches!(parse_header(&hdr), Err(StegoError::NoPayload)));
    }

    #[test]
    fn bad_version_is_unsupportedversion() {
        let (mut hdr, _, _) = sample(SelectorKind::Sequential);
        hdr[O_VERSION] = 9;
        assert!(matches!(
            parse_header(&hdr),
            Err(StegoError::UnsupportedVersion {
                found: 9,
                supported: 1
            })
        ));
    }

    #[test]
    fn unhonourable_flags_and_algs_are_badframe() {
        // The JPEG carrier bit IS honoured now (Phase 4) — it parses, it does not error.
        let (mut jpeg, _, _) = sample(SelectorKind::Sequential);
        jpeg[O_FLAGS] |= FLAG_CARRIER_JPEG;
        assert_eq!(parse_header(&jpeg).unwrap().carrier, CarrierKind::Jpeg);
        // The reserved high bit-plane flag is still not interpretable.
        let (mut bitplane, _, _) = sample(SelectorKind::Sequential);
        bitplane[O_FLAGS] |= FLAG_BITPLANE_HIGH;
        assert!(matches!(parse_header(&bitplane), Err(StegoError::BadFrame)));
        // Reserved high bit set.
        let (mut reserved, _, _) = sample(SelectorKind::Sequential);
        reserved[O_FLAGS] |= 0b1000_0000;
        assert!(matches!(parse_header(&reserved), Err(StegoError::BadFrame)));
        // Unknown KDF / AEAD ids.
        let (mut kdf, _, _) = sample(SelectorKind::Sequential);
        kdf[O_KDF] = 2;
        assert!(matches!(parse_header(&kdf), Err(StegoError::BadFrame)));
        let (mut aead, _, _) = sample(SelectorKind::Sequential);
        aead[O_AEAD] = 2;
        assert!(matches!(parse_header(&aead), Err(StegoError::BadFrame)));
    }
}
