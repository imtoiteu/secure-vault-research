# Secure Vault — Code-Signing & Notarization Requirements (release gate H5)

**Purpose.** A go/no-go *requirements* checklist for signed, distributable builds. This is the
acquisition + configuration side of the carry-forward blocker **H5 (signing/notarization)**.
The step-by-step *procedure* lives in [DEPLOYMENT.md §6](DEPLOYMENT.md) (signing) and
[§7](DEPLOYMENT.md) (artifact layout); this doc tracks **what must be obtained and set** before
those procedures can run, and the exact pre-flight verification that gates a public release.

> **Current status (2026-06-15): UNSIGNED.** Builds run and pass all code gates, but no
> Developer ID / Authenticode material exists, so artifacts are **not distributable outside a
> controlled test group**. macOS Gatekeeper quarantines unsigned apps; Windows SmartScreen flags
> them. Signing is **not** required for local/dev/internal use (`cargo tauri dev`, or an unsigned
> local build), only for distribution.

---

## 0. Distribution-readiness prerequisites (before any signing applies)

These are independent of signing but block a *bundle* regardless:

- [x] **`bundle.active` is already `true`** in [`desktop/tauri.conf.json`](../desktop/tauri.conf.json)
      — bundling is enabled, so `cargo tauri build` produces the app package (with the pinned `age`
      toolchain and ExifTool shipped via `bundle.resources: ["binaries/**/*"]`). Icons are wired:
      `bundle.icon` references the real `.png`/`.icns`/`.ico` set in `desktop/icons/` (an **interim**
      brand set; final branding still pending). The emitted bundle is **unsigned** until the rest of
      this checklist is met — do not distribute it.
- [ ] **Place the pinned `age` / `age-keygen` binaries** per [DEPLOYMENT.md §2.3](DEPLOYMENT.md)
      (acquire → verify provenance → place under `desktop/binaries/` → BLAKE3-pin). A *release*
      build refuses to run unpinned; today's local builds emit the DEV-UNPINNED warning.
- [ ] Decide architectures/targets to ship (macOS arm64 + x86_64, Windows x64) — see
      [DEPLOYMENT.md §7](DEPLOYMENT.md).

---

## 1. macOS — Developer ID + notarization

### Acquire
- [ ] **Apple Developer Program** membership (USD $99/year; org enrollment can take days — start
      early). Personal Apple ID is not sufficient for Developer ID distribution.
- [ ] **Developer ID Application** certificate (for distributing outside the Mac App Store),
      exported as a `.p12` with its password.
- [ ] **Notarization credential**: either an app-specific password for the Apple ID, **or** an
      App Store Connect **API key** (`.p8` + key id + issuer id). API key is preferred for CI.
- [ ] **Team ID** (10-char, from the Apple Developer account).

### Configure (Tauri reads these from the environment at `cargo tauri build` — see §6.1)
- [ ] `APPLE_SIGNING_IDENTITY` **or** (`APPLE_CERTIFICATE` + `APPLE_CERTIFICATE_PASSWORD`)
- [ ] `APPLE_ID` + `APPLE_PASSWORD` + `APPLE_TEAM_ID` **or** `APPLE_API_KEY` + `APPLE_API_ISSUER`
      (+ the `.p8` path)
- [ ] **Hardened Runtime** enabled and any required `entitlements` set in
      `bundle.macOS` (Hardened Runtime is mandatory for notarization).

### The nested-binary requirement (project-specific — do not skip)
- [ ] **Every nested Mach-O must be signed** or notarization fails. `age` and `age-keygen` ship
      inside the app's `Resources`. Per [DEPLOYMENT.md §6.1](DEPLOYMENT.md), either:
      (a) sign them in a pre-bundle step with the same Developer ID *before* Tauri signs the app, **or**
      (b) migrate them to `bundle.externalBin` (sidecars) — a **tracked follow-up**, not a
      release-day change (it renames binaries with the target triple and requires updating
      `resolve_binary` in [`desktop/src/lib.rs`](../desktop/src/lib.rs)).

### Pre-flight verification (must all pass)
- [ ] `codesign --verify --deep --strict "Secure Vault.app"` → no errors
- [ ] `spctl -a -vv "Secure Vault.app"` → `accepted`, source `Developer ID`
- [ ] `xcrun notarytool history` → submission `Accepted`
- [ ] `xcrun stapler validate "Secure Vault.app"` → ticket stapled

---

## 2. Windows — Authenticode

### Acquire
- [ ] A **code-signing certificate**. Options, cheapest path of trust last:
      - **Azure Trusted Signing** (cloud, subscription) — lowest operational burden, no HSM.
      - **EV (Extended Validation)** cert on hardware token — best SmartScreen reputation,
        immediate; requires the physical token (awkward in CI).
      - **OV (Organization Validation)** cert — works, but SmartScreen reputation accrues over
        time/installs.
- [ ] Certificate **thumbprint** (for the config path) or the signing material for `signtool`.
- [ ] An **RFC-3161 timestamp URL** from the CA (so signatures remain valid after the cert expires).

### Configure (see §6.2)
- [ ] `bundle.windows.certificateThumbprint` + `digestAlgorithm` (`sha256`) + `timestampUrl`,
      **or** sign the MSI/EXE post-build:
      `signtool sign /fd sha256 /tr <rfc3161-url> /td sha256 ...`
- [ ] **Sign the bundled `age.exe` / `age-keygen.exe` *before* packaging** so the installer payload
      is fully signed (same rationale as the macOS nested-binary rule).

### Pre-flight verification
- [ ] `signtool verify /pa /v "Secure Vault_X.Y.Z_x64_en-US.msi"` → verified, chains to a trusted root
- [ ] Timestamp present (signature outlives cert expiry)

---

## 3. CI secrets (if signing in GitHub Actions)

A signing job is **not** wired into [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) yet —
CI today only proves the code gates. When a release/signing job is added, these become repo/Org
**Actions secrets** (never commit any of them):

| Secret | Platform | Notes |
| --- | --- | --- |
| `APPLE_CERTIFICATE` (base64 `.p12`) + `APPLE_CERTIFICATE_PASSWORD` | macOS | Import into a temp keychain in the job |
| `APPLE_API_KEY` (`.p8`) + `APPLE_API_ISSUER` + key id | macOS | Preferred over Apple-ID password for CI notarization |
| `APPLE_TEAM_ID` | macOS | |
| `WINDOWS_CERTIFICATE` (base64) + `WINDOWS_CERTIFICATE_PASSWORD` | Windows | Or Azure Trusted Signing service principal creds |
| Azure Trusted Signing: `AZURE_*` service-principal vars | Windows | If using cloud signing instead of a token |

> EV-on-hardware-token certs generally **cannot** be used in hosted CI (the private key never
> leaves the token). For automated Windows signing, prefer **Azure Trusted Signing** or an OV cert.

---

## 4. Out of scope (do not confuse with OS signing)

- **Tauri auto-updater signature** (`tauri signer generate`, minisign keypair): only relevant once
  an **update channel** ships. No updater today → out of scope ([DEPLOYMENT.md §6.3](DEPLOYMENT.md)).
- **The vault's own minisign file-signing key** (Sign File / Verify Signature feature): a *product
  feature*, unrelated to Gatekeeper/Authenticode/updater signing.

---

## 5. Definition of done (H5 release gate)

H5 is satisfied for a given platform when:

1. Distribution-readiness prerequisites (§0) are met for that platform.
2. The platform's certificate/credentials (§1 or §2) are acquired and configured.
3. A signed (macOS: signed **and** notarized + stapled) artifact is produced.
4. All §1.4 / §2 pre-flight verifications pass on a **clean machine** (one that never built the app),
   to prove Gatekeeper/SmartScreen accept it.
5. Artifacts + checksums are published per [DEPLOYMENT.md §7](DEPLOYMENT.md).

Until then, label distribution **"unsigned — internal/test only."**
