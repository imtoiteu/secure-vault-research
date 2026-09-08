# Bundled `age` toolchain

Place the **build-host platform's** `age` and `age-keygen` executables here:

```
binaries/age          (age.exe on Windows)
binaries/age-keygen   (age-keygen.exe on Windows)
```

At build time, [`../build.rs`](../build.rs) BLAKE3-hashes each file and embeds the hash as a
compile-time **pin**. At runtime the app resolves these binaries from the Tauri resource
directory (they are listed under `bundle.resources` in `../tauri.conf.json`) and verifies the
hash before use (`AgeCipher::new_pinned` for `age`; an explicit hash check for `age-keygen`).

If a binary is missing at build time, the build emits a `dev-unpinned` sentinel and a warning:
debug builds then run unpinned (with a runtime warning), and **release builds refuse to run**
(fail-closed).

The binaries themselves are **git-ignored** (large, platform-specific, and not first-party
source). Obtain them from <https://github.com/FiloSottile/age/releases> or build from source,
and verify their provenance before bundling. To use a binary from elsewhere without copying it
here, set `SV_AGE_BIN_SRC` / `SV_AGE_KEYGEN_BIN_SRC` (build-time hashing) and/or
`SV_AGE_BIN` / `SV_AGE_KEYGEN_BIN` (runtime path override). The **runtime** path overrides are
honored in **debug builds only**: a release build ignores them and resolves the binary solely from
the bundled resource dir, so a shipped app can't be redirected to an out-of-bundle toolchain (the
BLAKE3 pin would reject a mismatch regardless — this just closes the resolution surface).

# Bundled `exiftool` (Analysis module)

**Self-staging + bundled.** Unlike `age`, ExifTool needs no manual placement: [`../build.rs`](../build.rs)
(`stage_exiftool`) copies the ExifTool distribution into `binaries/` on the first build, then
BLAKE3-pins `binaries/exiftool` into `SV_EXIFTOOL_BLAKE3_PIN`. `tauri.conf.json` bundles the whole
`binaries/` tree (`resources: ["binaries/**/*"]`) into the app's resource dir, so a packaged build is
**self-contained**: the runtime resolves the binary from app resources and verifies the pin
(`sv_meta::ExifTool::new_pinned`) with **no environment variable and no repository-relative path**.
The `SV_EXIFTOOL_BIN` (runtime) / `SV_EXIFTOOL_BIN_SRC` (build-time pin) overrides still exist but are
no longer required. As with `age`, the **runtime** `SV_EXIFTOOL_BIN` override is honored in **debug
builds only**; a release build resolves ExifTool solely from the bundle.

ExifTool stays an **optional** module: a missing / unpinned-in-release / hash-mismatched binary
**disables** the Analysis module (fail-closed) rather than aborting startup.

**The Perl distribution is a tree, not a lone file.** The `exiftool` Perl script locates its
`Image::ExifTool` modules in a **sibling `lib/` directory** (via its own `$0`), and runs through system
Perl (`/usr/bin/perl` on macOS/Linux; the shebang is `#!/usr/bin/env perl`). The pin hashes only the
script, so staging copies **both** `binaries/exiftool` **and** the whole `binaries/lib/` tree, and the
bundler ships them as siblings under `Contents/Resources/binaries/`. Both are git-ignored (derived
artifacts).

**Staging source / re-staging.** The default source is the in-repo `metadata/exiftool` clone (two
levels up); override with `SV_EXIFTOOL_DIST_SRC=/abs/path/to/exiftool-dist`. Staging is skipped when
`binaries/exiftool` already exists — to refresh from an updated clone, delete `binaries/exiftool` and
`binaries/lib/`, then rebuild.

**Windows.** A real standalone `exiftool.exe` is the **PAR-packed `exiftool(-k).exe`** from the official
ExifTool **Windows ZIP** (<https://exiftool.org>) — self-contained (no `lib/`/Perl). ⚠️ The in-repo
`metadata/exiftool` **clone does NOT contain that exe**: its `windows_exiftool` file is the ExifTool
**Perl source** (a `#!/usr/bin/env perl` script), which Windows cannot execute. `stage_exiftool`
therefore stages `windows_exiftool` to `binaries/exiftool.exe` **only if it is actually a PE (`MZ`)**;
otherwise it **refuses and warns**, and the Analysis module stays disabled (fail-closed) until you
supply the real exe — place the official `exiftool(-k).exe` at `binaries/exiftool.exe`, or point
`SV_EXIFTOOL_DIST_SRC` at a directory whose `windows_exiftool` is a genuine standalone executable.
