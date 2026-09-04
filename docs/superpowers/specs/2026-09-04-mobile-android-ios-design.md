# SecureVault Mobile (Android + iOS) — Design

**Date:** 2026-09-04
**Status:** Approved design, pending implementation plan
**Scope:** Extend the existing Tauri 2 desktop application to Android and iOS, sharing one
security core, without breaking the desktop build.

---

## 1. Context

SecureVault today is a Tauri 2 desktop application over an audited Rust core:

```
desktop/frontend  ──invoke──▶  #[tauri::command] (desktop/src/lib.rs)
                                   │
                                   ▼
                              sv_app::CommandSurface        ← the shell-agnostic boundary
                                   │
                                   ▼
        sv-core · sv-crypto · sv-platform · sv-stego · sv-qr · sv-watermark · sv-meta · sv-age
```

Three properties of the existing design make a mobile port tractable, and this spec leans on
all three rather than restructuring anything:

1. **`sv-app` has no `tauri` dependency.** `CommandSurface` (and the `Platform`, `Stego`,
   `Meta`, `Watermark` surfaces) are plain Rust traits. A second shell reuses them unchanged.
2. **`VaultBackend<P: PayloadCipher>` is generic over the payload cipher.** The seam that
   currently distinguishes production (`AgePayloadCipher`) from tests (`StubPayloadCipher`)
   is exactly the seam mobile needs.
3. **`metadata_available` already exists as a fail-closed capability probe**, and the
   frontend already banners and disables the metadata screens when it returns `false`, in
   both locales (`desktop/frontend/main.js`).

### 1.1 Purpose of this work

This is a **research/thesis artifact**, not a store-shipped product. Consequences that shape
every decision below:

- Feature parity is pursued where it is cheap; gaps are **documented and justified** rather
  than engineered around at any cost.
- No store submission workstream (no privacy manifests, no review process, no signing
  identities beyond debug).
- Evidence and honest reporting of what is verified matter more than polish.

---

## 2. Decisions taken

| # | Decision | Rationale |
|---|---|---|
| D1 | Mobile is a **thesis artifact**, not a shipped product | Sets the parity/gap policy |
| D2 | **Android built and verified here; iOS authored, unverified** | Apple's toolchain is macOS-only; this is a Linux host |
| D3 | Keystore/Keychain used for **secure storage only** — no new crypto | Leaves the audited key hierarchy and M0 contract untouched |
| D4 | **Approach A**: reuse the `PayloadCipher` seam, broker files in the shell | Smallest blast radius that still delivers the shared-core claim |
| D5 | Spike the C-dependency cross-compilation **first** | If libsodium would not cross-compile, the whole plan changes |
| D6 | `desktop/` is renamed **`app/`**; one crate serves all platforms | Tauri 2's intended model; makes the one-codebase claim literally true |
| D7 | Accept a **transient plaintext copy** in app-private cache | The cost of A over C; bounded and documented in the threat model |
| D8 | **Auto-lock the session on background** | Deliberate rather than accidental; strictly a security improvement |
| D9 | **One shared frontend**, adapted responsively | Keeps the one-codebase claim; avoids two UIs drifting |
| D10 | No emulator here (no KVM) → **build + QEMU ARM64 tests**, user runs the app | Honest verification boundary |

---

## 3. Spike evidence (completed 2026-09-04)

All four probes were run before this design was written. Toolchain: Android NDK **r28c**,
clang **19.0.1**, target `aarch64-linux-android24`.

| Probe | Command | Result |
|---|---|---|
| Whole core workspace | `cargo build --workspace --target aarch64-linux-android` | **exit 0**, 1m48s, all 13 crates including `sv-app` |
| C dependencies | `cargo build -p sv-crypto --target aarch64-linux-android` | **exit 0**, 5m20s |
| Artifact architecture | `file` on extracted objects | `ELF 64-bit LSB relocatable, ARM aarch64` for both `sv_crypto` and `libsodium.a` |
| Pure-Rust age | scratch crate, `age` 0.12.1 | **exit 0** cross-compiled to ARM64; x25519 round-trip test passes on host |

**Conclusion:** the single largest risk — that `libsodium-sys-stable` and the vendored
`hazmat.c` would not cross-compile — is retired. libsodium builds from source under NDK
clang via its autotools path, AES-NI variants included.

**Caveat, stated explicitly:** `sv-age` and `sv-meta` *compile* for Android because
`std::process` exists there. They cannot *run*: iOS forbids process spawning outright, and
Android blocks exec of app-writable binaries. Compiling is not working. What actually keeps
them out of the mobile graph is the composition root (§5).

### 3.1 Dependency note

`age` 0.12.1 is MIT OR Apache-2.0 (both on the `deny.toml` allowlist), pure Rust, and is the
reference Rust implementation of the age specification. It is **format-compatible** with the
bundled Go binary, so a `.svault` written on desktop opens on mobile and vice versa.

Its own crate description carries a `[BETA]` tag. This must be disclosed in the report
rather than glossed: the desktop build continues to use the hash-pinned Go `age`, and only
mobile — which has no alternative — uses the Rust implementation.

---

## 4. Code structure

```
app/                          ← git mv from desktop/
  src/
    lib.rs                    shared run() + all 38 #[tauri::command] wrappers (unchanged)
    compose/
      mod.rs                  cfg dispatch
      desktop.rs              #[cfg(desktop)] pinned age + exiftool subprocesses
      mobile.rs               #[cfg(mobile)] pure-Rust age; Meta composed unavailable
    broker/                   #[cfg(mobile)] platform URI ⇄ sandbox path brokering
  plugins/svstore/            first-party secure-storage plugin (Kotlin + Swift + Rust)
  frontend/                   one responsive frontend
  gen/android/, gen/apple/    Tauri-generated projects
```

Crates added to the workspace:

- **`sv-age-rs`** — implements `sv_crypto_traits::FileCipher` over the `age` crate. Lives in
  `crates/`, is pure Rust, and enters the audited workspace (unlike `desktop/`, which is
  excluded). Its API mirrors `sv-age` so `AgePayloadCipher` can be parameterised over either.

Nothing else in `crates/` changes.

### 4.1 Rename impact

`desktop/` → `app/` touches: the root `Cargo.toml` `exclude` entry, the `desktop` job in
`.github/workflows/ci.yml`, and path references in `README.md`, `desktop/README.md` and
`docs/`. All mechanical. The desktop application's behaviour is unchanged.

---

## 5. Composition roots

The **only** behavioural divergence between platforms lives here.

### 5.1 Desktop (`#[cfg(desktop)]`) — unchanged

Resolves and BLAKE3-verifies the bundled `age`, `age-keygen` and `exiftool`, exactly as
today. `type Backend = AppVault<AgePayloadCipher>`. The M7 hardening story — hash pinning,
cleared environment, wall-clock timeouts — is untouched.

### 5.2 Mobile (`#[cfg(mobile)]`)

```rust
type Backend = AppVault<RustAgePayloadCipher>;   // sv-age-rs, in-process, no subprocess
let meta = MetaApp::disabled();                  // ExifTool cannot exist here
```

`MetaApp::disabled()` is not a new affordance invented for mobile — it is the existing,
documented fail-closed constructor already used on desktop when the bundled ExifTool is
absent or fails its pin check. Mobile is simply another instance of a state the design
already models.

Consequences, all of which the existing code already handles:

- `metadata_available` returns `false`; the frontend banners and disables the three metadata
  screens using strings that already exist in both locales. **No new UI code.**
- The vault format, KDF parameters, header CBOR, signing keys and share format are
  byte-identical across platforms. Vaults interoperate.
- No binary is bundled on mobile, so there is no pin to verify and no `resolve_binary` path.

---

## 6. File access

### 6.1 The problem

Every `CommandSurface` method takes `path: String` and the core performs `std::fs`
operations on it. Android returns `content://` URIs from the Storage Access Framework; iOS
returns security-scoped URLs. Neither is openable with `std::fs`.

### 6.2 The design — a shell-layer broker, zero core changes

```
picker → content:// URI  ─┐
                          ├─▶ broker stages bytes into <cache>/<random>  ─▶  CommandSurface(path)
security-scoped URL     ─┘                                                          │
                                                                                    ▼
        share sheet / SAF create-document  ◀─ broker exports  ◀─ core writes output path
                                                     │
                                                     ▼
                                       broker shreds staged copies
```

- **Import:** `ContentResolver.openInputStream` (Android) /
  `startAccessingSecurityScopedResource` (iOS), streamed into the app cache directory under
  a random name.
- **Execute:** the unchanged command surface runs against a real filesystem path, so
  `sv-core`'s atomic temp-file-and-rename semantics are preserved exactly.
- **Export:** SAF `ACTION_CREATE_DOCUMENT` or the platform share sheet.
- **Shred:** best-effort overwrite then unlink, on completion and on error paths.

Vault files themselves live in app-private **persistent** storage (not cache), with explicit
import/export through the same broker.

### 6.3 Accepted residual (D7)

A transient plaintext copy of user data exists in app-private cache for the duration of an
operation. Desktop has no equivalent — it writes directly to the user-chosen path.

Mitigations: the cache directory is app-private (not world-readable), covered by platform
file-based encryption at rest, deterministically shredded by the broker, and evictable by
the OS. This is a **real divergence from the desktop threat model** and must appear in the
report's security chapter, not as a footnote.

### 6.4 Space guard

Staging requires free space equal to the input size. The broker checks available space
before staging and returns a coded `ApiError` rather than surfacing a confusing `ENOSPC`
from deep inside the core.

---

## 7. Secure storage plugin (`app/plugins/svstore`)

A first-party Tauri mobile plugin. `tauri-plugin-stronghold` was evaluated and rejected: it
is IOTA's software vault and does **not** use Android Keystore or iOS Keychain, so it would
not demonstrate the platform APIs this work is meant to exercise.

| Layer | Implementation |
|---|---|
| Rust API | `set(key, bytes)`, `get(key)`, `delete(key)`, `list()` |
| Android (Kotlin) | `EncryptedSharedPreferences` + `MasterKey` in AndroidKeystore, AES256-GCM, StrongBox where available |
| iOS (Swift) | Keychain via `SecItemAdd`/`SecItemCopyMatching`, `kSecAttrAccessibleWhenUnlockedThisDeviceOnly`, `kSecAttrSynchronizable = false` |
| Desktop | Not registered at all under `#[cfg(desktop)]` |

**Stores:** persisted SAF URI permission grants, iOS security-scoped bookmark blobs, and the
recent-vault list.

**Never stores:** passphrases, session keys, age identities, or any material from the vault
key hierarchy. Per D3, `sv-core`'s key derivation and the M0 contract are unchanged by this
work.

---

## 8. Session lifecycle

`SessionHandle` maps to in-memory state in `sv-app`. Android terminates backgrounded
processes, which destroys the session silently and leaves the UI holding a stale handle.

Mobile therefore locks explicitly on `onPause` / `didEnterBackground`: the shell calls
`vault_lock`, the UI returns to the locked view, and the next unlock re-prompts predictably.
Desktop behaviour is unaffected.

---

## 9. Mobile UI

One frontend, adapted responsively. Mobile-specific layout keys off a `data-platform="mobile"`
attribute set at runtime plus width media queries, so desktop rendering is untouched.

The existing information hierarchy already suits small screens: Quick start as the launcher,
"All tools" behind a disclosure, and per-screen "More info" collapsibles.

- **Navigation:** the 220px sidebar becomes an off-canvas drawer behind a hamburger. Nineteen
  tools do not fit a bottom tab bar; Home remains the primary launcher.
- **Touch targets:** raised to ≥44px on `.navitem`, `.tile` and buttons.
- **File fields:** an opaque `content://` URI is meaningless in a text box, so mobile renders
  a **chosen-file name chip** beside a primary "Choose file" button. The underlying input
  still carries the broker's staged path, so **`main.js` logic is unchanged**.
- **Safe areas:** `env(safe-area-inset-*)` for notch and home indicator.
- **Identity:** dark theme, palette and SecureVault identity preserved.

---

## 10. Feature coverage

| Module | Desktop | Mobile | Note |
|---|---|---|---|
| Vault: create, unlock, items, meta | ✅ | ✅ | Format-identical, interoperable |
| Vault: sign, recovery shares, change passphrase | ✅ | ✅ | |
| File encrypt / decrypt | ✅ | ✅ | |
| Sign / verify / keygen | ✅ | ✅ | |
| Hash, integrity, verify-download | ✅ | ✅ | |
| Secret sharing: split, recover | ✅ | ✅ | |
| QR transfer | ✅ | ✅ | Photo picker; live camera scanning out of scope |
| Steganography: hide, reveal, detect | ✅ | ✅ | |
| Watermark: embed, verify | ✅ | ✅ | |
| **Metadata: inspect, clean, compare** | ✅ | ❌ | ExifTool is Perl; fails closed via the existing probe |

One module of ten is unavailable on mobile, through an existing, already-translated
fail-closed path.

---

## 11. Security analysis

### 11.1 Unchanged

- Vault format, header CBOR, KDF parameters, suite versions
- Key hierarchy and derivation (`sv-core`, `sv-crypto`)
- The M0 frozen contract and the oracle-safe coded `ApiError` taxonomy
- Passphrase hygiene: `IpcPassphrase`, zeroization, redacted `Debug`
- `SessionHandle` opacity — no secret crosses the IPC boundary
- Desktop's hash-pinned subprocess hardening

### 11.2 Changed on mobile only

| Change | Direction | Note |
|---|---|---|
| Payload cipher is in-process pure Rust, not a pinned subprocess | Mixed | Removes subprocess/binary-tampering surface; adds trust in a `[BETA]`-labelled crate |
| Transient plaintext staged in app-private cache | **Weaker** | §6.3; accepted and documented |
| Session auto-locks on background | **Stronger** | Deliberate rather than accidental |
| SAF grants / bookmarks in Keystore/Keychain | **Stronger** | Hardware-backed at-rest protection for access tokens |
| Metadata module absent | Neutral | Capability reduction, not a weakening |

---

## 12. Testing and CI

The security-critical suite is untouched: `cargo test --workspace` continues to run on host
exactly as today.

Added:

| Job | Runner | Purpose |
|---|---|---|
| `android-core` | `ubuntu-latest` | Cross-compile the workspace per ABI (arm64-v8a, armeabi-v7a, x86_64) |
| `android-arm64-tests` | `ubuntu-latest` | Execute the core test suite on real ARM64 under `qemu-user-static` |
| `ios-core` | **`macos-latest`** | `cargo build -p sv-app --target aarch64-apple-ios` |
| `apk-verify` | `ubuntu-latest` | Static APK inspection: per-ABI `.so`, manifest, declared permissions |

The `ios-core` job matters disproportionately: it gives iOS **machine-verified compilation**
in CI despite no local macOS access.

---

## 13. Verified vs authored

Published in the README and here — not buried.

| | Android | iOS |
|---|---|---|
| Core cross-compiles | ✅ proven locally + CI | ⚠️ CI on `macos-latest` only |
| Core tests on ARM64 | ✅ via `qemu-user-static` | ❌ not run |
| App builds | ✅ APK produced | ⚠️ authored; requires a Mac |
| Runtime: UI, Keystore, pickers, share sheet | ⚠️ authored, unverified | ⚠️ authored, unverified |

**Why:** this host is a VM with no `/dev/kvm` and no nested virtualisation, so the Android
emulator cannot boot; and Apple's toolchain is macOS-only. Keystore, SAF pickers and the
share sheet prove themselves only at runtime and are therefore delivered unverified.

---

## 14. Non-goals

Deliberately excluded to keep this bounded:

- Biometric authentication (scoped out by D3)
- Live camera QR scanning
- A pure-Rust metadata engine to replace ExifTool
- Cloud sync, push notifications, accounts
- App Store / Play Store submission artefacts
- Replacing desktop's `age` subprocess with the Rust implementation

---

## 15. Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Tauri mobile init disturbs the desktop build | Medium | Desktop build + test gate runs on every commit of the port |
| `age` crate `[BETA]` status questioned in review | Medium | Disclosed; desktop keeps the pinned Go binary; format compatibility is verifiable by cross-opening vaults |
| QEMU cannot run Android-target binaries (bionic linkage) | Medium | Fall back to `aarch64-unknown-linux-gnu` for the ARM64 test run; the C and pure-Rust logic is identical |
| Runtime bugs in unverifiable code (Keystore, pickers) | **High** | Explicitly labelled unverified; small, isolated, reviewable surfaces |
| Large-file staging exhausts device storage | Low | Space guard, §6.4 |

---

## 16. Implementation phases

Detailed sequencing belongs in the implementation plan. The intended order:

1. `git mv desktop/ app/`; update `Cargo.toml`, CI, docs. **Desktop must still build and test green.**
2. Add `sv-age-rs`; prove format compatibility by round-tripping a desktop-written vault.
3. Split the composition root into `compose/{desktop,mobile}.rs`. Desktop behaviour unchanged.
4. `cargo tauri android init`; get an APK building with the mobile composition.
5. File broker + space guard.
6. `svstore` plugin (Kotlin + Swift + Rust).
7. Session auto-lock on background.
8. Mobile frontend adaptation.
9. `cargo tauri ios init` + iOS Swift plugin implementation (authored, unverified).
10. CI jobs; QEMU ARM64 test run; README verification matrix.

Every phase ends with the desktop suite green — that is the standing regression gate for the
whole port.
