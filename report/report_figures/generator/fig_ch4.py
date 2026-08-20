# -*- coding: utf-8 -*-
"""Hinh chuong 4 — Thu nghiem va danh gia. Moi so lieu deu lay tu tai lieu do dac cua du an."""
from figlib import Figure, emit

SRC = "Nguồn: "


def _axis(f, x0, y0, w, h, ymax, ticks, unit=""):
    """Truc toa do don gian: node duong + nhan."""
    f.node("_ax", x0 - 2, y0 + h, w + 4, 2, "", "axis", fontsize=8)
    f.node("_ay", x0 - 3, y0, 2, h, "", "axis", fontsize=8)
    for t in ticks:
        yy = y0 + h - h * t / ymax
        f.text(x0 - 10, yy + 4, f"{t:g}{unit}", 10, False, "#67707d", anchor="end", w=90)
        f.node(f"_g{t}", x0, yy, w, 1, "", "grid", fontsize=8)


def fig_4_1():
    data = [("sv-stego", 74), ("sv-platform", 46), ("sv-app (src-tauri)", 39), ("sv-core", 22),
            ("sv-crypto", 20), ("sv-watermark", 11), ("sv-meta", 10), ("sv-qr", 8),
            ("sv-age", 6), ("sv-crypto-traits", 6), ("sv-types", 4), ("sv-sys-sss", 4),
            ("sv-sys-sodium", 3)]
    f = Figure("Hinh-4-01-phan-bo-kiem-thu",
               "Hình 4.1 — Phân bố hàm kiểm thử theo crate (tổng 253 hàm)",
               "249 hàm chạy và đạt, 4 hàm gắn #[ignore] phụ thuộc biến môi trường; "
               "crate desktop có thêm 1 kiểm thử đối chiếu hợp đồng giao diện",
               1160, 660,
               SRC + "docs/architecture/08-testing-and-validation.md §8.2 (đo bằng cargo test --workspace, "
                     "ngày 17-6-2026); đối chiếu bằng cách đếm chú thích #[test] trong cây mã")

    x0, y0, h = 240, 100, 380
    bw, gap = 58, 12
    ymax = 80
    _axis(f, x0, y0, len(data) * (bw + gap) + 20, h, ymax, [0, 20, 40, 60, 80])
    for i, (name, v) in enumerate(data):
        bh = h * v / ymax
        x = x0 + 10 + i * (bw + gap)
        kind = "crypto" if v >= 40 else ("domain" if v >= 15 else "store")
        f.node(f"b{i}", x, y0 + h - bh, bw, bh, str(v), kind, fontsize=12)
        f.text(x + bw / 2, y0 + h + 18, name, 9.6, False, "#3a4a5a", anchor="middle", w=bw + 30)
    f.text(120, y0 + h / 2, "Số hàm", 11.5, True, "#3b4655", anchor="end", w=110)

    f.node("legend", 240, 560, 880, 66, "Trọng tâm kiểm thử", "note",
           sub="sv-stego: sóng mang, dung lượng, khung SVSTEG, bộ dò, tính chống oracle · "
               "sv-platform: niêm phong artifact, năm cổng của lược đồ chia sẻ, trần kích thước · "
               "sv-app: bề mặt lệnh, rào kích thước, từ chối ghi đè, khóa ghi theo két")
    emit(f, 4)


def fig_4_2():
    f = Figure("Hinh-4-02-cong-ci",
               "Hình 4.2 — Năm nhóm việc trong quy trình tích hợp liên tục",
               "Tính cả nhân bản ma trận là 9 lượt chạy cho mỗi lần đẩy mã",
               1160, 660,
               SRC + ".github/workflows/ci.yml; docs/CI-VALIDATION.md (lần chạy xanh trên commit 780444d, "
                     "ngày 15-6-2026)")

    f.node("push", 60, 250, 180, 60, "push / pull request", "ui")

    f.zone(290, 90, 500, 300, "check — ma trận Ubuntu · macOS · Windows", "ok", "")
    steps = ["cargo fmt --all --check",
             "cargo clippy --workspace --all-targets -- -D warnings",
             "cargo build --workspace --locked",
             "cargo test --workspace --locked",
             "kiểm thử đầu-cuối với age thật (setup-go → go install age)"]
    for i, s in enumerate(steps):
        f.node(f"s{i}", 312, 134 + i * 48, 456, 40, s, "plain", fontsize=10.5, bold=False)

    f.node("msrv", 840, 110, 280, 66, "msrv", "domain", sub="cố định Rust 1.96 trên Ubuntu")
    f.node("desk", 840, 192, 280, 66, "desktop (ma trận 3 hệ điều hành)", "domain",
           sub="fmt · clippy -D · kiểm thử ui_contract")
    f.node("sc", 840, 274, 280, 66, "supply-chain", "domain",
           sub="cargo-deny + cargo-audit trên lõi và cây desktop")
    f.node("sbom", 840, 356, 280, 66, "sbom", "domain", sub="sinh danh mục thành phần")

    f.edge("push", "s0", "", bend="ortho")
    f.edge("push", "msrv", "", bend="ortho")
    f.edge("push", "desk", "", bend="ortho")
    f.edge("push", "sc", "", bend="ortho")
    f.edge("push", "sbom", "", bend="ortho")

    f.node("h4", 60, 450, 1060, 90, "Kết quả đáng chú ý của lần chạy được ghi nhận", "ok",
           sub="Kiểm thử đầu-cuối age_backed_lifecycle_roundtrips chạy XANH trên máy windows-latest — "
               "đây là bằng chứng thực nghiệm đóng lại giả thuyết rủi ro H4 (lo ngại rằng env_clear() "
               "sẽ làm hỏng bộ sinh số ngẫu nhiên / trình nạp DLL của age trên Windows). "
               "Chênh lệch 127 so với 126 kiểm thử giữa Linux và Windows là do một hàm chỉ biên dịch "
               "trên Unix, không phải lỗi.")
    emit(f, 4)


def fig_4_3():
    f = Figure("Hinh-4-03-thong-luong-age",
               "Hình 4.3 — Thông lượng mã hóa và giải mã tải trọng qua tiến trình con age",
               "Đo trên một mẫu duy nhất: tệp 512 MiB, bản dựng release, macOS 14.6 arm64, age v1.3.1",
               1160, 660,
               SRC + "docs/VALIDATION-RESULTS.md §H1 (mã hóa 1,35 s; giải mã 1,69 s cho 512 MiB). "
                     "Đây là số đo thực tế, KHÔNG phải ước lượng.")

    x0, y0, h = 300, 110, 300
    ymax = 400
    _axis(f, x0, y0, 520, h, ymax, [0, 100, 200, 300, 400], " MiB/s")
    bars = [("Mã hóa (age -e)", 379, "crypto"), ("Giải mã (age -d)", 303, "ok")]
    for i, (nm, v, k) in enumerate(bars):
        bh = h * v / ymax
        x = x0 + 90 + i * 240
        f.node(f"b{i}", x, y0 + h - bh, 150, bh, f"{v} MiB/s", k, fontsize=13)
        f.text(x + 75, y0 + h + 22, nm, 11.5, True, "#3a4a5a", anchor="middle", w=220)
    f.text(180, y0 + h / 2, "Thông lượng", 11.5, True, "#3b4655", anchor="end", w=160)

    f.node("t1", 300, 460, 520, 88, "Hệ quả về hạn giờ", "note",
           sub="Với thông lượng này, hạn giờ tường 120 giây chỉ bị chạm ở khoảng 44 GiB khi mã hóa và "
               "35 GiB khi giải mã trên ổ đĩa cục bộ nhanh. Do đó hạn giờ là rủi ro ĐUÔI, không phải "
               "chế độ hỏng thường gặp.")
    f.node("t2", 850, 460, 270, 88, "Cảnh báo về phạm vi", "danger",
           sub="Chỉ một cấu hình, một lần đo, một kích thước tệp. Không đủ để rút ra đường cong "
               "thời gian theo kích thước.")
    emit(f, 4)


def fig_4_4():
    f = Figure("Hinh-4-04-dinh-bo-nho",
               "Hình 4.4 — Đỉnh bộ nhớ thường trú khi thêm một tệp vào két",
               "Một điểm ĐO THẬT (1024 MiB) và các giá trị NGOẠI SUY tuyến tính theo hệ số ≈ 2,7×",
               1160, 700,
               SRC + "docs/VALIDATION-RESULTS.md §H1: thêm tệp 1024 MiB đạt đỉnh 2 852 782 080 byte "
                     "≈ 2,66 GiB (đo bằng /usr/bin/time -l, bản dựng release)")

    x0, y0, h = 260, 110, 330
    ymax = 12.0
    _axis(f, x0, y0, 700, h, ymax, [0, 2, 4, 6, 8, 10, 12], " GiB")
    bars = [("256 MiB", 0.67, False), ("512 MiB", 1.33, False), ("1024 MiB\n(ĐO THẬT)", 2.66, True),
            ("2 GiB\n(trần cho phép)", 5.3, False), ("4 GiB\n(bị từ chối)", 10.6, False)]
    for i, (nm, v, real) in enumerate(bars):
        bh = h * v / ymax
        x = x0 + 40 + i * 130
        kind = "crypto" if real else "ext"
        f.node(f"b{i}", x, y0 + h - bh, 96, max(bh, 6), f"{v:.2f}", kind, fontsize=11.5)
        for j, ln in enumerate(nm.split("\n")):
            f.text(x + 48, y0 + h + 20 + j * 14, ln, 10, real, "#3a4a5a", anchor="middle", w=150)
    f.text(150, y0 + h / 2, "Đỉnh RSS", 11.5, True, "#3b4655", anchor="end", w=140)

    f.node("why", 260, 500, 480, 100, "Vì sao hệ số xấp xỉ 2,7 lần", "note",
           sub="Bốn bản sao cùng tồn tại trong bộ nhớ tại thời điểm cao nhất: bản đọc tệp nguồn, "
               "bản sao trong kho lưu trữ đã đóng gói, vùng đệm stdin đưa vào age và vùng đệm stdout "
               "nhận từ age. Toàn bộ đều là Vec<u8> nằm trong RAM.")
    f.node("guard", 770, 500, 350, 100, "Biện pháp hiện tại là RÀO, không phải sửa gốc", "danger",
           sub="Trần 2 GiB cho một mục được kiểm bằng metadata TRƯỚC khi đọc, nên tệp quá lớn bị từ chối "
               "bằng SV-TOO-LARGE thay vì làm cạn bộ nhớ. Cách sửa triệt để là truyền dòng, hiện chưa "
               "được thực hiện (H1).")

    f.text(260, 640, "Lưu ý phương pháp: chỉ cột 1024 MiB là số đo. Bốn cột còn lại là ngoại suy tuyến tính "
                     "từ hệ số đã đo và được ghi nhãn rõ ràng; chúng KHÔNG được coi là kết quả thực nghiệm.",
           11, False, "#3a4a5a", w=860)
    emit(f, 4)


def fig_4_5():
    f = Figure("Hinh-4-05-trang-thai-gia-thuyet-rui-ro",
               "Hình 4.5 — Trạng thái bảy giả thuyết rủi ro sau chiến dịch kiểm chứng và sửa lỗi",
               "Mỗi giả thuyết được tái hiện hoặc bác bỏ trên đúng đường mã sản phẩm (VaultBackend + age thật)",
               1180, 760,
               SRC + "docs/VALIDATION-PLAN.md và docs/VALIDATION-RESULTS.md (bảng trạng thái sau khi sửa)")

    rows = [
        ("H2", "Không xác nhận lại mật khẩu khi tạo két", "Nghiêm trọng", "ĐÃ SỬA",
         "Thêm ô nhập lại và chặn tạo nếu hai ô lệch nhau", "ok"),
        ("H7", "Ghi đồng thời làm mất dữ liệu", "Cao", "ĐÃ SỬA",
         "Khóa ghi theo đường dẫn két; mất 0/12 lượt thử sau khi sửa (trước đó mất 1 trong 12/12)", "ok"),
        ("H3", "Trích xuất âm thầm ghi đè tệp có sẵn", "Cao", "ĐÃ SỬA",
         "Từ chối khi đích tồn tại và trả SV-OUTPUT-EXISTS", "ok"),
        ("H6", "Mọi lỗi đều gộp thành SV-INTERNAL", "Cao", "ĐÃ SỬA",
         "Bổ sung SV-IO, SV-TOO-LARGE, SV-TIMEOUT, SV-OUTPUT-EXISTS; chi tiết I/O không kèm đường dẫn", "ok"),
        ("H1", "Tệp lớn gây hỏng khó hiểu", "Cao", "ĐÃ GIẢM NHẸ",
         "Trần 2 GiB kiểm trước khi đọc + mã lỗi rõ ràng; sửa gốc là truyền dòng thì CHƯA làm", "note"),
        ("H4", "env_clear() làm hỏng age trên Windows", "Chưa rõ → đã đóng", "BÁC BỎ / ĐÃ ĐÓNG",
         "Kiểm thử đầu-cuối chạy xanh trên windows-latest ngày 15-6-2026", "ok"),
        ("H5", "Nhị phân đi kèm bị chặn khi cài mới", "Cao (phân phối)", "CÒN MỞ",
         "Gatekeeper chấm dứt bản sao bị gắn nhãn cách ly (thoát 137). Cần ký số và công chứng — "
         "nằm ngoài phạm vi sử dụng nội bộ", "danger"),
    ]
    heads = ["Mã", "Nội dung giả thuyết", "Mức độ", "Trạng thái", "Bằng chứng / biện pháp"]
    xs = [50, 130, 460, 610, 780]
    ws = [70, 320, 140, 160, 350]
    for i, (hd, x, w) in enumerate(zip(heads, xs, ws)):
        f.node(f"h{i}", x, 100, w, 40, hd, "ext", fontsize=11.5)

    y = 148
    for i, (code, desc, sev, st, ev, kind) in enumerate(rows):
        f.node(f"c{i}", xs[0], y, ws[0], 74, code, "app", fontsize=13)
        f.node(f"d{i}", xs[1], y, ws[1], 74, desc, "plain", fontsize=11, bold=False)
        f.node(f"s{i}", xs[2], y, ws[2], 74, sev, "danger" if "Cao" in sev or "Nghiêm" in sev else "ext",
               fontsize=11)
        f.node(f"t{i}", xs[3], y, ws[3], 74, st, kind, fontsize=11.5)
        f.node(f"e{i}", xs[4], y, ws[4], 74, ev, "plain", fontsize=9.8, bold=False)
        y += 78

    f.text(50, y + 26, "Kết luận về tư thế phát hành: sau đợt sửa, điểm chặn duy nhất còn lại đối với việc "
                       "phân phối rộng là H5 (ký số và công chứng gói cài). Dự án khai báo rõ rằng đây là "
                       "công cụ dùng nội bộ nên việc ký số được đặt ngoài phạm vi, chứ không phải đã hoàn thành.",
           11, False, "#3a4a5a", w=1100)
    emit(f, 4)


ALL = [fig_4_1, fig_4_2, fig_4_3, fig_4_4, fig_4_5]

if __name__ == "__main__":
    for fn in ALL:
        fn()
    print("chapter4 figures:", len(ALL))
