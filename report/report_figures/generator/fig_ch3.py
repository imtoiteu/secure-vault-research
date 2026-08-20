# -*- coding: utf-8 -*-
"""Hinh chuong 3 — Xay dung va trien khai he thong."""
from figlib import Figure, emit, _wrap as _wrapn

SRC = "Nguồn: "


def fig_3_1():
    f = Figure("Hinh-3-01-cau-truc-ma-nguon",
               "Hình 3.1 — Cấu trúc mã nguồn của workspace Secure Vault",
               "13 crate trong workspace + 1 crate vỏ Tauri bị loại trừ có chủ ý; ~16 300 dòng Rust",
               1180, 860,
               SRC + "Cargo.toml (members, exclude), cây thư mục crates/, src-tauri/, desktop/, docs/")

    f.node("root", 60, 96, 300, 44, "secure-vault-research/", "ext", fontsize=13)

    rows = [
        ("Cargo.toml", "khai báo workspace, phiên bản phụ thuộc dùng chung, lint toàn cục", "ext", 0),
        ("rust-toolchain.toml · deny.toml", "cố định phiên bản trình biên dịch và chính sách chuỗi cung ứng", "ext", 0),
        ("crates/sv-types", "791 dòng — DTO IPC/UI, ApiError 12 mã, nameframe", "store", 1),
        ("crates/sv-crypto-traits", "449 dòng — ABI: trait, kiểu giá trị bí mật, định danh thuật toán", "sys", 1),
        ("crates/sv-sys-sodium", "214 dòng — FFI libsodium (sign, blake2b, secretbox)", "sys", 1),
        ("crates/sv-sys-sss", "155 dòng + hazmat.c — FFI Shamir, randombytes nối vào getrandom", "sys", 1),
        ("crates/sv-crypto", "668 dòng — Blake3Hasher, Argon2Kdf, SssSharer, minisign, secretbox, policy", "crypto", 1),
        ("crates/sv-age", "426 dòng — bộ điều hợp FileCipher trên tiến trình con age", "crypto", 1),
        ("crates/sv-core", "1 316 dòng — format, container, keys, service, error của két .svault", "domain", 1),
        ("crates/sv-platform", "1 945 dòng — artifact, crypto, integrity, sharing (không phụ thuộc két)", "domain", 1),
        ("crates/sv-stego", "≈2 490 dòng — carrier, embed, selector, envelope, seal, pipeline, detect", "domain", 1),
        ("crates/sv-watermark · sv-meta · sv-qr", "610 + 807 + 289 dòng — thủy vân, ExifTool, mã QR", "domain", 1),
        ("src-tauri (sv-app)", "1 990 dòng — gốc lắp ghép, 5 bề mặt lệnh, IpcPassphrase, VaultBackend", "app", 1),
        ("desktop/", "vỏ Tauri 2: build.rs (363 dòng), src/lib.rs (716 dòng), frontend tĩnh", "ui", 1),
        ("docs/", "18 tài liệu thiết kế + docs/architecture/ 10 chương kiến trúc", "note", 1),
        (".github/workflows/ci.yml", "5 nhóm việc CI: check (3 hệ điều hành), msrv, desktop, supply-chain, sbom", "ok", 1),
    ]
    y = 158
    for i, (name, desc, kind, ind) in enumerate(rows):
        x = 90 + ind * 40
        f.node(f"r{i}", x, y, 330, 40, name, kind, fontsize=11.5)
        f.text(x + 344, y + 24, desc, 10.6, False, "#3a4a5a", w=690)
        y += 44

    f.text(60, y + 30, "Quy ước phân tách quan trọng nhất: thư mục desktop/ được khai báo exclude trong "
                       "workspace. Nhờ vậy cây phụ thuộc rất nặng của webview không đi vào cổng kiểm toán "
                       "(cargo deny / cargo audit / cargo build --locked) của phần lõi mật mã, và phần lõi "
                       "vẫn kiểm thử được trên máy không có bộ công cụ Tauri.",
           11, False, "#3a4a5a", w=1060)
    emit(f, 3)


def fig_3_2():
    f = Figure("Hinh-3-02-abi-mat-ma",
               "Hình 3.2 — Sơ đồ lớp của tầng ABI mật mã và các bộ điều hợp hiện thực",
               "Cổng là trait, bộ điều hợp là struct kích thước không, kiểu bí mật tự xóa khi hủy",
               1200, 830,
               SRC + "crates/sv-crypto-traits/src/lib.rs; crates/sv-crypto/src/lib.rs")

    f.zone(50, 90, 540, 420, "«interface» — cổng trong sv-crypto-traits", "sys", "")
    traits = [
        ("Hasher", "alg() : HashAlg\\nhash(&[u8]) : Hash32\\nkeyed_hash(&[u8;32], &[u8]) : Hash32\\nstreaming() : Box<dyn StreamingHasher>"),
        ("KeyDerivation", "derive_key(context: &str, ikm: &[u8]) : Key32"),
        ("Kdf", "alg() : KdfAlg\\nderive(pass, salt, params) : Result<Key32>"),
        ("Signer", "generate() : (SecretBytes, Ed25519PublicKey)\\nsign(msg, sk, trusted_comment) : MinisignSignature\\nverify(msg, sig, pk) : Result<()>"),
        ("SecretSharer", "split(&Key32, n, k) : Vec<KeyShare>\\ncombine(&[KeyShare]) : Key32"),
        ("FileCipher", "alg() : FileCipherAlg\\nencrypt(pt, ct, recipient)\\ndecrypt(ct, pt, identity)"),
    ]
    y = 128
    for i, (nm, ops) in enumerate(traits):
        lines = ops.split("\\n")
        h = 26 + len(lines) * 13
        f.node(f"t{i}", 72, y, 496, h, "«trait» " + nm, "sys",
               sub=" · ".join(lines), fontsize=11.5)
        y += h + 8

    f.zone(640, 90, 520, 300, "Bộ điều hợp cụ thể trong sv-crypto / sv-age", "crypto", "")
    impls = [
        ("Blake3Hasher", "Hasher + KeyDerivation → crate blake3"),
        ("Argon2Kdf", "Kdf → crate argon2 (Argon2id, V0x13)"),
        ("SodiumMinisignSigner", "Signer → libsodium Ed25519 + BLAKE2b"),
        ("SssSharer", "SecretSharer → sss hazmat.c"),
        ("AgeCipher", "FileCipher → tiến trình con age đã ghim băm"),
    ]
    y = 128
    for i, (nm, be) in enumerate(impls):
        f.node(f"i{i}", 662, y, 476, 46, nm, "crypto", sub=be, fontsize=12)
        y += 52

    f.zone(640, 410, 520, 300, "Kiểu giá trị bí mật (không Serialize, Debug bị che)", "key", "")
    vals = [
        ("Key32", "[u8; 32] trên ngăn xếp · Zeroize + ZeroizeOnDrop · không cấp phát động"),
        ("KeyShare", "[u8; 33] · một mảnh Shamir đã xác thực"),
        ("SecretBytes", "Box<[u8]> — không có dung lượng dư nên không thể tái cấp phát rồi rò rỉ"),
        ("AgeIdentity", "bọc SecretBytes cho khóa bí mật age"),
    ]
    y = 448
    for i, (nm, note) in enumerate(vals):
        f.node(f"v{i}", 662, y, 476, 56, nm, "key", sub=note, fontsize=12)
        y += 62

    f.node("nonsec", 50, 530, 540, 130, "Kiểu giá trị KHÔNG bí mật (được Serialize, nằm trong header)",
           "plain", sub="Hash32 · Salt · Argon2idParams · KdfParams · MinisignSignature · "
                        "Ed25519PublicKey · AgeRecipient · KdfAlg · HashAlg · AeadAlg · "
                        "FileCipherAlg · SigAlg", fontsize=12)

    f.node("err", 50, 680, 540, 90, "CryptoError", "danger",
           sub="InvalidParameter · VerificationFailed · Backend · Timeout · NotImplemented; "
               "được tầng nghiệp vụ ánh xạ tiếp sang VaultError rồi ApiError", fontsize=12)

    for i in range(5):
        f.edge(f"i{i}", f"t{min(i, 5)}", "hiện thực", arrow="open", dashed=True, bend="ortho", fontsize=9)

    f.text(50, 800, "Ba kiểu bí mật cố tình không cài Serialize: đó là rào chắn ở mức trình biên dịch "
                    "khiến một lập trình viên không thể vô ý đưa khóa vào DTO đi qua biên IPC.",
           11, False, "#3a4a5a", w=1100)
    emit(f, 3)


def fig_3_3():
    f = Figure("Hinh-3-03-tuan-tu-tao-ket",
               "Hình 3.3 — Biểu đồ tuần tự khởi tạo két mới (lệnh vault_create)",
               "Mọi vật liệu khóa được sinh mới; két rỗng vẫn được ký và ghi nguyên tử",
               1280, 830,
               SRC + "src-tauri/src/service.rs create(); src-tauri/src/payload.rs generate_identity(); "
                     "crates/sv-crypto/src/lib.rs SodiumMinisignSigner::generate")

    cols = [("ui", "Giao diện", 40, "ui"), ("be", "VaultBackend", 250, "app"),
            ("rng", "getrandom", 470, "ok"), ("kg", "age-keygen", 680, "sys"),
            ("sg", "SodiumMinisignSigner", 890, "crypto"), ("ct", "container", 1110, "domain")]
    cx = {}
    for cid, name, x, kind in cols:
        f.node(cid, x, 92, 160, 46, name, kind, fontsize=11.3)
        cx[cid] = x + 80

    steps = [
        ("ui", "be", "vault_create(path, IpcPassphrase, Option<SharePolicy>)"),
        ("be", None, "Kiểm tra chính sách chia mảnh: 2 ≤ shares_total, 1 ≤ threshold ≤ shares_total"),
        ("be", "rng", "Sinh vault_uuid 16 byte và muối Argon2id 16 byte"),
        ("be", None, "Argon2id(mật khẩu, muối, tham số mặc định 256 MiB / t=3 / p=1) → khóa chủ MK"),
        ("be", "kg", "generate_identity(): chạy age-keygen với môi trường đã xóa"),
        ("kg", "be", "(AGE-SECRET-KEY-1…, age1… ) — danh tính bí mật và người nhận công khai"),
        ("be", "sg", "generate(): sinh cặp khóa Ed25519 64 byte / 32 byte"),
        ("be", None, "Bọc hai bí mật: derive_wrap_key(MK, <trường>, uuid) rồi secretbox::seal"),
        ("be", None, "Dựng VaultHeader: suite V1, uuid, kdf, hai khối đã bọc, khóa công khai ký, chính sách"),
        ("be", "ct", "pack_archive(danh sách mục rỗng) → DIR_LEN ‖ CBOR(ItemDirectory rỗng)"),
        ("be", "ct", "encrypt(archive, recipient) rồi encode(): tính gốc ràng buộc và ký"),
        ("be", "ct", "write_atomic(path): tệp tạm cùng thư mục → fsync → rename"),
        ("be", "ui", "VaultMeta { vault_uuid, format_version, item_count = 0, kdf, share_policy }"),
    ]
    y = 176
    for i, (a, b, lab) in enumerate(steps):
        if b is None:
            f.node(f"sb{i}", cx[a] - 9, y - 8, 18, 18, "", "note", fontsize=8)
            f.text(cx[a] + 18, y - 1, lab, 10.4, False, "#2f3d4c", w=700)
            y += 42
        else:
            x1, x2 = cx[a], cx[b]
            span = abs(x2 - x1)
            lines = _wrapn(lab, max(24, int(span / 5.6)))
            f.node(f"pa{i}", x1 - 7, y - 7, 14, 14, "", "app", fontsize=8)
            f.node(f"pb{i}", x2 - 7, y - 7, 14, 14, "", "app", fontsize=8)
            f.edge(f"pa{i}", f"pb{i}", "", fontsize=8)
            f.text(min(x1, x2) + 12, y - 8 - (len(lines) - 1) * 12.5, lab, 10.4, False, "#2f3d4c",
                   w=span - 20)
            y += 32 + (len(lines) - 1) * 13

    for cid, name, x, kind in cols:
        f.node(cid + "_l", x + 73, 138, 14, y - 138, "", kind, shape="lifeline", fontsize=8)

    f.text(40, 70, "Nếu chính sách khôi phục được bật, các mảnh KHÔNG được sinh ở bước này: két chỉ ghi "
                   "lại chính sách (n, k); mảnh thật chỉ được cắt khi người dùng gọi keys_split trên "
                   "một phiên đã mở khóa.", 11, False, "#3a4a5a", w=1200)
    emit(f, 3)


def fig_3_4():
    f = Figure("Hinh-3-04-chia-khoi-phuc-khoa-chu",
               "Hình 3.4 — Chia và khôi phục khóa chủ của két theo ngưỡng k trong n",
               "Phong bì mảnh SVSH 58 byte; mảnh không bao giờ được lưu trong két",
               1200, 780,
               SRC + "src-tauri/src/service.rs split_key/recover, build_share_envelope/parse_share_envelope; "
                     "crates/sv-crypto/src/lib.rs SssSharer")

    f.zone(50, 90, 540, 300, "Đường chia (keys_split, cần phiên đã mở khóa)", "ok", "")
    f.node("mk", 76, 136, 220, 60, "Khóa chủ MK (32 byte)", "key", sub="lấy từ bảng phiên")
    f.node("split", 330, 136, 236, 60, "SssSharer::split(MK, n, k)", "crypto",
           sub="Shamir trên GF(2⁸), mảnh đã xác thực")
    f.node("shares", 76, 216, 490, 56, "n mảnh, mỗi mảnh 33 byte (byte đầu là hoành độ x)", "key")
    f.node("env", 76, 288, 490, 84, "Phong bì SVSH — 58 byte cố định", "store",
           sub="MAGIC \"SVSH\" (4) ‖ version u16 LE (2) ‖ vault_uuid (16) ‖ index (1) ‖ total (1) "
               "‖ threshold (1) ‖ mảnh (33)")

    f.zone(620, 90, 540, 300, "Đường khôi phục (keys_recover, KHÔNG cần mật khẩu)", "domain", "")
    f.node("read", 646, 136, 490, 52, "Đọc k phong bì; kiểm MAGIC, phiên bản, độ dài", "app",
           fontsize=11.5)
    f.node("uuidchk", 646, 200, 490, 52, "Đối chiếu vault_uuid trong mảnh với uuid trong header két", "app",
           sub="lệch ⇒ SV-INVALID-INPUT \"mảnh thuộc két khác\"", fontsize=11.5)
    f.node("cnt", 646, 264, 490, 46, "Kiểm số lượng: got < threshold ⇒ SV-INSUFFICIENT-SHARES { got, need }",
           "ok", fontsize=11)
    f.node("comb", 646, 322, 490, 50, "SssSharer::combine → MK ứng viên", "crypto", fontsize=11.5)

    f.node("gate", 330, 430, 540, 78, "Cổng tín nhiệm chung: secretbox::open(wrapped_age_identity)", "key",
           sub="thất bại ⇒ SV-UNAUTHORIZED — cùng một mã với trường hợp sai mật khẩu")
    f.node("sess", 330, 534, 540, 60, "Tạo phiên mới ↦ (MK, đường dẫn két)", "app",
           sub="từ đây mọi thao tác giống hệt phiên mở bằng mật khẩu")

    f.node("outdir", 76, 430, 220, 78, "Thư mục xuất mảnh", "store", shape="cyl",
           sub="<uuid>.share1.svshare …")

    f.edge("mk", "split", "")
    f.edge("split", "shares", "", bend="orthoV")
    f.edge("shares", "env", "")
    f.edge("env", "outdir", "ghi nguyên tử", bend="orthoV", lx=180, ly=410)
    f.edge("read", "uuidchk", "")
    f.edge("uuidchk", "cnt", "")
    f.edge("cnt", "comb", "")
    f.edge("comb", "gate", "", bend="orthoV")
    f.edge("gate", "sess", "")

    f.text(50, 640, "Hai thuộc tính đáng chú ý. Thứ nhất, ngưỡng là tính chất của lược đồ Shamir chứ không "
                    "phải của phần mềm: với ít hơn k mảnh, thư viện vẫn trả về một khóa 32 byte nhưng là "
                    "khóa SAI — bằng chứng là kiểm thử sss_below_threshold_yields_wrong_key. Thứ hai, vì thế "
                    "phép kiểm tra thực sự nằm ở cổng mở bọc AEAD phía sau, chứ không nằm ở phép so sánh nào "
                    "trên chính các mảnh.", 11, False, "#3a4a5a", w=1100)
    emit(f, 3)


def fig_3_5():
    f = Figure("Hinh-3-05-ma-hoa-tep-doc-lap",
               "Hình 3.5 — Mã hóa và giải mã tệp độc lập bằng mật khẩu (định dạng SVENC)",
               "Đường này KHÔNG dùng age: chỉ Argon2id + secretbox, thuần Rust + libsodium",
               1180, 750,
               SRC + "crates/sv-platform/src/crypto.rs encrypt_file/decrypt_file; "
                     "crates/sv-platform/src/artifact.rs seal_with_passphrase/open_with_passphrase")

    f.node("in", 50, 110, 210, 62, "Tệp đầu vào", "store", shape="cyl", sub="≤ 2 GiB (kiểm bằng stat)")
    f.node("pw", 50, 196, 210, 62, "Mật khẩu", "key", sub="IpcPassphrase → &[u8]")
    f.node("salt", 50, 282, 210, 62, "Muối 16 byte mới", "plain", sub="getrandom")

    f.node("argon", 310, 196, 210, 62, "Argon2id", "crypto", sub="tham số theo sàn OWASP")
    f.node("dk", 310, 282, 210, 62, "BLAKE3::derive_key", "crypto",
           sub="ngữ cảnh tách miền theo MAGIC")
    f.node("fek", 570, 240, 210, 62, "Khóa tệp FEK (32 byte)", "key", sub="Key32, tự xóa khi hủy")

    f.node("sb", 830, 240, 300, 62, "secretbox::seal (XSalsa20-Poly1305)", "crypto",
           sub="nonce 24 byte ngẫu nhiên + thẻ Poly1305 16 byte")

    f.node("art", 310, 386, 820, 96, "Tệp .svenc — 62 byte header + bản mã", "store",
           sub="MAGIC \"SVENC\\0\" (6) ‖ version u16 (2) ‖ kdf_alg (1) ‖ mem_kib u32 ‖ time_cost u32 "
               "‖ parallelism u32 ‖ salt (16) ‖ aead_alg (1) ‖ nonce (24) ‖ ciphertext")

    f.node("open", 310, 512, 400, 76, "Đường mở: đọc header, chặn tham số Argon2 vượt trần", "ok",
           sub="mem ≤ 4 GiB, t ≤ 64, p ≤ 64 — kiểm TRƯỚC khi chạy KDF")
    f.node("fail", 760, 512, 370, 76, "Mọi thất bại ⇒ SV-UNAUTHORIZED", "danger",
           sub="sai mật khẩu và bản mã bị sửa không phân biệt được")

    f.node("key2", 50, 512, 210, 76, "Tệp .svkey", "store", shape="cyl",
           sub="cùng cơ chế, khác MAGIC — dùng để cất khóa ký Ed25519 khi lưu trữ")

    f.edge("in", "sb", "dữ liệu rõ", bend="ortho", lx=560, ly=140)
    f.edge("pw", "argon", "")
    f.edge("salt", "argon", "", bend="orthoV")
    f.edge("argon", "dk", "", bend="orthoV")
    f.edge("dk", "fek", "")
    f.edge("fek", "sb", "")
    f.edge("sb", "art", "", bend="orthoV")
    f.edge("art", "open", "")
    f.edge("open", "fail", "")
    f.edge("art", "key2", "cùng cơ chế", bend="ortho", dashed=True, lx=180, ly=470)

    f.text(50, 636, "Header là dữ liệu công khai nhưng CÓ THỂ bị kẻ tấn công điều khiển trước khi có bất kỳ "
                    "phép xác thực nào, nên tham số chi phí Argon2 phải được chặn trần trước khi chạy KDF; "
                    "nếu không, một tệp .svenc độc hại có thể yêu cầu hàng chục GiB bộ nhớ. Tính toàn vẹn của "
                    "header không được bảo vệ bằng AAD (secretbox không có AAD) mà bằng cách gấp MAGIC vào "
                    "ngữ cảnh dẫn xuất khóa: sửa header ⇒ sai khóa ⇒ hỏng thẻ xác thực.",
           11, False, "#3a4a5a", w=1080)
    emit(f, 3)


def fig_3_6():
    f = Figure("Hinh-3-06-chia-se-bi-mat",
               "Hình 3.6 — Lược đồ chia sẻ bí mật lai: Shamir trên DEK + AEAD trên tải trọng",
               "Vì sao phải lai: nguyên thủy sss chỉ chia được đúng một khóa 32 byte",
               1200, 820,
               SRC + "crates/sv-platform/src/sharing.rs split_core/recover_core/derive_payload_key, "
                     "encode_share_string; crates/sv-qr/src/lib.rs")

    f.zone(50, 90, 1100, 290, "Chia (split_secret / split_file)", "ok", "")
    f.node("sec", 74, 136, 220, 58, "Bí mật tùy độ dài", "key", sub="chuỗi người dùng gõ, hoặc nội dung tệp")
    f.node("nf", 74, 208, 220, 58, "nameframe::frame", "domain",
           sub="gắn tên tệp gốc VÀO BÊN TRONG vùng sẽ mã hóa")
    f.node("dek", 340, 136, 200, 58, "DEK 32 byte ngẫu nhiên", "key", sub="getrandom")
    f.node("gid", 340, 208, 200, 58, "group_id 16 byte", "plain", sub="thay cho UUID két")
    f.node("pk", 580, 172, 260, 58, "derive_payload_key", "crypto",
           sub="BLAKE3(\"…/SVSS|group|n|k\", DEK)")
    f.node("seal", 880, 172, 250, 58, "secretbox::seal", "crypto", sub="nonce 24 B + thẻ 16 B")
    f.node("payload", 580, 288, 260, 72, "Tệp tải trọng SVSSP", "store",
           sub="MAGIC (6) ‖ ver (2) ‖ aead_alg (1) ‖ nonce (24) ‖ ciphertext")
    f.node("ref", 880, 288, 250, 72, "payload_ref = BLAKE3(cả tệp tải trọng)", "crypto",
           sub="ràng buộc từng mảnh với đúng tải trọng này")
    f.node("piece", 74, 288, 480, 72, "n tệp mảnh SVSSS — mỗi tệp đúng 92 byte", "store",
           sub="MAGIC (6) ‖ ver (2) ‖ group_id (16) ‖ n (1) ‖ k (1) ‖ index (1) ‖ payload_ref (32) ‖ mảnh (33)")

    f.zone(50, 402, 1100, 300, "Khôi phục (recover_secret) — năm cổng kiểm tra không bí mật rồi mới tới AEAD", "domain", "")
    gates = [
        "1. Đồng thuận: mọi mảnh phải cùng group_id, cùng n, k, cùng payload_ref",
        "2. Trùng hoành độ: hai mảnh cùng x làm phép nội suy Lagrange suy biến ⇒ từ chối ngay",
        "3. Hoành độ khác 0: mảnh thật không bao giờ dùng x = 0 (bí mật nằm tại x = 0)",
        "4. Đếm số mảnh: got < k ⇒ SV-INSUFFICIENT-SHARES { got, need }",
        "5. Ràng buộc tải trọng: BLAKE3(tệp tải trọng) phải khớp payload_ref trong mảnh",
    ]
    y = 444
    for i, g in enumerate(gates):
        f.node(f"g{i}", 74, y, 700, 36, g, "ok", fontsize=10.8, bold=False)
        y += 40
    f.node("final", 800, 470, 330, 130, "Cổng mật mã cuối cùng", "key",
           sub="combine → DEK → derive_payload_key(group_id, n, k) → secretbox::open. "
               "Mọi thất bại tại đây đều là SV-UNAUTHORIZED, không phân biệt sai mảnh hay bản mã bị sửa.")

    f.node("b64", 74, 646, 700, 44, "Mỗi mảnh còn được xuất thành chuỗi Base64 124 ký tự để chép tay, "
                                    "và có thể in thành ảnh QR PNG (mức sửa lỗi H)", "store", fontsize=11)

    f.edge("sec", "nf", "")
    f.edge("nf", "seal", "dữ liệu rõ đã đóng khung", bend="ortho", lx=420, ly=120)
    f.edge("dek", "pk", "")
    f.edge("gid", "pk", "")
    f.edge("pk", "seal", "")
    f.edge("seal", "payload", "", bend="ortho")
    f.edge("payload", "ref", "")
    f.edge("dek", "piece", "SssSharer::split(DEK, n, k)", bend="ortho", lx=330, ly=270)
    f.edge("ref", "piece", "", bend="ortho", dashed=True)

    f.text(50, 736, "Vì secretbox không nhận dữ liệu liên kết (AAD), tính toàn vẹn của phần header không "
                    "được bảo vệ bằng AAD mà bằng cách gấp bộ ba (group_id, n, k) vào chính chuỗi ngữ cảnh "
                    "dẫn xuất khóa tải trọng. Sửa bất kỳ byte nào trong ba trường đó sẽ dẫn xuất ra khóa khác "
                    "và thẻ Poly1305 lập tức hỏng — đây chính là thuộc tính chịu lực của lược đồ.",
           11, False, "#3a4a5a", w=1100)
    emit(f, 3)


def fig_3_7():
    f = Figure("Hinh-3-07-giau-tin-encrypt-then-embed",
               "Hình 3.7 — Kiến trúc giấu tin theo nguyên tắc mã hóa-rồi-nhúng",
               "Che giấu KHÔNG phải là bí mật: toàn bộ tính bí mật nằm ở tầng AEAD, không nằm ở tầng sóng mang",
               1220, 830,
               SRC + "crates/sv-stego/src/{pipeline,seal,envelope,capacity,selector,embed}.rs; "
                     "crates/sv-stego/src/carrier/{spatial,jpeg}.rs")

    f.zone(50, 92, 560, 270, "Tầng bí mật + toàn vẹn — RANH GIỚI AN TOÀN DUY NHẤT", "ok", "")
    f.node("pl", 74, 136, 240, 56, "Dữ liệu cần giấu", "key")
    f.node("pw2", 74, 204, 240, 56, "Mật khẩu", "key")
    f.node("salt2", 74, 272, 240, 56, "Muối 16 byte công khai", "plain", sub="nằm trong header SVSTEG")
    f.node("sealer", 350, 176, 236, 130, "Argon2idSecretboxSealer", "crypto",
           sub="Argon2id(mật khẩu, muối) → Key32; secretbox seal/open. "
               "Không hề có nguyên thủy mật mã mới nào được tạo ra ở đây.")

    f.zone(650, 92, 500, 270, "Tầng che giấu — KHÔNG tuyên bố bất kỳ tính bí mật nào", "ext", "")
    f.node("cover", 674, 136, 220, 56, "Ảnh bìa", "store", sub="PNG / BMP / JPEG")
    f.node("carrier", 910, 136, 216, 56, "Carrier", "domain", sub="Spatial (LSB) hoặc Jpeg (hệ số DCT)")
    f.node("cap", 674, 204, 452, 52, "capacity::fits — chặn tải quá dung lượng TRƯỚC khi chạy Argon2id",
           "ok", fontsize=11)
    f.node("sel", 674, 268, 452, 60, "SiteSelector: Sequential hoặc Permuted", "domain",
           sub="hoán vị Fisher–Yates một phần, hạt giống = BLAKE3(muối) — chỉ làm mờ dấu vết thống kê",
           fontsize=11.5)

    f.node("env", 50, 400, 1100, 90, "Khung SVSTEG — header 54 byte cố định, số nguyên big-endian", "store",
           sub="magic \"SVSTEG\" (6) ‖ version (1) ‖ flags (1: bit0 sóng mang JPEG, bit1 hoán vị, "
               "bit2 mặt bit > 0 dành riêng) ‖ kdf_alg (1) ‖ aead_alg (1) ‖ salt (16) ‖ nonce (24) ‖ ct_len u32 (4)")

    f.node("emb", 50, 512, 530, 84, "LsbEmbedder::write_bits", "domain",
           sub="432 vị trí đầu tiên mang header theo thứ tự tuần tự (để đọc được trước khi biết lịch hoán vị); "
               "phần thân đi theo lịch của SiteSelector")
    f.node("out", 620, 512, 530, 84, "Ảnh chứa tin, cùng định dạng vật chứa", "store",
           sub="PNG/BMP mã hóa lại không mất mát; JPEG ghi lại ở miền hệ số lượng tử hóa")

    f.node("ex", 50, 618, 1100, 92, "Đường trích xuất và tính chống dò oracle", "danger",
           sub="Ảnh sạch, sai mật khẩu, sóng mang bị sửa và khung bị cắt cụt đều trả về NoPayload / BadFrame / "
               "AuthFailed — cả ba đều gộp thành đúng một mã SV-UNAUTHORIZED. Kẻ tấn công thậm chí không "
               "biết được một tấm ảnh CÓ mang dữ liệu hay không. Chỉ ảnh không giải mã nổi mới là SV-MALFORMED.")

    f.edge("pl", "sealer", "")
    f.edge("pw2", "sealer", "")
    f.edge("salt2", "sealer", "")
    f.edge("cover", "carrier", "")
    f.edge("carrier", "cap", "", bend="orthoV")
    f.edge("cap", "sel", "")
    f.edge("sealer", "env", "nonce ‖ bản mã", bend="orthoV", lx=468, ly=384)
    f.edge("sel", "env", "", bend="orthoV")
    f.edge("env", "emb", "", bend="orthoV")
    f.edge("emb", "out", "")
    f.edge("out", "ex", "", bend="orthoV")

    f.text(50, 748, "Hệ quả trực tiếp của thứ tự này: nếu tầng che giấu bị phá (ai đó phát hiện có dữ liệu ẩn), "
                    "tính bí mật của dữ liệu vẫn nguyên vẹn vì nó nằm sau AEAD. Ngược lại, tài liệu thiết kế "
                    "của dự án nói rõ rằng che giấu không được coi là biện pháp bảo mật.",
           11, False, "#3a4a5a", w=1120)
    emit(f, 3)


def fig_3_8():
    f = Figure("Hinh-3-08-phat-hien-giau-tin",
               "Hình 3.8 — Bảng các bộ dò giấu tin và cơ chế hợp nhất mức nghi ngờ",
               "Kết quả là mức NGHI NGỜ theo phương pháp thực nghiệm, không bao giờ là kết luận \"ảnh sạch\"",
               1180, 760,
               SRC + "crates/sv-stego/src/detect/{mod,appended,chi_square,rs,jpeg_dct}.rs; "
                     "sv_types::{StegoSignal, StegoDetectReport, Suspicion}")

    f.node("img", 50, 110, 220, 62, "Tệp ảnh đầu vào", "store", shape="cyl")
    f.node("disp", 310, 110, 260, 62, "Phân nhánh theo vật chứa", "app",
           sub="FF D8 FF ⇒ JPEG, ngược lại ⇒ PNG/BMP", shape="rhombus", fontsize=11)

    f.zone(50, 200, 540, 250, "Bảng dò cho ảnh không mất mát (PNG / BMP)", "domain", "")
    f.node("d1", 74, 244, 490, 58, "AppendedDataDetector", "domain",
           sub="dữ liệu nằm sau EOF hợp lệ + entropy Shannon + quét chữ ký tệp nhúng", fontsize=11.5)
    f.node("d2", 74, 312, 490, 58, "ChiSquareDetector", "domain",
           sub="kiểm định χ² trên cặp giá trị mẫu — dấu hiệu kinh điển của LSB tuần tự tỉ lệ cao", fontsize=11.5)
    f.node("d3", 74, 380, 490, 58, "RsDetector", "domain",
           sub="phân tích Regular/Singular theo hàm lật, ước lượng tỉ lệ nhúng", fontsize=11.5)

    f.zone(630, 200, 520, 180, "Bảng dò cho JPEG", "domain", "")
    f.node("j1", 654, 244, 474, 58, "jpeg_appended_signal", "domain",
           sub="dữ liệu nằm sau dấu EOI", fontsize=11.5)
    f.node("j2", 654, 312, 474, 58, "jpeg_dct::analyze", "domain",
           sub="χ² trên LSB của hệ số DCT đã lượng tử — miền nhúng thật của JPEG", fontsize=11.5)

    f.node("fuse", 630, 400, 520, 90, "Hợp nhất: lấy điểm CAO NHẤT trong bảng", "app",
           sub="≥ 0,75 → High · ≥ 0,45 → Elevated · ≥ 0,20 → Low · còn lại → NotObserved")

    f.node("rep", 310, 512, 560, 92, "StegoDetectReport", "store",
           sub="suspicion + danh sách StegoSignal (tên bộ dò, điểm 0…1, diễn giải) + câu cảnh báo cố định: "
               "\"suy đoán theo phương pháp thực nghiệm; nghi ngờ tăng không phải là bằng chứng, và "
               "không có tín hiệu cũng không phải là bằng chứng vắng mặt\"")

    f.node("honest", 50, 512, 220, 92, "Mức thấp nhất là NotObserved", "note",
           sub="cố ý KHÔNG có mức \"Clean\"")

    f.edge("img", "disp", "")
    f.edge("disp", "d1", "", bend="orthoV")
    f.edge("disp", "j1", "", bend="orthoV")
    f.edge("d1", "fuse", "", bend="ortho")
    f.edge("d2", "fuse", "", bend="ortho")
    f.edge("d3", "fuse", "", bend="ortho")
    f.edge("j1", "fuse", "", bend="orthoV")
    f.edge("j2", "fuse", "", bend="orthoV")
    f.edge("fuse", "rep", "", bend="ortho")

    f.text(50, 650, "Phạm vi trung thực do chính tài liệu của mô-đun ghi nhận: bảng dò này bắt tốt các trường hợp "
                    "giấu tin thô sơ, tỉ lệ nhúng cao hoặc kiểu \"nối thêm tệp vào sau ảnh\". Một tải trọng "
                    "sv-stego đã mã hóa, hoán vị và tỉ lệ nhúng thấp thì gần như không bị các bộ dò này phát hiện — "
                    "đó là sự thật, và cũng chính là lý do kết quả được trình bày dưới dạng mức nghi ngờ chứ "
                    "không phải một phán quyết.", 11, False, "#3a4a5a", w=1100)
    emit(f, 3)


def fig_3_9():
    f = Figure("Hinh-3-09-thuy-van-de-vo",
               "Hình 3.9 — Thủy vân vô hình, có khóa, dễ vỡ: nhúng và kiểm tra",
               "Không phải giấu tin (không mang tải trọng) và cố ý KHÔNG bền vững — mục tiêu là bằng chứng sửa đổi",
               1200, 800,
               SRC + "crates/sv-watermark/src/lib.rs (BLOCK, PRESENCE_THRESHOLD, BLOCK_CONTEXT, "
                     "PRESENCE_CONTEXT, WATERMARK_SALT)")

    f.node("pw", 50, 110, 230, 58, "Mật khẩu người dùng", "key")
    f.node("kdf", 310, 110, 230, 58, "Argon2id + muối cố định", "crypto",
           sub="muối chỉ để tách miền, không chống bảng cầu vồng")
    f.node("k", 570, 110, 200, 58, "Khóa K (32 byte)", "key", sub="không bao giờ được lưu")

    f.zone(50, 190, 1100, 250, "Nhúng (watermark_embed) — chỉ ảnh PNG / BMP", "ok", "")
    f.node("blk", 74, 234, 320, 76, "Chia ảnh thành khối 16 × 16", "domain",
           sub="hàng/cột cuối hấp thụ phần dư nên mọi khối đều ≥ 16 px mỗi cạnh")
    f.node("tag", 420, 234, 340, 76, "Nhãn từng khối", "crypto",
           sub="BLAKE3::keyed_hash(K, ngữ cảnh ‖ W ‖ H ‖ bx ‖ by ‖ nội dung)")
    f.node("cont", 790, 234, 336, 76, "\"Nội dung\" = 7 bit CAO của R, G, B", "domain",
           sub="mặt bit thấp nhất bị loại khỏi phép băm nên nhúng không làm đổi nhãn")
    f.node("blue", 74, 330, 500, 88, "Rải 256 bit nhãn lên mặt LSB kênh LAM của khối", "domain",
           sub="mọi LSB lam trong khối trở thành một bit nhãn ⇒ mọi sửa đổi nội dung đều làm hỏng nhãn")
    f.node("green", 600, 330, 526, 88, "Dấu hiệu hiện diện trên mặt LSB kênh LỤC", "domain",
           sub="chuỗi có khóa nhưng ĐỘC LẬP nội dung, dẫn từ K ‖ W ‖ H — cho phép trả lời câu hỏi "
               "\"ảnh này có mang dấu của khóa này không\" ngay cả khi mọi khối nội dung đều hỏng")

    f.zone(50, 456, 1100, 230, "Kiểm tra (watermark_verify) — thang phán quyết ba mức", "domain", "")
    f.node("q1", 74, 500, 420, 60, "Bit dấu hiệu khớp ≥ 75 %?", "app", shape="rhombus", fontsize=11.5)
    f.node("nw", 540, 490, 260, 56, "NotWatermarked", "note",
           sub="chưa đánh dấu, sai khóa, hoặc dấu bị phá hoàn toàn")
    f.node("q2", 74, 580, 420, 60, "Mọi khối tái tính đều khớp?", "app", shape="rhombus", fontsize=11.5)
    f.node("ok", 540, 570, 260, 56, "Intact", "ok", sub="ảnh nguyên vẹn từng bit")
    f.node("tp", 840, 570, 286, 56, "Tampered", "danger",
           sub="kèm danh sách khối hỏng ⇒ định vị được vùng bị sửa")

    f.edge("pw", "kdf", "")
    f.edge("kdf", "k", "")
    f.edge("k", "tag", "", bend="orthoV")
    f.edge("blk", "tag", "")
    f.edge("cont", "tag", "")
    f.edge("tag", "blue", "", bend="orthoV")
    f.edge("k", "green", "", bend="ortho")
    f.edge("q1", "nw", "không")
    f.edge("q1", "q2", "có")
    f.edge("q2", "ok", "có")
    f.edge("q2", "tp", "không", lx=900, ly=630)

    f.text(50, 720, "Đây là thủy vân DỄ VỠ: bất kỳ thao tác biên tập nào — kể cả nén lại sang JPEG — đều làm hỏng "
                    "dấu. Đó là ĐẶC TÍNH chứ không phải khuyết điểm: mục tiêu là phát hiện sửa đổi, không phải "
                    "chứng minh bản quyền. Họ thủy vân bền vững (DWT-DCT-SVD) được ghi nhận là hướng nghiên cứu "
                    "hoãn lại vì chưa có thư viện biến đổi sóng con hai chiều thuần Rust đủ tin cậy.",
           11, False, "#3a4a5a", w=1100)
    emit(f, 3)


def fig_3_10():
    f = Figure("Hinh-3-10-ban-do-lenh-ipc",
               "Hình 3.10 — Bản đồ 38 lệnh IPC và năm trạng thái quản lý",
               "Mỗi bề mặt lệnh là một đoạn độc lập, cộng thêm chứ không sửa đổi bề mặt đã có",
               1220, 840,
               SRC + "desktop/src/lib.rs generate_handler! + run(); src-tauri/src/{lib,platform,stego,meta,"
                     "watermark}.rs")

    f.node("fe", 460, 96, 300, 50, "frontend/main.js — invoke(...)", "ui", fontsize=12.5)
    f.node("tauri", 460, 162, 300, 50, "Tauri 2 — 38 #[tauri::command]", "ui", fontsize=12.5)

    groups = [
        ("Backend = AppVault<AgePayloadCipher>", "app", 50, 250, [
            "app_info", "vault_create", "vault_unlock", "vault_lock",
            "vault_change_passphrase", "vault_meta", "export_signing_public_key",
            "item_list", "item_add", "item_extract", "integrity_check",
            "integrity_hash", "sign_file", "verify_file", "keys_split", "keys_recover"]),
        ("Platform = PlatformApp", "domain", 340, 250, [
            "integrity_hash_file", "integrity_verify_signature", "integrity_verify_integrity",
            "crypto_encrypt_file", "crypto_decrypt_file", "crypto_generate_signing_keypair",
            "crypto_sign_file", "shares_split_secret", "shares_split_file",
            "shares_recover_secret", "shares_export_qr", "shares_recover_from_qr", "copy_file"]),
        ("Stego = StegoApp", "crypto", 630, 250, [
            "stego_hide", "stego_extract", "stego_detect"]),
        ("Meta = MetaApp", "sys", 880, 250, [
            "metadata_available", "metadata_inspect", "metadata_sanitize", "metadata_diff"]),
    ]
    for title, kind, x, y, cmds in groups:
        h = 54 + len(cmds) * 26
        f.node(f"g{x}", x, y, 260, 48, title, kind, fontsize=11.5)
        for i, c in enumerate(cmds):
            f.node(f"c{x}_{i}", x + 14, y + 56 + i * 26, 232, 22, c, "plain", fontsize=9.8, bold=False)
        f.edge("tauri", f"g{x}", "", bend="orthoV")

    f.node("gwm", 880, 388, 260, 48, "Watermark = WatermarkApp", "store", fontsize=11.5)
    for i, c in enumerate(["watermark_embed", "watermark_verify"]):
        f.node(f"cw{i}", 894, 444 + i * 26, 232, 22, c, "plain", fontsize=9.8, bold=False)
    f.edge("tauri", "gwm", "", bend="orthoV")

    f.node("pp", 50, 700, 500, 76, "IpcPassphrase — kiểu duy nhất mang mật khẩu qua biên", "key",
           sub="tự xóa khi hủy, Debug bị che, chuyển thành SecretBytes ngay dòng đầu mỗi handler")
    f.node("err", 600, 700, 540, 76, "Mọi lệnh trả Result<T, ApiError>", "danger",
           sub="12 mã SV-* ổn định; kiểm thử ui_contract khẳng định bản đồ thông điệp của giao diện "
               "khớp 1:1 với ApiError::ALL_CODES")

    f.edge("fe", "tauri", "")
    emit(f, 3)


def fig_3_11():
    f = Figure("Hinh-3-11-ghim-bam-nhi-phan",
               "Hình 3.11 — Ghim băm nhị phân ngoài lúc biên dịch và phân giải lúc chạy",
               "Chuỗi kiểm soát chuỗi cung ứng: nạp → ghim → kiểm kiến trúc → phân giải → xác minh lại → chạy có rào",
               1200, 780,
               SRC + "desktop/build.rs (emit_pin, detect_staged_target, check_staged_arch); "
                     "desktop/src/lib.rs resolve_binary/build_backend/build_meta; "
                     "crates/sv-age/src/lib.rs new_pinned")

    f.zone(50, 92, 1100, 250, "Thời điểm biên dịch — desktop/build.rs", "ok", "")
    f.node("stage", 74, 140, 240, 66, "Nạp nhị phân vào binaries/", "ext",
           sub="age · age-keygen · exiftool")
    f.node("hashb", 348, 140, 240, 66, "Tính BLAKE3 của từng tệp", "crypto")
    f.node("emit", 622, 140, 240, 66, "Phát hằng số qua env!()", "ok",
           sub="băm được nhúng vào mã máy")
    f.node("arch", 896, 140, 230, 66, "Kiểm kiến trúc tệp", "ok",
           sub="đọc header ELF / Mach-O / PE, KHÔNG thực thi")
    f.node("mand", 74, 236, 1052, 80, "Chính sách bắt buộc và tùy chọn", "note",
           sub="age và age-keygen là BẮT BUỘC: bản release thiếu chúng thì build hỏng ngay. "
               "exiftool là TÙY CHỌN: thiếu thì mô-đun Phân tích tự tắt theo hướng an toàn "
               "(mọi lệnh trả lỗi thay vì âm thầm bỏ qua).")

    f.zone(50, 366, 1100, 250, "Thời điểm chạy — desktop/src/lib.rs", "app", "")
    f.node("res", 74, 414, 300, 76, "resolve_binary", "app",
           sub="bản release CHỈ tìm trong thư mục tài nguyên của gói hoặc cạnh tệp thực thi")
    f.node("ovr", 410, 414, 300, 76, "SV_AGE_BIN / SV_EXIFTOOL_BIN", "danger",
           sub="chỉ có hiệu lực trong bản debug — bề mặt phân giải bị đóng lại khi phát hành")
    f.node("verify", 746, 414, 380, 76, "new_pinned: băm lại rồi so sánh", "ok",
           sub="lệch băm ⇒ từ chối khởi tạo bộ điều hợp, không có đường vòng")
    f.node("run", 74, 512, 1052, 80, "Chạy có rào chắn", "sys",
           sub="env_clear() (Windows chỉ thêm lại SystemRoot, SystemDrive, TEMP, TMP cho trình nạp DLL "
               "và bộ sinh số ngẫu nhiên) · không qua shell · thư mục làm việc riêng cho ExifTool · "
               "ExifTool luôn nhận -config \"\" để tắt cơ chế cấu hình bằng mã Perl · "
               "hạn giờ tường 120 giây cho age và 60 giây cho ExifTool")

    f.node("gap", 50, 646, 1100, 76, "Khoảng trống đã ghi nhận", "danger",
           sub="Kiểm tra băm diễn ra một lần khi khởi tạo bộ điều hợp; nếu tệp nhị phân bị thay thế giữa "
               "lần kiểm tra và lần thực thi (TOCTOU) thì hệ thống không phát hiện được. Ngoài ra gói phát "
               "hành hiện chưa được ký số và công chứng (H5), nên trên macOS một bản sao bị gắn nhãn cách ly "
               "có thể bị Gatekeeper chấm dứt — đây là điểm chặn phân phối đã được xác nhận bằng thực nghiệm.")
    emit(f, 3)


def fig_3_12():
    f = Figure("Hinh-3-12-so-do-dieu-huong-giao-dien",
               "Hình 3.12 — Sơ đồ điều hướng của giao diện người dùng",
               "Thanh bên tổ chức theo MỤC TIÊU của người dùng chứ không theo tên thuật toán",
               1180, 760,
               SRC + "desktop/frontend/index.html (data-screen), main.js showScreen/wireSidebar, i18n.js")

    f.node("home", 460, 100, 260, 60, "Trang chủ", "ui",
           sub="ba thẻ bắt đầu nhanh + lưới toàn bộ công cụ")

    groups = [
        ("KÉT AN TOÀN", "app", 50, 200, ["Két an toàn (vault)"]),
        ("BẢO VỆ TỆP", "crypto", 50, 300, ["Khóa tệp (encrypt)", "Mở khóa tệp (decrypt)",
                                            "Giấu dữ liệu trong ảnh (hide)", "Hiện dữ liệu ẩn (unhide)",
                                            "Chống giả mạo tệp (watermark)"]),
        ("CHỨNG MINH TÍNH XÁC THỰC", "ok", 620, 200, ["Ký tệp (sign)", "Kiểm tra chữ ký (verify)",
                                                       "Lấy vân tay tệp (hash)",
                                                       "Kiểm tra tệp chưa bị đổi (intact)",
                                                       "Xác minh tệp tải về (verify-integrity)"]),
        ("SAO LƯU & KHÔI PHỤC", "domain", 620, 440, ["Chia nhỏ bí mật (split-secret)",
                                                      "Chia nhỏ tệp (split-file)",
                                                      "Khôi phục từ các mảnh (recover-pieces)",
                                                      "Chuyển qua mã QR (qr-transfer)"]),
        ("KIỂM TRA & LÀM SẠCH", "store", 50, 500, ["Phát hiện dữ liệu ẩn (detect)",
                                                    "Xem siêu dữ liệu (metadata-inspect)",
                                                    "Xóa siêu dữ liệu (metadata-clean)",
                                                    "So sánh siêu dữ liệu (metadata-compare)"]),
    ]
    for title, kind, x, y, screens in groups:
        f.node(f"h{x}_{y}", x, y, 300, 40, title, kind, fontsize=11.5)
        for i, s in enumerate(screens):
            f.node(f"s{x}_{y}_{i}", x + 16, y + 48 + i * 30, 268, 26, s, "plain",
                   fontsize=10, bold=False)
        f.edge("home", f"h{x}_{y}", "", bend="orthoV")

    f.node("i18n", 460, 620, 500, 80, "Bản địa hóa", "note",
           sub="i18n.js với DEFAULT_LANG = \"vi\": toàn bộ nhãn, thông điệp và mã lỗi được dịch; "
               "tiếng Anh là ngôn ngữ dự phòng")

    f.text(50, 730, "Hai màn hình \"sắp có\" (soon-hide, soon-detect) còn sót lại trong mã HTML nhưng "
                    "không được nối vào thanh điều hướng và không gọi lệnh nào — đây là mã giao diện chết "
                    "đã được ghi nhận trong bảng đối chiếu tài liệu ↔ mã nguồn (mục D-12).",
           11, False, "#3a4a5a", w=1100)
    emit(f, 3)


ALL = [fig_3_1, fig_3_2, fig_3_3, fig_3_4, fig_3_5, fig_3_6, fig_3_7, fig_3_8,
       fig_3_9, fig_3_10, fig_3_11, fig_3_12]

if __name__ == "__main__":
    for fn in ALL:
        fn()
    print("chapter3 figures:", len(ALL))
