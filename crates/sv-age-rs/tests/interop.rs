//! Cross-implementation format compatibility: the Go `age` binary and this pure-Rust adapter
//! must read each other's ciphertext. This is the test behind the design claim that a vault
//! written on desktop opens on mobile.
//!
//! Ignored by default because it needs the real `age` binary. Run with:
//!   SV_AGE_BIN=app/binaries/age SV_AGE_KEYGEN_BIN=app/binaries/age-keygen \
//!     cargo test -p sv-age-rs --test interop -- --ignored --nocapture

use std::io::Write;
use std::path::PathBuf;
use std::process::{Command, Stdio};

use sv_age_rs::{generate_identity, RustAgeCipher};
use sv_crypto_traits::{AgeIdentity, AgeRecipient, FileCipher, SecretBytes};

fn env_bin(var: &str) -> String {
    std::env::var(var).unwrap_or_else(|_| panic!("{var} not set — see the module docs"))
}

/// A unique scratch directory that cleans itself up.
struct Scratch(PathBuf);

impl Scratch {
    fn new(tag: &str) -> Self {
        let dir = std::env::temp_dir().join(format!("sv-interop-{tag}-{}", std::process::id()));
        std::fs::create_dir_all(&dir).expect("create scratch dir");
        Self(dir)
    }
}

impl Drop for Scratch {
    fn drop(&mut self) {
        let _ = std::fs::remove_dir_all(&self.0);
    }
}

#[test]
#[ignore = "requires the real age binary; see module docs"]
fn rust_ciphertext_decrypts_with_go_age() {
    let age_bin = env_bin("SV_AGE_BIN");

    let (id_bytes, recipient) = generate_identity().unwrap();
    let plaintext = b"interop payload".to_vec();

    let mut ct = Vec::new();
    RustAgeCipher::new()
        .encrypt(&mut plaintext.as_slice(), &mut ct, &AgeRecipient(recipient))
        .unwrap();

    // Hand the Rust-generated identity to the Go binary exactly as the desktop path does.
    let scratch = Scratch::new("r2g");
    let id_path = scratch.0.join("id.txt");
    std::fs::write(&id_path, &id_bytes).unwrap();

    let mut child = Command::new(&age_bin)
        .args(["-d", "-i"])
        .arg(&id_path)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .expect("spawn age");
    child.stdin.as_mut().unwrap().write_all(&ct).unwrap();
    let out = child.wait_with_output().unwrap();

    assert!(
        out.status.success(),
        "go age failed to decrypt Rust ciphertext: {}",
        String::from_utf8_lossy(&out.stderr)
    );
    assert_eq!(out.stdout, plaintext, "Go age must decrypt Rust ciphertext");
}

#[test]
#[ignore = "requires the real age binary; see module docs"]
fn go_ciphertext_decrypts_with_rust() {
    let age_bin = env_bin("SV_AGE_BIN");
    let keygen_bin = env_bin("SV_AGE_KEYGEN_BIN");

    // Generate the identity with the real age-keygen — the exact desktop production path.
    let kg = Command::new(&keygen_bin).output().expect("spawn age-keygen");
    assert!(kg.status.success(), "age-keygen failed");
    let id_bytes = kg.stdout;
    let text = String::from_utf8_lossy(&id_bytes);
    let recipient = text
        .lines()
        .find_map(|l| l.strip_prefix("# public key: "))
        .expect("age-keygen must print the public key")
        .trim()
        .to_string();

    let plaintext = b"interop payload".to_vec();
    let mut child = Command::new(&age_bin)
        .args(["-r", &recipient])
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .expect("spawn age");
    child.stdin.as_mut().unwrap().write_all(&plaintext).unwrap();
    let enc = child.wait_with_output().unwrap();
    assert!(
        enc.status.success(),
        "go age encrypt failed: {}",
        String::from_utf8_lossy(&enc.stderr)
    );

    let mut out = Vec::new();
    RustAgeCipher::new()
        .decrypt(
            &mut enc.stdout.as_slice(),
            &mut out,
            &AgeIdentity::new(SecretBytes::new(id_bytes)),
        )
        .expect("Rust must decrypt Go age ciphertext");
    assert_eq!(out, plaintext, "Rust must decrypt Go age ciphertext");
}
