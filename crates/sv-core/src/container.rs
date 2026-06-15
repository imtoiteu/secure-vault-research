//! `.svault` container framing, signing, and verification (M5).
//!
//! Implements the byte layout from [`crate::format`]: assemble + sign on write, and
//! verify-then-trust on read. Frozen per
//! [`docs/M5-SCHEMA-DECISIONS.md`](../../../docs/M5-SCHEMA-DECISIONS.md) (H4, H5).
//!
//! Like the key hierarchy, the container is **generic over injected crypto** (`Hasher` +
//! `Signer`) so `sv-core` stays backend-/FFI-free in its production graph; the concrete
//! `Blake3Hasher` / `SodiumMinisignSigner` are wired in by the service layer (M6) and by
//! tests (dev-dependency).
//!
//! ## Authentication model (H5)
//! The signature covers the **binding root** `BLAKE3(header_digest ‖ payload_digest)`, where
//! `header_digest = BLAKE3(MAGIC‖VERSION‖HEADER_LEN‖HEADER)` and `payload_digest =
//! BLAKE3(PAYLOAD)`. Section digests are recomputed on read, never stored — so a header from
//! one file cannot be spliced onto another file's payload. Full authentication needs the
//! payload (single-signature design); [`verify_header`] is a cheap *structural* parse used to
//! read KDF params before unlock, and does **not** by itself authenticate.
//!
//! ## Integrity vs. provenance (H4)
//! [`decode`] without `expected_pubkey` checks the self-signature against the in-header
//! signing key → **integrity / tamper-evidence**, not authorship. Passing a pinned external
//! key additionally requires the in-header key to equal it → **provenance**. The two outcomes
//! are reported distinctly via [`OpenedContainer::provenance_verified`]; a self-signed vault
//! is never reported as authentic-origin.

use std::path::Path;

use serde::de::DeserializeOwned;
use serde::Serialize;
use sv_crypto_traits::{Ed25519PublicKey, Hash32, Hasher, MinisignSignature, SecretBytes, Signer};
use zeroize::Zeroize;

use crate::error::VaultError;
use crate::format::{CipherSuite, ContentLayout, ItemDirectory, ItemEntry, VaultHeader};
use crate::format::{FORMAT_VERSION, MAGIC};

/// Byte offset where the CBOR header begins: `MAGIC(4) + FORMAT_VERSION(2) + HEADER_LEN(4)`.
const HEADER_OFFSET: usize = 10;
/// Reject absurd header sizes before allocation/parse (DoS guard).
pub const MAX_HEADER_LEN: u32 = 1 << 20; // 1 MiB

// ===========================================================================
// Container encode / decode
// ===========================================================================

/// A decoded, signature-verified container.
#[derive(Debug, Clone)]
pub struct OpenedContainer {
    /// The authenticated header (safe to act on — signature verified).
    pub header: VaultHeader,
    /// The encrypted payload blob (one age ciphertext); decryption is the service layer's job.
    pub payload: Vec<u8>,
    /// The signed binding root, for integrity display (`IntegrityReport.computed_hash_hex`).
    pub content_digest: Hash32,
    /// `true` iff verified against a caller-pinned external key (provenance, H4); `false` for
    /// integrity-only (self-signed) verification.
    pub provenance_verified: bool,
}

/// Assemble and sign a `.svault` container into a byte buffer. `payload` is the
/// already-encrypted blob; the header's `content_layout.payload_len` and `format_version`
/// are set from the actual bytes (any caller-supplied values are overwritten for
/// self-consistency). `signing_key` is the unlocked Ed25519 secret key.
pub fn encode<H: Hasher, S: Signer>(
    header: &VaultHeader,
    payload: &[u8],
    hasher: &H,
    signer: &S,
    signing_key: &SecretBytes,
) -> Result<Vec<u8>, VaultError> {
    let mut header = header.clone();
    header.format_version = FORMAT_VERSION;
    header.content_layout = ContentLayout {
        payload_len: payload.len() as u64,
    };

    let header_cbor = to_cbor(&header)?;
    let header_len: u32 = header_cbor
        .len()
        .try_into()
        .map_err(|_| VaultError::InvalidInput("header too large".into()))?;
    if header_len > MAX_HEADER_LEN {
        return Err(VaultError::InvalidInput(
            "header exceeds maximum size".into(),
        ));
    }

    // Prefix = MAGIC ‖ VERSION ‖ HEADER_LEN ‖ HEADER — exactly what header_digest covers.
    let mut out = Vec::with_capacity(HEADER_OFFSET + header_cbor.len() + payload.len());
    out.extend_from_slice(&MAGIC);
    out.extend_from_slice(&FORMAT_VERSION.to_le_bytes());
    out.extend_from_slice(&header_len.to_le_bytes());
    out.extend_from_slice(&header_cbor);

    let header_digest = hasher.hash(&out);
    let payload_digest = hasher.hash(payload);
    let root = binding_root(hasher, &header_digest, &payload_digest);

    let trusted_comment = format!("secure-vault v{FORMAT_VERSION} container");
    let sig = signer.sign(&root.0, signing_key, &trusted_comment)?;

    out.extend_from_slice(payload);
    out.extend_from_slice(&sig.0);
    Ok(out)
}

/// Parse, verify the binding-root signature, and return the authenticated container.
///
/// `expected_pubkey`: `None` → integrity (self-signed) check against the in-header key;
/// `Some(pinned)` → provenance, additionally requiring the in-header key to equal `pinned`.
/// Panic-free on arbitrary input; every malformed/forged case maps to an oracle-safe error.
pub fn decode<H: Hasher, S: Signer>(
    bytes: &[u8],
    hasher: &H,
    signer: &S,
    expected_pubkey: Option<&Ed25519PublicKey>,
) -> Result<OpenedContainer, VaultError> {
    let (header, payload_offset) = parse_framing(bytes)?;

    // Locate the payload using the (not-yet-authenticated) length. A wrong length can only
    // cause a verification failure below, never a bypass — the bytes hashed would differ.
    let payload_len = header.content_layout.payload_len as usize;
    let payload_end = payload_offset
        .checked_add(payload_len)
        .ok_or(VaultError::Corrupted)?;
    if payload_end > bytes.len() {
        return Err(VaultError::Corrupted);
    }
    let payload = &bytes[payload_offset..payload_end];
    let sig_bytes = &bytes[payload_end..];
    if sig_bytes.is_empty() {
        return Err(VaultError::Corrupted);
    }

    // Recompute the binding root over the actual bytes.
    let header_digest = hasher.hash(&bytes[..payload_offset]);
    let payload_digest = hasher.hash(payload);
    let root = binding_root(hasher, &header_digest, &payload_digest);

    // Choose the authenticating key: in-header (integrity) or pinned (provenance).
    let header_key = Ed25519PublicKey(header.signing_public_key);
    let pubkey = match expected_pubkey {
        Some(pinned) => {
            if pinned.0 != header.signing_public_key {
                return Err(VaultError::Corrupted);
            }
            pinned
        }
        None => &header_key,
    };

    let sig = MinisignSignature(sig_bytes.to_vec());
    signer
        .verify(&root.0, &sig, pubkey)
        .map_err(|_| VaultError::Corrupted)?;

    Ok(OpenedContainer {
        header,
        payload: payload.to_vec(),
        content_digest: root,
        provenance_verified: expected_pubkey.is_some(),
    })
}

/// Structural parse of the framing + header **without** verifying the signature. Used to read
/// KDF params before unlock; full authentication is [`decode`]. Panic-free on arbitrary input.
pub fn verify_header(bytes: &[u8]) -> Result<VaultHeader, VaultError> {
    Ok(parse_framing(bytes)?.0)
}

/// Recompute the binding-root digest (`BLAKE3(header_digest ‖ payload_digest)`) **without**
/// verifying the signature — for an `IntegrityReport`'s `computed_hash_hex`, which must be shown
/// even when the signature fails. Returns `Malformed`/`IncompatibleVersion` if the framing
/// itself is unreadable.
pub fn content_digest<H: Hasher>(bytes: &[u8], hasher: &H) -> Result<Hash32, VaultError> {
    let (header, payload_offset) = parse_framing(bytes)?;
    let payload_len = header.content_layout.payload_len as usize;
    let payload_end = payload_offset
        .checked_add(payload_len)
        .ok_or(VaultError::Corrupted)?;
    if payload_end > bytes.len() {
        return Err(VaultError::Corrupted);
    }
    let header_digest = hasher.hash(&bytes[..payload_offset]);
    let payload_digest = hasher.hash(&bytes[payload_offset..payload_end]);
    Ok(binding_root(hasher, &header_digest, &payload_digest))
}

/// Parse magic/version/header and return `(header, payload_offset)`. All bounds checked.
///
/// Failure taxonomy (E1/E2): structural problems (size, magic, truncation, bad CBOR) → a
/// benign `Malformed` ("not a vault"); an unsupported **format version** detected via the raw
/// prefix → the actionable `IncompatibleVersion`. The in-header `suite` mismatch is
/// defense-in-depth → `Corrupted` (honest version skew is caught by the prefix gate first,
/// because any suite change co-bumps FORMAT_VERSION).
fn parse_framing(bytes: &[u8]) -> Result<(VaultHeader, usize), VaultError> {
    if bytes.len() < HEADER_OFFSET {
        return Err(VaultError::Malformed);
    }
    if bytes[..4] != MAGIC {
        return Err(VaultError::Malformed);
    }
    let version = u16::from_le_bytes([bytes[4], bytes[5]]);
    if version != FORMAT_VERSION {
        return Err(VaultError::IncompatibleVersion {
            found: version,
            supported: FORMAT_VERSION,
        });
    }
    let header_len = u32::from_le_bytes([bytes[6], bytes[7], bytes[8], bytes[9]]);
    if header_len > MAX_HEADER_LEN {
        return Err(VaultError::Malformed);
    }
    let header_end = HEADER_OFFSET
        .checked_add(header_len as usize)
        .ok_or(VaultError::Malformed)?;
    if header_end > bytes.len() {
        return Err(VaultError::Malformed);
    }
    let header: VaultHeader = ciborium::from_reader(&bytes[HEADER_OFFSET..header_end])
        .map_err(|_| VaultError::Malformed)?;
    // Cross-check the self-described version + suite against what we wrote.
    if header.format_version != FORMAT_VERSION || header.suite != CipherSuite::CURRENT {
        return Err(VaultError::Corrupted);
    }
    Ok((header, header_end))
}

/// `BLAKE3(header_digest ‖ payload_digest)` — the message the signature covers (H5).
fn binding_root<H: Hasher>(hasher: &H, header_digest: &Hash32, payload_digest: &Hash32) -> Hash32 {
    let mut buf = [0u8; 64];
    buf[..32].copy_from_slice(&header_digest.0);
    buf[32..].copy_from_slice(&payload_digest.0);
    hasher.hash(&buf)
}

// ===========================================================================
// Payload archive (the single-stream plaintext, H3)
// ===========================================================================

/// One item to pack into the payload plaintext.
#[derive(Debug, Clone)]
pub struct ItemPlaintext {
    pub item_id: [u8; 16],
    pub name: String,
    pub added_unix: u64,
    pub data: Vec<u8>,
}

/// The decrypted payload archive: the directory plus a slice-able item-bytes region. The
/// `item_bytes` region is **plaintext**, so it is zeroized on drop (M7 hardening).
#[derive(Debug, Clone)]
pub struct UnpackedArchive {
    pub directory: ItemDirectory,
    pub item_bytes: Vec<u8>,
}

impl Drop for UnpackedArchive {
    fn drop(&mut self) {
        self.item_bytes.zeroize();
    }
}

impl UnpackedArchive {
    /// Borrow one item's plaintext by its directory entry. Bounds-checked.
    pub fn item_data(&self, entry: &ItemEntry) -> Result<&[u8], VaultError> {
        let start = entry.plaintext_offset as usize;
        let end = start
            .checked_add(entry.plaintext_len as usize)
            .ok_or(VaultError::Corrupted)?;
        self.item_bytes.get(start..end).ok_or(VaultError::Corrupted)
    }
}

/// Pack items into the payload **plaintext** archive: `DIR_LEN(u32 LE) ‖ CBOR(ItemDirectory)
/// ‖ item-bytes`. This is the plaintext the service age-encrypts into the container payload,
/// so the directory (names/sizes/count) is hidden in a locked vault (H3). Per-item BLAKE3 is
/// computed with `hasher`. Pure; no encryption here.
pub fn pack_archive<H: Hasher>(items: &[ItemPlaintext], hasher: &H) -> Result<Vec<u8>, VaultError> {
    let mut item_bytes = Vec::new();
    let mut entries = Vec::with_capacity(items.len());
    for it in items {
        let offset = item_bytes.len() as u64;
        entries.push(ItemEntry {
            item_id: it.item_id,
            name: it.name.clone(),
            plaintext_offset: offset,
            plaintext_len: it.data.len() as u64,
            plaintext_blake3: hasher.hash(&it.data).0,
            added_unix: it.added_unix,
        });
        item_bytes.extend_from_slice(&it.data);
    }

    let dir_cbor = to_cbor(&ItemDirectory { items: entries })?;
    let dir_len: u32 = dir_cbor
        .len()
        .try_into()
        .map_err(|_| VaultError::InvalidInput("item directory too large".into()))?;

    let mut out = Vec::with_capacity(4 + dir_cbor.len() + item_bytes.len());
    out.extend_from_slice(&dir_len.to_le_bytes());
    out.extend_from_slice(&dir_cbor);
    out.extend_from_slice(&item_bytes);
    item_bytes.zeroize(); // wipe the plaintext scratch; `out` (the archive) is the caller's to wipe
    Ok(out)
}

/// Inverse of [`pack_archive`]. Panic-free on arbitrary input.
pub fn unpack_archive(blob: &[u8]) -> Result<UnpackedArchive, VaultError> {
    if blob.len() < 4 {
        return Err(VaultError::Corrupted);
    }
    let dir_len = u32::from_le_bytes([blob[0], blob[1], blob[2], blob[3]]) as usize;
    let dir_end = 4usize.checked_add(dir_len).ok_or(VaultError::Corrupted)?;
    if dir_end > blob.len() {
        return Err(VaultError::Corrupted);
    }
    let directory: ItemDirectory = from_cbor(&blob[4..dir_end])?;
    Ok(UnpackedArchive {
        directory,
        item_bytes: blob[dir_end..].to_vec(),
    })
}

// ===========================================================================
// Atomic on-disk write
// ===========================================================================

/// Atomically write `bytes` to `path` via a same-directory temp file + rename, so a crash or
/// concurrent reader never observes a partially-written vault.
pub fn write_atomic(path: &Path, bytes: &[u8]) -> Result<(), VaultError> {
    use std::io::Write as _;
    let dir = path
        .parent()
        .filter(|p| !p.as_os_str().is_empty())
        .ok_or_else(|| VaultError::InvalidInput("path has no parent directory".into()))?;
    let mut tmp =
        tempfile::NamedTempFile::new_in(dir).map_err(|e| VaultError::Io(e.to_string()))?;
    tmp.write_all(bytes)
        .map_err(|e| VaultError::Io(e.to_string()))?;
    tmp.as_file()
        .sync_all()
        .map_err(|e| VaultError::Io(e.to_string()))?;
    tmp.persist(path)
        .map_err(|e| VaultError::Io(e.error.to_string()))?;
    Ok(())
}

// ===========================================================================
// CBOR helpers (errors collapsed to oracle-safe variants)
// ===========================================================================

fn to_cbor<T: Serialize>(value: &T) -> Result<Vec<u8>, VaultError> {
    let mut buf = Vec::new();
    ciborium::into_writer(value, &mut buf)
        .map_err(|e| VaultError::InvalidInput(format!("cbor encode failed: {e}")))?;
    Ok(buf)
}

fn from_cbor<T: DeserializeOwned>(bytes: &[u8]) -> Result<T, VaultError> {
    // Any parse failure (truncation, type mismatch, unknown field) → Corrupted; no detail
    // leaks to the caller.
    ciborium::from_reader(bytes).map_err(|_| VaultError::Corrupted)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::format::sample_header;
    use sv_crypto::{Blake3Hasher, SodiumMinisignSigner};

    /// A signer + a fresh keypair, with the public key planted into a sample header.
    fn signed_setup() -> (SodiumMinisignSigner, SecretBytes, VaultHeader) {
        let signer = SodiumMinisignSigner;
        let (sk, pk) = signer.generate().unwrap();
        let mut header = sample_header();
        header.signing_public_key = pk.0;
        (signer, sk, header)
    }

    #[test]
    fn encode_decode_round_trips_and_authenticates() {
        let (signer, sk, header) = signed_setup();
        let hasher = Blake3Hasher;
        let payload = b"this-is-an-age-ciphertext-blob".to_vec();

        let bytes = encode(&header, &payload, &hasher, &signer, &sk).unwrap();
        assert_eq!(&bytes[..4], b"SVLT");

        let opened = decode(&bytes, &hasher, &signer, None).unwrap();
        assert_eq!(opened.payload, payload);
        assert_eq!(opened.header.signing_public_key, header.signing_public_key);
        assert_eq!(
            opened.header.content_layout.payload_len,
            payload.len() as u64
        );
        assert!(!opened.provenance_verified); // integrity-only without a pinned key
    }

    #[test]
    fn tampered_payload_header_or_signature_are_rejected() {
        let (signer, sk, header) = signed_setup();
        let hasher = Blake3Hasher;
        let payload = b"payload-bytes";
        let bytes = encode(&header, payload, &hasher, &signer, &sk).unwrap();
        // Payload sits in the middle (not the tail — the tail is the variable-length minisign
        // trailer, which tolerates whitespace and has base64 redundancy, so tail flips are
        // unreliable tamper probes). Locate it from HEADER_LEN.
        let header_len = u32::from_le_bytes([bytes[6], bytes[7], bytes[8], bytes[9]]) as usize;
        let payload_offset = HEADER_OFFSET + header_len;
        let payload_end = payload_offset + payload.len();

        // Flip a payload byte (covered by payload_digest → root mismatch).
        let mut bad_payload = bytes.clone();
        bad_payload[payload_offset] ^= 0xff;
        assert!(matches!(
            decode(&bad_payload, &hasher, &signer, None),
            Err(VaultError::Corrupted)
        ));

        // Flip a header byte (covered by header_digest → root mismatch).
        let mut bad_header = bytes.clone();
        bad_header[HEADER_OFFSET + 1] ^= 0xff;
        assert!(decode(&bad_header, &hasher, &signer, None).is_err());

        // Replace the entire signature trailer with garbage of the same length.
        let mut bad_sig = bytes.clone();
        bad_sig[payload_end..].fill(b'!');
        assert!(decode(&bad_sig, &hasher, &signer, None).is_err());

        // Drop the signature trailer entirely → empty signature is rejected.
        assert!(matches!(
            decode(&bytes[..payload_end], &hasher, &signer, None),
            Err(VaultError::Corrupted)
        ));
    }

    #[test]
    fn splice_resistance_header_from_one_payload_from_another() {
        // The binding root ties header_digest to payload_digest, so a valid header cannot be
        // recombined with a different valid payload.
        let (signer, sk, header) = signed_setup();
        let hasher = Blake3Hasher;
        let a = encode(&header, b"payload-A", &hasher, &signer, &sk).unwrap();
        let b = encode(&header, b"a-different-payload-B", &hasher, &signer, &sk).unwrap();

        // Header+sig framing differ only in payload_len/payload/sig; splice A's prefix onto
        // B's payload region by hand → must fail to verify.
        let a_prefix_end = HEADER_OFFSET + u32::from_le_bytes([a[6], a[7], a[8], a[9]]) as usize;
        let mut spliced = a[..a_prefix_end].to_vec();
        let b_prefix_end = HEADER_OFFSET + u32::from_le_bytes([b[6], b[7], b[8], b[9]]) as usize;
        let b_payload_len = {
            // decode B's header to learn its payload length
            decode(&b, &hasher, &signer, None).unwrap().payload.len()
        };
        spliced.extend_from_slice(&b[b_prefix_end..b_prefix_end + b_payload_len]); // B's payload
        spliced.extend_from_slice(&a[a_prefix_end + (b"payload-A".len())..]); // A's signature
        assert!(decode(&spliced, &hasher, &signer, None).is_err());
    }

    #[test]
    fn provenance_mode_requires_matching_pinned_key() {
        let (signer, sk, header) = signed_setup();
        let hasher = Blake3Hasher;
        let bytes = encode(&header, b"p", &hasher, &signer, &sk).unwrap();

        // Correct pinned key → provenance verified.
        let pinned = Ed25519PublicKey(header.signing_public_key);
        let opened = decode(&bytes, &hasher, &signer, Some(&pinned)).unwrap();
        assert!(opened.provenance_verified);

        // A different pinned key → rejected, even though the self-signature is valid.
        let (_, other_pk) = signer.generate().unwrap();
        assert!(matches!(
            decode(&bytes, &hasher, &signer, Some(&other_pk)),
            Err(VaultError::Corrupted)
        ));
    }

    #[test]
    fn malformed_inputs_never_panic() {
        let hasher = Blake3Hasher;
        let signer = SodiumMinisignSigner;
        for bad in [
            &b""[..],
            &b"SV"[..],
            &b"SVLT"[..],
            &b"XXXX\x01\x00\x00\x00\x00\x00"[..], // wrong magic
            &[b'S', b'V', b'L', b'T', 9, 0, 0, 0, 0, 0][..], // unknown version 9
            &[b'S', b'V', b'L', b'T', 1, 0, 0xff, 0xff, 0xff, 0xff][..], // huge header_len
        ] {
            // Must return an error, never panic.
            let _ = decode(bad, &hasher, &signer, None);
            let _ = verify_header(bad);
        }
        // Unknown version is reported as an actionable incompatibility, not corruption (E1).
        let v9 = [b'S', b'V', b'L', b'T', 9, 0, 0, 0, 0, 0];
        assert!(matches!(
            verify_header(&v9),
            Err(VaultError::IncompatibleVersion {
                found: 9,
                supported: 1
            })
        ));
        // A short / wrong-magic buffer is "not a vault", distinct from corruption (E2).
        assert!(matches!(verify_header(b"nope"), Err(VaultError::Malformed)));
    }

    #[test]
    fn decode_is_panic_free_on_truncations_mutations_and_random_input() {
        // Robustness sweep (M7): the parser must never panic on adversarial bytes, and a
        // mutated container must never authenticate as anything but the original payload (a
        // mutation can only survive if it lands in the unsigned minisign comment).
        let (signer, sk, header) = signed_setup();
        let hasher = Blake3Hasher;
        let valid = encode(&header, b"payload-here", &hasher, &signer, &sk).unwrap();

        // 1. Every truncation length.
        for n in 0..=valid.len() {
            let _ = decode(&valid[..n], &hasher, &signer, None);
            let _ = verify_header(&valid[..n]);
            let _ = content_digest(&valid[..n], &hasher);
        }

        // 2. Deterministic single-byte mutations across the whole buffer (xorshift PRNG).
        let mut state: u64 = 0x9E37_79B9_7F4A_7C15;
        let mut next = || {
            state ^= state << 13;
            state ^= state >> 7;
            state ^= state << 17;
            state
        };
        for _ in 0..4000 {
            let mut buf = valid.clone();
            let pos = (next() as usize) % buf.len();
            buf[pos] ^= (next() as u8) | 1; // guaranteed change
            if let Ok(opened) = decode(&buf, &hasher, &signer, None) {
                assert_eq!(opened.payload, b"payload-here");
            }
            let _ = verify_header(&buf);
            let _ = content_digest(&buf, &hasher);
        }

        // 3. Pure-random buffers of assorted lengths.
        for len in [0usize, 1, 4, 9, 10, 11, 32, 64, 256] {
            let mut buf = vec![0u8; len];
            buf.iter_mut().for_each(|b| *b = next() as u8);
            let _ = decode(&buf, &hasher, &signer, None);
            let _ = verify_header(&buf);
            let _ = content_digest(&buf, &hasher);
        }
    }

    #[test]
    fn verify_header_reads_kdf_params_without_authentication() {
        let (signer, sk, header) = signed_setup();
        let hasher = Blake3Hasher;
        let bytes = encode(&header, b"payload", &hasher, &signer, &sk).unwrap();
        let parsed = verify_header(&bytes).unwrap();
        assert_eq!(parsed.kdf.params, header.kdf.params);
        assert_eq!(parsed.suite, CipherSuite::V1);
    }

    #[test]
    fn archive_packs_unpacks_and_records_per_item_hashes() {
        let hasher = Blake3Hasher;
        let items = vec![
            ItemPlaintext {
                item_id: [1; 16],
                name: "a.txt".into(),
                added_unix: 10,
                data: b"hello".to_vec(),
            },
            ItemPlaintext {
                item_id: [2; 16],
                name: "b.bin".into(),
                added_unix: 20,
                data: vec![0u8, 1, 2, 3, 255],
            },
        ];
        let blob = pack_archive(&items, &hasher).unwrap();
        let arch = unpack_archive(&blob).unwrap();

        assert_eq!(arch.directory.items.len(), 2);
        for (entry, original) in arch.directory.items.iter().zip(&items) {
            assert_eq!(entry.name, original.name);
            assert_eq!(arch.item_data(entry).unwrap(), original.data.as_slice());
            assert_eq!(entry.plaintext_blake3, hasher.hash(&original.data).0);
        }
    }

    #[test]
    fn unpack_rejects_truncated_archive() {
        assert!(matches!(
            unpack_archive(b"\xff"),
            Err(VaultError::Corrupted)
        ));
        // dir_len claims more bytes than present.
        assert!(matches!(
            unpack_archive(&[0xff, 0xff, 0xff, 0x7f]),
            Err(VaultError::Corrupted)
        ));
    }

    #[test]
    fn write_atomic_then_read_round_trips() {
        let (signer, sk, header) = signed_setup();
        let hasher = Blake3Hasher;
        let bytes = encode(&header, b"payload", &hasher, &signer, &sk).unwrap();

        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("test.svault");
        write_atomic(&path, &bytes).unwrap();

        let read_back = std::fs::read(&path).unwrap();
        let opened = decode(&read_back, &hasher, &signer, None).unwrap();
        assert_eq!(opened.payload, b"payload");
    }
}
