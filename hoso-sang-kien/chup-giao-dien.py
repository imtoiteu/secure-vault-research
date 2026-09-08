#!/usr/bin/env python3
"""Kết xuất ảnh chụp toàn bộ màn hình giao diện của ứng dụng cho hồ sơ sáng kiến.

Máy chủ dựng hồ sơ không có thiết bị Android, nên ảnh được kết xuất từ *chính mã giao diện
của sản phẩm* (app/frontend/) ở kích thước màn hình điện thoại, với cầu nối IPC được mô phỏng
trả về đúng giá trị mà gốc hợp thành Android sinh ra. Nhờ vậy toàn bộ logic giao diện thật
(main.js, i18n.js) được thực thi — đây không phải ảnh dựng bằng công cụ thiết kế.

Kịch bản chạy hai bước:
  1. Chụp từng màn hình một → hinh-anh/screenshot/GDxx-<tên>.png
  2. Ghép ảnh của cùng một nhóm nghiệp vụ thành hình lưới có nhãn → GN-x-<nhóm>.png
     (bản ghép mới là hình chèn vào Thuyết minh; ảnh đơn giữ lại làm bằng chứng gốc)

Dùng: python3 chup-giao-dien.py
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parent
FE = BASE.parent / "app" / "frontend"
SS = BASE / "hinh-anh" / "screenshot"
WORK = SS / "_work"

CHROME = "/usr/bin/google-chrome"
RONG = 400          # bề rộng khung nhìn, điểm ảnh CSS (cỡ điện thoại phổ thông)
CAO = 2400          # dựng khung cao rồi cắt bớt phần nền thừa ở dưới
TY_LE = 2           # kết xuất ở mật độ điểm ảnh gấp đôi cho nét khi in

# --------------------------------------------------------------------------- #
# Danh mục màn hình: (mã hình, khoá màn hình trong index.html, tên tiếng Việt)
# Thứ tự bám theo thứ tự xuất hiện trong thanh điều hướng của ứng dụng.
# --------------------------------------------------------------------------- #
MAN_HINH = [
    ("GD01", "home",              "Trang chủ"),
    ("GD02", "__drawer__",        "Ngăn kéo điều hướng"),
    ("GD03", "vault",             "Két an toàn"),
    ("GD04", "encrypt",           "Khoá tệp"),
    ("GD05", "decrypt",           "Mở khoá tệp"),
    ("GD06", "sign",              "Ký tệp"),
    ("GD07", "verify",            "Kiểm tra chữ ký"),
    ("GD08", "hash",              "Lấy vân tay tệp"),
    ("GD09", "intact",            "Kiểm tra tệp chưa bị đổi"),
    ("GD10", "verify-integrity",  "Xác minh tệp tải về"),
    ("GD11", "split-secret",      "Chia nhỏ bí mật"),
    ("GD12", "split-file",        "Chia nhỏ tệp"),
    ("GD13", "recover-pieces",    "Ghép lại từ các mảnh"),
    ("GD14", "qr-transfer",       "Chuyển mảnh bằng mã QR"),
    ("GD15", "hide",              "Giấu dữ liệu trong ảnh"),
    ("GD16", "unhide",            "Hiện dữ liệu ẩn"),
    ("GD17", "detect",            "Phát hiện dữ liệu ẩn"),
    ("GD18", "watermark",         "Chống giả mạo ảnh"),
    ("GD19", "metadata-inspect",  "Xem siêu dữ liệu"),
    ("GD20", "metadata-clean",    "Xoá siêu dữ liệu"),
    ("GD21", "metadata-compare",  "So sánh siêu dữ liệu"),
]

# Ảnh chụp trạng thái giao diện đặc biệt, đứng riêng chứ không vào lưới phụ lục:
# (mã, khoá màn hình, tên, đoạn kịch bản chạy sau khi tải trang)
TRANG_THAI = [
    ("GDX1", "metadata-inspect",
     "Xem siêu dữ liệu — mở mục “Thông tin thêm”",
     'document.querySelectorAll("[data-screen=\'metadata-inspect\'] details")'
     '.forEach(function (d) { d.open = true; });'),
]

# Hình ghép cho Phụ lục danh mục màn hình: mỗi hình gồm hai màn hình đặt cạnh nhau, đủ lớn
# để đọc được chữ khi in trên khổ A4 (mỗi máy rộng khoảng 7,5 cm).
GHEP_MOI_HINH = 2

STUB = """\
// Lớp mô phỏng cầu IPC của Tauri, CHỈ dùng để kết xuất ảnh giao diện trên máy chủ dựng hồ sơ
// (không có thiết bị Android). Nó trả về đúng những giá trị mà gốc hợp thành Android
// (app/src/compose/mobile.rs) sinh ra: metadata_available = true vì mô-đun siêu dữ liệu đã
// được viết lại bằng Rust thuần (crate sv-meta-rs) và chạy ngay trong tiến trình ứng dụng.
// Nhờ lớp mô phỏng này, toàn bộ logic giao diện thật (main.js) được thực thi thay vì chỉ
// hiển thị HTML tĩnh.
window.__TAURI__ = {
  core: {
    invoke: async (cmd) => {
      if (cmd === "app_info") {
        return {
          app_version: "0.1.0", contract_version: 1,
          max_format_version: 1, suite_version: 1,
        };
      }
      if (cmd === "metadata_available") return true;
      throw { code: "SV-INTERNAL", detail: "stub" };
    },
  },
};
"""


def chuan_bi():
    WORK.mkdir(parents=True, exist_ok=True)
    for ten in ("styles.css", "main.js", "i18n.js"):
        shutil.copy2(FE / ten, WORK / ten)
    (WORK / "stub-tauri.js").write_text(STUB, encoding="utf-8")
    return (FE / "index.html").read_text(encoding="utf-8")


def dung_trang(goc: str, khoa: str, kich_ban: str = "") -> str:
    """Sinh trang HTML hiển thị đúng một màn hình, dùng lại nguyên mã giao diện sản phẩm."""
    # Trỏ các tệp tài nguyên về thư mục làm việc và chèn lớp mô phỏng cầu IPC.
    trang = goc.replace('<script src="i18n.js">',
                        '<script src="stub-tauri.js"></script>\n    <script src="i18n.js">')

    if khoa == "__drawer__":
        # Ngăn kéo mở ra là một trạng thái giao diện, không phải một màn hình riêng.
        them = ('<script>window.addEventListener("load", function () {'
                'document.querySelector(".shell").classList.add("drawer-open");'
                'var s = document.getElementById("drawer-scrim"); if (s) s.hidden = false;'
                '});</script>')
        return trang.replace("</body>", them + "\n  </body>")

    # Ẩn màn hình mặc định, hiện màn hình cần chụp. Chỉ đổi thuộc tính class, không đổi
    # nội dung — ảnh chụp vẫn là giao diện thật của sản phẩm.
    trang = trang.replace('<section class="screen" data-screen="home">',
                          '<section class="screen hidden" data-screen="home">')
    cu = f'<section class="screen hidden" data-screen="{khoa}">'
    moi = f'<section class="screen" data-screen="{khoa}">'
    if cu not in trang:
        sys.exit(f"không tìm thấy màn hình {khoa} trong index.html")
    trang = trang.replace(cu, moi)
    # Đánh dấu mục điều hướng tương ứng đang được chọn, đúng như khi người dùng bấm vào nó.
    trang = trang.replace(f'class="navitem" data-screen="{khoa}"',
                          f'class="navitem active" data-screen="{khoa}"')
    if kich_ban:
        trang = trang.replace(
            "</body>",
            '<script>window.addEventListener("load", function () {' + kich_ban
            + '});</script>\n  </body>')
    return trang


def cat_nen(duong_dan: Path):
    """Cắt bỏ phần nền trống ở dưới ảnh (khung nhìn dựng cao hơn nội dung thật)."""
    anh = Image.open(duong_dan).convert("RGB")
    rong, cao = anh.size
    nen = anh.getpixel((rong - 3, cao - 3))
    diem = anh.load()
    day = cao
    while day > 200:
        hang_trong = all(
            abs(diem[x, day - 1][k] - nen[k]) <= 2 for x in range(0, rong, 7) for k in range(3)
        )
        if not hang_trong:
            break
        day -= 1
    day = min(cao, day + 24 * TY_LE)     # chừa lề dưới cho cân đối
    if day < cao:
        anh.crop((0, 0, rong, day)).save(duong_dan)
    return Image.open(duong_dan).size


def chup(goc: str):
    ket_qua = {}
    for ma, khoa, ten in MAN_HINH:
        trang = WORK / f"{ma}.html"
        trang.write_text(dung_trang(goc, khoa), encoding="utf-8")
        dich = SS / f"{ma}-{khoa.replace('__', '')}.png"
        # Ngăn kéo mở phủ kín chiều cao khung nhìn, phép cắt nền ở dưới không áp dụng được,
        # nên dựng khung ở chiều cao vừa đủ hiển thị hết danh mục nhóm công cụ.
        cao_khung = 1460 if khoa == "__drawer__" else CAO
        subprocess.run(
            [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
             "--hide-scrollbars", "--force-color-profile=srgb",
             f"--force-device-scale-factor={TY_LE}",
             f"--window-size={RONG},{cao_khung}",
             "--virtual-time-budget=4000",
             f"--screenshot={dich}", f"file://{trang}"],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        kt = cat_nen(dich)
        ket_qua[ma] = (dich, ten, kt)
        print(f"  {ma}  {ten:34s} {kt[0]}x{kt[1]}")

    for ma, khoa, ten, kich_ban in TRANG_THAI:
        trang = WORK / f"{ma}.html"
        trang.write_text(dung_trang(goc, khoa, kich_ban), encoding="utf-8")
        dich = SS / f"{ma}-{khoa}-mo-rong.png"
        subprocess.run(
            [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
             "--hide-scrollbars", "--force-color-profile=srgb",
             f"--force-device-scale-factor={TY_LE}",
             f"--window-size={RONG},{CAO}",
             "--virtual-time-budget=4000",
             f"--screenshot={dich}", f"file://{trang}"],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        kt = cat_nen(dich)
        ket_qua[ma] = (dich, ten, kt)
        print(f"  {ma}  {ten:34s} {kt[0]}x{kt[1]}")
    return ket_qua


def ghep(ket_qua):
    """Ghép các màn hình thành hình lưới hai cột có nhãn, dùng cho Phụ lục danh mục màn hình.

    Ảnh nào cao hơn ô lưới thì được thu nhỏ vừa ô chứ không bị cắt — nguyên tắc là không mất
    bất kỳ phần nội dung nào của màn hình.
    """
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
    LE, KHE, CAO_NHAN, CAO_TOI_DA = 18, 24, 46, 2100
    NEN, CHU, VIEN = (255, 255, 255), (17, 17, 17), (170, 176, 188)

    ds = [(ma, ket_qua[ma]) for ma, _, _ in MAN_HINH]
    ket = []
    for i in range(0, len(ds), GHEP_MOI_HINH):
        khoi = ds[i:i + GHEP_MOI_HINH]
        anh_con = []
        for ma, (dd, ten, _) in khoi:
            a = Image.open(dd).convert("RGB")
            if a.height > CAO_TOI_DA:
                a = a.resize((round(a.width * CAO_TOI_DA / a.height), CAO_TOI_DA),
                             Image.LANCZOS)
            anh_con.append((ma, ten, a))

        rong_o = max(a.width for _, _, a in anh_con)
        cao_o = max(a.height for _, _, a in anh_con)
        cot = len(anh_con)
        W = LE * 2 + cot * rong_o + (cot - 1) * KHE
        H = LE * 2 + cao_o + CAO_NHAN
        tam = Image.new("RGB", (W, H), NEN)
        ve = ImageDraw.Draw(tam)
        for c, (ma, ten, a) in enumerate(anh_con):
            x = LE + c * (rong_o + KHE) + (rong_o - a.width) // 2
            y = LE
            tam.paste(a, (x, y))
            ve.rectangle([x, y, x + a.width - 1, y + a.height - 1], outline=VIEN, width=2)
            nhan = f"{ma}. {ten}"
            w = ve.textlength(nhan, font=font)
            ve.text((x + (a.width - w) / 2, y + a.height + 11), nhan, font=font, fill=CHU)

        ma_hinh = f"GC{i // GHEP_MOI_HINH + 1:02d}"
        ten_hinh = "-".join(ma for ma, _, _ in anh_con).lower()
        dich = SS / f"{ma_hinh}-{ten_hinh}.png"
        tam.save(dich)
        ket.append((ma_hinh, dich.name, [(ma, ten) for ma, ten, _ in anh_con]))
        print(f"  {ma_hinh}  {dich.name:34s} {tam.size[0]}x{tam.size[1]}")
    return ket


def main():
    goc = chuan_bi()
    print("Chụp từng màn hình:")
    ket_qua = chup(goc)
    print("Ghép hình cho phụ lục danh mục màn hình:")
    ghep_ds = ghep(ket_qua)

    # Ghi danh mục ra JSON để tệp sinh Thuyết minh chèn hình mà không phải chép tay tên tệp —
    # cùng nguyên tắc với các số liệu khác trong hồ sơ: sinh tự động, không nhập tay.
    danh_muc = {
        "trang_thai": [{"ma": m, "khoa": k, "ten": t, "tep": ket_qua[m][0].name}
                       for m, k, t, _ in TRANG_THAI],
        "man_hinh": [{"ma": m, "khoa": k, "ten": t,
                      "tep": ket_qua[m][0].name,
                      "rong": ket_qua[m][2][0], "cao": ket_qua[m][2][1]}
                     for m, k, t in MAN_HINH],
        "hinh_ghep": [{"ma": a, "tep": b, "gom": [{"ma": x, "ten": y} for x, y in c]}
                      for a, b, c in ghep_ds],
    }
    (BASE / "bang-chung" / "danh-muc-man-hinh.json").write_text(
        json.dumps(danh_muc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Xong: {len(MAN_HINH)} màn hình, {len(ghep_ds)} hình ghép → {SS}")


if __name__ == "__main__":
    main()
