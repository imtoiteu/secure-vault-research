//! `VaultBackend` — the concrete [`sv_core::VaultService`] (M6).
//!
//! Composes the frozen pieces: `StdKeyHierarchy` (M4), `secretbox` wrap/unwrap (M2), the
//! `.svault` `container` (M5), `SodiumMinisignSigner` (M2), `SssSharer` (M2), and an injected
//! [`PayloadCipher`] (age, M3). Lives in the composition root so `sv-core` stays backend-free.
//!
//! Session model (M6 / pre-M6 freeze): an opaque random `session_id` maps to a `SessionState`
//! holding **only the zeroizing master key** plus the vault path. The unwrapped age identity /
//! signing key are materialized **transiently per operation** and dropped (zeroizing). No
//! secret crosses the IPC boundary; the UI only ever holds the opaque handle.

use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::sync::{Arc, Mutex};
use std::time::{SystemTime, UNIX_EPOCH};

use sv_core::container::{self, ItemPlaintext, OpenedContainer, UnpackedArchive};
use sv_core::format::{
    CipherSuite, ContentLayout, ItemEntry, KdfRecord, SharePolicyRecord, VaultHeader, WrappedSecret,
};
use sv_core::keys::{StdKeyHierarchy, WrapField};
use sv_core::{KeyHierarchy, VaultError, VaultService, FORMAT_VERSION};
use sv_crypto::{secretbox, Argon2Kdf, Blake3Hasher, SodiumMinisignSigner, SssSharer};
use sv_crypto_traits::{
    AgeIdentity, CryptoError, Ed25519PublicKey, Hasher, KdfParams, Key32, KeyShare,
    MinisignSignature, Salt, SecretBytes, SecretSharer, Signer, KEYSHARE_LEN,
};
// Single source of truth for the whole-file read ceiling, shared with the crypto-services layer so
// the two can never drift (audit M-2).
use sv_platform::MAX_PLAINTEXT_BYTES;
use sv_types::{
    IntegrityReport, ItemInfo, KdfDescriptor, SessionHandle, ShareExportInfo, SharePolicy,
    VaultMeta,
};
use zeroize::Zeroize;

use crate::payload::PayloadCipher;

// ---- pre-unlock KDF-parameter ceiling (DoS guard) -------------------------
// The header is attacker-influenceable before authentication, so cap the Argon2 work a
// hostile vault can request before we run it. Generous upper bounds — far above any honest
// configuration (cf. the recommended 256 MiB / t=3 / p=1).
const MAX_KDF_MEM_KIB: u32 = 4 * 1024 * 1024; // 4 GiB
const MAX_KDF_TIME_COST: u32 = 64;
const MAX_KDF_PARALLELISM: u32 = 64;

// ---- in-memory size ceiling (OOM guard, validation H1) --------------------
// The payload pipeline is fully in-memory and the `age` subprocess buffers the whole input and
// output (measured peak ≈ 2.7× the item size). Until the pipeline streams, refuse a single item
// past this ceiling with a clear `TooLarge` error rather than risking an out-of-memory crash and
// an opaque `SV-INTERNAL`. Conservative, single-point-of-truth constant — raise it once the
// encrypt/decrypt path streams instead of buffering.
const MAX_ITEM_BYTES: u64 = 2 * 1024 * 1024 * 1024; // 2 GiB

// ---- recovery share envelope ----------------------------------------------
const SHARE_MAGIC: [u8; 4] = *b"SVSH";
const SHARE_ENVELOPE_VERSION: u16 = 1;
// magic(4) + version(2) + uuid(16) + index(1) + total(1) + threshold(1) + share(33)
const SHARE_ENVELOPE_LEN: usize = 4 + 2 + 16 + 1 + 1 + 1 + KEYSHARE_LEN;

/// In-memory session secret. `Key32` zeroizes on drop, so removing the entry wipes the MK.
#[derive(Debug)]
struct SessionState {
    master_key: Key32,
    vault_path: PathBuf,
}

/// The concrete vault service. Generic over the payload cipher so the lifecycle is testable
/// without the `age` toolchain.
#[derive(Debug)]
pub struct VaultBackend<P: PayloadCipher> {
    payload: P,
    hierarchy: StdKeyHierarchy<Argon2Kdf, Blake3Hasher>,
    hasher: Blake3Hasher,
    signer: SodiumMinisignSigner,
    sharer: SssSharer,
    sessions: Mutex<HashMap<String, SessionState>>,
    /// Per-vault write serialization (validation H7). A mutating op (`create`/`add_item`/
    /// `change_passphrase`) is a read-modify-write of the whole container; without this, two
    /// concurrent writers (Tauri dispatches commands on a thread pool) lose an update. The map
    /// holds one lock per vault path so different vaults still proceed in parallel.
    write_locks: Mutex<HashMap<PathBuf, Arc<Mutex<()>>>>,
}

impl<P: PayloadCipher> VaultBackend<P> {
    /// Wire the backend with a payload cipher; all other adapters are fixed Phase-1 choices.
    #[must_use]
    pub fn new(payload: P) -> Self {
        Self {
            payload,
            hierarchy: StdKeyHierarchy::new(Argon2Kdf, Blake3Hasher),
            hasher: Blake3Hasher,
            signer: SodiumMinisignSigner,
            sharer: SssSharer,
            sessions: Mutex::new(HashMap::new()),
            write_locks: Mutex::new(HashMap::new()),
        }
    }

    /// Acquire the per-vault write lock for `path`, returning a guard owner. Held across the
    /// entire read-modify-write of a mutating op so concurrent writers can't lose an update
    /// (H7). Keyed by the canonicalized parent dir + file name so trivial path spellings of the
    /// same vault share one lock; the file itself need not exist yet (create).
    fn vault_write_lock(&self, path: &Path) -> Result<Arc<Mutex<()>>, VaultError> {
        let key = match (path.parent(), path.file_name()) {
            (Some(parent), Some(name)) => parent
                .canonicalize()
                .map(|c| c.join(name))
                .unwrap_or_else(|_| path.to_path_buf()),
            _ => path.to_path_buf(),
        };
        let mut map = self.write_locks.lock().map_err(|_| VaultError::Internal)?;
        Ok(map.entry(key).or_default().clone())
    }

    // ---- session helpers --------------------------------------------------

    fn new_session(
        &self,
        master_key: Key32,
        vault_path: PathBuf,
    ) -> Result<SessionHandle, VaultError> {
        let session_id = hex::encode(random_array::<32>()?);
        let mut map = self.sessions.lock().map_err(|_| VaultError::Internal)?;
        map.insert(
            session_id.clone(),
            SessionState {
                master_key,
                vault_path,
            },
        );
        Ok(SessionHandle { session_id })
    }

    /// Clone out the session's MK + path (the MK clone is itself zeroizing), so we don't hold
    /// the session lock across crypto/file I/O.
    fn session_mk_path(&self, session: &SessionHandle) -> Result<(Key32, PathBuf), VaultError> {
        let map = self.sessions.lock().map_err(|_| VaultError::Internal)?;
        let st = map.get(&session.session_id).ok_or(VaultError::NotFound)?;
        Ok((st.master_key.clone(), st.vault_path.clone()))
    }

    // ---- container + secret helpers --------------------------------------

    /// Read + authenticate (binding-root signature) the container at `path`.
    fn read_container(&self, path: &Path) -> Result<(Vec<u8>, OpenedContainer), VaultError> {
        let bytes = read_file(path)?;
        let opened = container::decode(&bytes, &self.hasher, &self.signer, None)?;
        Ok((bytes, opened))
    }

    fn wrap_secret(
        &self,
        mk: &Key32,
        field: WrapField,
        uuid: &[u8; 16],
        secret: &[u8],
    ) -> WrappedSecret {
        let wk = self.hierarchy.derive_wrap_key(mk, field, uuid);
        let w = secretbox::seal(wk.expose_secret(), secret);
        WrappedSecret {
            nonce: w.nonce.to_vec(),
            ciphertext: w.ciphertext,
        }
    }

    /// Unwrap a stored secret. A failure is mapped to `AuthFailed`: the **first** unwrap (the
    /// age identity) is the post-signature credential gate, so a wrong passphrase/share surfaces
    /// here; later unwraps (signing key) only run once the MK is already proven correct.
    fn unwrap_secret(
        &self,
        mk: &Key32,
        field: WrapField,
        uuid: &[u8; 16],
        wrapped: &WrappedSecret,
    ) -> Result<SecretBytes, VaultError> {
        let nonce: [u8; 24] = wrapped
            .nonce
            .as_slice()
            .try_into()
            .map_err(|_| VaultError::Corrupted)?;
        let wk = self.hierarchy.derive_wrap_key(mk, field, uuid);
        let w = secretbox::Wrapped {
            nonce,
            ciphertext: wrapped.ciphertext.clone(),
        };
        let plaintext =
            secretbox::open(wk.expose_secret(), &w).map_err(|_| VaultError::AuthFailed)?;
        Ok(SecretBytes::new(plaintext))
    }

    /// Unwrap the age identity, decrypt the payload, and unpack the directory + item bytes.
    fn decrypt_archive(
        &self,
        mk: &Key32,
        header: &VaultHeader,
        payload: &[u8],
    ) -> Result<UnpackedArchive, VaultError> {
        let identity_bytes = self.unwrap_secret(
            mk,
            WrapField::AgeIdentity,
            &header.vault_uuid,
            &header.wrapped_age_identity,
        )?;
        let identity = AgeIdentity::new(identity_bytes);
        let mut plaintext = self.payload.decrypt(payload, &identity)?;
        let archive = container::unpack_archive(&plaintext);
        plaintext.zeroize();
        archive
    }

    /// Re-pack `items`, encrypt to `header.age_recipient`, re-sign with the (unwrapped) signing
    /// key, and atomically rewrite `path`. Used by create / add / (rewrite) flows.
    fn write_vault(
        &self,
        mk: &Key32,
        header: &mut VaultHeader,
        items: &[ItemPlaintext],
        path: &Path,
    ) -> Result<(), VaultError> {
        let mut archive = container::pack_archive(items, &self.hasher)?;
        let payload = self.payload.encrypt(&archive, &header.age_recipient)?;
        archive.zeroize();
        let signing_sk = self.unwrap_secret(
            mk,
            WrapField::SigningKey,
            &header.vault_uuid,
            &header.wrapped_signing_key,
        )?;
        header.modified_unix = now_unix();
        let bytes = container::encode(header, &payload, &self.hasher, &self.signer, &signing_sk)?;
        container::write_atomic(path, &bytes)
    }

    fn meta(&self, header: &VaultHeader, item_count: u32) -> VaultMeta {
        let KdfParams::Argon2id(p) = header.kdf.params;
        VaultMeta {
            vault_uuid: hyphenated(&header.vault_uuid),
            format_version: header.format_version,
            created_unix: header.created_unix,
            modified_unix: header.modified_unix,
            item_count,
            share_policy: header.share_policy.map(|s| SharePolicy {
                shares_total: s.shares_total,
                threshold: s.threshold,
            }),
            kdf: KdfDescriptor {
                algorithm: "argon2id".into(),
                mem_kib: p.mem_kib,
                time_cost: p.time_cost,
                parallelism: p.parallelism,
            },
        }
    }
}

impl<P: PayloadCipher> VaultService for VaultBackend<P> {
    fn create(
        &self,
        path: &Path,
        passphrase: SecretBytes,
        policy: Option<SharePolicy>,
    ) -> Result<VaultMeta, VaultError> {
        validate_policy(policy.as_ref())?;
        let lock = self.vault_write_lock(path)?;
        let _guard = lock.lock().unwrap_or_else(|p| p.into_inner());
        let uuid = random_array::<16>()?;
        let salt = Salt(random_array::<16>()?);
        let params = KdfParams::default();
        let mk = self
            .hierarchy
            .derive_master(passphrase.expose_secret(), &salt, &params)?;

        let (identity, recipient) = self.payload.generate_identity()?;
        let (signing_sk, signing_pk) = self.signer.generate().map_err(|_| VaultError::Internal)?;

        let now = now_unix();
        let mut header = VaultHeader {
            format_version: FORMAT_VERSION,
            suite: CipherSuite::V1,
            vault_uuid: uuid,
            created_unix: now,
            modified_unix: now,
            kdf: KdfRecord { salt, params },
            wrapped_age_identity: self.wrap_secret(
                &mk,
                WrapField::AgeIdentity,
                &uuid,
                identity.expose_secret(),
            ),
            age_recipient: recipient,
            wrapped_signing_key: self.wrap_secret(
                &mk,
                WrapField::SigningKey,
                &uuid,
                signing_sk.expose_secret(),
            ),
            signing_public_key: signing_pk.0,
            share_policy: policy.map(|p| SharePolicyRecord {
                shares_total: p.shares_total,
                threshold: p.threshold,
            }),
            content_layout: ContentLayout { payload_len: 0 }, // set by encode
        };

        let empty: Vec<ItemPlaintext> = Vec::new();
        self.write_vault(&mk, &mut header, &empty, path)?;
        Ok(self.meta(&header, 0))
    }

    fn unlock(&self, path: &Path, passphrase: SecretBytes) -> Result<SessionHandle, VaultError> {
        let (_, opened) = self.read_container(path)?; // authenticates integrity first
        let header = &opened.header;
        validate_kdf(&header.kdf.params)?;
        let mk = self.hierarchy.derive_master(
            passphrase.expose_secret(),
            &header.kdf.salt,
            &header.kdf.params,
        )?;
        // Credential gate: unwrap the age identity (post-signature → failure = wrong passphrase).
        let _ = self.unwrap_secret(
            &mk,
            WrapField::AgeIdentity,
            &header.vault_uuid,
            &header.wrapped_age_identity,
        )?;
        self.new_session(mk, path.to_path_buf())
    }

    fn lock(&self, session: &SessionHandle) -> Result<(), VaultError> {
        let mut map = self.sessions.lock().map_err(|_| VaultError::Internal)?;
        map.remove(&session.session_id)
            .ok_or(VaultError::NotFound)
            .map(|_| ()) // SessionState (and its Key32) zeroized on drop here
    }

    fn change_passphrase(
        &self,
        session: &SessionHandle,
        new_passphrase: SecretBytes,
    ) -> Result<(), VaultError> {
        let (old_mk, path) = self.session_mk_path(session)?;
        let lock = self.vault_write_lock(&path)?;
        let _guard = lock.lock().unwrap_or_else(|p| p.into_inner());
        let (_, opened) = self.read_container(&path)?;
        let mut header = opened.header;
        // Unwrap the stored secrets under the old MK.
        let identity = self.unwrap_secret(
            &old_mk,
            WrapField::AgeIdentity,
            &header.vault_uuid,
            &header.wrapped_age_identity,
        )?;
        let signing_sk = self.unwrap_secret(
            &old_mk,
            WrapField::SigningKey,
            &header.vault_uuid,
            &header.wrapped_signing_key,
        )?;
        // Fresh salt + new MK; re-wrap (payload unchanged), re-sign.
        let new_salt = Salt(random_array::<16>()?);
        let new_mk = self.hierarchy.derive_master(
            new_passphrase.expose_secret(),
            &new_salt,
            &header.kdf.params,
        )?;
        header.kdf.salt = new_salt;
        header.wrapped_age_identity = self.wrap_secret(
            &new_mk,
            WrapField::AgeIdentity,
            &header.vault_uuid,
            identity.expose_secret(),
        );
        header.wrapped_signing_key = self.wrap_secret(
            &new_mk,
            WrapField::SigningKey,
            &header.vault_uuid,
            signing_sk.expose_secret(),
        );
        header.modified_unix = now_unix();
        let bytes = container::encode(
            &header,
            &opened.payload,
            &self.hasher,
            &self.signer,
            &signing_sk,
        )?;
        container::write_atomic(&path, &bytes)?;
        // Rotate the live session's MK to the new one. If the session is no longer present it was
        // concurrently locked (removed from the map) — the on-disk re-wrap above still committed, and
        // no live session is left holding a now-stale key, so reporting success is correct. A racing
        // second change_passphrase on the same session read its MK before this write and would fail
        // its own unwrap against the new wrapping (AuthFailed), never silently corrupting state (M4).
        let mut map = self.sessions.lock().map_err(|_| VaultError::Internal)?;
        if let Some(st) = map.get_mut(&session.session_id) {
            st.master_key = new_mk;
        }
        Ok(())
    }

    fn vault_meta(&self, session: &SessionHandle) -> Result<VaultMeta, VaultError> {
        let (mk, path) = self.session_mk_path(session)?;
        let (_, opened) = self.read_container(&path)?;
        // The item directory is inside the encrypted payload, so counting items requires the MK
        // (same cost as `list_items`). Everything returned is non-secret (the `sv-types` invariant).
        let archive = self.decrypt_archive(&mk, &opened.header, &opened.payload)?;
        let item_count = archive.directory.items.len() as u32;
        Ok(self.meta(&opened.header, item_count))
    }

    fn export_signing_public_key(&self, session: &SessionHandle) -> Result<String, VaultError> {
        // Public key only — the MK isn't needed (it's dropped/zeroized immediately). The session
        // gates the call to the open vault and supplies its authenticated path; `read_container`
        // verifies the binding-root signature before we trust the header field.
        let (_, path) = self.session_mk_path(session)?;
        let (_, opened) = self.read_container(&path)?;
        Ok(hex::encode(opened.header.signing_public_key))
    }

    fn list_items(&self, session: &SessionHandle) -> Result<Vec<ItemInfo>, VaultError> {
        let (mk, path) = self.session_mk_path(session)?;
        let (_, opened) = self.read_container(&path)?;
        let archive = self.decrypt_archive(&mk, &opened.header, &opened.payload)?;
        Ok(archive.directory.items.iter().map(item_info).collect())
    }

    fn add_item(
        &self,
        session: &SessionHandle,
        source: &Path,
        name: &str,
    ) -> Result<ItemInfo, VaultError> {
        if name.is_empty() {
            return Err(VaultError::InvalidInput(
                "item name must not be empty".into(),
            ));
        }
        // Size guard (H1): reject an oversized source up front — before any read/decrypt — rather
        // than buffering it (and the whole re-encrypted archive) in memory and risking an OOM.
        let source_len = std::fs::metadata(source)
            .map_err(|e| map_io(e, source))?
            .len();
        if source_len > MAX_ITEM_BYTES {
            return Err(VaultError::TooLarge {
                limit_bytes: MAX_ITEM_BYTES,
                actual_bytes: source_len,
            });
        }
        let (mk, path) = self.session_mk_path(session)?;
        let lock = self.vault_write_lock(&path)?;
        let _guard = lock.lock().unwrap_or_else(|p| p.into_inner());
        let (_, opened) = self.read_container(&path)?;
        let archive = self.decrypt_archive(&mk, &opened.header, &opened.payload)?;
        let mut header = opened.header;

        let data = read_file(source)?;
        // Rebuild the full item set (existing plaintexts + the new one) and re-pack.
        let mut items: Vec<ItemPlaintext> = Vec::with_capacity(archive.directory.items.len() + 1);
        for e in &archive.directory.items {
            items.push(ItemPlaintext {
                item_id: e.item_id,
                name: e.name.clone(),
                added_unix: e.added_unix,
                data: archive.item_data(e)?.to_vec(),
            });
        }
        let item_id = random_array::<16>()?;
        let now = now_unix();
        let content_hash_hex = hex::encode(self.hasher.hash(&data).0);
        let size_bytes = data.len() as u64;
        items.push(ItemPlaintext {
            item_id,
            name: name.to_string(),
            added_unix: now,
            data,
        });

        self.write_vault(&mk, &mut header, &items, &path)?;
        items.iter_mut().for_each(|it| it.data.zeroize());

        Ok(ItemInfo {
            item_id: hyphenated(&item_id),
            name: name.to_string(),
            size_bytes,
            content_hash_hex,
            added_unix: now,
        })
    }

    fn extract_item(
        &self,
        session: &SessionHandle,
        item_id: &str,
        dest: &Path,
    ) -> Result<(), VaultError> {
        // Data-safety (H3): never silently overwrite an existing file. Refuse up front and let the
        // caller choose a different path (an explicit "overwrite" affordance is a future UI choice).
        if dest.exists() {
            return Err(VaultError::OutputExists);
        }
        let (mk, path) = self.session_mk_path(session)?;
        let (_, opened) = self.read_container(&path)?;
        let archive = self.decrypt_archive(&mk, &opened.header, &opened.payload)?;
        let entry = archive
            .directory
            .items
            .iter()
            .find(|e| hyphenated(&e.item_id) == item_id)
            .ok_or(VaultError::NotFound)?;
        let data = archive.item_data(entry)?;
        container::write_atomic(dest, data)
    }

    fn integrity_check(&self, path: &Path) -> Result<IntegrityReport, VaultError> {
        let bytes = read_file(path)?;
        // Recompute the binding root (shown even if the signature fails); propagate
        // Malformed/IncompatibleVersion (those are not "integrity false", they are errors).
        let computed_hash_hex = hex::encode(container::content_digest(&bytes, &self.hasher)?.0);
        let ok = container::decode(&bytes, &self.hasher, &self.signer, None).is_ok();
        Ok(IntegrityReport {
            blake3_ok: ok,
            signature_ok: ok,
            computed_hash_hex,
        })
    }

    fn hash_file(&self, path: &Path) -> Result<String, VaultError> {
        let bytes = read_file(path)?;
        Ok(hex::encode(self.hasher.hash(&bytes).0))
    }

    fn sign_file(&self, session: &SessionHandle, path: &Path) -> Result<String, VaultError> {
        let (mk, vault_path) = self.session_mk_path(session)?;
        let (_, opened) = self.read_container(&vault_path)?;
        let signing_sk = self.unwrap_secret(
            &mk,
            WrapField::SigningKey,
            &opened.header.vault_uuid,
            &opened.header.wrapped_signing_key,
        )?;
        let data = read_file(path)?;
        let trusted_comment = format!("secure-vault signed {}", now_unix());
        let sig = self
            .signer
            .sign(&data, &signing_sk, &trusted_comment)
            .map_err(|_| VaultError::Internal)?;
        let sig_path = append_extension(path, "minisig");
        std::fs::write(&sig_path, &sig.0).map_err(|e| VaultError::Io(e.to_string()))?;
        Ok(sig_path.to_string_lossy().into_owned())
    }

    fn verify_file(
        &self,
        path: &Path,
        signature_path: &Path,
        public_key_path: &Path,
    ) -> Result<IntegrityReport, VaultError> {
        let data = read_file(path)?;
        let sig_bytes = read_file(signature_path)?;
        let pk_text =
            std::fs::read_to_string(public_key_path).map_err(|e| map_io(e, public_key_path))?;
        let public_key = parse_pubkey_hex(&pk_text)?;
        let sig = MinisignSignature(sig_bytes);
        let ok = self.signer.verify(&data, &sig, &public_key).is_ok();
        Ok(IntegrityReport {
            blake3_ok: ok,
            signature_ok: ok,
            computed_hash_hex: hex::encode(self.hasher.hash(&data).0),
        })
    }

    fn split_key(
        &self,
        session: &SessionHandle,
        shares_total: u8,
        threshold: u8,
        out_dir: &Path,
    ) -> Result<Vec<ShareExportInfo>, VaultError> {
        if threshold == 0 || threshold > shares_total || shares_total < 2 {
            return Err(VaultError::InvalidInput(
                "invalid shares_total/threshold".into(),
            ));
        }
        let (mk, path) = self.session_mk_path(session)?;
        let (_, opened) = self.read_container(&path)?;
        let uuid = opened.header.vault_uuid;
        let shares = self
            .sharer
            .split(&mk, shares_total, threshold)
            .map_err(|e| match e {
                CryptoError::InvalidParameter(m) => VaultError::InvalidInput(m),
                _ => VaultError::Internal,
            })?;
        let mut infos = Vec::with_capacity(shares.len());
        for (i, share) in shares.iter().enumerate() {
            let index = (i + 1) as u8;
            let envelope = build_share_envelope(&uuid, index, shares_total, threshold, share);
            let out_path = out_dir.join(format!("{}.share{index}.svshare", hyphenated(&uuid)));
            container::write_atomic(&out_path, &envelope)?;
            infos.push(ShareExportInfo {
                share_index: index,
                vault_uuid: hyphenated(&uuid),
                threshold,
                shares_total,
                envelope_version: SHARE_ENVELOPE_VERSION,
                output_path: out_path.to_string_lossy().into_owned(),
            });
        }
        Ok(infos)
    }

    fn recover(&self, path: &Path, share_paths: &[&Path]) -> Result<SessionHandle, VaultError> {
        let (_, opened) = self.read_container(path)?;
        let need = opened
            .header
            .share_policy
            .map(|s| s.threshold)
            .ok_or_else(|| VaultError::InvalidInput("vault has no recovery policy".into()))?;
        // Count pre-check (non-secret) — distinct from a wrong-share auth failure (E2).
        if share_paths.len() < need as usize {
            return Err(VaultError::InsufficientShares {
                got: share_paths.len().min(255) as u8,
                need,
            });
        }
        let mut shares = Vec::with_capacity(share_paths.len());
        for sp in share_paths {
            let bytes = read_file(sp)?;
            let (share_uuid, _threshold, share) = parse_share_envelope(&bytes)?;
            if share_uuid != opened.header.vault_uuid {
                return Err(VaultError::InvalidInput(
                    "share belongs to a different vault".into(),
                ));
            }
            shares.push(share);
        }
        let mk = self
            .sharer
            .combine(&shares)
            .map_err(|_| VaultError::AuthFailed)?;
        // Credential gate: a wrong reconstruction fails to unwrap the identity → AuthFailed.
        let _ = self.unwrap_secret(
            &mk,
            WrapField::AgeIdentity,
            &opened.header.vault_uuid,
            &opened.header.wrapped_age_identity,
        )?;
        self.new_session(mk, path.to_path_buf())
    }
}

// ===========================================================================
// Free helpers
// ===========================================================================

fn now_unix() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0)
}

fn random_array<const N: usize>() -> Result<[u8; N], VaultError> {
    let mut buf = [0u8; N];
    getrandom::getrandom(&mut buf).map_err(|_| VaultError::Internal)?;
    Ok(buf)
}

/// Render a 16-byte id as a hyphenated UUID string.
fn hyphenated(bytes: &[u8; 16]) -> String {
    let h = hex::encode(bytes);
    format!(
        "{}-{}-{}-{}-{}",
        &h[0..8],
        &h[8..12],
        &h[12..16],
        &h[16..20],
        &h[20..32]
    )
}

fn item_info(e: &ItemEntry) -> ItemInfo {
    ItemInfo {
        item_id: hyphenated(&e.item_id),
        name: e.name.clone(),
        size_bytes: e.plaintext_len,
        content_hash_hex: hex::encode(e.plaintext_blake3),
        added_unix: e.added_unix,
    }
}

fn read_file(path: &Path) -> Result<Vec<u8>, VaultError> {
    // Cap whole-file reads at the same 2 GiB ceiling the crypto-services layer enforces
    // (`sv_platform::MAX_PLAINTEXT_BYTES`, documented there as "the vault's 2 GiB cap" — a cap the
    // vault assumed but never enforced; that gap is audit M-2). A multi-gigabyte input now fails
    // with a clear `TooLarge` ("file too large") instead of an unbounded allocation / OOM. The size
    // is checked from metadata *before* the read, so the allocation never happens. Every read path
    // goes through here — add-item source, integrity/hash/sign/verify, recover shares, AND opening
    // the vault container itself (so selecting a huge non-vault file can't OOM the open path).
    // Vault hashing is not yet streamed (tracked separately as H1), so the cap applies uniformly.
    let meta = std::fs::metadata(path).map_err(|e| map_io(e, path))?;
    if meta.len() > MAX_PLAINTEXT_BYTES {
        return Err(VaultError::TooLarge {
            limit_bytes: MAX_PLAINTEXT_BYTES,
            actual_bytes: meta.len(),
        });
    }
    std::fs::read(path).map_err(|e| map_io(e, path))
}

fn map_io(e: std::io::Error, _path: &Path) -> VaultError {
    match e.kind() {
        std::io::ErrorKind::NotFound => VaultError::NotFound,
        _ => VaultError::Io(e.to_string()),
    }
}

fn append_extension(path: &Path, ext: &str) -> PathBuf {
    let mut s = path.as_os_str().to_os_string();
    s.push(".");
    s.push(ext);
    PathBuf::from(s)
}

fn validate_policy(policy: Option<&SharePolicy>) -> Result<(), VaultError> {
    if let Some(p) = policy {
        if p.threshold == 0 || p.threshold > p.shares_total || p.shares_total < 2 {
            return Err(VaultError::InvalidInput("invalid share policy".into()));
        }
    }
    Ok(())
}

/// Reject header KDF parameters that exceed the safe ceiling, before running Argon2 on them.
fn validate_kdf(params: &KdfParams) -> Result<(), VaultError> {
    let KdfParams::Argon2id(p) = params;
    if p.mem_kib > MAX_KDF_MEM_KIB
        || p.time_cost > MAX_KDF_TIME_COST
        || p.parallelism > MAX_KDF_PARALLELISM
    {
        // A validly-signed but hostile vault: refuse rather than run unbounded work.
        return Err(VaultError::Corrupted);
    }
    Ok(())
}

fn parse_pubkey_hex(text: &str) -> Result<Ed25519PublicKey, VaultError> {
    let bytes = hex::decode(text.trim())
        .map_err(|_| VaultError::InvalidInput("public key must be hex".into()))?;
    let arr: [u8; 32] = bytes
        .as_slice()
        .try_into()
        .map_err(|_| VaultError::InvalidInput("public key must be 32 bytes".into()))?;
    Ok(Ed25519PublicKey(arr))
}

fn build_share_envelope(
    uuid: &[u8; 16],
    index: u8,
    total: u8,
    threshold: u8,
    share: &KeyShare,
) -> Vec<u8> {
    let mut v = Vec::with_capacity(SHARE_ENVELOPE_LEN);
    v.extend_from_slice(&SHARE_MAGIC);
    v.extend_from_slice(&SHARE_ENVELOPE_VERSION.to_le_bytes());
    v.extend_from_slice(uuid);
    v.push(index);
    v.push(total);
    v.push(threshold);
    v.extend_from_slice(share.expose_secret());
    v
}

fn parse_share_envelope(bytes: &[u8]) -> Result<([u8; 16], u8, KeyShare), VaultError> {
    if bytes.len() != SHARE_ENVELOPE_LEN || bytes[..4] != SHARE_MAGIC {
        return Err(VaultError::Malformed);
    }
    let version = u16::from_le_bytes([bytes[4], bytes[5]]);
    if version != SHARE_ENVELOPE_VERSION {
        return Err(VaultError::IncompatibleVersion {
            found: version,
            supported: SHARE_ENVELOPE_VERSION,
        });
    }
    let uuid: [u8; 16] = bytes[6..22].try_into().map_err(|_| VaultError::Malformed)?;
    let threshold = bytes[24];
    let share: [u8; KEYSHARE_LEN] = bytes[25..25 + KEYSHARE_LEN]
        .try_into()
        .map_err(|_| VaultError::Malformed)?;
    Ok((uuid, threshold, KeyShare::new(share)))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::payload::StubPayloadCipher;

    fn backend() -> VaultBackend<StubPayloadCipher> {
        VaultBackend::new(StubPayloadCipher)
    }
    fn pass(s: &str) -> SecretBytes {
        SecretBytes::new(s.as_bytes().to_vec())
    }
    fn tmp() -> tempfile::TempDir {
        tempfile::tempdir().unwrap()
    }

    #[test]
    fn full_lifecycle_create_unlock_add_list_extract() {
        let dir = tmp();
        let vault = dir.path().join("v.svault");
        let be = backend();

        let meta = be.create(&vault, pass("pw1"), None).unwrap();
        assert_eq!(meta.item_count, 0);
        assert_eq!(meta.format_version, FORMAT_VERSION);

        let session = be.unlock(&vault, pass("pw1")).unwrap();
        assert!(be.list_items(&session).unwrap().is_empty());

        let src = dir.path().join("secret.txt");
        std::fs::write(&src, b"top secret data").unwrap();
        let info = be.add_item(&session, &src, "secret.txt").unwrap();
        assert_eq!(info.name, "secret.txt");
        assert_eq!(info.size_bytes, 15);

        let items = be.list_items(&session).unwrap();
        assert_eq!(items.len(), 1);
        assert_eq!(items[0].name, "secret.txt");

        let out = dir.path().join("out.txt");
        be.extract_item(&session, &items[0].item_id, &out).unwrap();
        assert_eq!(std::fs::read(&out).unwrap(), b"top secret data");

        // A second item appends without disturbing the first (single-stream re-encrypt).
        let src2 = dir.path().join("two.bin");
        std::fs::write(&src2, [0u8, 1, 2, 255]).unwrap();
        be.add_item(&session, &src2, "two.bin").unwrap();
        assert_eq!(be.list_items(&session).unwrap().len(), 2);
    }

    #[test]
    fn locked_vault_leaks_no_items_and_wrong_pass_is_unauthorized() {
        let dir = tmp();
        let vault = dir.path().join("v.svault");
        let be = backend();
        be.create(&vault, pass("right"), None).unwrap();

        // Wrong passphrase → AuthFailed (merged, oracle-safe).
        assert!(matches!(
            be.unlock(&vault, pass("wrong")),
            Err(VaultError::AuthFailed)
        ));

        let s = be.unlock(&vault, pass("right")).unwrap();
        be.lock(&s).unwrap();
        // After lock the session id is gone → NotFound, and items are unreadable.
        assert!(matches!(be.list_items(&s), Err(VaultError::NotFound)));
        assert!(matches!(be.lock(&s), Err(VaultError::NotFound)));
    }

    #[test]
    fn change_passphrase_rotates_and_old_passphrase_fails() {
        let dir = tmp();
        let vault = dir.path().join("v.svault");
        let be = backend();
        be.create(&vault, pass("old"), None).unwrap();

        // Add an item so we can confirm the payload survives a passphrase change.
        let s = be.unlock(&vault, pass("old")).unwrap();
        let src = dir.path().join("f");
        std::fs::write(&src, b"keep me").unwrap();
        be.add_item(&s, &src, "f").unwrap();

        be.change_passphrase(&s, pass("new")).unwrap();
        be.lock(&s).unwrap();

        assert!(matches!(
            be.unlock(&vault, pass("old")),
            Err(VaultError::AuthFailed)
        ));
        let s2 = be.unlock(&vault, pass("new")).unwrap();
        let items = be.list_items(&s2).unwrap();
        assert_eq!(items.len(), 1);
        let out = dir.path().join("o");
        be.extract_item(&s2, &items[0].item_id, &out).unwrap();
        assert_eq!(std::fs::read(out).unwrap(), b"keep me");
    }

    #[test]
    fn split_and_recover_roundtrip_with_count_precheck() {
        let dir = tmp();
        let vault = dir.path().join("v.svault");
        let be = backend();
        be.create(
            &vault,
            pass("pw"),
            Some(SharePolicy {
                shares_total: 5,
                threshold: 3,
            }),
        )
        .unwrap();
        let s = be.unlock(&vault, pass("pw")).unwrap();
        let infos = be.split_key(&s, 5, 3, dir.path()).unwrap();
        assert_eq!(infos.len(), 5);
        let paths: Vec<std::path::PathBuf> =
            infos.iter().map(|i| i.output_path.clone().into()).collect();

        // Too few shares → InsufficientShares (non-secret counts), not a generic auth error.
        let two: Vec<&Path> = paths[..2].iter().map(|p| p.as_path()).collect();
        assert!(matches!(
            be.recover(&vault, &two),
            Err(VaultError::InsufficientShares { got: 2, need: 3 })
        ));

        // Any 3 of 5 reconstruct and yield a working session.
        let three: Vec<&Path> = [&paths[0], &paths[2], &paths[4]]
            .iter()
            .map(|p| p.as_path())
            .collect();
        let recovered = be.recover(&vault, &three).unwrap();
        assert!(be.list_items(&recovered).is_ok());
    }

    #[test]
    fn integrity_check_passes_then_detects_payload_tamper() {
        let dir = tmp();
        let vault = dir.path().join("v.svault");
        let be = backend();
        be.create(&vault, pass("pw"), None).unwrap();

        let report = be.integrity_check(&vault).unwrap();
        assert!(report.signature_ok && report.blake3_ok);
        assert_eq!(report.computed_hash_hex.len(), 64);

        // Flip a byte inside the payload region → signature no longer verifies.
        let mut bytes = std::fs::read(&vault).unwrap();
        let header_len = u32::from_le_bytes([bytes[6], bytes[7], bytes[8], bytes[9]]) as usize;
        let payload_offset = 10 + header_len;
        bytes[payload_offset] ^= 0xff;
        std::fs::write(&vault, &bytes).unwrap();

        let bad = be.integrity_check(&vault).unwrap();
        assert!(!bad.signature_ok && !bad.blake3_ok);
    }

    #[test]
    fn sign_and_verify_file_roundtrip() {
        let dir = tmp();
        let vault = dir.path().join("v.svault");
        let be = backend();
        be.create(&vault, pass("pw"), None).unwrap();
        let s = be.unlock(&vault, pass("pw")).unwrap();

        let data = dir.path().join("doc.txt");
        std::fs::write(&data, b"sign me").unwrap();
        let sig_path = be.sign_file(&s, &data).unwrap();

        // Export the vault's signing public key (hex) for verification.
        let header = container::verify_header(&std::fs::read(&vault).unwrap()).unwrap();
        let pk_path = dir.path().join("key.pub");
        std::fs::write(&pk_path, hex::encode(header.signing_public_key)).unwrap();

        let ok = be
            .verify_file(&data, Path::new(&sig_path), &pk_path)
            .unwrap();
        assert!(ok.signature_ok);

        // Tamper the signed file → verification fails.
        std::fs::write(&data, b"sign ME").unwrap();
        let bad = be
            .verify_file(&data, Path::new(&sig_path), &pk_path)
            .unwrap();
        assert!(!bad.signature_ok);
    }

    #[test]
    fn hash_file_matches_blake3() {
        let dir = tmp();
        let f = dir.path().join("f");
        std::fs::write(&f, b"hash me").unwrap();
        let be = backend();
        let got = be.hash_file(&f).unwrap();
        assert_eq!(got, hex::encode(Blake3Hasher.hash(b"hash me").0));
    }

    #[test]
    fn malformed_and_incompatible_files_are_distinct() {
        let dir = tmp();
        let f = dir.path().join("bad");
        let be = backend();

        std::fs::write(&f, b"definitely not a vault").unwrap();
        assert!(matches!(
            be.unlock(&f, pass("x")),
            Err(VaultError::Malformed)
        ));

        let mut v = b"SVLT".to_vec();
        v.extend_from_slice(&9u16.to_le_bytes());
        v.extend_from_slice(&0u32.to_le_bytes());
        std::fs::write(&f, &v).unwrap();
        assert!(matches!(
            be.unlock(&f, pass("x")),
            Err(VaultError::IncompatibleVersion {
                found: 9,
                supported: 1
            })
        ));

        // A missing file is NotFound.
        assert!(matches!(
            be.unlock(dir.path().join("nope.svault").as_path(), pass("x")),
            Err(VaultError::NotFound)
        ));
    }

    #[test]
    fn vault_meta_is_readonly_and_reports_policy_and_item_count() {
        let dir = tmp();
        let vault = dir.path().join("v.svault");
        let be = backend();
        be.create(
            &vault,
            pass("pw"),
            Some(SharePolicy {
                shares_total: 4,
                threshold: 2,
            }),
        )
        .unwrap();
        let before = std::fs::read(&vault).unwrap();

        let s = be.unlock(&vault, pass("pw")).unwrap();
        let m0 = be.vault_meta(&s).unwrap();
        assert_eq!(m0.item_count, 0);
        assert_eq!(m0.format_version, FORMAT_VERSION);
        assert_eq!(m0.kdf.algorithm, "argon2id");
        let policy = m0.share_policy.expect("policy present");
        assert_eq!((policy.shares_total, policy.threshold), (4, 2));

        // A read-only query must not rewrite the container on disk.
        assert_eq!(
            std::fs::read(&vault).unwrap(),
            before,
            "vault_meta mutated the file"
        );

        let src = dir.path().join("f");
        std::fs::write(&src, b"data").unwrap();
        be.add_item(&s, &src, "f").unwrap();
        assert_eq!(be.vault_meta(&s).unwrap().item_count, 1);

        // Invalid/locked session is NotFound — no oracle, same as every other session op.
        be.lock(&s).unwrap();
        assert!(matches!(be.vault_meta(&s), Err(VaultError::NotFound)));
    }

    #[test]
    fn export_signing_public_key_matches_header_and_verifies_signatures() {
        let dir = tmp();
        let vault = dir.path().join("v.svault");
        let be = backend();
        be.create(&vault, pass("pw"), None).unwrap();
        let s = be.unlock(&vault, pass("pw")).unwrap();

        let exported = be.export_signing_public_key(&s).unwrap();
        // Exactly the header's public key, as plain 64-char hex (what `verify_file` parses).
        let header = container::verify_header(&std::fs::read(&vault).unwrap()).unwrap();
        assert_eq!(exported, hex::encode(header.signing_public_key));
        assert_eq!(exported.len(), 64);

        // Round-trip: export → write to a key file → verify a file signed by this vault.
        let data = dir.path().join("doc.txt");
        std::fs::write(&data, b"sign me").unwrap();
        let sig_path = be.sign_file(&s, &data).unwrap();
        let pk_path = dir.path().join("exported.pub");
        std::fs::write(&pk_path, &exported).unwrap();
        let report = be
            .verify_file(&data, Path::new(&sig_path), &pk_path)
            .unwrap();
        assert!(report.signature_ok);

        be.lock(&s).unwrap();
        assert!(matches!(
            be.export_signing_public_key(&s),
            Err(VaultError::NotFound)
        ));
    }

    #[test]
    fn extract_refuses_to_overwrite_existing_destination() {
        // H3 regression: extracting onto an existing file must not clobber it.
        let dir = tmp();
        let vault = dir.path().join("v.svault");
        let be = backend();
        be.create(&vault, pass("pw"), None).unwrap();
        let s = be.unlock(&vault, pass("pw")).unwrap();
        let src = dir.path().join("item.txt");
        std::fs::write(&src, b"VAULT-CONTENT").unwrap();
        let id = be.add_item(&s, &src, "item.txt").unwrap().item_id;

        let dest = dir.path().join("precious.txt");
        std::fs::write(&dest, b"USER-PRECIOUS-DATA").unwrap();
        assert!(matches!(
            be.extract_item(&s, &id, &dest),
            Err(VaultError::OutputExists)
        ));
        // The existing file is untouched.
        assert_eq!(std::fs::read(&dest).unwrap(), b"USER-PRECIOUS-DATA");
        assert_eq!(
            sv_types::ApiError::from(VaultError::OutputExists).code(),
            "SV-OUTPUT-EXISTS"
        );

        // A fresh destination still works.
        let fresh = dir.path().join("fresh.txt");
        be.extract_item(&s, &id, &fresh).unwrap();
        assert_eq!(std::fs::read(&fresh).unwrap(), b"VAULT-CONTENT");
    }

    #[test]
    fn add_item_rejects_oversized_source() {
        // H1 regression: a source larger than MAX_ITEM_BYTES is refused *before* any read, so the
        // pipeline can't OOM. A sparse file (set_len) gives the logical size with no disk/RAM cost.
        let dir = tmp();
        let vault = dir.path().join("v.svault");
        let be = backend();
        be.create(&vault, pass("pw"), None).unwrap();
        let s = be.unlock(&vault, pass("pw")).unwrap();

        let big = dir.path().join("big.bin");
        let f = std::fs::File::create(&big).unwrap();
        f.set_len(MAX_ITEM_BYTES + 1).unwrap();
        drop(f);

        match be.add_item(&s, &big, "big.bin") {
            Err(VaultError::TooLarge {
                limit_bytes,
                actual_bytes,
            }) => {
                assert_eq!(limit_bytes, MAX_ITEM_BYTES);
                assert_eq!(actual_bytes, MAX_ITEM_BYTES + 1);
            }
            other => panic!("expected TooLarge, got {other:?}"),
        }
        // Nothing was added.
        assert!(be.list_items(&s).unwrap().is_empty());
        assert_eq!(
            sv_types::ApiError::from(VaultError::TooLarge {
                limit_bytes: 1,
                actual_bytes: 2
            })
            .code(),
            "SV-TOO-LARGE"
        );
    }

    #[test]
    fn concurrent_add_item_keeps_both_items() {
        // H7 regression: two concurrent adds on one session must not lose an update. Without the
        // per-vault write lock this lost one item in 8/8 trials (see docs/VALIDATION-RESULTS.md).
        for trial in 0..6 {
            let dir = tmp();
            let vault = dir.path().join("v.svault");
            let be = std::sync::Arc::new(backend());
            be.create(&vault, pass("pw"), None).unwrap();
            let s = be.unlock(&vault, pass("pw")).unwrap();

            let a = dir.path().join("a.txt");
            std::fs::write(&a, b"AAAA").unwrap();
            let b = dir.path().join("b.txt");
            std::fs::write(&b, b"BBBB").unwrap();

            let (be1, be2) = (be.clone(), be.clone());
            let (s1, s2) = (s.clone(), s.clone());
            let h1 = std::thread::spawn(move || be1.add_item(&s1, &a, "a.txt"));
            let h2 = std::thread::spawn(move || be2.add_item(&s2, &b, "b.txt"));
            h1.join().unwrap().unwrap();
            h2.join().unwrap().unwrap();

            assert_eq!(
                be.list_items(&s).unwrap().len(),
                2,
                "trial {trial}: a concurrent add was lost"
            );
        }
    }

    // ---- age-backed end-to-end (requires SV_AGE_BIN + SV_AGE_KEYGEN_BIN) ----
    #[test]
    fn age_backed_lifecycle_roundtrips() {
        let (Ok(age), Ok(keygen)) = (
            std::env::var("SV_AGE_BIN"),
            std::env::var("SV_AGE_KEYGEN_BIN"),
        ) else {
            eprintln!("skipping: set SV_AGE_BIN and SV_AGE_KEYGEN_BIN for the age e2e test");
            return;
        };
        let cipher = sv_age::AgeCipher::new_unpinned(&age).unwrap();
        let be = VaultBackend::new(crate::payload::AgePayloadCipher::new(cipher, keygen.into()));

        let dir = tmp();
        let vault = dir.path().join("real.svault");
        be.create(&vault, pass("pw"), None).unwrap();

        // The on-disk payload is a genuine age ciphertext.
        let bytes = std::fs::read(&vault).unwrap();
        assert!(
            bytes
                .windows(b"age-encryption.org/v1".len())
                .any(|w| w == b"age-encryption.org/v1"),
            "payload should be a real age blob"
        );

        let s = be.unlock(&vault, pass("pw")).unwrap();
        let src = dir.path().join("in");
        std::fs::write(&src, b"real age payload \x00\x01 end").unwrap();
        be.add_item(&s, &src, "in").unwrap();
        let items = be.list_items(&s).unwrap();
        assert_eq!(items.len(), 1);
        let out = dir.path().join("out");
        be.extract_item(&s, &items[0].item_id, &out).unwrap();
        assert_eq!(
            std::fs::read(out).unwrap(),
            b"real age payload \x00\x01 end"
        );

        assert!(matches!(
            be.unlock(&vault, pass("nope")),
            Err(VaultError::AuthFailed)
        ));
    }
}
