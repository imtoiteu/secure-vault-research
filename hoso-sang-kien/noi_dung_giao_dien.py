#!/usr/bin/env python3
"""Danh mục màn hình giao diện và các lệnh chạy ở mức toàn ứng dụng.

Bảng danh mục là bằng chứng đối chiếu một-một giữa *chức năng* và *giao diện thực hiện nó*:
mọi lệnh nghiệp vụ của lõi đều xuất hiện ở ít nhất một dòng, và mọi lệnh xuất hiện ở đây đều
có thật trong lõi. Phần mô tả giao diện của từng nhóm nằm cùng chỗ với bảng chức năng, trong
noi_dung_chuc_nang.py, để một nhóm chỉ có một nơi duy nhất để sửa.

Mã màn hình (GD01…GD21) trùng với mã trên ảnh chụp trong hinh-anh/screenshot/ và với mã ghi
trong bang-chung/danh-muc-man-hinh.json do chup-giao-dien.py sinh ra.
"""

# (mã, tên màn hình, mã nhóm nghiệp vụ, các lệnh nghiệp vụ màn hình này gọi)
DANH_MUC_MAN_HINH = [
    ("GD01", "Trang chủ", "—",
     "app_info (qua khối Giới thiệu)"),
    ("GD02", "Ngăn kéo điều hướng", "—",
     "không gọi lệnh; điều hướng giữa các màn hình"),
    ("GD03", "Két an toàn", "Nhóm 1",
     "vault_create, vault_unlock, vault_lock, vault_change_passphrase, vault_meta, item_add, "
     "item_list, item_extract, sign_file, export_signing_public_key, integrity_check, "
     "integrity_hash, keys_split, keys_recover, verify_file"),
    ("GD04", "Khoá tệp", "Nhóm 2", "crypto_encrypt_file"),
    ("GD05", "Mở khoá tệp", "Nhóm 2", "crypto_decrypt_file, copy_file"),
    ("GD06", "Ký tệp", "Nhóm 3", "crypto_generate_signing_keypair, crypto_sign_file"),
    ("GD07", "Kiểm tra chữ ký", "Nhóm 3", "integrity_verify_signature"),
    ("GD08", "Lấy vân tay tệp", "Nhóm 3", "integrity_hash_file"),
    ("GD09", "Kiểm tra tệp chưa bị đổi", "Nhóm 3", "integrity_hash_file"),
    ("GD10", "Xác minh tệp tải về", "Nhóm 3", "integrity_verify_integrity"),
    ("GD11", "Chia nhỏ bí mật", "Nhóm 4", "shares_split_secret"),
    ("GD12", "Chia nhỏ tệp", "Nhóm 4", "shares_split_file"),
    ("GD13", "Ghép lại từ các mảnh", "Nhóm 4", "shares_recover_secret, copy_file"),
    ("GD14", "Chuyển mảnh bằng mã QR", "Nhóm 4", "shares_export_qr, shares_recover_from_qr"),
    ("GD15", "Giấu dữ liệu trong ảnh", "Nhóm 5", "stego_hide"),
    ("GD16", "Hiện dữ liệu ẩn", "Nhóm 5", "stego_extract, copy_file"),
    ("GD17", "Phát hiện dữ liệu ẩn", "Nhóm 5", "stego_detect"),
    ("GD18", "Chống giả mạo ảnh", "Nhóm 6", "watermark_embed, watermark_verify"),
    ("GD19", "Xem siêu dữ liệu", "Nhóm 7", "metadata_inspect"),
    ("GD20", "Xoá siêu dữ liệu", "Nhóm 7", "metadata_sanitize"),
    ("GD21", "So sánh siêu dữ liệu", "Nhóm 7", "metadata_diff"),
]

# Lệnh không gắn với một màn hình riêng mà chạy ở mức toàn ứng dụng.
LENH_MUC_UNG_DUNG = [
    ("app_info", "Khối “Giới thiệu” trên thanh tiêu đề",
     "Hiển thị phiên bản ứng dụng, phiên bản giao tiếp với lõi xử lý, phiên bản định dạng két "
     "và phiên bản bộ thuật toán"),
    ("metadata_available", "Chạy ngay khi khởi động, trước khi người dùng thao tác",
     "Kiểm tra mô-đun siêu dữ liệu có sẵn sàng hay không; nếu không sẵn sàng, các màn hình "
     "GD19–GD21 được vô hiệu hoá và hiển thị cảnh báo"),
]
