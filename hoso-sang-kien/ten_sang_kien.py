#!/usr/bin/env python3
"""Tên sáng kiến và lĩnh vực — nguồn duy nhất cho cả bốn văn bản của hồ sơ.

Trước đây chuỗi này được chép hai bản trong tao-don-va-hieu-qua.py và tao-thuyet-minh.py.
Sửa tên mà sót một chỗ thì hai văn bản trong cùng một bộ hồ sơ ghi tên khác nhau — lỗi nhỏ
nhưng đủ để hội đồng nghi ngờ toàn bộ hồ sơ. Nay chỉ còn một chỗ để sửa.

Bản tác giả rà soát thủ công dùng ba biến thể tên khác nhau: trang bìa và Đơn đăng ký ghi
"Bộ công cụ bảo đảm an toàn thông tin và quyền riêng tư dữ liệu trên thiết bị di động",
còn mục A.1 của Thuyết minh giữ lại tên cũ. Lấy tên trên Đơn đăng ký làm chuẩn — đó là
văn bản đăng ký chính thức, và cũng là tên tác giả tự gõ ở hai chỗ.
"""

TEN_SANG_KIEN = (
    "Bộ công cụ bảo đảm an toàn thông tin và quyền riêng tư dữ liệu "
    "trên thiết bị di động (SecureVault Mobile)"
)

# Dạng in hoa dùng cho trang bìa.
TEN_SANG_KIEN_HOA = (
    "BỘ CÔNG CỤ BẢO ĐẢM AN TOÀN THÔNG TIN VÀ QUYỀN RIÊNG TƯ DỮ LIỆU "
    "TRÊN THIẾT BỊ DI ĐỘNG (SECUREVAULT MOBILE)"
)

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
