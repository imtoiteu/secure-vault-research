//! Internal error taxonomy and its oracle-safe projection to [`sv_types::ApiError`].
//!
//! Mirrors [`sv_platform::PlatformError`](../../sv-platform/src/error.rs): a richer internal type
//! that collapses to the redacted, coded `ApiError` at the boundary. The `From` impl lives here
//! (this crate depends on `sv-types`, exactly as `sv-core`/`sv-platform` do) so there is no
//! orphan-rule conflict and `sv-types` needs no change.
//!
//! ## The oracle-safety guarantee (load-bearing)
//! Every "this image does not yield a payload **for you**" outcome — there is no SVSTEG frame
//! ([`StegoError::NoPayload`]), the frame is structurally wrong ([`StegoError::BadFrame`]), or the
//! AEAD failed because the passphrase was wrong / the carrier was tampered
//! ([`StegoError::AuthFailed`]) — collapses to a **single** [`ApiError::Unauthorized`]. An attacker
//! therefore cannot learn whether a given image carries an `sv-stego` payload, nor distinguish a
//! wrong passphrase from a tampered carrier. Only a genuinely undecodable *image* (a fact about the
//! file, not about the secret) is [`ApiError::Malformed`]. Same discipline as the vault unlock and
//! the Secret-Sharing recover paths.

use sv_types::ApiError;

/// Failure modes for the steganography services.
#[derive(Debug, thiserror::Error)]
pub enum StegoError {
    /// An input file (cover / payload / stego / image) does not exist.
    #[error("file not found")]
    NotFound,

    /// An input file exceeds the safe in-memory read cap; refused before buffering (alloc guard).
    #[error("file too large: {actual_bytes} bytes exceeds the {limit_bytes}-byte limit")]
    FileTooLarge { limit_bytes: u64, actual_bytes: u64 },

    /// The cover bytes could not be decoded as an image at all. A fact about the *file*, not the
    /// secret, so it is surfaced distinctly (not merged into the oracle-safe bucket).
    #[error("cover is not a decodable image")]
    CoverUndecodable,

    /// The image decoded, but its container format is not a supported lossless cover (PNG/BMP).
    #[error("unsupported cover format (only lossless PNG/BMP are supported)")]
    UnsupportedCoverFormat,

    /// The payload does not fit in the cover's embedding capacity. Counts are **non-secret** and
    /// surfaced as an actionable limit/actual pair (mirrors `sv-platform`'s `TooLarge`).
    #[error("payload too large: {needed} bytes exceeds the {capacity}-byte cover capacity")]
    CapacityExceeded { capacity: u64, needed: u64 },

    /// No SVSTEG frame is present (bad/absent magic, implausible declared length). Merged into the
    /// oracle-safe bucket so "carries no payload" is indistinguishable from "wrong passphrase".
    #[error("no recoverable payload")]
    NoPayload,

    /// A frame is present but structurally invalid (bad flags/algorithm ids, truncated). Merged
    /// into the oracle-safe bucket for the same reason as [`StegoError::NoPayload`].
    #[error("no recoverable payload")]
    BadFrame,

    /// De-embedding succeeded but the AEAD open failed: wrong passphrase **or** tampered carrier.
    /// Merged to avoid an authentication oracle (mirrors the vault's `AuthFailed`).
    #[error("no recoverable payload")]
    AuthFailed,

    /// A recognised frame whose envelope version this build does not support. **Non-secret**
    /// (the version is framing, present in any well-formed frame regardless of the key).
    #[error("incompatible stego envelope version: found {found}, this build supports {supported}")]
    UnsupportedVersion { found: u16, supported: u16 },

    /// An output destination already exists; refused to overwrite it (Phase 3 file I/O).
    #[error("destination already exists")]
    OutputExists,

    /// A file could not be read or written (Phase 3 file I/O). The raw message may include a path,
    /// so it is surfaced via the fixed, path-free [`ApiError::io_generic`].
    #[error("i/o error: {0}")]
    Io(String),

    /// A bounded detector exceeded its wall-clock budget (Phase 2 detection).
    #[error("detector timed out")]
    DetectorTimeout,

    /// Caller-supplied options were structurally invalid. `detail` is **non-secret**.
    #[error("invalid options: {0}")]
    InvalidOptions(String),

    /// Unexpected internal failure (redacted at the boundary).
    #[error("internal error")]
    Internal,
}

impl From<StegoError> for ApiError {
    fn from(e: StegoError) -> Self {
        match e {
            // Benign, non-secret file facts.
            StegoError::NotFound => ApiError::NotFound,
            StegoError::FileTooLarge {
                limit_bytes,
                actual_bytes,
            } => ApiError::TooLarge {
                limit_bytes,
                actual_bytes,
            },
            // A fact about the file → distinct, actionable.
            StegoError::CoverUndecodable | StegoError::UnsupportedCoverFormat => {
                ApiError::Malformed
            }
            // Capacity counts are non-secret.
            StegoError::CapacityExceeded { capacity, needed } => ApiError::TooLarge {
                limit_bytes: capacity,
                actual_bytes: needed,
            },
            // The oracle-safe merge: no payload / bad frame / wrong key / tamper are one outcome.
            StegoError::NoPayload | StegoError::BadFrame | StegoError::AuthFailed => {
                ApiError::Unauthorized
            }
            StegoError::UnsupportedVersion { found, supported } => {
                ApiError::IncompatibleVersion { found, supported }
            }
            StegoError::OutputExists => ApiError::OutputExists,
            // Path-free, centralized in sv-types so this stays byte-identical with the vault boundary.
            StegoError::Io(_) => ApiError::io_generic(),
            StegoError::DetectorTimeout => ApiError::Timeout,
            StegoError::InvalidOptions(detail) => ApiError::InvalidInput { detail },
            StegoError::Internal => ApiError::Internal,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn extract_failures_all_merge_to_one_unauthorized_code() {
        // The oracle-safety property: no-payload, bad-frame, and auth-failed are indistinguishable.
        for e in [
            StegoError::NoPayload,
            StegoError::BadFrame,
            StegoError::AuthFailed,
        ] {
            let api = ApiError::from(e);
            assert_eq!(api, ApiError::Unauthorized);
            assert_eq!(api.code(), "SV-UNAUTHORIZED");
        }
    }

    #[test]
    fn the_three_merged_variants_render_an_identical_message() {
        // Not just the same code — the same Display string, so the text cannot be an oracle either.
        let msgs: Vec<String> = [
            StegoError::NoPayload,
            StegoError::BadFrame,
            StegoError::AuthFailed,
        ]
        .iter()
        .map(|e| e.to_string())
        .collect();
        assert!(msgs.iter().all(|m| m == &msgs[0]));
    }

    #[test]
    fn file_facts_and_counts_stay_distinct_and_non_secret() {
        // Missing input and oversized input are benign, non-secret file facts.
        assert_eq!(ApiError::from(StegoError::NotFound), ApiError::NotFound);
        assert_eq!(
            ApiError::from(StegoError::FileTooLarge {
                limit_bytes: 10,
                actual_bytes: 99
            }),
            ApiError::TooLarge {
                limit_bytes: 10,
                actual_bytes: 99
            }
        );
        // Undecodable / unsupported are facts about the file, not the secret.
        assert_eq!(
            ApiError::from(StegoError::CoverUndecodable),
            ApiError::Malformed
        );
        assert_eq!(
            ApiError::from(StegoError::UnsupportedCoverFormat),
            ApiError::Malformed
        );
        // Capacity surfaces the actionable limit/actual.
        assert_eq!(
            ApiError::from(StegoError::CapacityExceeded {
                capacity: 100,
                needed: 250
            }),
            ApiError::TooLarge {
                limit_bytes: 100,
                actual_bytes: 250
            }
        );
        // Version is framing, surfaced distinctly.
        assert_eq!(
            ApiError::from(StegoError::UnsupportedVersion {
                found: 9,
                supported: 1
            }),
            ApiError::IncompatibleVersion {
                found: 9,
                supported: 1
            }
        );
        // I/O is path-free.
        assert!(matches!(
            ApiError::from(StegoError::Io("read /home/u/secret.png failed".into())),
            ApiError::Io { detail } if !detail.contains("secret")
        ));
        assert_eq!(
            ApiError::from(StegoError::OutputExists),
            ApiError::OutputExists
        );
        assert_eq!(
            ApiError::from(StegoError::DetectorTimeout),
            ApiError::Timeout
        );
        assert_eq!(
            ApiError::from(StegoError::InvalidOptions("bad".into())),
            ApiError::InvalidInput {
                detail: "bad".into()
            }
        );
        assert_eq!(ApiError::from(StegoError::Internal), ApiError::Internal);
    }
}
