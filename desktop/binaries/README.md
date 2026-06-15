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
`SV_AGE_BIN` / `SV_AGE_KEYGEN_BIN` (runtime path override).
