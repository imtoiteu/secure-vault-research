//! N1 — passphrase handling across the Tauri IPC boundary.
//!
//! A passphrase arrives over the JSON IPC bridge, so the Tauri/serde machinery has already
//! made copies we cannot reach (the raw message buffer, the JSON parse buffer). [`IpcPassphrase`]
//! is the command argument type: it zeroizes **our** copy on drop and redacts `Debug`, and is
//! converted to a [`SecretBytes`] on the first line of each handler. The upstream framework
//! copies remain the **documented residual** (see `docs/M6-IPC-DECISIONS.md` §N1 / threat model):
//! full passphrase-entry memory hygiene through the JSON bridge is not achievable; mitigate with
//! OS disk+swap encryption and by excluding these commands from argument logging.

use serde::{Deserialize, Deserializer};
use sv_crypto_traits::SecretBytes;
use zeroize::Zeroize;

/// A passphrase received at the IPC boundary. Zeroized on drop; `Debug` is redacted; never
/// logged, never placed in a DTO or error.
pub struct IpcPassphrase(String);

impl IpcPassphrase {
    /// Move the passphrase into a zeroizing [`SecretBytes`] and wipe our `String` copy. The
    /// returned value is what the internal [`sv_core::VaultService`] consumes.
    #[must_use]
    pub fn into_secret(mut self) -> SecretBytes {
        let secret = SecretBytes::new(self.0.as_bytes().to_vec());
        self.0.zeroize();
        secret
    }

    /// Construct directly (tests / non-IPC callers).
    #[must_use]
    pub fn new(s: String) -> Self {
        Self(s)
    }
}

impl<'de> Deserialize<'de> for IpcPassphrase {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        // The intermediate `String` is an unavoidable upstream copy (the documented residual).
        Ok(IpcPassphrase(String::deserialize(deserializer)?))
    }
}

impl Drop for IpcPassphrase {
    fn drop(&mut self) {
        self.0.zeroize();
    }
}

impl core::fmt::Debug for IpcPassphrase {
    fn fmt(&self, f: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
        write!(f, "IpcPassphrase(<redacted>)")
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn debug_is_redacted_and_secret_round_trips() {
        let p = IpcPassphrase::new("correct horse".into());
        assert_eq!(format!("{p:?}"), "IpcPassphrase(<redacted>)");
        let s = p.into_secret();
        assert_eq!(s.expose_secret(), b"correct horse");
    }

    #[test]
    fn deserializes_from_a_json_string() {
        let p: IpcPassphrase = serde_json::from_str("\"hunter2\"").unwrap();
        assert_eq!(p.into_secret().expose_secret(), b"hunter2");
    }
}
