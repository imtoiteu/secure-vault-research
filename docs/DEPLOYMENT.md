# Secure Vault — Deployment & Validation Plan

Status: **operational guide** (no code/feature changes). Describes how to build, package, sign,
and validate the desktop product for real-world execution, and how to run it locally for the
first time on macOS.

This document is descriptive of the *current* repository. Where a step requires a release-time
configuration edit (icons, `bundle.active`, signing identities), that edit is given explicitly
and is **not** applied to the committed defaults — the default state keeps `cargo build` /
`cargo test` of the audited core green and Tauri excluded.

---

## 0. Architecture recap (what already exists)

- The audited core is a Cargo workspace (`crates/*` + `src-tauri` = the `sv-app` crate). The
  Tauri GUI lives in [`desktop/`](../desktop/), which is **`exclude`d** from the workspace
  ([`Cargo.toml`](../Cargo.toml) `exclude = ["desktop"]`) so the webview dependency tree never
  enters the core's `build`/`test`/`deny` gates.
- The `age` toolchain is an **external dependency**, not first-party code. It is:
  1. **hashed at build time** — [`desktop/build.rs`](../desktop/build.rs) BLAKE3-hashes
     `binaries/age` and `binaries/age-keygen` (or the `SV_AGE_BIN_SRC` / `SV_AGE_KEYGEN_BIN_SRC`
     overrides) and embeds each as a compile-time pin (`SV_AGE_BLAKE3_PIN`,
     `SV_AGE_KEYGEN_BLAKE3_PIN`). A missing binary emits the `dev-unpinned` sentinel + a warning.
  2. **bundled as a resource** — `bundle.resources: ["binaries/**/*"]` in
     [`tauri.conf.json`](../desktop/tauri.conf.json) (the recursive glob also carries ExifTool's
     sibling `lib/` tree; see below).
  3. **verified at runtime** — [`desktop/src/lib.rs`](../desktop/src/lib.rs) resolves each binary
     (the `SV_AGE_BIN` / `SV_AGE_KEYGEN_BIN` env override **in debug builds only** → Tauri resource
     dir → next to the executable), ensures it is executable, and checks its BLAKE3 against the pin
     (`AgeCipher::new_pinned` for `age`; an explicit check for `age-keygen`) before first use.
  4. **fail-closed in release** — an unpinned binary is tolerated only in `debug_assertions`
     builds; a release build refuses to start unpinned. A release build also ignores the `SV_*_BIN`
     runtime path overrides (they are honored only in debug), resolving solely from the bundle.
- **ExifTool** (the **Analysis** module's engine) is **bundled into the app package and resolved from
  app resources — no env var, no external setup, no repository-relative path at runtime.** `build.rs`
  `stage_exiftool` copies the ExifTool distribution into `binaries/` on first build (the `exiftool`
  Perl script **plus its sibling `lib/` tree** on Unix; the self-contained `windows_exiftool` PAR exe
  on Windows), source = the in-repo `metadata/exiftool` clone or `SV_EXIFTOOL_DIST_SRC`. It is then
  BLAKE3-pinned into `SV_EXIFTOOL_BLAKE3_PIN` and bundled via `bundle.resources` (`binaries/**/*`,
  which carries the whole `lib/` tree as a sibling of the script). At runtime
  [`desktop/src/lib.rs`](../desktop/src/lib.rs) `build_meta` resolves it (the `SV_EXIFTOOL_BIN`
  override is honored first **in debug builds only**, then the **bundled resource dir**, then next to
  the executable — a release build resolves solely from the bundle) and verifies it via
  `sv_meta::ExifTool::new_pinned`. The hardened runner adds `-config ""` (disables
  ExifTool's executable-Perl config — the one attacker-controllable RCE surface), a throwaway cwd,
  `env_clear` (re-adding only a fixed `PATH=/usr/bin:/bin` on Unix so the script's `#!/usr/bin/env perl`
  finds system Perl), and a wall-clock timeout. **One deliberate difference from `age`:** ExifTool is an
  *optional* module, so a missing / unpinned (in release) / hash-mismatched binary **disables the
  Analysis module** (every `metadata_*` command then returns the fail-closed `SV-INTERNAL`) rather than
  aborting startup — the rest of the toolkit runs. See
  [metadata/EVALUATION.md](../../metadata/EVALUATION.md) §1.5 (security) and §4 (architecture).
- The frontend is dependency-free static files (`app.withGlobalTauri: true`), so **no Node/npm
  bundler step** is part of the build.

### Version axes (already frozen)

| Axis | Source of truth | Meaning |
| --- | --- | --- |
| App version | `desktop/Cargo.toml` `version` + `tauri.conf.json` `version` (`0.1.0`) | marketing/installer version |
| `FORMAT_VERSION` | `sv_core::format` | `.svault` container structure |
| `CipherSuite` / `SUITE_VERSION` | `sv_core` | crypto suite |
| `CONTRACT_VERSION` | `sv_types` (`1`) | IPC/DTO contract |

Keep `desktop/Cargo.toml` and `tauri.conf.json` `version` fields in lock-step on every release.

---

## 1. Prerequisites

| | macOS | Windows |
| --- | --- | --- |
| Rust | 1.96+ (`rust-version = "1.96"`) | same |
| Webview | system WebKit (built in) | **WebView2 runtime** (preinstalled on Win 11; ship the bootstrapper for Win 10) |
| Toolchain | Xcode Command Line Tools (`xcode-select --install`) | MSVC Build Tools + Windows 10/11 SDK |
| Tauri CLI | `cargo install tauri-cli --version '^2' --locked` | same |
| Bundler tools | built in (`hdiutil`, `productbuild`) | WiX 3 (MSI) and/or NSIS — Tauri CLI fetches NSIS automatically |

> **Cross-compilation is not supported here.** Build macOS artifacts on macOS and Windows
> artifacts on Windows (Tauri bundling and OS code-signing are host-bound). Use a CI matrix
> (e.g. `macos-14` + `windows-latest` runners), not a single host.

---

## 2. `age` / `age-keygen` packaging

The bundled binaries must match the **build target's OS and architecture** exactly (the runtime
runs them as subprocesses; an arch mismatch fails immediately).

### 2.1 Acquire (per target)

Official releases: <https://github.com/FiloSottile/age/releases>. Pick a fixed version (example
below uses `v1.2.1`; check for the latest stable before a release and pin it).

| Build host | Asset |
| --- | --- |
| macOS Apple Silicon | `age-v1.2.1-darwin-arm64.tar.gz` |
| macOS Intel | `age-v1.2.1-darwin-amd64.tar.gz` |
| Windows x64 | `age-v1.2.1-windows-amd64.zip` |

Each archive extracts to an `age/` directory containing `age` and `age-keygen`
(`age.exe` / `age-keygen.exe` on Windows).

Alternative for **local dev only**: `brew install age` (macOS) provides both at
`/opt/homebrew/bin`. Homebrew binaries are fine for `tauri dev` via the env overrides (§Quickstart),
but for a shippable, pinned, bundled build use a **fixed downloaded version** so the embedded pin
is reproducible.

### 2.2 Verify provenance (required before bundling — CLAUDE.md evidence standard)

Download the release's `age-v1.2.1-SHA256SUMS`, then check the archive hash against it:

```sh
# macOS
shasum -a 256 age-v1.2.1-darwin-arm64.tar.gz
grep darwin-arm64 age-v1.2.1-SHA256SUMS    # the two hashes must match
```

```powershell
# Windows
Get-FileHash age-v1.2.1-windows-amd64.zip -Algorithm SHA256
Select-String windows-amd64 age-v1.2.1-SHA256SUMS
```

Record the verified upstream version + SHA-256 in the release notes. After placement, the
build-time BLAKE3 pin (§2.3) becomes the *internal* integrity anchor for the bundle.

### 2.3 Place + pin

Copy the two executables into [`desktop/binaries/`](../desktop/binaries/) (git-ignored — see that
folder's README):

```sh
# macOS arm64 example
tar xzf age-v1.2.1-darwin-arm64.tar.gz
cp age/age age/age-keygen desktop/binaries/
chmod +x desktop/binaries/age desktop/binaries/age-keygen
```

On the next `cargo tauri build`/`dev`, `build.rs` hashes them and embeds the pins; the bundler
copies them into the app's resource directory; the runtime verifies them. To hash a binary that
lives elsewhere without copying, set `SV_AGE_BIN_SRC` / `SV_AGE_KEYGEN_BIN_SRC` to its path at
build time.

---

## 3. macOS build

```sh
cd desktop

# Dev (debug, unpinned-OK): see the Quickstart in §8 for the binary/env setup.
cargo tauri dev

# Release app + bundle (requires binaries placed per §2.3 and icons per §5):
cargo tauri build
```

- Output app: `desktop/target/release/bundle/macos/Secure Vault.app`
- Output disk image (when `dmg` is a target): `desktop/target/release/bundle/dmg/Secure Vault_0.1.0_aarch64.dmg`
- **Architecture:** the artifact is single-arch matching the host (`aarch64` on Apple Silicon).
  For a universal app, build `--target universal-apple-darwin` **and** bundle a universal `age`
  binary (`lipo`-merged arm64+amd64), since a single-arch `age` would break on the other arch.
  Simpler and recommended: ship **two per-arch builds** (arm64, x86_64) with matching per-arch
  `age` binaries.

---

## 4. Windows build

```powershell
cd desktop
cargo tauri dev                 # debug, unpinned-OK
cargo tauri build               # release + installers (icons + §5 config required)
```

- MSI (WiX): `desktop\target\release\bundle\msi\Secure Vault_0.1.0_x64_en-US.msi`
- NSIS:      `desktop\target\release\bundle\nsis\Secure Vault_0.1.0_x64-setup.exe`
- `desktop/src/main.rs` already sets `windows_subsystem = "windows"` for release (no console
  window). Ship/assume the **WebView2 runtime**; for Windows 10 targets configure
  `bundle.windows.webviewInstallMode` to embed or download the bootstrapper.

---

## 5. Installer generation

Bundling is **enabled** (`bundle.active: true`), so `cargo tauri build` produces the app package —
this is what the local ExifTool/age end-to-end verification and internal distribution use. **The
emitted installers are unsigned until H5 (signing/notarization) is addressed; do not distribute them
externally** (see [SIGNING-REQUIREMENTS.md](SIGNING-REQUIREMENTS.md)). The `bundle` block in
[`desktop/tauri.conf.json`](../desktop/tauri.conf.json) currently reads:

```jsonc
"bundle": {
  "active": true,
  "targets": "all",                     // per-host: emits .dmg/.app on macOS, .msi/.nsis on Windows
  "icon": [
    "icons/32x32.png", "icons/128x128.png", "icons/128x128@2x.png",
    "icons/icon.icns", "icons/icon.ico"
  ],
  "resources": ["binaries/**/*"]        // bundles the age toolchain + ExifTool (script + lib/ tree)
}
```

The icon set is wired (real `.png`/`.icns`/`.ico` files in `desktop/icons/`, an **interim** brand
set — regenerate with `cargo tauri icon path/to/Secure-Vault-1024.png` when final art lands). `targets: "all"`
emits whatever the **host** OS supports (you cannot emit a `.dmg` on Windows or an `.msi` on macOS);
narrow it to e.g. `["dmg", "app"]` if you want a specific subset.

---

## 6. Code-signing considerations

Unsigned apps are quarantined (macOS Gatekeeper) or SmartScreen-flagged (Windows). For
distribution outside a controlled test group, sign + (macOS) notarize.

### 6.1 macOS — Developer ID + notarization

- Need an Apple Developer account, a **Developer ID Application** certificate, and an app-specific
  password / API key for notarization.
- Tauri reads signing/notarization from env at `cargo tauri build`:
  `APPLE_SIGNING_IDENTITY` (or `APPLE_CERTIFICATE` + `APPLE_CERTIFICATE_PASSWORD`), and
  `APPLE_ID` + `APPLE_PASSWORD` + `APPLE_TEAM_ID` (or `APPLE_API_KEY*`). Set
  `bundle.macOS.signingIdentity` / `entitlements` in config as needed (Hardened Runtime is
  required for notarization).
- **Nested executables matter.** `age` and `age-keygen` are Mach-O executables shipped inside the
  app's `Resources`. Every nested Mach-O must be signed for notarization to pass. Two options:
  1. Sign them in a pre-bundle step with the same Developer ID, *then* let Tauri sign the app, **or**
  2. Migrate them from `bundle.resources` to **`bundle.externalBin` (sidecars)**, which Tauri
     signs as part of the app — note this renames binaries with the target triple and would
     require updating `resolve_binary` in `desktop/src/lib.rs`, so treat it as a tracked
     follow-up, not a release-day change.
- Verify post-build: `codesign --verify --deep --strict "Secure Vault.app"` and
  `spctl -a -vv "Secure Vault.app"`; confirm `xcrun notarytool history` shows `Accepted` and the
  ticket is stapled (`xcrun stapler validate`).

### 6.2 Windows — Authenticode

- Need a code-signing certificate (OV/EV, or Azure Trusted Signing). Configure
  `bundle.windows.certificateThumbprint` + `digestAlgorithm` + `timestampUrl`, or sign the MSI/EXE
  post-build with `signtool sign /fd sha256 /tr <rfc3161-url> /td sha256 ...`.
- Sign the bundled `age.exe` / `age-keygen.exe` **before** they are packaged so the installer's
  payload is fully signed.

### 6.3 Tauri updater signature (distinct from OS signing)

Tauri's auto-updater uses its **own** minisign keypair (`tauri signer generate`) to sign update
artifacts — separate from Gatekeeper/Authenticode. The current build ships **no updater**, so this
is out of scope until an update channel is added. The vault's *own* minisign signing key (for
signing user files) is unrelated to both.

---

## 7. Release artifact structure

Per platform/arch, publish the installer plus integrity metadata. Suggested layout for a tagged
release `vX.Y.Z`:

```
secure-vault-vX.Y.Z/
├── macos-arm64/
│   ├── Secure Vault_X.Y.Z_aarch64.dmg          # signed + notarized
│   └── Secure Vault_X.Y.Z_aarch64.dmg.sha256
├── macos-x86_64/
│   ├── Secure Vault_X.Y.Z_x64.dmg
│   └── Secure Vault_X.Y.Z_x64.dmg.sha256
├── windows-x64/
│   ├── Secure Vault_X.Y.Z_x64_en-US.msi         # Authenticode-signed
│   ├── Secure Vault_X.Y.Z_x64-setup.exe         # NSIS, signed
│   └── *.sha256
├── SHA256SUMS                                    # all artifacts
└── RELEASE_NOTES.md                              # app ver, FORMAT/SUITE/CONTRACT vers,
                                                  # bundled age version + upstream SHA-256 + BLAKE3 pins
```

Generate checksums: `shasum -a 256 *` (macOS) / `Get-FileHash` (Windows). Optionally sign
`SHA256SUMS` with the maintainer's minisign key and publish the public key out-of-band. Record in
`RELEASE_NOTES.md`: app version, the three internal version axes, and the exact `age` upstream
version + verified SHA-256 + the embedded BLAKE3 pins (from the `build.rs` output).

---

## 8. Validation plan

Run in order; do not ship if any gate is red.

### 8.1 Core gates (audited workspace — run from repo root)

```sh
cargo fmt --all --check
cargo clippy --workspace --all-targets -- -D warnings
cargo build --workspace --locked
cargo test --workspace            # 253 tests: 249 pass; 4 are #[ignore] age/ExifTool e2e (set SV_AGE_BIN[_KEYGEN] to run them). Desktop crate adds 1 parity test, run separately.
cargo deny check
```

The age-backed end-to-end test is skipped unless `age` is provided:

```sh
SV_AGE_BIN=$(command -v age) SV_AGE_KEYGEN_BIN=$(command -v age-keygen) \
  cargo test -p sv-app age_backed_lifecycle_roundtrips -- --nocapture
```

### 8.2 Desktop smoke matrix (per platform, against a real build)

| Flow | Steps | Expected |
| --- | --- | --- |
| Version handshake | launch | header shows app/format/suite/contract versions |
| Create | Open/Create → set path + passphrase (optional recovery policy) → Create | "Created vault …" |
| Unlock | Unlock | banner shows uuid / item count / format / KDF / policy (via `vault_meta`) |
| Add / list / extract | Items → add a file → Extract elsewhere | byte-identical output |
| Lock | Lock | returns to locked view; items unreadable |
| Integrity | Verify & integrity → Check integrity | "Integrity OK" on a good vault |
| Tamper | flip a payload byte, re-check | "FAILED — damaged or tampered" (`SV-CORRUPTED`) |
| Wrong passphrase | unlock with wrong pass | "Wrong passphrase or recovery shares" (`SV-UNAUTHORIZED`) |
| Sign / verify | Sign a file; Settings → show public key → save to `.pub`; Verify | "Signature VALID", and INVALID after editing the file |
| Split / recover | Recovery shares → generate n; Lock; Recover with k share paths | unlocks; too-few shares → `SV-INSUFFICIENT-SHARES{got,need}` |
| Change passphrase | Settings → change; Lock; unlock with new (old fails) | old → `SV-UNAUTHORIZED`, new → unlocks |
| Wrong file | integrity-check a non-vault | "not a Secure Vault" (`SV-MALFORMED`) |

### 8.3 Pinning / fail-closed checks (the deployment-specific gate)

1. **Release refuses unpinned:** build a release bundle with `desktop/binaries/` empty → launching
   it must refuse to start (fail-closed). Confirms `require_dev_build` blocks release.
2. **Tamper rejection:** in a *pinned* build, replace the bundled `age` with a different binary →
   startup must fail with a hash-mismatch error. Confirms `new_pinned` enforces the pin.
3. **Pin provenance:** the BLAKE3 pin printed by `build.rs` matches `b3sum desktop/binaries/age`
   (and matches the value in `RELEASE_NOTES.md`).
4. **Signing (if applied):** §6 verification commands pass (`spctl`/`stapler` on macOS;
   `signtool verify /pa` on Windows).

---

## 9. Manual first-run (developer machine)

A debug `cargo tauri dev` build runs the age toolchain **unpinned** by design (the runtime
fail-closed only applies to *release* builds), so you can launch before any signing/pinning work.
The app resolves the binaries via `SV_AGE_BIN` / `SV_AGE_KEYGEN_BIN` first, so env overrides are the
fastest dev path — no need to copy anything into `desktop/binaries/`.

### macOS
Prereqs on a typical Apple-Silicon box: Xcode Command Line Tools (`xcode-select --install`), Rust,
and `age` (`brew install age`). Then:

```sh
cargo install tauri-cli --version '^2' --locked      # one-time
export SV_AGE_BIN="$(command -v age)"
export SV_AGE_KEYGEN_BIN="$(command -v age-keygen)"
# Analysis module: nothing to do. build.rs auto-stages ExifTool (script + lib/) from the in-repo
# metadata/exiftool clone into desktop/binaries/ on first build, and the runtime resolves it from
# there. Override the staging source with SV_EXIFTOOL_DIST_SRC, or skip staging by pointing
# SV_EXIFTOOL_BIN at any in-tree `exiftool` script. Needs system Perl (`/usr/bin/perl`, on macOS).
cd desktop && cargo tauri dev
```

> The Analysis module is **self-contained**: `build.rs` `stage_exiftool` copies ExifTool into
> `desktop/binaries/` (default source: the `metadata/exiftool/` clone one level above the product
> root `secure-vault/`; override with `SV_EXIFTOOL_DIST_SRC`). A debug build runs it **unpinned**
> (enabled with a warning); a **release** `cargo tauri build` pins the staged binary and bundles it
> (with its `lib/` tree) into the app package, so the packaged app resolves it from app resources
> **with no env var** — verified end-to-end against the in-package binary. Delete `binaries/exiftool`
> + `binaries/lib/` to re-stage from an updated clone.

### Windows (10/11)
Prereqs: Rust (MSVC toolchain) + "Desktop development with C++" build tools; WebView2 (preinstalled
on Win11; install the runtime on Win10); and the `age` toolchain. Get `age` by downloading
`age-vX.Y.Z-windows-amd64.zip` from <https://github.com/FiloSottile/age/releases> (or `scoop install
age`). Then, in **PowerShell**:

```powershell
cargo install tauri-cli --version "^2" --locked      # one-time
$env:SV_AGE_BIN        = "C:\path\to\age.exe"
$env:SV_AGE_KEYGEN_BIN = "C:\path\to\age-keygen.exe"
cd desktop ; cargo tauri dev
```

Notes (both OSes): the first `cargo tauri dev` compiles the full Tauri dependency tree (slow, needs
network) and `build.rs` prints a `dev-unpinned` warning (expected when using env overrides).

**Icons are a hard build requirement** (verified by building the app): `tauri::generate_context!()`
panics at compile time without `desktop/icons/icon.png` —
`failed to open icon …/desktop/icons/icon.png`. The repo ships a real **interim** icon set
(`icons/{icon,32x32,128x128,128x128@2x}.png` plus the `.icns`/`.ico` and Windows Square* tiles) so the
app compiles, runs, and bundles out of the box. **Replace it with final branding before a public
release** via `cargo tauri icon path/to/logo.png` (which regenerates `icon.icns`/`icon.ico` and the
full set for installers). `bundle.icon` is already wired in `tauri.conf.json` (§5), so a regenerated
set is picked up with no further config edit.

Then walk the smoke matrix in §8.2 — it now also exercises the validation fixes: confirm-passphrase
on create (H2), "file already exists" on extract to an existing path (`SV-OUTPUT-EXISTS`, H3), and a
clear `SV-TOO-LARGE` rather than a hang/`SV-INTERNAL` on an oversized add (H1).
```
