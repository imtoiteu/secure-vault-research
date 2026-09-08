#!/usr/bin/env python3
"""Kiểm tra tĩnh gói cài đặt APK và ghi kết quả ra bang-chung/kiem-tra-apk.json.

Kiểm tra ba điều mà hồ sơ có tuyên bố, để tuyên bố nào cũng có bằng chứng:
  1. Thư viện lõi bảo mật thực sự nằm trong gói và đúng kiến trúc ARM64.
  2. Ứng dụng KHÔNG khai báo quyền truy cập mạng.
  3. Toàn bộ giao diện được nhúng sẵn (không tải từ mạng khi chạy).
"""

import hashlib
import json
import pathlib
import re
import subprocess
import sys
import zipfile

BASE = pathlib.Path(__file__).parent
REPO = BASE.parent
OUT = BASE / "bang-chung" / "kiem-tra-apk.json"


def tim_apk():
    ket_qua = sorted(
        (REPO / "app/gen/android").rglob("*.apk"),
        key=lambda p: p.stat().st_size, reverse=True,
    )
    return ket_qua[0] if ket_qua else None


def kien_truc_so(zf, ten):
    """Đọc 20 byte đầu của tệp .so để xác định kiến trúc từ phần đầu ELF."""
    with zf.open(ten) as f:
        head = f.read(20)
    if head[:4] != b"\x7fELF":
        return "không phải ELF"
    lop = {1: "32-bit", 2: "64-bit"}.get(head[4], "?")
    may = int.from_bytes(head[18:20], "little")
    ten_may = {0xB7: "ARM aarch64", 0x28: "ARM", 0x3E: "x86-64", 0x03: "x86"}.get(may, f"0x{may:x}")
    return f"{lop} {ten_may}"


def main():
    apk = tim_apk()
    if not apk:
        print("CHƯA CÓ APK — bỏ qua kiểm tra")
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps({"co_apk": False}, ensure_ascii=False, indent=2),
                       encoding="utf-8")
        return 1

    kq = {"co_apk": True, "duong_dan": str(apk.relative_to(REPO)),
          "kich_thuoc_byte": apk.stat().st_size,
          "sha256": hashlib.sha256(apk.read_bytes()).hexdigest()}

    with zipfile.ZipFile(apk) as zf:
        names = zf.namelist()

        # 1. thư viện lõi
        so_files = [n for n in names if n.startswith("lib/") and n.endswith(".so")]
        kq["thu_vien_native"] = {n: kien_truc_so(zf, n) for n in so_files}
        kq["co_thu_vien_arm64"] = any(
            "arm64-v8a" in n and "aarch64" in kien_truc_so(zf, n) for n in so_files
        )

        # 3. giao diện nhúng sẵn
        #
        # Tauri KHÔNG để giao diện dưới dạng tệp rời trong assets/ mà nhúng thẳng (đã nén)
        # vào thư viện native lúc biên dịch. Vì vậy phải kiểm tra bảng tài nguyên bên trong
        # tệp .so, chứ không phải tìm index.html trong gói — kiểm tra sai chỗ sẽ cho kết
        # luận sai.
        kq["assets_roi_trong_goi"] = sorted(n for n in names if n.startswith("assets/"))

        import re as _re
        chuoi_tai_nguyen = []
        for n in so_files:
            with zf.open(n) as f:
                du_lieu = f.read()
            for muc in (b"/index.html", b"/main.js", b"/i18n.js", b"/styles.css"):
                if muc in du_lieu:
                    chuoi_tai_nguyen.append(muc.decode())
            break
        kq["tai_nguyen_giao_dien_nhung_trong_so"] = sorted(set(chuoi_tai_nguyen))
        kq["giao_dien_da_nhung"] = "/index.html" in chuoi_tai_nguyen

    # 2. quyền — đọc từ tệp kê khai nguồn (chính xác và không cần công cụ ngoài)
    manifest = REPO / "app/gen/android/app/src/main/AndroidManifest.xml"
    if manifest.exists():
        txt = manifest.read_text(encoding="utf-8")
        txt_khong_chu_thich = re.sub(r"<!--.*?-->", "", txt, flags=re.S)
        quyen = re.findall(r'uses-permission android:name="([^"]+)"', txt_khong_chu_thich)
        kq["quyen_khai_bao"] = quyen
        kq["khong_co_quyen_mang"] = not any("INTERNET" in q for q in quyen)

    # đối chiếu thêm bằng aapt2 nếu có
    aapt = REPO.parent / "android/sdk/build-tools/34.0.0/aapt2"
    aapt = pathlib.Path("/root/android/sdk/build-tools/34.0.0/aapt2")
    if aapt.exists():
        try:
            r = subprocess.run([str(aapt), "dump", "permissions", str(apk)],
                               capture_output=True, text=True, timeout=120)
            kq["aapt2_permissions"] = [l for l in r.stdout.splitlines() if l.strip()]
        except Exception as e:
            kq["aapt2_permissions"] = f"không chạy được: {e}"

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(kq, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"APK: {kq['duong_dan']}  ({kq['kich_thuoc_byte']/1e6:.1f} MB)")
    print(f"SHA-256: {kq['sha256']}")
    print("Thư viện native:")
    for n, a in kq["thu_vien_native"].items():
        print(f"  {n}  →  {a}")
    print(f"Có thư viện ARM64 đúng kiến trúc: {kq['co_thu_vien_arm64']}")
    print(f"Quyền khai báo: {kq.get('quyen_khai_bao', '?')}")
    print(f"KHÔNG có quyền mạng: {kq.get('khong_co_quyen_mang', '?')}")
    print(f"Giao diện nhúng trong thư viện: {kq['giao_dien_da_nhung']} "
          f"{kq['tai_nguyen_giao_dien_nhung_trong_so']}")
    if kq["assets_roi_trong_goi"]:
        print("Tệp rời trong assets/ (cần rà soát xem có thừa không):")
        for n in kq["assets_roi_trong_goi"]:
            print("   ", n)
    else:
        print("Không có tệp rời thừa trong assets/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
