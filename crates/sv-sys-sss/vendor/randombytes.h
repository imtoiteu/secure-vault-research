/*
 * Minimal randombytes.h for the vendored sss `hazmat.c`.
 *
 * The upstream sss repo provides `randombytes` via a git submodule whose source is
 * absent in this checkout (the top-level randombytes.{c,h} are broken symlinks). We
 * instead satisfy the `randombytes` symbol from Rust (the `getrandom` crate, exported
 * with C ABI in this crate's `lib.rs`), which removes the cross-platform C randomness
 * problem. This header only declares the prototype `hazmat.c` includes.
 */
#ifndef sv_RANDOMBYTES_H_
#define sv_RANDOMBYTES_H_

#include <stddef.h>

int randombytes(void *buf, size_t n);

#endif /* sv_RANDOMBYTES_H_ */
