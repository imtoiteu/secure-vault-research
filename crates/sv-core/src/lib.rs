//! # sv-core — vault domain contracts
//!
//! Holds the on-disk [`format`] schema, the [`keys`] hierarchy contract, the
//! [`service`] capability surface, and the [`error`] taxonomy. **No UI/Tauri
//! dependencies** — this crate is pure domain logic and is unit-testable in isolation.
//!
//! The crypto-free shapes are frozen in M0; behaviour lands in M4 (key hierarchy),
//! M5 (container [`format`] + [`container`] framing/sign/verify), and M6
//! (session + service + recovery). Crypto is **injected** (generic over `sv-crypto-traits`),
//! so this crate's production graph stays backend-/FFI-free.

#![forbid(unsafe_code)]

pub mod container;
pub mod error;
pub mod format;
pub mod keys;
pub mod service;

pub use container::{decode, encode, verify_header, OpenedContainer};
pub use error::VaultError;
pub use format::{CipherSuite, VaultHeader, FORMAT_VERSION, MAGIC};
pub use keys::{KeyHierarchy, StdKeyHierarchy, WrapField, SUITE_VERSION};
pub use service::VaultService;
