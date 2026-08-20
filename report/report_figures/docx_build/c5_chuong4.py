# -*- coding: utf-8 -*-
"""CHUONG 4 — Thu nghiem va danh gia he thong."""


def blocks():
    B = [("h1", "CHƯƠNG 4\nTHỬ NGHIỆM VÀ ĐÁNH GIÁ HỆ THỐNG")]

    # ============================== 1. Moi truong va phuong phap
    B += [
        ("h2", "1. Môi trường và phương pháp thử nghiệm"),

        ("h3", "1.1. Môi trường thử nghiệm"),
        ("p", "Việc đánh giá hệ thống được thực hiện trên hai môi trường có vai trò khác nhau. Môi "
              "trường thứ nhất là hạ tầng tích hợp liên tục, phục vụ kiểm thử tự động trên diện rộng và "
              "trên nhiều hệ điều hành. Môi trường thứ hai là một máy phát triển đơn lẻ, phục vụ các "
              "phép đo hiệu năng và các thực nghiệm kiểm chứng giả thuyết rủi ro vốn đòi hỏi thao tác "
              "thủ công và quan sát chi tiết."),
        ("tbl", "Bảng 4.1. Cấu hình các môi trường thử nghiệm",
         ["Thành phần", "Môi trường tích hợp liên tục", "Môi trường đo hiệu năng"],
         [
             ["Hệ điều hành", "Ma trận ba nền: Ubuntu, macOS, Windows (bản chạy trên máy chủ)",
              "macOS 14.6, kiến trúc arm64"],
             ["Trình biên dịch", "Rust ổn định, kèm một nhóm việc riêng cố định phiên bản tối thiểu 1.96",
              "Rust 1.96"],
             ["Chế độ dựng", "Mặc định cho kiểm thử; có nhóm việc dựng với tệp khóa phiên bản",
              "Bản dựng tối ưu (release)"],
             ["Công cụ age", "Cài qua chuỗi công cụ Go trong nhóm việc chính",
              "age và age-keygen phiên bản 1.3.1"],
             ["Công cụ ExifTool", "Không được nạp; mô-đun Phân tích ở trạng thái tắt an toàn",
              "Không được nạp"],
             ["Bộ mã hóa tải trọng dùng trong kiểm thử đơn vị",
              "Bộ giả lập trong bộ nhớ (không cần nhị phân ngoài)",
              "Bộ thật, điều khiển tiến trình con age"],
             ["Phạm vi", "Toàn bộ workspace, cộng thêm crate giao diện được kiểm riêng",
              "Một bộ khai thác riêng dựng trực tiếp trên lớp dịch vụ két"],
         ], [3.4, 6.6, 6.2], 10),
        ("p", "Cần nêu rõ một khác biệt quan trọng giữa hai môi trường: bộ kiểm thử đơn vị của workspace "
              "sử dụng một **bộ mã hóa tải trọng giả lập** chạy hoàn toàn trong bộ nhớ. Đây là lựa chọn "
              "cho phép toàn bộ vòng đời của két được kiểm thử trên máy không cài age, nhưng nó cũng có "
              "nghĩa là bộ kiểm thử đơn vị **không hề chạm tới** tiến trình con, hạn giờ, cơ chế đệm "
              "trong bộ nhớ, việc xóa biến môi trường hay tệp tạm chứa danh tính. Chính khoảng trống này "
              "là lý do tồn tại của chiến dịch kiểm chứng giả thuyết rủi ro ở mục 5."),

        ("h3", "1.2. Bốn trụ cột kiểm chứng"),
        ("p", "Việc đánh giá dựa trên bốn trụ cột bổ sung cho nhau. **Trụ cột thứ nhất** là bộ kiểm thử "
              "đơn vị và tích hợp gắn liền với từng crate, chạy trong cùng một tiến trình với mã được "
              "kiểm và có quyền truy cập cả các hàm nội bộ."),
        ("p", "**Trụ cột thứ hai** là các cổng chất lượng trong quy trình tích hợp liên tục, chạy trên "
              "ma trận ba hệ điều hành. Ngoài việc chạy kiểm thử, các cổng này còn cưỡng chế định dạng "
              "mã, phân tích tĩnh với mọi cảnh báo là lỗi, và kiểm tra chuỗi cung ứng."),
        ("p", "**Trụ cột thứ ba** là một kiểm thử đối chiếu hợp đồng giữa giao diện và lõi. Kiểm thử này "
              "phân tích chính khối mã ánh xạ mã lỗi trong tệp JavaScript của giao diện và đối chiếu với "
              "danh sách mã lỗi khai báo trong lõi Rust, khẳng định hai bên khớp nhau một-đối-một. Đây "
              "là một trụ cột nhỏ nhưng có giá trị đặc thù: nó biến một hợp đồng vốn chỉ tồn tại trên "
              "giấy thành một hợp đồng được công cụ cưỡng chế."),
        ("p", "**Trụ cột thứ tư** là các chiến dịch kiểm chứng có tài liệu hóa, trong đó từng giả thuyết "
              "rủi ro được cố gắng tái hiện hoặc bác bỏ trên đúng đường mã sản phẩm, với nhị phân thật. "
              "Đây là trụ cột phát hiện được nhiều khiếm khuyết nghiêm trọng nhất."),

        ("h3", "1.3. Hạn chế của phương pháp đánh giá"),
        ("p", "Để người đọc đánh giá đúng giá trị của các kết quả trình bày ở các mục sau, cần nêu rõ "
              "bốn hạn chế về phương pháp."),
        ("b", "Các phép đo hiệu năng được thực hiện trên **một cấu hình duy nhất**, với **một lần đo cho "
              "mỗi kịch bản**. Chúng đủ để rút ra kết luận về bậc độ lớn và về cơ chế, nhưng không đủ để "
              "xây dựng đường cong hiệu năng hay so sánh giữa các nền tảng."),
        ("b", "Giao diện người dùng **không có kiểm thử tự động ở mức chạy thật**. Trụ cột thứ ba chỉ "
              "đối chiếu bảng mã lỗi; không có kiểm thử nào mở ứng dụng và mô phỏng thao tác người dùng."),
        ("b", "Các kiểm thử đầu-cuối với nhị phân age **bị điều kiện hóa bởi biến môi trường**: trên một "
              "máy không cài age, chúng tự bỏ qua thay vì thất bại. Điều này thuận tiện cho phát triển "
              "nhưng cũng có nghĩa là một bản chạy kiểm thử cục bộ có thể không bao phủ đường mã đó."),
        ("b", "Hệ thống **chưa được kiểm định độc lập bởi bên thứ ba**. Toàn bộ đánh giá trong báo cáo "
              "này là đánh giá nội bộ, và không thay thế được một cuộc kiểm toán mật mã chuyên nghiệp."),
    ]

    # ======================================= 2. Kiem thu chuc nang
    B += [
        ("h2", "2. Kiểm thử chức năng hệ thống"),

        ("h3", "2.1. Quy mô và phân bố của bộ kiểm thử"),
        ("p", "Phép quét trực tiếp cây mã nguồn cho kết quả **253 hàm kiểm thử** trong workspace, trong "
              "đó 249 hàm chạy và đạt, còn 4 hàm được đánh dấu bỏ qua vì phụ thuộc vào biến môi trường "
              "chỉ đường dẫn nhị phân ngoài. Crate giao diện, vốn nằm ngoài workspace, có thêm một hàm "
              "kiểm thử đối chiếu hợp đồng."),
        ("fig", "Hinh-4-01-phan-bo-kiem-thu",
         "Hình 4.1. Phân bố hàm kiểm thử theo crate"),
        ("p", "Phân bố trong Hình 4.1 cho thấy ba crate chiếm phần lớn: mô-đun giấu tin với 74 hàm, "
              "mô-đun dịch vụ mức tệp với 46 hàm và lớp bề mặt lệnh với 39 hàm. Sự tập trung này phản "
              "ánh đúng nơi có nhiều nhánh xử lý và nhiều điều kiện biên nhất."),
        ("p", "Một chi tiết về tính chính xác của số liệu cần được ghi nhận. Tài liệu kiểm chứng của dự "
              "án ở một thời điểm trước đó ghi nhận 127 kiểm thử đạt cho một commit cụ thể. Con số 253 "
              "và con số 127 **không mâu thuẫn**: chúng thuộc hai thời điểm khác nhau, và phần chênh "
              "lệch tương ứng đúng với các mô-đun được bổ sung sau. Dự án đã ghi nhận sự lệch pha này "
              "trong một bảng đối chiếu tài liệu và mã nguồn, cùng khuyến nghị rằng mọi con số kiểm thử "
              "khi được trích dẫn phải kèm ngày đo hoặc mã commit. Báo cáo này tuân thủ khuyến nghị đó."),
        ("tbl", "Bảng 4.2. Phân bố và trọng tâm kiểm thử theo crate",
         ["Crate", "Số hàm", "Trọng tâm kiểm thử"],
         [
             ["`sv-stego`", "74", "Sóng mang không mất mát và JPEG, số học dung lượng, vòng lặp khung SVSTEG, bảng bộ dò, tính chống dò oracle của đường trích xuất, giới hạn giải nén"],
             ["`sv-platform`", "46", "Niêm phong và mở artifact, năm cổng của lược đồ chia sẻ, tổ hợp phép kiểm toàn vẹn, trần kích thước, ánh xạ lỗi"],
             ["`sv-app` (src-tauri)", "39", "Bề mặt lệnh, tính chống dò oracle, rào kích thước, từ chối ghi đè, khóa ghi theo két"],
             ["`sv-core`", "22", "Vòng lặp CBOR của header, phân cấp khóa, khung container và gốc ràng buộc, tính chống dò oracle của bảng lỗi"],
             ["`sv-crypto`", "20", "Hành vi từng bộ điều hợp, vectơ thử nghiệm BLAKE3, sàn tham số Argon2id, ngưỡng Shamir, các đường giả mạo chữ ký"],
             ["`sv-watermark`", "11", "Nhúng và kiểm tra, định vị sửa đổi một điểm ảnh, khóa sai, từ chối ảnh JPEG"],
             ["`sv-meta`", "10", "Ghim băm, phân tích đầu ra JSON, so sánh, tính trung thực của thao tác xóa, ánh xạ lỗi"],
             ["`sv-qr`", "8", "Vòng lặp mã hóa và giải mã, nhiều mã QR trong một ảnh, hỏng theo hướng an toàn khi không có mã"],
             ["`sv-age`", "6", "Khớp và lệch băm ghim, kết liễu tiến trình khi hết giờ, dọn tệp tạm danh tính, đầu-cuối với age thật"],
             ["`sv-crypto-traits`", "6", "Che nội dung khi in nhật ký, không tuần tự hóa được, vòng lặp định danh thuật toán"],
             ["`sv-types`", "4", "Vòng lặp DTO, tính đầy đủ của danh sách mã lỗi"],
             ["`sv-sys-sss`", "4", "Vòng lặp FFI của lược đồ Shamir"],
             ["`sv-sys-sodium`", "3", "Ràng buộc FFI tới libsodium"],
             ["**Tổng workspace**", "**253**", "249 đạt, 4 bỏ qua do phụ thuộc biến môi trường"],
             ["`desktop` (riêng)", "1", "Đối chiếu bảng thông điệp giao diện với danh sách mã lỗi của lõi"],
         ], [3.6, 1.6, 11.0], 10),

        ("h3", "2.2. Kết quả kiểm thử chức năng theo mô-đun"),
        ("p", "Bảng 4.3 tổng hợp các trường hợp kiểm thử chức năng tiêu biểu, được rút ra từ chính các "
              "hàm kiểm thử có trong mã nguồn. Cột kết quả phản ánh trạng thái của bộ kiểm thử tại thời "
              "điểm đo."),
        ("tbl", "Bảng 4.3. Kết quả kiểm thử các chức năng chính",
         ["Mã", "Chức năng", "Điều kiện / dữ liệu thử", "Kết quả mong đợi", "Kết quả", "Đánh giá"],
         [
             ["KT-01", "Vòng đời két đầy đủ", "Tạo két, mở khóa, thêm một tệp 15 byte, liệt kê, trích xuất",
              "Tệp trích xuất trùng khớp bit với tệp gốc", "Đúng như mong đợi", "Đạt"],
             ["KT-02", "Mở khóa bằng mật khẩu sai", "Két hợp lệ, mật khẩu khác mật khẩu tạo",
              "Trả về mã chứng thực thất bại", "SV-UNAUTHORIZED", "Đạt"],
             ["KT-03", "Đổi mật khẩu", "Đổi rồi mở lại bằng mật khẩu mới và mật khẩu cũ",
              "Mật khẩu mới mở được, mật khẩu cũ bị từ chối", "Đúng như mong đợi", "Đạt"],
             ["KT-04", "Chia và khôi phục khóa chủ", "Chia 5 mảnh ngưỡng 3, khôi phục bằng 3 mảnh bất kỳ",
              "Tạo được phiên mới không cần mật khẩu", "Đúng như mong đợi", "Đạt"],
             ["KT-05", "Khôi phục thiếu mảnh", "Cung cấp 2 mảnh cho lược đồ ngưỡng 3",
              "Mã lỗi riêng kèm số hiện có và số cần", "SV-INSUFFICIENT-SHARES {2, 3}", "Đạt"],
             ["KT-06", "Khôi phục bằng mảnh của két khác", "Mảnh hợp lệ nhưng khác định danh két",
              "Từ chối với thông báo rõ ràng", "SV-INVALID-INPUT", "Đạt"],
             ["KT-07", "Kiểm tra toàn vẹn két nguyên vẹn", "Két vừa ghi",
              "Kết luận đạt cho cả băm và chữ ký", "Đúng như mong đợi", "Đạt"],
             ["KT-08", "Kiểm tra két bị sửa một byte", "Lật một byte trong vùng tải trọng",
              "Phát hiện và trả về mã tệp hỏng", "SV-CORRUPTED", "Đạt"],
             ["KT-09", "Mã hóa và giải mã tệp độc lập", "Tệp có byte không, mật khẩu đúng",
              "Khôi phục nguyên vẹn, tệp bắt đầu bằng chuỗi nhận dạng", "Đúng như mong đợi", "Đạt"],
             ["KT-10", "Giải mã tệp độc lập sai mật khẩu", "Cùng tệp, mật khẩu khác",
              "Trả về mã chứng thực thất bại", "SV-UNAUTHORIZED", "Đạt"],
             ["KT-11", "Ký và kiểm chữ ký tệp", "Tạo cặp khóa, ký, kiểm bằng khóa công khai",
              "Chữ ký hợp lệ; sửa tệp thì không hợp lệ", "Đúng như mong đợi", "Đạt"],
             ["KT-12", "Chia và khôi phục bí mật độc lập", "Chia chuỗi thành 5 mảnh ngưỡng 3",
              "Khôi phục đúng nội dung; mảnh trùng bị từ chối", "Đúng như mong đợi", "Đạt"],
             ["KT-13", "Chia và khôi phục tệp", "Chia một tệp, khôi phục lại",
              "Tệp khôi phục mang đúng tên gốc, nội dung trùng khớp", "Đúng như mong đợi", "Đạt"],
             ["KT-14", "Xuất và đọc mã QR", "Chuỗi mảnh 124 ký tự",
              "Ảnh QR đọc lại cho đúng chuỗi ban đầu", "Đúng như mong đợi", "Đạt"],
             ["KT-15", "Giấu và hiện dữ liệu trong ảnh", "Ảnh PNG, tải trọng nhỏ, mật khẩu đúng",
              "Trích xuất đúng tải trọng; ảnh vẫn mở được bình thường", "Đúng như mong đợi", "Đạt"],
             ["KT-16", "Giấu tin quá dung lượng", "Tải trọng lớn hơn dung lượng ảnh bìa",
              "Từ chối trước khi chạy hàm dẫn xuất khóa", "Mã dung lượng vượt quá", "Đạt"],
             ["KT-17", "Trích xuất từ ảnh sạch", "Ảnh không mang dữ liệu ẩn",
              "Trả về đúng mã hợp nhất, không phân biệt được với sai mật khẩu", "SV-UNAUTHORIZED", "Đạt"],
             ["KT-18", "Dò dữ liệu nối thêm vào ảnh", "Ảnh PNG có tệp nén nối phía sau",
              "Mức nghi ngờ cao", "High", "Đạt"],
             ["KT-19", "Nhúng và kiểm thủy vân", "Ảnh PNG, khóa đúng, không sửa",
              "Kết luận nguyên vẹn", "Intact", "Đạt"],
             ["KT-20", "Kiểm thủy vân sau khi sửa một điểm ảnh", "Đổi một điểm ảnh duy nhất",
              "Kết luận bị sửa, kèm định vị khối hỏng", "Tampered + danh sách khối", "Đạt"],
             ["KT-21", "Kiểm thủy vân bằng khóa sai", "Ảnh đã đánh dấu, khóa khác",
              "Kết luận không có dấu", "NotWatermarked", "Đạt"],
             ["KT-22", "Từ chối ghi đè tệp đích", "Trích xuất ra một đường dẫn đã có tệp",
              "Từ chối, tệp cũ được giữ nguyên", "SV-OUTPUT-EXISTS", "Đạt"],
             ["KT-23", "Từ chối tệp quá lớn", "Tệp nguồn vượt trần hai gigabyte",
              "Từ chối trước khi đọc, két không đổi", "SV-TOO-LARGE", "Đạt"],
             ["KT-24", "Mô-đun Phân tích khi thiếu nhị phân", "Không có ExifTool trong bản dựng",
              "Mọi lệnh trả lỗi rõ ràng, giao diện vô hiệu hóa nút", "Tắt an toàn", "Đạt"],
         ], [1.4, 3.2, 4.0, 3.6, 2.4, 1.6], 9.5),
        ("p", "Cần nêu rõ một hạn chế trong cách đọc bảng trên: các trường hợp KT-01 đến KT-08 chạy trên "
              "**bộ mã hóa tải trọng giả lập** trong bộ kiểm thử của workspace. Chúng chứng minh tính "
              "đúng đắn của toàn bộ chuỗi đóng gói, mã hóa, lưu trữ, giải mã cấu trúc và giải nén, nhưng "
              "chúng **không** chứng minh gì về hành vi của tiến trình con age. Bằng chứng cho đường mã "
              "đó đến từ kiểm thử đầu-cuối chạy trong môi trường tích hợp liên tục và từ chiến dịch kiểm "
              "chứng ở mục 5."),

        ("h3", "2.3. Các cổng kiểm tra trong quy trình tích hợp liên tục"),
        ("fig", "Hinh-4-02-cong-ci", "Hình 4.2. Năm nhóm việc trong quy trình tích hợp liên tục"),
        ("p", "Quy trình gồm năm nhóm việc; tính cả nhân bản theo ma trận hệ điều hành thì mỗi lần đẩy "
              "mã kích hoạt chín lượt chạy. Tài liệu kiểm chứng của dự án ghi nhận một lần chạy **xanh "
              "toàn bộ** trên một commit cụ thể."),
        ("p", "Ba quan sát từ lần chạy đó đáng được ghi nhận. **Thứ nhất**, kiểm thử đầu-cuối với age "
              "thật đã chạy và đạt trên máy Windows, qua đó đóng lại bằng thực nghiệm một giả thuyết "
              "rủi ro trước đó chỉ là suy đoán. **Thứ hai**, có chênh lệch một kiểm thử giữa Linux và "
              "Windows; nguyên nhân được xác định là một hàm kiểm thử chỉ biên dịch trên nền Unix, "
              "không phải một thất bại. **Thứ ba**, lần chạy đầu tiên đã thất bại ở năm điểm, và cả năm "
              "đều là vấn đề khả chuyển: thiếu tệp khóa phiên bản cho crate giao diện, chưa cố định "
              "phiên bản trình biên dịch tối thiểu, xung đột tên ký hiệu của hàm sinh ngẫu nhiên, một "
              "cấu trúc mảng độ dài động không được trình biên dịch của Microsoft chấp nhận trong tệp C "
              "được nhúng, và thiếu chuỗi công cụ để cài age trên macOS."),
        ("p", "Điểm quan trọng nhất về mặt an toàn: cả năm sửa chữa đều là sửa chữa khả chuyển, **không "
              "có thay đổi thuật toán nào**. Đặc biệt, việc sửa cấu trúc mảng trong tệp C được nhúng "
              "được xác nhận là bảo toàn hành vi. Đây là một điểm cần cẩn trọng: sửa mã C của một thư "
              "viện mật mã đã được kiểm chứng là thao tác rủi ro, và việc dự án ghi nhận rõ tính bảo "
              "toàn hành vi của thay đổi là một thực hành tốt."),
    ]

    # ================================ 3. Kiem thu thuoc tinh an toan
    B += [
        ("h2", "3. Kiểm thử và thẩm định các thuộc tính an toàn"),
        ("p", "Khác với kiểm thử chức năng vốn trả lời câu hỏi “hệ thống có làm đúng việc không”, phần "
              "này trả lời câu hỏi “hệ thống có giữ được các thuộc tính an toàn mà nó tuyên bố không”. "
              "Mỗi thuộc tính được trình bày kèm cơ chế bảo đảm và bằng chứng kiểm thử tương ứng."),

        ("h3", "3.1. Tính chống dò kênh lỗi"),
        ("p", "Thuộc tính này được kiểm chứng ở ba tầng độc lập. Ở tầng két, một hàm kiểm thử khẳng định "
              "rằng thất bại chứng thực — dù xuất phát từ mật khẩu sai hay mảnh khôi phục sai — đều "
              "chiếu về đúng một mã, trong khi mười một mã còn lại vẫn giữ được tính phân biệt. Hàm này "
              "còn kiểm tra một chi tiết tinh tế: khi một lỗi vào-ra chứa đường dẫn tệp trong thông điệp "
              "gốc, mã lỗi công khai **không được chứa lại đường dẫn đó**; kiểm thử khẳng định trực tiếp "
              "rằng chuỗi kết quả không chứa phần nhạy cảm của đường dẫn."),
        ("p", "Ở tầng giấu tin, một nhóm kiểm thử khẳng định rằng cả bốn tình huống thất bại — ảnh sạch, "
              "khung dữ liệu hỏng, mật khẩu sai, sóng mang bị sửa — đều cho ra cùng một mã. Đây là dạng "
              "chống dò oracle mạnh nhất trong hệ thống, vì nó khiến kẻ tấn công không xác định được cả "
              "sự tồn tại của dữ liệu ẩn."),
        ("p", "Ở tầng giao diện, kiểm thử đối chiếu hợp đồng bảo đảm rằng bảng thông điệp của giao diện "
              "khớp một-đối-một với danh sách mã lỗi của lõi. Ý nghĩa an toàn của kiểm thử này không "
              "hiển nhiên nhưng thực sự tồn tại: nếu giao diện nhận một mã lỗi mà nó không có bản dịch, "
              "nó có thể hiển thị chuỗi mã thô, và trong một số trường hợp việc hiển thị khác biệt giữa "
              "các mã có thể vô tình tái tạo lại chính oracle mà lõi đã cẩn thận loại bỏ."),

        ("h3", "3.2. Tính toàn vẹn của container và khả năng chống ghép tệp"),
        ("p", "Nhóm kiểm thử của mô-đun container bao phủ bốn đường tấn công. Đường thứ nhất là **sửa "
              "tải trọng**: lật một byte trong vùng tải trọng làm gốc ràng buộc thay đổi và phép kiểm "
              "chữ ký thất bại. Đường thứ hai là **sửa header**. Đường thứ ba là **sửa chính chữ ký**."),
        ("p", "Đường thứ tư là quan trọng nhất và cũng đặc thù nhất: **ghép header của tệp này với tải "
              "trọng của tệp khác**. Một hàm kiểm thử riêng dựng hai container hợp lệ từ cùng một khóa "
              "ký rồi ghép chéo chúng, và khẳng định rằng kết quả bị từ chối. Đây chính là bằng chứng "
              "cho hiệu quả của cơ chế gốc ràng buộc: nếu chữ ký chỉ ký lên header, phép ghép này sẽ "
              "thành công và kẻ tấn công có thể thay toàn bộ nội dung két mà vẫn giữ chữ ký hợp lệ."),
        ("p", "Một nhóm kiểm thử thứ hai bao phủ sự phân biệt giữa toàn vẹn và xuất xứ: khi kiểm bằng "
              "khóa công khai nằm trong tệp, kết quả được đánh dấu là **chưa xác thực xuất xứ**; chỉ khi "
              "phía gọi cung cấp một khóa công khai bên ngoài và khóa trong tệp trùng khớp, kết quả mới "
              "được đánh dấu là đã xác thực xuất xứ. Một két tự ký **không bao giờ** được báo cáo là đã "
              "chứng minh được nguồn gốc."),

        ("h3", "3.3. Ràng buộc ngữ cảnh của khóa bọc"),
        ("p", "Hai thuộc tính chống cấy ghép và chống nhầm lẫn trường được kiểm chứng bằng cách chạy qua "
              "toàn bộ chuỗi thật: dẫn xuất khóa bọc, niêm phong một bí mật, rồi thử mở bằng khóa dẫn "
              "xuất từ một ngữ cảnh khác. Cả hai thử nghiệm đều thất bại đúng như dự kiến."),
        ("p", "Bên cạnh đó, chuỗi ngữ cảnh được **đóng băng bằng kiểm thử**: hàm kiểm thử so sánh chuỗi "
              "sinh ra với một hằng số văn bản viết cứng. Giá trị của biện pháp này rất cao so với chi "
              "phí: một thay đổi vô ý trong văn phạm sẽ làm mọi két đã tồn tại trở nên không mở được, và "
              "đây là loại lỗi mà không có cơ chế nào khác trong chuỗi công cụ phát hiện được."),

        ("h3", "3.4. Vệ sinh bí mật"),
        ("p", "Nhóm kiểm thử ở tầng hợp đồng khẳng định ba tính chất của các kiểu bí mật: nội dung bị "
              "che khi in ra nhật ký gỡ lỗi và giá trị thật không xuất hiện trong chuỗi kết quả; kiểu "
              "byte bí mật có độ dài đúng bằng dữ liệu và không có dung lượng dư; và các kiểu bí mật "
              "không tuần tự hóa được — tính chất này được cưỡng chế bởi trình biên dịch chứ không cần "
              "kiểm thử tại thời điểm chạy."),
        ("p", "Ở tầng điều khiển tiến trình con, một hàm kiểm thử xác nhận rằng tệp tạm chứa danh tính "
              "được xóa khi cấu trúc quản lý nó bị hủy. Cần nhắc lại giới hạn đã ghi nhận: việc ghi đè "
              "trước khi xóa liên kết là nỗ lực tối đa chứ không phải bảo đảm, vì các hệ thống tệp "
              "sao-chép-khi-ghi và các ổ đĩa thể rắn có thể không ghi đè tại chỗ."),
        ("p", "Cần nói rõ điều mà bộ kiểm thử **không** chứng minh được: không có kiểm thử nào quét bộ "
              "nhớ tiến trình sau khi khóa bị hủy để xác nhận rằng vùng nhớ thực sự đã bị ghi đè. Bằng "
              "chứng ở đây là bằng chứng **cấu trúc** — các kiểu dữ liệu được khai báo với thuộc tính "
              "tự xóa — chứ không phải bằng chứng thực nghiệm. Đây là sự phân biệt giữa “thuộc tính "
              "được thiết kế và cưỡng chế bởi hệ thống kiểu” và “thuộc tính được đo đạc”, và báo cáo "
              "không gộp hai loại bằng chứng này làm một."),

        ("h3", "3.5. Tính bền vững của bộ phân tích cú pháp"),
        ("p", "Phép quét kiểu fuzz có tính tất định đã mô tả ở Chương 3 tạo ra bằng chứng cho hai mệnh "
              "đề. Mệnh đề thứ nhất là **không gây hoảng loạn**: với mọi độ dài cắt cụt, với bốn nghìn "
              "phép lật một byte và với các bộ đệm ngẫu nhiên, không lời gọi nào làm chương trình dừng "
              "đột ngột. Mệnh đề thứ hai mạnh hơn: một container đã bị đột biến **không bao giờ được "
              "xác thực thành công với một tải trọng khác tải trọng gốc**."),
        ("p", "Cần đánh giá đúng phạm vi của bằng chứng này. Phép quét tất định bao phủ tốt các đột biến "
              "cục bộ nhưng không phải là fuzz có dẫn hướng theo độ phủ; nó không tìm ra các đầu vào cần "
              "một tổ hợp nhiều thay đổi phối hợp. Dự án ghi nhận rõ rằng một mục tiêu fuzz có dẫn hướng "
              "là bước tiếp theo **chưa được nối vào quy trình tích hợp liên tục**."),

        ("h3", "3.6. Tính chất ngưỡng của lược đồ chia sẻ bí mật"),
        ("p", "Ba kiểm thử bao phủ nhóm thuộc tính này. Kiểm thử thứ nhất xác nhận vòng lặp chia — gộp "
              "hoạt động với mọi tập con đủ ngưỡng. Kiểm thử thứ hai, quan trọng hơn về mặt nhận thức, "
              "xác nhận rằng **dưới ngưỡng thì cho ra khóa sai chứ không báo lỗi**. Kiểm thử thứ ba xác "
              "nhận rằng các tham số vô lý bị từ chối."),
        ("p", "Ở tầng lược đồ chia sẻ độc lập, các cổng bổ sung cũng được kiểm chứng: mảnh trùng hoành "
              "độ bị từ chối, mảnh có hoành độ bằng không bị từ chối, mảnh thuộc lần chia khác bị từ "
              "chối, và tệp tải trọng không khớp bị từ chối. Việc kiểm thử phủ đầy đủ các cạm bẫy đã "
              "biết của lược đồ Shamir là một điểm mạnh đáng ghi nhận, vì đây chính là những chỗ mà "
              "nhiều hiện thực khác mắc lỗi."),

        ("h3", "3.7. Tính đúng đắn của thang phán quyết thủy vân"),
        ("p", "Nhóm kiểm thử của mô-đun thủy vân bao phủ ba mức phán quyết cùng hai trường hợp biên. "
              "Trường hợp biên thứ nhất là **định vị sửa đổi cực nhỏ**: đổi đúng một điểm ảnh vẫn được "
              "phát hiện và khối chứa điểm ảnh đó được chỉ ra. Trường hợp biên thứ hai kiểm chứng chính "
              "cơ chế dấu hiệu hiện diện: một ảnh bị sửa trên diện rộng phải cho kết luận “bị sửa” chứ "
              "**không được** cho kết luận “không có dấu”. Trường hợp thứ hai này chính là khiếm khuyết "
              "mà thiết kế ban đầu mắc phải và đã được sửa bằng cơ chế dấu hiệu hiện diện."),
        ("tbl", "Bảng 4.4. Đối chiếu thuộc tính an toàn với cơ chế và bằng chứng",
         ["Thuộc tính an toàn", "Cơ chế bảo đảm", "Loại bằng chứng"],
         [
             ["Bí mật khi lưu trữ", "age cho tải trọng; Argon2id + secretbox cho khóa và tệp độc lập",
              "Kiểm thử vòng lặp; **giả thiết an toàn của nguyên thủy**, không phải chứng minh"],
             ["Bí mật của siêu dữ liệu nội dung", "Danh mục tệp nằm trong vùng đã mã hóa",
              "Bằng chứng cấu trúc từ định dạng + kiểm thử vòng lặp đóng gói"],
             ["Toàn vẹn và chống sửa đổi", "Chữ ký Ed25519 trên gốc ràng buộc",
              "Kiểm thử bốn đường tấn công, gồm cả ghép chéo hai tệp"],
             ["Chống cấy ghép và nhầm lẫn trường", "Ràng buộc ngữ cảnh trong dẫn xuất khóa bọc",
              "Kiểm thử chạy qua toàn bộ chuỗi thật"],
             ["Chống dò kênh lỗi", "Hợp nhất mã lỗi chứng thực; cổng chữ ký chạy trước cổng mật khẩu",
              "Kiểm thử ở ba tầng độc lập"],
             ["Bền vững trước đầu vào độc hại", "Kiểm biên toàn diện; trần header; trần tham số trước xác thực",
              "Phép quét đột biến tất định (không phải fuzz có dẫn hướng)"],
             ["Tính chất ngưỡng", "Lược đồ Shamir + cổng xác thực AEAD phía sau",
              "Kiểm thử; **an toàn theo lý thuyết thông tin** là tính chất của lược đồ"],
             ["Vệ sinh bí mật trong bộ nhớ", "Kiểu dữ liệu tự xóa, không tuần tự hóa được",
              "Bằng chứng **cấu trúc** cưỡng chế bởi trình biên dịch, KHÔNG phải bằng chứng đo đạc"],
             ["Toàn vẹn chuỗi cung ứng nhị phân", "Ghim băm, kiểm kiến trúc, đóng bề mặt phân giải",
              "Kiểm thử khớp và lệch băm; **còn khoảng trống TOCTOU**"],
             ["An toàn dữ liệu người dùng", "Ghi nguyên tử; từ chối ghi đè; khóa ghi theo két",
              "Kiểm thử hồi quy được bổ sung sau chiến dịch kiểm chứng"],
         ], [4.2, 5.4, 6.6], 10),
        ("p", "Cột cuối của bảng trên được thiết kế để tránh một sai lầm phổ biến trong các báo cáo an "
              "toàn: gộp lẫn bốn loại phát biểu vốn có giá trị chứng minh rất khác nhau. **Mục tiêu "
              "thiết kế** là điều hệ thống muốn đạt. **Cơ chế đã hiện thực** là mã thật đang chạy. "
              "**Thuộc tính đã được kiểm thử** là điều có hàm kiểm thử chứng minh. **Thuộc tính được "
              "chứng minh hình thức** thì hệ thống này **không có** — không có phần nào được đặc tả và "
              "chứng minh bằng phương pháp hình thức. Và cuối cùng, **thuộc tính được giả định** là "
              "những gì kế thừa từ giả thiết an toàn của các nguyên thủy, chẳng hạn tính khó của bài "
              "toán logarit rời rạc trên đường cong elliptic."),
    ]

    # ============================== 4. Hieu nang
    B += [
        ("h2", "4. Đánh giá hiệu năng và mức sử dụng tài nguyên"),
        ("note", "Toàn bộ số liệu trong mục này được lấy từ tài liệu kiểm chứng của dự án, đo trên đúng "
                 "đường mã sản phẩm với nhị phân age thật. Không có con số nào được ước lượng hay suy "
                 "diễn; các giá trị mang tính ngoại suy đều được ghi nhãn rõ ràng."),

        ("h3", "4.1. Thông lượng mã hóa và giải mã tải trọng"),
        ("fig", "Hinh-4-03-thong-luong-age",
         "Hình 4.3. Thông lượng mã hóa và giải mã tải trọng qua tiến trình con age"),
        ("p", "Phép đo trên một tệp 512 MiB cho thời gian mã hóa 1,35 giây và thời gian giải mã 1,69 "
              "giây, tương ứng thông lượng khoảng 379 MiB/s và 303 MiB/s. Các con số này bao gồm toàn "
              "bộ chi phí của mô hình tiến trình con: sinh tiến trình, truyền dữ liệu qua ống dẫn hai "
              "chiều, và đồng bộ giữa ba luồng."),
        ("p", "Hệ quả trực tiếp của các con số này là một đánh giá lại về vai trò của hạn giờ tường. Với "
              "thông lượng đo được, hạn giờ 120 giây chỉ bị chạm ở khoảng 44 GiB khi mã hóa và 35 GiB "
              "khi giải mã trên ổ đĩa cục bộ nhanh. Nói cách khác, **hạn giờ không phải là chế độ hỏng "
              "thường gặp** mà là một biện pháp bảo vệ trước tình huống bất thường — nhị phân bị treo, "
              "ổ đĩa mạng rất chậm, hoặc máy đang chịu tải nặng."),
        ("p", "Đây là một ví dụ về giá trị của việc đo đạc: giả thuyết ban đầu của dự án cho rằng hạn "
              "giờ sẽ là nguyên nhân hỏng chính khi xử lý tệp lớn. Phép đo cho thấy giả thuyết đó **sai "
              "về cơ chế**, và nguyên nhân hỏng thực sự nằm ở chỗ khác, như mục tiếp theo trình bày."),
        ("tbl", "Bảng 4.5. Kết quả đo thông lượng",
         ["Thao tác", "Kích thước tải trọng", "Thời gian", "Thông lượng", "Ngưỡng chạm hạn giờ 120 s (ngoại suy)"],
         [
             ["Mã hóa (age -e)", "512 MiB", "1,35 s", "≈ 379 MiB/s", "≈ 44 GiB"],
             ["Giải mã (age -d)", "512 MiB", "1,69 s", "≈ 303 MiB/s", "≈ 35 GiB"],
         ], [3.4, 3.0, 2.2, 2.8, 4.8], 10.5),

        ("h3", "4.2. Mức tiêu thụ bộ nhớ và nguyên nhân"),
        ("fig", "Hinh-4-04-dinh-bo-nho",
         "Hình 4.4. Đỉnh bộ nhớ thường trú khi thêm một tệp vào két"),
        ("p", "Phép đo đỉnh bộ nhớ khi thêm một tệp 1024 MiB cho kết quả 2 852 782 080 byte, tức khoảng "
              "2,66 GiB — xấp xỉ **2,7 lần** kích thước tệp. Đây là kết quả đáng chú ý nhất trong toàn "
              "bộ phần đánh giá hiệu năng, vì nó xác định giới hạn thực tế của hệ thống."),
        ("p", "Nguyên nhân được truy vết chính xác tới bốn bản sao cùng tồn tại trong bộ nhớ tại thời "
              "điểm cao nhất: bản đọc tệp nguồn, bản sao của nội dung trong kho lưu trữ đã đóng gói, "
              "vùng đệm dữ liệu đưa vào tiến trình con, và vùng đệm nhận dữ liệu ra từ tiến trình con. "
              "Tất cả đều là vectơ byte nằm hoàn toàn trong bộ nhớ."),
        ("p", "Cần nêu rõ một tình huống làm vấn đề nghiêm trọng hơn: khi thêm tệp vào một két **đã "
              "chứa sẵn nhiều dữ liệu**, hệ thống phải giải mã và giữ toàn bộ tải trọng cũ trong bộ nhớ "
              "trước khi đóng gói lại. Nghĩa là hệ số 2,7 lần áp lên **tổng kích thước két** chứ không "
              "chỉ tệp mới. Đây là hệ quả trực tiếp của mô hình một khối tải trọng duy nhất."),
        ("p", "Cần đọc Hình 4.4 với sự cẩn trọng về phương pháp: **chỉ cột 1024 MiB là số đo thật**. Bốn "
              "cột còn lại là ngoại suy tuyến tính từ hệ số đã đo, được đưa vào để minh họa vì sao trần "
              "hai gigabyte là cần thiết, và chúng được ghi nhãn rõ ràng là ngoại suy."),
        ("p", "Biện pháp hiện tại là một **rào chắn chứ không phải một cách sửa gốc**: hệ thống kiểm tra "
              "kích thước tệp nguồn trước khi đọc và từ chối nếu vượt trần, với một mã lỗi rõ ràng. "
              "Người dùng nhận được thông báo “tệp quá lớn” thay vì ứng dụng bị hệ điều hành chấm dứt vì "
              "cạn bộ nhớ, và két giữ nguyên trạng thái. Cách sửa gốc là chuyển sang mô hình truyền "
              "dòng, và dự án ghi nhận đây là hạng mục **chưa được thực hiện**."),

        ("h3", "4.3. Chi phí của hàm dẫn xuất khóa"),
        ("p", "Tham số mặc định 256 MiB bộ nhớ với ba vòng lặp là một lựa chọn cao hơn đáng kể so với "
              "sàn khuyến nghị của OWASP — cao hơn khoảng mười ba lần về bộ nhớ. Chi phí này được trả "
              "một lần cho mỗi thao tác cần tới khóa chủ: mở khóa két, đổi mật khẩu, mã hóa hoặc giải mã "
              "một tệp độc lập, giấu hoặc hiện dữ liệu trong ảnh, và nhúng hoặc kiểm thủy vân."),
        ("p", "Báo cáo không đưa ra con số thời gian cụ thể cho phép dẫn xuất khóa vì tài liệu kiểm "
              "chứng của dự án không ghi nhận phép đo này. Đây là một khoảng trống trong dữ liệu thực "
              "nghiệm cần được bổ sung: thời gian dẫn xuất khóa là yếu tố ảnh hưởng trực tiếp và rõ rệt "
              "nhất tới cảm nhận của người dùng, bởi vì nó xảy ra ở **mọi** thao tác mở khóa, kể cả trên "
              "một két rỗng."),
        ("p", "Cơ chế hiệu chỉnh theo phần cứng đã trình bày ở Chương 3 chính là câu trả lời có sẵn cho "
              "vấn đề này: thay vì cố định tham số, hệ thống có thể đo trên máy thật và chọn mức chi phí "
              "đạt một mốc thời gian mục tiêu. Nhưng như đã ghi nhận, cơ chế này **đã có mã nhưng chưa "
              "được nối vào đường tạo két**."),

        ("h3", "4.4. Nhận xét chung về hiệu năng"),
        ("p", "Có thể rút ra ba nhận xét. **Thứ nhất**, hiệu năng thông lượng ở mức chấp nhận được cho "
              "một ứng dụng máy tính để bàn; ba trăm tới bốn trăm mebibyte mỗi giây là đủ để thao tác "
              "trên tệp cỡ trăm mebibyte diễn ra trong thời gian người dùng còn kiên nhẫn chờ."),
        ("p", "**Thứ hai**, ràng buộc thực sự của hệ thống là **bộ nhớ chứ không phải thời gian**. Đây "
              "là kết luận trái với giả thuyết ban đầu và chỉ có được nhờ đo đạc."),
        ("p", "**Thứ ba**, mô hình một khối tải trọng duy nhất là nguồn gốc chung của cả hai hạn chế về "
              "hiệu năng: nó buộc phải mã hóa lại toàn bộ mỗi lần thay đổi, và nó buộc phải giữ toàn bộ "
              "trong bộ nhớ. Đây chính là cái giá phải trả cho thuộc tính bí mật của siêu dữ liệu — một "
              "sự đánh đổi có ý thức, nhưng cần được nêu rõ để người đọc tự đánh giá."),
    ]

    # ==================== 5. Chien dich kiem chung gia thuyet rui ro
    B += [
        ("h2", "5. Chiến dịch kiểm chứng các giả thuyết rủi ro"),

        ("h3", "5.1. Phương pháp"),
        ("p", "Đây là phần đánh giá có giá trị nhất trong toàn bộ chương, cả về kết quả lẫn về phương "
              "pháp. Cách làm gồm ba bước. Bước một: đặt ra một danh sách các **giả thuyết rủi ro** — "
              "các phát biểu cụ thể, kiểm chứng được về những gì có thể sai. Bước hai: với mỗi giả "
              "thuyết, thiết kế một thực nghiệm nhằm **tái hiện hoặc bác bỏ** nó. Bước ba: chạy thực "
              "nghiệm trên **đúng đường mã sản phẩm** với nhị phân thật, chứ không phải trên bản giả lập."),
        ("p", "Điểm mấu chốt nằm ở bước ba. Bộ kiểm thử đơn vị của dự án dùng bộ mã hóa tải trọng giả "
              "lập, nên nó không bao giờ chạm tới tiến trình con, hạn giờ, cơ chế đệm trong bộ nhớ, việc "
              "xóa biến môi trường hay tệp tạm chứa danh tính — chính xác là những bề mặt cần kiểm "
              "chứng. Một bộ khai thác riêng được dựng bên ngoài kho mã, tạo trực tiếp lớp dịch vụ két "
              "với bộ mã hóa thật và gọi các thao tác đúng như các hàm lệnh gọi."),
        ("p", "Cần nhấn mạnh một điểm về tính khách quan: trong đợt kiểm chứng, **không có dòng mã sản "
              "phẩm nào bị sửa**. Việc sửa lỗi được thực hiện thành một đợt riêng sau đó, và sau khi sửa "
              "thì toàn bộ thực nghiệm được **chạy lại** để xác nhận. Cách tách bạch này giúp kết quả "
              "không bị thiên lệch bởi mong muốn chứng minh rằng hệ thống ổn."),

        ("h3", "5.2. Kết quả kiểm chứng"),
        ("p", "Bảy giả thuyết được đặt ra. **Sáu giả thuyết được xác nhận là đúng**, trong đó có một "
              "khiếm khuyết ở mức nghiêm trọng dẫn tới mất dữ liệu vĩnh viễn. Một giả thuyết bị bác bỏ "
              "trên nền tảng được thử và về sau được đóng lại bằng bằng chứng trên nền tảng còn lại."),
        ("tbl", "Bảng 4.6. Kết quả kiểm chứng bảy giả thuyết rủi ro",
         ["Mã", "Giả thuyết", "Kết quả", "Bằng chứng thực nghiệm", "Mức độ"],
         [
             ["H1", "Tệp lớn gây hỏng theo cách khó hiểu",
              "Xác nhận, nhưng **sai về cơ chế**",
              "Nguyên nhân là bộ nhớ (đỉnh ≈ 2,7 × kích thước tệp) chứ không phải hạn giờ; một lần hết "
              "giờ cưỡng bức trả về mã lỗi nội bộ vô nghĩa, két giữ nguyên", "Cao"],
             ["H2", "Không có xác nhận lại mật khẩu khi tạo két",
              "Xác nhận",
              "Biểu mẫu tạo két chỉ có một ô mật khẩu, trong khi biểu mẫu đổi mật khẩu lại có hai ô và "
              "có kiểm tra khớp", "**Nghiêm trọng**"],
             ["H3", "Trích xuất âm thầm ghi đè tệp có sẵn",
              "Xác nhận",
              "Đặt sẵn một tệp có nội dung nhận dạng được tại đường dẫn đích; sau khi trích xuất, nội "
              "dung cũ bị thay thế hoàn toàn, không có cảnh báo", "Cao"],
             ["H4", "Việc xóa biến môi trường làm hỏng age trên Windows",
              "**Bác bỏ** trên macOS; sau đó **đóng lại** trên Windows",
              "Thử nghiệm với môi trường rỗng hoàn toàn trên macOS đều thành công; về sau kiểm thử "
              "đầu-cuối chạy xanh trên máy Windows trong môi trường tích hợp liên tục", "Đã đóng"],
             ["H5", "Nhị phân đi kèm bị chặn khi cài mới",
              "Xác nhận trên macOS",
              "Một bản sao nhị phân mang nhãn cách ly, chạy đúng bằng cơ chế mà thư viện chuẩn dùng, bị "
              "chấm dứt với mã thoát 137; công cụ kiểm tra của hệ điều hành báo từ chối", "Cao (phân phối)"],
             ["H6", "Mọi lỗi đều gộp về một mã nội bộ vô nghĩa",
              "Xác nhận",
              "Tạo két trong thư mục chỉ đọc cho ra mã lỗi nội bộ; theo cùng nhánh ánh xạ, lỗi đầy đĩa "
              "và hết giờ cũng cho kết quả giống hệt", "Cao"],
             ["H7", "Ghi đồng thời làm mất dữ liệu",
              "Xác nhận, **tái hiện được 8 trên 8 lần**",
              "Hai lệnh thêm tệp chạy trên hai luồng đối với cùng một két; kết quả cuối chỉ còn một tệp "
              "thay vì hai, lặp lại ở toàn bộ tám lượt thử", "Cao"],
         ], [1.2, 3.6, 3.0, 6.0, 2.4], 9.8),
        ("p", "Giả thuyết H2 xứng đáng được phân tích riêng vì nó minh họa một điểm quan trọng. Đây "
              "không phải là một lỗi mật mã; toàn bộ tầng mật mã hoạt động hoàn hảo. Đây là một khiếm "
              "khuyết ở tầng giao diện: thiếu một ô nhập lại mật khẩu. Nhưng hậu quả thì tuyệt đối — một "
              "lỗi gõ phím duy nhất khi tạo két tạo ra một két **không bao giờ mở được**, và người dùng "
              "thậm chí không thể cắt mảnh khôi phục vì việc đó đòi hỏi phải mở khóa trước. Bài học ở "
              "đây rất rõ: trong một hệ thống mật mã, **an toàn của người dùng và an toàn của thuật "
              "toán là hai vấn đề riêng biệt**, và cái thứ nhất có thể phá hủy giá trị của cái thứ hai."),
        ("p", "Giả thuyết H1 minh họa một điểm khác: giả thuyết ban đầu **đúng về triệu chứng nhưng sai "
              "về nguyên nhân**. Dự đoán là hạn giờ sẽ gây hỏng; thực tế là bộ nhớ. Nếu chỉ dựa vào suy "
              "luận mà không đo, biện pháp khắc phục được chọn có thể đã hoàn toàn nhắm sai đích."),
        ("p", "Giả thuyết H5 minh họa khoảng cách giữa môi trường phát triển và môi trường người dùng. "
              "Trên máy của người phát triển, nhị phân không mang nhãn cách ly nên mọi thứ hoạt động "
              "bình thường; chỉ khi mô phỏng đúng điều kiện của một bản tải về, vấn đề mới lộ ra."),

        ("h3", "5.3. Kết quả sau khi sửa chữa"),
        ("p", "Năm giả thuyết được xác nhận đã được xử lý, và toàn bộ được **chạy lại thực nghiệm** trên "
              "cùng đường mã sản phẩm."),
        ("fig", "Hinh-4-05-trang-thai-gia-thuyet-rui-ro",
         "Hình 4.5. Trạng thái bảy giả thuyết rủi ro sau đợt sửa chữa"),
        ("tbl", "Bảng 4.7. Đối chiếu hành vi trước và sau khi sửa (đo lại trên đường mã sản phẩm)",
         ["Kịch bản kiểm chứng", "Trước khi sửa", "Sau khi sửa"],
         [
             ["Trích xuất ra một đường dẫn đã có tệp",
              "Ghi đè âm thầm, dữ liệu cũ mất",
              "Từ chối với mã SV-OUTPUT-EXISTS; tệp cũ nguyên vẹn; đường dẫn mới vẫn hoạt động"],
             ["Tạo két trong thư mục không có quyền ghi",
              "Trả về mã lỗi nội bộ vô nghĩa",
              "Trả về mã SV-IO với mô tả cố định, không kèm đường dẫn"],
             ["Thêm tệp vượt trần hai gigabyte",
              "Nguy cơ cạn bộ nhớ hoặc mã lỗi nội bộ",
              "Trả về mã SV-TOO-LARGE trước khi đọc; két giữ nguyên"],
             ["Cưỡng bức hết giờ với tệp 256 MiB",
              "Trả về mã lỗi nội bộ",
              "Trả về mã SV-TIMEOUT; két nguyên vẹn"],
             ["Hai lệnh thêm tệp chạy đồng thời",
              "Mất một tệp trong **12 trên 12** lượt thử",
              "Mất **0 trên 12** lượt thử"],
             ["Gõ sai mật khẩu khi tạo két",
              "Tạo ra một két không bao giờ mở được",
              "Ô nhập lại chặn việc tạo khi hai ô không khớp"],
         ], [4.6, 5.4, 6.2], 10),
        ("p", "Cần trình bày chính xác **mức độ triệt để** của từng cách xử lý, vì không phải tất cả đều "
              "là sửa gốc. Bốn hạng mục H2, H3, H6, H7 được **sửa triệt để** trong phạm vi của chúng. "
              "Hạng mục H1 chỉ được **giảm nhẹ**: trần hai gigabyte và các mã lỗi rõ ràng làm cho thất "
              "bại trở nên an toàn và dễ hiểu, nhưng cách sửa gốc là truyền dòng thì vẫn chưa được thực "
              "hiện. Hạng mục H7 tuy đạt kết quả 0 trên 12 nhưng chỉ giải quyết **xung đột trong cùng "
              "một tiến trình**; hai bản ứng dụng cùng mở một két vẫn chưa được chặn. Hạng mục H5 vẫn "
              "hoàn toàn **để ngỏ** và là điểm chặn duy nhất còn lại đối với việc phân phối rộng rãi."),

        ("h3", "5.4. Bài học phương pháp luận"),
        ("p", "Chiến dịch này cho phép rút ra bốn bài học có giá trị vượt ra ngoài phạm vi một dự án cụ "
              "thể."),
        ("p", "**Bài học thứ nhất: bản giả lập trong kiểm thử che khuất chính những bề mặt cần kiểm "
              "chứng nhất.** Bộ mã hóa giả lập cho phép kiểm thử chạy nhanh và không phụ thuộc môi "
              "trường — đó là một quyết định kỹ thuật đúng. Nhưng nó có nghĩa là 253 hàm kiểm thử không "
              "hề chạm tới tiến trình con, hạn giờ, cơ chế đệm và biến môi trường. Cả sáu khiếm khuyết "
              "được xác nhận đều nằm ở những bề mặt đó hoặc ở tầng giao diện."),
        ("p", "**Bài học thứ hai: các khiếm khuyết nghiêm trọng nhất thường không phải lỗi mật mã.** "
              "Trong sáu khiếm khuyết được xác nhận, không có khiếm khuyết nào là lỗi thuật toán hay lỗi "
              "lắp ghép nguyên thủy. Chúng là: thiếu một ô nhập liệu, thiếu một phép kiểm tra tồn tại "
              "tệp, thiếu một khóa đồng bộ, ánh xạ lỗi quá thô, mô hình bộ nhớ không phù hợp với dữ liệu "
              "lớn, và một vấn đề của cơ chế phân phối phần mềm."),
        ("p", "**Bài học thứ ba: giả thuyết có thể đúng về triệu chứng nhưng sai về nguyên nhân.** "
              "Trường hợp H1 cho thấy nếu chỉ suy luận mà không đo, biện pháp khắc phục có thể nhắm sai "
              "hoàn toàn."),
        ("p", "**Bài học thứ tư: một số giả thuyết chỉ kiểm chứng được trên nền tảng thật.** Giả thuyết "
              "H4 không thể giải quyết trên máy phát triển; nó chỉ được đóng lại khi kiểm thử chạy trên "
              "một máy Windows thật trong môi trường tích hợp liên tục. Điều này biện minh cho chi phí "
              "duy trì một ma trận nhiều hệ điều hành."),
    ]

    # ============================ 6. Nhan xet chung
    B += [
        ("h2", "6. Nhận xét chung về kết quả thử nghiệm"),

        ("h3", "6.1. Kết quả đạt được"),
        ("p", "Về **tính đầy đủ chức năng**, cả sáu mô-đun đều đã được hiện thực hóa và có mã vượt qua "
              "toàn bộ cổng chất lượng. Ba mươi tám lệnh được đăng ký và có hiện thực tương ứng; không "
              "có lệnh nào là khung rỗng."),
        ("p", "Về **độ bao phủ kiểm thử**, 253 hàm kiểm thử với 249 hàm đạt là một mức bao phủ tốt cho "
              "một dự án ở quy mô này, và điều quan trọng hơn con số là **trọng tâm** của chúng: một tỷ "
              "lệ đáng kể nhắm trực tiếp vào các thuộc tính an toàn — tính chống dò kênh lỗi, tính chống "
              "ghép tệp, ràng buộc ngữ cảnh khóa, tính bền vững của bộ phân tích — chứ không chỉ vào "
              "đường thực thi thuận lợi."),
        ("p", "Về **kiến trúc**, ba thuộc tính thiết kế đã được kiểm chứng bằng thực tế phát triển: "
              "crate nghiệp vụ không phụ thuộc nền tảng và kiểm thử được độc lập; việc bổ sung mô-đun "
              "mới diễn ra theo cách cộng thêm; và việc cách ly cây phụ thuộc của giao diện cho phép "
              "kiểm toán chuỗi cung ứng của phần lõi một cách có ý nghĩa."),
        ("p", "Về **tính trung thực trong tài liệu hóa**, dự án duy trì một bảng đối chiếu giữa tài liệu "
              "và mã nguồn, ghi nhận cả các chú thích đã lỗi thời, các đoạn mã giao diện chết, và các "
              "quyết định thiết kế bị hoãn. Đây là một thực hành đáng ghi nhận trong bối cảnh nhiều dự "
              "án chọn cách im lặng."),
        ("p", "Về **phương pháp kiểm chứng**, chiến dịch kiểm chứng giả thuyết rủi ro đã chứng minh giá "
              "trị của mình một cách rất cụ thể: nó phát hiện sáu khiếm khuyết mà 253 hàm kiểm thử hoàn "
              "toàn bỏ sót, trong đó có một khiếm khuyết ở mức nghiêm trọng."),

        ("h3", "6.2. Hạn chế và nguyên nhân"),
        ("p", "**Hạn chế thứ nhất — mô hình bộ nhớ.** Đường xử lý tải trọng nạp toàn bộ vào bộ nhớ, dẫn "
              "tới đỉnh tiêu thụ khoảng 2,7 lần kích thước dữ liệu. Nguyên nhân là quyết định dùng một "
              "khối tải trọng duy nhất, vốn cần thiết để giấu danh mục tệp. Biện pháp hiện tại là rào "
              "chắn, không phải sửa gốc."),
        ("p", "**Hạn chế thứ hai — chi phí ghi tỉ lệ với tổng kích thước két.** Mỗi lần thêm một tệp, "
              "toàn bộ két được đóng gói lại, mã hóa lại và ký lại. Cùng nguyên nhân với hạn chế thứ "
              "nhất."),
        ("p", "**Hạn chế thứ ba — chưa có khóa ở mức hệ điều hành.** Hai bản ứng dụng cùng mở một két "
              "vẫn có thể gây mất cập nhật. Nguyên nhân là biện pháp hiện tại chỉ dùng cơ chế đồng bộ "
              "trong tiến trình."),
        ("p", "**Hạn chế thứ tư — gói cài chưa được ký số.** Đây là điểm chặn duy nhất còn lại đối với "
              "việc phân phối rộng rãi, và hậu quả đã được xác nhận bằng thực nghiệm trên macOS. Nguyên "
              "nhân là dự án tự xác định phạm vi là công cụ dùng nội bộ."),
        ("p", "**Hạn chế thứ năm — chưa xác minh tương thích chữ ký với công cụ chuẩn.** Định dạng đã "
              "được hiện thực theo đặc tả và vòng lặp nội bộ đã được kiểm chứng, nhưng chưa có bằng "
              "chứng thực nghiệm rằng một chữ ký do hệ thống sinh ra kiểm được bằng công cụ minisign "
              "chuẩn."),
        ("p", "**Hạn chế thứ sáu — chưa có cơ chế ràng buộc bằng dữ liệu liên kết.** Việc ràng buộc "
              "khối bọc vào ngữ cảnh hiện là gián tiếp qua khóa. Đây là lớp phòng thủ theo chiều sâu bị "
              "hoãn, không phải lỗ hổng."),
        ("p", "**Hạn chế thứ bảy — khoảng trống TOCTOU trong ghim băm nhị phân.** Phép kiểm băm diễn ra "
              "một lần lúc khởi tạo."),
        ("p", "**Hạn chế thứ tám — chưa có kiểm thử tự động cho giao diện ở mức chạy thật.** Chỉ có "
              "kiểm thử đối chiếu bảng mã lỗi."),
        ("p", "**Hạn chế thứ chín — chưa có kiểm định độc lập.** Toàn bộ đánh giá là đánh giá nội bộ."),
        ("p", "**Hạn chế thứ mười — dữ liệu hiệu năng còn thưa.** Các phép đo thực hiện trên một cấu "
              "hình duy nhất, một lần đo cho mỗi kịch bản, và thiếu hẳn phép đo cho hàm dẫn xuất khóa "
              "vốn ảnh hưởng trực tiếp nhất tới cảm nhận của người dùng."),

        ("h3", "6.3. Hướng hoàn thiện"),
        ("p", "Theo thứ tự ưu tiên dựa trên tương quan giữa mức độ ảnh hưởng và chi phí thực hiện, sáu "
              "hướng hoàn thiện được đề xuất."),
        ("b", "**Chuyển đường xử lý tải trọng sang mô hình truyền dòng.** Đây là thay đổi có ảnh hưởng "
              "lớn nhất, giải quyết đồng thời hạn chế thứ nhất và thứ hai, và cho phép nâng hoặc bỏ trần "
              "hai gigabyte. Cần thiết kế lại cả cơ chế đóng gói và cách trao đổi với tiến trình con."),
        ("b", "**Bổ sung khóa ở mức hệ điều hành cho tệp két**, đóng lại phần còn lại của hạn chế thứ ba. "
              "Chi phí thấp, giá trị an toàn dữ liệu rõ ràng."),
        ("b", "**Nối cổng kiểm tra tương thích chữ ký vào quy trình tích hợp liên tục.** Chi phí rất "
              "thấp, và giá trị là biến một tuyên bố tương thích thành một sự kiện được kiểm chứng tự "
              "động ở mỗi lần đẩy mã."),
        ("b", "**Nối cơ chế hiệu chỉnh tham số vào đường tạo két và giao diện thiết lập**, kèm bổ sung "
              "phép đo thời gian dẫn xuất khóa. Chi phí thấp vì mã đã có sẵn."),
        ("b", "**Bổ sung mục tiêu fuzz có dẫn hướng theo độ phủ** cho bộ phân tích container, chạy định "
              "kỳ. Điều này mở rộng đáng kể phạm vi bằng chứng về tính bền vững."),
        ("b", "**Thiết lập quy trình ký số và công chứng gói cài** nếu phạm vi sử dụng được mở rộng ra "
              "ngoài nội bộ. Đây không phải công việc kỹ thuật phần mềm mà là công việc quy trình và "
              "quản lý chứng thư."),
    ]

    B += [
        ("h2", "Kết luận chương 4"),
        ("p", "Chương 4 đã trình bày kết quả đánh giá hệ thống trên bốn trụ cột bổ sung cho nhau. Bộ "
              "kiểm thử tự động với 253 hàm cho thấy độ bao phủ tốt và, quan trọng hơn, có trọng tâm "
              "nhắm vào các thuộc tính an toàn chứ không chỉ vào đường thực thi thuận lợi. Các cổng "
              "kiểm tra trong quy trình tích hợp liên tục đã chứng minh giá trị của mình bằng việc đóng "
              "lại một giả thuyết rủi ro mà máy phát triển không thể kiểm chứng."),
        ("p", "Phép đo hiệu năng cho thấy thông lượng ở mức chấp nhận được nhưng đồng thời phát hiện "
              "rằng ràng buộc thực sự của hệ thống là bộ nhớ chứ không phải thời gian — một kết luận "
              "trái với giả thuyết ban đầu và chỉ có được nhờ đo đạc."),
        ("p", "Chiến dịch kiểm chứng giả thuyết rủi ro là phần có giá trị nhất: bảy giả thuyết được đặt "
              "ra, sáu được xác nhận, và sáu khiếm khuyết được phát hiện đều nằm ngoài tầm với của bộ "
              "kiểm thử tự động. Đáng chú ý nhất là không một khiếm khuyết nào là lỗi mật mã — chúng "
              "nằm ở giao diện, ở xử lý đồng thời, ở mô hình bộ nhớ, ở cách báo lỗi và ở cơ chế phân "
              "phối phần mềm."),
        ("p", "Chương cũng đã liệt kê đầy đủ mười hạn chế còn tồn đọng cùng nguyên nhân, và đề xuất sáu "
              "hướng hoàn thiện theo thứ tự ưu tiên. Việc trình bày các hạn chế một cách đầy đủ và cụ "
              "thể, thay vì làm nhẹ chúng, là điều kiện để đánh giá trong báo cáo này có giá trị tham "
              "khảo thực sự."),
    ]
    return B
