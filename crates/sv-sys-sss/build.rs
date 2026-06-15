//! Compiles the vendored Daan Sprenkels `sss` hazmat secret-sharing core (`hazmat.c`)
//! into a static library linked into this crate. `randombytes` is NOT compiled here — it
//! is supplied as a C-ABI symbol from Rust (`getrandom`) in `src/lib.rs`.

fn main() {
    cc::Build::new()
        .file("vendor/hazmat.c")
        .include("vendor")
        .warnings(false)
        .compile("sss_hazmat");

    println!("cargo:rerun-if-changed=vendor/hazmat.c");
    println!("cargo:rerun-if-changed=vendor/hazmat.h");
    println!("cargo:rerun-if-changed=vendor/randombytes.h");
}
