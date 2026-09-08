//! Platform composition roots.
//!
//! The **only** place where desktop and mobile diverge. Desktop resolves and BLAKE3-verifies
//! the bundled `age`/`age-keygen`/`exiftool` binaries exactly as before; mobile cannot spawn
//! subprocesses at all, so it composes the in-process cipher and a disabled Analysis module.
//!
//! Everything below this boundary — the command surface, the vault format, the crypto, the
//! error taxonomy — is identical on every platform. The `Backend` type alias differs only in
//! its `PayloadCipher` type parameter, which is exactly the seam `sv-app` already provided for
//! swapping in `StubPayloadCipher` under test.

#[cfg(desktop)]
mod desktop;
#[cfg(mobile)]
mod mobile;

#[cfg(desktop)]
pub use desktop::{backend, meta, Backend};
#[cfg(mobile)]
pub use mobile::{backend, meta, Backend};
