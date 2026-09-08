//! A vault created through the desktop cipher (bundled `age` subprocess) must open through
//! the mobile cipher (in-process pure Rust), and vice versa.
//!
//! `sv-age-rs`'s `interop` test proves the two implementations agree at the age-blob level.
//! This proves it at the level users actually care about: a whole `.svault` container, with
//! its Argon2id key hierarchy, binding signature and encrypted item directory intact across
//! the swap. It is the user-visible form of the design's central claim.
//!
//! Ignored by default — needs the real age binaries. Run with:
//!   SV_AGE_BIN=app/binaries/age SV_AGE_KEYGEN_BIN=app/binaries/age-keygen \
//!     cargo test -p sv-app --test vault_interop -- --ignored --nocapture

use std::path::{Path, PathBuf};

use sv_app::{AgePayloadCipher, RustAgePayloadCipher};
use sv_core::VaultService;
use sv_crypto_traits::SecretBytes;

const PASS: &[u8] = b"correct horse battery staple";

fn env_bin(var: &str) -> PathBuf {
    PathBuf::from(std::env::var(var).unwrap_or_else(|_| panic!("{var} not set — see module docs")))
}

/// The production desktop cipher, unpinned (the pin is a release-build concern; this test is
/// about wire format, not tamper-evidence).
fn desktop_cipher() -> AgePayloadCipher {
    let age = env_bin("SV_AGE_BIN");
    let keygen = env_bin("SV_AGE_KEYGEN_BIN");
    AgePayloadCipher::new(
        sv_age::AgeCipher::new_unpinned(&age).expect("age binary must exist"),
        keygen,
    )
}

struct Scratch(PathBuf);

impl Scratch {
    fn new(tag: &str) -> Self {
        let dir = std::env::temp_dir().join(format!("sv-vault-interop-{tag}-{}", std::process::id()));
        std::fs::create_dir_all(&dir).expect("create scratch dir");
        Self(dir)
    }
    fn path(&self, name: &str) -> PathBuf {
        self.0.join(name)
    }
}

impl Drop for Scratch {
    fn drop(&mut self) {
        let _ = std::fs::remove_dir_all(&self.0);
    }
}

/// Create a vault with `backend`, then open it with `other` and read its metadata back.
fn cross_open<A, B>(tag: &str, creator: &A, opener: &B)
where
    A: VaultService,
    B: VaultService,
{
    let scratch = Scratch::new(tag);
    let path: PathBuf = scratch.path("interop.svault");

    let created = creator
        .create(&path, SecretBytes::new(PASS.to_vec()), None)
        .expect("create must succeed");

    let session = opener
        .unlock(&path, SecretBytes::new(PASS.to_vec()))
        .expect("the other cipher must open this vault");

    let opened = opener.vault_meta(&session).expect("metadata must be readable");

    assert_eq!(
        created.vault_uuid, opened.vault_uuid,
        "the same vault must be reported by both ciphers"
    );
    assert_eq!(created.format_version, opened.format_version);
    assert_eq!(opened.item_count, 0);
}

#[test]
#[ignore = "requires the real age binaries; see module docs"]
fn desktop_written_vault_opens_with_the_mobile_cipher() {
    let desktop = sv_app::VaultBackend::new(desktop_cipher());
    let mobile = sv_app::VaultBackend::new(RustAgePayloadCipher::new());
    cross_open("d2m", &desktop, &mobile);
}

#[test]
#[ignore = "requires the real age binaries; see module docs"]
fn mobile_written_vault_opens_with_the_desktop_cipher() {
    let mobile = sv_app::VaultBackend::new(RustAgePayloadCipher::new());
    let desktop = sv_app::VaultBackend::new(desktop_cipher());
    cross_open("m2d", &mobile, &desktop);
}

/// A wrong passphrase must still be rejected after the cipher swap — the swap must not weaken
/// the credential gate.
#[test]
#[ignore = "requires the real age binaries; see module docs"]
fn cross_cipher_open_still_rejects_a_wrong_passphrase() {
    let scratch = Scratch::new("wrongpass");
    let path: PathBuf = scratch.path("interop.svault");

    let desktop = sv_app::VaultBackend::new(desktop_cipher());
    desktop
        .create(&path, SecretBytes::new(PASS.to_vec()), None)
        .expect("create must succeed");

    let mobile = sv_app::VaultBackend::new(RustAgePayloadCipher::new());
    let err = mobile
        .unlock(Path::new(&path), SecretBytes::new(b"wrong passphrase".to_vec()))
        .expect_err("a wrong passphrase must not open the vault");
    assert!(
        matches!(err, sv_core::VaultError::AuthFailed),
        "wrong passphrase must be AuthFailed, got {err:?}"
    );
}
