# -*- coding: utf-8 -*-
"""Hinh chuong 2 — Phan tich va thiet ke he thong."""
from figlib import Figure, emit, _wrap as _wrapn

SRC = "Nguon: "


# ===========================================================================
# Hinh 2.1 — Bieu do ca su dung tong quat
# ===========================================================================
def fig_2_1():
    f = Figure("Hinh-2-01-use-case-tong-quat",
               "Hình 2.1 — Biểu đồ ca sử dụng tổng quát của hệ thống Secure Vault",
               "18 ca sử dụng, tương ứng 38 lệnh IPC được đăng ký trong generate_handler!",
               1300, 870,
               SRC + "desktop/src/lib.rs (generate_handler!), src-tauri/src/{lib,platform,stego,meta,watermark}.rs, "
                     "docs/architecture/02-requirements-analysis.md §2.2")

    f.zone(300, 82, 700, 690, "Phạm vi hệ thống: ứng dụng Secure Vault (chạy hoàn toàn ngoại tuyến)",
           "ext", "Sáu mô-đun chức năng trên một nền mật mã dùng chung")

    col1, col2, w = 322, 656, 300
    rows = [110 + i * 72 for i in range(9)]

    uc1 = ["Tạo két an toàn mới", "Mở khóa và khóa két", "Thêm / trích xuất tệp trong két",
           "Đổi mật khẩu két", "Kiểm tra toàn vẹn và chữ ký của két",
           "Chia khóa chủ thành k trong n mảnh", "Khôi phục két từ các mảnh khóa",
           "Mã hóa / giải mã tệp bằng mật khẩu", "Tạo cặp khóa ký và ký tệp"]
    uc2 = ["Kiểm tra chữ ký số tách rời", "Lấy vân tay BLAKE3 của tệp",
           "Kiểm tra tệp tải về theo băm / chữ ký", "Chia nhỏ bí mật hoặc tệp (k trong n)",
           "Khôi phục bí mật từ các mảnh", "Chuyển mảnh qua mã QR an toàn",
           "Giấu và hiện dữ liệu trong ảnh", "Phát hiện dấu hiệu dữ liệu ẩn",
           "Nhúng và kiểm tra thủy vân dễ vỡ"]

    for i, (a, b) in enumerate(zip(uc1, uc2)):
        f.node(f"a{i}", col1, rows[i], w, 52, a, "domain", shape="ellipse", fontsize=11.5, bold=False)
        f.node(f"b{i}", col2, rows[i], w, 52, b, "domain", shape="ellipse", fontsize=11.5, bold=False)
    f.node("meta3", col2, rows[8] + 0, 0, 0, "", "domain")  # placeholder removed below
    f.nodes.pop()
    f.node("m9", col1, rows[8] + 72, w, 52, "Xem / xóa / so sánh siêu dữ liệu", "domain",
           shape="ellipse", fontsize=11.5, bold=False)

    f.node("user", 96, 330, 96, 108, "Người dùng cuối", "ui", shape="actor")
    f.node("dev", 96, 590, 96, 108, "Nhà phát triển / đóng gói", "ui", shape="actor")

    f.node("age", 1112, 150, 96, 108, "age · age-keygen (nhị phân đi kèm)", "sys", shape="actor")
    f.node("exif", 1112, 380, 96, 108, "ExifTool (nhị phân đi kèm)", "sys", shape="actor")
    f.node("fs", 1112, 610, 96, 108, "Hệ thống tệp cục bộ", "store", shape="actor")

    for i in range(9):
        f.edge("user", f"a{i}", arrow="none")
    for i in range(9):
        f.edge("user", f"b{i}", arrow="none")
    f.edge("user", "m9", arrow="none")
    f.edge("dev", "m9", "«build» nạp và ghim băm nhị phân", arrow="none", dashed=True, lx=250, ly=770)

    f.edge("a0", "age", "sinh danh tính age", dashed=True, lx=1010, ly=140)
    f.edge("a2", "age", "mã hóa / giải mã tải trọng", dashed=True, lx=1030, ly=210)
    f.edge("m9", "exif", "tiến trình con đã ghim băm", dashed=True, lx=1010, ly=700)
    f.edge("b2", "fs", "đọc / ghi nguyên tử", dashed=True, lx=1030, ly=640)

    f.text(300, 800, "Ghi chú: Nhà phát triển là tác nhân thời điểm biên dịch (stage + ghim băm BLAKE3 "
                     "cho age, age-keygen, exiftool), không phải tác nhân lúc chạy.", 10.5, False, "#67707d", w=920)
    emit(f, 2)


# ===========================================================================
# Hinh 2.2 — Bieu do ngu canh
# ===========================================================================
def fig_2_2():
    f = Figure("Hinh-2-02-ngu-canh-he-thong",
               "Hình 2.2 — Biểu đồ ngữ cảnh của hệ thống Secure Vault",
               "Toàn bộ trao đổi diễn ra trên một máy; không có thành phần mạng trong đồ thị ứng dụng",
               1180, 730,
               SRC + "docs/architecture/01-system-overview.md §1.4; desktop/tauri.conf.json (CSP default-src 'self'); "
                     "desktop/src/lib.rs resolve_binary")

    f.node("sys", 400, 250, 380, 150, "Secure Vault — Bộ công cụ Bảo mật & Riêng tư",
           "app", sub="Ứng dụng máy tính để bàn Tauri 2 · Rust · hoàn toàn ngoại tuyến", fontsize=14)

    f.node("user", 80, 290, 200, 70, "Người dùng cuối", "ui",
           sub="một người dùng, một máy, không tài khoản")
    f.node("dev", 80, 470, 200, 70, "Nhà phát triển / đóng gói", "ui",
           sub="cargo tauri build · stage + ghim băm")

    f.node("age", 900, 90, 220, 70, "age / age-keygen v1", "sys",
           sub="X25519 + ChaCha20-Poly1305")
    f.node("exif", 900, 210, 220, 70, "ExifTool", "sys", sub="đọc / ghi siêu dữ liệu")
    f.node("fs", 900, 340, 220, 78, "Hệ thống tệp cục bộ", "store",
           sub=".svault · .svenc · .svkey · .svss · ảnh", shape="cyl")
    f.node("os", 900, 460, 220, 70, "Dịch vụ hệ điều hành", "ext",
           sub="getrandom (CSPRNG) · tệp tạm 0600")

    f.node("nonet", 400, 470, 380, 60, "KHÔNG có máy chủ, dịch vụ đám mây hay đồng bộ",
           "danger", sub="CSP default-src 'self'; không có ứng dụng khách mạng nào trong đồ thị", fontsize=11.5)

    f.edge("user", "sys", "đường dẫn tệp, mật khẩu, tham số", lx=345, ly=300)
    f.edge("sys", "user", "trạng thái, mã lỗi SV-*, kết quả không bí mật", lx=345, ly=372)
    f.edge("dev", "sys", "nhị phân đã ghim băm BLAKE3", dashed=True, lx=345, ly=440)
    f.edge("sys", "age", "stdin/stdout, env_clear, hết giờ 120 s", lx=845, ly=150)
    f.edge("sys", "exif", "argv, -config \"\", hết giờ 60 s", lx=845, ly=250)
    f.edge("sys", "fs", "đọc có giới hạn, ghi nguyên tử", lx=845, ly=330)
    f.edge("sys", "os", "sinh số ngẫu nhiên, tệp tạm", dashed=True, lx=845, ly=440)

    f.text(80, 640, "Đơn vị chia sẻ duy nhất là một tệp mà người dùng tự di chuyển: két .svault, "
                    "tệp .svenc, các mảnh Shamir hoặc ảnh mang dữ liệu ẩn. Hệ thống không có kênh truyền nào.",
           11, False, "#3a4a5a", w=1020)
    emit(f, 2)


# ===========================================================================
# Hinh 2.3 — Ranh gioi tin cay
# ===========================================================================
def fig_2_3():
    f = Figure("Hinh-2-03-ranh-gioi-tin-cay",
               "Hình 2.3 — Bốn ranh giới tin cậy và cơ chế kiểm soát trên mỗi ranh giới",
               "TB-1 … TB-4 theo docs/architecture/03-system-architecture.md §3.6",
               1240, 900,
               SRC + "src-tauri/src/passphrase.rs; crates/sv-age/src/lib.rs:62,108,147; "
                     "crates/sv-core/src/container.rs:333; Cargo.toml (exclude=[\"desktop\"])")

    f.zone(40, 80, 400, 150, "Vùng ít tin cậy — giao diện webview", "danger",
           "JavaScript / DOM, không giữ khóa")
    f.node("ui", 70, 130, 340, 76, "Giao diện tĩnh HTML · CSS · JS",
           "ui", sub="chỉ giữ SessionHandle mờ; hiển thị mã lỗi SV-*")

    f.zone(40, 268, 700, 300, "Lõi tin cậy — tiến trình Rust", "ok",
           "#![forbid(unsafe_code)] ngoài hai crate FFI")
    f.node("cmd", 70, 315, 300, 66, "38 hàm #[tauri::command]", "app",
           sub="desktop/src/lib.rs")
    f.node("surf", 70, 400, 300, 66, "CommandSurface + 4 bề mặt lệnh", "app",
           sub="AppVault · PlatformApp · StegoApp · MetaApp · WatermarkApp")
    f.node("dom", 70, 486, 300, 62, "Sáu crate nghiệp vụ", "domain",
           sub="sv-core · sv-platform · sv-stego · sv-meta · sv-qr · sv-watermark")
    f.node("sec", 410, 350, 300, 180, "Bí mật trong bộ nhớ", "key",
           sub="Key32 / SecretBytes / KeyShare — tự xóa khi hủy, Debug bị che, không Serialize")

    f.zone(790, 268, 410, 140, "Vùng tiến trình con ngoài", "sys",
           "nhị phân đi kèm, được ghim băm BLAKE3")
    f.node("age", 815, 312, 170, 76, "age / age-keygen", "sys", sub="hết giờ 120 s")
    f.node("exif", 1005, 312, 170, 76, "exiftool", "sys", sub="hết giờ 60 s, -config \"\"")

    f.zone(790, 450, 410, 200, "Vùng lưu trữ tại chỗ", "store", "tệp trên đĩa của người dùng")
    f.node("vault", 815, 495, 170, 66, ".svault", "store", sub="ký + mã hóa", shape="cyl")
    f.node("art", 1005, 495, 170, 66, ".svenc · .svkey · .svss", "store", sub="AEAD", shape="cyl")
    f.node("img", 815, 578, 360, 52, "ảnh mang dữ liệu ẩn / thủy vân (PNG · BMP · JPEG)", "store",
           fontsize=11)

    f.zone(40, 610, 700, 130, "Ranh giới xây dựng — TB-4", "ext",
           "desktop/ bị loại khỏi workspace nên cây phụ thuộc webview không lọt vào cổng kiểm toán")
    f.node("deny", 70, 655, 320, 66, "cargo deny + cargo audit", "ok",
           sub="chỉ soi phần lõi đã kiểm toán")
    f.node("webv", 410, 655, 300, 66, "cây phụ thuộc webview", "ext",
           sub="quét riêng, ngoài cổng giấy phép")

    f.edge("ui", "cmd", "TB-1 · IPC JSON: đường dẫn + DTO không bí mật; mật khẩu là IpcPassphrase",
           bend="orthoV", lx=250, ly=258)
    f.edge("cmd", "surf", "")
    f.edge("surf", "dom", "")
    f.edge("surf", "sec", "cấp phát / xóa", bend="ortho", lx=395, ly=410)
    f.edge("dom", "age", "TB-2 · env_clear, không shell, hết giờ", bend="ortho", lx=770, ly=470)
    f.edge("dom", "exif", "", bend="ortho")
    f.edge("dom", "vault", "TB-3 · ghi nguyên tử, từ chối ghi đè", bend="ortho", lx=770, ly=560)
    f.edge("deny", "webv", "loại trừ", arrow="open", dashed=True)

    f.text(40, 790, "TB-1: không bí mật nào nằm trong DTO; lỗi trả về là mã SV-* đã hợp nhất để chống dò oracle. "
                    "TB-2: nhị phân được ghim băm BLAKE3, chạy với môi trường đã xóa, không qua shell, có hạn giờ tường. "
                    "TB-3: container được ký trên gốc ràng buộc và ghi bằng temp + rename. "
                    "TB-4: cây phụ thuộc nặng của webview không được phép ảnh hưởng tới cổng kiểm toán của lõi.",
           10.8, False, "#3a4a5a", w=1160)
    emit(f, 2)


# ===========================================================================
# Hinh 2.4 — Kien truc phan tang
# ===========================================================================
def fig_2_4():
    f = Figure("Hinh-2-04-kien-truc-phan-tang",
               "Hình 2.4 — Kiến trúc phân tầng của hệ thống (L0 – L5)",
               "Khối một-mảnh có mô-đun, tiêm phụ thuộc, kiểu cổng–bộ điều hợp tại lõi mật mã",
               1180, 880,
               SRC + "docs/architecture/03-system-architecture.md §3.2; Cargo.toml; crates/*/Cargo.toml")

    lanes = [
        ("L5", "Tầng trình bày — desktop/ (bị loại khỏi workspace)", "ui", 96),
        ("L4", "Tầng ứng dụng / IPC — sv-app (src-tauri/)", "app", 226),
        ("L3", "Tầng nghiệp vụ — không FFI, tổng quát trên ABI", "domain", 356),
        ("L2", "Tầng bộ điều hợp mật mã", "crypto", 496),
        ("L1", "Tầng ABI và ràng buộc nguyên thủy", "sys", 606),
        ("L0", "Hợp đồng DTO / lỗi dùng chung", "store", 716),
    ]
    for code, name, kind, y in lanes:
        h = 118 if code in ("L5", "L4", "L3") else (98 if code in ("L2", "L1") else 78)
        f.zone(150, y, 990, h, f"{code} — {name}", kind)
        f.text(96, y + 34, code, 17, True, "#5b6675", anchor="start", w=60)

    f.node("fe", 175, 132, 300, 62, "frontend/ — giao diện tĩnh", "ui",
           sub="index.html · main.js · i18n.js · styles.css")
    f.node("shell", 500, 132, 300, 62, "desktop/src/lib.rs — vỏ Tauri", "ui",
           sub="38 #[tauri::command] · resolve_binary · run()")
    f.node("build", 825, 132, 290, 62, "desktop/build.rs", "ui",
           sub="stage + ghim băm BLAKE3 nhị phân ngoài")

    f.node("surf", 175, 262, 300, 62, "Năm bề mặt lệnh", "app",
           sub="CommandSurface · PlatformSurface · StegoSurface · MetaSurface · WatermarkSurface")
    f.node("comp", 500, 262, 300, 62, "Gốc lắp ghép", "app",
           sub="AppVault · PlatformApp · StegoApp · MetaApp · WatermarkApp")
    f.node("ipcsec", 825, 262, 290, 62, "Kiểm soát biên IPC", "app",
           sub="IpcPassphrase (tự xóa) · ánh xạ ApiError chống oracle")

    dw, gap = 148, 12
    names = [("sv-core", "két .svault"), ("sv-platform", "dịch vụ mức tệp"),
             ("sv-stego", "giấu tin ảnh"), ("sv-meta", "siêu dữ liệu"),
             ("sv-qr", "mã QR"), ("sv-watermark", "thủy vân")]
    for i, (nm, sb) in enumerate(names):
        f.node(f"d{i}", 175 + i * (dw + gap), 392, dw, 62, nm, "domain", sub=sb, fontsize=11.5)

    f.node("impl", 175, 528, 460, 56, "sv-crypto — bộ điều hợp cụ thể", "crypto",
           sub="Blake3Hasher · Argon2Kdf · SodiumMinisignSigner · SssSharer · secretbox · policy")
    f.node("age", 660, 528, 455, 56, "sv-age — bộ điều hợp FileCipher", "crypto",
           sub="điều khiển tiến trình con age đã ghim băm")

    f.node("traits", 175, 638, 460, 56, "sv-crypto-traits — ABI ổn định", "sys",
           sub="Hasher · KeyDerivation · Kdf · Signer · SecretSharer · FileCipher + kiểu giá trị")
    f.node("sod", 660, 638, 220, 56, "sv-sys-sodium", "sys", sub="FFI libsodium")
    f.node("sss", 895, 638, 220, 56, "sv-sys-sss", "sys", sub="FFI Shamir (hazmat.c)")

    f.node("types", 175, 742, 940, 44, "sv-types — DTO IPC/UI + ApiError (12 mã SV-*) · tuyệt đối không chứa bí mật",
           "store", fontsize=12)

    f.edge("fe", "shell", "invoke", lx=487, ly=150)
    f.edge("shell", "surf", "", bend="orthoV")
    f.edge("surf", "comp", "")
    f.edge("comp", "d0", "", bend="orthoV")
    f.edge("comp", "d1", "", bend="orthoV")
    f.edge("d0", "traits", "tổng quát trên ABI", bend="orthoV", lx=250, ly=610)
    f.edge("d1", "impl", "", bend="orthoV")
    f.edge("impl", "traits", "", bend="orthoV")
    f.edge("impl", "sod", "", bend="orthoV")
    f.edge("impl", "sss", "", bend="orthoV")
    f.edge("age", "traits", "", bend="orthoV")

    f.text(150, 812, "sv-core không phụ thuộc sv-crypto trong đồ thị sản phẩm: nó chỉ dựa vào ABI, "
                     "còn bộ điều hợp cụ thể do gốc lắp ghép tiêm vào. Nhờ vậy crate nghiệp vụ hoàn toàn "
                     "không dính FFI và kiểm thử được độc lập.", 10.8, False, "#3a4a5a", w=1000)
    emit(f, 2)


# ===========================================================================
# Hinh 2.5 — Do thi phu thuoc crate
# ===========================================================================
def fig_2_5():
    f = Figure("Hinh-2-05-do-thi-phu-thuoc-crate",
               "Hình 2.5 — Đồ thị phụ thuộc giữa các crate trong bản dựng sản phẩm",
               "Mũi tên hướng từ crate phụ thuộc sang crate được phụ thuộc",
               1160, 760,
               SRC + "Cargo.toml và crates/*/Cargo.toml, src-tauri/Cargo.toml, desktop/Cargo.toml")

    f.node("desk", 430, 80, 300, 58, "secure-vault-desktop (desktop/)", "ui",
           sub="loại khỏi workspace · vỏ Tauri 2")
    f.node("app", 430, 180, 300, 58, "sv-app (src-tauri/)", "app", sub="gốc lắp ghép + IPC")

    f.node("core", 60, 300, 190, 58, "sv-core", "domain", sub="két .svault")
    f.node("plat", 268, 300, 190, 58, "sv-platform", "domain", sub="dịch vụ mức tệp")
    f.node("steg", 476, 300, 190, 58, "sv-stego", "domain", sub="giấu tin")
    f.node("wm", 684, 300, 190, 58, "sv-watermark", "domain", sub="thủy vân")
    f.node("meta", 892, 300, 190, 58, "sv-meta", "domain", sub="siêu dữ liệu")
    f.node("qr", 892, 380, 190, 50, "sv-qr", "domain", sub="mã QR")

    f.node("crypto", 268, 440, 300, 58, "sv-crypto", "crypto", sub="bộ điều hợp")
    f.node("age", 60, 440, 190, 58, "sv-age", "crypto", sub="tiến trình con age")

    f.node("traits", 268, 560, 300, 58, "sv-crypto-traits", "sys", sub="ABI (traits + kiểu giá trị)")
    f.node("sod", 610, 560, 200, 58, "sv-sys-sodium", "sys", sub="FFI libsodium")
    f.node("sss", 830, 560, 200, 58, "sv-sys-sss", "sys", sub="FFI hazmat.c")

    f.node("types", 268, 665, 542, 50, "sv-types — DTO + ApiError", "store")

    for s in ("core", "plat", "steg", "wm", "meta", "qr"):
        f.edge("app", s, "", bend="orthoV")
    f.edge("desk", "app", "")
    f.edge("app", "age", "", bend="orthoV")
    f.edge("app", "crypto", "", bend="orthoV")
    f.edge("plat", "crypto", "", bend="orthoV")
    f.edge("steg", "crypto", "", bend="orthoV")
    f.edge("wm", "crypto", "", bend="orthoV")
    f.edge("crypto", "traits", "")
    f.edge("crypto", "sod", "", bend="orthoV")
    f.edge("crypto", "sss", "", bend="orthoV")
    f.edge("age", "traits", "", bend="orthoV")
    f.edge("core", "traits", "chỉ ABI, không bộ điều hợp", bend="orthoV", lx=150, ly=530)
    f.edge("core", "types", "", bend="orthoV")
    f.edge("plat", "types", "", bend="orthoV")
    f.edge("traits", "sod", "", bend="orthoV", dashed=True)

    f.node("devdep", 60, 660, 190, 58, "sv-crypto (dev-dep)", "note",
           sub="chỉ dùng cho kiểm thử của sv-core", fontsize=11)
    f.edge("core", "devdep", "chỉ khi kiểm thử", dashed=True, bend="orthoV", lx=120, ly=630)

    f.text(60, 745, "Hai điểm quan trọng: (1) sv-core chỉ phụ thuộc ABI trong bản dựng sản phẩm; "
                    "(2) tiến trình con age chỉ được nối dây ở gốc lắp ghép, nên phụ thuộc nhị phân ngoài "
                    "không lan vào tầng nghiệp vụ.", 10.8, False, "#3a4a5a", w=1040)
    emit(f, 2)


# ===========================================================================
# Hinh 2.6 — Kien truc trien khai
# ===========================================================================
def fig_2_6():
    f = Figure("Hinh-2-06-kien-truc-trien-khai",
               "Hình 2.6 — Kiến trúc triển khai và thực thi trên máy người dùng",
               "Một tiến trình, một webview, hai họ tiến trình con, không có tiến trình nền hay cổng mạng",
               1160, 830,
               SRC + "desktop/tauri.conf.json (bundle.resources), desktop/src/lib.rs run()/resolve_binary, "
                     "docs/DEPLOYMENT.md")

    f.zone(50, 80, 1060, 560, "Máy của người dùng (Windows / macOS / Linux)", "ext",
           "Không yêu cầu quyền quản trị; không có dịch vụ nền")

    f.zone(80, 128, 620, 300, "Tiến trình ứng dụng Secure Vault", "app", "")
    f.node("wv", 106, 176, 270, 84, "Luồng WebView", "ui",
           sub="WebView2 / WKWebView / WebKitGTK · CSP default-src 'self'")
    f.node("rust", 400, 176, 274, 84, "Luồng lõi Rust", "app",
           sub="bộ điều phối lệnh Tauri (thread pool)")
    f.node("state", 106, 292, 568, 110, "Năm trạng thái quản lý được đăng ký lúc khởi động", "app",
           sub="Backend = AppVault<AgePayloadCipher> · Platform · Stego · Meta (bật/tắt an toàn) · Watermark;"
               " bảng phiên giữ duy nhất khóa chủ theo SessionHandle")

    f.zone(740, 128, 340, 300, "Tài nguyên đi kèm gói cài", "sys", "bundle.resources: binaries/**/*")
    f.node("bage", 766, 176, 288, 60, "age · age-keygen", "sys", sub="bắt buộc — thiếu thì bản release lỗi build")
    f.node("bexif", 766, 250, 288, 60, "exiftool", "sys", sub="tùy chọn — thiếu thì tắt mô-đun an toàn")
    f.node("pin", 766, 324, 288, 78, "Băm BLAKE3 được ghim lúc biên dịch", "ok",
           sub="kiểm tra lại khi khởi tạo bộ điều hợp; sai băm là từ chối chạy")

    f.zone(80, 452, 1000, 168, "Hệ thống tệp cục bộ", "store", "")
    f.node("f1", 106, 500, 220, 96, ".svault", "store", shape="cyl",
           sub="MAGIC SVLT · header CBOR đã ký · tải trọng age")
    f.node("f2", 344, 500, 220, 96, ".svenc / .svkey", "store", shape="cyl",
           sub="Argon2id + secretbox")
    f.node("f3", 582, 500, 220, 96, ".svss (mảnh + tải trọng)", "store", shape="cyl",
           sub="SVSSS 92 byte · SVSSP")
    f.node("f4", 820, 500, 234, 96, "ảnh PNG / BMP / JPEG", "store", shape="cyl",
           sub="mang dữ liệu ẩn hoặc thủy vân")

    f.edge("wv", "rust", "IPC nội tiến trình", lx=390, ly=200)
    f.edge("rust", "state", "", bend="orthoV")
    f.edge("state", "bage", "spawn có kiểm soát", bend="ortho", lx=715, ly=250)
    f.edge("state", "bexif", "", bend="ortho")
    f.edge("pin", "bage", "xác minh", arrow="open", dashed=True)
    f.edge("state", "f1", "", bend="orthoV")
    f.edge("state", "f3", "", bend="orthoV")

    f.text(50, 672, "Bản dựng release chỉ phân giải nhị phân từ thư mục tài nguyên của gói hoặc thư mục "
                    "cạnh tệp thực thi; các biến môi trường SV_AGE_BIN / SV_AGE_KEYGEN_BIN / SV_EXIFTOOL_BIN "
                    "chỉ có hiệu lực trong bản debug. Gói phát hành hiện chưa được ký số và công chứng — "
                    "đây là hạn chế đã ghi nhận (H5) và nằm ngoài phạm vi sử dụng nội bộ.",
           11, False, "#3a4a5a", w=1040)
    emit(f, 2)


# ===========================================================================
# Hinh 2.7 — Bieu do tuan tu them tep vao ket
# ===========================================================================
def fig_2_7():
    f = Figure("Hinh-2-07-tuan-tu-them-tep",
               "Hình 2.7 — Biểu đồ tuần tự: thêm một tệp vào két (lệnh item_add)",
               "Trình tự thực tế trong VaultBackend::add_item, kể cả khóa ghi theo két và các cổng kiểm tra",
               1300, 1010,
               SRC + "src-tauri/src/service.rs add_item/write_vault/decrypt_archive; "
                     "crates/sv-core/src/container.rs pack_archive/encode/write_atomic")

    cols = [("ui", "Giao diện", 40, "ui"), ("cmd", "Lệnh Tauri", 240, "app"),
            ("be", "VaultBackend", 440, "app"), ("kh", "StdKeyHierarchy", 660, "crypto"),
            ("pc", "AgePayloadCipher", 880, "crypto"), ("ct", "container", 1100, "domain")]
    cx = {}
    for cid, name, x, kind in cols:
        w = 170
        f.node(cid, x, 92, w, 46, name, kind, fontsize=11.5)
        cx[cid] = x + w / 2

    steps = [
        ("ui", "cmd", 'invoke("item_add", { session, source, name })'),
        ("cmd", "be", "add_item(&session, source, name)"),
        ("be", None, "1. Kiểm tra tên khác rỗng; stat(source): nếu > 2 GiB trả SV-TOO-LARGE "
                     "trước khi đọc bất kỳ byte nào"),
        ("be", None, "2. Lấy khóa ghi theo đường dẫn két đã chuẩn hóa — giữ suốt chu trình "
                     "đọc-sửa-ghi để hai lệnh đồng thời không mất cập nhật"),
        ("be", "ct", "3. decode(bytes): xác minh chữ ký trên gốc ràng buộc TRƯỚC mọi thao tác khóa"),
        ("ct", "be", "OpenedContainer { header, payload }"),
        ("be", "kh", "4. derive_wrap_key(MK, WrapField::AgeIdentity, vault_uuid)"),
        ("kh", "be", "Key32 — tự xóa khi hủy"),
        ("be", None, "5. secretbox::open(khóa bọc, wrapped_age_identity); thất bại ⇒ SV-UNAUTHORIZED"),
        ("be", "pc", "6. decrypt(payload, identity) → age -d với danh tính trong tệp tạm 0600"),
        ("pc", "be", "Kho lưu trữ dạng rõ (bị xóa sạch ngay sau khi dùng)"),
        ("be", "ct", "7. unpack_archive → ItemDirectory + vùng byte nội dung"),
        ("be", None, "8. Đọc tệp nguồn, sinh item_id 16 byte ngẫu nhiên, tính BLAKE3 nội dung"),
        ("be", "ct", "9. pack_archive(toàn bộ mục cũ + mục mới) → kho lưu trữ mới"),
        ("be", "pc", "10. encrypt(archive, age_recipient) → PAYLOAD mới"),
        ("be", "kh", "11. Mở bọc khóa ký; encode() tính lại gốc ràng buộc và ký lại"),
        ("be", "ct", "12. write_atomic: tệp tạm cùng thư mục → fsync → rename"),
        ("be", "cmd", "ItemInfo { item_id, name, size_bytes, content_hash_hex } — không chứa bí mật"),
        ("cmd", "ui", "Kết quả, hoặc ApiError mang mã SV-* đã bản địa hóa"),
    ]

    y = 176
    ys = []
    for i, (a, b, lab) in enumerate(steps):
        if b is None:
            lines = _wrapn(lab, 92)
            h = 20 + len(lines) * 13
            f.node(f"sb{i}", cx[a] - 9, y - 8, 18, 18, "", "note", fontsize=8)
            f.text(cx[a] + 18, y - 1, lab, 10.4, False, "#2f3d4c", w=640)
            ys.append(y)
            y += max(38, h + 8)
        else:
            x1, x2 = cx[a], cx[b]
            span = abs(x2 - x1)
            lines = _wrapn(lab, max(24, int(span / 5.6)))
            f.node(f"pa{i}", x1 - 7, y - 7, 14, 14, "", "app", fontsize=8)
            f.node(f"pb{i}", x2 - 7, y - 7, 14, 14, "", "app", fontsize=8)
            f.edge(f"pa{i}", f"pb{i}", "", fontsize=8)
            f.text(min(x1, x2) + 12, y - 8 - (len(lines) - 1) * 12.5, lab, 10.4, False,
                   "#2f3d4c", w=span - 20)
            ys.append(y)
            y += 30 + (len(lines) - 1) * 13

    bottom = y + 6
    for cid, name, x, kind in cols:
        f.node(cid + "_l", x + 170 / 2 - 7, 138, 14, bottom - 138, "", kind,
               shape="lifeline", fontsize=8)

    f.text(40, 70, "Thứ tự các cổng là điểm cốt lõi: chữ ký container được kiểm TRƯỚC khi mật khẩu "
                   "được dùng, nên việc tệp bị sửa không thể bị lợi dụng làm oracle đoán mật khẩu.",
           11, False, "#3a4a5a", w=1220)
    emit(f, 2)


# ===========================================================================
# Hinh 2.8 — Ngan xep nguyen thuy mat ma
# ===========================================================================
def fig_2_8():
    f = Figure("Hinh-2-08-ngan-xep-nguyen-thuy",
               "Hình 2.8 — Ngăn xếp nguyên thủy mật mã: cổng → bộ điều hợp → nền tảng",
               "Không có nguyên thủy tự chế; phần logic tự viết duy nhất là mã hóa định dạng minisign và "
               "chuỗi ngữ cảnh tách miền",
               1200, 730,
               SRC + "crates/sv-crypto-traits/src/lib.rs; crates/sv-crypto/src/{lib,secretbox,minisign,policy}.rs; "
                     "crates/sv-age/src/lib.rs; docs/architecture/06-security-design.md §6.7")

    heads = [("Mục đích", 60), ("Cổng (trait)", 300), ("Bộ điều hợp", 540), ("Nền tảng thực thi", 800)]
    for t, x in heads:
        f.text(x, 96, t, 12.5, True, "#3b4655", w=230)

    rows = [
        ("Dẫn xuất khóa từ mật khẩu", "Kdf", "Argon2Kdf", "crate argon2 (thuần Rust)\nArgon2id 256 MiB / t=3 / p=1"),
        ("Băm nội dung, MAC, khóa con", "Hasher + KeyDerivation", "Blake3Hasher",
         "crate blake3\nhash · keyed_hash · derive_key"),
        ("Bọc bí mật lưu trữ (AEAD)", "— (hàm secretbox)", "secretbox::seal / open",
         "libsodium crypto_secretbox\nXSalsa20-Poly1305"),
        ("Mã hóa tải trọng tệp", "FileCipher", "AgeCipher", "nhị phân age v1 đi kèm\nX25519 + ChaCha20-Poly1305"),
        ("Chữ ký số / xuất xứ", "Signer", "SodiumMinisignSigner",
         "libsodium Ed25519 + BLAKE2b\nđịnh dạng minisign tiền băm"),
        ("Chia sẻ bí mật ngưỡng", "SecretSharer", "SssSharer", "sss hazmat.c (vendored)\nShamir trên GF(2⁸)"),
    ]
    y = 118
    for i, (purpose, port, adapter, backend) in enumerate(rows):
        f.node(f"p{i}", 60, y, 230, 74, purpose, "domain", fontsize=11.3)
        f.node(f"t{i}", 300, y, 230, 74, port, "sys", fontsize=11.8)
        f.node(f"a{i}", 540, y, 250, 74, adapter, "crypto", fontsize=11.8)
        bl = backend.split("\n")
        f.node(f"b{i}", 800, y, 340, 74, bl[0], "ext", sub=bl[1] if len(bl) > 1 else "", fontsize=11.5)
        f.edge(f"p{i}", f"t{i}", "")
        f.edge(f"t{i}", f"a{i}", "")
        f.edge(f"a{i}", f"b{i}", "")
        y += 86

    f.node("policy", 300, y + 6, 490, 56, "sv-crypto::policy — sàn tham số Argon2id theo OWASP",
           "ok", sub="mem ≥ 19 456 KiB · t ≥ 2 · p ≥ 1; calibrate() đo máy thật để chọn time_cost", fontsize=11.5)
    f.node("suite", 800, y + 6, 340, 56, "CipherSuite::V1 — enum đóng", "ok",
           sub="một định danh duy nhất cho toàn bộ tổ hợp thuật toán", fontsize=11.5)
    emit(f, 2)


# ===========================================================================
# Hinh 2.9 — Phan cap khoa
# ===========================================================================
def fig_2_9():
    f = Figure("Hinh-2-09-phan-cap-khoa",
               "Hình 2.9 — Phân cấp khóa của két an toàn và cơ chế bọc khóa theo trường",
               "Khóa chủ chỉ tồn tại trong bộ nhớ; mọi khóa bọc đều gắn với UUID két và nhãn trường",
               1200, 800,
               SRC + "crates/sv-core/src/keys.rs (wrap_context, SUITE_VERSION); "
                     "crates/sv-crypto/src/secretbox.rs; src-tauri/src/service.rs create/unlock")

    f.node("pw", 60, 110, 240, 64, "Mật khẩu người dùng", "key",
           sub="IpcPassphrase → SecretBytes")
    f.node("salt", 60, 200, 240, 56, "Muối 16 byte ngẫu nhiên", "plain",
           sub="lưu công khai trong header")
    f.node("params", 60, 282, 240, 56, "Tham số Argon2id", "plain",
           sub="mem_kib · time_cost · parallelism")

    f.node("argon", 360, 176, 220, 84, "Argon2id", "crypto",
           sub="hàm dẫn xuất khóa từ mật khẩu")
    f.node("mk", 650, 176, 260, 84, "Khóa chủ MK (32 byte)", "key",
           sub="Key32, chỉ nằm trong RAM, tự xóa khi hủy — KHÔNG BAO GIỜ ghi ra đĩa")

    f.node("ctx1", 380, 330, 470, 60, "BLAKE3::derive_key(\"secure-vault/v1/wrap/age-identity:<uuid_hex>\", MK)",
           "crypto", fontsize=11, sub="ngữ cảnh đã đóng băng theo byte")
    f.node("ctx2", 380, 404, 470, 60, "BLAKE3::derive_key(\"secure-vault/v1/wrap/signing-key:<uuid_hex>\", MK)",
           "crypto", fontsize=11, sub="đổi ngữ cảnh ⇒ đổi khóa ⇒ MAC hỏng")

    f.node("wk1", 900, 330, 240, 60, "Khóa bọc A", "key", sub="cho danh tính age")
    f.node("wk2", 900, 404, 240, 60, "Khóa bọc S", "key", sub="cho khóa ký Ed25519")

    f.node("w1", 380, 506, 320, 74, "wrapped_age_identity", "store",
           sub="secretbox(nonce 24 B ‖ ciphertext + thẻ 16 B) — nằm trong header CBOR")
    f.node("w2", 730, 506, 320, 74, "wrapped_signing_key", "store",
           sub="secretbox(nonce ‖ ciphertext + thẻ) — nằm trong header CBOR")

    f.node("id", 380, 616, 320, 62, "Danh tính age (tạm thời)", "key",
           sub="giải mã tải trọng rồi bị hủy ngay trong một thao tác")
    f.node("sk", 730, 616, 320, 62, "Khóa ký Ed25519 (tạm thời)", "key",
           sub="ký gốc ràng buộc rồi bị hủy ngay")

    f.node("shares", 60, 560, 260, 118, "Chia ngưỡng khóa chủ", "ok",
           sub="SssSharer.split(MK, n, k) → n mảnh 33 byte;\nchỉ k mảnh mới khôi phục được MK;\nmảnh không bao giờ nằm trong két")

    f.edge("pw", "argon", "", bend="orthoV")
    f.edge("salt", "argon", "", bend="orthoV")
    f.edge("params", "argon", "", bend="orthoV")
    f.edge("argon", "mk", "")
    f.edge("mk", "ctx1", "", bend="orthoV")
    f.edge("mk", "ctx2", "", bend="orthoV")
    f.edge("ctx1", "wk1", "")
    f.edge("ctx2", "wk2", "")
    f.edge("wk1", "w1", "secretbox::seal / open", bend="orthoV", lx=800, ly=478)
    f.edge("wk2", "w2", "", bend="orthoV")
    f.edge("w1", "id", "")
    f.edge("w2", "sk", "")
    f.edge("mk", "shares", "Shamir k trong n", bend="orthoV", lx=470, ly=140)

    f.text(60, 716, "Vì UUID két và nhãn trường đều nằm trong chuỗi ngữ cảnh, một khối bí mật đã bọc không thể "
                    "bị mang sang két khác (chống cấy ghép) cũng không thể bị hoán đổi giữa hai trường "
                    "(chống nhầm lẫn trường): ngữ cảnh sai sẽ dẫn xuất khóa sai và thẻ xác thực Poly1305 hỏng.",
           11, False, "#3a4a5a", w=1090)
    emit(f, 2)


# ===========================================================================
# Hinh 2.10 — Quy trinh niem phong ket
# ===========================================================================
def fig_2_10():
    f = Figure("Hinh-2-10-quy-trinh-niem-phong",
               "Hình 2.10 — Quy trình mã hóa và niêm phong két (đường ghi)",
               "Trình tự thực tế: đóng gói → mã hóa age → ký gốc ràng buộc → ghi nguyên tử",
               1220, 770,
               SRC + "src-tauri/src/service.rs write_vault; crates/sv-core/src/container.rs "
                     "pack_archive/encode/binding_root/write_atomic")

    xs = [50, 300, 550, 800]
    f.node("items", xs[0], 110, 220, 76, "Danh sách mục dạng rõ", "domain",
           sub="mục đã có + mục mới thêm")
    f.node("pack", xs[1], 110, 220, 76, "pack_archive", "domain",
           sub="DIR_LEN ‖ CBOR(ItemDirectory) ‖ byte nội dung")
    f.node("arch", xs[2], 110, 220, 76, "Kho lưu trữ dạng rõ", "key",
           sub="danh mục tệp nằm BÊN TRONG vùng sẽ được mã hóa")
    f.node("age", xs[3], 110, 220, 76, "age -e -r <recipient>", "crypto",
           sub="X25519 + ChaCha20-Poly1305")

    f.node("payload", xs[3], 240, 220, 70, "PAYLOAD", "store", sub="một khối mã age duy nhất")
    f.node("hdr", xs[2], 240, 220, 70, "HEADER (CBOR)", "store",
           sub="suite · uuid · kdf · khóa đã bọc · khóa công khai")
    f.node("pre", xs[1], 240, 220, 70, "Tiền tố", "store", sub="MAGIC ‖ VERSION ‖ HEADER_LEN")

    f.node("hd", xs[1], 360, 220, 62, "BLAKE3(tiền tố ‖ header)", "crypto", fontsize=11)
    f.node("pd", xs[3], 360, 220, 62, "BLAKE3(payload)", "crypto", fontsize=11)
    f.node("root", xs[2], 452, 220, 66, "Gốc ràng buộc", "key",
           sub="BLAKE3(header_digest ‖ payload_digest)")
    f.node("sign", xs[2], 552, 220, 66, "Ký minisign (Ed25519)", "crypto",
           sub="tiền băm BLAKE2b-512")

    f.node("file", 50, 452, 220, 166, "Tệp .svault", "store", shape="cyl",
           sub="MAGIC ‖ VERSION ‖ HEADER_LEN ‖ HEADER ‖ PAYLOAD ‖ SIG_TRAILER")
    f.node("atomic", 800, 552, 220, 66, "write_atomic", "ok",
           sub="temp cùng thư mục → fsync → rename")

    f.edge("items", "pack", "")
    f.edge("pack", "arch", "")
    f.edge("arch", "age", "")
    f.edge("age", "payload", "")
    f.edge("payload", "pd", "", bend="orthoV")
    f.edge("hdr", "pre", "", arrow="none")
    f.edge("pre", "hd", "", bend="orthoV")
    f.edge("hd", "root", "")
    f.edge("pd", "root", "")
    f.edge("root", "sign", "")
    f.edge("sign", "atomic", "SIG_TRAILER", bend="ortho", lx=790, ly=530)
    f.edge("atomic", "file", "", bend="ortho")

    f.text(50, 662, "Hai bản tóm lược thành phần được TÍNH LẠI mỗi lần đọc chứ không lưu trong tệp, nên không thể "
                    "ghép header của tệp này với payload của tệp khác. Do danh mục tệp nằm trong vùng đã mã hóa, "
                    "một két đang khóa không để lộ tên, kích thước hay số lượng mục — chỉ lộ tổng độ dài bản mã.",
           11, False, "#3a4a5a", w=1120)
    emit(f, 2)


# ===========================================================================
# Hinh 2.11 — Quy trinh mo khoa
# ===========================================================================
def fig_2_11():
    f = Figure("Hinh-2-11-quy-trinh-mo-khoa",
               "Hình 2.11 — Quy trình mở khóa và giải mã, theo đúng thứ tự các cổng kiểm tra",
               "Chống dò oracle: xác thực tệp trước, xác thực người dùng sau",
               1120, 930,
               SRC + "src-tauri/src/service.rs unlock/decrypt_archive; crates/sv-core/src/container.rs "
                     "parse_framing/decode; crates/sv-core/src/error.rs")

    x = 330
    f.node("s0", x, 96, 400, 54, "Người dùng chọn tệp két và nhập mật khẩu", "ui")
    f.node("s1", x, 172, 400, 54, "read_file: stat rồi mới đọc, chặn tệp > 2 GiB", "app")
    f.node("d1", x, 248, 400, 62, "Đúng MAGIC \"SVLT\" và FORMAT_VERSION = 1?", "domain", shape="rhombus",
           fontsize=11)
    f.node("d2", x, 336, 400, 62, "Chữ ký minisign trên gốc ràng buộc hợp lệ?", "domain", shape="rhombus",
           fontsize=11)
    f.node("s2", x, 424, 400, 60, "validate_kdf: chặn tham số Argon2 vượt trần trước khi chạy",
           "ok", sub="mem ≤ 4 GiB, t ≤ 64, p ≤ 64", fontsize=11)
    f.node("s3", x, 500, 400, 54, "Argon2id(mật khẩu, muối, tham số) → MK", "crypto")
    f.node("s4", x, 570, 400, 54, "derive_wrap_key(MK, age-identity, uuid)", "crypto")
    f.node("d3", x, 640, 400, 62, "secretbox::open(danh tính age) thành công?", "domain", shape="rhombus",
           fontsize=11)
    f.node("s5", x, 728, 400, 60, "Tạo phiên: session_id ngẫu nhiên 32 byte ↦ (MK, đường dẫn)", "app",
           sub="chỉ khóa chủ được giữ; danh tính và khóa ký sinh lại theo từng thao tác", fontsize=11)

    f.node("e1", 810, 250, 260, 58, "SV-MALFORMED", "danger", sub="không phải tệp két")
    f.node("e1b", 810, 320, 260, 58, "SV-INCOMPATIBLE-VERSION", "danger", sub="phiên bản định dạng lạ")
    f.node("e2", 810, 396, 260, 58, "SV-CORRUPTED", "danger", sub="tệp hỏng hoặc bị sửa đổi")
    f.node("e3", 810, 650, 260, 58, "SV-UNAUTHORIZED", "danger",
           sub="sai mật khẩu HOẶC sai mảnh khôi phục — hợp nhất một mã")

    f.node("note", 40, 336, 250, 300, "Vì sao thứ tự này quan trọng?", "note",
           sub="Cổng chữ ký nằm TRƯỚC cổng mật khẩu và không dùng đến bất kỳ thông tin bí mật nào. "
               "Nhờ vậy kết quả \"tệp bị sửa\" không thể bị dùng làm tín hiệu phân biệt mật khẩu đúng/sai. "
               "Ngược lại, mọi thất bại ở cổng mật khẩu đều trả về đúng một mã duy nhất.", fontsize=12)

    f.edge("s0", "s1", "")
    f.edge("s1", "d1", "")
    f.edge("d1", "s2", "", arrow="none")
    f.edge("d1", "e1", "không", lx=790, ly=270)
    f.edge("d1", "d2", "có")
    f.edge("d2", "e2", "không", lx=790, ly=400)
    f.edge("d2", "s2", "có")
    f.edge("s2", "s3", "")
    f.edge("s3", "s4", "")
    f.edge("s4", "d3", "")
    f.edge("d3", "e3", "không", lx=790, ly=655)
    f.edge("d3", "s5", "có")
    f.edge("d1", "e1b", "", dashed=True)

    f.text(40, 830, "Đường khôi phục bằng mảnh (recover) đi theo đúng khung này, chỉ khác ở chỗ MK được "
                    "tái tạo bằng SssSharer::combine thay vì Argon2id; cổng tín nhiệm cuối cùng vẫn là "
                    "phép mở bọc danh tính age, nên hai đường thất bại theo cùng một cách.",
           11, False, "#3a4a5a", w=1000)
    emit(f, 2)


# ===========================================================================
# Hinh 2.12 — Bo cuc byte .svault
# ===========================================================================
def fig_2_12():
    f = Figure("Hinh-2-12-bo-cuc-svault",
               "Hình 2.12 — Bố cục byte của container .svault và phạm vi chữ ký",
               "Định dạng tự mô tả: 4 byte MAGIC + phiên bản u16 LE, phân tích rẻ trước mọi thao tác mật mã",
               1180, 720,
               SRC + "crates/sv-core/src/format.rs (MAGIC, FORMAT_VERSION); "
                     "crates/sv-core/src/container.rs (HEADER_OFFSET, MAX_HEADER_LEN, binding_root)")

    segs = [("MAGIC\n\"SVLT\"", 120, "sys"), ("FORMAT_VERSION\nu16 LE = 1", 130, "sys"),
            ("HEADER_LEN\nu32 LE", 120, "sys"), ("HEADER (CBOR)\n≤ 1 MiB", 250, "domain"),
            ("PAYLOAD\nmột khối mã age", 260, "crypto"), ("SIG_TRAILER\nđịnh dạng minisign", 220, "ok")]
    x = 50
    for i, (lab, w, kind) in enumerate(segs):
        a, b = lab.split("\n")
        f.node(f"s{i}", x, 130, w, 84, a, kind, sub=b, fontsize=11.8)
        x += w
    f.text(50, 122, "0", 10, False, "#77808c")
    f.text(170, 122, "4", 10, False, "#77808c")
    f.text(300, 122, "6", 10, False, "#77808c")
    f.text(420, 122, "10", 10, False, "#77808c")
    f.text(670, 122, "10 + HEADER_LEN", 10, False, "#77808c", w=140)

    f.node("hdig", 300, 268, 370, 62, "header_digest = BLAKE3(byte 0 … 10+HEADER_LEN)", "crypto",
           fontsize=11)
    f.node("pdig", 700, 268, 300, 62, "payload_digest = BLAKE3(PAYLOAD)", "crypto", fontsize=11)
    f.node("root", 480, 366, 420, 66, "Gốc ràng buộc = BLAKE3(header_digest ‖ payload_digest)", "key",
           fontsize=12)
    f.node("sig", 480, 460, 420, 62, "Chữ ký Ed25519 định dạng minisign trên gốc ràng buộc", "ok",
           sub="tiền băm BLAKE2b-512, kèm chữ ký toàn cục ràng buộc trusted comment", fontsize=11.5)

    f.node("note", 50, 268, 220, 254, "Không lưu hai bản tóm lược", "note",
           sub="header_digest và payload_digest được tính lại mỗi lần đọc, không nằm trong tệp. "
               "Vì thế header của tệp A không thể ghép với payload của tệp B: gốc ràng buộc thay đổi "
               "và chữ ký lập tức sai.", fontsize=12)

    f.edge("s3", "hdig", "", bend="orthoV")
    f.edge("s4", "pdig", "", bend="orthoV")
    f.edge("hdig", "root", "", bend="orthoV")
    f.edge("pdig", "root", "", bend="orthoV")
    f.edge("root", "sig", "")
    f.edge("sig", "s5", "ghi vào phần đuôi", bend="ortho", lx=1050, ly=330)

    f.node("pl", 50, 566, 1080, 84, "Bên trong PAYLOAD sau khi giải mã", "domain",
           sub="DIR_LEN (u32 LE) ‖ CBOR(ItemDirectory) ‖ byte của các mục nối tiếp nhau "
               "— danh mục tệp do đó cũng được mã hóa và không lộ khi két đang khóa", fontsize=12)
    emit(f, 2)


# ===========================================================================
# Hinh 2.13 — Mo hinh du lieu header
# ===========================================================================
def fig_2_13():
    f = Figure("Hinh-2-13-mo-hinh-du-lieu-header",
               "Hình 2.13 — Mô hình dữ liệu của header CBOR và danh mục tệp",
               "Trường nào công khai, trường nào là bản mã: ranh giới bí mật của định dạng",
               1180, 790,
               SRC + "crates/sv-core/src/format.rs (VaultHeader, KdfRecord, WrappedSecret, "
                     "SharePolicyRecord, ContentLayout, ItemDirectory, ItemEntry)")

    f.node("hdr", 60, 100, 470, 34, "VaultHeader  «CBOR, serde(deny_unknown_fields)»", "domain",
           fontsize=12)
    fields = [
        ("format_version : u16", "công khai", "plain"),
        ("suite : CipherSuite = V1", "công khai — enum đóng", "plain"),
        ("vault_uuid : [u8; 16]", "công khai — ràng buộc dẫn xuất khóa", "plain"),
        ("created_unix / modified_unix : u64", "công khai", "plain"),
        ("kdf : KdfRecord { salt, params }", "công khai", "plain"),
        ("wrapped_age_identity : WrappedSecret", "BẢN MÃ của bí mật", "key"),
        ("age_recipient : AgeRecipient", "công khai (khóa công khai age1…)", "plain"),
        ("wrapped_signing_key : WrappedSecret", "BẢN MÃ của bí mật", "key"),
        ("signing_public_key : [u8; 32]", "công khai — kiểm chữ ký khi chưa mở khóa", "plain"),
        ("share_policy : Option<SharePolicyRecord>", "công khai — chỉ là chính sách", "plain"),
        ("content_layout : ContentLayout { payload_len }", "công khai", "plain"),
    ]
    y = 138
    for i, (nm, note, kind) in enumerate(fields):
        f.node(f"f{i}", 60, y, 470, 40, nm, kind, sub=note, fontsize=11, bold=False)
        y += 44

    f.node("ws", 600, 140, 300, 108, "WrappedSecret", "key",
           sub="nonce : Vec<u8> (24 byte)\nciphertext : Vec<u8> (bản mã + thẻ Poly1305 16 byte)\n"
               "→ libsodium crypto_secretbox")
    f.node("kdfr", 600, 268, 300, 96, "KdfRecord", "plain",
           sub="salt : Salt([u8; 16])\nparams : KdfParams::Argon2id { mem_kib, time_cost, parallelism }")
    f.node("sp", 600, 384, 300, 76, "SharePolicyRecord", "plain",
           sub="shares_total : u8\nthreshold : u8 — mảnh KHÔNG nằm trong két")

    f.node("dir", 600, 486, 480, 34, "ItemDirectory  «nằm bên trong PAYLOAD đã mã hóa»", "domain",
           fontsize=12)
    ent = [("item_id : [u8; 16]", "định danh ổn định"),
           ("name : String", "tên hiển thị — bí mật khi két khóa"),
           ("plaintext_offset / plaintext_len : u64", "vị trí trong vùng byte nội dung"),
           ("plaintext_blake3 : [u8; 32]", "vân tay nội dung từng mục"),
           ("added_unix : u64", "thời điểm thêm")]
    y = 524
    for i, (nm, note) in enumerate(ent):
        f.node(f"e{i}", 600, y, 480, 40, nm, "store", sub=note, fontsize=11, bold=False)
        y += 44

    f.edge("f5", "ws", "", bend="ortho")
    f.edge("f7", "ws", "", bend="ortho")
    f.edge("f4", "kdfr", "", bend="ortho")
    f.edge("f9", "sp", "", bend="ortho")

    f.text(60, 630, "Header hoàn toàn KHÔNG chứa danh mục tệp. Mọi thông tin về nội dung — tên tệp, kích thước, "
                    "số lượng — đều nằm trong vùng đã mã hóa. Đây là quyết định thiết kế H3 của lược đồ M5.",
           11, False, "#3a4a5a", w=500)
    f.text(60, 700, "deny_unknown_fields là lớp phòng vệ bổ sung phía trên chữ ký: một header có trường lạ "
                    "bị từ chối ngay ở bước giải mã CBOR.", 11, False, "#3a4a5a", w=500)
    emit(f, 2)


# ===========================================================================
# Hinh 2.14 — Phong thu theo chieu sau
# ===========================================================================
def fig_2_14():
    f = Figure("Hinh-2-14-phong-thu-chieu-sau",
               "Hình 2.14 — Kiến trúc phòng thủ theo chiều sâu bảo vệ dữ liệu",
               "Bảy lớp kiểm soát; mỗi lớp có cơ chế và bằng chứng mã nguồn riêng",
               1160, 860,
               SRC + "docs/architecture/06-security-design.md §6.1–6.8; docs/M7-HARDENING.md")

    layers = [
        ("L7 · Kỷ luật dự án", "Không tự chế nguyên thủy · unsafe bị cấm toàn workspace · cargo deny/audit · CI ba hệ điều hành", "ext"),
        ("L6 · Kiểm soát tài nguyên", "Trần 2 GiB cho tệp · header ≤ 1 MiB · trần Argon2 trước xác thực · chặn bom giải nén ảnh · hạn giờ tường", "ok"),
        ("L5 · Làm cứng tiến trình con", "Ghim băm BLAKE3 · kiểm kiến trúc lúc build · env_clear · không shell · thư mục làm việc riêng · -config \"\"", "sys"),
        ("L4 · An toàn dữ liệu", "Ghi nguyên tử temp+rename · từ chối ghi đè · khóa ghi theo két · tên tệp gốc nằm trong vùng mã hóa", "store"),
        ("L3 · Toàn vẹn và xuất xứ", "Chữ ký Ed25519 trên gốc ràng buộc · BLAKE3 từng mục · thẻ AEAD trên mọi bản mã", "domain"),
        ("L2 · Bí mật trong bộ nhớ", "Key32/SecretBytes/KeyShare tự xóa · Debug bị che · không Serialize · bí mật chỉ tồn tại theo thao tác", "key"),
        ("L1 · Bí mật khi lưu trữ", "age (X25519+ChaCha20-Poly1305) cho tải trọng · Argon2id + secretbox cho khóa và tệp độc lập", "crypto"),
    ]
    y = 96
    for i, (name, mech, kind) in enumerate(layers):
        w = 1060 - i * 0
        f.node(f"l{i}", 50 + i * 20, y, w - i * 40, 76, name, kind, sub=mech, fontsize=12.5)
        y += 92

    f.node("data", 380, y + 6, 400, 60, "DỮ LIỆU CỦA NGƯỜI DÙNG", "danger", fontsize=14)

    f.text(50, y + 100, "Mô hình lỗi chống dò oracle là lớp cắt ngang: nó áp lên mọi lớp phía trên bằng cách "
                        "hợp nhất mọi thất bại chứng thực về đúng một mã SV-UNAUTHORIZED, đồng thời giữ nguyên "
                        "tính hành động được của các tình huống lành tính (sai tệp, sai phiên bản, thiếu mảnh, "
                        "tệp quá lớn, hết giờ, đích đã tồn tại).", 11, False, "#3a4a5a", w=1060)
    emit(f, 2)


# ===========================================================================
# Hinh 2.15 — Anh xa loi
# ===========================================================================
def fig_2_15():
    f = Figure("Hinh-2-15-anh-xa-loi-chong-oracle",
               "Hình 2.15 — Ánh xạ lỗi nội bộ sang mã ApiError chống dò oracle",
               "12 mã ổn định; mọi thất bại chứng thực hội tụ về một mã duy nhất",
               1200, 810,
               SRC + "crates/sv-types/src/lib.rs (ApiError, ALL_CODES, io_generic); "
                     "crates/sv-core/src/error.rs; crates/sv-platform/src/error.rs; crates/sv-stego/src/error.rs")

    f.zone(50, 96, 430, 250, "Lỗi nội bộ trong lõi (giàu thông tin)", "ext", "")
    f.node("v1", 70, 138, 390, 44, "VaultError::AuthFailed — sai mật khẩu HOẶC sai mảnh", "danger",
           fontsize=11, bold=False)
    f.node("p1", 70, 190, 390, 44, "PlatformError::AuthFailed — sai mật khẩu HOẶC bản mã bị sửa", "danger",
           fontsize=11, bold=False)
    f.node("s1", 70, 242, 390, 44, "StegoError::NoPayload | BadFrame | AuthFailed", "danger",
           fontsize=11, bold=False)
    f.node("w1", 70, 294, 390, 40, "(mọi thất bại giải mã tải trọng có khóa)", "danger",
           fontsize=11, bold=False)

    f.node("merge", 560, 190, 260, 100, "SV-UNAUTHORIZED", "key",
           sub="một mã duy nhất — kẻ tấn công không phân biệt được nguyên nhân", fontsize=14)

    f.zone(50, 372, 430, 356, "Điều kiện lành tính, không bí mật", "ok", "")
    benign = [
        ("NotFound", "SV-NOT-FOUND"),
        ("Malformed", "SV-MALFORMED — không phải tệp két / ảnh không đọc được"),
        ("Corrupted", "SV-CORRUPTED — đúng là két nhưng chữ ký hỏng"),
        ("IncompatibleVersion{found,supported}", "SV-INCOMPATIBLE-VERSION"),
        ("InsufficientShares{got,need}", "SV-INSUFFICIENT-SHARES"),
        ("TooLarge{limit,actual}", "SV-TOO-LARGE"),
        ("Timeout", "SV-TIMEOUT"),
        ("OutputExists", "SV-OUTPUT-EXISTS"),
        ("Io(_)", "SV-IO — chuỗi cố định, KHÔNG kèm đường dẫn"),
        ("Crypto(_) | Internal", "SV-INTERNAL — che kín"),
    ]
    y = 410
    for i, (a, b) in enumerate(benign):
        f.node(f"bl{i}", 70, y, 195, 30, a, "plain", fontsize=9.6, bold=False)
        f.node(f"br{i}", 275, y, 185, 30, b, "ok", fontsize=9.2, bold=False)
        f.edge(f"bl{i}", f"br{i}", "", fontsize=8)
        y += 31

    f.node("ui", 880, 300, 280, 150, "Giao diện", "ui",
           sub="Bản đồ MESSAGES trong main.js dịch mã SV-* sang thông điệp đã bản địa hóa. "
               "Kiểm thử ui_contract khẳng định bản đồ này khớp 1:1 với ApiError::ALL_CODES.")

    for s in ("v1", "p1", "s1", "w1"):
        f.edge(s, "merge", "", bend="ortho")
    f.edge("merge", "ui", "", bend="ortho")
    f.edge("br0", "ui", "", bend="ortho", dashed=True)

    f.text(50, 756, "Điểm tinh tế: kiểm tra SỐ LƯỢNG mảnh (InsufficientShares) là phép thử trước, "
                    "không phải một lần thử chứng thực, nên nó có thể tách riêng mà không tạo ra oracle; "
                    "còn việc mảnh có ĐÚNG hay không thì luôn hợp nhất vào SV-UNAUTHORIZED.",
           11, False, "#3a4a5a", w=1100)
    emit(f, 2)


# ===========================================================================
# Hinh 2.16 — Vong doi bi mat
# ===========================================================================
def fig_2_16():
    f = Figure("Hinh-2-16-vong-doi-bi-mat",
               "Hình 2.16 — Vòng đời của bí mật trong bộ nhớ và cơ chế xóa",
               "Bí mật duy nhất tồn tại suốt phiên là khóa chủ; mọi bí mật khác chỉ sống trong một thao tác",
               1200, 780,
               SRC + "crates/sv-crypto-traits/src/lib.rs (Key32/SecretBytes/KeyShare); "
                     "src-tauri/src/{passphrase,service}.rs; crates/sv-core/src/container.rs (UnpackedArchive::drop)")

    lanes = [("Nhập", 96), ("Dẫn xuất", 232), ("Sử dụng", 368), ("Hủy", 504)]
    for name, y in lanes:
        f.zone(50, y, 1100, 120, name, "ext", "")

    f.node("in1", 80, 130, 300, 72, "IpcPassphrase", "key",
           sub="tự xóa khi hủy; Debug bị che; chuyển sang SecretBytes ngay dòng đầu của handler")
    f.node("in2", 410, 130, 320, 72, "Bản sao thượng nguồn của Tauri/serde", "danger",
           sub="RỦI RO TỒN ĐỌNG N1 — nằm ngoài tầm với của ứng dụng")
    f.node("in3", 760, 130, 390, 72, "getrandom (CSPRNG hệ điều hành)", "ok",
           sub="uuid · muối · nonce · session_id · DEK · group_id")

    f.node("dv1", 80, 266, 300, 72, "Key32 — khóa chủ", "key", sub="ZeroizeOnDrop, không Serialize")
    f.node("dv2", 410, 266, 320, 72, "Key32 — khóa bọc theo trường", "key",
           sub="sinh lại mỗi thao tác, không lưu ở đâu")
    f.node("dv3", 760, 266, 390, 72, "SecretBytes / KeyShare", "key",
           sub="Box<[u8]> không dư dung lượng nên không thể tái cấp phát rồi rò rỉ")

    f.node("us1", 80, 402, 300, 72, "SessionState { master_key, vault_path }", "app",
           sub="tra cứu theo session_id mờ; UI chỉ giữ chuỗi handle")
    f.node("us2", 410, 402, 320, 72, "Danh tính age tạm thời", "crypto",
           sub="ghi ra tệp tạm 0600 chỉ trong một lệnh age -d")
    f.node("us3", 760, 402, 390, 72, "UnpackedArchive.item_bytes", "domain",
           sub="vùng dữ liệu rõ của các mục")

    f.node("de1", 80, 538, 300, 72, "vault_lock", "ok", sub="xóa khỏi bảng phiên ⇒ Key32 bị ghi 0")
    f.node("de2", 410, 538, 320, 72, "Drop của SecureIdentityFile", "ok",
           sub="ghi đè bằng 0 rồi unlink (nỗ lực tối đa)")
    f.node("de3", 760, 538, 390, 72, "Drop của UnpackedArchive", "ok",
           sub="zeroize vùng byte nội dung; pack_archive cũng xóa vùng nháp")

    f.edge("in1", "dv1", "Argon2id", bend="orthoV", lx=180, ly=248)
    f.edge("in3", "dv3", "", bend="orthoV")
    f.edge("dv1", "dv2", "BLAKE3 derive_key", lx=395, ly=290)
    f.edge("dv1", "us1", "", bend="orthoV")
    f.edge("dv2", "us2", "secretbox::open", bend="orthoV", lx=570, ly=384)
    f.edge("us2", "us3", "age -d", lx=745, ly=428)
    f.edge("us1", "de1", "", bend="orthoV")
    f.edge("us2", "de2", "", bend="orthoV")
    f.edge("us3", "de3", "", bend="orthoV")

    f.text(50, 652, "Giới hạn được thừa nhận: dự án KHÔNG khóa trang bộ nhớ (mlock/VirtualLock) vì việc đó "
                    "đòi hỏi mã unsafe theo nền tảng, trái với tư thế #![forbid(unsafe_code)] của các crate "
                    "nghiệp vụ. Biện pháp thay thế được khuyến nghị là mã hóa toàn đĩa và mã hóa vùng swap ở "
                    "mức hệ điều hành. Một kẻ tấn công đọc được bộ nhớ tiến trình nằm NGOÀI mô hình đe dọa.",
           11, False, "#3a4a5a", w=1100)
    emit(f, 2)


ALL = [fig_2_1, fig_2_2, fig_2_3, fig_2_4, fig_2_5, fig_2_6, fig_2_7, fig_2_8,
       fig_2_9, fig_2_10, fig_2_11, fig_2_12, fig_2_13, fig_2_14, fig_2_15, fig_2_16]

if __name__ == "__main__":
    for fn in ALL:
        fn()
    print("chapter2 figures:", len(ALL))
