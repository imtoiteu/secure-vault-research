# Secure Vault — Desktop shell (Tauri 2)

The GUI/runtime over the audited core. This crate is **intentionally excluded** from the
parent Cargo workspace (`exclude = ["desktop"]`) so Tauri's large, platform-specific (webview)
dependency tree never enters the core's `build`/`test`/`deny` gates. It depends on the core
crates by path and adds only thin glue:

- [`src/lib.rs`](src/lib.rs) — `#[tauri::command]` wrappers (1:1 with `sv_app::CommandSurface`),
  backend wiring, and the Tauri builder. **No business logic** — crypto, sessions, the
  oracle-safe error taxonomy, and passphrase hygiene all live in the core crates.
- [`frontend/`](frontend/) — a dependency-free static UI (`withGlobalTauri`, no npm bundler).
  A tabbed shell over the full command surface: **Open/Create** (with optional recovery
  policy), **Recover with shares**, offline **Verify & integrity** when locked; and **Items**,
  **Recovery shares** (Shamir split), **Sign**, and **Settings** (change passphrase, export the
  signing public key) when unlocked. After unlock it shows a metadata banner driven by the
  read-only `vault_meta` command (uuid, item count, format, KDF cost, recovery policy). It
  renders only the oracle-safe `SV-…` error codes and never holds key material — just the
  opaque `SessionHandle`.
- [`tauri.conf.json`](tauri.conf.json), [`capabilities/`](capabilities/), [`build.rs`](build.rs).

## Architecture

```
frontend (webview)  ──invoke──▶  #[tauri::command] (this crate)
                                      │ tauri::State<AppVault<AgePayloadCipher>>
                                      ▼
                                 sv_app::CommandSurface  ──▶  VaultBackend  ──▶  sv-core / sv-crypto / sv-age
                                 (IpcPassphrase → SecretBytes; VaultError → coded ApiError)
```

The frontend only ever holds an opaque `SessionHandle` and coded `ApiError`s — **no secret
crosses the boundary** (beyond the documented passphrase-entry residual, see
`../docs/M6-IPC-DECISIONS.md` §N1).

## Prerequisites

- The Tauri 2 toolchain and **platform webview dev libraries** (e.g. `libwebkit2gtk-4.1-dev` +
  `libsoup-3.0-dev` on Debian/Ubuntu; WebKit ships with macOS; WebView2 on Windows). See
  <https://tauri.app/start/prerequisites/>.
- `cargo install tauri-cli --version '^2'` (for `cargo tauri dev`).
- The `age` and `age-keygen` binaries (the payload cipher). For a real build, drop them in
  [`binaries/`](binaries/) (see that README) so they are hashed, pinned, and bundled. For quick
  dev runs you can instead point at them with `SV_AGE_BIN` / `SV_AGE_KEYGEN_BIN`.

## Run

```sh
cd desktop
# Dev: place binaries in ./binaries (pinned + bundled), or override the path:
SV_AGE_BIN=/path/to/age SV_AGE_KEYGEN_BIN=/path/to/age-keygen cargo tauri dev
# or, without the CLI:
SV_AGE_BIN=… SV_AGE_KEYGEN_BIN=… cargo run
```

## Bundling & pinning the `age` toolchain (wired)

1. Put the build-host platform's `age`/`age-keygen` in [`binaries/`](binaries/).
2. [`build.rs`](build.rs) BLAKE3-hashes each and embeds the **pin** as a compile-time env var.
3. `bundle.resources` (in [`tauri.conf.json`](tauri.conf.json)) bundles `binaries/*` into the app.
4. At startup the app resolves each binary (env override → resource dir → next to the exe),
   ensures it is executable, and **verifies its hash against the pin** before use — `age` via
   `AgeCipher::new_pinned`, `age-keygen` via an explicit check (the payload cipher drives it).
5. **Fail-closed:** if a binary was absent at build time (`dev-unpinned`), a **release** build
   refuses to run; a debug build runs unpinned with a runtime warning.

## Verification status

This crate is **scaffolded but not compiled in the core CI environment** (which has no webview
toolchain and builds offline). The parent workspace — the entire audited core and its 75 tests
— remains green and is unaffected by this crate. Build and run the shell on a developer machine
with the Tauri prerequisites above.

## Remaining production items

- **age-binary pinning + bundling** — **done** (see above): hashed at build time, bundled as a
  resource, verified at runtime, fail-closed in release.
- **Installers / icons.** `bundle.active` is `false`; run `cargo tauri icon` and set it `true`
  to produce signed installers (`.dmg`/`.msi`/`.AppImage`). The resource pinning above already
  works in `cargo tauri dev`.
- **Native passphrase entry** (`../docs/M6-IPC-DECISIONS.md` §N1, deferred): the passphrase still
  crosses the JSON IPC bridge. A native OS prompt or keychain integration would close that
  residual.
- **Capabilities.** Review `capabilities/default.json` against the commands actually used.
