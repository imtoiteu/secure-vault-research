#!/usr/bin/env python3
"""Số liệu kỹ thuật dùng chung cho cả bốn văn bản của hồ sơ.

Nguyên tắc bất di bất dịch của bộ hồ sơ này: *không con số nào được nhập tay*. Mọi số liệu
đọc từ bang-chung/du-kien.json và bang-chung/kiem-tra-apk.json — hai tệp do thu-thap-du-kien.py
và kiem-tra-apk.py sinh trực tiếp từ mã nguồn, gói cài đặt và nhật ký kiểm thử.

Trước đây khối đọc dữ kiện này được chép trong từng tệp sinh văn bản. Hệ quả đã xảy ra thật:
văn bản 03 ghi 267 hàm kiểm thử trong khi văn bản 02 ghi 272, vì một tệp được cập nhật còn
tệp kia thì không. Gom về một chỗ để lỗi đó không lặp lại.
"""

import json
import pathlib

BASE = pathlib.Path(__file__).parent
DK = json.loads((BASE / "bang-chung" / "du-kien.json").read_text(encoding="utf-8"))

_apk_file = BASE / "bang-chung" / "kiem-tra-apk.json"
APK = json.loads(_apk_file.read_text(encoding="utf-8")) if _apk_file.exists() else {"co_apk": False}

_dm_file = BASE / "bang-chung" / "danh-muc-man-hinh.json"
DMMH = json.loads(_dm_file.read_text(encoding="utf-8")) if _dm_file.exists() else None

N_LENH = DK["lenh_ipc"]["so_luong"]
DS_LENH = DK["lenh_ipc"]["danh_sach"]
N_CRATE = DK["crate"]["so_luong"]
DS_CRATE = DK["crate"]["danh_sach"]
N_TEST = sum(DK["test_trong_nguon"].values())
TEST_THEO_CRATE = DK["test_trong_nguon"]
A2 = DK["argon2id"]
TT = DK["thuat_toan"]
KQ = DK["ket_qua_kiem_thu"]

host = KQ.get("host_toan_bo") or {}
arm = KQ.get("arm64_loi_mat_ma") or {}
_iva = KQ.get("interop_age") or {}
_ivv = KQ.get("interop_vault") or {}
SO_DOI_CHUNG = _iva.get("passed", 0) + _ivv.get("passed", 0)

# --- Khả năng đa nền tảng -------------------------------------------------
# Nguồn: .github/workflows/ci.yml (ma trận hệ điều hành) và docs/CI-VALIDATION.md (biên bản
# lần chạy CI đã xanh). Hồ sơ chỉ được nói tới mức hai tệp này chứng minh được.
DNT = DK.get("da_nen_tang") or {}
OS_CI = DNT.get("he_dieu_hanh_ci") or []
CI_XANH = DNT.get("lan_chay_ci_xanh") or {}

_TEN_OS = {"ubuntu": "Linux", "macos": "macOS", "windows": "Windows"}
# Xếp theo thứ tự người đọc quen gặp, không theo thứ tự chữ cái của tên kỹ thuật.
TEN_OS = [_TEN_OS[k] for k in ("windows", "macos", "ubuntu") if k in OS_CI]
CHUOI_OS = ", ".join(TEN_OS)

GIT = DK.get("git") or {}

MB_APK = (
    f"{APK['kich_thuoc_byte'] / 1_000_000:.1f}".replace(".", ",")
    if APK.get("co_apk") else None
)
SHA_APK = APK.get("sha256")

SS = BASE / "hinh-anh" / "screenshot"
PNG = BASE / "hinh-anh" / "png"


def ngat_duoc(chuoi):
    """Chèn ký tự ngắt dòng vô hình sau dấu gạch dưới của tên lệnh.

    Tên lệnh (ví dụ crypto_generate_signing_keypair) là một từ dài không có chỗ xuống dòng,
    khiến ô bảng bị vỡ chữ. Ký tự U+200B không hiển thị nhưng cho phép trình soạn thảo ngắt
    dòng đúng ranh giới từ.
    """
    return chuoi.replace("_", "_​")


def anh_man_hinh(ma):
    """Đường dẫn ảnh chụp của một màn hình theo mã GDxx (tên tệp do chup-giao-dien.py sinh)."""
    if not DMMH:
        return None
    for m in DMMH.get("man_hinh", []) + DMMH.get("trang_thai", []):
        if m["ma"] == ma:
            dd = SS / m["tep"]
            return dd if dd.exists() else None
    return None


def hinh_ghep():
    """Danh sách ảnh ghép hai màn hình một khung, kèm chú thích — dùng cho phụ lục ảnh."""
    if not DMMH:
        return []
    ra = []
    for g in DMMH.get("hinh_ghep", []):
        dd = SS / g["tep"]
        if not dd.exists():
            continue
        ra.append((dd, "; ".join(f"{m['ma']} — {m['ten']}" for m in g["gom"])))
    return ra
