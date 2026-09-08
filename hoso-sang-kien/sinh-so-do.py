#!/usr/bin/env python3
"""Sinh toàn bộ sơ đồ của hồ sơ (SVG + drawio) từ mô tả dữ liệu."""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from tao_so_do import Diagram  # noqa: E402

import json

# Số liệu trong sơ đồ phải lấy từ cùng nguồn với số liệu trong bảng, nếu không hình và
# bảng sẽ mâu thuẫn nhau — lỗi mà người đọc kỹ chắc chắn phát hiện.
_dk_path = pathlib.Path(__file__).parent / "bang-chung" / "du-kien.json"
DK = json.loads(_dk_path.read_text(encoding="utf-8")) if _dk_path.exists() else {}
_kq = DK.get("ket_qua_kiem_thu", {})
_host = _kq.get("host_toan_bo") or {}
_arm = _kq.get("arm64_loi_mat_ma") or {}
_iva = _kq.get("interop_age") or {}
_ivv = _kq.get("interop_vault") or {}
N_CRATE = DK.get("crate", {}).get("so_luong", "—")
S_HOST = f"{_host.get('passed', '—')} test, {_host.get('failed', 0)} lỗi" if _host else "chưa đo"
S_ARM = (f"{_arm.get('passed', '—')} test, {_arm.get('failed', 0)} lỗi trên "
         f"{_arm.get('suites', '—')} bộ kiểm thử") if _arm else "chưa đo"
S_INTEROP = f"{_iva.get('passed', 0) + _ivv.get('passed', 0)} phép đối chứng"

made = []

# =====================================================================
# H1 — Bài toán thực tế: dữ liệu nhạy cảm trên thiết bị di động
# =====================================================================
d = Diagram(
    "H1-bai-toan-thuc-te",
    "Hình 1. Bài toán bảo vệ dữ liệu nhạy cảm trên thiết bị di động",
    1040, 560,
    "Nguy cơ phát sinh khi dữ liệu nội bộ được lưu, chuyển và xử lý trên điện thoại",
)
d.box("nv", 60, 100, 210, 92,
      ["Cán bộ, giảng viên,", "học viên", "sử dụng điện thoại trong", "công tác và huấn luyện"], "neutral")
d.box("dl", 340, 100, 220, 92,
      ["Dữ liệu cần bảo vệ", "tài liệu nghiệp vụ, giáo án,", "kết quả nghiên cứu,", "ảnh/tư liệu nội bộ"], "accent")

d.note(520, 236, "Bốn nhóm nguy cơ khi thiếu công cụ bảo vệ tại chỗ", 14, "middle", True, "#B3403A")

d.box("r1", 60, 262, 220, 86,
      ["1. Mất / thất lạc thiết bị", "dữ liệu ở dạng rõ có thể", "bị đọc trực tiếp"], "danger")
d.box("r2", 300, 262, 220, 86,
      ["2. Chuyển qua dịch vụ ngoài", "ứng dụng nhắn tin, lưu trữ", "đám mây không kiểm soát"], "danger")
d.box("r3", 540, 262, 220, 86,
      ["3. Siêu dữ liệu ẩn", "toạ độ GPS, thiết bị,", "tác giả đi kèm tệp"], "danger")
d.box("r4", 780, 262, 200, 86,
      ["4. Phụ thuộc bên thứ ba", "khoá và dữ liệu do", "nhà cung cấp nắm giữ"], "danger")

d.box("nc", 300, 400, 460, 78,
      ["Nhu cầu: công cụ bảo vệ dữ liệu chạy hoàn toàn trên thiết bị",
       "không phụ thuộc mạng, không phụ thuộc dịch vụ bên ngoài,",
       "kiểm soát được mã nguồn và có thể dùng để huấn luyện"], "core")

d.arrow(270, 146, 340, 146)
d.arrow(450, 192, 170, 262)
d.arrow(450, 192, 410, 262)
d.arrow(450, 192, 650, 262)
d.arrow(450, 192, 880, 262)
d.arrow(170, 348, 480, 400)
d.arrow(410, 348, 500, 400)
d.arrow(650, 348, 560, 400)
d.arrow(880, 348, 600, 400)
d.note(520, 512, "SecureVault Mobile được xây dựng để đáp ứng nhu cầu này", 13, "middle", True, "#2E7D4F")
made.append(d.write())

# =====================================================================
# H2 — Kiến trúc phân lớp
# =====================================================================
d = Diagram(
    "H2-kien-truc-phan-lop",
    "Hình 2. Kiến trúc phân lớp của SecureVault Mobile (Android)",
    1040, 640,
    "Sáu lớp, phụ thuộc một chiều từ trên xuống; lõi mật mã không phụ thuộc giao diện",
)
d.box("l1", 120, 86, 800, 62,
      ["L1 — Giao diện (WebView): HTML/CSS/JS tĩnh, song ngữ Việt–Anh",
       "ngăn kéo điều hướng, vùng chạm ≥ 44px, không có mã nội tuyến (CSP)"], "layer")
d.box("l2", 120, 168, 800, 62,
      ["L2 — Vỏ ứng dụng (Tauri 2, thư mục app/): 38 lệnh #[tauri::command]",
       "gốc hợp thành riêng cho Android (compose/mobile.rs)"], "mobile")
d.box("l3", 120, 250, 800, 62,
      ["L3 — Bề mặt lệnh (sv-app): CommandSurface, Platform/Stego/Meta/Watermark",
       "IpcPassphrase, SessionHandle mờ, lỗi có mã an toàn (oracle-safe)"], "core")
d.box("l4", 120, 332, 800, 62,
      ["L4 — Nghiệp vụ: sv-core (.svault), sv-platform, sv-stego, sv-qr, sv-watermark",
       "không phụ thuộc backend cụ thể — chỉ phụ thuộc trait"], "core")
d.box("l5", 120, 414, 800, 62,
      ["L5 — Bộ điều hợp: sv-crypto (BLAKE3, Argon2id, Shamir, minisign),",
       "sv-age-rs (age v1 thuần Rust) và sv-meta-rs (siêu dữ liệu thuần Rust)"], "core")
d.box("l6", 120, 496, 800, 62,
      ["L6 — Nguyên hàm/FFI: libsodium (secretbox, Ed25519), hazmat.c (Shamir)",
       "biên dịch chéo sang aarch64-linux-android bằng NDK r28c / clang 19"], "core")

for y in (148, 230, 312, 394, 476):
    d.arrow(520, y, 520, y + 20)

d.note(60, 600, "Vùng xanh = lõi dùng chung, đã kiểm chứng bằng kiểm thử tự động; "
                "vùng cam = thành phần riêng cho di động", 12, "start", False, "#4B5768")
made.append(d.write())

# =====================================================================
# H3 — Tính mới cốt lõi: một lõi, hai gốc hợp thành
# =====================================================================
d = Diagram(
    "H3-loi-dung-chung",
    "Hình 3. Một lõi bảo mật, hai gốc hợp thành theo nền tảng",
    1040, 650,
    "Rào cản kỹ thuật và cách giải quyết đã được kiểm chứng bằng thực nghiệm",
)
d.box("core", 300, 92, 440, 84,
      [f"Lõi bảo mật dùng chung ({N_CRATE} thành phần Rust)",
       "định dạng .svault, phân cấp khoá, mật mã, phân loại lỗi",
       "GIỐNG HỆT NHAU trên mọi nền tảng"], "core")

d.box("cfgd", 90, 244, 380, 60, ["Biên dịch với cfg = desktop"], "neutral")
d.box("cfgm", 570, 244, 380, 60, ["Biên dịch với cfg = mobile (Android)"], "mobile")

d.box("dsk", 90, 330, 380, 108,
      ["compose/desktop.rs",
       "tiến trình con age/age-keygen ghim băm BLAKE3",
       "ExifTool cho siêu dữ liệu",
       "(không thuộc phạm vi hồ sơ này)"], "neutral", dashed=True)
d.box("mob", 570, 330, 380, 108,
      ["compose/mobile.rs",
       "RustAgePayloadCipher — mã hoá két trong tiến trình",
       "RustMetaApp — siêu dữ liệu bằng Rust thuần",
       "không sinh tiến trình con"], "mobile")

d.box("why", 570, 462, 380, 66,
      ["Vì sao bắt buộc phải thay đổi:",
       "iOS cấm sinh tiến trình; Android chặn thực thi",
       "tệp nhị phân trong vùng ghi được của ứng dụng"], "danger")

d.box("proof", 90, 462, 380, 66,
      ["Hệ quả nếu không xử lý:",
       "toàn bộ chức năng két sẽ không hoạt động",
       "trên thiết bị di động"], "danger")

d.box("bridge", 90, 556, 860, 56,
      ["Cùng một nguyên tắc áp dụng cho hai thành phần: thay phần hiện thực bên dưới, giữ nguyên mọi thứ phía trên",
       "két vẫn liên thông giữa hai nền tảng; siêu dữ liệu là chức năng chạy thật trên di động"], "core")

d.arrow(430, 176, 280, 244)
d.arrow(610, 176, 760, 244)
d.arrow(280, 304, 280, 330)
d.arrow(760, 304, 760, 330)
d.arrow(760, 438, 760, 462)
d.arrow(280, 438, 280, 462)
d.arrow(280, 528, 400, 556)
d.arrow(760, 528, 640, 556)
made.append(d.write())

# =====================================================================
# H4 — Phân cấp khoá
# =====================================================================
d = Diagram(
    "H4-phan-cap-khoa",
    "Hình 4. Phân cấp khoá và luồng mở két an toàn",
    1040, 600,
    "Mật khẩu không bao giờ được lưu; khoá chính chỉ tồn tại trong bộ nhớ phiên",
)
d.box("pw", 60, 96, 200, 70, ["Mật khẩu người dùng", "chỉ tồn tại trong RAM,", "xoá sạch sau khi dùng"], "accent")
d.box("kdf", 330, 96, 240, 70,
      ["Argon2id", "ngưỡng tối thiểu 19 MiB,", "2 vòng lặp (theo OWASP)"], "core")
d.box("mk", 640, 96, 200, 70, ["Khoá chính (MK)", "32 byte, chỉ trong", "bộ nhớ phiên"], "core")

d.box("d1", 120, 246, 210, 76, ["Khoá bọc danh tính age", "(BLAKE3 derive_key)", "mở khoá nội dung két"], "core")
d.box("d2", 380, 246, 210, 76, ["Khoá bọc khoá ký", "(BLAKE3 derive_key)", "ký tệp bằng két"], "core")
d.box("d3", 640, 246, 250, 76, ["Khoá phục hồi (tuỳ chọn)", "chia Shamir k trong n", "khôi phục khi mất mật khẩu"], "core")

d.box("payload", 250, 392, 520, 76,
      ["Nội dung két: một luồng age v1 (X25519 + ChaCha20-Poly1305)",
       "danh mục tệp được mã hoá; chữ ký minisign/Ed25519 ràng buộc phần đầu",
       "phát hiện được mọi sửa đổi hoặc ghép nối tệp"], "core")

d.arrow(260, 131, 330, 131)
d.arrow(570, 131, 640, 131)
d.arrow(700, 166, 225, 246)
d.arrow(720, 166, 485, 246)
d.arrow(750, 166, 765, 246)
d.arrow(225, 322, 400, 392)
d.arrow(485, 322, 500, 392)

d.note(520, 520, "Sai mật khẩu và tệp hỏng trả về hai mã lỗi khác nhau nhưng "
                 "không tiết lộ thông tin phân biệt được (oracle-safe)",
       12.5, "middle", False, "#4B5768")
made.append(d.write())

# =====================================================================
# H5 — Luồng tệp trên Android
# =====================================================================
d = Diagram(
    "H5-luong-tep-android",
    "Hình 5. Luồng xử lý tệp trên Android và ranh giới tin cậy",
    1040, 560,
    "Mọi xử lý diễn ra trên thiết bị; không có kết nối mạng trong toàn bộ luồng",
)
d.box("saf", 60, 110, 220, 84,
      ["Bộ chọn tệp Android (SAF)", "trả về content:// URI", "người dùng cấp quyền từng tệp"], "mobile")
d.box("stage", 330, 110, 240, 84,
      ["Vùng đệm riêng của ứng dụng", "sao chép tạm để lõi", "đọc bằng đường dẫn thật"], "mobile")
d.box("core", 620, 110, 340, 84,
      ["Lõi bảo mật (Rust)", "mã hoá / giải mã / ký / kiểm tra",
       "ghi tệp nguyên tử (tạm rồi đổi tên)"], "core")
d.box("out", 620, 250, 340, 76,
      ["Kết quả trả về người dùng", "lưu qua SAF hoặc chia sẻ", "bằng cơ chế của hệ điều hành"], "mobile")
d.box("shred", 330, 250, 240, 76,
      ["Xoá vùng đệm", "ghi đè rồi huỷ tệp tạm", "ngay khi thao tác kết thúc"], "danger")

d.arrow(280, 152, 330, 152)
d.arrow(570, 152, 620, 152)
d.arrow(790, 194, 790, 250)
d.arrow(620, 288, 570, 288)

d.note(520, 380, "Ranh giới tin cậy: toàn bộ khối trên nằm trong vùng lưu trữ riêng của ứng dụng,",
       12.5, "middle", False, "#4B5768")
d.note(520, 400, "được hệ điều hành cách ly và mã hoá ở mức tệp (File-Based Encryption).",
       12.5, "middle", False, "#4B5768")
d.note(520, 440, "Ứng dụng KHÔNG khai báo quyền truy cập mạng (INTERNET).",
       13.5, "middle", True, "#2E7D4F")
d.note(520, 470, "Điểm cần ghi nhận trung thực: bản sao tạm ở dạng rõ tồn tại trong vùng đệm",
       12, "middle", False, "#B3403A")
d.note(520, 490, "trong thời gian thao tác — đã được ghi nhận trong mô hình mối đe doạ.",
       12, "middle", False, "#B3403A")
made.append(d.write())

# =====================================================================
# H6 — Tháp bằng chứng kiểm chứng
# =====================================================================
d = Diagram(
    "H6-thap-bang-chung",
    "Hình 6. Các mức kiểm chứng của sản phẩm",
    1040, 620,
    "Mỗi tuyên bố kỹ thuật trong hồ sơ đều gắn với một mức kiểm chứng cụ thể",
)
d.box("m1", 240, 96, 560, 66,
      [f"Mức 1 — Kiểm thử đơn vị trên máy chủ: {S_HOST}",
       "toàn bộ lõi mật mã và nghiệp vụ"], "core")
d.box("m2", 240, 178, 560, 66,
      [f"Mức 2 — Tương thích định dạng: {S_INTEROP}",
       "hai chiều với age v1.2.1 thật, và mở chéo tệp .svault"], "core")
d.box("m3", 240, 260, 560, 66,
      [f"Mức 3 — Biên dịch chéo: {N_CRATE} thành phần sang aarch64-linux-android",
       "kiểm chứng tệp đối tượng thực sự là mã ARM64"], "core")
d.box("m4", 240, 342, 560, 66,
      [f"Mức 4 — Thực thi trên ARM64 (giả lập QEMU): {S_ARM}",
       "chạy thật mã lệnh ARM64 của lõi mật mã"], "core")
d.box("m5", 240, 424, 560, 66,
      ["Mức 5 — Đóng gói APK và kiểm tra tĩnh",
       "thư viện .so đúng kiến trúc, không khai báo quyền mạng"], "core")
d.box("m6", 240, 506, 560, 66,
      ["Mức 6 — Nghiệm thu trên điện thoại Android",
       "quy trình 15 bước có tiêu chí đạt, tại Phụ lục A của Thuyết minh"], "mobile")

for y in (162, 244, 326, 408, 490):
    d.arrow(520, y, 520, y + 16)

d.note(60, 596, "Nguyên tắc của hồ sơ: mỗi tuyên bố kỹ thuật đều gắn với một mức kiểm chứng cụ thể ở trên.",
       12.5, "start", True, "#12325B")
made.append(d.write())

print("Đã sinh:", ", ".join(made))
