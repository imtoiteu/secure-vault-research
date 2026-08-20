# -*- coding: utf-8 -*-
"""CHUONG 2 — Phan tich va thiet ke he thong."""


def blocks():
    B = [("h1", "CHƯƠNG 2\nPHÂN TÍCH VÀ THIẾT KẾ HỆ THỐNG")]

    # ======================================================= 1. Phan tich bai toan
    B += [
        ("h2", "1. Phân tích bài toán"),

        ("h3", "1.1. Đặt vấn đề và mục tiêu xây dựng hệ thống"),
        ("p", "Bài toán đặt ra cho hệ thống có thể phát biểu như sau: xây dựng một ứng dụng máy tính để "
              "bàn cho phép một người dùng đơn lẻ, trên một máy tính không nối mạng, thực hiện được năm "
              "nhóm tác vụ bảo mật thiết yếu — cất giữ tệp trong hộp chứa mã hóa, mã hóa và ký tệp đơn "
              "lẻ, kiểm tra tính toàn vẹn và xuất xứ của tệp nhận về, sao lưu vật liệu khóa theo cơ chế "
              "ngưỡng, và làm sạch các dấu vết riêng tư — với điều kiện toàn bộ các thao tác mật mã đều "
              "dựa trên nguyên thủy đã được kiểm chứng và toàn bộ các bảo đảm an toàn đều có thể truy "
              "vết được tới mã nguồn."),
        ("p", "Từ phát biểu đó, ba mục tiêu thiết kế cấp cao được xác lập. Mục tiêu thứ nhất là **tính "
              "bí mật gắn liền với tính toàn vẹn**: mọi dữ liệu được hệ thống ghi ra đĩa đều phải ở dạng "
              "mã hóa có xác thực, và mọi phép đọc phải kiểm tra tính toàn vẹn trước khi trả về dù chỉ "
              "một byte dữ liệu rõ. Mục tiêu thứ hai là **an toàn khi thất bại**: mọi trạng thái lỗi "
              "phải dẫn tới hành vi từ chối rõ ràng chứ không phải hành vi âm thầm sai, và các thông "
              "điệp lỗi không được trở thành kênh rò rỉ. Mục tiêu thứ ba là **an toàn về dữ liệu người "
              "dùng**: hệ thống không bao giờ được phá hủy dữ liệu có sẵn, kể cả khi thao tác đang thực "
              "hiện bị gián đoạn giữa chừng."),
        ("p", "Ba mục tiêu này không đứng riêng lẻ mà ràng buộc lẫn nhau và ràng buộc lên kiến trúc. "
              "Chẳng hạn, mục tiêu thứ nhất buộc container phải mang chữ ký; mục tiêu thứ hai buộc phép "
              "kiểm chữ ký phải nằm **trước** phép kiểm mật khẩu; và mục tiêu thứ ba buộc mọi thao tác "
              "ghi phải là ghi nguyên tử qua tệp tạm rồi đổi tên. Toàn bộ phần còn lại của chương này có "
              "thể đọc như một chuỗi các hệ quả kỹ thuật rút ra từ ba mục tiêu đó."),

        ("h3", "1.2. Phạm vi chức năng của hệ thống"),
        ("p", "Hệ thống được tổ chức thành sáu mô-đun chức năng nhìn từ phía người dùng. **Két an toàn** "
              "là mô-đun sáng lập, cung cấp một hộp chứa mã hóa cho nhiều tệp với vòng đời tạo — mở khóa "
              "— thao tác — khóa lại, kèm khả năng đổi mật khẩu, kiểm tra toàn vẹn và sao lưu khóa chủ. "
              "**Mật mã tệp** cung cấp các dịch vụ mức tệp không cần tới két: mã hóa và giải mã bằng mật "
              "khẩu, tạo cặp khóa ký, ký tệp, kiểm tra chữ ký, lấy vân tay và kiểm tra tính toàn vẹn của "
              "tệp tải về. **Chia sẻ bí mật** cho phép chia một bí mật hoặc một tệp thành n mảnh với "
              "ngưỡng k, kèm khả năng chuyển mảnh qua mã QR. **Giấu tin** cho phép giấu dữ liệu đã mã "
              "hóa vào ảnh, trích xuất trở lại và dò tìm dấu hiệu dữ liệu ẩn. **Thủy vân** cung cấp dấu "
              "chống giả mạo vô hình có khóa. **Phân tích siêu dữ liệu** cho phép xem, xóa và so sánh "
              "siêu dữ liệu nhúng trong tệp."),
        ("p", "Điểm cần làm rõ về mặt trạng thái hiện thực: cả sáu mô-đun đều **đã được hiện thực hóa** "
              "và có mã vượt qua toàn bộ cổng chất lượng của dự án. Tuy vậy có ba sắc thái cần ghi nhận. "
              "Thứ nhất, mô-đun Két an toàn hiện **chưa sử dụng lại** tầng dịch vụ mức tệp mà dùng đường "
              "băm, ký và kiểm tra riêng của nó; việc hợp nhất hai đường này được dự án ghi nhận là một "
              "bước tái cấu trúc còn để ngỏ. Thứ hai, mô-đun Phân tích siêu dữ liệu phụ thuộc vào một "
              "nhị phân ngoài không bắt buộc; nếu nhị phân đó không có mặt trong gói cài, mô-đun sẽ tự "
              "tắt theo hướng an toàn thay vì hoạt động một phần. Thứ ba, các nhánh nghiên cứu như thủy "
              "vân bền vững hay dùng mã QR cho các loại bí mật ngoài mảnh chia sẻ được xác định rõ là "
              "**chưa hiện thực hóa**."),

        ("h3", "1.3. Các tác nhân và vai trò"),
        ("p", "Khác với các hệ thống thông tin nhiều người dùng, hệ thống này chỉ có **một tác nhân con "
              "người lúc chạy**: người dùng cuối. Không có khái niệm tài khoản, không có phân quyền theo "
              "vai trò, không có quản trị viên. Quyền truy cập được xác định hoàn toàn bởi hai yếu tố: "
              "quyền truy cập tệp ở mức hệ điều hành, và việc nắm giữ mật khẩu hoặc đủ số mảnh khôi phục."),
        ("p", "Bên cạnh đó tồn tại một tác nhân con người thứ hai nhưng chỉ hoạt động ở **thời điểm biên "
              "dịch**: nhà phát triển hoặc người đóng gói. Tác nhân này chịu trách nhiệm đặt các nhị phân "
              "ngoài vào đúng vị trí và, thông qua kịch bản dựng, ghim giá trị băm của chúng vào mã máy. "
              "Việc tách bạch tác nhân này khỏi tác nhân lúc chạy là một chi tiết quan trọng của mô hình "
              "tin cậy: người dùng cuối không có khả năng và không được phép thay thế các nhị phân đó."),
        ("p", "Ngoài hai tác nhân con người, hệ thống tương tác với ba tác nhân phi con người: hai nhị "
              "phân ngoài đi kèm gói cài, và hệ thống tệp cục bộ. Cả ba đều nằm ở phía bên kia một ranh "
              "giới tin cậy và do đó đều phải được xử lý theo nguyên tắc phòng vệ."),
    ]

    # ==================================================== 2. Phan tich yeu cau
    B += [
        ("h2", "2. Phân tích yêu cầu hệ thống"),

        ("h3", "2.1. Yêu cầu chức năng"),
        ("p", "Các yêu cầu chức năng được tái dựng từ chính bề mặt lệnh mà giao diện có thể gọi, tức là "
              "từ ba mươi tám hàm lệnh được đăng ký trong bộ điều phối của khung ứng dụng. Cách tiếp cận "
              "này bảo đảm rằng không có yêu cầu nào được liệt kê mà không có hiện thực tương ứng. Bảng "
              "2.1 tổng hợp các yêu cầu chức năng theo từng mô-đun."),
        ("tbl", "Bảng 2.1. Danh mục yêu cầu chức năng và lệnh hiện thực tương ứng",
         ["Mã", "Yêu cầu chức năng", "Lệnh hiện thực", "Trạng thái"],
         [
             ["FR-V1", "Tạo két mã hóa mới với mật khẩu và chính sách khôi phục tùy chọn", "`vault_create`", "Đã hiện thực"],
             ["FR-V2", "Mở khóa két thành một phiên mờ; khóa lại để xóa khóa trong bộ nhớ", "`vault_unlock`, `vault_lock`", "Đã hiện thực"],
             ["FR-V3", "Đổi mật khẩu bằng cách bọc lại khóa, không mã hóa lại tải trọng", "`vault_change_passphrase`", "Đã hiện thực"],
             ["FR-V4", "Liệt kê, thêm và trích xuất tệp trong két", "`item_list`, `item_add`, `item_extract`", "Đã hiện thực"],
             ["FR-V5", "Báo cáo siêu dữ liệu không bí mật của két; xuất khóa công khai ký", "`vault_meta`, `export_signing_public_key`", "Đã hiện thực"],
             ["FR-V6", "Kiểm tra tính toàn vẹn và chữ ký của container", "`integrity_check`, `integrity_hash`", "Đã hiện thực"],
             ["FR-V7", "Chia và khôi phục khóa chủ theo ngưỡng k trong n", "`keys_split`, `keys_recover`", "Đã hiện thực"],
             ["FR-C1", "Lấy vân tay BLAKE3 của tệp bất kỳ theo cơ chế truyền dòng", "`integrity_hash_file`", "Đã hiện thực"],
             ["FR-C2", "Kiểm tra chữ ký tách rời theo khóa công khai bên ngoài", "`integrity_verify_signature`", "Đã hiện thực"],
             ["FR-C3", "Kiểm tra toàn vẹn theo băm và/hoặc chữ ký, hai phép kiểm độc lập", "`integrity_verify_integrity`", "Đã hiện thực"],
             ["FR-C4", "Mã hóa và giải mã tệp bằng mật khẩu (định dạng SVENC)", "`crypto_encrypt_file`, `crypto_decrypt_file`", "Đã hiện thực"],
             ["FR-C5", "Tạo cặp khóa ký cất giữ đã mã hóa; ký tệp", "`crypto_generate_signing_keypair`, `crypto_sign_file`", "Đã hiện thực"],
             ["FR-S1", "Chia một bí mật dạng chuỗi, trả về chuỗi mảnh chép tay được", "`shares_split_secret`", "Đã hiện thực"],
             ["FR-S2", "Chia một tệp; mảnh lưu hành dưới dạng tệp", "`shares_split_file`", "Đã hiện thực"],
             ["FR-S3", "Khôi phục từ tệp mảnh và/hoặc chuỗi mảnh dán vào", "`shares_recover_secret`", "Đã hiện thực"],
             ["FR-S4", "Xuất mảnh ra ảnh QR; khôi phục từ ảnh QR", "`shares_export_qr`, `shares_recover_from_qr`", "Đã hiện thực"],
             ["FR-G1", "Mã hóa rồi giấu tải trọng vào ảnh bìa PNG, BMP hoặc JPEG", "`stego_hide`", "Đã hiện thực"],
             ["FR-G2", "Trích xuất và giải mã tải trọng, bảo đảm chống dò kênh lỗi", "`stego_extract`", "Đã hiện thực"],
             ["FR-G3", "Dò dấu hiệu dữ liệu ẩn theo phương pháp thực nghiệm", "`stego_detect`", "Đã hiện thực"],
             ["FR-W1", "Nhúng dấu chống giả mạo vô hình, có khóa, dễ vỡ", "`watermark_embed`", "Đã hiện thực"],
             ["FR-W2", "Kiểm tra dấu: Nguyên vẹn / Bị sửa / Không có dấu", "`watermark_verify`", "Đã hiện thực"],
             ["FR-A1", "Xem siêu dữ liệu nhúng trong tệp", "`metadata_inspect`", "Phụ thuộc nhị phân tùy chọn"],
             ["FR-A2", "Xóa siêu dữ liệu và báo cáo trung thực mức bảo đảm theo định dạng", "`metadata_sanitize`", "Phụ thuộc nhị phân tùy chọn"],
             ["FR-A3", "So sánh siêu dữ liệu của hai tệp", "`metadata_diff`", "Phụ thuộc nhị phân tùy chọn"],
             ["FR-A4", "Báo cáo mô-đun Phân tích có sẵn sàng hay không (tắt an toàn)", "`metadata_available`", "Đã hiện thực"],
         ], [1.4, 6.4, 5.6, 2.8], 10),
        ("p", "Cần lưu ý một chi tiết dễ gây hiểu nhầm trong bảng trên: hai yêu cầu FR-V6 và FR-C1 nhìn "
              "bề ngoài đều là “tính băm tệp”, nhưng chúng đi qua hai đường mã khác nhau. Đường của két "
              "nạp toàn bộ tệp vào bộ nhớ và do đó chịu trần hai gigabyte, trong khi đường của tầng dịch "
              "vụ mức tệp **truyền dòng theo từng khối 64 KiB** và vì thế không có trần kích thước. Đây "
              "chính là biểu hiện cụ thể của việc két chưa dùng lại tầng dịch vụ chung, như đã nêu ở mục "
              "1.2."),

        ("h3", "2.2. Yêu cầu phi chức năng"),
        ("p", "Nếu các yêu cầu chức năng trả lời câu hỏi “hệ thống làm được gì”, thì các yêu cầu phi chức "
              "năng trả lời câu hỏi “hệ thống phải làm điều đó với những ràng buộc nào”. Đối với một hệ "
              "thống an toàn thông tin, nhóm yêu cầu thứ hai này thường quan trọng hơn nhóm thứ nhất. "
              "Bảng 2.2 trình bày mười ba yêu cầu phi chức năng cùng cơ chế bảo đảm tương ứng."),
        ("tbl", "Bảng 2.2. Yêu cầu phi chức năng và cơ chế bảo đảm",
         ["Mã", "Nhóm", "Yêu cầu", "Cơ chế bảo đảm trong hiện thực"],
         [
             ["NFR-1", "Bí mật", "Không vật liệu bí mật nào đi qua biên giao tiếp hay xuất hiện trong DTO",
              "Crate DTO không chứa kiểu bí mật nào; các kiểu bí mật cố ý không cài đặt Serialize"],
             ["NFR-2", "Bí mật", "Bí mật trong bộ nhớ được xóa, che trong nhật ký gỡ lỗi, chống tái cấp phát",
              "`Key32`/`KeyShare` tự xóa khi hủy; `SecretBytes` dùng `Box<[u8]>` không có dung lượng dư"],
             ["NFR-3", "Toàn vẹn", "Container được ký và phát hiện được mọi sửa đổi",
              "Chữ ký Ed25519 trên gốc ràng buộc BLAKE3(header ‖ tải trọng)"],
             ["NFR-4", "Chống oracle", "Thất bại chứng thực không phân biệt được; lỗi lành tính vẫn hành động được",
              "Hợp nhất về `SV-UNAUTHORIZED`; mười một mã còn lại giữ nguyên tính phân biệt"],
             ["NFR-5", "Sẵn sàng", "Bộ nhớ có biên; từ chối đầu vào quá lớn; hạn giờ cho tiến trình con",
              "Trần 2 GiB; header ≤ 1 MiB; hạn giờ 120 s cho age và 60 s cho ExifTool"],
             ["NFR-6", "Chuỗi cung ứng", "Nhị phân ngoài được ghim theo byte; bề mặt phân giải bị đóng khi phát hành",
              "Ghim BLAKE3 lúc dựng; bản release bỏ qua biến môi trường ghi đè đường dẫn"],
             ["NFR-7", "Đặc quyền tối thiểu", "Tiến trình con chạy với môi trường đã xóa, không shell, thư mục cố định",
              "`env_clear()` kèm danh sách cho phép tối thiểu trên Windows; `-config \"\"` cho ExifTool"],
             ["NFR-8", "Ngoại tuyến", "Không phụ thuộc mạng; chính sách nội dung giới hạn nguồn nội bộ",
              "Không có ứng dụng khách mạng nào trong đồ thị phụ thuộc; CSP `default-src 'self'`"],
             ["NFR-9", "Khả chuyển", "Dựng và kiểm thử được trên Linux, macOS và Windows",
              "Ma trận CI ba hệ điều hành; phiên bản Rust tối thiểu 1.96 được cưỡng chế"],
             ["NFR-10", "An toàn dữ liệu", "Không bao giờ ghi đè âm thầm; mọi phép ghi là nguyên tử",
              "Từ chối khi đích tồn tại; ghi qua tệp tạm cùng thư mục rồi đồng bộ và đổi tên"],
             ["NFR-11", "Kiểm toán", "Phần lõi được kiểm toán cách ly khỏi cây phụ thuộc của webview",
              "Crate `desktop` bị loại khỏi workspace; `cargo deny`/`cargo audit` chỉ soi phần lõi"],
             ["NFR-12", "Bản địa hóa", "Giao diện được bản địa hóa hoàn toàn, mặc định tiếng Việt",
              "Mô-đun i18n với ngôn ngữ mặc định là tiếng Việt, tiếng Anh là dự phòng"],
             ["NFR-13", "Linh hoạt thuật toán", "Danh tính thuật toán tường minh ở biên hợp đồng và trên đĩa",
              "Các enum định danh thuật toán ở tầng ABI; `CipherSuite::V1` là enum đóng trên đĩa"],
         ], [1.6, 2.2, 5.6, 6.8], 10),

        ("h3", "2.3. Mô hình ca sử dụng của hệ thống"),
        ("p", "Mô hình ca sử dụng của hệ thống có một đặc điểm khác biệt so với các hệ thống thông tin "
              "thông thường: bên trong phạm vi hệ thống có rất nhiều ca sử dụng, nhưng chỉ có một tác "
              "nhân con người lúc chạy liên kết tới tất cả. Điều này phản ánh đúng bản chất của một công "
              "cụ cá nhân — không có sự phân tách quyền hạn giữa các nhóm người dùng, mà chỉ có sự phân "
              "tách theo việc nắm giữ vật liệu khóa."),
        ("fig", "Hinh-2-01-use-case-tong-quat",
         "Hình 2.1. Biểu đồ ca sử dụng tổng quát của hệ thống Secure Vault Research"),
        ("p", "Hình 2.1 thể hiện mười tám ca sử dụng chia thành sáu nhóm tương ứng với sáu mô-đun chức "
              "năng. Tác nhân “Người dùng cuối” liên kết tới toàn bộ các ca sử dụng, phản ánh việc hệ "
              "thống không có mô hình phân quyền. Tác nhân “Nhà phát triển / đóng gói” được vẽ bằng liên "
              "kết đứt nét và gắn nhãn thời điểm biên dịch, nhằm nhấn mạnh rằng đây không phải một vai "
              "trò sử dụng mà là một vai trò trong chuỗi cung ứng."),
        ("p", "Ba tác nhân phi con người được đặt ở phía đối diện: hai nhị phân ngoài và hệ thống tệp. "
              "Các liên kết tới chúng cũng được vẽ đứt nét và mang nhãn mô tả cơ chế kiểm soát chứ không "
              "chỉ mô tả luồng dữ liệu — chẳng hạn “tiến trình con đã ghim băm” thay vì đơn thuần “gọi "
              "ExifTool”. Cách gắn nhãn này giúp biểu đồ ca sử dụng vẫn giữ được thông tin về mô hình "
              "tin cậy, thay vì chỉ mô tả chức năng."),
        ("p", "Cần lưu ý rằng biểu đồ này chỉ mô tả **khả năng truy cập chức năng ở mức tổng quát**. Các "
              "điều kiện thực thi chi tiết — chẳng hạn một ca sử dụng đòi hỏi phiên đã mở khóa, hay một "
              "ca sử dụng bị vô hiệu hóa khi nhị phân phụ trợ vắng mặt — được trình bày trong phần thiết "
              "kế quy trình và thiết kế an ninh."),
    ]

    # ================================================== 3. Mo hinh de doa
    B += [
        ("h2", "3. Mô hình đe dọa và yêu cầu an toàn"),
        ("note", "Phần này tổng hợp và mở rộng mô hình đe dọa đã được dự án ghi nhận trong tài liệu làm "
                 "cứng. Các mục 3.1 đến 3.4 bám sát tài liệu gốc; các nhận định bổ sung mang tính diễn "
                 "giải phân tích được ghi chú rõ tại chỗ."),

        ("h3", "3.1. Tài sản cần bảo vệ"),
        ("p", "Mô hình đe dọa của hệ thống xác định ba nhóm tài sản. Nhóm thứ nhất là **nội dung dữ liệu**: "
              "bản rõ của các tệp mà người dùng cất trong két, cũng như bản rõ của các tệp được mã hóa "
              "độc lập. Nhóm thứ hai là **vật liệu khóa**: mật khẩu và toàn bộ những gì dẫn xuất từ nó — "
              "khóa chủ, các khóa bọc, danh tính age đã mở bọc và khóa ký đã mở bọc. Nhóm thứ ba là "
              "**các mảnh khôi phục**, vốn có tính chất đặc biệt vì chúng nằm ngoài két và do người dùng "
              "tự bảo quản."),
        ("p", "Bên cạnh ba nhóm tài sản chính, cần bổ sung một tài sản thứ tư mà thiết kế của hệ thống "
              "cho thấy đã được cân nhắc kỹ dù không được liệt kê tường minh: **siêu dữ liệu về nội "
              "dung**. Tên tệp, kích thước từng tệp và số lượng tệp trong một két đều có thể tiết lộ "
              "nhiều thông tin, và quyết định đặt danh mục tệp vào bên trong vùng đã mã hóa cho thấy đây "
              "là một tài sản được bảo vệ có chủ đích."),

        ("h3", "3.2. Ngữ cảnh hoạt động của hệ thống"),
        ("p", "Trước khi liệt kê các mối đe dọa, cần xác định rõ ngữ cảnh hoạt động, bởi vì rất nhiều "
              "mối đe dọa thường gặp trong các hệ thống thông tin đơn giản là **không tồn tại** đối với "
              "hệ thống này."),
        ("fig", "Hinh-2-02-ngu-canh-he-thong",
         "Hình 2.2. Biểu đồ ngữ cảnh của hệ thống Secure Vault Research"),
        ("p", "Hình 2.2 đặt hệ thống ở trung tâm và liệt kê toàn bộ các thực thể bên ngoài mà nó trao "
              "đổi thông tin. Điểm đáng chú ý nhất của biểu đồ này là **những gì không có mặt**: không "
              "có máy chủ ứng dụng, không có cơ sở dữ liệu tập trung, không có dịch vụ đám mây, không có "
              "kênh đồng bộ và không có bất kỳ ứng dụng khách mạng nào. Khối màu đỏ ở giữa biểu đồ ghi "
              "nhận điều này một cách tường minh, vì việc chứng minh sự vắng mặt của một thành phần cũng "
              "quan trọng như việc mô tả các thành phần có mặt."),
        ("p", "Hệ quả trực tiếp là toàn bộ họ mối đe dọa liên quan tới mạng — chặn bắt trên đường truyền, "
              "tấn công người-ở-giữa, chiếm quyền phiên làm việc, tấn công vào máy chủ — đều nằm ngoài "
              "mô hình. Đây không phải là một sự lơ là mà là hệ quả của quyết định kiến trúc: bằng cách "
              "loại bỏ hoàn toàn thành phần mạng, hệ thống loại bỏ luôn cả một mảng lớn bề mặt tấn công."),
        ("p", "Đổi lại, một trọng trách được chuyển sang người dùng: đơn vị chia sẻ duy nhất là một tệp, "
              "và việc di chuyển tệp đó tới người nhận là trách nhiệm của người dùng. Hệ thống bảo đảm "
              "rằng tệp đó an toàn khi ở trạng thái tĩnh, nhưng không cung cấp và không tuyên bố cung "
              "cấp bất kỳ bảo đảm nào về kênh vận chuyển."),

        ("h3", "3.3. Các mối đe dọa trong phạm vi phòng vệ"),
        ("p", "Năm nhóm mối đe dọa được xác định là nằm trong phạm vi phòng vệ của hệ thống, và mỗi nhóm "
              "gắn với một hoặc nhiều cơ chế cụ thể trong hiện thực."),
        ("p", "**Thứ nhất, lộ dữ liệu ở trạng thái tĩnh.** Kẻ tấn công có được tệp két — do đánh cắp "
              "thiết bị, do lấy được bản sao lưu, hoặc do tệp bị đồng bộ nhầm lên dịch vụ đám mây. Cơ chế "
              "phòng vệ gồm ba lớp chồng nhau: tải trọng được mã hóa có xác thực bằng age; vật liệu khóa "
              "trong header được bọc bằng AEAD dưới khóa dẫn xuất từ mật khẩu qua Argon2id; và thư mục "
              "mục nằm bên trong vùng đã mã hóa. Kết quả là một tệp két bị đánh cắp chỉ để lộ đúng những "
              "gì được thiết kế cho phép lộ: kích thước tổng của bản mã, hai dấu thời gian, tham số chi "
              "phí của hàm dẫn xuất khóa, và các khóa công khai."),
        ("p", "**Thứ hai, sửa đổi và giả mạo.** Kẻ tấn công sửa nội dung tệp két nhằm gây hành vi sai "
              "lệch, hoặc ghép phần header của một tệp này với phần tải trọng của tệp khác. Cơ chế phòng "
              "vệ là chữ ký trên gốc ràng buộc, được trình bày chi tiết ở mục 7.2. Điểm mấu chốt là phép "
              "kiểm tra này diễn ra **trước khi mật khẩu được sử dụng**, nên nó vừa là lớp bảo vệ toàn "
              "vẹn vừa là điều kiện để mô hình lỗi không trở thành oracle."),
        ("p", "**Thứ ba, tệp đầu vào độc hại.** Kẻ tấn công cung cấp một tệp được chế tác đặc biệt nhằm "
              "khai thác bộ phân tích cú pháp của hệ thống. Cơ chế phòng vệ gồm: bộ phân tích được viết "
              "bằng Rust an toàn với mọi truy cập đều kiểm tra biên, và được chứng minh không gây hoảng "
              "loạn bằng một phép quét kiểu fuzz có tính tất định; trần kích thước header một mebibyte; "
              "và đặc biệt là **trần tham số Argon2id được kiểm tra trước khi xác thực** — vì header có "
              "thể bị kẻ tấn công điều khiển trước khi bất kỳ phép xác thực nào chạy, nên nếu không có "
              "trần này, một tệp két được ký hợp lệ nhưng có ác ý vẫn có thể yêu cầu hàng chục gigabyte "
              "bộ nhớ."),
        ("p", "**Thứ tư, nhị phân đi kèm bị thay thế hoặc treo.** Cơ chế phòng vệ là ghim băm BLAKE3 kết "
              "hợp hạn giờ tường và môi trường thực thi đã bị xóa sạch. Cần ghi nhận một khoảng trống đã "
              "được dự án nêu rõ: phép kiểm băm diễn ra một lần lúc khởi tạo, nên nếu tệp nhị phân bị "
              "thay thế trong khoảng thời gian giữa lần kiểm và lần chạy thì hệ thống không phát hiện "
              "được. Đây là một điểm yếu TOCTOU đã biết, được xếp mức thấp trong hồ sơ rủi ro."),
        ("p", "**Thứ năm, dò kênh lỗi.** Kẻ tấn công gọi lặp các lệnh với đầu vào biến đổi và quan sát mã "
              "lỗi trả về nhằm suy ra thông tin bí mật. Cơ chế phòng vệ là mô hình lỗi được thiết kế có "
              "chủ đích, trình bày ở mục 9.2."),

        ("h3", "3.4. Các mối đe dọa nằm ngoài phạm vi"),
        ("p", "Việc tuyên bố rõ những gì hệ thống **không** bảo vệ có giá trị không kém việc mô tả những "
              "gì nó bảo vệ. Bốn nhóm sau được xác định là nằm ngoài phạm vi."),
        ("b", "**Kẻ tấn công đọc được bộ nhớ tiến trình đang chạy.** Một kẻ tấn công có quyền gắn trình "
              "gỡ lỗi hoặc chạy mã tùy ý trên máy đã mở khóa có thể đọc trực tiếp khóa chủ, bất kể mọi "
              "biện pháp vệ sinh bộ nhớ. Việc xóa bí mật thu hẹp cửa sổ tấn công nhưng không thể loại bỏ nó."),
        ("b", "**Các bản sao mật khẩu do khung ứng dụng tạo ra trước khi mã của hệ thống chạy.** Mật khẩu "
              "đi qua cầu giao tiếp dưới dạng chuỗi JSON, nên bộ đệm thông điệp và bộ đệm phân tích cú "
              "pháp của khung ứng dụng đã giữ bản sao trước khi kiểu bọc mật khẩu của hệ thống nhận được "
              "quyền kiểm soát. Đây là rủi ro tồn đọng được ghi nhận công khai."),
        ("b", "**Các kênh kề ngoài phạm vi đã kiểm tra.** Hệ thống dựa vào tính không phụ thuộc thời gian "
              "của các nguyên thủy libsodium, nhưng không kiểm soát được các kênh kề ở mức bộ nhớ đệm của "
              "bộ xử lý, mức hệ điều hành hay bên trong tiến trình age."),
        ("b", "**Cấu hình vùng trao đổi và tệp kết xuất sự cố của hệ điều hành.** Hệ thống có thể khuyến "
              "nghị nhưng không thể cưỡng chế người dùng bật mã hóa toàn đĩa và mã hóa vùng trao đổi."),
        ("p", "Liên quan tới nhóm thứ tư, cần phân tích một quyết định thiết kế đáng chú ý: dự án đã "
              "**cân nhắc và cố ý hoãn** việc khóa trang bộ nhớ chứa bí mật. Lý do được nêu rất cụ thể: "
              "cơ chế khóa trang đòi hỏi mã không an toàn phụ thuộc nền tảng, mâu thuẫn với kỷ luật cấm "
              "mã không an toàn của các crate nghiệp vụ; hơn nữa nó phải khóa đúng các trang đang chứa "
              "khóa chủ, điều khó bảo đảm khi giá trị được lưu trong một bảng băm và có thể bị di chuyển "
              "trong bộ nhớ. Biện pháp thay thế được lựa chọn là khuyến nghị mã hóa toàn đĩa và vùng trao "
              "đổi ở mức hệ điều hành, đồng thời giữ cho khóa chủ là bí mật duy nhất tồn tại lâu dài. "
              "Đây là một ví dụ tốt về việc ghi nhận trung thực một sự đánh đổi thay vì che giấu nó."),

        ("h3", "3.5. Ranh giới tin cậy và cơ chế kiểm soát trên từng ranh giới"),
        ("p", "Mô hình đe dọa được cụ thể hóa thành bốn ranh giới tin cậy. Mỗi ranh giới là một điểm mà "
              "dữ liệu hoặc quyền điều khiển đi từ vùng có mức tin cậy này sang vùng có mức tin cậy khác, "
              "và do đó là nơi bắt buộc phải đặt cơ chế kiểm soát."),
        ("fig", "Hinh-2-03-ranh-gioi-tin-cay",
         "Hình 2.3. Bốn ranh giới tin cậy và cơ chế kiểm soát tương ứng"),
        ("p", "Hình 2.3 thể hiện đồng thời bốn ranh giới. Ranh giới thứ nhất, giữa giao diện webview và "
              "lõi Rust, là ranh giới bận rộn nhất. Nguyên tắc kiểm soát ở đây gồm ba vế: không có bí "
              "mật nào nằm trong bất kỳ đối tượng truyền dữ liệu nào; phiên làm việc chỉ được biểu diễn "
              "bằng một chuỗi định danh mờ, không mang thông tin; và mật khẩu — thứ duy nhất bắt buộc "
              "phải đi ngược chiều qua ranh giới này — được nhận bằng một kiểu dữ liệu chuyên dụng có "
              "khả năng tự xóa và che nội dung khi in ra nhật ký."),
        ("p", "Ranh giới thứ hai, giữa lõi và các tiến trình con ngoài, được kiểm soát bằng năm biện pháp "
              "chồng lên nhau: ghim băm nhị phân, xóa sạch biến môi trường, không thông qua trình thông "
              "dịch lệnh, thư mục làm việc riêng biệt, và hạn giờ tường. Riêng với tiến trình con xử lý "
              "siêu dữ liệu còn có biện pháp thứ sáu là truyền tham số vô hiệu hóa cơ chế cấu hình bằng "
              "mã thực thi — đây là bề mặt tấn công nghiêm trọng nhất của công cụ đó."),
        ("p", "Ranh giới thứ ba, giữa lõi và hệ thống tệp, được kiểm soát bằng ba biện pháp: container "
              "được ký và mã hóa nên nội dung đọc lên không được tin cho tới khi chữ ký được xác minh; "
              "mọi phép ghi đều nguyên tử qua tệp tạm cùng thư mục rồi đồng bộ và đổi tên; và mọi thao "
              "tác xuất ra đều từ chối ghi đè lên tệp đã tồn tại."),
        ("p", "Ranh giới thứ tư có tính chất khác hẳn ba ranh giới trên: nó là một ranh giới ở **thời "
              "điểm xây dựng** chứ không phải lúc chạy. Cây phụ thuộc của thành phần webview rất lớn và "
              "chứa nhiều crate mà dự án không thể kiểm toán một cách có ý nghĩa. Giải pháp là loại crate "
              "vỏ giao diện ra khỏi workspace, nhờ đó hai công cụ kiểm tra chuỗi cung ứng chỉ soi phần "
              "lõi mật mã. Đây là một quyết định đáng chú ý vì nó cho thấy khả năng kiểm toán được coi "
              "là một thuộc tính an toàn chứ không chỉ là một tiện ích phát triển."),
        ("tbl", "Bảng 2.3. Tổng hợp bốn ranh giới tin cậy",
         ["Ranh giới", "Cái gì đi qua", "Cơ chế kiểm soát", "Rủi ro tồn đọng"],
         [
             ["TB-1 · Webview ↔ lõi Rust",
              "Đường dẫn tệp, tham số, DTO không bí mật; chiều ngược lại là mã lỗi SV-*; mật khẩu đi vào",
              "Không bí mật trong DTO; phiên là chuỗi mờ; mật khẩu dùng kiểu tự xóa",
              "Bản sao mật khẩu do khung ứng dụng tạo trước khi mã hệ thống chạy"],
             ["TB-2 · Lõi ↔ tiến trình con",
              "Bản rõ và bản mã qua luồng chuẩn (age); đường dẫn tệp qua tham số dòng lệnh (ExifTool)",
              "Ghim băm BLAKE3; `env_clear`; không shell; thư mục làm việc riêng; hạn giờ; `-config \"\"`",
              "Khoảng trống TOCTOU giữa lần kiểm băm và lần thực thi"],
             ["TB-3 · Lõi ↔ hệ thống tệp",
              "Tệp container và các tệp artifact",
              "Container ký + mã hóa; ghi nguyên tử; từ chối ghi đè; giới hạn kích thước đọc",
              "Chỉ có khóa ghi trong cùng tiến trình; hai bản ứng dụng cùng mở một két vẫn chưa được chặn"],
             ["TB-4 · Lõi kiểm toán ↔ cây webview",
              "(thời điểm biên dịch)",
              "Crate `desktop` bị loại khỏi workspace; `cargo deny`/`audit` chỉ gác phần lõi",
              "Cây phụ thuộc webview không nằm dưới cổng kiểm tra giấy phép, chỉ có quét riêng"],
         ], [3.4, 4.4, 4.6, 3.8], 10),
    ]

    # ============================================= 4. Thiet ke kien truc
    B += [
        ("h2", "4. Thiết kế kiến trúc hệ thống"),

        ("h3", "4.1. Phong cách kiến trúc và mô hình phân tầng"),
        ("p", "Hệ thống được xây dựng theo phong cách **khối một mảnh có mô-đun**, kết hợp với kiểu cổng "
              "và bộ điều hợp tại lõi mật mã cùng cơ chế tiêm phụ thuộc xuyên suốt. Việc chọn khối một "
              "mảnh thay vì kiến trúc phân tán là hiển nhiên đối với một ứng dụng máy tính để bàn ngoại "
              "tuyến; điều đáng bàn hơn là cách khối đó được phân chia bên trong."),
        ("p", "Ý tưởng trung tâm là tách **hợp đồng** khỏi **hiện thực**. Một crate riêng, hoàn toàn "
              "không chứa bất kỳ thuật toán nào, định nghĩa các trait mô tả năng lực mật mã cần có cùng "
              "các kiểu giá trị đi qua chúng. Các crate nghiệp vụ được viết **tổng quát trên các trait "
              "đó** chứ không gọi trực tiếp thư viện nào. Bộ điều hợp cụ thể chỉ được lắp vào tại một "
              "điểm duy nhất gọi là gốc lắp ghép."),
        ("p", "Lợi ích của cách tổ chức này là rất cụ thể chứ không thuần túy hình thức. Thứ nhất, crate "
              "nghiệp vụ của két có đồ thị phụ thuộc **hoàn toàn không chứa FFI**, nghĩa là nó biên dịch "
              "và kiểm thử được trên một máy không có trình biên dịch C. Thứ hai, toàn bộ vòng đời của "
              "két có thể được kiểm thử đầu-cuối bằng một bộ mã hóa tải trọng giả lập trong bộ nhớ, "
              "không cần tới nhị phân age — điều này giải thích vì sao bộ kiểm thử của dự án chạy được "
              "trên máy không cài age. Thứ ba, việc thay thế một nguyên thủy trong tương lai chỉ tác "
              "động tới bộ điều hợp và gốc lắp ghép."),
        ("fig", "Hinh-2-04-kien-truc-phan-tang",
         "Hình 2.4. Kiến trúc phân tầng của hệ thống từ L0 đến L5"),
        ("p", "Hình 2.4 thể hiện sáu tầng. Tầng L0 nằm dưới cùng và được mọi tầng khác dùng chung: đó là "
              "crate chứa các đối tượng truyền dữ liệu và bảng mã lỗi. Việc đặt nó ở đáy chứ không ở "
              "đỉnh là có chủ đích: hợp đồng lỗi và hợp đồng dữ liệu là thứ mọi tầng đều phải tuân theo."),
        ("p", "Tầng L1 gồm crate ABI và hai crate FFI. Tầng L2 gồm các bộ điều hợp cụ thể. Tầng L3 là "
              "tầng nghiệp vụ với sáu crate tương ứng sáu mô-đun chức năng. Tầng L4 là tầng ứng dụng "
              "chứa gốc lắp ghép và năm bề mặt lệnh. Tầng L5 là vỏ giao diện, và như đã nêu, nó nằm "
              "ngoài workspace."),
        ("p", "Một quy tắc phụ thuộc được tuân thủ nghiêm ngặt: các tầng chỉ phụ thuộc xuống dưới, không "
              "bao giờ lên trên và không bao giờ ngang hàng giữa các crate nghiệp vụ. Sáu crate ở tầng "
              "L3 hoàn toàn không biết tới nhau; chúng chỉ gặp nhau tại gốc lắp ghép. Nhờ vậy việc thêm "
              "một mô-đun mới là một thao tác **cộng thêm** — thêm một crate nghiệp vụ, thêm một bề mặt "
              "lệnh, thêm một nhóm màn hình — chứ không phải sửa đổi phần đã có."),

        ("h3", "4.2. Đồ thị phụ thuộc giữa các crate"),
        ("p", "Kiến trúc phân tầng ở trên mô tả ý định thiết kế; đồ thị phụ thuộc thực tế mới là bằng "
              "chứng cho thấy ý định đó được tuân thủ. Hình 2.5 trình bày đồ thị phụ thuộc được tái dựng "
              "từ các tệp khai báo của từng crate."),
        ("fig", "Hinh-2-05-do-thi-phu-thuoc-crate",
         "Hình 2.5. Đồ thị phụ thuộc giữa các crate trong bản dựng sản phẩm"),
        ("p", "Hai chi tiết trong hình đáng được phân tích kỹ. Thứ nhất, crate của két **không** có cạnh "
              "nối tới crate bộ điều hợp trong đồ thị sản phẩm; nó chỉ nối tới crate ABI. Crate bộ điều "
              "hợp xuất hiện trong tệp khai báo của nó nhưng nằm ở mục phụ thuộc dành cho kiểm thử — tức "
              "là nó chỉ được nạp khi chạy `cargo test`. Đây chính là cơ chế cho phép crate nghiệp vụ "
              "vừa giữ được tính độc lập với nền tảng, vừa có bộ kiểm thử chạy trên nguyên thủy thật."),
        ("p", "Thứ hai, crate điều khiển tiến trình con age chỉ được nối vào tại gốc lắp ghép. Không một "
              "crate nghiệp vụ nào phụ thuộc trực tiếp vào nó. Nhờ vậy, phụ thuộc vào một chương trình "
              "ngoài — vốn là dạng phụ thuộc “nặng” nhất về mặt kiểm toán và khả chuyển — được giới hạn "
              "trong một điểm duy nhất và có thể thay thế được."),
        ("p", "Một điều dễ bị hiểu nhầm cần đính chính: đã từng có nhận định cho rằng crate giấu tin và "
              "crate mã QR phụ thuộc vào crate dịch vụ mức tệp. Việc đối chiếu tệp khai báo cho thấy điều "
              "này **không đúng**: crate giấu tin chỉ phụ thuộc ABI, bộ điều hợp và crate DTO; crate mã "
              "QR chỉ phụ thuộc crate DTO. Crate dịch vụ mức tệp được tiêu thụ duy nhất bởi gốc lắp ghép. "
              "Đồ thị trong Hình 2.5 dùng đúng các cạnh có thật."),
        ("tbl", "Bảng 2.4. Danh mục crate, tầng, trách nhiệm và chính sách mã không an toàn",
         ["Crate", "Tầng", "Trách nhiệm chính", "Mã không an toàn"],
         [
             ["`sv-types`", "L0", "DTO cho giao diện và bảng mười hai mã lỗi; tuyệt đối không chứa bí mật", "Cấm"],
             ["`sv-crypto-traits`", "L1", "ABI: sáu trait, các kiểu giá trị bí mật và không bí mật, định danh thuật toán", "Cấm tuyệt đối"],
             ["`sv-sys-sodium`", "L1", "Bọc an toàn quanh libsodium: ký, băm BLAKE2b, secretbox", "Cho phép (FFI)"],
             ["`sv-sys-sss`", "L1", "FFI tới thư viện Shamir; hàm sinh ngẫu nhiên nối vào nguồn hệ điều hành", "Cho phép (FFI)"],
             ["`sv-crypto`", "L2", "Bộ điều hợp cụ thể, bọc khóa bằng secretbox, chính sách tham số Argon2id", "Cấm tuyệt đối"],
             ["`sv-age`", "L2", "Bộ điều hợp mã hóa tệp trên tiến trình con age đã ghim băm", "Không có"],
             ["`sv-core`", "L3", "Định dạng và khung container .svault, phân cấp khóa, hợp đồng dịch vụ, bảng lỗi", "Cấm"],
             ["`sv-platform`", "L3", "Dịch vụ mức tệp độc lập với két: băm, ký, mã hóa, chia sẻ bí mật", "Cấm"],
             ["`sv-stego`", "L3", "Giấu tin trong ảnh theo nguyên tắc mã hóa rồi nhúng, kèm bảng dò", "Cấm"],
             ["`sv-meta`", "L3", "Xem, xóa, so sánh siêu dữ liệu qua tiến trình con ExifTool đã ghim băm", "Cấm"],
             ["`sv-qr`", "L3", "Bộ mã hóa và giải mã QR thuần Rust, chỉ làm nhiệm vụ vận chuyển", "Cấm"],
             ["`sv-watermark`", "L3", "Thủy vân vô hình, có khóa, dễ vỡ dựa trên MAC theo khối", "Cấm"],
             ["`sv-app`", "L4", "Gốc lắp ghép, năm bề mặt lệnh, kiểu mật khẩu ở biên, ánh xạ lỗi", "Cấm"],
             ["`secure-vault-desktop`", "L5", "Vỏ Tauri, ba mươi tám hàm lệnh, kịch bản dựng, giao diện tĩnh", "Cấm"],
         ], [3.4, 1.2, 9.2, 2.4], 10),

        ("h3", "4.3. Kiến trúc triển khai và thực thi"),
        ("p", "Ở mức triển khai, hệ thống là một tiến trình duy nhất chạy trên máy người dùng, không yêu "
              "cầu quyền quản trị và không đăng ký bất kỳ dịch vụ nền nào. Hình 2.6 mô tả cấu trúc thực "
              "thi thực tế."),
        ("fig", "Hinh-2-06-kien-truc-trien-khai",
         "Hình 2.6. Kiến trúc triển khai và thực thi trên máy người dùng"),
        ("p", "Trong tiến trình ứng dụng có hai vùng thực thi: luồng webview chịu trách nhiệm hiển thị và "
              "thu nhận thao tác, và lõi Rust chịu trách nhiệm xử lý. Cần lưu ý rằng khung ứng dụng điều "
              "phối các lệnh trên một nhóm luồng, nghĩa là **hai lệnh có thể chạy đồng thời**. Đây là "
              "một chi tiết thực thi có hệ quả an toàn dữ liệu trực tiếp: thao tác thêm tệp vào két là "
              "một chu trình đọc — sửa — ghi trên toàn bộ container, nên hai lệnh đồng thời có thể làm "
              "mất cập nhật. Hệ quả này đã được kiểm chứng bằng thực nghiệm và dẫn tới việc bổ sung khóa "
              "ghi theo từng két, như sẽ trình bày ở Chương 4."),
        ("p", "Năm trạng thái quản lý được đăng ký khi khởi động, mỗi trạng thái tương ứng một bề mặt "
              "lệnh. Trạng thái của két là trạng thái duy nhất có bộ nhớ phiên; bốn trạng thái còn lại "
              "hoàn toàn không lưu trạng thái giữa các lệnh. Việc phần lớn hệ thống không lưu trạng thái "
              "là một thuộc tính an toàn có giá trị: nó thu hẹp đáng kể vùng có thể chứa bí mật."),
        ("p", "Các nhị phân ngoài được đóng gói như tài nguyên của gói cài chứ không phải phụ thuộc hệ "
              "thống. Điều này có hai hệ quả trái chiều. Về mặt tích cực, người dùng không phải cài đặt "
              "gì thêm và hệ thống biết chính xác nó đang chạy phiên bản nào. Về mặt tiêu cực, gói cài "
              "trở nên lớn hơn và trách nhiệm cập nhật các nhị phân đó chuyển sang nhà phát triển."),

        ("h3", "4.4. Mô hình tương tác giữa các thành phần"),
        ("p", "Để cụ thể hóa cách các tầng phối hợp, phần này phân tích một thao tác đại diện: thêm một "
              "tệp vào két. Đây là thao tác phức tạp nhất trong hệ thống vì nó chạm tới hầu hết các tầng "
              "và vì nó là một chu trình đọc — sửa — ghi trên toàn bộ container."),
        ("fig", "Hinh-2-07-tuan-tu-them-tep",
         "Hình 2.7. Biểu đồ tuần tự quá trình thêm một tệp vào két"),
        ("p", "Hình 2.7 cho thấy mười tám bước, trong đó thứ tự có ý nghĩa an toàn ở nhiều chỗ. Bước một "
              "kiểm tra kích thước tệp nguồn **bằng siêu dữ liệu hệ thống tệp, trước khi đọc bất kỳ byte "
              "nào**; nhờ vậy một tệp nhiều gigabyte bị từ chối mà không hề gây cấp phát bộ nhớ. Bước hai "
              "lấy khóa ghi theo đường dẫn két đã chuẩn hóa và giữ nó suốt toàn bộ chu trình."),
        ("p", "Bước ba là điểm mấu chốt về mặt an toàn: container được giải mã cấu trúc và **chữ ký được "
              "xác minh trước mọi thao tác liên quan tới khóa**. Chỉ sau khi container được chứng minh "
              "là chưa bị sửa đổi, hệ thống mới dẫn xuất khóa bọc và cố gắng mở bọc danh tính age ở bước "
              "năm. Thất bại ở bước năm chính là tín hiệu “sai mật khẩu”, nhưng vì bước ba đã lọc hết các "
              "trường hợp tệp hỏng, tín hiệu này không thể bị lẫn với tín hiệu về tính toàn vẹn."),
        ("p", "Các bước từ chín đến mười hai là phần ghi lại. Điều đáng chú ý là toàn bộ kho lưu trữ được "
              "đóng gói lại, mã hóa lại và ký lại **mỗi lần thêm một tệp**, kể cả khi tệp mới rất nhỏ so "
              "với các tệp đã có. Đây là hệ quả trực tiếp của mô hình một khối tải trọng duy nhất — mô "
              "hình cho phép giấu hoàn toàn danh mục tệp bên trong két, nhưng phải trả giá bằng chi phí ghi tỉ lệ với "
              "kích thước tổng của két thay vì kích thước tệp mới. Đây là một sự đánh đổi có ý thức giữa "
              "tính bí mật của siêu dữ liệu và hiệu năng ghi."),
        ("p", "Bước cuối cùng trả về một đối tượng mô tả tệp vừa thêm, gồm định danh, tên, kích thước và "
              "vân tay nội dung. Toàn bộ các trường này đều không bí mật, phù hợp với bất biến “không có "
              "bí mật nào đi qua biên giao tiếp”."),
    ]

    # ============================================= 5. Kien truc mat ma
    B += [
        ("h2", "5. Thiết kế kiến trúc mật mã"),

        ("h3", "5.1. Ngăn xếp nguyên thủy: từ cổng tới nền tảng"),
        ("p", "Kiến trúc mật mã của hệ thống được tổ chức thành ba lớp: mục đích sử dụng, cổng trừu "
              "tượng và nền tảng thực thi. Việc tách ba lớp này giúp trả lời rành mạch một câu hỏi mà "
              "nhiều tài liệu thiết kế trả lời mập mờ: **thuật toán nào đang thực sự chạy cho việc gì**."),
        ("fig", "Hinh-2-08-ngan-xep-nguyen-thuy",
         "Hình 2.8. Ngăn xếp nguyên thủy mật mã: mục đích, cổng, bộ điều hợp và nền tảng"),
        ("p", "Hình 2.8 liệt kê sáu hàng tương ứng sáu mục đích. Một quan sát quan trọng: **không có hàng "
              "nào mà cột nền tảng ghi tên dự án**. Toàn bộ phép tính mật mã đều được ủy thác cho thư "
              "viện bên ngoài. Phần logic do dự án viết chỉ gồm cách sắp xếp byte của định dạng chữ ký "
              "và cách xây dựng chuỗi ngữ cảnh dẫn xuất khóa — cả hai đều là mã hóa định dạng và tách "
              "miền, không phải thiết kế thuật toán."),
        ("p", "Hai khối bổ sung ở đáy hình cũng đáng chú ý. Khối chính sách tham số thể hiện việc dự án "
              "tách bạch giữa “tham số hợp lệ về cấu trúc” và “tham số đủ mạnh theo chính sách”, đồng "
              "thời cung cấp cơ chế hiệu chỉnh theo phần cứng thật. Khối bộ thuật toán thể hiện một "
              "quyết định thiết kế mà mục 5.4 sẽ phân tích kỹ."),
        ("tbl", "Bảng 2.5. Nguyên thủy mật mã sử dụng và vai trò trong hệ thống",
         ["Mục đích", "Nguyên thủy", "Tham số / định dạng", "Nơi sử dụng"],
         [
             ["Dẫn xuất khóa từ mật khẩu", "Argon2id (phiên bản 0x13)",
              "Mặc định 256 MiB / 3 vòng / 1 luồng; sàn 19 456 KiB / 2 vòng / 1 luồng",
              "Mở khóa két; mã hóa tệp SVENC; cất khóa ký; khóa giấu tin; khóa thủy vân"],
             ["Băm nội dung", "BLAKE3", "Đầu ra 32 byte; có chế độ truyền dòng",
              "Vân tay tệp; băm từng mục; ghim băm nhị phân; ràng buộc mảnh với tải trọng"],
             ["MAC có khóa", "BLAKE3 chế độ khóa", "Khóa 32 byte, đầu ra 32 byte", "Nhãn từng khối trong thủy vân"],
             ["Dẫn xuất khóa con", "BLAKE3 chế độ dẫn xuất", "Chuỗi ngữ cảnh có phiên bản, ràng buộc định danh",
              "Khóa bọc của két; khóa tệp SVENC; khóa tải trọng chia sẻ bí mật"],
             ["Bọc bí mật (AEAD)", "XSalsa20-Poly1305 (`crypto_secretbox`)",
              "Nonce 24 byte ngẫu nhiên; thẻ 16 byte; **không hỗ trợ dữ liệu liên kết**",
              "Bọc danh tính age và khóa ký; niêm phong SVENC/SVKEY; tải trọng chia sẻ; tải trọng giấu tin"],
             ["Mã hóa tải trọng lớn", "age v1 (X25519 + ChaCha20-Poly1305)",
              "Tiến trình con đã ghim băm, có hạn giờ 120 giây", "Toàn bộ tải trọng của két"],
             ["Chữ ký số", "Ed25519 ở định dạng minisign",
              "Tiền băm BLAKE2b-512; có chữ ký toàn cục ràng buộc chú thích tin cậy",
              "Ký container; ký tệp độc lập"],
             ["Chia sẻ bí mật", "Shamir trên GF(2⁸) (thư viện `sss` hazmat)",
              "Mảnh 33 byte, byte đầu là hoành độ", "Chia khóa chủ của két; chia khóa DEK ở tầng dịch vụ"],
             ["Sinh số ngẫu nhiên", "Nguồn của hệ điều hành qua `getrandom`",
              "Không có bộ sinh giả ngẫu nhiên trong tiến trình cho vật liệu khóa",
              "UUID, muối, nonce, định danh phiên, DEK, định danh nhóm"],
         ], [3.2, 3.4, 5.0, 4.6], 10),
        ("p", "Một điểm cần nhấn mạnh trong bảng trên là dòng về nguồn ngẫu nhiên. Toàn bộ vật liệu khóa "
              "và mọi giá trị dùng một lần đều được lấy trực tiếp từ nguồn của hệ điều hành, **không** "
              "thông qua bất kỳ bộ sinh giả ngẫu nhiên nội bộ nào. Ngay cả hàm sinh ngẫu nhiên bên trong "
              "thư viện C của lược đồ Shamir cũng đã được thay thế bằng một hàm nối vào nguồn hệ điều "
              "hành. Đây là một quyết định đúng đắn vì bộ sinh giả ngẫu nhiên tự chế là một trong những "
              "nguồn lỗi phổ biến nhất trong phần mềm mật mã."),
        ("p", "Cần bổ sung một ghi nhận về tính nhất quán: bộ sinh giả ngẫu nhiên duy nhất do dự án tự "
              "xây dựng là bộ sinh dùng để tính lịch hoán vị vị trí nhúng trong mô-đun giấu tin. Bộ sinh "
              "này chạy BLAKE3 ở chế độ đếm và được **cố ý** gieo từ một giá trị công khai. Tài liệu của "
              "mô-đun nêu rõ lý do: vị trí nhúng không phải là ranh giới an toàn, toàn bộ tính bí mật nằm "
              "ở tầng AEAD phía trước, nên bộ sinh này không cần và không được coi là một nguồn ngẫu "
              "nhiên mật mã."),

        ("h3", "5.2. Phân cấp khóa của két an toàn"),
        ("p", "Phân cấp khóa là phần thiết kế mật mã trung tâm của mô-đun két. Hình 2.9 trình bày toàn bộ "
              "phân cấp từ mật khẩu tới các bí mật cuối cùng."),
        ("fig", "Hinh-2-09-phan-cap-khoa",
         "Hình 2.9. Phân cấp khóa của két an toàn và cơ chế bọc khóa theo trường"),
        ("p", "Phân cấp gồm ba mức rõ rệt. Mức thứ nhất là **khóa chủ**, thu được bằng cách chạy Argon2id "
              "trên mật khẩu với muối và tham số lấy từ header. Bất biến quan trọng nhất của toàn bộ "
              "thiết kế nằm ở đây: khóa chủ **không bao giờ được ghi ra đĩa dưới bất kỳ hình thức nào**, "
              "kể cả ở dạng đã mã hóa. Nó tồn tại trong một cấu trúc dữ liệu tự xóa khi hủy, được giữ "
              "trong bảng phiên và biến mất khi phiên bị khóa lại."),
        ("p", "Mức thứ hai là hai **khóa bọc**, mỗi khóa dành cho một loại bí mật. Chúng được dẫn xuất "
              "trực tiếp từ khóa chủ bằng hàm dẫn xuất khóa của BLAKE3, với chuỗi ngữ cảnh theo văn phạm "
              "`secure-vault/v<phiên bản bộ thuật toán>/wrap/<nhãn trường>:<UUID dạng hex>`. Ba thành "
              "phần của chuỗi này đều có vai trò riêng: phần phiên bản cho phép thay đổi toàn bộ hệ khóa "
              "trong tương lai bằng một lần tăng số; phần nhãn trường bảo đảm hai bí mật không dùng chung "
              "khóa; phần định danh két bảo đảm khóa không dùng lại được cho két khác."),
        ("p", "Mức thứ ba là hai **bí mật thực sự**: danh tính age dùng để giải mã tải trọng, và khóa ký "
              "Ed25519 dùng để ký container. Cả hai đều được cất trong header ở dạng đã bọc bằng AEAD, "
              "và cả hai đều chỉ được mở bọc **tạm thời trong phạm vi một thao tác** rồi bị hủy ngay. "
              "Điều này có nghĩa là ngay cả khi két đang mở, hai bí mật này cũng không thường trú trong "
              "bộ nhớ — chỉ có khóa chủ mới thường trú."),
        ("p", "Nhánh bên trái của hình thể hiện đường sao lưu khóa: khóa chủ có thể được chia thành n "
              "mảnh với ngưỡng k. Cần nhấn mạnh rằng các mảnh **không bao giờ được lưu trong két**; két "
              "chỉ ghi lại chính sách (n và k) như một thông tin siêu dữ liệu không bí mật, còn bản thân "
              "các mảnh là trách nhiệm bảo quản của người dùng."),

        ("h3", "5.3. Cơ chế bọc khóa và ý nghĩa an toàn của ràng buộc ngữ cảnh"),
        ("p", "Cần phân tích kỹ vì sao cơ chế ràng buộc ngữ cảnh lại là thành phần chịu lực của thiết kế. "
              "Hàm AEAD được dùng để bọc khóa không hỗ trợ dữ liệu liên kết, nghĩa là không có cách trực "
              "tiếp nào để ràng buộc khối bản mã vào ngữ cảnh của nó. Nếu chỉ dùng một khóa bọc duy nhất, "
              "hai kịch bản tấn công sau đây sẽ không bị phát hiện."),
        ("p", "**Kịch bản cấy ghép giữa các két.** Kẻ tấn công lấy khối bí mật đã bọc từ két của nạn nhân "
              "và ghi đè vào két của chính mình, hy vọng dùng mật khẩu của mình để mở ra bí mật của nạn "
              "nhân. Với ràng buộc ngữ cảnh, việc này thất bại vì hai lý do độc lập: khóa chủ khác nhau, "
              "và định danh két trong chuỗi ngữ cảnh cũng khác nhau."),
        ("p", "**Kịch bản nhầm lẫn trường.** Kẻ tấn công hoán đổi vị trí hai khối đã bọc trong cùng một "
              "két, khiến hệ thống hiểu nhầm khóa ký là danh tính age hoặc ngược lại. Đây là một họ tấn "
              "công thực sự tồn tại trong các giao thức mật mã, thường dẫn tới việc dùng lại vật liệu "
              "khóa cho mục đích không dự kiến. Với ràng buộc theo nhãn trường, hai khối được bọc bằng "
              "hai khóa khác nhau, nên phép hoán đổi làm thẻ xác thực thất bại ngay lập tức."),
        ("p", "Cả hai thuộc tính này đều được xác nhận bằng kiểm thử tự động trong mã nguồn, với các hàm "
              "kiểm thử kiểm tra rằng khóa dẫn xuất cho két A không mở được khối bọc của két B, và khóa "
              "dẫn xuất cho trường ký không mở được khối bọc của trường danh tính."),
        ("p", "Ở đây cần ghi nhận trung thực một hạn chế đã được dự án nêu ra: cơ chế ràng buộc hiện nay "
              "là **gián tiếp**, thông qua khóa, chứ không phải trực tiếp thông qua dữ liệu liên kết. Dự "
              "án ghi nhận việc chuyển sang một AEAD có hỗ trợ dữ liệu liên kết là một cải tiến đã hoãn "
              "lại, và đánh giá mức độ là “phòng thủ theo chiều sâu bị hoãn, không phải lỗ hổng khai "
              "thác được”. Nhận định đó có cơ sở, vì tính chất bảo vệ vẫn được duy trì; điều bị mất là "
              "một lớp dự phòng nếu cơ chế tách miền vì lý do nào đó bị suy yếu."),

        ("h3", "5.4. Bộ thuật toán đóng và ba trục phiên bản"),
        ("p", "Một quyết định thiết kế đáng chú ý là cách hệ thống ghi nhận danh tính thuật toán trên "
              "đĩa. Thay vì lưu từng ô thuật toán riêng biệt — một ô cho hàm dẫn xuất khóa, một ô cho "
              "hàm băm, một ô cho AEAD và cứ thế — header chỉ lưu **một định danh bộ thuật toán duy "
              "nhất**, là một kiểu liệt kê đóng hiện chỉ có một giá trị."),
        ("p", "Lợi ích an toàn của cách làm này rất rõ ràng: các tổ hợp thuật toán không hợp lệ trở nên "
              "**không biểu diễn được**, và không tồn tại bất kỳ cơ chế thương lượng thuật toán nào để "
              "kẻ tấn công có thể hạ cấp. Lịch sử các giao thức bảo mật cho thấy tấn công hạ cấp là một "
              "trong những họ tấn công dai dẳng nhất, và nguyên nhân gốc thường chính là sự linh hoạt "
              "quá mức trong việc chọn thuật toán."),
        ("p", "Đi kèm với quyết định đó là việc tách ba **trục phiên bản** độc lập. Trục thứ nhất là "
              "phiên bản hợp đồng giao tiếp giữa giao diện và lõi. Trục thứ hai là phiên bản cấu trúc "
              "container trên đĩa. Trục thứ ba là phiên bản bộ thuật toán, đồng thời là thành phần của "
              "chuỗi ngữ cảnh dẫn xuất khóa. Ba trục này thay đổi vì ba lý do khác nhau và với ba hệ quả "
              "khác nhau: đổi trục thứ nhất buộc phải cập nhật giao diện; đổi trục thứ hai làm các bản "
              "cũ không đọc được tệp mới; còn đổi trục thứ ba thì **thay đổi mọi khóa bọc** và bắt buộc "
              "phải có một quy trình chuyển đổi mở-bằng-cũ rồi bọc-lại-bằng-mới cho các két đã tồn tại."),
        ("p", "Việc gộp ba trục này làm một — như nhiều hệ thống vẫn làm — sẽ dẫn tới hoặc là tăng phiên "
              "bản một cách vô nghĩa, hoặc là bỏ sót một thay đổi có hệ quả nghiêm trọng. Cách tách ba "
              "trục thể hiện một mức độ chín muồi nhất định trong tư duy thiết kế định dạng."),
    ]

    # ================================================ 6. Quy trinh xu ly
    B += [
        ("h2", "6. Thiết kế quy trình xử lý dữ liệu"),

        ("h3", "6.1. Quy trình mã hóa và niêm phong két"),
        ("p", "Đường ghi của két được kích hoạt trong ba tình huống: tạo két mới, thêm một tệp, và đổi "
              "mật khẩu. Cả ba đều quy về cùng một chuỗi thao tác, được trình bày ở Hình 2.10."),
        ("fig", "Hinh-2-10-quy-trinh-niem-phong",
         "Hình 2.10. Quy trình mã hóa và niêm phong két theo đường ghi"),
        ("p", "Chuỗi bắt đầu bằng việc đóng gói toàn bộ danh sách tệp thành một khối byte có cấu trúc "
              "gồm ba phần: độ dài thư mục, thư mục ở dạng CBOR, và vùng byte nội dung các tệp nối tiếp "
              "nhau. Điểm cần nhấn mạnh là **thư mục nằm bên trong khối sẽ được mã hóa**, chứ không nằm "
              "trong header. Đây là lựa chọn quyết định tính bí mật của siêu dữ liệu."),
        ("p", "Khối đóng gói sau đó được mã hóa thành một khối mã age duy nhất. Việc dùng đúng **một** "
              "khối thay vì mã hóa từng tệp riêng có hai hệ quả. Hệ quả tích cực là kẻ tấn công không "
              "suy ra được ranh giới giữa các tệp, do đó không biết được số lượng và kích thước từng tệp. "
              "Hệ quả tiêu cực là mọi thay đổi dù nhỏ cũng buộc phải mã hóa lại toàn bộ."),
        ("p", "Phần tiếp theo là cơ chế **gốc ràng buộc**. Hệ thống tính hai giá trị băm độc lập: một cho "
              "toàn bộ phần đầu tệp gồm chuỗi nhận dạng, phiên bản, độ dài header và chính header; một "
              "cho phần tải trọng. Hai giá trị này được ghép lại và băm thêm một lần nữa để tạo ra gốc "
              "ràng buộc, và **chính gốc ràng buộc mới là thứ được ký**, chứ không phải toàn bộ tệp."),
        ("p", "Thiết kế này giải quyết cùng lúc ba vấn đề. Thứ nhất, một chữ ký duy nhất bảo vệ được cả "
              "header lẫn tải trọng. Thứ hai, vì hai giá trị băm thành phần **được tính lại mỗi lần đọc "
              "và không được lưu trong tệp**, không tồn tại cơ hội cho kẻ tấn công ghép header của tệp "
              "này với tải trọng của tệp khác — bất kỳ sự ghép nào cũng làm gốc ràng buộc thay đổi. Thứ "
              "ba, phần đuôi tệp chỉ chứa duy nhất chữ ký, giữ cho định dạng đơn giản."),
        ("p", "Bước cuối cùng là ghi ra đĩa theo cơ chế nguyên tử: ghi vào một tệp tạm nằm **cùng thư "
              "mục** với tệp đích, đồng bộ xuống thiết bị lưu trữ, rồi đổi tên đè lên tệp đích. Yêu cầu "
              "cùng thư mục là bắt buộc để phép đổi tên có tính nguyên tử ở mức hệ thống tệp. Kết quả là "
              "một sự cố mất điện giữa chừng không bao giờ để lại một tệp két bị ghi dở."),

        ("h3", "6.2. Quy trình mở khóa và thứ tự các cổng kiểm tra"),
        ("p", "Nếu đường ghi là nơi thể hiện thiết kế định dạng, thì đường đọc là nơi thể hiện thiết kế "
              "an toàn. Hình 2.11 trình bày toàn bộ chuỗi cổng kiểm tra."),
        ("fig", "Hinh-2-11-quy-trinh-mo-khoa",
         "Hình 2.11. Quy trình mở khóa và thứ tự các cổng kiểm tra"),
        ("p", "Chuỗi gồm sáu cổng nối tiếp. Cổng thứ nhất giới hạn kích thước tệp được đọc, dựa trên siêu "
              "dữ liệu chứ không phải bằng cách đọc thử. Cổng thứ hai kiểm tra chuỗi nhận dạng và phiên "
              "bản định dạng; thất bại ở đây cho ra hai kết quả khác nhau và cả hai đều **không bí mật**: "
              "“đây không phải tệp két” hoặc “đây là tệp két nhưng thuộc phiên bản không hỗ trợ”."),
        ("p", "Cổng thứ ba là cổng chữ ký, và đây là cổng có ý nghĩa kiến trúc lớn nhất. Nó xác minh chữ "
              "ký trên gốc ràng buộc mà **hoàn toàn không sử dụng mật khẩu**. Nhờ vậy, kết quả của cổng "
              "này không mang bất kỳ thông tin nào về mật khẩu, và ngược lại, mọi tệp hỏng hoặc bị sửa "
              "đều bị loại bỏ trước khi mật khẩu được đưa vào sử dụng."),
        ("p", "Cổng thứ tư kiểm tra tham số chi phí của hàm dẫn xuất khóa lấy từ header. Vị trí của cổng "
              "này rất đáng chú ý: nó nằm **sau** cổng chữ ký nhưng **trước** khi hàm dẫn xuất khóa được "
              "chạy. Điều này phản ánh một nhận thức tinh tế — ngay cả một tệp két có chữ ký hợp lệ cũng "
              "có thể là tệp do kẻ tấn công tạo ra với tham số cực đại nhằm gây cạn kiệt tài nguyên, bởi "
              "vì kẻ tấn công hoàn toàn có thể tự tạo một két và tự ký nó."),
        ("p", "Cổng thứ năm là phép chạy hàm dẫn xuất khóa, và cổng thứ sáu là phép mở bọc danh tính age "
              "— cổng tín nhiệm thực sự. Thất bại ở cổng thứ sáu chính là “sai mật khẩu”. Cần chú ý rằng "
              "hệ thống **không** lưu bất kỳ giá trị kiểm tra nào của mật khẩu; việc mật khẩu có đúng hay "
              "không được xác định gián tiếp thông qua việc thẻ xác thực AEAD có hợp lệ hay không. Đây là "
              "cách làm đúng, vì nó không tạo ra thêm bất kỳ dữ liệu nào có thể bị tấn công ngoại tuyến."),
        ("p", "Đường khôi phục bằng mảnh đi theo đúng khung này, chỉ khác ở chỗ khóa chủ được tái tạo từ "
              "các mảnh thay vì từ mật khẩu. Điều quan trọng là **cổng thứ sáu vẫn giữ nguyên**: cả hai "
              "đường đều kết thúc bằng cùng một phép mở bọc, nên chúng thất bại theo cùng một cách và "
              "trả về cùng một mã lỗi. Đây là lý do vì sao mã lỗi chứng thực hợp nhất được cả hai trường "
              "hợp mà không cần thêm cơ chế nào."),

        ("h3", "6.3. Quy trình đổi mật khẩu"),
        ("p", "Quy trình đổi mật khẩu minh họa rõ nhất lợi ích của phân cấp khóa. Hệ thống mở bọc hai bí "
              "mật bằng khóa chủ cũ, sinh một muối mới, dẫn xuất khóa chủ mới từ mật khẩu mới, bọc lại "
              "hai bí mật bằng các khóa bọc mới, rồi ký lại và ghi lại container. **Phần tải trọng hoàn "
              "toàn không bị mã hóa lại**: nó được chuyển nguyên vẹn từ container cũ sang container mới."),
        ("p", "Hệ quả thực tiễn rất đáng kể: đổi mật khẩu của một két chứa nhiều gigabyte dữ liệu có chi "
              "phí gần như bằng đổi mật khẩu của một két rỗng, vì khối lượng công việc mật mã chỉ là hai "
              "phép bọc trên vài chục byte cộng với một lần chạy hàm dẫn xuất khóa. Cần lưu ý rằng "
              "container vẫn phải được ghi lại toàn bộ vì chữ ký phải được tính lại, nhưng đó là chi phí "
              "vào-ra chứ không phải chi phí mật mã."),
        ("p", "Một chi tiết xử lý đồng thời đáng ghi nhận: sau khi ghi thành công, hệ thống cập nhật khóa "
              "chủ trong phiên đang mở. Nếu phiên đó vừa bị khóa lại bởi một lệnh song song, việc cập "
              "nhật đơn giản là không xảy ra và thao tác vẫn được coi là thành công — điều này đúng, vì "
              "dữ liệu trên đĩa đã được ghi và không còn phiên nào giữ khóa cũ. Nếu có hai lệnh đổi mật "
              "khẩu chạy song song trên cùng một phiên, lệnh thứ hai sẽ thất bại ở phép mở bọc với mã "
              "lỗi chứng thực, chứ không âm thầm làm hỏng trạng thái."),

        ("h3", "6.4. Quy trình chia và khôi phục khóa chủ"),
        ("p", "Quy trình chia khóa chủ yêu cầu một phiên đã mở khóa, vì nó cần chính khóa chủ làm đầu "
              "vào. Khóa chủ được chia thành n mảnh, mỗi mảnh dài 33 byte trong đó byte đầu tiên là hoành "
              "độ. Mỗi mảnh sau đó được đóng vào một phong bì 58 byte gồm chuỗi nhận dạng, phiên bản, "
              "định danh két, chỉ số mảnh, tổng số mảnh, ngưỡng và bản thân mảnh."),
        ("p", "Việc đưa định danh két vào phong bì phục vụ một mục đích rất thực tế: khi người dùng cung "
              "cấp nhầm mảnh của két khác, hệ thống có thể báo lỗi rõ ràng “mảnh này thuộc két khác” thay "
              "vì để phép khôi phục thất bại một cách khó hiểu. Đây là **thông tin không bí mật** nên "
              "việc phân biệt nó không tạo ra oracle."),
        ("p", "Quy trình khôi phục có bốn cổng. Cổng thứ nhất và thứ hai kiểm tra cấu trúc phong bì và "
              "sự khớp định danh két. Cổng thứ ba đếm số mảnh và so với ngưỡng ghi trong header; thiếu "
              "mảnh cho ra một mã lỗi riêng kèm số lượng hiện có và số lượng cần — hoàn toàn không bí "
              "mật, và rất hữu ích cho người dùng. Cổng thứ tư là phép tái tạo khóa chủ, và như đã phân "
              "tích, phép tái tạo này **không tự phát hiện được mảnh sai**; việc kiểm tra thực sự nằm ở "
              "phép mở bọc danh tính age ngay sau đó."),

        ("h3", "6.5. Xử lý lỗi và bảo toàn dữ liệu người dùng"),
        ("p", "Một nguyên tắc được tuân thủ nhất quán trên mọi đường xử lý: **hệ thống không bao giờ phá "
              "hủy dữ liệu có sẵn của người dùng**. Nguyên tắc này được hiện thực hóa bằng ba cơ chế."),
        ("p", "Cơ chế thứ nhất là ghi nguyên tử qua tệp tạm và đổi tên, như đã trình bày. Cơ chế thứ hai "
              "là từ chối ghi đè: mọi thao tác xuất dữ liệu ra tệp — trích xuất tệp khỏi két, giải mã tệp, "
              "ký tệp, xuất mảnh — đều kiểm tra sự tồn tại của tệp đích và trả về một mã lỗi riêng nếu "
              "tệp đã có. Cần ghi nhận rằng cơ chế này **không có ngay từ đầu**: nó được bổ sung sau khi "
              "một chiến dịch kiểm chứng phát hiện thao tác trích xuất âm thầm ghi đè lên tệp có sẵn, như "
              "sẽ trình bày ở Chương 4."),
        ("p", "Cơ chế thứ ba là khóa ghi theo từng két, cũng là kết quả của chiến dịch kiểm chứng đó. "
              "Khóa được lập chỉ mục theo đường dẫn két đã chuẩn hóa, nhờ vậy hai cách viết khác nhau "
              "của cùng một đường dẫn vẫn dùng chung một khóa, trong khi hai két khác nhau vẫn xử lý "
              "song song được. Hạn chế đã biết là khóa này chỉ có hiệu lực **trong cùng một tiến trình**; "
              "hai bản ứng dụng cùng mở một két vẫn có thể xung đột, và việc bổ sung khóa ở mức hệ điều "
              "hành được ghi nhận là một việc còn để ngỏ."),
    ]

    # =================================================== 7. Thiet ke du lieu
    B += [
        ("h2", "7. Thiết kế dữ liệu"),

        ("h3", "7.1. Danh mục định dạng trên đĩa"),
        ("p", "Hệ thống định nghĩa sáu định dạng dữ liệu, tất cả đều tuân theo cùng một quy ước: bắt đầu "
              "bằng một chuỗi nhận dạng dài bốn hoặc sáu byte, tiếp theo là một số phiên bản hai byte "
              "theo thứ tự byte nhỏ trước. Quy ước này cho phép hệ thống từ chối một tệp sai loại hoặc "
              "sai phiên bản với chi phí gần như bằng không, trước khi thực hiện bất kỳ phép tính mật mã "
              "nào."),
        ("tbl", "Bảng 2.6. Danh mục các định dạng dữ liệu trên đĩa",
         ["Định dạng", "Chuỗi nhận dạng", "Kích thước", "Mục đích", "Cơ chế bảo vệ"],
         [
             ["`.svault`", "`SVLT` (4 byte)", "thay đổi", "Container két mã hóa nhiều tệp",
              "age cho tải trọng + secretbox cho khóa + chữ ký Ed25519 trên gốc ràng buộc"],
             ["`.svenc`", "`SVENC\\0` (6 byte)", "header 62 byte + bản mã", "Tệp được mã hóa bằng mật khẩu",
              "Argon2id + secretbox; header ràng buộc qua ngữ cảnh dẫn xuất khóa"],
             ["`.svkey`", "`SVKEY\\0` (6 byte)", "header 62 byte + bản mã", "Khóa ký được cất giữ đã mã hóa",
              "Cùng cơ chế với `.svenc`, khác chuỗi nhận dạng nên không hoán đổi được"],
             ["`.svshare`", "`SVSH` (4 byte)", "58 byte cố định", "Một mảnh khôi phục khóa chủ của két",
              "Bản thân mảnh Shamir; xác thực gián tiếp qua phép mở bọc sau khi tái tạo"],
             ["`.svss` (mảnh)", "`SVSSS\\0` (6 byte)", "92 byte cố định", "Một mảnh của lược đồ chia sẻ độc lập",
              "Chứa vân tay tải trọng để ràng buộc mảnh với đúng tệp tải trọng"],
             ["`.svss` (tải trọng)", "`SVSSP\\0` (6 byte)", "header 33 byte + bản mã", "Tải trọng đã mã hóa bằng DEK",
              "secretbox dưới khóa dẫn xuất có gấp các trường header vào ngữ cảnh"],
             ["`SVSTEG`", "`SVSTEG` (6 byte)", "header 54 byte + bản mã", "Khung dữ liệu nhúng trong ảnh",
              "Argon2id + secretbox; bản thân khung không phải là tệp mà nằm trong mặt bit của ảnh"],
         ], [2.8, 2.6, 2.8, 3.6, 4.4], 9.5),
        ("p", "Riêng mô-đun thủy vân không định nghĩa định dạng nào: nó ghi ra một tệp ảnh PNG hoặc BMP "
              "hoàn toàn bình thường, còn dấu nằm trong mặt bit thấp nhất của các kênh màu. Đây là hệ quả "
              "tất yếu của yêu cầu “vô hình”: nếu có thêm bất kỳ khối dữ liệu nào trong tệp, dấu sẽ không "
              "còn vô hình đối với công cụ phân tích."),

        ("h3", "7.2. Cấu trúc container két"),
        ("p", "Container két là định dạng phức tạp nhất và cũng là nơi tập trung nhiều quyết định thiết "
              "kế nhất. Hình 2.12 trình bày bố cục byte cùng phạm vi bảo vệ của chữ ký."),
        ("fig", "Hinh-2-12-bo-cuc-svault",
         "Hình 2.12. Bố cục byte của container .svault và phạm vi chữ ký"),
        ("p", "Tệp gồm sáu vùng liên tiếp. Bốn vùng đầu là phần khung: chuỗi nhận dạng, phiên bản định "
              "dạng, độ dài header và bản thân header ở dạng CBOR. Vùng thứ năm là tải trọng — một khối "
              "mã age duy nhất. Vùng thứ sáu là phần đuôi chứa chữ ký ở định dạng văn bản của minisign."),
        ("p", "Một chi tiết thiết kế nhỏ nhưng đáng chú ý: header lưu độ dài tải trọng nhưng **không lưu "
              "vị trí bắt đầu** của nó. Lý do là vị trí đó có thể suy ra được từ độ dài header, và nếu "
              "lưu nó thì sẽ tạo ra một quan hệ vòng — vị trí phụ thuộc vào kích thước header, mà kích "
              "thước header lại phụ thuộc vào việc có lưu vị trí hay không. Việc nhận ra và tránh vòng "
              "lặp này là một dấu hiệu của thiết kế định dạng cẩn thận."),
        ("p", "Một chi tiết khác: độ dài header bị giới hạn ở một mebibyte. Con số này lớn hơn nhiều lần "
              "so với kích thước header thực tế, nhưng nó ngăn được kịch bản một tệp độc hại khai báo độ "
              "dài header là bốn tỉ byte và buộc hệ thống cấp phát bộ nhớ trước khi kịp nhận ra sai sót."),
        ("p", "Về phần bên trong tải trọng, sau khi giải mã, khối byte có ba phần: độ dài thư mục ở dạng "
              "số nguyên bốn byte, thư mục ở dạng CBOR, và vùng byte nội dung. Thư mục ghi lại vị trí và "
              "độ dài của từng tệp **trong không gian bản rõ**, tức là các giá trị này chỉ có ý nghĩa sau "
              "khi giải mã. Việc dùng vị trí bản rõ thay vì vị trí bản mã là bắt buộc, vì tải trọng được "
              "mã hóa như một khối liền và không có ranh giới có thể định vị từ bên ngoài."),

        ("h3", "7.3. Mô hình dữ liệu của header"),
        ("p", "Hình 2.13 trình bày chi tiết mô hình dữ liệu của header, trong đó mỗi trường được đánh dấu "
              "là công khai hay là bản mã của một bí mật."),
        ("fig", "Hinh-2-13-mo-hinh-du-lieu-header",
         "Hình 2.13. Mô hình dữ liệu của header CBOR và danh mục tệp"),
        ("p", "Việc phân loại từng trường cho phép trả lời chính xác câu hỏi: một kẻ tấn công có tệp két "
              "trong tay thì biết được những gì? Câu trả lời là: phiên bản định dạng và bộ thuật toán; "
              "định danh của két; hai dấu thời gian; muối và tham số chi phí của hàm dẫn xuất khóa; khóa "
              "công khai của người nhận age; khóa công khai của cặp khóa ký; chính sách khôi phục nếu "
              "có; và tổng độ dài tải trọng. Đó là toàn bộ."),
        ("p", "Đặc biệt, kẻ tấn công **không** biết được: có bao nhiêu tệp trong két, tên của chúng, kích "
              "thước của từng tệp, và thời điểm từng tệp được thêm vào. Toàn bộ các thông tin này nằm "
              "trong danh mục tệp, mà danh mục tệp thì nằm bên trong vùng đã mã hóa."),
        ("p", "Một chi tiết an toàn bổ sung nằm ở cách cấu trúc dữ liệu được khai báo: bộ giải mã CBOR "
              "được cấu hình **từ chối các trường lạ**. Nghĩa là một header chứa thêm bất kỳ khóa nào "
              "không nằm trong lược đồ sẽ bị từ chối ngay ở bước giải mã cấu trúc. Về lý thuyết, chữ ký "
              "đã ngăn được việc thêm trường; nhưng đây chính là tinh thần phòng thủ theo chiều sâu — nếu "
              "vì lý do nào đó phép kiểm chữ ký bị bỏ qua trên một đường mã nào đó, lớp này vẫn còn."),
        ("p", "Cuối cùng, cần ghi nhận một quyết định làm sạch lược đồ mà tài liệu của dự án nêu rõ: "
              "trường chuỗi tự do mô tả tên thuật toán dẫn xuất khóa đã bị **loại bỏ khỏi định dạng trên "
              "đĩa**, vì nó thừa so với thẻ định danh có sẵn trong kiểu dữ liệu tham số và tạo ra khả "
              "năng mâu thuẫn nội tại. Một chuỗi mô tả tương tự vẫn tồn tại nhưng chỉ ở tầng đối tượng "
              "truyền dữ liệu để hiển thị cho người dùng, hoàn toàn không tham gia vào quyết định mật mã "
              "nào."),
    ]

    # ============================================ 8. Thiet ke giao dien
    B += [
        ("h2", "8. Thiết kế giao diện người dùng"),
        ("p", "Thiết kế giao diện của hệ thống tuân theo một nguyên tắc tổ chức khác biệt so với phần lớn "
              "công cụ bảo mật: các chức năng được nhóm theo **mục tiêu của người dùng** chứ không theo "
              "tên thuật toán hay tên mô-đun kỹ thuật. Thanh điều hướng bên trái không có mục nào tên là "
              "“AEAD”, “Shamir” hay “Steganography”; thay vào đó là “Bảo vệ tệp”, “Chứng minh tính xác "
              "thực”, “Sao lưu và khôi phục”, “Kiểm tra và làm sạch”."),
        ("p", "Cách đặt tên này có ý nghĩa an toàn thực sự chứ không chỉ là vấn đề thẩm mỹ. Một người dùng "
              "không hiểu mình đang làm gì sẽ chọn sai công cụ, và trong lĩnh vực bảo mật, chọn sai công "
              "cụ thường tệ hơn không dùng công cụ nào. Chẳng hạn, việc gọi mô-đun giấu tin là “Giấu dữ "
              "liệu trong ảnh” thay vì “Steganography” giúp người dùng hiểu đúng rằng đây là che giấu, "
              "chứ không nhầm tưởng đó là một phương thức mã hóa mạnh hơn."),
        ("p", "Hai quyết định thiết kế giao diện khác cũng liên quan trực tiếp tới an toàn. Thứ nhất, mọi "
              "trường nhập mật khẩu đều **bị xóa nội dung khi người dùng rời màn hình**, để một mật khẩu "
              "đã gõ nhưng chưa gửi đi không nằm lại trong cây tài liệu. Thứ hai, mọi thẻ kết quả của "
              "thao tác trước đều bị ẩn khi chuyển màn hình, để một phán quyết “ĐẠT” của công cụ này "
              "không bị đọc nhầm thành kết quả của công cụ khác — một dạng nhầm lẫn có thể gây hậu quả "
              "nghiêm trọng với các công cụ kiểm tra."),
        ("p", "Giao diện được bản địa hóa hoàn toàn với tiếng Việt là ngôn ngữ mặc định. Điều đáng chú ý "
              "về mặt kiến trúc là **bảng thông điệp lỗi của giao diện được ràng buộc với bảng mã lỗi "
              "của lõi bằng một kiểm thử tự động**: nếu lõi thêm một mã lỗi mới mà giao diện chưa dịch, "
              "hoặc giao diện còn giữ một khóa dịch đã lỗi thời, kiểm thử sẽ thất bại. Đây là một cách "
              "biến một hợp đồng vốn chỉ tồn tại trên giấy thành một hợp đồng được cưỡng chế bởi công cụ."),
    ]

    # =============================================== 9. Kien truc an ninh
    B += [
        ("h2", "9. Thiết kế kiến trúc an ninh nhiều lớp"),

        ("h3", "9.1. Mô hình phòng thủ theo chiều sâu"),
        ("p", "Toàn bộ các cơ chế đã trình bày ở các mục trước có thể được sắp xếp thành một mô hình bảy "
              "lớp, trong đó mỗi lớp che một loại giả thiết có thể sai. Hình 2.14 trình bày mô hình này."),
        ("fig", "Hinh-2-14-phong-thu-chieu-sau",
         "Hình 2.14. Kiến trúc phòng thủ theo chiều sâu bảo vệ dữ liệu người dùng"),
        ("p", "Đọc từ trong ra ngoài, lớp gần dữ liệu nhất là mã hóa khi lưu trữ; lớp tiếp theo là vệ "
              "sinh bí mật trong bộ nhớ; rồi tới toàn vẹn và xuất xứ; an toàn dữ liệu; làm cứng tiến "
              "trình con; kiểm soát tài nguyên; và ngoài cùng là kỷ luật dự án."),
        ("p", "Việc đặt **kỷ luật dự án** làm lớp ngoài cùng không phải là một cách nói hình tượng. Các "
              "biện pháp như cấm mã không an toàn ở phạm vi toàn workspace, nâng mọi cảnh báo phân tích "
              "tĩnh thành lỗi, biên dịch với tệp khóa phiên bản, và chạy hai công cụ kiểm tra chuỗi cung "
              "ứng đều là những cơ chế loại bỏ **cả một họ lỗi** thay vì sửa từng lỗi riêng lẻ. Về mặt "
              "hiệu quả trên một đơn vị công sức, chúng thường vượt trội so với việc rà soát mã thủ công."),
        ("p", "Mô hình lỗi chống dò oracle không xuất hiện như một lớp riêng trong hình vì nó là một "
              "**mối quan tâm cắt ngang**: nó áp lên mọi lớp bằng cách quy định cách các lớp báo cáo thất "
              "bại ra ngoài."),

        ("h3", "9.2. Mô hình lỗi chống dò oracle"),
        ("p", "Hệ thống định nghĩa đúng mười hai mã lỗi, và toàn bộ các loại lỗi nội bộ — vốn phong phú "
              "hơn nhiều — đều được chiếu về mười hai mã này. Hình 2.15 trình bày phép chiếu đó."),
        ("fig", "Hinh-2-15-anh-xa-loi-chong-oracle",
         "Hình 2.15. Ánh xạ lỗi nội bộ sang mã lỗi công khai chống dò oracle"),
        ("p", "Phần bên trên của hình thể hiện nguyên tắc **hội tụ**: mọi thất bại liên quan tới chứng "
              "thực, bất kể xuất phát từ mô-đun nào, đều cho ra cùng một mã. Sai mật khẩu két, sai mảnh "
              "khôi phục, sai mật khẩu tệp mã hóa độc lập, bản mã bị sửa, ảnh không mang dữ liệu ẩn, "
              "khung dữ liệu ẩn bị hỏng — tất cả đều là cùng một câu trả lời."),
        ("p", "Trường hợp của mô-đun giấu tin đáng được phân tích riêng vì nó thể hiện nguyên tắc này ở "
              "mức triệt để nhất. Bốn tình huống hoàn toàn khác nhau — ảnh sạch không mang gì, khung dữ "
              "liệu bị cắt cụt, mật khẩu sai, và sóng mang bị chỉnh sửa — đều trả về cùng một mã. Hệ quả "
              "là kẻ tấn công **thậm chí không xác định được một tấm ảnh có mang dữ liệu ẩn hay không**, "
              "chứ chưa nói tới việc đọc dữ liệu đó. Nếu bốn tình huống này được phân biệt, chính bộ "
              "công cụ sẽ trở thành một máy dò giấu tin hoàn hảo cho kẻ tấn công."),
        ("p", "Phần bên dưới của hình thể hiện nguyên tắc **giữ nguyên tính phân biệt** cho các tình "
              "huống lành tính. Đây là vế thường bị bỏ qua khi người ta áp dụng nguyên tắc chống oracle "
              "một cách máy móc. Nếu mọi lỗi đều trả về cùng một mã, hệ thống trở nên không dùng được: "
              "người dùng chọn nhầm tệp, ổ đĩa đầy hay quên rằng tệp đích đã tồn tại đều nhận được cùng "
              "một thông báo vô nghĩa."),
        ("tbl", "Bảng 2.7. Mười hai mã lỗi công khai và tiêu chí phân loại",
         ["Mã lỗi", "Ý nghĩa", "Vì sao phân biệt được mà không tạo oracle"],
         [
             ["`SV-UNAUTHORIZED`", "Chứng thực thất bại: sai mật khẩu HOẶC sai mảnh HOẶC bản mã bị sửa",
              "Đây chính là mã hợp nhất — nó cố ý KHÔNG phân biệt"],
             ["`SV-NOT-FOUND`", "Không tìm thấy tệp, mục hoặc phiên", "Sự thật về hệ thống tệp, không phải về bí mật"],
             ["`SV-MALFORMED`", "Không phải tệp của định dạng này; hoặc ảnh không giải mã được",
              "Xác định từ chuỗi nhận dạng, trước mọi thao tác mật mã"],
             ["`SV-CORRUPTED`", "Đúng là tệp két nhưng chữ ký không hợp lệ",
              "Cổng chữ ký chạy trước và không dùng bí mật nào"],
             ["`SV-INCOMPATIBLE-VERSION`", "Phiên bản định dạng không được hỗ trợ, kèm hai số phiên bản",
              "Số phiên bản là dữ liệu công khai trong phần khung"],
             ["`SV-INSUFFICIENT-SHARES`", "Số mảnh cung cấp ít hơn ngưỡng, kèm số hiện có và số cần",
              "Là phép đếm trước khi thử, không phải một lần thử chứng thực"],
             ["`SV-INVALID-INPUT`", "Đầu vào sai cấu trúc, kèm mô tả không bí mật",
              "Sự thật về tham số do chính người dùng cung cấp"],
             ["`SV-TOO-LARGE`", "Đầu vào vượt trần, kèm giới hạn và kích thước thực tế",
              "Kích thước tệp là thông tin công khai"],
             ["`SV-TIMEOUT`", "Thao tác vượt hạn giờ tường", "Sự thật về tài nguyên, không liên quan bí mật"],
             ["`SV-OUTPUT-EXISTS`", "Tệp đích đã tồn tại, từ chối ghi đè", "Sự thật về hệ thống tệp"],
             ["`SV-IO`", "Không đọc/ghi được tệp, kèm chuỗi mô tả CỐ ĐỊNH không chứa đường dẫn",
              "Loại lỗi là công khai; đường dẫn bị loại bỏ vì có thể chứa thông tin nhạy cảm"],
             ["`SV-INTERNAL`", "Lỗi nội bộ không lường trước, đã che kín", "Không tiết lộ gì"],
         ], [4.0, 6.0, 6.2], 10),
        ("p", "Chi tiết về mã lỗi vào-ra đáng được chú ý: hệ thống không trả về thông điệp gốc của hệ điều "
              "hành, vì thông điệp đó thường chứa **đường dẫn đầy đủ** của tệp, mà đường dẫn có thể tự nó "
              "đã là thông tin nhạy cảm. Thay vào đó, một chuỗi mô tả cố định được dùng chung cho cả tầng "
              "két và tầng dịch vụ mức tệp, bảo đảm hai tầng không lệch nhau dù chỉ một byte."),

        ("h3", "9.3. Vệ sinh bí mật trong bộ nhớ"),
        ("p", "Vệ sinh bí mật trong bộ nhớ được thiết kế thành một vòng đời bốn giai đoạn, trình bày ở "
              "Hình 2.16."),
        ("fig", "Hinh-2-16-vong-doi-bi-mat",
         "Hình 2.16. Vòng đời của bí mật trong bộ nhớ và cơ chế xóa"),
        ("p", "Nền tảng của cơ chế là ba kiểu dữ liệu ở tầng ABI, mỗi kiểu giải quyết một khía cạnh. "
              "Kiểu khóa 32 byte dùng mảng cố định trên ngăn xếp nên không bao giờ tái cấp phát, và nó "
              "được xóa tại chỗ khi bị hủy. Kiểu mảnh khôi phục tương tự với độ dài 33 byte. Kiểu byte "
              "bí mật độ dài thay đổi thì tinh tế hơn: nó dùng một lát cắt đóng hộp thay vì một vectơ "
              "động, và **không cung cấp bất kỳ phương thức sửa đổi nào**. Lý do rất cụ thể: một vectơ "
              "động có thể tái cấp phát khi lớn lên, để lại bản sao bí mật ở vùng nhớ cũ đã giải phóng "
              "mà không xóa được."),
        ("p", "Cả ba kiểu đều che nội dung khi được in ra nhật ký gỡ lỗi, và cả ba đều **cố ý không cài "
              "đặt khả năng tuần tự hóa**. Điểm cuối này là một biện pháp phòng vệ ở mức trình biên dịch: "
              "một lập trình viên không thể vô ý đưa một khóa vào một cấu trúc dữ liệu đi qua biên giao "
              "tiếp, vì mã đó sẽ không biên dịch được."),
        ("p", "Vòng đời cho thấy khóa chủ là bí mật **duy nhất** tồn tại suốt phiên; danh tính age và "
              "khóa ký chỉ được mở bọc trong phạm vi từng thao tác. Riêng danh tính age còn có một đặc "
              "thù: vì công cụ age nhận danh tính qua tệp chứ không qua tham số dòng lệnh hay biến môi "
              "trường, hệ thống buộc phải ghi nó ra một tệp tạm. Tệp tạm này được tạo với quyền chỉ chủ "
              "sở hữu đọc-ghi, và khi bị hủy thì được ghi đè bằng số không trước khi xóa liên kết. Tài "
              "liệu của mô-đun ghi rõ rằng việc ghi đè này là **nỗ lực tối đa** chứ không phải bảo đảm, "
              "vì các hệ thống tệp sao-chép-khi-ghi và các ổ đĩa thể rắn có thể không ghi đè tại chỗ."),
        ("p", "Việc chọn tệp thay vì tham số dòng lệnh hay biến môi trường là quyết định đúng: tham số "
              "dòng lệnh hiển thị cho mọi tiến trình khác trên hệ thống, và biến môi trường có thể bị "
              "kế thừa xuống các tiến trình con. Luồng vào chuẩn thì đã bị chiếm bởi chính dữ liệu cần "
              "giải mã. Tệp tạm với quyền hạn chế là lựa chọn ít tệ nhất trong các lựa chọn có sẵn, và "
              "báo cáo ghi nhận điều này như một sự đánh đổi chứ không phải một giải pháp hoàn hảo."),

        ("h3", "9.4. Làm cứng tiến trình con ngoài"),
        ("p", "Việc nhúng một chương trình bên ngoài vào một ứng dụng bảo mật là một quyết định tiềm ẩn "
              "rủi ro, và hệ thống xử lý rủi ro đó bằng một chuỗi sáu biện pháp nối tiếp nhau, sẽ được "
              "trình bày chi tiết ở Chương 3 kèm hình minh họa."),
        ("p", "Ở mức thiết kế, điều đáng phân tích là **chính sách bắt buộc và tùy chọn**. Hai nhị phân "
              "phục vụ mã hóa được đánh dấu bắt buộc: một bản dựng phát hành thiếu chúng sẽ **hỏng ngay "
              "ở khâu biên dịch** chứ không tạo ra một ứng dụng chạy được nhưng thiếu chức năng. Ngược "
              "lại, nhị phân phục vụ siêu dữ liệu được đánh dấu tùy chọn: nếu vắng mặt, mô-đun tương ứng "
              "**tự tắt theo hướng an toàn** — mọi lệnh trả về lỗi rõ ràng và giao diện hiển thị biểu ngữ "
              "giải thích, thay vì để người dùng nhấn nút và nhận một lỗi nội bộ khó hiểu."),
        ("p", "Sự phân biệt này phản ánh đúng vai trò của từng thành phần: không có mã hóa thì sản phẩm "
              "không còn là sản phẩm; không có phân tích siêu dữ liệu thì sản phẩm vẫn dùng được cho năm "
              "mô-đun còn lại. Nguyên tắc chung ở đây là **hỏng theo hướng an toàn**: khi một thành phần "
              "vắng mặt, hệ thống phải từ chối rõ ràng chứ không được im lặng bỏ qua."),

        ("h3", "9.5. Kiểm soát tài nguyên và chống từ chối dịch vụ"),
        ("p", "Nhóm biện pháp cuối cùng nhắm tới tính sẵn sàng. Điểm chung của chúng là **kiểm tra trước "
              "khi cấp phát**, chứ không phải bắt lỗi sau khi cấp phát thất bại."),
        ("tbl", "Bảng 2.8. Các biện pháp kiểm soát tài nguyên",
         ["Biện pháp", "Giá trị", "Kiểm tra ở đâu và bằng cách nào"],
         [
             ["Trần kích thước một tệp / một mục", "2 GiB",
              "Đọc siêu dữ liệu hệ thống tệp trước, so sánh, rồi mới đọc nội dung"],
             ["Trần kích thước header container", "1 MiB",
              "So sánh với trường độ dài trong phần khung, trước khi cấp phát bộ đệm"],
             ["Trần tham số Argon2id trước xác thực", "4 GiB bộ nhớ, 64 vòng, 64 luồng",
              "Kiểm tra ngay sau khi giải mã header, trước khi chạy hàm dẫn xuất khóa"],
             ["Chống bom giải nén ảnh", "Cạnh ≤ 30 000 px (20 000 với QR); cấp phát ≤ 1 GiB (512 MiB với QR)",
              "Đọc kích thước từ header ảnh trước khi giải nén toàn bộ"],
             ["Trần kích thước tệp ảnh và tệp siêu dữ liệu", "64 MiB (giấu tin, QR), 256 MiB (thủy vân), 8 GiB (siêu dữ liệu)",
              "Kiểm tra bằng siêu dữ liệu hệ thống tệp trước khi đọc"],
             ["Hạn giờ tường cho tiến trình con", "120 giây (age), 60 giây (ExifTool)",
              "Luồng chính chờ có thời hạn; hết hạn thì kết liễu tiến trình con"],
             ["Khóa ghi theo từng két", "Một khóa cho mỗi đường dẫn đã chuẩn hóa",
              "Giữ suốt chu trình đọc–sửa–ghi; các két khác nhau vẫn song song"],
         ], [4.6, 5.0, 6.6], 10),
        ("p", "Cần ghi nhận một hạn chế đã biết liên quan tới bảng khóa ghi: bảng này **tăng đơn điệu** — "
              "mỗi đường dẫn két từng được thao tác sẽ để lại một mục trong bảng và mục đó không bao giờ "
              "bị dọn. Trong một ứng dụng máy tính để bàn với vòng đời tiến trình ngắn, ảnh hưởng thực tế "
              "là không đáng kể; nhưng đây vẫn là một điểm được xếp vào danh sách rủi ro mức thấp cần "
              "theo dõi, và báo cáo ghi nhận nó thay vì bỏ qua."),
    ]

    # ============================================================= ket luan
    B += [
        ("h2", "Kết luận chương 2"),
        ("p", "Chương 2 đã đi từ phân tích bài toán tới thiết kế chi tiết của hệ thống. Ba mục tiêu thiết "
              "kế cấp cao — bí mật gắn với toàn vẹn, an toàn khi thất bại, và an toàn về dữ liệu người "
              "dùng — đã được triển khai thành một chuỗi các quyết định kiến trúc cụ thể và có thể kiểm "
              "chứng."),
        ("p", "Về kiến trúc phần mềm, việc tách hợp đồng khỏi hiện thực và tiêm bộ điều hợp tại một gốc "
              "lắp ghép duy nhất đã cho phép các crate nghiệp vụ hoàn toàn không phụ thuộc nền tảng và "
              "kiểm thử được độc lập, đồng thời giới hạn phụ thuộc vào chương trình ngoài trong một điểm "
              "duy nhất."),
        ("p", "Về kiến trúc mật mã, đóng góp thiết kế đáng kể nhất nằm ở hai chỗ: cơ chế gốc ràng buộc "
              "cho phép một chữ ký duy nhất bảo vệ cả header lẫn tải trọng và chống được tấn công ghép "
              "tệp; và cơ chế ràng buộc ngữ cảnh trong dẫn xuất khóa bọc, thay thế cho dữ liệu liên kết "
              "mà hàm AEAD được chọn không hỗ trợ. Cả hai đều được xác nhận bằng kiểm thử tự động."),
        ("p", "Về kiến trúc an ninh, điểm đáng chú ý nhất là **thứ tự các cổng kiểm tra** trên đường mở "
              "khóa. Việc đặt cổng chữ ký trước cổng mật khẩu, và việc cổng chữ ký hoàn toàn không sử "
              "dụng thông tin bí mật, là điều kiện tiên quyết để mô hình lỗi có thể vừa chống dò oracle "
              "vừa giữ được tính hành động được cho người dùng."),
        ("p", "Chương cũng đã ghi nhận trung thực bốn hạn chế ở mức thiết kế: cơ chế ràng buộc bằng dữ "
              "liệu liên kết bị hoãn lại; khóa ghi chỉ có hiệu lực trong cùng tiến trình; khoảng trống "
              "TOCTOU trong việc ghim băm nhị phân; và bảng khóa ghi tăng đơn điệu. Việc nêu rõ các hạn "
              "chế này ngay ở chương thiết kế, thay vì để tới phần đánh giá, phản ánh đúng cách một hồ "
              "sơ kỹ thuật về an toàn thông tin nên được viết. Chương 3 sẽ trình bày cách các thiết kế "
              "này được hiện thực hóa thành mã nguồn."),
    ]
    return B
