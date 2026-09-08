# 7. UML & Architecture Diagrams

All diagrams are Mermaid and reflect the implemented code. They complement the textual sections;
where a diagram simplifies, the authoritative detail is the cited source.

---

## 7.1 Use-case diagram

```mermaid
graph LR
    user([End user])

    subgraph Vault
        uc1((Create vault))
        uc2((Unlock / lock))
        uc3((Add / extract item))
        uc4((Change passphrase))
        uc5((Check integrity))
        uc6((Split / recover key))
    end
    subgraph Cryptography
        uc7((Encrypt / decrypt file))
        uc8((Sign file))
        uc9((Verify signature))
        uc10((Hash file))
        uc11((Verify integrity))
    end
    subgraph "Secret Sharing"
        uc12((Split secret / file))
        uc13((Recover from pieces))
        uc14((QR export / import))
    end
    subgraph Media
        uc15((Hide data))
        uc16((Extract data))
        uc17((Detect hidden data))
        uc18((Watermark embed / verify))
    end
    subgraph Analysis
        uc19((Inspect metadata))
        uc20((Sanitize metadata))
        uc21((Compare metadata))
    end

    user --- uc1 & uc2 & uc3 & uc4 & uc5 & uc6
    user --- uc7 & uc8 & uc9 & uc10 & uc11
    user --- uc12 & uc13 & uc14
    user --- uc15 & uc16 & uc17 & uc18
    user --- uc19 & uc20 & uc21

    age([age / age-keygen])
    exif([ExifTool])
    uc1 -. uses .-> age
    uc7 -. "Argon2id+secretbox (no age)" .-> note1[" "]
    uc19 -. uses .-> exif
    uc20 -. uses .-> exif
    uc21 -. uses .-> exif
```

> Note: the **vault** payload uses the `age` binary; the **Cryptography** module's Encrypt/Decrypt
> File uses pure-Rust Argon2id + `secretbox` (the `SVENC` artifact) and does **not** invoke `age`.

---

## 7.2 Component diagram

```mermaid
graph TB
    subgraph Presentation
        FE["Webview frontend<br/>(static, withGlobalTauri)"]
        HND["#[tauri::command] handlers<br/>(app/src/lib.rs)"]
    end
    subgraph Application
        AV["AppVault / CommandSurface"]
        PA["PlatformApp"]
        SA["StegoApp"]
        MA["MetaApp (fail-closed)"]
        WA["WatermarkApp"]
        IPC["IpcPassphrase + ApiError map"]
    end
    subgraph Domain
        CORE["sv-core"]
        PLAT["sv-platform"]
        STEG["sv-stego"]
        META["sv-meta"]
        QR["sv-qr"]
        WM["sv-watermark"]
    end
    subgraph Platform
        TR["sv-crypto-traits (ABI)"]
        CR["sv-crypto"]
        AGE["sv-age"]
        SOD["sv-sys-sodium"]
        SSS["sv-sys-sss"]
    end
    TYPES["sv-types (DTO/ApiError)"]

    FE <-->|invoke| HND
    HND --> AV & PA & SA & MA & WA
    AV & PA & SA & MA & WA --> IPC
    AV --> CORE
    PA --> PLAT
    PA --> QR
    SA --> STEG
    MA --> META
    WA --> WM
    CORE --> TR
    CORE -. composition root .-> AGE
    PLAT --> CR
    STEG --> CR
    WM --> CR
    CR --> TR
    CR --> SOD & SSS
    AGE --> TR
    AV & PA & SA & MA & WA & CORE & PLAT & STEG & META & QR & WM --> TYPES
```

---

## 7.3 Class diagram — crypto ABI and adapters

```mermaid
classDiagram
    class Hasher {
        <<trait>>
        +alg() HashAlg
        +hash(input) Hash32
        +keyed_hash(key, input) Hash32
        +streaming() StreamingHasher
    }
    class KeyDerivation {
        <<trait>>
        +derive_key(context, ikm) Key32
    }
    class Kdf {
        <<trait>>
        +alg() KdfAlg
        +derive(passphrase, salt, params) Key32
    }
    class Signer {
        <<trait>>
        +generate() Keypair
        +sign(msg, sk, comment) MinisignSignature
        +verify(msg, sig, pk) Result
    }
    class SecretSharer {
        <<trait>>
        +split(key, n, k) Shares
        +combine(shares) Key32
    }
    class FileCipher {
        <<trait>>
        +encrypt(pt, ct, recipient)
        +decrypt(ct, pt, identity)
    }

    class Blake3Hasher
    class Argon2Kdf
    class SodiumMinisignSigner
    class SssSharer
    class AgeCipher

    Hasher <|.. Blake3Hasher
    KeyDerivation <|.. Blake3Hasher
    Kdf <|.. Argon2Kdf
    Signer <|.. SodiumMinisignSigner
    SecretSharer <|.. SssSharer
    FileCipher <|.. AgeCipher

    class Key32 {
        +expose_secret() bytes
    }
    note for Key32 "fixed [u8;32]; ZeroizeOnDrop; redacted Debug; not Serialize"
    class SecretBytes {
        +expose_secret() bytes
    }
    note for SecretBytes "boxed bytes (no spare capacity); Drop-zeroize; not Serialize"
    Argon2Kdf ..> Key32 : returns
    Blake3Hasher ..> Key32 : derive_key
    SssSharer ..> Key32 : combine
```

---

## 7.4 Class diagram — vault composition root

```mermaid
classDiagram
    class CommandSurface {
        <<trait>>
        +vault_create()
        +vault_unlock()
        +item_add()
        +integrity_check()
        +keys_split()
    }
    class AppVault~P~ {
        -backend VaultBackend
    }
    class VaultBackend~P~ {
        -payload P
        -hierarchy StdKeyHierarchy
        -hasher Blake3Hasher
        -signer SodiumMinisignSigner
        -sharer SssSharer
        -sessions SessionMap
        -write_locks LockMap
    }
    note for VaultBackend "hierarchy = StdKeyHierarchy of Argon2Kdf + Blake3Hasher; sessions/write_locks are mutex-guarded maps"
    class SessionState {
        -master_key Key32
        -vault_path PathBuf
    }
    class PayloadCipher {
        <<trait>>
        +generate_identity()
        +encrypt(pt, recipient)
        +decrypt(ct, identity)
    }
    class AgePayloadCipher {
        -cipher: AgeCipher
        -keygen_bin: PathBuf
    }
    class StubPayloadCipher

    CommandSurface <|.. AppVault
    AppVault *-- VaultBackend
    VaultBackend *-- SessionState
    VaultBackend o-- PayloadCipher
    PayloadCipher <|.. AgePayloadCipher
    PayloadCipher <|.. StubPayloadCipher
```

---

## 7.5 Sequence — vault unlock

```mermaid
sequenceDiagram
    actor U as User
    participant FE as Frontend (JS)
    participant H as Cmd vault_unlock
    participant B as VaultBackend
    participant C as sv-core container
    participant S as Signer (minisign)
    participant K as KeyHierarchy (Argon2id+BLAKE3)
    participant A as AgePayloadCipher

    U->>FE: enter path + passphrase
    FE->>H: invoke("vault_unlock", {path, passphrase})
    H->>H: IpcPassphrase → SecretBytes
    H->>B: unlock(path, secret)
    B->>C: read container, recompute binding root
    C->>S: verify(root, sig, in-header pubkey)
    alt signature fails
        S-->>B: VerificationFailed → Corrupted
        B-->>H: VaultError::Corrupted
        H-->>FE: ApiError SV-CORRUPTED
    else signature ok
        B->>K: derive_master(passphrase, salt, params)
        K-->>B: Master Key (Key32)
        B->>K: derive_wrap_key → unwrap age identity (secretbox.open)
        alt unwrap fails
            B-->>H: VaultError::AuthFailed
            H-->>FE: ApiError SV-UNAUTHORIZED
        else ok
            B->>B: store SessionState{master_key}
            B-->>H: SessionHandle (opaque)
            H-->>FE: session_id
        end
    end
    Note over FE,A: A used later only for item add/extract
```

The wrong-passphrase path (`AuthFailed → SV-UNAUTHORIZED`) and the tamper path (`Corrupted →
SV-CORRUPTED`) are intentionally distinct because tamper is detected *before* the credential check
(signature gate first); wrong passphrase vs. wrong recovery share remain merged.

---

## 7.6 Sequence — add item (encrypt-and-store)

```mermaid
sequenceDiagram
    participant H as item_add handler
    participant B as VaultBackend
    participant L as write_lock (per-vault mutex)
    participant C as container/archive
    participant A as age subprocess
    participant S as Signer
    participant FS as Filesystem

    H->>B: add_item(session, source, name)
    B->>B: stat source; reject if > 2 GiB (TooLarge)
    B->>L: acquire per-vault write lock (H7)
    B->>C: read+decrypt current payload, unpack archive
    B->>C: append item, repack (DIR_LEN ‖ CBOR ‖ bytes), per-item BLAKE3
    B->>A: encrypt(archive, recipient)  [env_clear, timeout]
    A-->>B: age ciphertext
    B->>S: sign(binding_root)
    S-->>B: minisign trailer
    B->>FS: write_atomic(temp → fsync → rename)
    B->>L: release lock
    B-->>H: ItemInfo
```

---

## 7.7 Sequence — encrypt a file (Cryptography module, no age)

```mermaid
sequenceDiagram
    participant FE as Frontend
    participant H as crypto_encrypt_file handler
    participant P as PlatformCrypto
    participant K as Argon2Kdf + BLAKE3 derive_key
    participant X as secretbox (XSalsa20-Poly1305)
    participant FS as Filesystem

    FE->>H: invoke("crypto_encrypt_file", {input, output, passphrase})
    H->>H: IpcPassphrase → SecretBytes
    H->>P: encrypt_file(input, output, secret)
    P->>P: refuse_existing(output); read_capped(input, 2 GiB)
    P->>K: derive file key (random salt, recommended params, domain ctx)
    P->>X: seal(plaintext)
    X-->>P: nonce + ciphertext+tag
    P->>FS: write_atomic SVENC artifact
    P-->>H: output path
    H-->>FE: path (DTO)
```

---

## 7.8 Sequence — secret sharing split + recover

```mermaid
sequenceDiagram
    participant H as shares_split_* / recover handler
    participant P as sharing engine
    participant SSS as Shamir (sss)
    participant X as secretbox

    Note over H,X: SPLIT
    H->>P: split_secret/file(secret, n, k, dir)
    P->>P: random DEK (32B), random group_id (16B)
    P->>SSS: create_keyshares(DEK, n, k)
    P->>X: payload key = BLAKE3.derive_key(ctx|group|n|k, DEK); seal(secret)
    P-->>H: SVSSP payload + n SVSSS pieces (+ Base64 / QR)

    Note over H,X: RECOVER
    H->>P: recover_secret(pieces, payload, out)
    P->>P: gates: agreement, dup-x, non-zero-x, count≥k, payload_ref
    P->>SSS: combine_keyshares(shares) → DEK
    P->>X: re-derive payload key; open()
    alt open fails (wrong/tampered)
        P-->>H: AuthFailed → SV-UNAUTHORIZED
    else ok
        P-->>H: RecoverOutput (path, bytes, original name)
    end
```

---

## 7.9 Sequence — metadata inspect (fail-closed subprocess)

```mermaid
sequenceDiagram
    participant FE as Frontend
    participant H as metadata_inspect handler
    participant M as MetaApp
    participant E as ExifTool subprocess
    FE->>H: invoke("metadata_available")
    H-->>FE: bool (disable UI if false)
    FE->>H: invoke("metadata_inspect", {path})
    alt MetaApp disabled (no pinned binary)
        H-->>FE: ApiError SV-INTERNAL (unavailable)
    else available
        H->>M: inspect(path)
        M->>M: precheck size (≤ 8 GiB)
        M->>E: exiftool -config "" -j -G -struct -fast2 PATH  [env_clear, fresh cwd, 60s]
        E-->>M: JSON
        M-->>H: MetadataReport (grouped tags)
        H-->>FE: report
    end
```

---

## 7.10 Deployment diagram

```mermaid
graph TB
    subgraph build["Build host (cargo tauri build)"]
        src["Workspace crates + app/"]
        brs["build.rs: stage age/age-keygen/exiftool + lib/<br/>compute BLAKE3 pins (rustc-env)<br/>detect_staged_target arch check"]
        src --> brs --> bundle["Per-OS bundle (.app/.dmg, .msi/.exe, .deb/AppImage)"]
    end

    subgraph target["Target machine (offline)"]
        subgraph proc["Secure Vault process"]
            wv["WebView (OS engine: WebKit/WebView2/WebKitGTK)"]
            rust["Rust core (sv-app + crates), 5 managed states"]
            wv <-->|"Tauri IPC (coded ApiError)"| rust
        end
        res["App Resources/binaries/** : age, age-keygen, exiftool + lib/ (BLAKE3-pinned)"]
        data[("User files: .svault, .svenc, .svss, images")]
        rust -->|"subprocess: env_clear + timeout + no shell"| res
        rust -->|"atomic read/write"| data
    end

    bundle -->|install / copy| proc
    bundle -->|packaged| res

    note["Bundle is UNSIGNED (H5) — internal use only"]
    bundle -.-> note
```

- The webview engine is **OS-provided** (WebKit on macOS, WebView2 on Windows, WebKitGTK on Linux) —
  it is not bundled; only the static frontend assets and the Rust binary + pinned tool binaries are.
- The five managed states (`Backend`, `Platform`, `Stego`, `Meta`, `Watermark`) are constructed in
  the Tauri `setup` hook ([app/src/lib.rs](../../app/src/lib.rs) `run()`).

---

## 7.11 Data-flow diagram (DFD)

```mermaid
flowchart TD
    user([User])
    pw["passphrase"]:::secret
    file["input file / cover / pieces"]

    user --> pw & file

    subgraph proc["Secure Vault core"]
        ipc{{"IPC boundary: IpcPassphrase + non-secret DTOs"}}
        kdf["Argon2id KDF → Key32"]:::secret
        seal["AEAD / age / minisign"]
        verdict["report builder (no secrets)"]
    end

    pw --> ipc --> kdf --> seal
    file --> ipc --> seal
    seal --> store[("at-rest: .svault / artifact")]
    seal --> verdict --> out["DTO + ApiError"] --> user
    store -. read .-> seal

    classDef secret fill:#3a1d1d,stroke:#f85149,color:#ffd;
```

**Trust-boundary crossings in the DFD**

1. **`user → ipc`**: the passphrase is the only secret to cross inward; it becomes `IpcPassphrase`
   then `SecretBytes` (documented upstream-copy residual).
2. **`seal ↔ store`**: data at rest is authenticated-encrypted; reads recompute and verify before
   trusting.
3. **`verdict → out → user`**: only non-secret DTOs and coded errors flow back; verdict/suspicion
   enums cannot express “clean/authentic.”
4. **(not shown) `seal → external binary`**: age/ExifTool subprocess crossing, hardened per §6.6.
