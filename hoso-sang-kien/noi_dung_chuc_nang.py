#!/usr/bin/env python3
"""Mục mô tả chi tiết toàn bộ chức năng của ứng dụng.

Tách riêng khỏi tệp sinh Thuyết minh vì đây là phần dài nhất và có cấu trúc lặp: mỗi nhóm
nghiệp vụ gồm một đoạn dẫn nhập và một bảng liệt kê từng chức năng theo ba cột
(đầu vào — xử lý — kết quả). Cách trình bày này giúp hội đồng nắm được ứng dụng làm được gì
mà không phải đọc mã nguồn.
"""

# Mỗi nhóm: (mã nhóm, tên nhóm, đoạn dẫn nhập, [(tên chức năng, đầu vào, xử lý, kết quả)])
NHOM_CHUC_NANG = [
    (
        "3.2.4.1",
        "Nhóm 1 — Két an toàn: nơi cất giữ nhiều tệp dưới một mật khẩu",
        "Két an toàn là một tệp duy nhất (phần mở rộng .svault) đóng vai trò như một chiếc "
        "hộp có khoá: bên trong chứa nhiều tệp cùng danh mục của chúng, toàn bộ ở dạng mã "
        "hoá. Người dùng chỉ cần nhớ một mật khẩu thay vì quản lý nhiều tệp rời rạc. Danh "
        "mục tệp cũng được mã hoá, nên người có được tệp két mà không có mật khẩu thì không "
        "biết bên trong có những gì — kể cả tên tệp.",
        [
            ("Tạo két mới",
             "Nơi lưu, mật khẩu, tuỳ chọn chính sách khoá phục hồi k trong n",
             "Sinh khoá chính từ mật khẩu bằng Argon2id; sinh cặp khoá nội dung và cặp khoá "
             "ký riêng cho két; ghi tệp theo kiểu nguyên tử",
             "Tệp .svault mới kèm thông tin tóm tắt của két"),
            ("Mở két",
             "Tệp két, mật khẩu",
             "Kiểm tra chữ ký ràng buộc trước, rồi mới dẫn xuất khoá và mở khoá nội dung — "
             "thứ tự này giúp phân biệt tệp hỏng với mật khẩu sai",
             "Một mã phiên làm việc không mang thông tin bí mật"),
            ("Khoá két",
             "Mã phiên",
             "Xoá khoá chính khỏi bộ nhớ phiên",
             "Phiên kết thúc; muốn mở lại phải nhập mật khẩu"),
            ("Đổi mật khẩu két",
             "Mã phiên, mật khẩu mới",
             "Dẫn xuất khoá chính mới và bọc lại các khoá nội bộ; nội dung không phải mã hoá lại",
             "Két dùng mật khẩu mới; các mảnh khoá phục hồi cũ vẫn dùng được"),
            ("Xem thông tin két",
             "Mã phiên",
             "Đọc phần đầu tệp đã được xác thực",
             "Mã định danh két, phiên bản định dạng, thời điểm tạo và sửa, số tệp bên trong, "
             "chính sách khoá phục hồi"),
            ("Thêm tệp vào két",
             "Mã phiên, tệp nguồn, tên đặt trong két",
             "Nạp tệp, ghi vào danh mục đã mã hoá, ghi lại tệp két theo kiểu nguyên tử",
             "Tệp nằm trong két; tệp nguồn bên ngoài không bị thay đổi"),
            ("Liệt kê tệp trong két",
             "Mã phiên",
             "Đọc danh mục đã giải mã trong bộ nhớ",
             "Danh sách tên tệp, kích thước và thời điểm thêm"),
            ("Trích xuất tệp khỏi két",
             "Mã phiên, tên tệp trong két, nơi lưu",
             "Giải mã và ghi ra tệp mới",
             "Tệp khôi phục nguyên vẹn, giống hệt bản đã đưa vào"),
            ("Ký tệp bằng két",
             "Mã phiên, tệp cần ký",
             "Dùng khoá ký riêng của két tạo chữ ký số",
             "Tệp chữ ký, chứng minh tệp đến từ két này và chưa bị sửa"),
            ("Xuất khoá công khai của két",
             "Mã phiên",
             "Đọc khoá công khai từ phần đầu tệp",
             "Chuỗi khoá công khai để người khác kiểm tra chữ ký do két tạo ra"),
            ("Kiểm tra tệp két còn nguyên vẹn",
             "Tệp két (không cần mật khẩu)",
             "Kiểm tra chữ ký ràng buộc trên toàn bộ phần đầu tệp",
             "Kết luận nguyên vẹn hay đã bị sửa — làm được mà không cần mở két"),
            ("Lấy vân tay tệp két",
             "Tệp két",
             "Tính giá trị băm BLAKE3 của toàn bộ tệp",
             "Chuỗi vân tay để đối chiếu giữa hai máy"),
        ],
    ),
    (
        "3.2.4.2",
        "Nhóm 2 — Bảo vệ tệp đơn lẻ",
        "Không phải lúc nào cũng cần đến két. Khi chỉ muốn gửi một tệp đi hoặc cất riêng một "
        "tệp, người dùng có thể khoá trực tiếp tệp đó bằng mật khẩu. Tệp kết quả tự mang đủ "
        "thông tin để mở lại ở bất kỳ đâu, chỉ cần đúng mật khẩu.",
        [
            ("Khoá một tệp bằng mật khẩu",
             "Tệp bất kỳ, mật khẩu, nơi lưu kết quả",
             "Dẫn xuất khoá từ mật khẩu bằng Argon2id rồi mã hoá có xác thực",
             "Tệp đã khoá; sửa dù chỉ một byte cũng bị phát hiện khi mở"),
            ("Mở khoá tệp",
             "Tệp đã khoá, mật khẩu, nơi lưu kết quả",
             "Dẫn xuất lại khoá và giải mã, đồng thời kiểm tra tính toàn vẹn",
             "Tệp gốc khôi phục nguyên vẹn, hoặc thông báo lỗi nếu sai mật khẩu / tệp hỏng"),
            ("Sao chép tệp an toàn",
             "Tệp nguồn, nơi lưu",
             "Sao chép và kiểm tra kết quả",
             "Bản sao dùng cho các bước xử lý tiếp theo mà không đụng đến tệp gốc"),
        ],
    ),
    (
        "3.2.4.3",
        "Nhóm 3 — Chứng minh nguồn gốc và tính toàn vẹn",
        "Mã hoá trả lời câu hỏi “ai đọc được”, còn nhóm chức năng này trả lời hai câu hỏi "
        "khác: “tệp này có đúng do người đó tạo ra không” và “tệp có bị sửa trên đường đi "
        "không”. Đây là nội dung thường bị bỏ qua trong các ứng dụng bảo mật phổ thông nhưng "
        "lại rất quan trọng khi trao đổi tài liệu.",
        [
            ("Tạo cặp khoá ký",
             "Thư mục lưu, tên định danh, mật khẩu bảo vệ khoá bí mật",
             "Sinh cặp khoá Ed25519; khoá bí mật được bảo vệ bằng mật khẩu",
             "Tệp khoá công khai để chia sẻ và tệp khoá bí mật để giữ riêng"),
            ("Ký một tệp",
             "Tệp cần ký, khoá bí mật, mật khẩu",
             "Tạo chữ ký số theo định dạng minisign",
             "Tệp chữ ký đi kèm tệp gốc"),
            ("Kiểm tra chữ ký",
             "Tệp, tệp chữ ký, khoá công khai của người ký",
             "Xác minh chữ ký trên nội dung tệp",
             "Kết luận đạt hoặc không đạt; sửa tệp sau khi ký sẽ làm chữ ký không còn hợp lệ"),
            ("Lấy vân tay tệp",
             "Tệp bất kỳ",
             "Tính giá trị băm BLAKE3",
             "Chuỗi vân tay dùng để đối chiếu hai bản sao của cùng một tệp"),
            ("Đối chiếu tệp với vân tay cho trước",
             "Tệp, chuỗi vân tay nhận được",
             "Tính lại vân tay và so sánh, bỏ qua khác biệt về hoa thường và khoảng trắng",
             "Kết luận tệp có đúng như bản gốc hay không"),
            ("Xác minh tệp tải về",
             "Tệp, vân tay và/hoặc chữ ký kèm khoá công khai",
             "Kiểm tra đồng thời cả hai loại bằng chứng nếu có",
             "Một kết luận đạt/không đạt duy nhất, tránh phải dùng nhiều công cụ rời"),
        ],
    ),
    (
        "3.2.4.4",
        "Nhóm 4 — Sao lưu và khôi phục bằng chia sẻ bí mật ngưỡng",
        "Nguyên tắc không lưu khoá đem lại an toàn nhưng cũng tạo rủi ro: quên mật khẩu là "
        "mất dữ liệu. Nhóm chức năng này giải quyết bằng sơ đồ chia sẻ bí mật Shamir: bí mật "
        "được chia thành n mảnh, cần đúng k mảnh bất kỳ để khôi phục. Một mảnh đơn lẻ không "
        "tiết lộ bất cứ điều gì — đây là tính chất toán học của sơ đồ, không phải quy ước. "
        "Nhờ vậy có thể gửi các mảnh cho nhiều người hoặc cất ở nhiều nơi mà không ai một "
        "mình mở được.",
        [
            ("Chia một bí mật thành nhiều mảnh",
             "Chuỗi bí mật (mật khẩu, khoá, cụm từ khôi phục), tổng số mảnh n, ngưỡng k",
             "Sinh khoá ngẫu nhiên, chia khoá theo Shamir, niêm phong bí mật bằng khoá đó",
             "n tệp mảnh cùng một tệp dữ liệu niêm phong; cần k mảnh và tệp này để khôi phục"),
            ("Chia một tệp thành nhiều mảnh",
             "Tệp bất kỳ, tổng số mảnh, ngưỡng",
             "Tương tự nhưng đối tượng là toàn bộ nội dung tệp",
             "Các tệp mảnh nhỏ gọn cùng một tệp dữ liệu niêm phong"),
            ("Khôi phục từ các mảnh",
             "Đủ số mảnh theo ngưỡng (dạng tệp hoặc chuỗi dán vào), tệp dữ liệu niêm phong",
             "Ghép khoá từ các mảnh rồi mở niêm phong",
             "Bí mật hoặc tệp ban đầu; thiếu mảnh thì báo rõ còn thiếu bao nhiêu"),
            ("Tạo mảnh khôi phục cho két",
             "Mã phiên của két đang mở, tổng số mảnh, ngưỡng",
             "Chia khoá dự phòng của két theo Shamir",
             "Các mảnh dùng để mở lại két khi quên mật khẩu"),
            ("Khôi phục két từ các mảnh",
             "Tệp két, đủ số mảnh theo ngưỡng",
             "Ghép khoá dự phòng và mở két",
             "Phiên làm việc mở, không cần mật khẩu gốc"),
            ("Xuất mảnh ra mã QR",
             "Các chuỗi mảnh",
             "Sinh ảnh mã QR cho từng mảnh",
             "Các ảnh QR để in ra hoặc chuyển sang máy khác bằng camera"),
            ("Khôi phục từ ảnh mã QR",
             "Đủ số ảnh QR theo ngưỡng, tệp dữ liệu niêm phong",
             "Đọc mã QR từ ảnh rồi khôi phục như trên",
             "Bí mật hoặc tệp ban đầu"),
        ],
    ),
    (
        "3.2.4.5",
        "Nhóm 5 — Che giấu dữ liệu trong ảnh và phát hiện dữ liệu ẩn",
        "Che giấu không thay thế mã hoá mà bổ sung cho nó: dữ liệu được mã hoá trước rồi mới "
        "giấu vào ảnh, nên ngay cả khi bị phát hiện thì vẫn không đọc được nếu không có mật "
        "khẩu. Chức năng phát hiện đi kèm giúp người dùng hiểu rõ giới hạn của việc che giấu "
        "— một nội dung có giá trị trong huấn luyện.",
        [
            ("Giấu dữ liệu vào ảnh",
             "Ảnh nền, tệp cần giấu, mật khẩu, tuỳ chọn phân tán dữ liệu",
             "Mã hoá tệp trước, sau đó nhúng vào các bit ít quan trọng của ảnh",
             "Ảnh mới nhìn bằng mắt không khác ảnh gốc, mang dữ liệu đã mã hoá bên trong"),
            ("Lấy dữ liệu đã giấu ra",
             "Ảnh có dữ liệu ẩn, mật khẩu, thư mục lưu",
             "Trích các bit ẩn rồi giải mã",
             "Tệp ban đầu, giữ nguyên tên và phần mở rộng"),
            ("Phát hiện dấu hiệu dữ liệu ẩn",
             "Ảnh bất kỳ",
             "Phân tích dữ liệu thừa sau điểm kết thúc ảnh và thống kê bit ít quan trọng",
             "Mức độ nghi ngờ kèm giải thích; kết quả thấp nghĩa là “các phép thử này không "
             "phát hiện được”, không phải bảo đảm ảnh sạch"),
        ],
    ),
    (
        "3.2.4.6",
        "Nhóm 6 — Thuỷ vân chống giả mạo ảnh",
        "Thuỷ vân dễ vỡ là dấu vô hình gắn với mật khẩu, được nhúng vào ảnh sao cho mọi chỉnh "
        "sửa đều phá vỡ nó. Khác với chữ ký số vốn chỉ cho biết tệp có bị sửa hay không, "
        "thuỷ vân còn chỉ ra được vùng nào của ảnh bị can thiệp.",
        [
            ("Nhúng thuỷ vân",
             "Ảnh PNG hoặc BMP, mật khẩu, nơi lưu",
             "Tính mã xác thực theo từng khối ảnh, khoá bằng mật khẩu, nhúng vào bit ít quan trọng",
             "Ảnh đã đóng dấu, nhìn không khác ảnh gốc; tệp gốc không bị sửa"),
            ("Kiểm tra thuỷ vân",
             "Ảnh đã đóng dấu, mật khẩu",
             "Tính lại mã xác thực từng khối và đối chiếu",
             "Kết luận ảnh còn nguyên hay đã bị sửa, kèm vị trí các vùng bị thay đổi"),
        ],
    ),
    (
        "3.2.4.7",
        "Nhóm 7 — Siêu dữ liệu ẩn trong tệp",
        "Ảnh chụp bằng điện thoại thường mang theo toạ độ GPS nơi chụp, kiểu máy, thời điểm "
        "và đôi khi cả tên chủ sở hữu. Người dùng hiếm khi biết điều này, và đây là một trong "
        "những kênh lộ thông tin phổ biến nhất khi chia sẻ ảnh. Nhóm chức năng này cho phép "
        "xem, xoá và đối chiếu siêu dữ liệu ngay trên máy.",
        [
            ("Xem siêu dữ liệu của tệp",
             "Tệp ảnh",
             "Đọc và nhóm các thẻ theo loại; nhóm toạ độ GPS được tách riêng vì nhạy cảm nhất",
             "Danh sách thẻ theo nhóm kèm định dạng và kiểu MIME; thao tác chỉ đọc, không sửa tệp"),
            ("Xoá siêu dữ liệu",
             "Tệp ảnh, nơi lưu bản sạch",
             "Dựng lại tệp từ dữ liệu ảnh, loại bỏ khối EXIF, hồ sơ màu, chú thích và các khối "
             "văn bản; ghi theo kiểu nguyên tử",
             "Bản sao đã sạch siêu dữ liệu; tệp gốc giữ nguyên; báo cáo số thẻ trước và sau"),
            ("So sánh siêu dữ liệu hai tệp",
             "Hai tệp ảnh",
             "Đối chiếu tập thẻ của hai tệp, bỏ qua tên tệp và dấu thời gian của hệ thống",
             "Danh sách thẻ chỉ có ở tệp thứ nhất, chỉ có ở tệp thứ hai, và các thẻ khác giá trị"),
            ("Kiểm tra mô-đun sẵn sàng",
             "Không có",
             "Báo trạng thái sẵn sàng của mô-đun cho giao diện",
             "Giao diện biết để bật hoặc tắt nhóm chức năng tương ứng"),
        ],
    ),
    (
        "3.2.4.8",
        "Nhóm 8 — Thông tin ứng dụng",
        "Một lệnh duy nhất phục vụ minh bạch phiên bản: cho biết ứng dụng đang chạy phiên bản "
        "nào, hỗ trợ định dạng két đến phiên bản nào và dùng bộ thuật toán phiên bản mấy. "
        "Thông tin này cần cho việc đối chiếu khi trao đổi tệp giữa các máy.",
        [
            ("Xem thông tin phiên bản",
             "Không có",
             "Đọc các hằng số phiên bản được biên dịch vào ứng dụng",
             "Phiên bản ứng dụng, phiên bản giao ước lệnh, phiên bản định dạng két, "
             "phiên bản bộ thuật toán"),
        ],
    ),
]
