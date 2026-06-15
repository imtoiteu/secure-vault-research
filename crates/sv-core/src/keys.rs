//! Key-hierarchy implementation (M4).
//!
//! ```text
//! passphrase ──Argon2id(salt, params)──▶ Master Key (MK, 32B, in-memory only)
//!                                          │  BLAKE3 derive_key, per-field + vault-bound:
//!                                          ├─ wrap/age-identity:<uuid> ▶ wrap key (age identity)
//!                                          └─ wrap/signing-key:<uuid>  ▶ wrap key (signing key)
//! ```
//!
//! Frozen per [`docs/M5-SCHEMA-DECISIONS.md`](../../../docs/M5-SCHEMA-DECISIONS.md)
//! (H2 / K1 / K2). The MK never touches disk. Each stored secret is wrapped under a key
//! derived **directly** from MK with a per-field, vault-bound context, so a wrapped blob
//! cannot be transplanted between vaults (the `vault_uuid` is in the context) or moved
//! between fields (the field label is in the context) — the wrong context derives the
//! wrong key and the secretbox MAC fails. Changing the passphrase re-derives MK and
//! re-wraps those secrets only; the payload is never re-encrypted.

use sv_crypto_traits::{Kdf, KdfParams, Key32, KeyDerivation, Salt};

use crate::error::VaultError;

/// Crypto-suite version (K2). Single source of truth for the key-derivation context
/// version token; distinct from the on-disk `FORMAT_VERSION` and the IPC `CONTRACT_VERSION`
/// (see the versioning strategy in `docs/M5-SCHEMA-DECISIONS.md`). Changing it re-keys every
/// wrap key and requires an unwrap-old / re-wrap-new migration of existing vaults.
pub const SUITE_VERSION: u8 = 1;

/// A secret stored (wrapped) in the vault header. Each is wrapped under its own key derived
/// from the master key, so the two cannot be confused for one another.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum WrapField {
    /// The age X25519 identity (wraps the vault payload's recipient identity).
    AgeIdentity,
    /// The Ed25519 signing key (provenance/authenticity, #5).
    SigningKey,
}

impl WrapField {
    /// Stable context label. **Byte-frozen** — changing it makes existing vaults
    /// unreadable (the wrap key would change).
    const fn label(self) -> &'static str {
        match self {
            WrapField::AgeIdentity => "age-identity",
            WrapField::SigningKey => "signing-key",
        }
    }
}

/// Build the BLAKE3 `derive_key` context for a wrapped field (K1 grammar
/// `secure-vault/v<SUITE_VERSION>/wrap/<field>:<uuid_hex>`). The prefix is frozen; the
/// `uuid_hex` suffix binds the key to one vault (H2). Lowercase-hex, deterministic.
fn wrap_context(field: WrapField, vault_uuid: &[u8; 16]) -> String {
    format!(
        "secure-vault/v{SUITE_VERSION}/wrap/{}:{}",
        field.label(),
        hex::encode(vault_uuid)
    )
}

/// Derivation contract. Implemented by [`StdKeyHierarchy`] over [`sv_crypto_traits::Kdf`] +
/// [`sv_crypto_traits::KeyDerivation`]. All keys are zeroizing [`Key32`] (C1).
pub trait KeyHierarchy {
    /// passphrase + salt + params → Master Key.
    fn derive_master(
        &self,
        passphrase: &[u8],
        salt: &Salt,
        params: &KdfParams,
    ) -> Result<Key32, VaultError>;

    /// MK → the wrapping key for `field`, bound to `vault_uuid`
    /// (`BLAKE3::derive_key("secure-vault/v1/wrap/<field>:<uuid_hex>", mk)`). Infallible.
    fn derive_wrap_key(&self, master: &Key32, field: WrapField, vault_uuid: &[u8; 16]) -> Key32;
}

/// Production key hierarchy: Argon2id master derivation + BLAKE3 per-field wrap keys.
///
/// Generic over the injected adapters so `sv-core` stays **backend-free** in its production
/// dependency graph (the concrete `Argon2Kdf` / `Blake3Hasher` — and thus the heavy
/// crypto/FFI crates — are wired in by the service layer in M6, and by this crate's tests
/// via a dev-dependency). This keeps the domain crate unit-testable in isolation.
#[derive(Debug, Clone, Copy)]
pub struct StdKeyHierarchy<K, D> {
    kdf: K,
    kd: D,
}

impl<K: Kdf, D: KeyDerivation> StdKeyHierarchy<K, D> {
    /// Wire a master-key KDF (Argon2id) and a subkey deriver (BLAKE3) into a hierarchy.
    pub fn new(kdf: K, kd: D) -> Self {
        Self { kdf, kd }
    }
}

impl<K: Kdf, D: KeyDerivation> KeyHierarchy for StdKeyHierarchy<K, D> {
    fn derive_master(
        &self,
        passphrase: &[u8],
        salt: &Salt,
        params: &KdfParams,
    ) -> Result<Key32, VaultError> {
        // `CryptoError` → `VaultError::Crypto` via the existing `From` impl.
        Ok(self.kdf.derive(passphrase, salt, params)?)
    }

    fn derive_wrap_key(&self, master: &Key32, field: WrapField, vault_uuid: &[u8; 16]) -> Key32 {
        let context = wrap_context(field, vault_uuid);
        self.kd.derive_key(&context, master.expose_secret())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use sv_crypto::{secretbox, Argon2Kdf, Blake3Hasher};
    use sv_crypto_traits::Argon2idParams;

    fn hierarchy() -> StdKeyHierarchy<Argon2Kdf, Blake3Hasher> {
        StdKeyHierarchy::new(Argon2Kdf, Blake3Hasher)
    }

    // Small, structurally-valid params keep the master-key derivation fast (the OWASP floor
    // is a policy concern, asserted in `sv_crypto::policy`).
    fn fast_params() -> KdfParams {
        KdfParams::Argon2id(Argon2idParams {
            mem_kib: 64,
            time_cost: 1,
            parallelism: 1,
        })
    }

    #[test]
    fn wrap_context_is_frozen_and_suite_bound() {
        // K2: changing these literals bricks existing vaults — freeze them so an accidental
        // edit fails CI.
        let uuid = [0u8; 16];
        assert_eq!(
            wrap_context(WrapField::AgeIdentity, &uuid),
            "secure-vault/v1/wrap/age-identity:00000000000000000000000000000000"
        );
        assert_eq!(
            wrap_context(WrapField::SigningKey, &uuid),
            "secure-vault/v1/wrap/signing-key:00000000000000000000000000000000"
        );
        // The version token is bound to the suite constant.
        let prefix = format!("secure-vault/v{SUITE_VERSION}/wrap/");
        assert!(wrap_context(WrapField::AgeIdentity, &uuid).starts_with(&prefix));
        assert_eq!(SUITE_VERSION, 1);
        // Field labels are distinct → domain separation between the two wrapped secrets.
        assert_ne!(
            WrapField::AgeIdentity.label(),
            WrapField::SigningKey.label()
        );
    }

    #[test]
    fn derive_master_is_deterministic_and_binds_passphrase_and_salt() {
        let h = hierarchy();
        let p = fast_params();
        let mk1 = h
            .derive_master(b"correct horse", &Salt([1; 16]), &p)
            .unwrap();
        let mk2 = h
            .derive_master(b"correct horse", &Salt([1; 16]), &p)
            .unwrap();
        assert_eq!(mk1.expose_secret(), mk2.expose_secret()); // deterministic

        // Different passphrase / salt → different master key.
        let mk3 = h.derive_master(b"wrong horse", &Salt([1; 16]), &p).unwrap();
        assert_ne!(mk1.expose_secret(), mk3.expose_secret());
        let mk4 = h
            .derive_master(b"correct horse", &Salt([2; 16]), &p)
            .unwrap();
        assert_ne!(mk1.expose_secret(), mk4.expose_secret());
    }

    #[test]
    fn derive_master_propagates_invalid_params() {
        let h = hierarchy();
        let bad = KdfParams::Argon2id(Argon2idParams {
            mem_kib: 64,
            time_cost: 1,
            parallelism: 0, // structurally invalid
        });
        assert!(matches!(
            h.derive_master(b"x", &Salt([0; 16]), &bad),
            Err(VaultError::Crypto(_))
        ));
    }

    #[test]
    fn wrap_keys_are_domain_separated_by_field_and_vault() {
        let h = hierarchy();
        let mk = Key32::new([7; 32]);
        let uuid_a = [0xAA; 16];
        let uuid_b = [0xBB; 16];

        let age_a = h.derive_wrap_key(&mk, WrapField::AgeIdentity, &uuid_a);
        let age_a2 = h.derive_wrap_key(&mk, WrapField::AgeIdentity, &uuid_a);
        let sig_a = h.derive_wrap_key(&mk, WrapField::SigningKey, &uuid_a);
        let age_b = h.derive_wrap_key(&mk, WrapField::AgeIdentity, &uuid_b);

        assert_eq!(age_a.expose_secret(), age_a2.expose_secret()); // deterministic
        assert_ne!(age_a.expose_secret(), sig_a.expose_secret()); // field separation
        assert_ne!(age_a.expose_secret(), age_b.expose_secret()); // vault separation
                                                                  // A wrap key is never the master key itself.
        assert_ne!(age_a.expose_secret(), mk.expose_secret());
    }

    #[test]
    fn wrap_key_matches_blake3_reference() {
        let h = hierarchy();
        let mk = Key32::new([9; 32]);
        let uuid = [0x11; 16];
        let got = h.derive_wrap_key(&mk, WrapField::AgeIdentity, &uuid);
        let ctx = format!("secure-vault/v1/wrap/age-identity:{}", hex::encode(uuid));
        let want = Blake3Hasher.derive_key(&ctx, mk.expose_secret());
        assert_eq!(got.expose_secret(), want.expose_secret());
    }

    #[test]
    fn wrap_key_seals_and_unwraps_and_resists_transplant() {
        // The real use case: derive a wrap key, secretbox-seal a stored secret, unwrap it.
        // Proves the M4 keys interoperate with M2's secretbox and that the per-field +
        // per-vault binding actually prevents transplant/field-confusion at the AEAD layer.
        let h = hierarchy();
        let mk = Key32::new([5; 32]);
        let uuid_a = [0xAA; 16];
        let uuid_b = [0xBB; 16];
        let secret = b"AGE-SECRET-KEY-1-EXAMPLE";

        let k_a = h.derive_wrap_key(&mk, WrapField::AgeIdentity, &uuid_a);
        let wrapped = secretbox::seal(k_a.expose_secret(), secret);
        assert_eq!(
            secretbox::open(k_a.expose_secret(), &wrapped).unwrap(),
            secret
        );

        // A key for a different vault cannot unwrap (transplant resistance).
        let k_b = h.derive_wrap_key(&mk, WrapField::AgeIdentity, &uuid_b);
        assert!(secretbox::open(k_b.expose_secret(), &wrapped).is_err());

        // A key for a different field cannot unwrap (field-confusion resistance).
        let k_sig = h.derive_wrap_key(&mk, WrapField::SigningKey, &uuid_a);
        assert!(secretbox::open(k_sig.expose_secret(), &wrapped).is_err());
    }
}
