//! On-disk `.svault` container **schema** (finalized in M5).
//!
//! The framing/sign/verify *logic* lives in [`crate::container`]; this module defines the
//! byte-layout constants and the CBOR types. Frozen per
//! [`docs/M5-SCHEMA-DECISIONS.md`](../../../docs/M5-SCHEMA-DECISIONS.md) (H1, H3, H5, H6, V1).
//!
//! ## File layout
//! ```text
//! ┌────────┬───────────────┬────────────┬──────────────────┬─────────┬──────────────┐
//! │ MAGIC  │ FORMAT_VERSION│ HEADER_LEN │ HEADER (CBOR)     │ PAYLOAD │ SIG_TRAILER   │
//! │ 4 byte │ u16 LE        │ u32 LE     │ HEADER_LEN bytes  │ …       │ minisign fmt  │
//! └────────┴───────────────┴────────────┴──────────────────┴─────────┴──────────────┘
//! ```
//! Integrity + provenance (H5): the signature covers the **binding root**
//! `BLAKE3(BLAKE3(MAGIC‖VERSION‖HEADER_LEN‖HEADER) ‖ BLAKE3(PAYLOAD))`. Section digests are
//! recomputed on read (not stored), so the trailer holds only the signature, and a header
//! from one file cannot be spliced onto another file's payload.
//!
//! ## Confidentiality of metadata (H3)
//! The header carries **no item directory**. The payload is a *single* age ciphertext whose
//! plaintext is `DIR_LEN ‖ CBOR(ItemDirectory) ‖ item-bytes` (see [`crate::container`]). A
//! locked vault therefore leaks neither item names, sizes, nor count — only the total
//! ciphertext length. The header contains only *wrapped* secrets, never plaintext keys.

use serde::{Deserialize, Serialize};
use sv_crypto_traits::{
    AeadAlg, AgeRecipient, FileCipherAlg, HashAlg, KdfAlg, KdfParams, Salt, SigAlg,
};

/// Container magic bytes.
pub const MAGIC: [u8; 4] = *b"SVLT";
/// Current on-disk **structure** version (V1 axis). Independent of [`CipherSuite`] (the
/// crypto axis) and of `sv_types::CONTRACT_VERSION` (the IPC axis). Readers accept only
/// versions in their known set — there is no forward-compatible minor parsing.
pub const FORMAT_VERSION: u16 = 1;

/// Crypto-suite identifier (H1/V1). A **closed** enum: the header stores this single
/// discriminant, never independently-selectable algorithm slots, so invalid combinations
/// are unrepresentable and there is no per-field algorithm negotiation to downgrade.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum CipherSuite {
    /// Argon2id · BLAKE3 · secretbox (XSalsa20-Poly1305) · age v1 · Ed25519-minisign.
    V1,
}

impl CipherSuite {
    /// The suite this build writes.
    pub const CURRENT: CipherSuite = CipherSuite::V1;

    /// Compile-time expansion to the concrete algorithm ids. The suite is the **single
    /// authority** for algorithm identity (per-record algorithm tags are intentionally
    /// absent — see H2).
    #[must_use]
    pub const fn spec(self) -> SuiteSpec {
        match self {
            CipherSuite::V1 => SuiteSpec {
                kdf: KdfAlg::Argon2id,
                hash: HashAlg::Blake3,
                wrap_aead: AeadAlg::XSalsa20Poly1305,
                file_cipher: FileCipherAlg::AgeV1,
                sig: SigAlg::Ed25519Minisign,
            },
        }
    }
}

/// The algorithms a [`CipherSuite`] expands to. Self-describing, but derived from the suite
/// rather than stored field-by-field.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct SuiteSpec {
    pub kdf: KdfAlg,
    pub hash: HashAlg,
    pub wrap_aead: AeadAlg,
    pub file_cipher: FileCipherAlg,
    pub sig: SigAlg,
}

/// Authenticated CBOR header. **No plaintext secrets, no item directory** — key material is
/// stored wrapped; the item directory lives encrypted inside the payload (H3).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct VaultHeader {
    /// Mirrors the on-disk `FORMAT_VERSION` for self-description (cross-checked on read).
    pub format_version: u16,
    /// Crypto suite (H1). Cross-checked against [`CipherSuite::CURRENT`] on read.
    pub suite: CipherSuite,
    /// 16-byte vault UUID (rendered hyphenated in DTOs); binds the wrap-key derivation (H2).
    pub vault_uuid: [u8; 16],
    pub created_unix: u64,
    pub modified_unix: u64,
    /// KDF descriptor used to derive the master key from the passphrase.
    pub kdf: KdfRecord,
    /// age X25519 identity, wrapped under its per-field, vault-bound key (libsodium secretbox).
    pub wrapped_age_identity: WrappedSecret,
    /// age recipient (public `age1…`) for the wrapped identity. Non-secret; needed to
    /// re-encrypt the single-stream payload on every item change (added during M6 integration).
    pub age_recipient: AgeRecipient,
    /// Ed25519 signing key, wrapped under its per-field, vault-bound key.
    pub wrapped_signing_key: WrappedSecret,
    /// Public half of the signing key (non-secret), for verification without unlock.
    pub signing_public_key: [u8; 32],
    /// Recovery policy if key-splitting is configured (metadata only; shares live elsewhere).
    pub share_policy: Option<SharePolicyRecord>,
    /// Length of the single encrypted payload blob (its offset is derived from `HEADER_LEN`).
    pub content_layout: ContentLayout,
}

/// KDF parameters as stored in the header. The algorithm is carried by the [`KdfParams`] tag
/// (H6 — the redundant free-form `algorithm` string was removed) and cross-checked against
/// the suite.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct KdfRecord {
    pub salt: Salt,
    pub params: KdfParams,
}

/// A libsodium-secretbox-wrapped secret (nonce ‖ ciphertext+MAC). Non-secret as a whole.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct WrappedSecret {
    pub nonce: Vec<u8>,
    pub ciphertext: Vec<u8>,
}

/// Shamir recovery policy as stored in the header.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SharePolicyRecord {
    pub shares_total: u8,
    pub threshold: u8,
}

/// Location of the single encrypted payload blob. Only the length is stored; the offset is
/// derived as `MAGIC(4) + FORMAT_VERSION(2) + HEADER_LEN(4) + HEADER_LEN` — storing the
/// offset would be circular (it depends on the header's own serialized size).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ContentLayout {
    pub payload_len: u64,
}

/// One stored item, recorded in the **encrypted** [`ItemDirectory`] (not the header). Offsets
/// are *plaintext* positions within the decrypted item-bytes region (H3).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ItemEntry {
    pub item_id: [u8; 16],
    pub name: String,
    pub plaintext_offset: u64,
    pub plaintext_len: u64,
    pub plaintext_blake3: [u8; 32],
    pub added_unix: u64,
}

/// The vault's item directory. Lives **inside** the encrypted payload (H3), so a locked vault
/// reveals no item metadata. Serialized ahead of the concatenated item bytes by
/// [`crate::container::pack_archive`].
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ItemDirectory {
    pub items: Vec<ItemEntry>,
}

/// Test-only sample header, shared with [`crate::container`]'s tests.
#[cfg(test)]
pub(crate) fn sample_header() -> VaultHeader {
    VaultHeader {
        format_version: FORMAT_VERSION,
        suite: CipherSuite::V1,
        vault_uuid: [0x11; 16],
        created_unix: 1_700_000_000,
        modified_unix: 1_700_000_001,
        kdf: KdfRecord {
            salt: Salt([7; 16]),
            params: KdfParams::default(),
        },
        wrapped_age_identity: WrappedSecret {
            nonce: vec![1; 24],
            ciphertext: vec![2; 48],
        },
        age_recipient: AgeRecipient("age1samplerecipient000000000000000000000000000000000".into()),
        wrapped_signing_key: WrappedSecret {
            nonce: vec![3; 24],
            ciphertext: vec![4; 80],
        },
        signing_public_key: [9; 32],
        share_policy: Some(SharePolicyRecord {
            shares_total: 5,
            threshold: 3,
        }),
        content_layout: ContentLayout { payload_len: 64 },
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn magic_and_version_are_frozen() {
        assert_eq!(&MAGIC, b"SVLT");
        assert_eq!(FORMAT_VERSION, 1);
    }

    #[test]
    fn suite_expands_to_the_phase1_algorithms() {
        let s = CipherSuite::CURRENT.spec();
        assert_eq!(s.kdf, KdfAlg::Argon2id);
        assert_eq!(s.hash, HashAlg::Blake3);
        assert_eq!(s.wrap_aead, AeadAlg::XSalsa20Poly1305);
        assert_eq!(s.file_cipher, FileCipherAlg::AgeV1);
        assert_eq!(s.sig, SigAlg::Ed25519Minisign);
    }

    #[test]
    fn header_round_trips_through_cbor() {
        let h = sample_header();
        let mut buf = Vec::new();
        ciborium::into_writer(&h, &mut buf).expect("serialize header");
        let back: VaultHeader = ciborium::from_reader(buf.as_slice()).expect("deserialize header");
        assert_eq!(h, back);
    }

    #[test]
    fn item_directory_round_trips_through_cbor() {
        let dir = ItemDirectory {
            items: vec![ItemEntry {
                item_id: [0xab; 16],
                name: "secret.txt".into(),
                plaintext_offset: 0,
                plaintext_len: 42,
                plaintext_blake3: [0xcd; 32],
                added_unix: 1_700_000_002,
            }],
        };
        let mut buf = Vec::new();
        ciborium::into_writer(&dir, &mut buf).expect("serialize directory");
        let back: ItemDirectory =
            ciborium::from_reader(buf.as_slice()).expect("deserialize directory");
        assert_eq!(dir, back);
    }

    #[test]
    fn header_rejects_unknown_fields() {
        // deny_unknown_fields (H6): a CBOR map with an extra key must fail to deserialize.
        // (Defense-in-depth atop the signature.)
        let mut m = std::collections::BTreeMap::new();
        m.insert(
            "format_version".to_string(),
            ciborium::Value::Integer(1.into()),
        );
        m.insert("unexpected".to_string(), ciborium::Value::Bool(true));
        let mut buf = Vec::new();
        ciborium::into_writer(&m, &mut buf).unwrap();
        let r: Result<VaultHeader, _> = ciborium::from_reader(buf.as_slice());
        assert!(r.is_err());
    }
}
