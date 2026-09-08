//! Mobile composition root (Android + iOS).
//!
//! No subprocess is possible here: iOS forbids spawning executables outright, and Android
//! blocks exec of app-writable binaries. Two consequences, and nothing else changes:
//!
//!   * the vault payload cipher is the in-process [`RustAgePayloadCipher`]. The wire format is
//!     the same age v1, proven bidirectionally against the real Go binary by `sv-age-rs`'s
//!     `interop` test and at container level by `sv-app`'s `vault_interop` test — so a vault
//!     written on desktop opens here and vice versa;
//!   * the Analysis module is composed **disabled**. `MetaApp::disabled()` is not a new
//!     affordance invented for mobile: it is the existing fail-closed state desktop already
//!     uses when its pinned ExifTool is absent or fails its pin check, so the frontend's
//!     `metadata_available` probe disables those screens with no new UI code.
//!
//! There is no binary to resolve and therefore no pin to verify — the tamper-evidence control
//! that `compose::desktop` implements has no subject on this platform.

use sv_app::{AppVault, MetaApp, RustAgePayloadCipher, VaultBackend};

/// The concrete, thread-safe vault backend managed by Tauri on mobile.
pub type Backend = AppVault<RustAgePayloadCipher>;

/// Compose the vault backend. Infallible on mobile: nothing to resolve, nothing to pin.
pub fn backend(_app: &tauri::AppHandle) -> Result<Backend, String> {
    Ok(AppVault::new(VaultBackend::new(RustAgePayloadCipher::new())))
}

/// The Analysis module cannot exist on mobile (ExifTool is a Perl program). Fail closed.
pub fn meta(_app: &tauri::AppHandle) -> MetaApp {
    MetaApp::disabled()
}
