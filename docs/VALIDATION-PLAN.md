# Secure Vault — Practical Validation Plan

Status: **test plan only — no code changes.** Goal: find the bugs a *real user* hits, not prove
the happy path. Each hypothesis below is grounded in the current code (file references); the test
procedures are written to **provoke** the failure, not to confirm success.

How to read this: §1 is a ranked list of concrete bug hypotheses (start here — these are where the
real-user failures most likely are). §2–§7 are the test procedures by category. §8 covers
fixtures, environment, severity rubric, and exit criteria.

> Run against a **real `age`/`age-keygen`** build, not the test stub. The unit suite uses an
> in-memory `StubPayloadCipher`, so it does **not** exercise the subprocess, the 120 s timeout, the
> in-memory buffering, the identity temp file, or `env_clear()` — exactly where the real bugs are.
> See [DEPLOYMENT.md](DEPLOYMENT.md) §8 for the smoke matrix and the `SV_AGE_BIN`/`SV_AGE_KEYGEN_BIN`
> env setup.

---

## 1. Ranked bug hypotheses (most likely real-user failures first)

Severity = likelihood × user impact. "Grounded in" cites the code that creates the risk.

### H1 — Large payloads hit the 120 s age timeout and/or exhaust RAM → opaque failure  · **Critical**
- **Symptom:** adding, extracting, or unlocking a vault with a large payload hangs for up to 120 s
  then fails with **"An internal error occurred." (`SV-INTERNAL`)** — or the app/OS kills it for
  memory.
- **Grounded in:** `sv-age` `run()` buffers the whole input *and* output as `Vec<u8>`; `AgeCipher`
  `DEFAULT_TIMEOUT = 120 s` wall-clock per invocation; `service.rs` reads the source file fully
  (`read_file`), `pack_archive` builds the whole archive in memory, and the payload is one age
  stream. A timeout becomes `AgeError::TimedOut` → `CryptoError::Backend` → `crypto_to_vault` →
  `Internal`. So the size/time cause is **invisible** to the user.
- **Repro:** add a 2 GB, then 5 GB file on a typical 16 GB laptop; watch RSS and wall-clock.
  Re-test on a slow/encrypted disk or an external USB drive (slower → more likely to trip 120 s).
- **Expected vs. risk:** at minimum it should report *why* (too large / timed out), not
  `SV-INTERNAL`; ideally stream instead of buffering. Capture the threshold where it breaks.

### H2 — Vault creation has **no passphrase confirmation** → a typo permanently locks the vault  · **Critical (data loss)**
- **Symptom:** mistype the passphrase once at create time and the vault can **never** be opened.
- **Grounded in:** `frontend/index.html` create form has a single `#passphrase` field;
  `main.js` `vault_create` sends it directly. Only **change-passphrase** has a confirm field.
- **Repro:** create with `correcthorse`, intend `correcthrose`; try to unlock. No recovery path
  (you can't split shares without unlocking first).
- **Expected vs. risk:** create should require confirm-match like change-passphrase does.

### H3 — Extract **silently overwrites** an existing destination file  · **High (data loss)**
- **Symptom:** extracting an item onto an existing path replaces it with no warning.
- **Grounded in:** `service.rs` `extract_item` → `container::write_atomic(dest, …)` → `persist`
  replaces any file at `dest`.
- **Repro:** extract `notes.txt` into a folder that already has `notes.txt`.

### H4 — `age`/`age-keygen` spawned with `env_clear()` → likely **fails on Windows**  · **High (cross-platform)**
- **Symptom (hypothesis):** on Windows, vault create (and all encrypt/decrypt) fails with
  `SV-INTERNAL`; works on macOS/Linux.
- **Grounded in:** `payload.rs` `generate_identity` uses `Command::…env_clear()`; `sv-age` `run()`
  also `.env_clear()`. `age` is a Go binary using `crypto/rand`; on Windows a cleared environment
  removes `SystemRoot`, which the OS loader/CSPRNG (bcrypt / `RtlGenRandom`) typically needs →
  process fails to start or to seed RNG.
- **Repro:** run create + add on a real Windows host. **Verify** — this is a strong hypothesis, not
  yet observed. If confirmed, the fix is to allow-list `SystemRoot`/`SystemDrive` (Windows) rather
  than fully clearing the env.

### H5 — Bundled `age` is quarantined/blocked on a freshly installed app → every op fails  · **High (cross-platform, distributed builds)**
- **Symptom:** a downloaded, installed build fails all crypto on first run (`SV-INTERNAL`), while a
  `cargo tauri dev` build works.
- **Grounded in:** `age`/`age-keygen` ship as `bundle.resources` and run as subprocesses. An
  unsigned/unnotarized macOS app's nested Mach-O is Gatekeeper-quarantined; Windows SmartScreen/
  Defender may block `age.exe`. See [DEPLOYMENT.md](DEPLOYMENT.md) §6 (nested-binary signing).
- **Repro:** build a `.dmg` **without** notarization, install on a clean macOS user account, try to
  create a vault. Repeat on Windows with the unsigned NSIS/MSI.

### H6 — I/O, permission, disk-full, and timeout errors all collapse to `SV-INTERNAL`  · **High (diagnosability)**
- **Symptom:** "An internal error occurred." for disk-full, no-permission, file-locked, path-typo
  (on read), and large-file timeout — the user can't tell a real bug from an environmental issue.
- **Grounded in:** `error.rs` `From<VaultError>`: `Io(_) | Crypto(_) | Internal → ApiError::Internal`.
- **Repro:** create a vault on a full / read-only volume; add a file you don't have read permission
  to; add a file currently locked by another process.

### H7 — Concurrent writes to one vault → lost update (whole-vault read-modify-write)  · **High (data loss)**
- **Symptom:** double-clicking **Add**, or running two operations quickly, silently drops an item;
  two app instances on the same vault clobber each other.
- **Grounded in:** `service.rs` `add_item`/`change_passphrase` read the whole container, decrypt,
  rebuild, and rewrite; the session `Mutex` guards the session map, **not** the file RMW. Tauri
  dispatches commands on a thread pool, so two `add_item`s can interleave; `write_atomic` prevents a
  *torn file* but not a *lost update* (last full rewrite wins).
- **Repro:** script two `item_add` invokes ~simultaneously on the same session; or double-click Add
  on a large file (long op window). Confirm both items survive (expected) vs. one lost (bug).

### H8 — Passphrases are raw bytes with no Unicode normalization → cross-OS unlock mismatch  · **Medium-High (cross-platform)**
- **Symptom (hypothesis):** a passphrase with accents/emoji created on macOS won't unlock the same
  vault on Windows/Linux (and vice-versa).
- **Grounded in:** the passphrase flows `IpcPassphrase → SecretBytes → Argon2` as raw UTF-8; no NFC/
  NFD normalization anywhere. macOS input/filesystems lean NFD, Windows/Linux NFC → different bytes.
- **Repro:** create with passphrase `café🔐` on macOS; copy the `.svault` to Windows; unlock with the
  "same" passphrase typed there. **Verify.**

### H9 — Single-stream re-encryption re-encrypts the **entire** vault on every add  · **Medium (perf/large-file)**
- **Symptom:** once a vault holds a large item, adding even a tiny note is slow and memory-heavy and
  can itself hit H1's timeout; building a vault incrementally is O(n²) in bytes moved.
- **Grounded in:** `add_item` rebuilds the full item set (`archive.item_data(e)?.to_vec()` for every
  existing item) and re-encrypts the whole archive.
- **Repro:** add a 1 GB file, then time adding a 10 KB file.

### H10 — No progress/feedback on long operations → looks hung, users force-quit mid-write  · **Medium (usability → data risk)**
- **Symptom:** during a multi-second/up-to-120 s op the window looks frozen (buttons disabled, no
  spinner); a user force-quits and worries the vault is corrupt.
- **Grounded in:** `main.js` `withButton` only disables the button; the `invoke` is synchronous from
  the UI's view; no progress events. (`write_atomic` does keep the on-disk vault intact across a
  mid-write quit — worth demonstrating to users, but they can't tell.)

### H11 — Splitting shares on a vault created **without** a recovery policy yields unusable shares  · **Medium (recovery)**
- **Symptom:** you generate share files, distribute them, then recovery fails: "vault has no
  recovery policy."
- **Grounded in:** `split_key` writes shares but does **not** set `header.share_policy`; `recover`
  requires `header.share_policy`. The UI lets you split regardless (only a text note warns).
- **Repro:** create **without** recovery → Recovery tab → generate shares → Lock → Recover. Expect a
  clear up-front block; observe whether the shares were a false sense of safety.

### H12 — Plaintext identity temp file can linger if the process is killed mid-decrypt  · **Medium (security/corruption)**
- **Symptom:** an `AGE-SECRET-KEY-1…` file remains in the temp dir after a crash/force-quit.
- **Grounded in:** `sv-age` `SecureIdentityFile` writes the identity `0600` and overwrites+unlinks
  on **Drop**; a kill (SIGKILL / force-quit / power loss) skips Drop.
- **Repro:** force-quit during a large extract (decrypt window); inspect `$TMPDIR` for `sv-age-id-*`.

### H13 — Hand-typed paths everywhere (no native picker) → frequent `SV-NOT-FOUND`/`SV-INTERNAL`  · **Medium (usability)**
- **Grounded in:** all paths are text inputs; extract destination is a `window.prompt`. `~` is not
  expanded; relative paths resolve against the app's working directory (unclear to the user).
- **Repro:** enter `~/Documents/x.svault`; enter a relative path; enter a path with spaces/unicode.

### H14 — Backend accepts an empty passphrase  · **Low (functional)**
- **Grounded in:** `create` validates only the share policy, not passphrase length (the UI blocks
  empty, but the command surface does not).
- **Repro:** call `vault_create` with `""` via the command surface.

---

## 2. Real-world functional testing

Exercise the whole product as a user would, against a real `age` build. (Codes in parentheses are
the expected `ApiError`.)

| # | Scenario | Steps | Expected |
| --- | --- | --- | --- |
| F1 | First-run create→use | create (no policy) → unlock → add 3 mixed files (txt, pdf, png) → list → extract each elsewhere | extracted bytes identical (`b3sum` match) |
| F2 | Reopen across restart | create+add → quit app → relaunch → unlock → list/extract | survives process restart |
| F3 | Round-trip fidelity | add a binary with NUL bytes, a 0-byte file, a file named with unicode/emoji | all extract byte-identical; empty file handled |
| F4 | Duplicate names | add two items both named `report.pdf` | both stored (distinct ids); extract each correctly |
| F5 | Wrong passphrase | unlock with a wrong passphrase | `SV-UNAUTHORIZED`; no hint which credential |
| F6 | Wrong file | integrity-check / unlock a random non-vault file | `SV-MALFORMED` |
| F7 | Change passphrase | change → lock → unlock new (old fails) → items intact | old→`SV-UNAUTHORIZED`, new works |
| F8 | Sign→verify loop | sign a file → Settings export pubkey to `.pub` → verify; then edit file and re-verify | VALID then INVALID |
| F9 | Verify third-party | verify a file signed by a *different* minisign key with the wrong pubkey | INVALID, not a crash |
| F10 | Metadata banner | unlock → check banner vs. truth | uuid/format/KDF/policy/count correct (`vault_meta`) |
| F11 | Empty/edge passphrase | try empty (UI), very long (10 KB), whitespace-only, with newline | consistent behavior; document what's accepted (H14) |
| F12 | Re-add same source | add `a.txt`, modify it on disk, add again as `a.txt` | two independent snapshots; first unchanged |

## 3. Large-file & scale testing (drives H1, H6, H9)

Track for each: wall-clock, peak RSS, success/failure, and the **exact** error surfaced.

| # | Case | Expected/observe |
| --- | --- | --- |
| L1 | Add 100 MB / 500 MB / 1 GB / 2 GB / 5 GB single files | find the size where it slows badly, OOMs, or hits 120 s → `SV-INTERNAL` |
| L2 | Extract each of the above | decrypt path has the same buffering+timeout exposure |
| L3 | Unlock a vault whose total payload is large | unlock decrypts the whole payload to list items — measure |
| L4 | Many small items: add 1k × 1 KB, then 10k | re-pack cost per add grows (H9); directory/UI responsiveness |
| L5 | Big-then-small: add 1 GB, then time adding 10 KB | quantify the O(n) re-encrypt-everything penalty (H9) |
| L6 | Low-RAM host (e.g. 8 GB) + 3 GB file | likely OOM/kill; how is it surfaced? |
| L7 | Slow/external/encrypted volume + 1 GB | higher chance of 120 s timeout; is the cause reported? |
| L8 | Concurrency under load: double-click Add on a 1 GB file | long op window maximizes H7 (lost update) chance |

## 4. Recovery testing (drives H7, H11)

| # | Case | Expected |
| --- | --- | --- |
| R1 | Policy 3-of-5, split, recover with exactly 3 (various combinations) | unlocks with any 3 |
| R2 | Recover with 2 of 3 | `SV-INSUFFICIENT-SHARES {got:2, need:3}` (a count pre-check, not an auth attempt) |
| R3 | Recover with 3 where one is wrong/garbled | `SV-UNAUTHORIZED` (oracle-safe), not "share #2 bad" |
| R4 | Share from a *different* vault mixed in | rejected ("different vault"), clear message |
| R5 | Split on a no-policy vault, then recover | the H11 trap — expect an up-front block; today shares write then recovery fails |
| R6 | Change passphrase, then recover with old shares | shares still recover (they protect the MK, not the passphrase) — confirm |
| R7 | Split mismatch: policy 3-of-5 but split with n=4,k=2 | document what happens (header threshold drives the recover pre-check) |
| R8 | Tamper one byte of a `.svshare` file | rejected as malformed/incompatible, not a crash |
| R9 | Recover a vault while a session is already open on it | both paths behave; no state corruption |

## 5. Corruption & durability testing (drives H6, H10, H12)

| # | Case | Expected |
| --- | --- | --- |
| C1 | Flip 1 byte in the **header** region | `SV-CORRUPTED` (signature fails before passphrase) |
| C2 | Flip 1 byte in the **payload** region | `SV-CORRUPTED` |
| C3 | Replace the **signature trailer** with garbage | `SV-CORRUPTED` |
| C4 | **Truncate** the file at 0 / 10 / 50 / 95 % | `SV-MALFORMED` or `SV-CORRUPTED`; never a panic/hang (fuzz test exists, but re-check via UI) |
| C5 | Bump `FORMAT_VERSION` byte to a future value | `SV-INCOMPATIBLE-VERSION {found,supported}` |
| C6 | Hostile KDF params in header (huge mem/time) | rejected by the pre-unlock ceiling as `SV-CORRUPTED`, not an OOM/hang |
| C7 | **Power-loss simulation:** `kill -9` the app mid-`add` of a large file | original vault still opens (atomic write); verify no partial vault, list unchanged |
| C8 | Disk fills during a write | original vault intact; error surfaced (today `SV-INTERNAL`, H6) |
| C9 | Leftover temp files after a kill | check for `sv-age-id-*` (H12) and `write_atomic` temp files in the vault dir |
| C10 | Concurrent reader+writer | integrity-check while an `add` is mid-flight; no torn read |

## 6. Cross-platform validation (drives H4, H5, H8, H13)

Run the full F/L/R/C matrices on **macOS (arm64 + x86_64)**, **Windows 10 + 11**, and a Linux
distro. Platform-specific probes:

| # | Case | Platform | Watch for |
| --- | --- | --- | --- |
| X1 | Create + add (basic crypto) | **Windows** | H4: `env_clear()` breaking `age`/`age-keygen` (CSPRNG/DLL) → `SV-INTERNAL` |
| X2 | Fresh installed (signed? unsigned?) app, first crypto op | macOS + Windows | H5: Gatekeeper/SmartScreen blocking the bundled subprocess |
| X3 | Vault portability | create on macOS → open on Windows/Linux (and reverse) | container is portable; **passphrase** must still work (H8) |
| X4 | Non-ASCII passphrase portability | each pair of OSes | H8: NFC/NFD byte mismatch |
| X5 | Path styles | Windows | backslashes, drive letters, UNC `\\server\share`, `MAX_PATH` (>260) limits |
| X6 | Path styles | macOS/Linux | `~` not expanded (H13), spaces, unicode, symlinks as source/dest |
| X7 | Executable bit on bundled binary | macOS/Linux | resource copies can lose `+x`; runtime restores it — confirm it actually does post-install |
| X8 | Filesystem quirks | macOS (case-insensitive), Windows (reserved names `CON`, trailing dot/space) | item names / output paths that are legal on one OS, illegal on another |
| X9 | Temp dir on a different volume than the vault | all | identity temp file location vs. `write_atomic` (same-dir temp) — confirm no cross-device assumption breaks |

## 7. Usability issues to capture (drives H2, H3, H10, H13)

Not pass/fail — record friction a real user hits:

- **U1 (→H2):** create has no confirm-passphrase and no strength/feedback; one typo = permanent loss.
- **U2 (→H3):** extract overwrites without a confirmation prompt.
- **U3 (→H10):** no progress bar/spinner; long ops look like a hang; no cancel.
- **U4 (→H13):** every path is hand-typed; no native file/folder picker; `~` unexpanded; relative
  paths resolve against an unclear working dir.
- **U5:** no "reveal passphrase" toggle; no paste affordance shown.
- **U6:** errors are terse codes; `SV-INTERNAL` (the catch-all) gives no next step.
- **U7:** status messages are transient and single-line; a failed multi-step flow loses context.
- **U8:** Lock leaves the vault path populated but clears session state; re-unlock UX.
- **U9:** no confirmation before destructive-feeling actions (change passphrase, overwrite on extract).
- **U10:** the Recovery tab lets you split with no policy and only warns in prose (→H11).
- **U11:** no visible created/modified timestamps, item sizes are bytes (not human units), hashes
  truncated — fine, but note discoverability of "is this the right vault?".

---

## 8. Execution: fixtures, environment, triage

### 8.1 Environment
- Build/run per [DEPLOYMENT.md](DEPLOYMENT.md) §9 with a **real** `age`/`age-keygen`.
- Capture per run: OS+arch, app version, the three version axes (from the banner / `app_info`),
  `age` version, and the BLAKE3 pins.
- Tools: `b3sum`/`shasum` (fidelity), `/usr/bin/time -l` or Task Manager (RSS/time), a hex editor
  (corruption), and a 2-line script to fire two `invoke`s for the concurrency cases.

### 8.2 Fixtures
- Sizes: 0 B, 1 KB, 1 MB, 100 MB, 1 GB, 2 GB, 5 GB.
- Content: random binary (incompressible), text, a file with embedded NULs, deeply nested archive.
- Names: ASCII, spaces, unicode/emoji, Windows-reserved (`CON`, trailing dot), very long.
- Vaults: no-policy; 2-of-3; 3-of-5; one large item; 10k small items; a known-good + a pre-tampered
  copy for each corruption case.
- Passphrases: ASCII, empty, 10 KB, whitespace-only, non-ASCII (`café🔐`) for the NFC/NFD case.

### 8.3 Severity rubric
- **Critical:** data loss, permanent lockout, or all-crypto-broken on a supported platform (H1, H2,
  and H4/H5 if confirmed).
- **High:** silent data loss in a normal flow, or no diagnosable error for a common condition (H3,
  H6, H7).
- **Medium:** correctness/perf cliffs, recovery foot-guns, cross-OS portability gaps (H8–H13).
- **Low:** cosmetic/diagnostic polish (H14, most of §7).

### 8.4 Exit criteria (for declaring the build "user-ready")
1. No **Critical** open. H1 either streams or **fails with a clear, specific message** (size/timeout),
   never bare `SV-INTERNAL`. H2 has confirm-match at create.
2. No **High** silent-data-loss path: extract-overwrite (H3) and concurrent-write (H7) are guarded.
3. Cross-platform: X1 (Windows crypto), X2 (installed-app first run), and X3/X4 (vault + passphrase
   portability) pass on every shipped platform.
4. Corruption set §5 produces the **correct distinct code** (Malformed / Corrupted /
   IncompatibleVersion) and never panics/hangs.
5. Recovery set §4 passes, with R5/R11 (no-policy split) blocked up-front rather than failing late.
6. Every reproduced bug has a ticket with severity, the grounded root cause, and a regression test
   to add **after** fixes are approved.

> When fixes are authorized, prioritize H1, H2, H3, H6, H7 (the Critical/High user-facing set), then
> the cross-platform confirmations H4/H5/H8. This plan intentionally stops at *finding* — no code
> changes are made here.
