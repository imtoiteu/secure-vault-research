//! # sv-age — [`FileCipher`] adapter driving a bundled `age` CLI
//!
//! age is pure Go with no FFI exports, so the vault core drives a **bundled, first-party
//! `age` binary as a hardened subprocess**:
//! - the binary is **BLAKE3-hash-pinned** ([`AgeCipher::new_pinned`]); construction fails
//!   if the on-disk binary does not match the expected hash,
//! - **recipients** (public) are passed as args; **identities** (secret) are written to a
//!   `0600` temp file (auto-removed, best-effort overwrite) and passed via `-i` — never on
//!   argv/env (the encrypted stream occupies stdin/stdout, so the identity cannot also use
//!   stdin),
//! - spawns with a **cleared environment, no shell**, captured stderr, and strict
//!   non-zero-exit handling; stdin is fed from a writer thread while stdout is drained, so
//!   large payloads cannot deadlock the pipes.
//!
//! Secret hygiene: the input buffer is zeroized after being written to the child, and the
//! decrypted output buffer is zeroized after being handed to the caller's writer.
//!
//! Known M3 limitations (deferred): payloads are buffered in memory (not incrementally
//! streamed); there is no wall-clock spawn timeout yet (M7 hardening).

#![forbid(unsafe_code)]

use std::io::{Read, Write};
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::time::Duration;

use sv_crypto_traits::{AgeIdentity, AgeRecipient, CryptoError, FileCipher, FileCipherAlg};
use zeroize::Zeroize;

/// Failures from driving the `age` subprocess.
#[derive(Debug, thiserror::Error)]
pub enum AgeError {
    #[error("age binary not found at {0}")]
    BinaryNotFound(PathBuf),
    #[error("age binary hash mismatch: expected {expected}, got {actual}")]
    HashMismatch { expected: String, actual: String },
    #[error("failed to spawn age: {0}")]
    Spawn(std::io::Error),
    #[error("i/o error talking to age: {0}")]
    Io(std::io::Error),
    #[error("age exited with status {code:?}: {stderr}")]
    NonZeroExit { code: Option<i32>, stderr: String },
    #[error("age did not finish within {0:?}")]
    TimedOut(Duration),
}

/// Default per-invocation wall-clock limit (M7 hardening): a hung or malicious binary cannot
/// block a vault operation forever. Generous for in-memory payloads; tune with [`AgeCipher::with_timeout`].
const DEFAULT_TIMEOUT: Duration = Duration::from_secs(120);

/// Drives a bundled `age` binary.
#[derive(Debug, Clone)]
pub struct AgeCipher {
    binary: PathBuf,
    timeout: Duration,
}

impl AgeCipher {
    /// Construct, verifying the binary's BLAKE3 hash equals `pinned_blake3_hex`.
    /// This is the production path: the expected hash is embedded at build time.
    pub fn new_pinned(
        binary: impl Into<PathBuf>,
        pinned_blake3_hex: &str,
    ) -> Result<Self, AgeError> {
        let binary = binary.into();
        let actual = binary_blake3_hex(&binary)?;
        if !actual.eq_ignore_ascii_case(pinned_blake3_hex) {
            return Err(AgeError::HashMismatch {
                expected: pinned_blake3_hex.to_ascii_lowercase(),
                actual,
            });
        }
        Ok(Self {
            binary,
            timeout: DEFAULT_TIMEOUT,
        })
    }

    /// Construct without pinning — only for tests / a binary you built this session.
    pub fn new_unpinned(binary: impl Into<PathBuf>) -> Result<Self, AgeError> {
        let binary = binary.into();
        if !binary.exists() {
            return Err(AgeError::BinaryNotFound(binary));
        }
        Ok(Self {
            binary,
            timeout: DEFAULT_TIMEOUT,
        })
    }

    /// Override the per-invocation wall-clock timeout (M7 hardening).
    #[must_use]
    pub fn with_timeout(mut self, timeout: Duration) -> Self {
        self.timeout = timeout;
        self
    }

    /// Spawn `age <args>`, feed `input` on stdin, return captured stdout. `input` is
    /// zeroized after being written (it may be plaintext).
    fn run(&self, args: &[&str], input: Vec<u8>) -> Result<Vec<u8>, AgeError> {
        let mut command = Command::new(&self.binary);
        command
            .args(args)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .env_clear();
        // On Windows a fully-cleared environment can break the subprocess: the OS loader needs
        // SystemRoot/SystemDrive to locate system DLLs, and age uses TEMP/TMP for scratch. Re-add
        // just those (still no PATH, no user secrets) so env_clear's hardening holds without
        // breaking process startup (H4). No-op on Unix.
        #[cfg(windows)]
        for key in ["SystemRoot", "SystemDrive", "TEMP", "TMP"] {
            if let Ok(val) = std::env::var(key) {
                command.env(key, val);
            }
        }
        let mut child = command.spawn().map_err(AgeError::Spawn)?;

        // Feed stdin from a thread (owns the buffer → Send) while we drain stdout/stderr on
        // their own threads, so neither pipe can fill and deadlock and so the main thread can
        // enforce a wall-clock deadline (M7).
        let mut stdin = child.stdin.take().expect("stdin piped");
        let feeder = std::thread::spawn(move || {
            let mut input = input;
            let _ = stdin.write_all(&input); // ignore BrokenPipe if age exits early
            input.zeroize();
            // `stdin` dropped here → EOF to the child.
        });

        let mut stdout = child.stdout.take().expect("stdout piped");
        let (tx, rx) = std::sync::mpsc::channel();
        let reader = std::thread::spawn(move || {
            let mut out = Vec::new();
            let res = stdout.read_to_end(&mut out);
            let _ = tx.send((res, out));
        });

        let mut stderr = child.stderr.take().expect("stderr piped");
        let stderr_reader = std::thread::spawn(move || {
            let mut err = Vec::new();
            let _ = stderr.read_to_end(&mut err);
            err
        });

        // Wait for stdout to close (process output finished) within the deadline.
        let (read_res, mut out) = match rx.recv_timeout(self.timeout) {
            Ok(v) => v,
            Err(_) => {
                let _ = child.kill();
                let _ = child.wait();
                // Detach the feeder/reader threads rather than join: a killed shell can leave a
                // grandchild holding the pipes open, so a join could block until *it* exits.
                // The threads unblock and finish on their own once the write ends close.
                drop((feeder, reader, stderr_reader));
                return Err(AgeError::TimedOut(self.timeout));
            }
        };

        let _ = feeder.join();
        let _ = reader.join();
        let err = stderr_reader.join().unwrap_or_default();
        let status = child.wait().map_err(AgeError::Io)?;
        read_res.map_err(AgeError::Io)?;

        if !status.success() {
            out.zeroize();
            return Err(AgeError::NonZeroExit {
                code: status.code(),
                stderr: String::from_utf8_lossy(&err).trim().to_string(),
            });
        }
        Ok(out)
    }
}

impl FileCipher for AgeCipher {
    fn alg(&self) -> FileCipherAlg {
        FileCipherAlg::AgeV1
    }

    fn encrypt(
        &self,
        plaintext: &mut dyn Read,
        ciphertext: &mut dyn Write,
        recipient: &AgeRecipient,
    ) -> Result<(), CryptoError> {
        let mut input = Vec::new();
        plaintext
            .read_to_end(&mut input)
            .map_err(|e| CryptoError::Backend(format!("read plaintext: {e}")))?;
        let out = self
            .run(&["-e", "-r", recipient.0.as_str()], input)
            .map_err(|e| match e {
                AgeError::TimedOut(_) => CryptoError::Timeout,
                other => CryptoError::Backend(other.to_string()),
            })?;
        ciphertext
            .write_all(&out)
            .map_err(|e| CryptoError::Backend(format!("write ciphertext: {e}")))
    }

    fn decrypt(
        &self,
        ciphertext: &mut dyn Read,
        plaintext: &mut dyn Write,
        identity: &AgeIdentity,
    ) -> Result<(), CryptoError> {
        let mut input = Vec::new();
        ciphertext
            .read_to_end(&mut input)
            .map_err(|e| CryptoError::Backend(format!("read ciphertext: {e}")))?;

        let id_file = SecureIdentityFile::new(identity.expose_secret())
            .map_err(|e| CryptoError::Backend(format!("identity temp: {e}")))?;

        let mut out = self
            .run(&["-d", "-i", id_file.path_str()], input)
            .map_err(|e| match e {
                // A failed decryption (wrong identity / corrupt) is an authentication failure.
                AgeError::NonZeroExit { .. } => CryptoError::VerificationFailed,
                AgeError::TimedOut(_) => CryptoError::Timeout,
                other => CryptoError::Backend(other.to_string()),
            })?;

        let res = plaintext
            .write_all(&out)
            .map_err(|e| CryptoError::Backend(format!("write plaintext: {e}")));
        out.zeroize();
        res
    }
}

/// Compute the lowercase BLAKE3 hex of a file (used for binary pinning).
pub fn binary_blake3_hex(path: &Path) -> Result<String, AgeError> {
    let bytes = std::fs::read(path).map_err(|e| match e.kind() {
        std::io::ErrorKind::NotFound => AgeError::BinaryNotFound(path.to_path_buf()),
        _ => AgeError::Io(e),
    })?;
    Ok(blake3::hash(&bytes).to_hex().to_string())
}

/// A `0600` temp file holding an age identity, removed on drop (best-effort zero-overwrite
/// first). The identity is written to disk only for the lifetime of one `age -d` call.
struct SecureIdentityFile {
    file: tempfile::NamedTempFile,
}

impl SecureIdentityFile {
    fn new(identity: &[u8]) -> std::io::Result<Self> {
        // tempfile creates the file with 0600 on Unix and O_EXCL semantics.
        let mut file = tempfile::Builder::new().prefix("sv-age-id-").tempfile()?;
        file.write_all(identity)?;
        file.flush()?;
        Ok(Self { file })
    }

    fn path_str(&self) -> &str {
        self.file.path().to_str().unwrap_or_default()
    }
}

impl Drop for SecureIdentityFile {
    fn drop(&mut self) {
        // Best-effort overwrite before unlink (filesystems/SSDs may not honor in place).
        if let Ok(meta) = self.file.as_file().metadata() {
            let zeros = vec![0u8; meta.len() as usize];
            use std::io::Seek;
            let _ = self.file.as_file_mut().rewind();
            let _ = self.file.as_file_mut().write_all(&zeros);
            let _ = self.file.as_file_mut().flush();
        }
        // `NamedTempFile`'s own Drop unlinks the path.
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;

    // ---- always-on (no age binary needed) --------------------------------

    #[test]
    fn hash_pin_matches_and_mismatches() {
        // Use this test binary itself as a stand-in "binary" to hash.
        let me = std::env::current_exe().unwrap();
        let real = binary_blake3_hex(&me).unwrap();
        assert_eq!(real.len(), 64);
        assert!(AgeCipher::new_pinned(&me, &real).is_ok());
        let wrong = "00".repeat(32);
        assert!(matches!(
            AgeCipher::new_pinned(&me, &wrong),
            Err(AgeError::HashMismatch { .. })
        ));
    }

    #[test]
    fn missing_binary_is_reported() {
        assert!(matches!(
            AgeCipher::new_unpinned(PathBuf::from("/no/such/age")),
            Err(AgeError::BinaryNotFound(_))
        ));
    }

    #[cfg(unix)]
    #[test]
    fn run_aborts_a_hanging_binary_at_the_timeout() {
        use std::os::unix::fs::PermissionsExt;
        let dir = tempfile::tempdir().unwrap();
        let script = dir.path().join("hang.sh");
        std::fs::write(&script, b"#!/bin/sh\nsleep 30\n").unwrap();
        std::fs::set_permissions(&script, std::fs::Permissions::from_mode(0o755)).unwrap();

        let cipher = AgeCipher::new_unpinned(&script)
            .unwrap()
            .with_timeout(Duration::from_millis(200));

        let start = std::time::Instant::now();
        let err = cipher
            .encrypt(
                &mut b"data".as_slice(),
                &mut Vec::new(),
                &AgeRecipient("age1example".into()),
            )
            .unwrap_err();
        // Returned promptly (killed at the deadline), not after the 30s sleep.
        assert!(start.elapsed() < Duration::from_secs(10));
        // A wall-clock timeout now surfaces as the distinct `Timeout` variant (validation H1),
        // so callers can show "timed out" instead of a generic backend/internal error.
        assert!(matches!(err, CryptoError::Timeout));
    }

    #[test]
    fn identity_temp_file_is_removed_on_drop() {
        let path;
        {
            let f = SecureIdentityFile::new(b"AGE-SECRET-KEY-1TEST").unwrap();
            path = PathBuf::from(f.path_str());
            assert!(path.exists());
        }
        assert!(!path.exists(), "identity temp file must be removed on drop");
    }

    // ---- end-to-end (requires SV_AGE_BIN + SV_AGE_KEYGEN_BIN) -------------

    fn bins() -> Option<(PathBuf, PathBuf)> {
        let age = std::env::var("SV_AGE_BIN").ok()?;
        let keygen = std::env::var("SV_AGE_KEYGEN_BIN").ok()?;
        let (age, keygen) = (PathBuf::from(age), PathBuf::from(keygen));
        (age.exists() && keygen.exists()).then_some((age, keygen))
    }

    /// Run age-keygen → (identity_file_contents, recipient `age1…`).
    fn keygen(keygen_bin: &Path) -> (Vec<u8>, String) {
        let out = Command::new(keygen_bin).output().unwrap();
        assert!(out.status.success());
        let identity = out.stdout; // includes the AGE-SECRET-KEY-1 line + comments
        let text = String::from_utf8_lossy(&identity);
        let recipient = text
            .lines()
            .find_map(|l| l.split_whitespace().find(|w| w.starts_with("age1")))
            .expect("recipient in keygen output")
            .to_string();
        (identity, recipient)
    }

    #[test]
    fn encrypt_then_decrypt_roundtrips() {
        let Some((age, keygen_bin)) = bins() else {
            eprintln!("skipping: set SV_AGE_BIN and SV_AGE_KEYGEN_BIN to run age e2e tests");
            return;
        };
        let cipher = AgeCipher::new_unpinned(&age).unwrap();
        let (identity, recipient) = keygen(&keygen_bin);

        let plaintext = b"secure vault payload \x00\x01\x02 end".to_vec();
        let mut ct = Vec::new();
        cipher
            .encrypt(&mut plaintext.as_slice(), &mut ct, &AgeRecipient(recipient))
            .unwrap();
        assert!(ct.starts_with(b"age-encryption.org/v1"));

        let mut pt = Vec::new();
        cipher
            .decrypt(
                &mut ct.as_slice(),
                &mut pt,
                &AgeIdentity::new(sv_crypto_traits::SecretBytes::new(identity)),
            )
            .unwrap();
        assert_eq!(pt, plaintext);
    }

    #[test]
    fn decrypt_with_wrong_identity_fails_auth() {
        let Some((age, keygen_bin)) = bins() else {
            eprintln!("skipping: SV_AGE_BIN/SV_AGE_KEYGEN_BIN not set");
            return;
        };
        let cipher = AgeCipher::new_unpinned(&age).unwrap();
        let (_id_a, recipient_a) = keygen(&keygen_bin);
        let (id_b, _recipient_b) = keygen(&keygen_bin);

        let mut ct = Vec::new();
        cipher
            .encrypt(
                &mut b"top secret".as_slice(),
                &mut ct,
                &AgeRecipient(recipient_a),
            )
            .unwrap();

        // Decrypt with the *wrong* identity → VerificationFailed.
        let mut pt = Vec::new();
        let err = cipher
            .decrypt(
                &mut ct.as_slice(),
                &mut pt,
                &AgeIdentity::new(sv_crypto_traits::SecretBytes::new(id_b)),
            )
            .unwrap_err();
        assert!(matches!(err, CryptoError::VerificationFailed));
    }
}
