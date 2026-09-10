#!/usr/bin/env python3
"""Tên sáng kiến và lĩnh vực — nguồn duy nhất cho cả bốn văn bản của hồ sơ.

Trước đây chuỗi này được chép hai bản trong tao-don-va-hieu-qua.py và tao-thuyet-minh.py.
Sửa tên mà sót một chỗ thì hai văn bản trong cùng một bộ hồ sơ ghi tên khác nhau — lỗi nhỏ
nhưng đủ để hội đồng nghi ngờ toàn bộ hồ sơ. Nay chỉ còn một chỗ để sửa.

Tên do tác giả chốt. Tên bỏ chữ "Mobile" và thêm "đa nền tảng" vì sản phẩm dùng chung một
lõi nghiệp vụ cho cả bản di động lẫn bản máy tính. Điều đó *không* đổi trọng tâm của sáng
kiến: bản di động vẫn là nơi bài toán kỹ thuật phát sinh và được giải quyết. Vì tên gọi
không còn nhắc tới điều đó nữa, các văn bản phải nói rõ ngay ở phần mở đầu.
"""

TEN_SANG_KIEN = (
    "Bộ công cụ bảo đảm an toàn thông tin và quyền riêng tư dữ liệu "
    "đa nền tảng (SecureVault)"
)

# Dạng in hoa dùng cho trang bìa.
TEN_SANG_KIEN_HOA = (
    "BỘ CÔNG CỤ BẢO ĐẢM AN TOÀN THÔNG TIN VÀ QUYỀN RIÊNG TƯ DỮ LIỆU "
    "ĐA NỀN TẢNG (SECUREVAULT)"
)

# Tên sản phẩm và tên bản dành cho từng nền tảng. Tách riêng để văn bản gọi đúng: nói về cả
# sản phẩm thì dùng TEN_SP, nói riêng bản chạy trên điện thoại thì dùng TEN_SP_MOBILE.
TEN_SP = "SecureVault"
TEN_SP_MOBILE = "SecureVault Mobile"

LINH_VUC = "An toàn thông tin"

# Tác giả và đồng tác giả — theo Đơn đăng ký do tác giả điền.
CHU_NHIEM = {
    "ho_ten": "Trần Thị Tới",
    "nam_sinh": "2001",
    "ngay_sinh": "01/10/2001",
    "don_vi": "Khoa K6, Học viện Khoa học Quân sự",
    "cap_bac": "Thượng uý",
    "chuc_vu": "Giảng viên",
    "trinh_do": "Kỹ sư",
    "dien_thoai": "0972743096",
    "email": "toitt2001@gmail.com",
    "dia_chi": "Số 322E Lê Trọng Tấn, Phương Liệt, Hà Nội",
}

DONG_TAC_GIA = [
    {
        "ho_ten": "Hoàng Trung Dũng",
        "nam_sinh": "1989",
        "don_vi": "Phòng KHQS, Học viện Khoa học Quân sự",
        "cap_bac": "Trung tá",
        "chuc_vu": "Trưởng ban",
        "trinh_do": "Nghiên cứu viên chính",
        "dien_thoai": "0988989090",
        "ty_le": "25%",
    },
    {
        "ho_ten": "Đinh Bá Minh",
        "nam_sinh": "1991",
        "don_vi": "Khoa K6, Học viện Khoa học Quân sự",
        "cap_bac": "Thiếu tá",
        "chuc_vu": "Giảng viên",
        "trinh_do": "Kỹ sư",
        "dien_thoai": "0369029660",
        "ty_le": "25%",
    },
]

CHI_HUY_DON_VI = "Đại tá Đặng Kim Ngọc"
DIA_DANH_NGAY = "Hà Nội, ngày 09 tháng 9 năm 2026"
NAM = "2026"
