//! Internal error taxonomy and its oracle-safe projection to [`sv_types::ApiError`].
//!
//! Mirrors `sv_core::VaultError`: a richer internal type that collapses to the redacted,
//! coded `ApiError` at the boundary. The `From` impl lives here (this crate depends on
//! `sv-types`, exactly as `sv-core` does) so there is no orphan-rule conflict and `sv-types`
//! needs no change. The merge keeps the oracle-safe property: a wrong passphrase and a
//! tampered ciphertext both surface as a single `SV-UNAUTHORIZED`.

use sv_types::ApiError;

/// Failure modes for the file-level platform services.
#[derive(Debug, thiserror::Error)]
pub enum PlatformError {
    /// An input file/key/signature path does not exist.
    #[error("file not found")]
    NotFound,

    /// The artifact is structurally not what was expected (bad magic / truncated / wrong tag).
    #[error("not a recognised secure-vault artifact")]
    Malformed,

    /// A recognised artifact whose format version this build does not support. Non-secret.
    #[error("incompatible artifact version: found {found}, this build supports {supported}")]
    IncompatibleVersion { found: u16, supported: u16 },

    /// Decryption / key-unwrap failed: wrong passphrase **or** tampered ciphertext. Merged to
    /// avoid an authentication oracle (mirrors the vault's `AuthFailed`).
    #[error("authentication failed")]
    AuthFailed,

    /// Fewer secret-sharing pieces were supplied than the recorded threshold. A **non-secret**
    /// pre-check (counts are not secret), surfaced *before* any reconstruction is attempted —
    /// mirrors the vault's `keys_recover` count gate and maps to `ApiError::InsufficientShares`.
    #[error("insufficient shares: {got} provided, {need} required")]
    InsufficientShares { got: u8, need: u8 },

    /// Caller-supplied input was structurally invalid. `detail` is **non-secret**.
    #[error("invalid input: {0}")]
    InvalidInput(String),

    /// The input exceeds the safe in-memory size limit; refused rather than risking OOM (audit R5).
    #[error("input too large: {actual_bytes} bytes exceeds the {limit_bytes}-byte limit")]
    TooLarge { limit_bytes: u64, actual_bytes: u64 },

    /// An output destination already exists; refused to overwrite it (data-safety).
    #[error("destination already exists")]
    OutputExists,

    /// A file could not be read or written.
    #[error("i/o error: {0}")]
    Io(String),

    /// Unexpected internal failure (redacted at the boundary).
    #[error("internal error")]
    Internal,
}

impl From<PlatformError> for ApiError {
    fn from(e: PlatformError) -> Self {
        match e {
            PlatformError::NotFound => ApiError::NotFound,
            PlatformError::Malformed => ApiError::Malformed,
            PlatformError::IncompatibleVersion { found, supported } => {
                ApiError::IncompatibleVersion { found, supported }
            }
            // Wrong passphrase / tamper stay merged (oracle-safe).
            PlatformError::AuthFailed => ApiError::Unauthorized,
            // Counts are non-secret; surface the actionable got/need (reuses the frozen code).
            PlatformError::InsufficientShares { got, need } => {
                ApiError::InsufficientShares { got, need }
            }
            PlatformError::InvalidInput(m) => ApiError::InvalidInput { detail: m },
            PlatformError::TooLarge {
                limit_bytes,
                actual_bytes,
            } => ApiError::TooLarge {
                limit_bytes,
                actual_bytes,
            },
            PlatformError::OutputExists => ApiError::OutputExists,
            // The raw message may include a path, so surface a fixed, non-secret detail (H6).
            // Centralized in `sv_types` so this stays byte-identical with the vault's boundary.
            PlatformError::Io(_) => ApiError::io_generic(),
            PlatformError::Internal => ApiError::Internal,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn auth_failures_merge_but_benign_conditions_stay_distinct() {
        // Wrong passphrase / tamper → merged, oracle-safe.
        assert_eq!(
            ApiError::from(PlatformError::AuthFailed),
            ApiError::Unauthorized
        );
        // Insufficient shares is a non-secret, actionable count (maps to the frozen code).
        assert_eq!(
            ApiError::from(PlatformError::InsufficientShares { got: 2, need: 3 }),
            ApiError::InsufficientShares { got: 2, need: 3 }
        );
        // Benign, actionable conditions stay distinct.
        assert_eq!(ApiError::from(PlatformError::NotFound), ApiError::NotFound);
        assert_eq!(
            ApiError::from(PlatformError::Malformed),
            ApiError::Malformed
        );
        assert_eq!(
            ApiError::from(PlatformError::OutputExists),
            ApiError::OutputExists
        );
        assert_eq!(
            ApiError::from(PlatformError::IncompatibleVersion {
                found: 9,
                supported: 1
            }),
            ApiError::IncompatibleVersion {
                found: 9,
                supported: 1
            }
        );
        assert_eq!(
            ApiError::from(PlatformError::TooLarge {
                limit_bytes: 10,
                actual_bytes: 20
            }),
            ApiError::TooLarge {
                limit_bytes: 10,
                actual_bytes: 20
            }
        );
        // I/O detail is fixed and path-free (no secret leak).
        assert!(matches!(
            ApiError::from(PlatformError::Io("disk full at /home/u/secret.txt".into())),
            ApiError::Io { detail } if !detail.contains("secret")
        ));
    }
}
