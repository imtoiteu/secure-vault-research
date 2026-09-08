#!/usr/bin/env python3
"""Mục mô tả giao diện người dùng đi kèm từng nhóm chức năng.

Tách riêng khỏi tệp sinh Thuyết minh vì cùng lý do với noi_dung_chuc_nang.py: đây là phần
dài và có cấu trúc lặp. Mỗi nhóm nghiệp vụ trong noi_dung_chuc_nang.py được nối với các màn
hình giao diện thực hiện nhóm đó, để hội đồng đối chiếu được một-một giữa *chức năng* và
*giao diện tương ứng*, thay vì phải tin vào lời mô tả.

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
     "Hiển thị phiên bản ứng dụng, phiên bản giao ước lệnh, phiên bản định dạng két và phiên "
     "bản bộ thuật toán"),
    ("metadata_available", "Chạy ngay khi khởi động, trước khi người dùng thao tác",
     "Hỏi lõi xem mô-đun siêu dữ liệu có sẵn sàng không; nếu không, ba màn hình GD19–GD21 bị "
     "vô hiệu hoá kèm dải cảnh báo thay vì để người dùng bấm rồi nhận lỗi"),
]

# Mô tả giao diện của từng nhóm nghiệp vụ: (mã nhóm, [đoạn văn], [mã màn hình minh hoạ])
GIAO_DIEN_NHOM = {
    "3.2.4.1": (
        [
            "Toàn bộ nghiệp vụ két nằm trên một màn hình duy nhất (GD03) và màn hình này có "
            "hai trạng thái loại trừ nhau: *khi chưa mở két* và *khi két đang mở*. Tác giả "
            "chọn cách này thay vì chia thành nhiều màn hình con vì trạng thái khoá/mở là "
            "thông tin an toàn quan trọng nhất của phiên làm việc — người dùng phải nhìn là "
            "biết ngay két đang mở hay đã khoá, không phải suy đoán từ việc mình đang đứng ở "
            "màn hình nào.",
            "Ở trạng thái chưa mở, màn hình xếp theo đúng thứ tự việc người dùng cần làm: mở "
            "két đã có, tạo két mới, và — đặt trong mục thu gọn “Thêm: khôi phục từ mảnh, "
            "hoặc kiểm tra tệp két” — các thao tác ít dùng nhưng quan trọng khi có sự cố. "
            "Riêng phần thiết lập khoá phục hồi khi tạo két được đặt trong mục mở rộng kèm "
            "một ví dụ cụ thể (“5 mảnh, cần 3” nghĩa là bất kỳ 3 trong 5 mảnh khôi phục "
            "được), vì đây là khái niệm người dùng phổ thông ít gặp và là quyết định chỉ "
            "làm được một lần lúc tạo két.",
            "Ở trạng thái đang mở, màn hình chuyển thành bảng điều khiển gồm các thẻ xếp "
            "chồng: thông tin két, danh sách tệp bên trong kèm nút thêm và trích xuất, ký "
            "tệp bằng khoá của két, xuất khoá công khai, tạo mảnh khôi phục, đổi mật khẩu. "
            "Thẻ đầu tiên là dải thông tin két có nút “Khoá” đặt ngay cạnh tên két, để "
            "thao tác kết thúc phiên là thứ người dùng nhìn thấy trước tiên khi vào bảng "
            "điều khiển.",
        ],
        ["GD03"],
    ),
    "3.2.4.2": (
        [
            "Hai màn hình GD04 và GD05 là nơi tác giả áp dụng triệt để nhất nguyên tắc thiết "
            "kế “ba bước có đánh số”: chọn tệp nguồn (1), đặt nơi lưu kết quả (2), nhập mật "
            "khẩu (3), rồi một nút hành động duy nhất. Các bước được đánh số hiển thị, "
            "không phải chỉ xếp cạnh nhau, để người dùng ít kinh nghiệm biết chắc mình đã "
            "làm đủ chưa.",
            "Mỗi ô chọn tệp vừa nhận thao tác kéo-thả vừa có nút “Duyệt…”; trên Android nút "
            "này mở bộ chọn tệp của hệ điều hành. Ô mật khẩu khi tạo có ô nhập lại để chặn "
            "lỗi gõ nhầm — một lỗi mà hậu quả là mất dữ liệu vĩnh viễn chứ không phải phiền "
            "phức nhỏ. Phần giải thích kỹ thuật (Argon2id, secretbox) được đưa vào mục thu "
            "gọn “Thông tin thêm”, mở ra khi người dùng muốn kiểm chứng, đóng lại khi không.",
            "Kết quả hiển thị trong một thẻ kết quả riêng ngay dưới nút hành động, và thẻ này "
            "bị xoá mỗi khi người dùng chuyển màn hình — để một kết luận “Đạt” của công cụ "
            "trước không bị đọc nhầm thành kết luận của công cụ sau.",
        ],
        ["GD04", "GD05"],
    ),
    "3.2.4.3": (
        [
            "Nhóm này có năm màn hình (GD06–GD10) vì tác giả tách theo *việc người dùng cần "
            "làm* chứ không theo thuật toán. Cùng dựa trên chữ ký số và hàm băm, nhưng “tôi "
            "muốn ký một tệp”, “tôi nhận được tệp có chữ ký và muốn kiểm tra”, “tôi cần một "
            "mã nhận dạng của tệp”, “tôi có mã nhận dạng và muốn đối chiếu”, “tôi vừa tải "
            "một tệp về và muốn kiểm tra mọi bằng chứng đi kèm” là năm tình huống khác nhau; "
            "gộp chúng vào một màn hình sẽ buộc người dùng phải tự phân biệt.",
            "Màn hình Ký tệp (GD06) chia làm hai khối theo trình tự bắt buộc: khối “Trước "
            "tiên, danh tính ký của bạn” để tạo cặp khoá, rồi khối ký tệp bên dưới. Trình tự "
            "này phản ánh ràng buộc thật của nghiệp vụ — không có khoá bí mật thì không ký "
            "được — nên giao diện thể hiện nó bằng bố cục thay vì bằng một thông báo lỗi sau "
            "khi người dùng đã thao tác nhầm.",
            "Màn hình Xác minh tệp tải về (GD10) là màn hình gộp có chủ ý: người dùng có thể "
            "nhập vân tay, hoặc chữ ký kèm khoá công khai, hoặc cả hai, và nhận về đúng một "
            "kết luận. Hai trường bằng chứng đều được đánh dấu “(tuỳ chọn)” ngay trên nhãn "
            "để không gây cảm giác bắt buộc phải có đủ.",
            "Với các màn hình cho kết luận đạt/không đạt, kết quả hiển thị bằng thẻ có màu và "
            "tiêu đề chữ, không chỉ bằng màu — bảo đảm người dùng khó phân biệt màu vẫn đọc "
            "được kết luận.",
        ],
        ["GD06", "GD07", "GD08", "GD09", "GD10"],
    ),
    "3.2.4.4": (
        [
            "Bốn màn hình (GD11–GD14) phủ hết vòng đời của cơ chế chia sẻ ngưỡng: chia một "
            "bí mật dạng văn bản, chia một tệp, ghép lại từ các mảnh, và chuyển mảnh sang "
            "máy khác bằng mã QR.",
            "Ở hai màn hình chia, tổng số mảnh và ngưỡng khôi phục là hai ô số đặt cạnh "
            "nhau, có sẵn giá trị mặc định hợp lý (3 mảnh, cần 2). Nhãn của chúng được viết "
            "bằng lời — “Tổng số mảnh” và “Cần bao nhiêu để khôi phục” — chứ không dùng ký "
            "hiệu k, n. Đây là điểm dễ hiểu sai nhất của toàn bộ ứng dụng, vì nhầm hai giá "
            "trị này dẫn tới hoặc mất dữ liệu, hoặc chia mà không đạt mục tiêu an toàn; ví "
            "dụ diễn giải đầy đủ bằng lời (“5 mảnh, cần 3 → bất kỳ 3 trong 5 mảnh khôi phục "
            "được”) được đặt ở màn hình thiết lập khoá phục hồi của két (GD03), nơi người "
            "dùng gặp khái niệm này lần đầu.",
            "Kết quả chia được trình bày thành danh sách các mảnh sao chép được từng dòng, "
            "kèm một dòng riêng ghi đường dẫn tệp dữ liệu niêm phong có nút sao chép — vì "
            "thiếu tệp này thì đủ mảnh cũng không khôi phục được. Ô nhập bí mật được xoá "
            "trắng ngay sau khi chia, và danh sách mảnh bị xoá khỏi màn hình khi người dùng "
            "chuyển sang công cụ khác, để bí mật và mã mảnh không nằm lại trên màn hình "
            "thiết bị.",
            "Màn hình ghép lại (GD13) nhận mảnh theo hai cách: chọn các tệp mảnh, hoặc dán "
            "trực tiếp các chuỗi mảnh. Khi số mảnh chưa đủ, ứng dụng báo rõ còn thiếu bao "
            "nhiêu thay vì chỉ báo thất bại — thông tin này không làm lộ bí mật nhưng giúp "
            "người dùng biết phải làm gì tiếp.",
        ],
        ["GD11", "GD12", "GD13", "GD14"],
    ),
    "3.2.4.5": (
        [
            "Ba màn hình (GD15–GD17) đặt cạnh nhau có dụng ý sư phạm: giấu, lấy ra, và phát "
            "hiện. Người học nhìn thấy ngay rằng che giấu là một kỹ thuật *có thể bị phát "
            "hiện*, chứ không phải một lớp bảo vệ tuyệt đối.",
            "Màn hình giấu dữ liệu (GD15) yêu cầu ảnh nền, tệp cần giấu, mật khẩu và nơi lưu; "
            "phần “Thông tin thêm” nói rõ ảnh nền không mất chất lượng thì kết quả lưu ở "
            "định dạng gốc, và mô tả thứ tự xử lý là mã hoá trước rồi mới nhúng.",
            "Màn hình phát hiện (GD17) là màn hình mà tác giả chủ động *hạ thấp* kỳ vọng của "
            "người dùng: kết quả được diễn đạt thành mức độ nghi ngờ kèm giải thích, và ngay "
            "dòng mô tả đầu màn hình đã ghi rõ đây là phép thử theo kinh nghiệm — có thể chỉ "
            "ra dấu hiệu đáng ngờ nhưng không bao giờ chứng minh được một ảnh là sạch. Đây "
            "là lựa chọn thiết kế đi ngược xu hướng phần mềm thường thấy (luôn báo “an "
            "toàn”), và là một nội dung huấn luyện có giá trị.",
        ],
        ["GD15", "GD16", "GD17"],
    ),
    "3.2.4.6": (
        [
            "Màn hình GD18 chứa cả hai chiều của nghiệp vụ thuỷ vân — đóng dấu và kiểm tra — "
            "xếp thành hai khối trên cùng một màn hình, vì hai thao tác này dùng chung đúng "
            "một mật khẩu và người dùng thường làm cả hai trong cùng một phiên.",
            "Phần “Thông tin thêm” nêu rõ hai ràng buộc quyết định kết quả: khả năng chống "
            "giả mạo của dấu phụ thuộc vào độ mạnh của mật khẩu, và ảnh phải được lưu ở định "
            "dạng không mất chất lượng — lưu lại thành JPEG hoặc đổi kích thước sẽ phá huỷ "
            "dấu. Ràng buộc thứ hai được nhắc lại một lần nữa trong nội dung thông báo khi "
            "kiểm tra không tìm thấy dấu hợp lệ, để người dùng phân biệt được “ảnh bị sửa” "
            "với “ảnh đã bị lưu lại sai định dạng”.",
        ],
        ["GD18"],
    ),
    "3.2.4.7": (
        [
            "Ba màn hình (GD19–GD21) tương ứng ba nghiệp vụ xem, xoá và so sánh. Ba màn hình "
            "này còn minh hoạ một cơ chế an toàn của kiến trúc: ngay khi khởi động, giao "
            "diện hỏi lõi xem mô-đun siêu dữ liệu có sẵn sàng không; nếu không, cả ba màn "
            "hình bị vô hiệu hoá kèm dải cảnh báo, thay vì để người dùng thao tác rồi mới "
            "nhận lỗi. Nguyên tắc ở đây là *mặc định đóng*: chưa xác nhận được là còn dùng "
            "được thì coi như không dùng được.",
            "Trên bản Android, mô-đun này là bản viết lại bằng Rust thuần nên phạm vi định "
            "dạng hẹp hơn bản máy tính để bàn. Giao diện phản ánh đúng phạm vi của bản đang "
            "chạy: dòng chú thích phạm vi được thay theo nền tảng, nêu rõ bản di động xử lý "
            "ảnh JPEG, PNG, TIFF, WebP, HEIF và xoá sạch được JPEG, PNG; định dạng ngoài "
            "phạm vi bị từ chối bằng lỗi có mã. Tác giả coi việc giao diện hứa hẹn nhiều hơn "
            "năng lực thật của bản dựng là một lỗi đúng nghĩa, không phải chuyện câu chữ.",
            "Màn hình xoá siêu dữ liệu (GD20) luôn ghi bản sạch ra tệp mới và giữ nguyên tệp "
            "gốc; màn hình so sánh (GD21) là công cụ để người dùng tự kiểm chứng rằng bước "
            "xoá đã thực sự có tác dụng, thay vì phải tin vào thông báo của ứng dụng.",
        ],
        ["GD19", "GD20", "GD21"],
    ),
    "3.2.4.8": (
        [
            "Nhóm này không có màn hình riêng: thông tin phiên bản hiển thị trong khối “Giới "
            "thiệu” mở từ thanh tiêu đề (thấy ở GD01), đúng theo nguyên tắc đưa các chuỗi kỹ "
            "thuật ra khỏi luồng thao tác chính.",
            "Hai màn hình khung của ứng dụng cũng thuộc phần này: Trang chủ (GD01) đóng vai "
            "trò bảng chọn theo câu hỏi “Bạn muốn làm gì?”, gồm khối bắt đầu nhanh, khối "
            "công cụ vừa dùng gần đây, và mục thu gọn chứa toàn bộ công cụ; Ngăn kéo điều "
            "hướng (GD02) trượt ra từ cạnh trái, nhóm 19 công cụ thành năm nhóm theo mục "
            "đích. Tác giả chọn ngăn kéo thay vì thanh thẻ dưới đáy vì 19 mục không thể xếp "
            "vừa một thanh thẻ, và Trang chủ đã đóng vai trò bảng chọn nên ngăn kéo chỉ cần "
            "bổ sung chứ không phải thay thế.",
        ],
        ["GD01", "GD02"],
    ),
}
