//! Internal error taxonomy and its oracle-safe projection to [`sv_types::ApiError`].

use sv_types::ApiError;

/// Rich internal error type used throughout the core. It is intentionally *more*
/// descriptive than what crosses the IPC boundary; [`ApiError`] is the redacted view
/// (see the `From` impl) so the UI cannot use error variants as an authentication
/// oracle (open question Q8 — policy may tighten before M6).
#[derive(Debug, thiserror::Error)]
pub enum VaultError {
    #[error("vault, item, or session not found")]
    NotFound,

    /// Structurally not a vault / parse failure (bad magic, truncation, bad CBOR). Benign,
    /// non-secret — distinct from [`VaultError::Corrupted`] (E2).
    #[error("not a Secure Vault file")]
    Malformed,

    /// A real vault whose container **format version** is unsupported — actionable, not
    /// corruption (E1). Detected via the raw FORMAT_VERSION prefix; values are non-secret.
    #[error(
        "incompatible container format version: found {found}, this build supports {supported}"
    )]
    IncompatibleVersion { found: u16, supported: u16 },

    /// Integrity / signature failure on a *real* vault (damaged or tampered). Detected by the
    /// binding-root signature, before any credential — so it is not an oracle for [`AuthFailed`].
    #[error("container is corrupted or has been tampered with")]
    Corrupted,

    /// Wrong passphrase OR incorrect recovery shares (of sufficient count). Kept as a single
    /// internal variant to discourage building an oracle even in logs.
    #[error("authentication failed")]
    AuthFailed,

    /// Fewer recovery shares supplied than the threshold requires (pre-check; non-secret).
    #[error("insufficient recovery shares: got {got}, need {need}")]
    InsufficientShares { got: u8, need: u8 },

    #[error("invalid input: {0}")]
    InvalidInput(String),

    /// A requested item/payload exceeds the safe in-memory size limit. Non-secret counts; surfaced
    /// so the UI can say "file too large" instead of OOMing or returning a generic internal error
    /// (validation H1). `limit_bytes`/`actual_bytes` are informational, not secret.
    #[error("input too large: {actual_bytes} bytes exceeds the {limit_bytes}-byte limit")]
    TooLarge { limit_bytes: u64, actual_bytes: u64 },

    /// A crypto/back-end operation exceeded its wall-clock deadline (e.g. `age` on a very large
    /// payload). Actionable and non-secret — distinct from [`VaultError::Internal`] (H1/H6).
    #[error("operation timed out")]
    Timeout,

    /// An extract/export target already exists; refusing to overwrite it (data-safety, H3).
    #[error("destination already exists")]
    OutputExists,

    #[error(transparent)]
    Crypto(#[from] sv_crypto_traits::CryptoError),

    #[error("i/o error: {0}")]
    Io(String),

    #[error("internal error")]
    Internal,
}

impl From<VaultError> for ApiError {
    fn from(e: VaultError) -> Self {
        match e {
            VaultError::NotFound => ApiError::NotFound,
            VaultError::Malformed => ApiError::Malformed,
            VaultError::IncompatibleVersion { found, supported } => {
                ApiError::IncompatibleVersion { found, supported }
            }
            VaultError::Corrupted => ApiError::Corrupted,
            VaultError::AuthFailed => ApiError::Unauthorized,
            VaultError::InsufficientShares { got, need } => {
                ApiError::InsufficientShares { got, need }
            }
            VaultError::InvalidInput(m) => ApiError::InvalidInput { detail: m },
            VaultError::TooLarge {
                limit_bytes,
                actual_bytes,
            } => ApiError::TooLarge {
                limit_bytes,
                actual_bytes,
            },
            VaultError::Timeout => ApiError::Timeout,
            VaultError::OutputExists => ApiError::OutputExists,
            // I/O failures (permission, disk-full, path problems) are non-secret *conditions* but
            // the underlying message can include a path, so we surface a fixed, actionable detail
            // rather than the raw string (H6). Centralized in `sv_types` so the vault and platform
            // boundaries stay byte-identical.
            VaultError::Io(_) => ApiError::io_generic(),
            // `Crypto` should be translated to a semantic variant at the call site (unwrap-fail
            // → AuthFailed, sig-fail → Corrupted, timeout → Timeout); any that reaches here is an
            // unexpected backend/logic failure → Internal (E2).
            VaultError::Crypto(_) | VaultError::Internal => ApiError::Internal,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn auth_failures_stay_merged_but_benign_conditions_are_distinct() {
        // Wrong passphrase / wrong share stay merged (oracle-safe).
        assert_eq!(
            ApiError::from(VaultError::AuthFailed),
            ApiError::Unauthorized
        );
        // Tamper vs. wrong-file vs. version are now distinct, actionable, non-secret (E1/E2).
        assert_eq!(ApiError::from(VaultError::Corrupted), ApiError::Corrupted);
        assert_eq!(ApiError::from(VaultError::Malformed), ApiError::Malformed);
        assert_eq!(
            ApiError::from(VaultError::IncompatibleVersion {
                found: 99,
                supported: 1
            }),
            ApiError::IncompatibleVersion {
                found: 99,
                supported: 1
            }
        );
        assert_eq!(
            ApiError::from(VaultError::InsufficientShares { got: 2, need: 3 }),
            ApiError::InsufficientShares { got: 2, need: 3 }
        );
        // I/O failures now surface a distinct, actionable SV-IO with a fixed (path-free) detail —
        // no longer the opaque "internal error" (validation H6).
        assert!(matches!(
            ApiError::from(VaultError::Io("disk full at /home/u/secret".into())),
            ApiError::Io { detail } if !detail.is_empty() && !detail.contains("secret")
        ));
        // TooLarge / Timeout / OutputExists are distinct and actionable (H1/H3/H6).
        assert_eq!(
            ApiError::from(VaultError::TooLarge {
                limit_bytes: 10,
                actual_bytes: 20
            }),
            ApiError::TooLarge {
                limit_bytes: 10,
                actual_bytes: 20
            }
        );
        assert_eq!(ApiError::from(VaultError::Timeout), ApiError::Timeout);
        assert_eq!(
            ApiError::from(VaultError::OutputExists),
            ApiError::OutputExists
        );
        // Unexpected crypto/logic failures still redact to Internal (call sites translate the
        // meaningful ones: unwrap→Unauthorized, sig→Corrupted, timeout→Timeout).
        assert_eq!(
            ApiError::from(VaultError::Crypto(
                sv_crypto_traits::CryptoError::VerificationFailed
            )),
            ApiError::Internal
        );
    }
}
