# Final Report Diagrams — PlantUML version

> PlantUML rendering of the same diagram set as [10-report-diagrams.md](10-report-diagrams.md)
> (Mermaid). Same DIAG numbers, same source-grounded content. Use whichever your report toolchain
> prefers; the Mermaid file is the canonical reference for the captions and facts.
>
> **Render:** `plantuml -tsvg 10-report-diagrams.plantuml.md` (PlantUML reads `@startuml` blocks
> directly), or paste a single `@startuml…@enduml` block into the PlantUML server / IDE plugin. Each
> block is independent.
>
> **Graphviz:** the component/class diagrams (01–06, 08, 22, 23) use Graphviz `dot` by default;
> sequence and activity diagrams (10–20) do not. If you don't have Graphviz installed, either
> `brew install graphviz`, or force the pure-Java engine with `-Playout=smetana` (or add
> `!pragma layout smetana` after `@startuml`). All 23 blocks were syntax-checked and rendered to SVG
> with PlantUML 1.2024.8 (Smetana), exit 0, no errors.
>
> Required set: DIAG-01/02/03/04/05/07/09/10/11/12/13/14/15/17/21. Supporting: 06/08/16/18/19/20/22/23.

---

## DIAG-01 — System Context

```plantuml
@startuml
left to right direction
actor "User\n(local, single host)" as User
node "Desktop host (offline)" {
  rectangle "Security & Privacy Toolkit\n(Tauri 2 desktop app)" as App
  database "OS filesystem\nuser files · .svault · .minisig\nshares · keys · images" as FS
  rectangle "Bundled age / age-keygen\n(BLAKE3 hash-pinned)" as Age
  rectangle "Bundled ExifTool\n(hash-pinned · optional · fail-closed)" as Exif
}
cloud "Internet" as Net
User --> App : file paths, passphrases
App --> FS : read / atomic write
App --> Age : env_clear + timeout subprocess
App --> Exif : env_clear + timeout subprocess
App ..> Net : NO network access
@enduml
```

## DIAG-02 — Layered / Container Architecture

```plantuml
@startuml
top to bottom direction
package "Presentation — desktop/frontend (static withGlobalTauri)" {
  rectangle "index.html · main.js · i18n.js · styles.css\n22 screens · name-based routing · vi/en · CSP no-inline-scripts" as UI
}
package "IPC boundary" {
  rectangle "Tauri invoke · 38 commands · coded ApiError (oracle-safe)\nIpcPassphrase (zeroizing) · paths cross, never secret bytes" as IPC
}
package "Composition root — desktop/src/lib.rs + sv-app" {
  rectangle "run() / Builder · binary resolve + BLAKE3 hash-pin · fail-closed" as CR
  rectangle "Backend (vault)" as MS1
  rectangle "Platform" as MS2
  rectangle "Stego" as MS3
  rectangle "Meta" as MS4
  rectangle "Watermark" as MS5
}
package "Domain crates" {
  rectangle "sv-core\n.svault container" as Core
  rectangle "sv-platform\nvault-free services" as Plat
  rectangle "sv-stego" as Stego
  rectangle "sv-meta" as Meta
  rectangle "sv-qr" as Qr
  rectangle "sv-watermark" as Wm
}
package "Shared cryptographic platform" {
  rectangle "sv-crypto-traits\nbackend-free ABI + secret types" as Traits
  rectangle "sv-crypto\nimpl adapters" as Crypto
  rectangle "sv-types\nDTO + error island (no crypto deps)" as Types
}
package "Backends" {
  rectangle "libsodium (FFI)\nsv-sys-sodium" as Sodium
  rectangle "Shamir sss (vendored FFI)\nsv-sys-sss" as Sss
  rectangle "age subprocess\nsv-age" as AgeB
  rectangle "ExifTool subprocess" as ExifB
}
UI --> IPC
IPC --> CR
CR --> MS1
CR --> MS2
CR --> MS3
CR --> MS4
CR --> MS5
MS1 --> Core
MS2 --> Plat
MS2 --> Qr
MS3 --> Stego
MS4 --> Meta
MS5 --> Wm
Core --> Traits
Plat --> Crypto
Stego --> Crypto
Wm --> Crypto
Crypto --> Traits
Crypto --> Sodium
Crypto --> Sss
MS1 --> AgeB : AgePayloadCipher
Meta --> ExifB
Plat ..> Core : vault NOT yet routed here
@enduml
```

## DIAG-03 — Crate Dependency Graph

```plantuml
@startuml
skinparam linetype ortho
rectangle "sv-types\n(island)" as Types
rectangle "sv-crypto-traits\n(ABI root)" as Traits
rectangle "sv-sys-sodium" as Sodium
rectangle "sv-sys-sss" as Sss
rectangle "sv-crypto" as Crypto
rectangle "sv-age" as Age
rectangle "sv-core" as Core
rectangle "sv-platform" as Plat
rectangle "sv-stego" as Stego
rectangle "sv-watermark" as Wm
rectangle "sv-meta" as Meta
rectangle "sv-qr" as Qr
rectangle "sv-app (src-tauri)" as App
rectangle "desktop\n(workspace-excluded)" as Desktop
Sss --> Traits
Crypto --> Traits
Crypto --> Sss
Crypto --> Sodium
Age --> Traits
Core --> Traits
Core --> Types
Core ..> Crypto : dev-dep only
Plat --> Traits
Plat --> Crypto
Plat --> Types
Stego --> Traits
Stego --> Crypto
Stego --> Types
Wm --> Traits
Wm --> Crypto
Wm --> Types
Meta --> Types
Qr --> Types
App --> Core
App --> Plat
App --> Stego
App --> Meta
App --> Qr
App --> Wm
App --> Age
App --> Crypto
App --> Traits
App --> Types
Desktop --> App
Desktop --> Age
Desktop --> Meta
Desktop --> Types
@enduml
```

## DIAG-04 — Security-Domain Decomposition

```plantuml
@startuml
rectangle "D0 — Cryptographic Platform (foundation)\nsv-crypto-traits · sv-crypto · sv-sys-sodium · sv-sys-sss · sv-age\nBLAKE3 · Argon2id · secretbox · Ed25519/minisign · Shamir · age" as D0
rectangle "D1 Confidential Storage\nsv-core · vault_* item_* (16)" as D1
rectangle "D2 File Confidentiality\nsv-platform · crypto_encrypt/decrypt_file" as D2
rectangle "D3 Authenticity & Provenance\nkeygen · sign · verify_signature" as D3
rectangle "D4 Integrity Verification\nhash · verify_integrity · integrity_check" as D4
rectangle "D5 Escrow & Recovery\nkeys_split/recover · shares_* · qr_*" as D5
rectangle "D6 Data Concealment\nstego_hide/extract/detect" as D6
rectangle "D7 Tamper Evidence\nwatermark_embed/verify" as D7
rectangle "D8 Metadata Hygiene\nmetadata_inspect/sanitize/diff" as D8
D1 --> D0
D2 --> D0
D3 --> D0
D4 --> D0
D5 --> D0
D6 --> D0
D7 --> D0
D8 ..> D0 : subprocess only (no crypto)
note bottom of D0
Forks to keep distinct:
- Encryption: D1 age vs D2 Argon2id+secretbox
- Sharing: D5 vault master-key split vs D5 platform hybrid DEK
end note
@enduml
```

## DIAG-05 — Cryptographic Primitive Stack (trait → impl → backend)

```plantuml
@startuml
left to right direction
package "Traits (sv-crypto-traits)" {
  rectangle "Hasher" as tH
  rectangle "KeyDerivation" as tKD
  rectangle "Kdf" as tKdf
  rectangle "Signer" as tSig
  rectangle "SecretSharer" as tShare
  rectangle "FileCipher" as tFC
  rectangle "secretbox::seal/open\n(free fns, no trait)" as tFn
}
package "Impl adapters (sv-crypto / sv-age)" {
  rectangle "Blake3Hasher" as iH
  rectangle "Argon2Kdf" as iKdf
  rectangle "SodiumMinisignSigner" as iSig
  rectangle "SssSharer" as iShare
  rectangle "AgeCipher" as iFC
  rectangle "secretbox" as iSB
}
package "Backends" {
  rectangle "blake3 (pure-Rust)" as bBlake
  rectangle "argon2 (pure-Rust)" as bArgon
  rectangle "libsodium (FFI)" as bSodium
  rectangle "vendored Shamir (FFI, static C)" as bSss
  rectangle "age CLI (subprocess, pinned)" as bAge
}
tH --> iH
tKD --> iH
tKdf --> iKdf
tSig --> iSig
tShare --> iShare
tFC --> iFC
tFn --> iSB
iH --> bBlake
iKdf --> bArgon
iSig --> bSodium
iSB --> bSodium
iShare --> bSss
iFC --> bAge
@enduml
```

## DIAG-07 — `.svault` Container Byte-Layout

```plantuml
@startuml
left to right direction
rectangle "MAGIC\nb'SVLT' (4 B)" as A
rectangle "FORMAT_VERSION\nu16 LE = 1 (2 B)" as B
rectangle "HEADER_LEN\nu32 LE (4 B)" as C
rectangle "HEADER\nCBOR, HEADER_LEN B (<= 1 MiB)" as D
rectangle "PAYLOAD\nage ciphertext, payload_len B" as E
rectangle "SIG_TRAILER\nminisign signature (remainder)" as F
A -> B
B -> C
C -> D
D -> E
E -> F
note bottom
header_digest  = BLAKE3( MAGIC | VERSION | HEADER_LEN | HEADER )
payload_digest = BLAKE3( PAYLOAD )
binding_root   = BLAKE3( header_digest | payload_digest )
SIG_TRAILER    = minisign-sign( binding_root )   comment = secure-vault v1 container
end note
@enduml
```

## DIAG-09 — Vault Key Hierarchy

```plantuml
@startuml
top to bottom direction
rectangle "passphrase (SecretBytes)" as Pass
rectangle "salt [16] (random, in header)" as Salt
rectangle "Argon2id\n(default 256 MiB / t=3 / p=1)" as Kdf
rectangle "Master Key (Key32, 32 B)\nzeroizing · NEVER on disk · RAM-only" as MK
rectangle "wrap key (Key32)" as WK1
rectangle "wrap key (Key32)" as WK2
rectangle "age X25519 identity" as AgeId
rectangle "Ed25519 signing key" as SignSk
rectangle "secretbox seal" as SB1
rectangle "secretbox seal" as SB2
rectangle "wrapped_age_identity (header)" as W1
rectangle "wrapped_signing_key (header)" as W2
rectangle "k-of-n KeyShares [33 B]" as Shares
rectangle "SVSH envelopes (uuid-bound)\none .svshare per share, OUTSIDE the vault" as Env
Pass --> Kdf
Salt --> Kdf
Kdf --> MK
MK --> WK1 : derive_key  secure-vault/v1/wrap/age-identity:uuid
MK --> WK2 : derive_key  secure-vault/v1/wrap/signing-key:uuid
AgeId --> SB1
WK1 --> SB1
SB1 --> W1
SignSk --> SB2
WK2 --> SB2
SB2 --> W2
MK --> Shares : SssSharer.split(mk, n, k)
Shares --> Env
@enduml
```

## DIAG-10 — Vault Create / Seal

```plantuml
@startuml
autonumber
actor Frontend as UI
participant "VaultBackend (sv-core)" as VB
participant "KeyHierarchy" as KH
participant "AgePayloadCipher" as PC
participant "Signer (minisign)" as SG
database Filesystem as FS
UI -> VB : vault_create(path, passphrase, policy?)
VB -> VB : validate policy · acquire write-lock
VB -> VB : random uuid · salt · KdfParams::default
VB -> KH : derive_master(passphrase, salt, params)
KH --> VB : Master Key (Key32)
VB -> PC : generate_identity() (age-keygen)
PC --> VB : (age identity, recipient)
VB -> SG : generate() Ed25519
SG --> VB : (signing sk, pk)
VB -> VB : wrap identity + signing key (secretbox under derived keys)
VB -> VB : build header · pack ItemDirectory([]) (no compression)
VB -> PC : encrypt(archive, recipient) -> age ciphertext
VB -> VB : header_digest, payload_digest, binding_root (BLAKE3)
VB -> SG : sign(binding_root) -> minisign trailer
VB -> FS : write_atomic(SVLT bytes)
VB --> UI : VaultMeta (non-secret); no session created
@enduml
```

## DIAG-11 — Vault Unlock / Unseal (oracle-safe ordering)

```plantuml
@startuml
autonumber
actor Frontend as UI
participant VaultBackend as VB
participant "container::decode" as CT
participant KeyHierarchy as KH
database Filesystem as FS
UI -> VB : vault_unlock(path, passphrase)
VB -> FS : read (size-capped <= 2 GiB)
VB -> CT : decode(bytes) — parse framing, suite/version
CT -> CT : recompute digests · verify binding-root signature
alt signature invalid / tamper
  CT --> UI : ApiError::Corrupted (NOT an auth oracle)
else signature valid
  VB -> VB : validate_kdf (reject hostile Argon2 cost)
  VB -> KH : derive_master(passphrase, salt, params)
  KH --> VB : candidate Master Key
  VB -> VB : unwrap_secret(AgeIdentity) — credential gate
  alt unwrap MAC fails
    VB --> UI : ApiError::Unauthorized (wrong passphrase)
  else unwrap ok
    VB -> VB : new_session(mk, path) — random 32 B id, RAM-only
    VB --> UI : SessionHandle (opaque; no key crosses IPC)
  end
end
@enduml
```

## DIAG-12 — Standalone File Encrypt / Decrypt (D2 — Argon2id + secretbox)

```plantuml
@startuml
start
partition "encrypt_file (Argon2id + secretbox, NOT age)" {
  :refuse-existing output;
  :read input (capped <= 2 GiB);
  :random salt[16] (getrandom);
  :Argon2id(passphrase, salt) -> BLAKE3 derive_key\ncontext secure-vault/platform/v1/SVENC;
  :secretbox seal (fresh nonce);
  :write SVENC header (magic, ver, algs, params, salt, nonce, ct);
  :zeroize plaintext · write_atomic(output);
}
partition "decrypt_file" {
  :read blob (capped);
  if (magic / version / alg bytes ok?) then (no)
    :Malformed / IncompatibleVersion;
    stop
  else (yes)
  endif
  if (Argon2 params <= ceilings (mem<=4GiB, t<=64, p<=64)?) then (no)
    :Malformed;
    stop
  else (yes)
  endif
  :re-derive key · secretbox open;
  if (MAC ok?) then (no)
    :Unauthorized (wrong passphrase / tamper);
    stop
  else (yes)
    :write_atomic(output) · zeroize plaintext;
  endif
}
stop
@enduml
```

## DIAG-13 — Digital Signature: keygen → sign → verify (D3)

```plantuml
@startuml
autonumber
actor Frontend as UI
participant "PlatformCrypto" as P
participant "Signer (minisign)" as S
database Filesystem as FS
group generate_signing_keypair
  UI -> P : crypto_generate_signing_keypair(out_dir, name, passphrase)
  P -> S : generate() -> (sk, pk)
  P -> FS : write name.pub (pk 64-hex, public)
  P -> P : seal_with_passphrase(SVKEY, sk) (Argon2id+secretbox)
  P -> FS : write name.svkey (encrypted sk; orphan .pub removed on failure)
  P --> UI : PlatformKeypair (paths + pk hex; no secret)
end
group sign_file
  UI -> P : crypto_sign_file(input, signing_key_path, passphrase)
  P -> P : open SVKEY (wrong pass -> Unauthorized) -> sk
  P -> S : sign(data, sk, comment) — BLAKE2b-512 prehash + dual sig
  P -> FS : write input.minisig
  P --> UI : signature path
end
group verify_signature
  UI -> P : integrity_verify_signature(file, sig, pubkey)
  P -> P : parse pubkey hex · BLAKE3(file)
  P -> S : verify(prehash sig, then global sig)
  P --> UI : SignatureCheck{valid, file_blake3_hex} (invalid = Ok(false))
end
@enduml
```

## DIAG-14 — Integrity Verification Decision Flow (D4)

```plantuml
@startuml
start
:verify_integrity(file, expected_hash?, sig?, pubkey?);
if (sig+pubkey partial, or all absent with no hash?) then (yes)
  :InvalidInput;
  stop
else (no)
endif
if (signature requested?) then (yes)
  :verify_signature(file,sig,pubkey)\n-> valid + file_blake3_hex (single read);
else (no)
  :hash_file(file) -> computed_hash\nsignature_valid = false;
endif
if (expected_hash provided?) then (yes)
  :hash_matched = (computed == expected) case-insensitive;
else (no)
  :hash_matched = n/a;
endif
:verified = (not hash_checked OR hash_matched)\nAND (not sig_checked OR signature_valid);
:IntegrityVerification{verified, computed_hash_hex, ...};
stop
@enduml
```

## DIAG-15 — Steganography Embed / Extract Data-Flow (D6)

```plantuml
@startuml
start
partition "stego_hide (encrypt-then-embed)" {
  :decode carrier (format dispatch)\ndecode_bounded: <=30k px, <=1 GiB;
  :capacity guard (whole frame) — fail fast CapacityExceeded;
  :random salt[16];
  :seal: Argon2id(passphrase,salt) -> secretbox\n(SVSTEG 54-B header + ciphertext);
  :write header -> first 432 sites;
  :BLAKE3(salt)-seeded permuted body schedule;
  :write ciphertext LSBs into scheduled sites;
  :lossless re-serialize (PNG/BMP pixels · JPEG entropy-only);
}
partition "stego_extract" {
  :decode carrier;
  :read + validate SVSTEG header (first 432 sites);
  :re-derive body schedule from header salt;
  :read ciphertext from scheduled sites;
  if (secretbox open ok?) then (no)
    :AuthFailed (oracle-safe);
    stop
  else (yes)
    :unframe filename · sanitize basename · write (no overwrite);
  endif
}
stop
@enduml
```

## DIAG-17 — Secret Sharing & Recovery — two pipelines (D5)

```plantuml
@startuml
start
partition "Vault master-key escrow (sv-core)" {
  :unlocked session -> Master Key;
  :SssSharer.split(mk, n, k);
  :SVSH envelopes (uuid-bound) · one .svshare per share;
  :recover: count >= threshold? else InsufficientShares;
  :per-share uuid == header.uuid;
  :combine -> mk -> unwrap credential gate -> new session;
}
partition "Platform hybrid (sv-platform)" {
  :secret / file;
  :random DEK (Key32) + random group_id;
  :payload = secretbox(secret) under derive_key(DEK,group,n,k);
  :SssSharer.split(DEK, n, k);
  :92-B SVSS pieces + payload blob (+ Base64 -> QR);
  :recover: group/n/k agree · reject duplicate-x & zero-x ·\ncount gate · payload_ref binding;
  :combine -> DEK -> secretbox open -> write (sanitized name);
}
stop
@enduml
```

## DIAG-21 — Trust Boundaries & Subprocess Hardening

```plantuml
@startuml
package "Webview (untrusted-input zone)" {
  rectangle "frontend JS\nCSP scripts 'self', no inline\nrenders via textContent (no HTML injection)" as Front
}
package "Capability allowlist (Tauri)" {
  rectangle "core / dialog / opener defaults\nNO fs: / shell: permission to the webview" as Cap
}
package "Native (trusted) — Rust commands" {
  rectangle "38 commands · coded oracle-safe ApiError\nIpcPassphrase zeroizing · no secret in any DTO\nsize caps · bomb limits · atomic refuse-overwrite" as Cmds
}
package "External binaries (hardened subprocess)" {
  rectangle "age / age-keygen — hash-pinned\nenv_clear · 120 s timeout+kill · stdin zeroized" as S1
  rectangle "ExifTool — hash-pinned · env_clear · -config '' (RCE closed)\n60 s timeout+kill · fail-closed if absent" as S2
}
database Filesystem as FS
Front --> Cap : invoke (JSON IPC)
Cap --> Cmds
Cmds --> S1
Cmds --> S2
Cmds --> FS : read / atomic write
note bottom of Cmds
Documented residual: passphrase copies in the serde/JSON IPC bridge
are unreachable for zeroization (mitigate via OS disk/swap encryption,
exclude these commands from arg logging).
end note
@enduml
```

---

# Supporting figures

## DIAG-06 — IPC Command Surface & Managed-State Map

```plantuml
@startuml
left to right direction
rectangle "Frontend\ninvoke() · 38 commands" as F
rectangle "state 1: Backend (vault) — 16" as S1
rectangle "state 2: Platform — 13" as S2
rectangle "state 3: Stego — 3" as S3
rectangle "state 4: Meta — 4" as S4
rectangle "state 5: Watermark — 2" as S5
F --> S1
F --> S2
F --> S3
F --> S4
F --> S5
note right of S1
app_info · vault_create/unlock/lock · vault_meta
vault_change_passphrase · item_list/add/extract
export_signing_public_key · integrity_check/hash
sign_file · verify_file · keys_split · keys_recover
end note
note right of S2
integrity_hash_file · integrity_verify_signature
integrity_verify_integrity · crypto_encrypt/decrypt_file
crypto_generate_signing_keypair · crypto_sign_file
shares_split_secret/file · shares_recover_secret
shares_export_qr · shares_recover_from_qr · copy_file
end note
note right of S3
stego_hide · stego_extract · stego_detect
end note
note right of S4
metadata_inspect · metadata_sanitize · metadata_diff · metadata_available
end note
note right of S5
watermark_embed · watermark_verify
end note
@enduml
```

## DIAG-08 — Vault Header CBOR Data Model

```plantuml
@startuml
class VaultHeader {
  +u16 format_version
  +CipherSuite suite
  +[u8;16] vault_uuid
  +u64 created_unix
  +u64 modified_unix
  +KdfRecord kdf
  +WrappedSecret wrapped_age_identity
  +AgeRecipient age_recipient
  +WrappedSecret wrapped_signing_key
  +[u8;32] signing_public_key
  +Option<SharePolicyRecord> share_policy
  +ContentLayout content_layout
}
class KdfRecord {
  +Salt salt
  +KdfParams params
}
enum KdfParams {
  Argon2id
}
class Argon2idParams {
  +u32 mem_kib
  +u32 time_cost
  +u32 parallelism
}
class WrappedSecret {
  +Vec<u8> nonce
  +Vec<u8> ciphertext
}
class SharePolicyRecord {
  +u8 shares_total
  +u8 threshold
}
class ContentLayout {
  +u64 payload_len
}
class ItemDirectory {
  +Vec<ItemEntry> items
}
class ItemEntry {
  +[u8;16] item_id
  +String name
  +u64 plaintext_offset
  +u64 plaintext_len
  +[u8;32] plaintext_blake3
  +u64 added_unix
}
enum CipherSuite {
  V1
}
VaultHeader --> CipherSuite
VaultHeader --> KdfRecord
VaultHeader --> WrappedSecret
VaultHeader --> SharePolicyRecord
VaultHeader --> ContentLayout
KdfRecord --> KdfParams
KdfParams --> Argon2idParams
ItemDirectory --> ItemEntry
note bottom of ItemDirectory : lives INSIDE the encrypted age payload, not the header
@enduml
```

## DIAG-16 — Steganography Detection Fusion

```plantuml
@startuml
start
:image bytes;
:decode_bounded (<=30k px, <=1 GiB);
if (format?) then (PNG/BMP)
  :spatial panel:\n- AppendedData (binwalk-lite + entropy + magic)\n- ChiSquare (Westfeld-Pfitzmann)\n- RS (Fridrich-Goljan-Du);
else (JPEG)
  :jpeg panel:\n- appended-after-EOI\n- JPEG-DCT chi-square;
endif
:fusion = MAX(signal scores);
switch (max score?)
case ( >= 0.75 )
  :High;
case ( >= 0.45 )
  :Elevated;
case ( >= 0.20 )
  :Low;
case ( < 0.20 )
  :NotObserved (floor);
endswitch
:+ CAVEAT: heuristic, not proof;
stop
@enduml
```

## DIAG-18 — Secure QR Transfer

```plantuml
@startuml
autonumber
actor Frontend as UI
participant PlatformCrypto as P
participant "sv-qr (qrcode/rqrr)" as QR
database Filesystem as FS
group export (make QR)
  UI -> P : shares_export_qr(share_b64[], out_dir)
  loop each piece string (~124 ASCII)
    P -> QR : encode_text_to_png(text, path) — EC level H
    QR -> FS : write one PNG (over-capacity -> TooLargeForQr)
  end
  P --> UI : QrExportReport (paths)
end
group recover from QR
  UI -> P : shares_recover_from_qr(qr_paths[], payload_path, out_path)
  loop each QR image
    P -> QR : decode_png(path) — rqrr detect_grids
    QR --> P : piece string (or NoQrFound / NotAnImage)
  end
  P -> P : recover_secret(pieces, payload) — Shamir combine + secretbox open
  P --> UI : RecoverReport (output_path; no secret)
end
@enduml
```

## DIAG-19 — Fragile Watermark Embed / Verify

```plantuml
@startuml
start
partition "watermark_embed" {
  :precheck: <=256 MiB · PNG/BMP allowlist;
  :refuse-existing · require lossless output;
  :Argon2id(passphrase, fixed salt) -> WmKey;
  :load RGBA (bounded: <=30k px, <=1 GiB);
  :per 16x16 block: tag = BLAKE3_keyed(K, ctx | W | H | x0 | y0 | upper-7-bits);
  :tile 256 tag bits -> block blue-channel LSBs;
  :presence sentinel = BLAKE3_keyed(K, ctx | W | H) -> green-channel LSBs;
  :save PNG / BMP;
}
partition "watermark_verify" {
  :precheck · derive WmKey · load RGBA;
  :recompute each block tag; compare to blue LSBs;
  if (presence matched/total >= 0.75?) then (absent)
    :NotWatermarked (unmarked / wrong key / destroyed);
    stop
  else (present)
  endif
  if (tampered blocks == 0?) then (yes)
    :Intact;
  else (no)
    :Tampered (count reported);
  endif
}
stop
@enduml
```

## DIAG-20 — Metadata Inspect / Sanitize / Compare

```plantuml
@startuml
start
:metadata op (inspect / sanitize / diff);
note right
Hardened subprocess (all ops):
hash-pinned · env_clear + minimal PATH · -config '' (RCE closed)
throwaway cwd · 60 s timeout+kill · <=8 GiB input · stderr not echoed
disabled => fail-closed Internal for every op
end note
if (operation?) then (inspect)
  :-j -G -struct -fast2 -> grouped tag report;
elseif (operation = diff?) then (diff)
  :embedded-tag diff (exclude File/ExifTool/Composite/System);
else (sanitize)
  switch (sanitize_support(file_type)?)
  case (Native: images, A/V, raw)
    :-all= -o OUTPUT (guaranteed) · re-inspect before/after;
  case (Incremental: PDF)
    :strip, but prior metadata recoverable (guaranteed=false);
  case (ReadOnly: Office, archives)
    :refuse: Unsupported (never a false 'sanitized');
  endswitch
endif
stop
@enduml
```

## DIAG-22 — Error → Coded `ApiError` Oracle-Safety Mapping

```plantuml
@startuml
left to right direction
rectangle "VaultError" as ve
rectangle "PlatformError" as pe
rectangle "MetaError" as me
rectangle "StegoError" as se
rectangle "QrError" as qe
rectangle "WatermarkError" as we
rectangle "Unauthorized" as un
rectangle "Corrupted" as co
rectangle "Malformed" as mal
rectangle "InvalidInput{detail}" as iv
rectangle "InsufficientShares{got,need}" as is
rectangle "Io{detail} — path-stripped" as io
rectangle "Internal" as internal
rectangle "NotFound · TooLarge · IncompatibleVersion · Timeout · OutputExists" as pass
ve --> un : AuthFailed (wrong pass OR wrong share)
se --> un : NoPayload / BadFrame / AuthFailed (identical Display)
pe --> un : AuthFailed
ve --> co : signature / integrity fail
qe --> mal : NoQrFound / NotAnImage
me --> iv : ExifToolFailed / Unsupported (stderr never echoed)
we --> iv
ve --> is
pe --> is
ve --> io : Io(_) redacted
pe --> io : Io(_) redacted
me --> internal : BinaryNotFound / HashMismatch / Spawn (fail-closed)
ve --> internal : Crypto / Internal
ve --> pass
pe --> pass
me --> pass
@enduml
```

## DIAG-23 — Secret Lifecycle & Zeroization

```plantuml
@startuml
top to bottom direction
rectangle "passphrase typed in UI (password input)" as A
rectangle "JSON IPC bridge\n(residual copies here — un-zeroizable)" as B
rectangle "IpcPassphrase(String)\nDrop zeroizes · Debug redacts" as C
rectangle "SecretBytes\n(boxed slice, growth-proof, Drop zeroizes)" as D
rectangle "Argon2id" as E
rectangle "Key32 (master / file key)\nZeroize + ZeroizeOnDrop · redacted Debug · non-Serialize" as F
rectangle "transient unwrapped secrets\n(age identity, signing key, archive)\nper-op, zeroized after use" as G
rectangle "RAM-only session map\n(removing entry wipes Key32)" as H
rectangle "IPC boundary invariant:\nno secret in any DTO (sv-types has zero crypto deps)\nSessionHandle is an opaque id only" as INV
A --> B
B --> C
C --> D : into_secret() — zeroizes source String
D --> E
E --> F
F --> G
F --> H
H ..> INV
note bottom of A : UI password fields zeroed on navigation and after each task
@enduml
```
