#!/usr/bin/env python3
"""Nội dung tám nhóm chức năng — bảng chức năng và phần “Giao diện tương ứng”.

Nguồn văn bản: bản Thuyết minh do tác giả trực tiếp rà soát và chỉnh sửa. Tách riêng
khỏi hai tệp sinh văn bản vì cả Thuyết minh (bản rút gọn) và Đề cương chi tiết (bản đầy
đủ) đều dùng chung dữ liệu này, nên chỉ có một chỗ để sửa khi nội dung thay đổi.

Mỗi nhóm là một từ điển:
    ten        — tiêu đề nhóm
    dan_nhap   — đoạn dẫn nhập: nhóm này giải quyết việc gì
    chuc_nang  — bảng (Chức năng | Đầu vào | Xử lý | Kết quả), dòng đầu là tiêu đề cột
    giao_dien  — các đoạn mô tả giao diện thực hiện nhóm chức năng đó
    man_hinh   — bảng (Mã màn hình | Tên màn hình | Chức năng được thực hiện)
"""

NHOM_CHUC_NANG = [
    {
        "ten": "Nhóm 1. Két an toàn",
        "dan_nhap": "Két an toàn là một tệp duy nhất có phần mở rộng .svault, hoạt động như "
                    "một kho chứa được bảo vệ bằng mật khẩu. Bên trong két có thể lưu nhiều "
                    "tệp cùng thông tin danh mục; toàn bộ nội dung và danh mục đều được mã "
                    "hóa. Nhờ đó, người dùng chỉ cần quản lý một mật khẩu cho cả két, đồng "
                    "thời người có tệp két nhưng không có mật khẩu không thể xem nội dung "
                    "hoặc tên các tệp bên trong.",
        "chuc_nang": [
            (
                "Chức năng",
                "Đầu vào",
                "Xử lý",
                "Kết quả",
            ),
            (
                "Tạo két mới",
                "Vị trí lưu, mật khẩu, tùy chọn chính sách phục hồi khóa",
                "Sinh khoá chính từ mật khẩu bằng Argon2id; sinh cặp khoá nội dung và cặp "
                "khoá ký riêng cho két; Ghi tệp theo cơ chế an toàn, bảo đảm tệp cũ không bị "
                "thay đổi nếu quá trình ghi bị gián đoạn.",
                "Tệp .svault mới kèm thông tin tóm tắt của két",
            ),
            (
                "Mở két",
                "Tệp két, mật khẩu",
                "Kiểm tra tính hợp lệ của tệp, sau đó xác thực mật khẩu và mở nội dung",
                "Mã phiên làm việc để thực hiện các thao tác trên két",
            ),
            (
                "Khoá két",
                "Mã phiên",
                "Xoá khoá chính khỏi bộ nhớ phiên",
                "Phiên kết thúc; muốn mở lại phải nhập mật khẩu",
            ),
            (
                "Đổi mật khẩu két",
                "Mã phiên, mật khẩu mới",
                "Tạo khóa chính mới và bảo vệ lại các khóa bên trong; không cần mã hóa lại "
                "toàn bộ nội dung",
                "Két sử dụng mật khẩu mới; dữ liệu bên trong không thay đổi",
            ),
            (
                "Xem thông tin két",
                "Mã phiên",
                "Đọc và xác thực thông tin phần đầu tệp",
                "Mã định danh két, phiên bản định dạng, thời điểm tạo và sửa, số tệp bên "
                "trong, chính sách khoá phục hồi",
            ),
            (
                "Thêm tệp vào két",
                "Mã phiên, tệp nguồn, tên đặt trong két",
                "Mã hóa và bổ sung tệp vào danh mục của két",
                "Tệp được lưu trong két; tệp gốc bên ngoài không bị thay đổi",
            ),
            (
                "Liệt kê tệp trong két",
                "Mã phiên",
                "Đọc danh mục tệp đã giải mã trong bộ nhớ",
                "Danh sách tên tệp, kích thước và thời điểm thêm",
            ),
            (
                "Trích xuất tệp khỏi két",
                "Mã phiên, tên tệp trong két, nơi lưu",
                "Giải mã và ghi ra tệp mới",
                "Tệp được khôi phục từ két",
            ),
            (
                "Ký tệp bằng két",
                "Mã phiên, tệp cần ký",
                "Sử dụng khoá ký riêng của két để tạo chữ ký số",
                "Tệp chữ ký để kiểm tra nguồn gốc và tính toàn vẹn của tệp",
            ),
            (
                "Xuất khoá công khai của két",
                "Mã phiên",
                "Đọc khóa công khai từ thông tin của két",
                "Khóa công khai để kiểm tra chữ ký do két tạo",
            ),
            (
                "Kiểm tra tính toàn vẹn của két",
                "Tệp két (không cần mật khẩu)",
                "Kiểm tra chữ ký bảo vệ phần thông tin đầu tệp",
                "Kết luận tệp còn nguyên vẹn hay đã bị thay đổi, không cần mở két",
            ),
            (
                "Lấy vân tay tệp két",
                "Tệp két",
                "Tính giá trị băm BLAKE3 của toàn bộ tệp",
                "Chuỗi vân tay để đối chiếu tệp giữa các thiết bị",
            ),
        ],
        "giao_dien": [
            "Toàn bộ chức năng của két được bố trí trên một màn hình (GD03), với hai trạng "
            "thái rõ ràng: chưa mở két và đang mở két. Cách tổ chức này giúp trạng thái "
            "khóa/mở của két luôn được thể hiện trực quan, đồng thời hạn chế nhầm lẫn trong "
            "quá trình sử dụng.",
            "Khi chưa mở két, giao diện tập trung vào các thao tác chính gồm mở két, tạo két "
            "mới và nhóm các chức năng phục hồi, kiểm tra tệp trong mục mở rộng. Khi tạo két, "
            "thiết lập khóa phục hồi được đặt trong phần tùy chọn mở rộng, kèm ví dụ minh họa "
            "như “5 mảnh, cần 3”, giúp người dùng dễ hiểu cơ chế phục hồi.",
            "Khi két đang mở, giao diện chuyển sang bảng điều khiển gồm thông tin két, danh "
            "sách tệp và các chức năng thêm, trích xuất, ký tệp, xuất khóa công khai, tạo "
            "mảnh phục hồi và đổi mật khẩu. Nút “Khóa” được đặt ngay cạnh tên két để thao tác "
            "kết thúc phiên luôn được hiển thị rõ ràng.",
        ],
        "man_hinh": [
            ("Mã màn hình", "Tên màn hình", "Chức năng được thực hiện"),
            ("GD03", "Két an toàn", "vault_create, vault_unlock, vault_lock, vault_change_passphrase, vault_meta, "
                "item_add, item_list, item_extract, sign_file, export_signing_public_key, "
                "integrity_check, integrity_hash, keys_split, keys_recover, verify_file"),
        ],
    },
    {
        "ten": "Nhóm 2. Bảo vệ tệp đơn lẻ",
        "dan_nhap": "Không phải trường hợp nào cũng cần sử dụng két an toàn. Khi chỉ cần bảo "
                    "vệ một tệp riêng lẻ để lưu trữ hoặc chuyển giao, người dùng có thể khóa "
                    "trực tiếp tệp bằng mật khẩu. Tệp kết quả chứa đầy đủ thông tin cần thiết "
                    "để thực hiện quá trình mở khóa trên thiết bị hoặc công cụ tương thích "
                    "khi có đúng mật khẩu.",
        "chuc_nang": [
            (
                "Chức năng",
                "Đầu vào",
                "Xử lý",
                "Kết quả",
            ),
            (
                "Khoá một tệp bằng mật khẩu",
                "Tệp cần khóa, mật khẩu, vị trí lưu kết quả",
                "Dẫn xuất khoá từ mật khẩu bằng Argon2id rồi mã hoá có xác thực",
                "Tệp đã khóa; mọi thay đổi đối với nội dung đều được phát hiện khi mở khóa",
            ),
            (
                "Mở khoá tệp",
                "Tệp đã khóa, mật khẩu, vị trí lưu kết quả",
                "Dẫn xuất lại khoá và giải mã, đồng thời kiểm tra tính toàn vẹn",
                "Tệp gốc được khôi phục nếu thông tin hợp lệ; thông báo lỗi nếu mật khẩu "
                "không đúng hoặc tệp bị thay đổi",
            ),
            (
                "Sao chép tệp an toàn",
                "Tệp gốc, vị trí lưu",
                "Sao chép tệp và kiểm tra kết quả sau khi sao chép",
                "Bản sao được kiểm tra, sử dụng cho các bước xử lý tiếp theo mà không làm "
                "thay đổi tệp gốc",
            ),
        ],
        "giao_dien": [
            "Hai màn hình GD04 và GD05 được thiết kế theo quy trình ba bước có đánh số: (1) "
            "chọn tệp nguồn, (2) chọn vị trí lưu kết quả, (3) nhập mật khẩu, sau đó thực hiện "
            "thao tác bằng một nút chức năng chính. Cách đánh số giúp người dùng dễ theo dõi "
            "trình tự và kiểm tra các thông tin cần thiết trước khi thực hiện.",
            "Ô mật khẩu khi tạo tệp có thêm trường nhập lại để hạn chế lỗi nhập sai. Các "
            "thông tin kỹ thuật như Argon2id và secretbox được đặt trong mục “Thông tin "
            "thêm”, tránh làm giao diện chính quá phức tạp. Kết quả xử lý được hiển thị trong "
            "một thẻ riêng và được xóa khi chuyển màn hình, giúp tránh nhầm lẫn giữa kết quả "
            "của các thao tác khác nhau.",
        ],
        "man_hinh": [
            ("Mã màn hình", "Tên màn hình", "Chức năng được thực hiện"),
            ("GD04", "Khoá tệp", "crypto_encrypt_file"),
            ("GD05", "Mở khoá tệp", "crypto_decrypt_file, copy_file"),
        ],
    },
    {
        "ten": "Nhóm 3. Kiểm chứng nguồn gốc và tính toàn vẹn",
        "dan_nhap": "Mã hóa giúp bảo vệ nội dung tệp khỏi việc đọc trái phép, trong khi nhóm "
                    "chức năng này tập trung kiểm tra nguồn gốc và tính toàn vẹn của tệp. Chữ "
                    "ký số giúp xác minh tệp có đúng do người ký tạo hoặc xác nhận hay không; "
                    "giá trị băm giúp đối chiếu xem tệp có bị thay đổi so với bản được cung "
                    "cấp ban đầu hay không. Đây là các chức năng cần thiết khi trao đổi và "
                    "kiểm tra tài liệu.",
        "chuc_nang": [
            (
                "Chức năng",
                "Đầu vào",
                "Xử lý",
                "Kết quả",
            ),
            (
                "Tạo cặp khoá ký",
                "Thư mục lưu, tên định danh, mật khẩu bảo vệ khoá bí mật",
                "Sinh cặp khoá Ed25519; khoá bí mật được bảo vệ bằng mật khẩu",
                "Tệp khoá công khai để chia sẻ và tệp khoá bí mật để giữ riêng",
            ),
            (
                "Ký một tệp",
                "Tệp cần ký, khoá bí mật, mật khẩu",
                "Tạo chữ ký số theo định dạng minisign",
                "Tệp chữ ký đi kèm tệp gốc",
            ),
            (
                "Kiểm tra chữ ký",
                "Tệp, tệp chữ ký, khoá công khai của người ký",
                "Xác minh chữ ký trên nội dung tệp",
                "Kết luận chữ ký hợp lệ hoặc không hợp lệ; mọi thay đổi nội dung sau khi ký "
                "đều làm chữ ký không còn hợp lệ",
            ),
            (
                "Lấy vân tay tệp",
                "Tệp bất kỳ",
                "Tính giá trị băm BLAKE3",
                "Chuỗi vân tay dùng để đối chiếu hai bản sao của cùng một tệp",
            ),
            (
                "Đối chiếu tệp với vân tay cho trước",
                "Tệp, chuỗi vân tay nhận được",
                "Tính lại giá trị băm và so sánh với vân tay đã cung cấp",
                "Kết luận tệp có khớp với vân tay được cung cấp hay không",
            ),
            (
                "Xác minh tệp tải về",
                "Tệp, vân tay và/hoặc chữ ký kèm khoá công khai",
                "Kiểm tra các bằng chứng được cung cấp",
                "Kết luận đạt/không đạt, tránh phải dùng nhiều công cụ rời rạc",
            ),
        ],
        "giao_dien": [
            "Nhóm chức năng này gồm năm màn hình (GD06–GD10), được phân chia theo mục đích sử "
            "dụng. Mặc dù các chức năng đều sử dụng chữ ký số hoặc hàm băm, mỗi màn hình phục "
            "vụ một thao tác riêng như tạo khóa ký, ký tệp, kiểm tra chữ ký, lấy vân tay, đối "
            "chiếu vân tay và xác minh tệp tải về. Cách tổ chức này giúp người dùng lựa chọn "
            "đúng chức năng theo nhu cầu thực tế.",
            "Màn hình Ký tệp (GD06) bố trí việc tạo cặp khóa ký và ký tệp theo trình tự, bảo "
            "đảm người dùng có khóa bí mật trước khi thực hiện ký. Màn hình Xác minh tệp tải "
            "về (GD10) cho phép sử dụng vân tay, chữ ký kèm khóa công khai hoặc đồng thời cả "
            "hai loại bằng chứng; các trường không bắt buộc được đánh dấu rõ ràng là “(tùy "
            "chọn)”. Kết quả kiểm tra được thể hiện bằng thẻ kết quả có cả màu sắc và tiêu đề "
            "chữ, giúp người dùng nhận biết rõ trạng thái đạt/không đạt.",
        ],
        "man_hinh": [
            ("Mã màn hình", "Tên màn hình", "Chức năng được thực hiện"),
            ("GD06", "Ký tệp", "crypto_generate_signing_keypair, crypto_sign_file"),
            ("GD07", "Kiểm tra chữ ký", "integrity_verify_signature"),
            ("GD08", "Lấy vân tay tệp", "integrity_hash_file"),
            ("GD09", "Kiểm tra tệp chưa bị đổi", "integrity_hash_file"),
            ("GD10", "Xác minh tệp tải về", "integrity_verify_integrity"),
        ],
    },
    {
        "ten": "Nhóm 4. Sao lưu và khôi phục bằng chia sẻ bí mật theo ngưỡng",
        "dan_nhap": "Do ứng dụng không lưu mật khẩu và khóa bí mật lâu dài, việc quên mật "
                    "khẩu có thể dẫn đến mất khả năng truy cập dữ liệu. Nhóm chức năng này sử "
                    "dụng cơ chế chia sẻ bí mật Shamir, cho phép chia một bí mật thành nhiều "
                    "phần và quy định số phần tối thiểu cần có để khôi phục. Ví dụ, với cấu "
                    "hình “5 mảnh, cần 3”, bất kỳ 3 trong 5 mảnh đều có thể được sử dụng để "
                    "khôi phục. Khi chưa đủ số mảnh theo ngưỡng, bí mật không thể được khôi "
                    "phục.",
        "chuc_nang": [
            (
                "Chức năng",
                "Đầu vào",
                "Xử lý",
                "Kết quả",
            ),
            (
                "Chia một bí mật thành nhiều mảnh",
                "Chuỗi bí mật (mật khẩu, khoá, cụm từ khôi phục), tổng số mảnh n, ngưỡng khôi "
                "phục k",
                "Sinh khoá ngẫu nhiên, sử dụng cơ chế Shamir để chia bí mật và bảo vệ dữ liệu "
                "liên quan bằng khóa đó",
                "Các tệp mảnh và tệp dữ liệu cần thiết để khôi phục; phải có đủ số mảnh theo "
                "ngưỡng",
            ),
            (
                "Chia một tệp thành nhiều mảnh",
                "Tệp bất kỳ, tổng số mảnh, ngưỡng",
                "Bảo vệ nội dung tệp, sau đó chia khóa bảo vệ theo cơ chế Shamir",
                "Các tệp mảnh và tệp dữ liệu cần thiết để khôi phục tệp",
            ),
            (
                "Khôi phục từ các mảnh",
                "Đủ số mảnh theo ngưỡng, tệp dữ liệu cần khôi phục",
                "Ghép khóa từ các mảnh và sử dụng khóa đó để khôi phục dữ liệu",
                "Bí mật hoặc tệp ban đầu; nếu chưa đủ mảnh, hệ thống thông báo số mảnh còn "
                "thiếu",
            ),
            (
                "Tạo mảnh khôi phục cho két",
                "Mã phiên của két đang mở, tổng số mảnh, ngưỡng",
                "Chia khoá dự phòng của két theo Shamir",
                "Các mảnh dùng để khôi phục quyền truy cập két khi không còn mật khẩu",
            ),
            (
                "Khôi phục két từ các mảnh",
                "Tệp két, đủ số mảnh theo ngưỡng",
                "Khôi phục khóa từ các mảnh và sử dụng khóa đó để mở két",
                "Phiên làm việc được mở mà không cần mật khẩu ban đầu",
            ),
            (
                "Xuất mảnh ra mã QR",
                "Các chuỗi mảnh",
                "Sinh ảnh mã QR cho từng mảnh",
                "Ảnh mã QR có thể in hoặc chuyển sang thiết bị khác",
            ),
            (
                "Khôi phục từ ảnh mã QR",
                "Đủ số ảnh QR theo ngưỡng, tệp dữ liệu cần khôi phục",
                "Đọc dữ liệu từ các mã QR, sau đó thực hiện khôi phục như đối với các mảnh "
                "thông thường",
                "Bí mật hoặc tệp ban đầu",
            ),
        ],
        "giao_dien": [
            "Nhóm chức năng này gồm bốn màn hình (GD11–GD14), tương ứng với các thao tác "
            "chính: chia một bí mật, chia một tệp, khôi phục từ các mảnh và chuyển mảnh bằng "
            "mã QR.",
            "Tại các màn hình chia, tổng số mảnh và số mảnh tối thiểu để khôi phục được nhập "
            "riêng và có giá trị mặc định phù hợp. Giao diện sử dụng cách diễn đạt bằng lời "
            "thay cho ký hiệu k, n, đồng thời minh họa cụ thể như “5 mảnh, cần 3 → bất kỳ 3 "
            "trong 5 mảnh đều có thể khôi phục” để hạn chế nhầm lẫn khi thiết lập.",
            "Sau khi chia, các mảnh được hiển thị thành danh sách để người dùng sao chép; "
            "thông tin về tệp dữ liệu cần thiết cho quá trình khôi phục cũng được hiển thị "
            "riêng. Dữ liệu bí mật đầu vào được xóa khỏi ô nhập sau khi xử lý, đồng thời danh "
            "sách mảnh được xóa khi chuyển sang chức năng khác, hạn chế việc thông tin nhạy "
            "cảm còn hiển thị trên màn hình.",
            "Màn hình khôi phục (GD13) cho phép nhập mảnh bằng cách chọn tệp hoặc dán trực "
            "tiếp chuỗi mảnh. Khi chưa đủ số mảnh theo ngưỡng, hệ thống thông báo số mảnh còn "
            "thiếu để người dùng bổ sung trước khi thực hiện khôi phục.",
        ],
        "man_hinh": [
            ("Mã màn hình", "Tên màn hình", "Chức năng được thực hiện"),
            ("GD11", "Chia nhỏ bí mật", "shares_split_secret"),
            ("GD12", "Chia nhỏ tệp", "shares_split_file"),
            ("GD13", "Ghép lại từ các mảnh", "shares_recover_secret, copy_file"),
            ("GD14", "Chuyển mảnh bằng mã QR", "shares_export_qr, shares_recover_from_qr"),
        ],
    },
    {
        "ten": "Nhóm 5. Che giấu dữ liệu trong ảnh và phát hiện dữ liệu ẩn",
        "dan_nhap": "Che giấu dữ liệu không thay thế cho mã hóa mà được sử dụng như một lớp "
                    "bổ sung. Dữ liệu được mã hóa trước khi nhúng vào ảnh, do đó nếu dữ liệu "
                    "ẩn bị phát hiện thì nội dung vẫn cần mật khẩu để giải mã. Chức năng phát "
                    "hiện dữ liệu ẩn giúp người dùng nhận biết rằng kỹ thuật che giấu không "
                    "bảo đảm dữ liệu không bị phát hiện, qua đó làm rõ giới hạn của phương "
                    "pháp trong quá trình sử dụng và huấn luyện.",
        "chuc_nang": [
            (
                "Chức năng",
                "Đầu vào",
                "Xử lý",
                "Kết quả",
            ),
            (
                "Giấu dữ liệu vào ảnh",
                "Ảnh nền, tệp cần giấu, mật khẩu, tuỳ chọn phân tán dữ liệu",
                "Mã hoá tệp trước, sau đó nhúng vào các bit ít quan trọng của ảnh",
                "Ảnh mới nhìn bằng mắt không khác ảnh gốc, mang dữ liệu đã mã hoá bên trong",
            ),
            (
                "Lấy dữ liệu đã giấu ra",
                "Ảnh có dữ liệu ẩn, mật khẩu, thư mục lưu",
                "Trích các bit ẩn rồi giải mã",
                "Tệp ban đầu, giữ nguyên tên và phần mở rộng",
            ),
            (
                "Phát hiện dấu hiệu dữ liệu ẩn",
                "Ảnh bất kỳ",
                "Phân tích dữ liệu thừa sau điểm kết thúc ảnh và thống kê bit ít quan trọng",
                "Mức độ nghi ngờ kèm giải thích về các dấu hiệu được phát hiện; kết quả không "
                "phát hiện không đồng nghĩa với việc khẳng định ảnh không chứa dữ liệu ẩn",
            ),
        ],
        "giao_dien": [
            "Ba màn hình GD15–GD17 tương ứng với ba thao tác: giấu dữ liệu, lấy dữ liệu và "
            "phát hiện dữ liệu ẩn. Cách bố trí này giúp người dùng phân biệt rõ chức năng che "
            "giấu với chức năng kiểm tra, đồng thời thể hiện giới hạn của kỹ thuật che giấu "
            "dữ liệu.",
            "Màn hình Giấu dữ liệu (GD15) yêu cầu lựa chọn ảnh nền, tệp cần giấu, mật khẩu và "
            "vị trí lưu kết quả. Phần “Thông tin thêm” giải thích thứ tự xử lý: dữ liệu được "
            "mã hóa trước khi nhúng vào ảnh và thông tin về định dạng tệp đầu ra.",
            "Màn hình Phát hiện dữ liệu ẩn (GD17) không đưa ra kết luận tuyệt đối về việc ảnh "
            "có chứa dữ liệu ẩn hay không. Kết quả được thể hiện dưới dạng mức độ nghi ngờ "
            "kèm các dấu hiệu được phát hiện, đồng thời giải thích rõ rằng việc không phát "
            "hiện dấu hiệu qua các phép kiểm tra không đồng nghĩa với việc ảnh hoàn toàn "
            "không chứa dữ liệu ẩn. Cách thể hiện này giúp người dùng hiểu đúng giới hạn của "
            "công cụ và tránh diễn giải kết quả theo hướng tuyệt đối.",
        ],
        "man_hinh": [
            ("Mã màn hình", "Tên màn hình", "Chức năng được thực hiện"),
            ("GD15", "Giấu dữ liệu trong ảnh", "stego_hide"),
            ("GD16", "Hiện dữ liệu ẩn", "stego_extract, copy_file"),
            ("GD17", "Phát hiện dữ liệu ẩn", "stego_detect"),
        ],
    },
    {
        "ten": "Nhóm 6. Thuỷ vân chống giả mạo ảnh",
        "dan_nhap": "“Thủy vân dễ vỡ” (fragile watermark) là một dấu hiệu vô hình được gắn "
                    "với mật khẩu và nhúng vào ảnh. Khi ảnh bị chỉnh sửa, thủy vân có thể bị "
                    "phá vỡ, qua đó giúp kiểm tra tính toàn vẹn của ảnh và xác định các vùng "
                    "có dấu hiệu bị thay đổi. Khác với chữ ký số chủ yếu cho biết tệp có còn "
                    "nguyên vẹn hay không, thủy vân còn hỗ trợ khoanh vùng vị trí thay đổi "
                    "trên ảnh.",
        "chuc_nang": [
            (
                "Chức năng",
                "Đầu vào",
                "Xử lý",
                "Kết quả",
            ),
            (
                "Nhúng thuỷ vân",
                "Ảnh PNG hoặc BMP, mật khẩu, nơi lưu",
                "Tính mã xác thực theo từng khối ảnh, khoá bằng mật khẩu, nhúng vào bit ít "
                "quan trọng",
                "Ảnh đã được nhúng thủy vân; tệp ảnh gốc không bị thay đổi",
            ),
            (
                "Kiểm tra thuỷ vân",
                "Ảnh đã nhúng thủy vân, mật khẩu",
                "Tính lại mã xác thực theo từng khối và đối chiếu với thông tin thủy vân",
                "Kết luận ảnh còn nguyên vẹn hay đã bị sửa, kèm vị trí các vùng bị thay đổi",
            ),
        ],
        "giao_dien": [
            "Màn hình GD18 tích hợp hai thao tác nhúng thủy vân và kiểm tra thủy vân trên "
            "cùng một giao diện. Hai thao tác sử dụng chung cơ chế bảo vệ bằng mật khẩu và "
            "thường được thực hiện liên tiếp trong quá trình kiểm tra ảnh.",
            "Phần “Thông tin thêm” nêu rõ các điều kiện ảnh hưởng đến kết quả kiểm tra: độ an "
            "toàn của thủy vân phụ thuộc vào mật khẩu được sử dụng; ảnh cần được lưu ở định "
            "dạng không mất dữ liệu như PNG hoặc BMP. Việc chuyển sang JPEG hoặc thay đổi "
            "kích thước ảnh có thể làm thủy vân không còn hợp lệ. Khi kiểm tra không đạt, "
            "giao diện đồng thời lưu ý khả năng ảnh đã bị chỉnh sửa hoặc đã bị biến đổi trong "
            "quá trình lưu trữ, giúp người dùng tránh đồng nhất hai trường hợp này.",
        ],
        "man_hinh": [
            ("Mã màn hình", "Tên màn hình", "Chức năng được thực hiện"),
            ("GD18", "Chống giả mạo ảnh", "watermark_embed, watermark_verify"),
        ],
    },
    {
        "ten": "Nhóm 7. Siêu dữ liệu ẩn trong tệp",
        "dan_nhap": "Ảnh chụp bằng điện thoại có thể chứa các thông tin như tọa độ GPS, kiểu "
                    "thiết bị, thời điểm chụp và một số thông tin khác. Những dữ liệu này có "
                    "thể được chia sẻ cùng tệp ảnh mà người dùng không nhận biết. Nhóm chức "
                    "năng này cho phép xem, xóa và đối chiếu siêu dữ liệu trực tiếp trên "
                    "thiết bị, giúp người dùng kiểm tra và loại bỏ những thông tin không cần "
                    "thiết trước khi chia sẻ tệp.",
        "chuc_nang": [
            (
                "Chức năng",
                "Đầu vào",
                "Xử lý",
                "Kết quả",
            ),
            (
                "Xem siêu dữ liệu của tệp",
                "Tệp ảnh",
                "Đọc và nhóm các thẻ theo loại; nhóm toạ độ GPS được tách riêng vì nhạy cảm "
                "nhất",
                "Danh sách thẻ theo nhóm kèm định dạng và kiểu MIME; thao tác chỉ đọc, không "
                "sửa tệp",
            ),
            (
                "Xoá siêu dữ liệu",
                "Tệp ảnh, nơi lưu bản sạch",
                "Dựng lại tệp từ dữ liệu ảnh, loại bỏ khối EXIF, hồ sơ màu, chú thích và các "
                "khối văn bản; ghi theo kiểu nguyên tử",
                "Bản sao đã sạch siêu dữ liệu; tệp gốc giữ nguyên; báo cáo số thẻ trước và "
                "sau",
            ),
            (
                "So sánh siêu dữ liệu hai tệp",
                "Hai tệp ảnh",
                "Đối chiếu tập thẻ của hai tệp, bỏ qua tên tệp và dấu thời gian của hệ thống",
                "Danh sách thẻ chỉ có ở tệp thứ nhất, chỉ có ở tệp thứ hai, và các thẻ khác "
                "giá trị",
            ),
            (
                "Kiểm tra mô-đun sẵn sàng",
                "Không có",
                "Kiểm tra và báo trạng thái sẵn sàng của mô-đun cho giao diện",
                "Giao diện biết trạng thái để bật hoặc vô hiệu hóa các chức năng tương ứng",
            ),
        ],
        "giao_dien": [
            "Ba màn hình GD19–GD21 tương ứng với ba nghiệp vụ xem, xóa và so sánh siêu dữ "
            "liệu. Khi khởi động, giao diện kiểm tra trạng thái sẵn sàng của mô-đun siêu dữ "
            "liệu; nếu mô-đun không sẵn sàng, các chức năng liên quan được vô hiệu hóa và "
            "hiển thị cảnh báo. Cách tổ chức này thực hiện nguyên tắc “mặc định đóng”: khi "
            "chưa xác nhận được thành phần xử lý sẵn sàng, hệ thống không cho phép thực hiện "
            "chức năng phụ thuộc vào thành phần đó.",
            "Trên Android, mô-đun siêu dữ liệu được triển khai bằng Rust nên phạm vi định "
            "dạng được hỗ trợ được xác định rõ theo phiên bản đang chạy. Giao diện công bố cụ "
            "thể các định dạng được xử lý và các định dạng được hỗ trợ xóa siêu dữ liệu; định "
            "dạng ngoài phạm vi bị từ chối với thông báo lỗi có mã. Cách thể hiện này bảo đảm "
            "giao diện phản ánh đúng khả năng thực tế của mô-đun, tránh tạo kỳ vọng vượt quá "
            "phạm vi xử lý.",
            "Màn hình Xóa siêu dữ liệu (GD20) luôn tạo tệp kết quả mới và giữ nguyên tệp gốc. "
            "Màn hình So sánh siêu dữ liệu (GD21) cho phép đối chiếu trực tiếp trước và sau "
            "khi xử lý, giúp người dùng kiểm tra kết quả thay vì chỉ dựa vào thông báo của "
            "ứng dụng.",
        ],
        "man_hinh": [
            ("Mã màn hình", "Tên màn hình", "Chức năng được thực hiện"),
            ("GD19", "Xem siêu dữ liệu", "metadata_inspect"),
            ("GD20", "Xoá siêu dữ liệu", "metadata_sanitize"),
            ("GD21", "So sánh siêu dữ liệu", "metadata_diff"),
        ],
    },
    {
        "ten": "Nhóm 8. Thông tin ứng dụng",
        "dan_nhap": "Nhóm này cung cấp thông tin phiên bản của ứng dụng để phục vụ việc đối "
                    "chiếu khi trao đổi tệp giữa các thiết bị. Thông tin bao gồm phiên bản "
                    "ứng dụng, phiên bản giao diện lệnh, phiên bản định dạng két và phiên bản "
                    "bộ thuật toán mà ứng dụng đang sử dụng.",
        "chuc_nang": [
            (
                "Chức năng",
                "Đầu vào",
                "Xử lý",
                "Kết quả",
            ),
            (
                "Xem thông tin phiên bản",
                "Không có",
                "Đọc các thông tin phiên bản được xác định khi xây dựng ứng dụng",
                "Phiên bản ứng dụng, phiên bản giao tiếp với lõi xử lý, phiên bản định dạng "
                "két và phiên bản bộ thuật toán",
            ),
        ],
        "giao_dien": [
            "Nhóm này không có màn hình riêng. Thông tin phiên bản được hiển thị trong mục "
            "“Giới thiệu” mở từ thanh tiêu đề của màn hình chính (GD01), qua đó đưa các thông "
            "tin kỹ thuật ra khỏi luồng thao tác chính nhưng vẫn bảo đảm khả năng tra cứu khi "
            "cần.",
            "Trang chủ (GD01) đóng vai trò điểm bắt đầu, cung cấp các chức năng thường dùng "
            "và toàn bộ công cụ theo nhóm. Ngăn kéo điều hướng (GD02) tổ chức 19 công cụ "
            "thành năm nhóm theo mục đích sử dụng. Việc sử dụng ngăn kéo phù hợp với số lượng "
            "công cụ lớn, đồng thời bổ sung cho Trang chủ thay vì thay thế chức năng của màn "
            "hình này.",
        ],
        "man_hinh": [
            ("Mã màn hình", "Tên màn hình", "Chức năng được thực hiện"),
            ("GD01", "Trang chủ", "app_info (qua khối Giới thiệu)"),
            ("GD02", "Ngăn kéo điều hướng", "không gọi lệnh; điều hướng giữa các màn hình"),
        ],
    },
]
