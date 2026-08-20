# -*- coding: utf-8 -*-
"""Phan dau bao cao: bia, chu viet tat, muc luc, danh muc hinh/bang."""

ABBREV = [
    ("ABI", "Application Binary Interface", "Giao diện nhị phân ứng dụng — ở đây là tầng hợp đồng mật mã ổn định"),
    ("AEAD", "Authenticated Encryption with Associated Data", "Mã hóa có xác thực"),
    ("AES", "Advanced Encryption Standard", "Chuẩn mã hóa tiên tiến"),
    ("API", "Application Programming Interface", "Giao diện lập trình ứng dụng"),
    ("Argon2id", "Argon2 identity variant", "Hàm dẫn xuất khóa từ mật khẩu, biến thể lai chống cả tấn công kênh kề và GPU"),
    ("BLAKE3", "BLAKE3 cryptographic hash", "Hàm băm mật mã BLAKE3"),
    ("CBOR", "Concise Binary Object Representation", "Định dạng biểu diễn đối tượng nhị phân súc tích (RFC 8949)"),
    ("CI", "Continuous Integration", "Tích hợp liên tục"),
    ("CSP", "Content Security Policy", "Chính sách an toàn nội dung của trình duyệt/webview"),
    ("CSPRNG", "Cryptographically Secure Pseudo-Random Number Generator", "Bộ sinh số giả ngẫu nhiên an toàn về mật mã"),
    ("DCT", "Discrete Cosine Transform", "Biến đổi cosin rời rạc"),
    ("DEK", "Data Encryption Key", "Khóa mã hóa dữ liệu"),
    ("DoS", "Denial of Service", "Tấn công từ chối dịch vụ"),
    ("DTO", "Data Transfer Object", "Đối tượng truyền dữ liệu qua biên"),
    ("Ed25519", "Edwards-curve Digital Signature Algorithm (Curve25519)", "Lược đồ chữ ký số trên đường cong Edwards"),
    ("FFI", "Foreign Function Interface", "Giao diện gọi hàm ngoại ngôn ngữ"),
    ("HSM", "Hardware Security Module", "Mô-đun bảo mật phần cứng"),
    ("IPC", "Inter-Process Communication", "Giao tiếp giữa các tiến trình / giữa giao diện và lõi"),
    ("KDF", "Key Derivation Function", "Hàm dẫn xuất khóa"),
    ("KEK", "Key Encryption Key", "Khóa dùng để mã hóa khóa khác"),
    ("LSB", "Least Significant Bit", "Bit có trọng số nhỏ nhất"),
    ("MAC", "Message Authentication Code", "Mã xác thực thông điệp"),
    ("MK", "Master Key", "Khóa chủ của két"),
    ("MSRV", "Minimum Supported Rust Version", "Phiên bản Rust tối thiểu được hỗ trợ"),
    ("OWASP", "Open Worldwide Application Security Project", "Tổ chức phi lợi nhuận về an toàn ứng dụng"),
    ("PBKDF", "Password-Based Key Derivation Function", "Hàm dẫn xuất khóa từ mật khẩu"),
    ("PQC", "Post-Quantum Cryptography", "Mật mã hậu lượng tử"),
    ("RSS", "Resident Set Size", "Dung lượng bộ nhớ thường trú của tiến trình"),
    ("SBOM", "Software Bill of Materials", "Danh mục thành phần phần mềm"),
    ("SVG", "Scalable Vector Graphics", "Đồ họa vectơ co giãn"),
    ("TOCTOU", "Time Of Check To Time Of Use", "Khoảng trống giữa thời điểm kiểm tra và thời điểm sử dụng"),
    ("UUID", "Universally Unique Identifier", "Định danh duy nhất toàn cục"),
    ("XSalsa20-Poly1305", "XSalsa20 stream cipher with Poly1305 MAC", "Bộ mã hóa có xác thực của libsodium (crypto_secretbox)"),
]


def blocks():
    B = []
    # ---------------------------------------------------------------- bia ---
    B += [
        ("center", "HỌC VIỆN KỸ THUẬT QUÂN SỰ", True),
        ("center", "KHOA CÔNG NGHỆ THÔNG TIN", True),
        ("center", " "),
        ("center", " "),
        ("center", " "),
        ("center", " "),
        ("center", "BÁO CÁO ĐỀ TÀI", True),
        ("center", " "),
        ("center", "NGHIÊN CỨU, THIẾT KẾ VÀ XÂY DỰNG", True),
        ("center", "BỘ CÔNG CỤ BẢO MẬT VÀ RIÊNG TƯ NGOẠI TUYẾN", True),
        ("center", "SECURE VAULT RESEARCH", True),
        ("center", " "),
        ("center", "Két an toàn mã hóa có xác thực, quản lý khóa phân cấp,"),
        ("center", "chia sẻ bí mật theo ngưỡng và các dịch vụ mật mã mức tệp"),
        ("center", " "),
        ("center", " "),
        ("center", " "),
        ("center", " "),
        ("center", " "),
        ("center", " "),
        ("center", " "),
        ("center", "Hà Nội – 2026", True),
        ("pagebreak",),
    ]

    # ---------------------------------------------------- loi noi dau ngan ---
    B += [
        ("h1", "LỜI NÓI ĐẦU", False),
        ("p", "Báo cáo này trình bày kết quả nghiên cứu, phân tích, thiết kế và xây dựng hệ thống "
               "**Secure Vault Research** — một bộ công cụ bảo mật và riêng tư hoạt động hoàn toàn ngoại "
               "tuyến trên máy tính cá nhân. Toàn bộ nội dung kỹ thuật trong báo cáo được xây dựng trên "
               "cơ sở khảo sát trực tiếp mã nguồn của hệ thống chứ không dựa vào tài liệu quảng bá hay "
               "mô tả thiết kế ở mức ý tưởng. Mỗi hình vẽ kiến trúc, mỗi luồng xử lý và mỗi tuyên bố về "
               "thuộc tính an toàn đều được đối chiếu với tệp mã nguồn tương ứng, và nguồn đối chiếu "
               "được ghi ngay dưới chân hình hoặc trong phần dẫn giải."),
        ("p", "Một nguyên tắc trình bày được tuân thủ xuyên suốt: phân biệt rạch ròi giữa cái **đã được "
               "hiện thực hóa**, cái **mới ở mức thử nghiệm hoặc còn hạn chế đã biết**, và cái **mới nằm "
               "trong kế hoạch phát triển**. Một hệ thống mật mã được đánh giá không chỉ bởi những gì nó "
               "làm được, mà quan trọng hơn là bởi mức độ trung thực khi mô tả những gì nó chưa làm được. "
               "Vì lý do đó, báo cáo dành hẳn một phần riêng cho các hạn chế còn tồn đọng và cố ý tránh "
               "những khẳng định tuyệt đối như “không thể phá vỡ”, “an toàn tuyệt đối” hay “sẵn sàng cho "
               "môi trường sản xuất” khi bằng chứng chưa cho phép."),
        ("p", "Do đặc thù của một đề tài về an toàn thông tin, phần kiến trúc an ninh và mô hình đe dọa "
               "được trình bày với độ sâu lớn hơn các phần khác. Người đọc quan tâm tới tổng quan có thể "
               "đọc Chương 1 và phần kết luận từng chương; người đọc quan tâm tới chi tiết hiện thực nên "
               "đọc Chương 2 và Chương 3 cùng với các hình kiến trúc kèm theo."),
        ("pagebreak",),
    ]

    # --------------------------------------------------------- chu viet tat --
    B += [
        ("h1", "DANH MỤC CHỮ VIẾT TẮT", False),
        ("tbl", "", ["Từ viết tắt", "Tên đầy đủ bằng tiếng Anh", "Nghĩa tiếng Việt"],
         [[a, b, c] for a, b, c in ABBREV], [2.6, 6.0, 7.6], 11),
    ]
    return B
