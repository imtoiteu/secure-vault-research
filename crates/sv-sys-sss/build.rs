//! Compiles the vendored Daan Sprenkels `sss` hazmat secret-sharing core (`hazmat.c`)
//! into a static library linked into this crate. `randombytes` is NOT compiled here — it
//! is supplied as a C-ABI symbol from Rust (`getrandom`) in `src/lib.rs`, renamed to
//! `sv_sss_randombytes` (see the `.define` below).

fn main() {
    cc::Build::new()
        .file("vendor/hazmat.c")
        .include("vendor")
        // Rename the `randombytes` symbol that `hazmat.c` calls (and `randombytes.h` declares)
        // to a crate-private name. libsodium — linked into the final binary via `sv-sys-sodium`
        // — ALSO exports `randombytes`; the Linux `lld` linker rejects the duplicate definition
        // (macOS `ld` silently tolerates it, which is why this only failed on Linux/Windows CI).
        // Our Rust shim provides `sv_sss_randombytes` instead: same getrandom CSPRNG, no clash.
        // (Macro replacement does not touch the `#include "randombytes.h"` filename.)
        .define("randombytes", "sv_sss_randombytes")
        .warnings(false)
        .compile("sss_hazmat");

    println!("cargo:rerun-if-changed=vendor/hazmat.c");
    println!("cargo:rerun-if-changed=vendor/hazmat.h");
    println!("cargo:rerun-if-changed=vendor/randombytes.h");
}
