# -*- coding: utf-8 -*-
"""CHUONG 3 — Xay dung va trien khai he thong."""

SHOT = {"max_h_cm": 11.0}


def blocks():
    B = [("h1", "CHƯƠNG 3\nXÂY DỰNG VÀ TRIỂN KHAI HỆ THỐNG")]

    # ======================================== 1. Moi truong va cong nghe
    B += [
        ("h2", "1. Môi trường và công nghệ triển khai"),

        ("h3", "1.1. Môi trường phát triển và các cổng chất lượng"),
        ("p", "Hệ thống được phát triển bằng ngôn ngữ Rust ấn bản 2021, với phiên bản trình biên dịch "
              "tối thiểu được ấn định là 1.96 và được cưỡng chế bằng một nhóm việc riêng trong quy trình "
              "tích hợp liên tục. Việc cố định phiên bản tối thiểu không chỉ là vấn đề tương thích: nó "
              "bảo đảm rằng mọi thành viên phát triển và mọi máy dựng đều làm việc trên cùng một tập tính "
              "năng ngôn ngữ, tránh tình huống một đoạn mã chỉ biên dịch được trên máy của người viết."),
        ("p", "Năm cổng chất lượng được áp dụng cho mọi thay đổi. Cổng thứ nhất kiểm tra định dạng mã "
              "nguồn theo chuẩn chung. Cổng thứ hai chạy công cụ phân tích tĩnh với **mọi cảnh báo được "
              "nâng thành lỗi**; điều này có nghĩa là một đoạn mã chỉ cần sinh ra một cảnh báo về cách "
              "viết cũng đủ làm hỏng bản dựng. Cổng thứ ba biên dịch toàn bộ workspace với tệp khóa "
              "phiên bản, bảo đảm cây phụ thuộc chính xác tới từng phiên bản. Cổng thứ tư chạy toàn bộ "
              "bộ kiểm thử. Cổng thứ năm chạy hai công cụ kiểm tra chuỗi cung ứng, một cho chính sách "
              "giấy phép và nguồn gốc, một cho các lỗ hổng đã công bố."),
        ("p", "Một kỷ luật đáng chú ý ở mức workspace là việc **cấm mã không an toàn trên toàn bộ dự án** "
              "thông qua khai báo lint. Hai crate làm nhiệm vụ gọi thư viện C buộc phải mở lại quyền này "
              "một cách cục bộ và tường minh. Cách làm này biến một quy ước vốn dựa vào kỷ luật cá nhân "
              "thành một ràng buộc được trình biên dịch cưỡng chế, và đồng thời làm cho phạm vi mã cần "
              "rà soát thủ công thu hẹp lại còn đúng hai tệp."),

        ("h3", "1.2. Tổ chức mã nguồn"),
        ("p", "Toàn bộ hệ thống gồm khoảng 16 300 dòng mã Rust, phân bố trong mười ba crate thuộc "
              "workspace cộng với một crate vỏ giao diện nằm ngoài workspace. Hình 3.1 trình bày cấu "
              "trúc thư mục cùng quy mô và trách nhiệm của từng thành phần."),
        ("fig", "Hinh-3-01-cau-truc-ma-nguon",
         "Hình 3.1. Cấu trúc mã nguồn của workspace Secure Vault Research"),
        ("p", "Quyết định tổ chức đáng chú ý nhất nằm ở dòng cuối cùng của phần khai báo workspace: thư "
              "mục chứa vỏ giao diện được khai báo **loại trừ**. Hệ quả kỹ thuật của một dòng khai báo "
              "này khá sâu rộng. Thứ nhất, cây phụ thuộc của thành phần webview — vốn gồm hàng trăm "
              "crate với nhiều crate phụ thuộc nền tảng — không đi vào tệp khóa phiên bản của phần lõi, "
              "nên hai công cụ kiểm tra chuỗi cung ứng có thể soi phần lõi một cách có ý nghĩa thay vì "
              "chìm trong nhiễu. Thứ hai, phần lõi biên dịch và kiểm thử được trên một máy hoàn toàn "
              "không có bộ công cụ giao diện đồ họa — điều này rất quan trọng cho môi trường tích hợp "
              "liên tục và cho việc kiểm toán độc lập."),
        ("p", "Cái giá phải trả là crate vỏ giao diện phải được kiểm tra bằng một nhóm việc riêng trong "
              "quy trình tích hợp liên tục, với bộ cổng chất lượng riêng. Dự án chấp nhận cái giá này "
              "một cách có ý thức và ghi nhận nó trong tài liệu kiến trúc."),

        ("h3", "1.3. Thư viện và nhị phân đi kèm"),
        ("p", "Nguyên tắc chọn phụ thuộc của dự án là ưu tiên thư viện thuần Rust, chỉ dùng FFI khi "
              "không có lựa chọn thuần Rust đủ tin cậy, và chỉ dùng chương trình ngoài khi cả hai phương "
              "án trên đều không khả thi."),
        ("p", "Ở nhóm **thuần Rust**, hai thư viện mật mã cốt lõi là thư viện băm và thư viện dẫn xuất "
              "khóa từ mật khẩu. Nhóm này còn gồm thư viện xử lý ảnh, thư viện mã hóa và giải mã QR, và "
              "thư viện tuần tự hóa nhị phân."),
        ("p", "Ở nhóm **FFI**, hai crate đóng vai trò cầu nối. Crate thứ nhất bọc thư viện libsodium để "
              "cung cấp ba năng lực: ký và kiểm chữ ký Ed25519, băm BLAKE2b, và mã hóa có xác thực "
              "`crypto_secretbox`. Crate thứ hai nhúng trực tiếp mã nguồn C của thư viện chia sẻ bí mật "
              "Shamir vào cây dự án, với một chi tiết đáng chú ý: hàm sinh số ngẫu nhiên của thư viện "
              "gốc **được thay thế bằng một hàm do phía Rust cung cấp**, nối trực tiếp vào nguồn ngẫu "
              "nhiên của hệ điều hành. Cách làm này loại bỏ một nguồn rủi ro cổ điển là bộ sinh ngẫu "
              "nhiên yếu bên trong thư viện C."),
        ("p", "Ở nhóm **chương trình ngoài**, hệ thống dùng công cụ mã hóa age cùng công cụ sinh khóa đi "
              "kèm, và công cụ xử lý siêu dữ liệu ExifTool. Lý do phải dùng chương trình ngoài rất cụ "
              "thể trong từng trường hợp. Với age, thư viện gốc được viết bằng Go và không xuất khẩu "
              "giao diện gọi hàm ngoại ngôn ngữ, nên không có cách nào liên kết trực tiếp vào một chương "
              "trình Rust; các hiện thực Rust của định dạng age thì tồn tại nhưng không phải là hiện "
              "thực tham chiếu. Với ExifTool, công cụ này là chương trình Perl và độ bao phủ định dạng "
              "của nó lớn tới mức không có lựa chọn thay thế nào tương đương."),
        ("p", "Cả hai trường hợp đều dẫn tới cùng một hệ quả kiến trúc: hệ thống phải coi các chương "
              "trình này như thành phần nằm **bên kia một ranh giới tin cậy** và phải bao vây chúng bằng "
              "một chuỗi biện pháp, sẽ trình bày ở mục 6.1."),
    ]

    # ========================================== 2. Tang nen mat ma
    B += [
        ("h2", "2. Xây dựng tầng nền mật mã"),

        ("h3", "2.1. Tầng hợp đồng: các cổng trừu tượng và kiểu giá trị"),
        ("p", "Tầng nền mật mã bắt đầu bằng một crate hoàn toàn không chứa thuật toán, chỉ chứa hợp đồng. "
              "Hình 3.2 trình bày cấu trúc của tầng này cùng quan hệ với các bộ điều hợp cụ thể."),
        ("fig", "Hinh-3-02-abi-mat-ma",
         "Hình 3.2. Sơ đồ lớp của tầng hợp đồng mật mã và các bộ điều hợp hiện thực"),
        ("p", "Crate hợp đồng định nghĩa sáu cổng. Cách phân chia sáu cổng này thể hiện một nguyên tắc "
              "thiết kế đáng học hỏi: **một cổng cho một trách nhiệm**. Chẳng hạn, năng lực băm và năng "
              "lực dẫn xuất khóa con được tách thành hai cổng riêng biệt dù cùng được BLAKE3 hiện thực, "
              "vì một bộ điều hợp chỉ biết băm mà không biết dẫn xuất khóa vẫn là một bộ điều hợp hợp lệ. "
              "Sự tách bạch này cũng làm cho ý định của mã gọi trở nên rõ ràng hơn: khi một hàm nhận vào "
              "một tham số kiểu cổng dẫn xuất khóa, người đọc biết ngay rằng hàm đó sẽ sinh khóa chứ "
              "không đơn thuần tính vân tay."),
        ("p", "Phần kiểu giá trị được chia thành hai nhóm với hai chính sách trái ngược. Nhóm **không bí "
              "mật** — giá trị băm, muối, tham số chi phí, chữ ký, khóa công khai, người nhận age, các "
              "định danh thuật toán — đều hỗ trợ tuần tự hóa và được nhúng thẳng vào header hoặc đối "
              "tượng truyền dữ liệu. Nhóm **bí mật** thì ngược lại hoàn toàn: tự xóa khi bị hủy, che nội "
              "dung khi in ra nhật ký, và cố ý **không** hỗ trợ tuần tự hóa."),
        ("p", "Chi tiết thiết kế tinh tế nhất trong nhóm bí mật nằm ở kiểu byte bí mật độ dài thay đổi. "
              "Kiểu này bọc một lát cắt đóng hộp thay vì một vectơ động, và không cung cấp bất kỳ phương "
              "thức nào cho phép sửa đổi hay nối thêm dữ liệu. Lý do được ghi rõ trong chú thích mã "
              "nguồn: một vectơ động có phần dung lượng dư, và khi nó lớn lên vượt quá dung lượng đó, "
              "hệ thống cấp phát vùng nhớ mới rồi sao chép nội dung sang — để lại một bản sao bí mật ở "
              "vùng nhớ cũ mà cơ chế xóa khi hủy không với tới được. Bằng cách loại bỏ khả năng lớn lên, "
              "kiểu dữ liệu này loại bỏ luôn cả họ lỗi đó."),

        ("h3", "2.2. Bộ điều hợp băm và dẫn xuất khóa"),
        ("p", "Bộ điều hợp BLAKE3 hiện thực đồng thời hai cổng. Ở cổng băm, nó cung cấp ba chế độ: băm "
              "một lần, băm có khóa, và băm theo dòng cho các đầu vào không nạp hết vào bộ nhớ được. Ở "
              "cổng dẫn xuất khóa, nó gọi trực tiếp chế độ dẫn xuất của thư viện với một chuỗi ngữ cảnh "
              "do phía gọi cung cấp."),
        ("p", "Một chi tiết vệ sinh bộ nhớ đáng chú ý trong hiện thực: thư viện trả về khóa dẫn xuất "
              "dưới dạng một mảng byte thông thường; bộ điều hợp chuyển mảng đó vào kiểu khóa tự xóa, "
              "sau đó **xóa luôn mảng nháp**. Nếu bỏ qua bước xóa nháp, một bản sao của khóa sẽ nằm lại "
              "trên ngăn xếp cho tới khi vùng đó bị ghi đè một cách ngẫu nhiên. Cùng một kiểu xử lý được "
              "áp dụng nhất quán ở bộ điều hợp dẫn xuất khóa từ mật khẩu và ở bộ điều hợp chia sẻ bí mật."),
        ("p", "Tính đúng đắn của bộ điều hợp được kiểm chứng bằng ba nhóm kiểm thử: đối chiếu với vectơ "
              "thử nghiệm chính thức của BLAKE3 cho đầu vào rỗng; đối chiếu kết quả với lời gọi trực "
              "tiếp thư viện tham chiếu; và kiểm tra rằng chế độ băm theo dòng cho kết quả trùng khớp "
              "với chế độ băm một lần."),

        ("h3", "2.3. Bộ điều hợp dẫn xuất khóa từ mật khẩu và chính sách tham số"),
        ("p", "Bộ điều hợp Argon2id nhận mật khẩu, muối và bộ ba tham số chi phí, trả về khóa 32 byte. "
              "Điểm cần phân tích là sự phân chia trách nhiệm giữa bộ điều hợp và mô-đun chính sách. Bộ "
              "điều hợp chỉ kiểm tra tính hợp lệ **về mặt cấu trúc** của tham số — chẳng hạn số luồng "
              "bằng không là không hợp lệ — và trả về lỗi tham số nếu vi phạm. Nó **không** kiểm tra "
              "tham số có đủ mạnh hay không."),
        ("p", "Việc kiểm tra cường độ được đặt ở một mô-đun chính sách riêng, và chỉ được áp dụng khi "
              "**tạo mới**. Lý do đã nêu ở Chương 1 nhưng đáng nhắc lại vì nó là một quyết định thiết kế "
              "dễ làm sai: nếu áp sàn cường độ ở khâu xác minh, một két được tạo trên máy mạnh sẽ không "
              "mở được trên máy yếu nếu chính sách sau này bị siết chặt — một dạng khóa chặt dữ liệu do "
              "chính sách chứ không do mật mã."),
        ("p", "Mô-đun chính sách còn cung cấp một hàm **hiệu chỉnh theo phần cứng**. Hàm này đo thời gian "
              "thực thi thực tế của Argon2id trên máy đang chạy và tăng dần số vòng lặp cho tới khi đạt "
              "một mốc thời gian mục tiêu, với hai ràng buộc: không bao giờ xuống dưới sàn chính sách, "
              "và không vượt quá một trần đã định để bảo đảm hàm luôn dừng. Cần ghi nhận trạng thái hiện "
              "thực một cách chính xác: hàm này **đã tồn tại trong mã và có kiểm thử**, nhưng đường tạo "
              "két hiện vẫn dùng bộ tham số mặc định cố định. Việc đưa hiệu chỉnh vào giao diện thiết "
              "lập là một bước còn để ngỏ chứ không phải một tính năng đã hoàn tất."),

        ("h3", "2.4. Bộ điều hợp chữ ký và hiện thực định dạng minisign"),
        ("p", "Đây là một trong hai chỗ duy nhất mà dự án tự viết logic ở gần tầng mật mã, nên cần được "
              "mô tả chính xác về phạm vi. Phần **thuật toán** — sinh cặp khóa, ký và kiểm chữ ký "
              "Ed25519, băm BLAKE2b — hoàn toàn do libsodium đảm nhiệm. Phần dự án tự viết là **cách sắp "
              "xếp byte** của định dạng lưu trữ chữ ký, tức là công việc mã hóa và giải mã định dạng, "
              "không phải công việc mật mã."),
        ("p", "Định dạng gồm bốn dòng văn bản. Dòng đầu là chú thích không tin cậy. Dòng thứ hai là khối "
              "base64 chứa hai byte định danh thuật toán, tám byte định danh khóa và 64 byte chữ ký "
              "chính. Dòng thứ ba là chú thích tin cậy. Dòng thứ tư là base64 của chữ ký toàn cục."),
        ("p", "Hai chi tiết trong hiện thực đáng được phân tích. Thứ nhất, chữ ký chính không ký lên "
              "thông điệp mà ký lên **giá trị tiền băm BLAKE2b-512** của thông điệp — đây là biến thể "
              "tiền băm của định dạng. Thứ hai, chữ ký toàn cục ký lên chuỗi ghép của chữ ký chính với "
              "chú thích tin cậy; nhờ vậy chú thích tin cậy được ràng buộc mật mã và không thể bị sửa "
              "mà không bị phát hiện. Bộ kiểm thử xác nhận cả ba đường tấn công: sửa thông điệp, dùng "
              "sai khóa công khai, và sửa chú thích tin cậy đều bị từ chối."),
        ("p", "Một khác biệt so với công cụ gốc được ghi nhận trung thực trong chú thích mã nguồn: định "
              "danh khóa tám byte được tính theo cách **tất định** từ khóa công khai, trong khi công cụ "
              "gốc sinh nó ngẫu nhiên. Khác biệt này không ảnh hưởng tới việc kiểm chữ ký, vì phép kiểm "
              "luôn xác thực dựa trên khóa công khai do phía gọi cung cấp chứ không dựa vào định danh."),
        ("p", "Về khả năng tương thích byte với công cụ gốc, dự án ghi nhận rõ trạng thái: khả năng "
              "tương thích đã được **thiết kế** và một cổng kiểm tra tương thích trong quy trình tích "
              "hợp liên tục đã được **lên kế hoạch**, nhưng **chưa được nối dây**. Hiện tại chỉ có vòng "
              "lặp ký–kiểm nội bộ được kiểm chứng. Đây là một hạn chế thực sự cần ghi nhận: một chữ ký "
              "do hệ thống sinh ra chưa được chứng minh bằng thực nghiệm là kiểm được bằng công cụ "
              "minisign chuẩn."),

        ("h3", "2.5. Bộ điều hợp chia sẻ bí mật và lớp FFI"),
        ("p", "Bộ điều hợp chia sẻ bí mật gọi xuống thư viện C được nhúng trong dự án. Vai trò của lớp "
              "Rust ở đây chủ yếu là **vệ sinh bộ nhớ và kiểm tra biên**: thư viện C trả về các mảnh "
              "dưới dạng mảng byte thô, và lớp Rust chuyển chúng vào kiểu mảnh tự xóa rồi xóa sạch vùng "
              "nháp; ở chiều ngược lại, khóa tái tạo được chuyển vào kiểu khóa tự xóa và cả vùng nháp "
              "lẫn bản sao các mảnh đều được xóa."),
        ("p", "Bộ kiểm thử của bộ điều hợp xác nhận ba tính chất. Tính chất thứ nhất là vòng lặp chia — "
              "gộp: chia một khóa thành năm mảnh với ngưỡng ba, rồi gộp ba mảnh bất kỳ cho ra đúng khóa "
              "ban đầu. Tính chất thứ hai, quan trọng hơn về mặt nhận thức, là **dưới ngưỡng thì cho ra "
              "khóa sai chứ không báo lỗi**: gộp hai mảnh trong một lược đồ ngưỡng ba vẫn trả về một giá "
              "trị 32 byte, nhưng giá trị đó khác khóa gốc. Đây chính là bằng chứng cho luận điểm đã nêu "
              "ở Chương 1 rằng lược đồ Shamir thuần túy không tự phát hiện được mảnh sai, và vì thế phải "
              "có một cổng xác thực phía sau. Tính chất thứ ba là các tham số vô lý — ngưỡng lớn hơn "
              "tổng số mảnh, danh sách mảnh rỗng — bị từ chối tường minh."),

        ("h3", "2.6. Hiện thực bọc khóa"),
        ("p", "Mô-đun bọc khóa là một lớp rất mỏng trên hàm mã hóa có xác thực của libsodium, gồm đúng "
              "hai hàm. Hàm niêm phong sinh một nonce 24 byte ngẫu nhiên mới cho mỗi lần gọi rồi mã hóa; "
              "hàm mở bọc trả về lỗi xác thực nếu khóa sai hoặc bản mã bị sửa."),
        ("p", "Ba kiểm thử của mô-đun này rất ngắn nhưng bao phủ đúng các tính chất cần thiết: vòng lặp "
              "niêm phong — mở bọc; sai khóa hoặc sửa bản mã đều bị từ chối; và **mỗi lần niêm phong "
              "cùng một dữ liệu với cùng một khóa cho ra nonce khác nhau và bản mã khác nhau**. Kiểm thử "
              "thứ ba tuy đơn giản nhưng bảo vệ hệ thống khỏi một trong những lỗi nghiêm trọng nhất "
              "trong mật mã ứng dụng là dùng lại nonce."),
        ("p", "Chú thích của mô-đun ghi nhận thẳng thắn hạn chế đã phân tích ở Chương 2: hiện tại việc "
              "bọc dùng nonce ngẫu nhiên và **không có dữ liệu liên kết**; việc ràng buộc từng khối bọc "
              "vào định danh két, nhãn trường và số phiên bản là một quyết định lược đồ đã được ghi nhận "
              "nhưng chưa hiện thực hóa. Việc tách miền hiện được bảo đảm bằng khóa bọc dẫn xuất theo "
              "ngữ cảnh."),
    ]

    # ==================================== 3. Mo-dun Ket an toan
    B += [
        ("h2", "3. Xây dựng mô-đun Két an toàn"),

        ("h3", "3.1. Khung container: mã hóa, giải mã và phân tích cú pháp"),
        ("p", "Mô-đun khung container gồm ba nhóm hàm. Nhóm thứ nhất là hàm lắp ráp: nhận header, tải "
              "trọng đã mã hóa, bộ băm, bộ ký và khóa ký; trả về mảng byte hoàn chỉnh của tệp. Nhóm thứ "
              "hai là hàm giải mã có xác thực. Nhóm thứ ba là các hàm phân tích cú pháp phục vụ những "
              "trường hợp cần đọc header mà chưa cần xác thực."),
        ("p", "Hàm lắp ráp có một hành vi đáng chú ý: nó **ghi đè** hai trường trong header do phía gọi "
              "cung cấp là phiên bản định dạng và độ dài tải trọng, thay bằng giá trị thực tế. Đây là "
              "biện pháp bảo đảm tính tự nhất quán của tệp: không thể tồn tại một tệp mà header khai báo "
              "một độ dài tải trọng khác với độ dài thực."),
        ("p", "Hàm giải mã có một điểm thiết kế cần phân tích. Nó phải dùng độ dài tải trọng lấy từ "
              "header để xác định ranh giới giữa tải trọng và phần đuôi chữ ký, nhưng tại thời điểm đó "
              "header **chưa được xác thực**. Chú thích mã nguồn giải thích vì sao điều này an toàn: một "
              "độ dài sai chỉ dẫn tới việc băm nhầm phạm vi byte, và hệ quả tất yếu là gốc ràng buộc "
              "tính ra sẽ khác với gốc đã được ký, nên phép kiểm chữ ký thất bại. Nói cách khác, một độ "
              "dài sai chỉ có thể gây ra **từ chối**, không bao giờ gây ra **chấp nhận sai**."),
        ("p", "Hàm phân tích khung phân biệt ba loại thất bại theo một bảng phân loại rõ ràng. Các vấn "
              "đề cấu trúc — tệp quá ngắn, sai chuỗi nhận dạng, cụt giữa chừng, CBOR hỏng — đều cho ra "
              "kết luận lành tính “không phải tệp két”. Riêng phiên bản định dạng không được hỗ trợ, "
              "phát hiện từ hai byte trong phần khung, cho ra một kết luận riêng và hành động được là "
              "“hãy cập nhật ứng dụng”. Còn sự không khớp của trường bộ thuật toán bên trong header thì "
              "cho ra kết luận “tệp hỏng hoặc bị sửa”, vì trong thiết kế hiện tại mọi thay đổi bộ thuật "
              "toán đều kéo theo tăng phiên bản định dạng, nên sự lệch pha trung thực đã bị cổng phiên "
              "bản bắt trước rồi."),
        ("p", "Tính không gây hoảng loạn của bộ phân tích được kiểm chứng bằng một phép quét kiểu fuzz "
              "có tính tất định: kiểm thử cắt cụt tệp ở **mọi độ dài có thể**, thực hiện bốn nghìn phép "
              "lật một byte theo một bộ sinh giả ngẫu nhiên có hạt giống cố định, và thử với các bộ đệm "
              "ngẫu nhiên. Với mọi trường hợp, kiểm thử khẳng định hai điều: không có lời gọi nào gây "
              "hoảng loạn, và một container đã bị đột biến không bao giờ được xác thực thành công với "
              "một tải trọng khác tải trọng gốc."),
        ("p", "Dự án ghi nhận rằng một mục tiêu fuzz có dẫn hướng theo độ phủ là bước tiếp theo tự nhiên "
              "nhưng **chưa được nối vào quy trình tích hợp liên tục**, với lý do là công cụ đó đòi hỏi "
              "trình biên dịch bản nhánh phát triển và một cấu hình đa nền tảng không đơn giản."),

        ("h3", "3.2. Kho lưu trữ tải trọng và cơ chế xóa dữ liệu rõ"),
        ("p", "Hàm đóng gói nhận danh sách các mục dạng rõ và sinh ra khối byte gồm ba phần đã mô tả ở "
              "Chương 2. Trong quá trình đóng gói, hàm tính vân tay BLAKE3 cho từng mục và ghi vào thư "
              "mục; giá trị này về sau dùng để hiển thị cho người dùng và để phát hiện hỏng nội dung."),
        ("p", "Cấu trúc kho lưu trữ đã giải nén có một đặc điểm hiện thực đáng chú ý: nó cài đặt hành vi "
              "**xóa sạch vùng byte nội dung khi bị hủy**. Nhờ vậy, ngay khi cấu trúc này ra khỏi phạm "
              "vi sử dụng, toàn bộ dữ liệu rõ của các mục bị ghi đè bằng số không mà mã gọi không cần "
              "làm gì thêm. Hàm đóng gói cũng xóa vùng nháp của nó sau khi ghép xong."),
        ("p", "Cần ghi nhận giới hạn của cơ chế này một cách trung thực. Việc xóa chỉ có hiệu lực đối "
              "với các bộ đệm mà mã Rust trực tiếp kiểm soát. Dữ liệu đi qua tiến trình con age nằm "
              "trong không gian bộ nhớ của tiến trình đó, và hệ thống không có cách nào tác động tới. "
              "Tài liệu làm cứng của dự án nêu rõ đây là biện pháp **nỗ lực tối đa**, và bảo đảm đầy đủ "
              "chỉ đạt được khi đường xử lý chuyển sang mô hình truyền dòng."),

        ("h3", "3.3. Hiện thực phân cấp khóa"),
        ("p", "Phân cấp khóa được hiện thực dưới dạng một cấu trúc **tổng quát trên hai cổng**: cổng dẫn "
              "xuất khóa từ mật khẩu và cổng dẫn xuất khóa con. Nhờ tính tổng quát này, crate nghiệp vụ "
              "của két giữ được đồ thị phụ thuộc sạch, còn bộ điều hợp thật chỉ được lắp vào tại gốc lắp "
              "ghép và tại các kiểm thử."),
        ("p", "Chuỗi ngữ cảnh dẫn xuất khóa bọc được xây dựng theo văn phạm đã mô tả ở Chương 2. Điều "
              "đáng chú ý về mặt kỹ thuật phần mềm là chuỗi này được **đóng băng bằng kiểm thử**: bộ "
              "kiểm thử so sánh chuỗi sinh ra với một hằng số văn bản viết cứng trong mã kiểm thử. Nếu "
              "một lập trình viên vô tình sửa một ký tự trong văn phạm, kiểm thử sẽ thất bại ngay lập "
              "tức. Đây là một biện pháp bảo vệ rất đáng giá, bởi vì một thay đổi như vậy sẽ làm **mọi "
              "két đã tồn tại trở nên không mở được** mà không có bất kỳ dấu hiệu nào ở giai đoạn biên "
              "dịch."),
        ("p", "Bộ kiểm thử còn xác nhận trực tiếp hai thuộc tính an toàn đã phân tích ở Chương 2, bằng "
              "cách thực sự niêm phong một bí mật bằng khóa của một két rồi thử mở bằng khóa của két "
              "khác và bằng khóa của trường khác — cả hai đều thất bại đúng như dự kiến. Việc kiểm thử "
              "chạy qua toàn bộ chuỗi dẫn xuất và niêm phong, thay vì chỉ so sánh hai khóa, làm cho bằng "
              "chứng có sức thuyết phục hơn nhiều."),

        ("h3", "3.4. Bộ mã hóa tải trọng và cơ chế điều khiển tiến trình con"),
        ("p", "Bộ điều hợp điều khiển tiến trình con age là một trong những phần hiện thực đòi hỏi nhiều "
              "công sức nhất, không phải vì phần mật mã mà vì phần quản lý tiến trình. Bốn vấn đề kỹ "
              "thuật phải được giải quyết đồng thời."),
        ("p", "Vấn đề thứ nhất là **nguy cơ khóa chết giữa các ống dẫn**. Nếu tiến trình cha ghi toàn bộ "
              "dữ liệu vào luồng vào của tiến trình con rồi mới đọc luồng ra, hệ thống sẽ treo ngay khi "
              "dữ liệu vượt quá dung lượng bộ đệm ống dẫn của hệ điều hành: tiến trình con bị chặn vì "
              "không ghi ra được, còn tiến trình cha bị chặn vì không ghi vào được. Giải pháp trong hiện "
              "thực là dùng ba luồng riêng — một luồng nạp dữ liệu vào, một luồng rút dữ liệu ra, một "
              "luồng rút luồng lỗi — trong khi luồng chính chỉ làm nhiệm vụ chờ có thời hạn."),
        ("p", "Vấn đề thứ hai là **hạn giờ tường**. Luồng chính chờ tín hiệu hoàn tất với một thời hạn; "
              "khi hết hạn, nó kết liễu tiến trình con và trả về lỗi hết giờ. Một chi tiết xử lý tinh tế: "
              "sau khi kết liễu, mã **không** chờ các luồng phụ kết thúc mà thả chúng ra. Lý do được ghi "
              "trong chú thích: một tiến trình con bị kết liễu vẫn có thể để lại một tiến trình cháu giữ "
              "các ống dẫn, và việc chờ có thể treo cho tới khi tiến trình cháu đó kết thúc."),
        ("p", "Vấn đề thứ ba là **truyền danh tính bí mật một cách an toàn**. Như đã phân tích ở Chương "
              "2, ba kênh truyền thông thường đều không dùng được, nên hệ thống ghi danh tính ra một tệp "
              "tạm có quyền hạn chế, truyền đường dẫn qua tham số, và ghi đè rồi xóa tệp khi kết thúc."),
        ("p", "Vấn đề thứ tư là **môi trường thực thi**. Tiến trình con được sinh ra với biến môi trường "
              "bị xóa sạch. Trên Windows, việc xóa sạch hoàn toàn lại gây ra một vấn đề mới: trình nạp "
              "thư viện động của hệ điều hành cần một số biến để tìm được các thư viện hệ thống, và công "
              "cụ age cần biến chỉ thư mục tạm. Giải pháp là một **danh sách cho phép tối thiểu** gồm "
              "đúng bốn biến, và điều quan trọng là danh sách này không bao gồm biến đường dẫn tìm "
              "chương trình cũng như bất kỳ biến nào có thể chứa dữ liệu của người dùng."),
        ("p", "Về mặt trạng thái hiện thực, cần nêu rõ hai điều. Thứ nhất, hạn giờ tường **đã được hiện "
              "thực và có kiểm thử** — kiểm thử tạo một kịch bản shell ngủ ba mươi giây và xác nhận rằng "
              "lời gọi trả về trong khoảng hai trăm mili-giây. Chú thích ở đầu tệp mã nguồn vẫn còn ghi "
              "rằng chưa có hạn giờ; đây là một chú thích lỗi thời đã được dự án ghi nhận trong bảng đối "
              "chiếu tài liệu và mã nguồn. Thứ hai, việc **truyền dòng vẫn chưa được hiện thực**: tải "
              "trọng vẫn được nạp toàn bộ vào bộ nhớ ở cả hai chiều, và đây là hạn chế có ảnh hưởng thực "
              "tế lớn nhất của hệ thống, sẽ được định lượng ở Chương 4."),

        ("h3", "3.5. Quản lý phiên"),
        ("p", "Phiên làm việc được hiện thực bằng một bảng ánh xạ từ chuỗi định danh sang một cấu trúc "
              "chỉ chứa hai trường: khóa chủ và đường dẫn két. Ba đặc điểm của thiết kế này đáng được "
              "phân tích."),
        ("p", "Thứ nhất, định danh phiên là **32 byte ngẫu nhiên** lấy từ nguồn của hệ điều hành, biểu "
              "diễn dưới dạng chuỗi hex. Nó hoàn toàn không mang thông tin: không suy ra được đường dẫn "
              "két, không suy ra được thời điểm tạo, không đoán được. Giao diện chỉ giữ chuỗi này."),
        ("p", "Thứ hai, cấu trúc phiên chứa **duy nhất khóa chủ** chứ không chứa danh tính age hay khóa "
              "ký đã mở bọc. Mỗi thao tác cần tới hai bí mật đó sẽ mở bọc lại từ đầu rồi hủy ngay. Cách "
              "làm này đánh đổi một chút hiệu năng — mỗi thao tác phải chạy thêm hai phép dẫn xuất khóa "
              "và hai phép mở bọc, đều là các phép rất nhanh — để thu về một thuộc tính an toàn đáng giá: "
              "thu hẹp tối đa lượng bí mật thường trú trong bộ nhớ."),
        ("p", "Thứ ba, thao tác khóa lại đơn giản là **xóa mục khỏi bảng**. Vì kiểu khóa tự xóa khi bị "
              "hủy, việc xóa mục kéo theo việc ghi đè khóa chủ bằng số không một cách tự động. Đây là "
              "một ví dụ điển hình về việc dùng hệ thống kiểu dữ liệu để cưỡng chế một thuộc tính an "
              "toàn, thay vì dựa vào kỷ luật của lập trình viên."),

        ("h3", "3.6. Quy trình tạo két"),
        ("p", "Hình 3.3 trình bày chi tiết trình tự tạo một két mới, thao tác duy nhất trong hệ thống "
              "sinh ra toàn bộ vật liệu khóa của một két."),
        ("fig", "Hinh-3-03-tuan-tu-tao-ket",
         "Hình 3.3. Biểu đồ tuần tự quá trình khởi tạo két mới"),
        ("p", "Trình tự cho thấy bốn giá trị ngẫu nhiên được sinh ra: định danh két, muối cho hàm dẫn "
              "xuất khóa, cặp khóa age và cặp khóa ký. Ba giá trị đầu do hệ thống trực tiếp sinh; cặp "
              "khóa age do tiến trình con sinh khóa của công cụ age tạo ra."),
        ("p", "Một chi tiết cần làm rõ về cách xử lý đầu ra của công cụ sinh khóa: công cụ này in ra "
              "nhiều dòng, trong đó có dòng chú thích chứa khóa công khai và dòng chứa khóa bí mật. Hệ "
              "thống lấy **toàn bộ luồng ra làm danh tính** — vì toàn bộ luồng ra chính là một tệp danh "
              "tính hợp lệ theo định dạng của công cụ — và trích riêng chuỗi bắt đầu bằng tiền tố quy "
              "ước để làm khóa công khai người nhận. Cách làm này tránh phải phân tích cú pháp phức tạp "
              "và tránh nguy cơ tạo ra một tệp danh tính không hợp lệ."),
        ("p", "Một điểm nữa cần nhấn mạnh vì dễ hiểu nhầm: khi người dùng bật chính sách khôi phục lúc "
              "tạo két, hệ thống **không sinh mảnh ở bước này**. Nó chỉ ghi lại cặp số (tổng số mảnh, "
              "ngưỡng) vào header như một thông tin siêu dữ liệu. Các mảnh thật chỉ được cắt khi người "
              "dùng gọi lệnh chia khóa trên một phiên đã mở. Thiết kế này hợp lý vì mảnh là vật liệu bí "
              "mật cần được xuất ra một cách có chủ đích và cần được người dùng bảo quản ngay, không nên "
              "sinh ra một cách thụ động."),
        ("p", "Cuối cùng, một két rỗng vẫn đi qua toàn bộ đường ghi: kho lưu trữ rỗng vẫn được đóng gói, "
              "vẫn được mã hóa, vẫn được ký và vẫn được ghi nguyên tử. Không có đường tắt nào cho trường "
              "hợp rỗng, và điều này giúp giảm số nhánh mã cần kiểm chứng."),

        ("h3", "3.7. Chia và khôi phục khóa chủ"),
        ("p", "Hình 3.4 trình bày hai chiều của cơ chế sao lưu khóa chủ."),
        ("fig", "Hinh-3-04-chia-khoi-phuc-khoa-chu",
         "Hình 3.4. Chia và khôi phục khóa chủ của két theo ngưỡng k trong n"),
        ("p", "Phía chia rất trực tiếp: khóa chủ được lấy từ bảng phiên, chia thành n mảnh, mỗi mảnh "
              "được đóng vào một phong bì cố định 58 byte và ghi ra một tệp riêng theo cơ chế ghi nguyên "
              "tử. Phía khôi phục phức tạp hơn với bốn cổng kiểm tra nối tiếp đã mô tả ở Chương 2."),
        ("p", "Điểm đáng phân tích ở đây là **vị trí của cổng tín nhiệm thực sự**. Ba cổng đầu đều là "
              "kiểm tra cấu trúc và số lượng, hoàn toàn không liên quan tới mật mã, và các thông tin "
              "chúng tiết lộ đều không bí mật. Cổng thứ tư — tái tạo khóa chủ — như đã phân tích thì "
              "**không có khả năng tự phát hiện sai**. Do đó cổng tín nhiệm thực sự là phép mở bọc danh "
              "tính age đứng ngay sau, và đó chính là **cùng một cổng** với đường mở khóa bằng mật khẩu."),
        ("p", "Việc hai đường vào hội tụ về cùng một cổng tín nhiệm không phải là sự trùng hợp mà là một "
              "quyết định kiến trúc: nó bảo đảm hai đường thất bại theo cùng một cách và trả về cùng một "
              "mã lỗi, nên kẻ tấn công không thể dùng đường này để suy luận về đường kia."),
    ]

    # ================================== 4. Cac mo-dun doc lap voi ket
    B += [
        ("h2", "4. Xây dựng các mô-đun độc lập với két"),

        ("h3", "4.1. Mã hóa tệp bằng mật khẩu"),
        ("p", "Mô-đun mã hóa tệp độc lập là một trong những chỗ dễ bị hiểu nhầm nhất khi đọc lướt tài "
              "liệu của dự án, nên cần nêu rõ ngay: đường này **không sử dụng công cụ age**. Nó chạy "
              "hoàn toàn trong tiến trình bằng Argon2id kết hợp với hàm mã hóa có xác thực của libsodium."),
        ("fig", "Hinh-3-05-ma-hoa-tep-doc-lap",
         "Hình 3.5. Mã hóa và giải mã tệp độc lập bằng mật khẩu (định dạng SVENC)"),
        ("p", "Lý do của lựa chọn này rất thực dụng. Công cụ age được thiết kế quanh mô hình khóa công "
              "khai; việc dùng nó cho một tệp bảo vệ bằng mật khẩu đòi hỏi phải đi qua chế độ mật khẩu "
              "của công cụ, kéo theo một tiến trình con và toàn bộ chi phí làm cứng đi kèm — cho một "
              "thao tác hoàn toàn có thể thực hiện trong tiến trình. Việc giữ đường này thuần Rust cộng "
              "FFI khiến nó nhanh hơn, dễ kiểm thử hơn và không phụ thuộc vào sự có mặt của nhị phân "
              "ngoài."),
        ("p", "Định dạng tệp kết quả có header 62 byte tự mô tả, chứa chuỗi nhận dạng, phiên bản, định "
              "danh thuật toán dẫn xuất khóa, ba tham số chi phí, muối, định danh thuật toán mã hóa và "
              "nonce. Việc lưu tham số chi phí trong tệp là bắt buộc để giải mã được về sau, nhưng nó "
              "tạo ra chính xác vấn đề đã phân tích: header có thể bị kẻ tấn công điều khiển trước khi "
              "có bất kỳ phép xác thực nào. Hiện thực xử lý điều này bằng cách áp trần tham số **trước "
              "khi chạy hàm dẫn xuất khóa**, với cùng các giá trị trần mà mô-đun két sử dụng."),
        ("p", "Vấn đề ràng buộc header cũng được xử lý theo cùng nguyên tắc tách miền: khóa mã hóa tệp "
              "không phải là đầu ra trực tiếp của Argon2id mà là kết quả của một bước dẫn xuất tiếp theo "
              "trong đó **chuỗi nhận dạng của định dạng được gấp vào ngữ cảnh**. Nhờ vậy, một tệp mã hóa "
              "thông thường và một tệp cất khóa ký — vốn dùng chung cơ chế nhưng khác chuỗi nhận dạng — "
              "không thể bị hoán đổi cho nhau."),

        ("h3", "4.2. Các dịch vụ toàn vẹn"),
        ("p", "Mô-đun toàn vẹn cung cấp ba dịch vụ. Dịch vụ tính vân tay chạy theo cơ chế **truyền dòng "
              "theo từng khối 64 KiB**, nên nó xử lý được tệp có kích thước tùy ý mà không cần trần. Đây "
              "là điểm khác biệt so với đường tính vân tay của mô-đun két, vốn nạp toàn bộ tệp và do đó "
              "chịu trần hai gigabyte — một biểu hiện cụ thể của việc hai đường chưa được hợp nhất."),
        ("p", "Dịch vụ kiểm chữ ký nhận tệp, chữ ký tách rời và tệp khóa công khai. Một quyết định thiết "
              "kế quan trọng: chữ ký **không hợp lệ** được trả về như một kết quả bình thường với trường "
              "kết luận mang giá trị sai, chứ **không** phải như một lỗi. Chỉ các vấn đề cấu trúc — tệp "
              "không tồn tại, khóa công khai sai định dạng, tệp quá lớn — mới là lỗi. Sự phân biệt này "
              "rất quan trọng đối với trải nghiệm người dùng: “chữ ký không khớp” là một câu trả lời "
              "hợp lệ và có ý nghĩa, không phải một sự cố."),
        ("p", "Dịch vụ kiểm tra tổng hợp cho phép người dùng kiểm tra một tệp tải về theo giá trị băm "
              "công bố **và/hoặc** theo chữ ký. Hai phép kiểm là độc lập và mỗi phép có thể bật hoặc "
              "tắt; báo cáo trả về ghi rõ phép nào đã được yêu cầu và phép nào đã đạt, thay vì gộp thành "
              "một kết luận duy nhất. Đây là cách trình bày trung thực, vì “khớp băm” và “chữ ký hợp lệ” "
              "chứng minh hai điều khác nhau: cái thứ nhất chứng minh tệp trùng với một giá trị mà người "
              "dùng lấy từ nơi khác, cái thứ hai chứng minh tệp được ký bởi chủ thể nắm khóa tương ứng."),
        ("p", "Một chi tiết hiện thực nhỏ nhưng đáng ghi nhận: khi cả hai phép kiểm cùng được yêu cầu, "
              "hệ thống **chỉ đọc tệp một lần** và dùng chung giá trị băm đã tính trong quá trình kiểm "
              "chữ ký. Điều này tránh được cả chi phí đọc lặp lẫn nguy cơ hai phép kiểm nhìn thấy hai "
              "trạng thái khác nhau của tệp nếu tệp bị sửa giữa chừng."),

        ("h3", "4.3. Lược đồ chia sẻ bí mật độc lập"),
        ("p", "Mô-đun chia sẻ bí mật độc lập với két hiện thực một lược đồ lai giải quyết hạn chế cơ bản "
              "của nguyên thủy Shamir đã nêu ở Chương 1."),
        ("fig", "Hinh-3-06-chia-se-bi-mat",
         "Hình 3.6. Lược đồ chia sẻ bí mật lai: Shamir trên khóa dữ liệu kết hợp AEAD trên tải trọng"),
        ("p", "Cơ chế gồm bốn bước. Sinh một khóa dữ liệu 32 byte ngẫu nhiên. Mã hóa tải trọng bằng một "
              "khóa dẫn xuất từ khóa dữ liệu đó. Chia **khóa dữ liệu** — chứ không phải tải trọng — "
              "thành n mảnh. Cuối cùng, ràng buộc mỗi mảnh với đúng tệp tải trọng bằng cách nhúng vân "
              "tay của tệp tải trọng vào mảnh."),
        ("p", "Thuộc tính chịu lực của lược đồ nằm ở cách dẫn xuất khóa tải trọng: chuỗi ngữ cảnh **gấp "
              "vào cả ba trường header** là định danh nhóm, tổng số mảnh và ngưỡng. Vì hàm mã hóa được "
              "chọn không có dữ liệu liên kết, đây là cơ chế duy nhất bảo vệ tính toàn vẹn của header. "
              "Sửa bất kỳ byte nào trong ba trường đó sẽ dẫn xuất ra khóa khác và thẻ xác thực lập tức "
              "thất bại. Chú thích trong mã nguồn gọi đây là “thuộc tính an toàn chịu lực”, và cách gọi "
              "đó là chính xác."),
        ("p", "Năm cổng kiểm tra ở đường khôi phục đáng được phân tích vì chúng cho thấy sự cẩn thận "
              "trong việc xử lý các cạm bẫy đã biết. Cổng đồng thuận bảo đảm mọi mảnh thuộc cùng một lần "
              "chia. Cổng trùng hoành độ ngăn tình huống người dùng cung cấp cùng một mảnh hai lần — "
              "tình huống này làm phép nội suy suy biến và cho ra khóa sai một cách âm thầm, nên phải bị "
              "từ chối một cách tường minh và có thông báo dễ hiểu. Cổng hoành độ khác không loại bỏ các "
              "mảnh giả mạo hoặc hỏng. Cổng đếm số mảnh cho ra một mã lỗi riêng kèm số hiện có và số "
              "cần. Cổng ràng buộc tải trọng bảo đảm người dùng không ghép nhầm mảnh của lần chia này "
              "với tệp tải trọng của lần chia khác."),
        ("p", "Điểm chung của cả năm cổng: chúng đều kiểm tra các sự kiện **không bí mật** và đều chạy "
              "**trước** bất kỳ phép tính mật mã nào. Điều này cho phép hệ thống đưa ra thông báo cụ thể "
              "và hữu ích cho các lỗi thao tác thông thường, trong khi vẫn giữ nguyên tính hợp nhất của "
              "mã lỗi chứng thực."),
        ("p", "Mô-đun còn giải quyết một vấn đề trải nghiệm đáng chú ý: khi người dùng chia một **tệp**, "
              "họ mong muốn khôi phục lại được tệp với đúng tên và phần mở rộng ban đầu. Nhưng lưu tên "
              "tệp ở dạng rõ sẽ làm lộ thông tin. Giải pháp là một cơ chế đóng khung tên: tên tệp gốc "
              "được đặt **vào bên trong vùng sẽ được mã hóa**, phía trước nội dung. Khi khôi phục, tên "
              "được lấy ra, làm sạch thành tên cơ sở thuần túy để loại bỏ mọi ký tự phân cách đường dẫn, "
              "rồi dùng để đặt tên tệp kết quả. Việc làm sạch là bắt buộc vì tên tệp nằm trong vùng do "
              "người tạo mảnh kiểm soát, và một tên độc hại có thể chứa chuỗi vượt cấp thư mục."),

        ("h3", "4.4. Chuyển mảnh qua mã QR"),
        ("p", "Mô-đun mã QR là mô-đun đơn giản nhất về mặt mật mã: nó **hoàn toàn không có mật mã**. Nó "
              "chỉ nhận một chuỗi văn bản, dựng thành ảnh QR ở mức sửa lỗi cao nhất, và ở chiều ngược "
              "lại thì đọc một ảnh và trả về chuỗi."),
        ("p", "Sự đơn giản này là có chủ đích và đáng được ghi nhận như một quyết định thiết kế tốt. "
              "Mô-đun không biết gì về ngữ nghĩa của chuỗi mà nó vận chuyển; nó không biết đó là một "
              "mảnh Shamir. Nhờ vậy nó không thể vô tình vi phạm bất kỳ bất biến an toàn nào của lược đồ "
              "chia sẻ. Và vì chuỗi mảnh bản thân đã là dữ liệu **không bí mật** — nó chỉ là một điểm "
              "trên đa thức, vô nghĩa nếu không đủ ngưỡng — nên việc in nó ra giấy dưới dạng mã QR không "
              "làm giảm mức bảo đảm."),
        ("p", "Về mặt làm cứng, mô-đun áp trần kích thước tệp ảnh đầu vào, trần kích thước điểm ảnh và "
              "trần cấp phát bộ nhớ khi giải nén, nhằm chống các tệp ảnh được chế tác để gây cạn kiệt bộ "
              "nhớ. Nguyên tắc **hỏng theo hướng an toàn** cũng được áp dụng: nếu không tìm thấy mã QR "
              "hoặc không giải mã được, mô-đun trả về lỗi rõ ràng chứ không bao giờ trả về một kết quả "
              "sai."),

        ("h3", "4.5. Mô-đun giấu tin"),
        ("p", "Mô-đun giấu tin được tổ chức theo một nguyên tắc mà tài liệu của nó gọi là “che giấu không "
              "phải là bí mật”, thể hiện thành hai tầng tách biệt hoàn toàn."),
        ("fig", "Hinh-3-07-giau-tin-encrypt-then-embed",
         "Hình 3.7. Kiến trúc giấu tin theo nguyên tắc mã hóa rồi nhúng"),
        ("p", "Tầng bí mật dùng lại đúng cặp nguyên thủy mà mô-đun chia sẻ bí mật dùng — Argon2id kết "
              "hợp mã hóa có xác thực — và **không giới thiệu bất kỳ nguyên thủy nào mới**. Tầng che "
              "giấu nhúng các bit bản mã vào mặt bit thấp nhất của các mẫu màu, và tài liệu của nó tuyên "
              "bố thẳng rằng tầng này không đưa ra bất kỳ tuyên bố bảo mật nào."),
        ("p", "Hệ thống hỗ trợ hai họ sóng mang. Với ảnh không mất mát, các bit được nhúng trực tiếp vào "
              "giá trị mẫu màu. Với ảnh JPEG, việc nhúng diễn ra ở **miền hệ số biến đổi cosin rời rạc "
              "đã lượng tử hóa**, sau đó ảnh được mã hóa lại một cách không mất mát. Cả hai họ dùng chung "
              "khung dữ liệu, chung bộ niêm phong và chung đường xử lý lỗi."),
        ("p", "Khung dữ liệu nhúng có một chi tiết thiết kế đáng chú ý về thứ tự: phần header 54 byte "
              "được nhúng **tuần tự** vào 432 vị trí đầu tiên, còn phần thân mới đi theo lịch hoán vị. "
              "Lý do là lịch hoán vị được gieo từ muối, mà muối lại nằm trong header — nên header bắt "
              "buộc phải đọc được trước khi biết lịch. Đây là một ràng buộc kiểu “con gà và quả trứng” "
              "được giải quyết một cách gọn gàng."),
        ("p", "Về vai trò của lịch hoán vị, tài liệu mô-đun rất thẳng thắn: hạt giống là hàm băm của "
              "muối, mà muối là dữ liệu công khai nằm trong khung, nên **bất kỳ ai cũng tính lại được "
              "lịch**. Việc rải bit chỉ làm mờ các dấu hiệu thống kê thô sơ nhất, và **không phải là một "
              "thuộc tính an toàn**. Sự thẳng thắn này rất đáng ghi nhận, vì đây chính là chỗ mà nhiều "
              "công cụ giấu tin khác trình bày sai bản chất."),
        ("p", "Hai cơ chế bảo vệ nữa được cài đặt ở tầng dung lượng. Ở chiều nhúng, hệ thống kiểm tra "
              "dung lượng **trước khi chạy hàm dẫn xuất khóa**, nên một yêu cầu bất khả thi bị từ chối "
              "mà không tiêu tốn hàng trăm mili-giây tính toán. Ở chiều trích xuất, hệ thống kiểm tra "
              "**độ dài bản mã do khung khai báo** so với dung lượng thực tế của ảnh trước khi cấp phát "
              "bộ đệm — nếu không, một khung được chế tác có thể khai báo bốn tỉ byte và gây cạn kiệt bộ "
              "nhớ."),

        ("h3", "4.6. Bảng dò tìm dấu hiệu giấu tin"),
        ("p", "Mô-đun dò tìm chạy một bảng các bộ dò độc lập và hợp nhất kết quả thành một mức nghi ngờ."),
        ("fig", "Hinh-3-08-phat-hien-giau-tin",
         "Hình 3.8. Bảng các bộ dò giấu tin và cơ chế hợp nhất mức nghi ngờ"),
        ("p", "Với ảnh không mất mát, bảng gồm ba bộ dò thuộc hai họ khác nhau. Bộ dò dữ liệu nối thêm "
              "làm việc trên chuỗi byte thô: nó tìm dữ liệu nằm sau điểm kết thúc hợp lệ của ảnh, đo "
              "entropy của phần dữ liệu thừa đó, và quét các chuỗi nhận dạng của các định dạng tệp phổ "
              "biến. Hai bộ dò còn lại làm việc trên điểm ảnh đã giải mã, hiện thực hai phương pháp "
              "thống kê kinh điển đã nêu ở Chương 1. Với ảnh JPEG, bảng gồm hai bộ dò khác: một cho dữ "
              "liệu nối sau dấu kết thúc, và một cho kiểm định thống kê **trên hệ số biến đổi** — vì các "
              "bit thấp của điểm ảnh JPEG sau giải nén chỉ là hiện vật của phép lượng tử hóa chứ không "
              "phải miền nhúng."),
        ("p", "Cơ chế hợp nhất lấy **điểm cao nhất** trong bảng thay vì lấy trung bình. Lựa chọn này phù "
              "hợp với mục đích: chỉ cần một bộ dò phát tín hiệu mạnh là đủ để cảnh báo, và việc lấy "
              "trung bình sẽ làm loãng tín hiệu đó."),
        ("p", "Điểm đáng ghi nhận nhất của mô-đun này là **tính trung thực trong cách trình bày kết "
              "quả**. Thang đánh giá có bốn mức, và mức thấp nhất được đặt tên là “không quan sát thấy” "
              "chứ **không phải** “sạch”. Mỗi báo cáo đều kèm một câu cảnh báo cố định nói rõ rằng nghi "
              "ngờ tăng không phải là bằng chứng và không có tín hiệu cũng không phải là bằng chứng vắng "
              "mặt. Tài liệu mô-đun còn đi xa hơn khi tự thừa nhận rằng một tải trọng do chính mô-đun "
              "giấu tin của hệ thống tạo ra — đã mã hóa, đã hoán vị và ở tỉ lệ nhúng thấp — thì **gần "
              "như không bị các bộ dò này phát hiện**. Việc một hệ thống công bố giới hạn của chính công "
              "cụ dò tìm của mình là điều hiếm gặp và đáng được ghi nhận."),

        ("h3", "4.7. Mô-đun thủy vân"),
        ("p", "Mô-đun thủy vân trả lời một câu hỏi rất hẹp: tấm ảnh này có bị thay đổi kể từ khi được "
              "đánh dấu, bởi một người không có khóa, hay không?"),
        ("fig", "Hinh-3-09-thuy-van-de-vo",
         "Hình 3.9. Thủy vân vô hình, có khóa, dễ vỡ: nhúng và kiểm tra"),
        ("p", "Cơ chế dựa trên một ý tưởng gọn gàng. Ảnh được chia thành các khối 16 × 16 điểm ảnh. Với "
              "mỗi khối, hệ thống tính một nhãn bằng hàm băm có khóa trên nội dung khối, rồi rải 256 bit "
              "nhãn đó lên mặt bit thấp nhất của **kênh lam** trong chính khối đó. Chìa khóa của thiết "
              "kế nằm ở định nghĩa “nội dung”: nó là **bảy bit cao** của ba kênh màu, tức là mặt bit "
              "thấp nhất bị loại khỏi phép băm. Nhờ vậy, việc ghi nhãn vào mặt bit thấp nhất không làm "
              "thay đổi nội dung, và do đó không làm thay đổi chính nhãn — hệ thống tự nhất quán."),
        ("p", "Một cơ chế thứ hai giải quyết một vấn đề mà thiết kế ban đầu bỏ sót. Nếu chỉ dựa vào nhãn "
              "theo khối, hệ thống không phân biệt được ba tình huống: ảnh chưa từng được đánh dấu, ảnh "
              "được đánh dấu bằng khóa khác, và ảnh được đánh dấu đúng khóa nhưng đã bị sửa nặng tới mức "
              "mọi khối đều hỏng. Giải pháp là một **dấu hiệu hiện diện** độc lập nội dung, dẫn xuất từ "
              "khóa cùng kích thước ảnh, rải trên mặt bit thấp nhất của kênh lục. Phép kiểm trước hết "
              "hỏi “có dấu của khóa này không” dựa trên tỉ lệ khớp của dấu hiệu, rồi mới hỏi “nội dung "
              "có nguyên vẹn không”."),
        ("p", "Ngưỡng nhận biết dấu hiệu được đặt ở 75 phần trăm. Con số này nằm khá xa mức 50 phần trăm "
              "mà một ảnh chưa đánh dấu hoặc một khóa sai sẽ cho ra do ngẫu nhiên, nên xác suất báo "
              "nhầm là rất nhỏ; đồng thời nó đủ khoan dung để chịu được một sửa đổi cục bộ ảnh hưởng tới "
              "khoảng một phần tư số điểm ảnh."),
        ("p", "Kết quả kiểm tra là một thang ba mức, trong đó mức “bị sửa” còn kèm theo **danh sách các "
              "khối hỏng**, cho phép định vị được vùng ảnh đã bị can thiệp. Cần nhấn mạnh lại rằng tính "
              "dễ vỡ là **đặc tính chứ không phải khuyết điểm**: bất kỳ thao tác biên tập nào, kể cả nén "
              "lại sang JPEG, đều làm hỏng dấu. Dự án ghi nhận rõ rằng họ thủy vân **bền vững** là hướng "
              "nghiên cứu **chưa được hiện thực hóa**, với lý do cụ thể là chưa có thư viện biến đổi "
              "sóng con hai chiều thuần Rust đủ tin cậy để xây dựng."),

        ("h3", "4.8. Mô-đun phân tích siêu dữ liệu"),
        ("p", "Mô-đun này điều khiển công cụ ExifTool như một tiến trình con, theo đúng tinh thần đã áp "
              "dụng với công cụ age nhưng với một biện pháp bổ sung rất quan trọng. ExifTool là chương "
              "trình Perl có cơ chế cấu hình bằng **mã Perl thực thi được** — đây là bề mặt thực thi mã "
              "từ xa nguy hiểm nhất của công cụ. Hệ thống vô hiệu hóa cơ chế này bằng cách truyền tham "
              "số cấu hình rỗng làm **hai tham số đầu tiên** của mọi lời gọi, không có ngoại lệ nào."),
        ("p", "Bên cạnh đó, tiến trình con được chạy trong một **thư mục làm việc dùng một lần**, với "
              "biến môi trường đã xóa và chỉ được cấp lại một đường dẫn tìm chương trình tối thiểu do "
              "chính lớp bọc quyết định chứ không kế thừa từ môi trường người dùng, luồng vào bị đóng, "
              "và có hạn giờ 60 giây."),
        ("p", "Về mặt chức năng, điều đáng phân tích nhất là cách mô-đun xử lý thao tác xóa siêu dữ liệu, "
              "vì đây là chỗ dễ đưa ra bảo đảm sai nhất. Hệ thống phân loại định dạng thành ba nhóm với "
              "ba mức bảo đảm khác nhau. Nhóm thứ nhất là các định dạng mà công cụ **thực sự ghi lại "
              "được**; danh sách này được lấy từ chính danh sách kiểu ghi được của công cụ và được thu "
              "hẹp một cách bảo thủ về các họ ảnh, âm thanh, video và ảnh thô phổ biến. Nhóm thứ hai là "
              "định dạng PDF, nơi cơ chế sửa đổi tăng dần khiến thao tác xóa chỉ là ghi thêm một bản cập "
              "nhật — dữ liệu cũ vẫn còn trong tệp. Nhóm thứ ba là các định dạng chỉ đọc, và hệ thống "
              "**từ chối thẳng** thay vì làm ra vẻ đã xử lý."),
        ("p", "Nguyên tắc thiết kế ở đây là **bảo thủ và hỏng theo hướng an toàn**: một định dạng có thể "
              "ghi được nhưng không nằm trong danh sách sẽ bị từ chối, chứ không bao giờ được báo cáo "
              "sai là “đã làm sạch”. Việc báo cáo trung thực mức bảo đảm theo từng định dạng, thay vì "
              "luôn hiển thị một thông báo thành công, là một quyết định thiết kế đáng ghi nhận trong "
              "một lĩnh vực mà việc phóng đại bảo đảm là rất phổ biến."),
        ("p", "Cuối cùng, cần nêu rõ trạng thái triển khai: nhị phân ExifTool được đánh dấu là **tùy "
              "chọn**. Trong cây mã nguồn hiện tại, thư mục chứa nhị phân đi kèm chỉ có tài liệu hướng "
              "dẫn chứ chưa có nhị phân thật, nên một bản dựng trực tiếp từ cây mã này sẽ có mô-đun "
              "Phân tích ở trạng thái **tắt an toàn**."),
    ]

    # ============================= 5. Lop ung dung va giao dien
    B += [
        ("h2", "5. Xây dựng lớp ứng dụng và giao diện người dùng"),

        ("h3", "5.1. Bề mặt lệnh và các trạng thái quản lý"),
        ("p", "Lớp ứng dụng đóng vai trò gốc lắp ghép: nó là nơi duy nhất các bộ điều hợp cụ thể được "
              "nối vào các dịch vụ nghiệp vụ, và là nơi duy nhất các kiểu dữ liệu của biên giao tiếp "
              "được chuyển đổi thành kiểu dữ liệu nghiệp vụ."),
        ("fig", "Hinh-3-10-ban-do-lenh-ipc",
         "Hình 3.10. Bản đồ ba mươi tám lệnh IPC và năm trạng thái quản lý"),
        ("p", "Ba mươi tám lệnh được phân thành năm nhóm, mỗi nhóm gắn với một trạng thái quản lý riêng. "
              "Cách phân nhóm này có một hệ quả kiến trúc rõ ràng: bốn nhóm ngoài nhóm két hoàn toàn "
              "**không lưu trạng thái** và **không nhận tham số phiên**. Chúng là các hàm thuần túy trên "
              "đường dẫn tệp và mật khẩu. Điều này khiến chúng dễ kiểm thử hơn nhiều và thu hẹp đáng kể "
              "vùng bộ nhớ có thể chứa bí mật."),
        ("p", "Việc thêm một mô-đun mới vào hệ thống, theo kiến trúc này, là một thao tác **cộng thêm** "
              "thuần túy: thêm một crate nghiệp vụ, thêm một bề mặt lệnh, đăng ký thêm một trạng thái "
              "quản lý, và thêm một nhóm màn hình. Không có thành phần nào đã có phải sửa đổi. Đây là "
              "một thuộc tính kiến trúc có giá trị thực tiễn cao và đã được kiểm chứng qua chính lịch sử "
              "phát triển của dự án: các mô-đun giấu tin, thủy vân, mã QR và siêu dữ liệu đều được bổ "
              "sung sau khi mô-đun két đã hoàn thiện, mà không phải thay đổi mô-đun két."),

        ("h3", "5.2. Xử lý mật khẩu tại biên giao tiếp"),
        ("p", "Mật khẩu là dữ liệu duy nhất thực sự bí mật phải đi từ giao diện vào lõi, nên nó được xử "
              "lý bằng một kiểu dữ liệu chuyên dụng. Kiểu này có ba đặc tính: tự xóa nội dung khi bị "
              "hủy; che nội dung khi được in ra nhật ký gỡ lỗi; và cung cấp một phương thức chuyển đổi "
              "sang kiểu byte bí mật của tầng nghiệp vụ, đồng thời xóa bản sao của chính nó. Quy ước sử "
              "dụng là gọi phương thức chuyển đổi này ngay ở **dòng đầu tiên** của mỗi hàm xử lý lệnh."),
        ("p", "Điều quan trọng là dự án ghi nhận rất rõ **giới hạn** của biện pháp này. Mật khẩu đi qua "
              "cầu giao tiếp dưới dạng chuỗi trong một thông điệp JSON. Trước khi mã của hệ thống nhận "
              "được quyền kiểm soát, khung ứng dụng đã tạo ít nhất hai bản sao: bộ đệm thông điệp thô và "
              "bộ đệm phân tích cú pháp. Hệ thống **không thể** với tới hai bản sao đó để xóa."),
        ("p", "Chú thích trong mã nguồn gọi thẳng đây là “rủi ro tồn đọng được ghi nhận” và nêu ba biện "
              "pháp giảm thiểu thay thế: mã hóa toàn đĩa và mã hóa vùng trao đổi ở mức hệ điều hành, "
              "loại các lệnh này khỏi cơ chế ghi nhật ký tham số, và trong tương lai là chuyển sang một "
              "kênh nhập mật khẩu riêng nằm ngoài webview. Việc ghi nhận công khai một hạn chế không thể "
              "khắc phục trong kiến trúc hiện tại, thay vì im lặng, là cách xử lý đúng đắn."),

        ("h3", "5.3. Giao diện người dùng"),
        ("p", "Giao diện được xây dựng bằng HTML, CSS và JavaScript tĩnh, không dùng bất kỳ công cụ đóng "
              "gói nào. Lựa chọn này làm cho toàn bộ mã giao diện đọc được trực tiếp và kiểm toán được, "
              "đồng thời loại bỏ một cây phụ thuộc thời điểm xây dựng vốn cũng là một bề mặt tấn công "
              "chuỗi cung ứng."),
        ("fig", "Hinh-3-12-so-do-dieu-huong-giao-dien",
         "Hình 3.11. Sơ đồ điều hướng chính của giao diện người dùng"),
        ("p", "Hai mươi màn hình được nhóm theo mục tiêu người dùng như đã phân tích ở Chương 2. Các hình "
              "tiếp theo trình bày ảnh chụp thực tế của giao diện. Cần nêu rõ điều kiện chụp để người "
              "đọc đánh giá đúng: các ảnh này được chụp từ **chính mã giao diện thật của hệ thống**, "
              "kết xuất trong một trình duyệt không giao diện, **không có lõi Rust chạy phía sau**. Do "
              "đó chúng thể hiện chính xác bố cục, nhãn tiếng Việt và cấu trúc biểu mẫu của từng màn "
              "hình, nhưng **không** thể hiện kết quả của một thao tác thực. Các trạng thái có kết quả "
              "được đánh dấu bằng chỗ dành sẵn kèm hướng dẫn chụp lại, và được liệt kê đầy đủ trong tài "
              "liệu hướng dẫn chụp màn hình đi kèm báo cáo."),
        ("shot", "screen-home.png", "Hình 3.12. Màn hình Trang chủ với ba thẻ bắt đầu nhanh và lưới toàn bộ công cụ", SHOT),
        ("p", "Màn hình trang chủ cho thấy nguyên tắc tổ chức theo mục tiêu: thanh bên trái nhóm các công "
              "cụ thành năm nhóm mang tên hành động chứ không mang tên kỹ thuật, và khu vực chính đưa ra "
              "ba lối tắt cho các tác vụ được dự đoán là phổ biến nhất."),
        ("shot", "screen-vault.png", "Hình 3.13. Màn hình Két an toàn ở trạng thái đã khóa", SHOT),
        ("p", "Màn hình két gồm hai thẻ: mở két đã có và tạo két mới. Chi tiết đáng chú ý nằm ở thẻ tạo "
              "két: có **hai ô mật khẩu** với ô thứ hai để nhập lại, kèm dòng cảnh báo “Gõ sai ở đây sẽ "
              "khiến bạn mất quyền truy cập vĩnh viễn”. Đây không phải là một chi tiết trang trí mà là "
              "kết quả trực tiếp của một khiếm khuyết mức nghiêm trọng được phát hiện trong chiến dịch "
              "kiểm chứng, sẽ trình bày ở Chương 4."),
        ("ph", "[CHỖ DÀNH SẴN – CHÈN ẢNH CHỤP MÀN HÌNH KÉT AN TOÀN Ở TRẠNG THÁI ĐÃ MỞ KHÓA]",
         "Cần ảnh chụp màn hình két sau khi mở khóa thành công, hiển thị dải trạng thái “ĐÃ MỞ”, "
         "danh sách các tệp bên trong kèm kích thước và vân tay rút gọn, cùng các nút thêm tệp, "
         "trích xuất, đổi mật khẩu và chia khóa. Xem hướng dẫn chi tiết trong tệp MANUAL_SCREENSHOTS.md."),
        ("shot", "screen-encrypt.png", "Hình 3.14. Màn hình Khóa tệp — mã hóa một tệp bằng mật khẩu", SHOT),
        ("shot", "screen-sign.png", "Hình 3.15. Màn hình Ký tệp — tạo cặp khóa ký và ký tệp", SHOT),
        ("p", "Màn hình ký tệp minh họa cách giao diện xử lý một khái niệm khó: nó tách rõ hai việc là "
              "tạo cặp khóa ký và dùng khóa đó để ký, đồng thời làm rõ rằng khóa bí mật được cất ở dạng "
              "đã mã hóa bằng chính mật khẩu người dùng nhập."),
        ("shot", "screen-verify-integrity.png",
         "Hình 3.16. Màn hình Xác minh tệp tải về — kiểm theo giá trị băm và/hoặc chữ ký", SHOT),
        ("p", "Đây là màn hình thể hiện rõ nhất sự phân biệt giữa toàn vẹn và xuất xứ đã phân tích ở "
              "Chương 1: người dùng có thể cung cấp một giá trị băm công bố, một cặp chữ ký và khóa công "
              "khai, hoặc cả hai; và báo cáo trả về nêu rõ từng phép kiểm đã được yêu cầu và kết quả của "
              "từng phép, thay vì gộp thành một phán quyết duy nhất."),
        ("shot", "screen-split-secret.png", "Hình 3.17. Màn hình Chia nhỏ bí mật theo ngưỡng k trong n", SHOT),
        ("shot", "screen-recover-pieces.png",
         "Hình 3.18. Màn hình Khôi phục từ các mảnh — nhận cả tệp mảnh và chuỗi dán vào", SHOT),
        ("ph", "[CHỖ DÀNH SẴN – CHÈN ẢNH CHỤP DANH SÁCH MẢNH SAU KHI CHIA THÀNH CÔNG]",
         "Cần ảnh chụp kết quả sau khi chia một bí mật thành 5 mảnh với ngưỡng 3, hiển thị đường dẫn "
         "tệp tải trọng, danh sách năm tệp mảnh và năm chuỗi Base64 chép tay được. Xem MANUAL_SCREENSHOTS.md."),
        ("shot", "screen-hide.png", "Hình 3.19. Màn hình Giấu dữ liệu trong ảnh", SHOT),
        ("shot", "screen-detect.png", "Hình 3.20. Màn hình Phát hiện dữ liệu ẩn", SHOT),
        ("ph", "[CHỖ DÀNH SẴN – CHÈN ẢNH CHỤP BÁO CÁO PHÁT HIỆN GIẤU TIN]",
         "Cần ảnh chụp báo cáo sau khi chạy dò trên một ảnh có dữ liệu nối thêm, hiển thị mức nghi ngờ "
         "(High/Elevated/Low/NotObserved), điểm số của từng bộ dò và câu cảnh báo cố định về giới hạn "
         "của phương pháp thực nghiệm. Xem MANUAL_SCREENSHOTS.md."),
        ("shot", "screen-watermark.png", "Hình 3.21. Màn hình Chống giả mạo tệp — nhúng và kiểm tra thủy vân", SHOT),
        ("shot", "screen-qr-transfer.png", "Hình 3.22. Màn hình Chuyển mảnh qua mã QR an toàn", SHOT),
        ("shot", "screen-metadata-inspect.png",
         "Hình 3.23. Màn hình Xem siêu dữ liệu ở trạng thái mô-đun chưa sẵn sàng", SHOT),
        ("p", "Ảnh chụp này minh họa nguyên tắc **hỏng theo hướng an toàn** đã phân tích ở mục 4.8: khi "
              "nhị phân ExifTool không có mặt trong bản dựng, giao diện hiển thị một biểu ngữ giải thích "
              "và **vô hiệu hóa các nút thao tác**, thay vì để người dùng nhấn nút và nhận về một lỗi "
              "nội bộ khó hiểu. Trạng thái này phản ánh đúng một bản dựng từ cây mã nguồn hiện tại."),
    ]

    # ================================== 6. Lam cung va dong goi
    B += [
        ("h2", "6. Làm cứng và đóng gói hệ thống"),

        ("h3", "6.1. Chuỗi kiểm soát nhị phân ngoài"),
        ("p", "Việc nhúng chương trình ngoài vào một ứng dụng bảo mật được xử lý bằng một chuỗi sáu biện "
              "pháp nối tiếp, trải từ thời điểm biên dịch tới thời điểm thực thi."),
        ("fig", "Hinh-3-11-ghim-bam-nhi-phan",
         "Hình 3.24. Ghim băm nhị phân ngoài lúc biên dịch và phân giải lúc chạy"),
        ("p", "Biện pháp thứ nhất là **ghim băm lúc biên dịch**: kịch bản dựng tính giá trị băm BLAKE3 "
              "của từng nhị phân và phát nó ra dưới dạng hằng số được nhúng thẳng vào mã máy. Biện pháp "
              "thứ hai là **kiểm tra kiến trúc tệp**: kịch bản đọc phần đầu của tệp nhị phân để nhận "
              "dạng định dạng thực thi và kiến trúc bộ xử lý, **hoàn toàn không thực thi tệp**, và làm "
              "hỏng bản dựng phát hành nếu phát hiện một nhị phân bắt buộc sai kiến trúc — đây là loại "
              "lỗi mà bản thân phép ghim băm không phát hiện được vì một tệp sai kiến trúc vẫn có băm "
              "hợp lệ của chính nó."),
        ("p", "Biện pháp thứ ba là **đóng bề mặt phân giải đường dẫn**: trong bản dựng gỡ lỗi, các biến "
              "môi trường cho phép chỉ định đường dẫn nhị phân — rất tiện cho phát triển và kiểm thử. "
              "Trong bản phát hành, các biến này bị **bỏ qua hoàn toàn** và hệ thống chỉ tìm nhị phân "
              "trong thư mục tài nguyên của gói cài hoặc thư mục cạnh tệp thực thi. Về mặt lý thuyết, "
              "phép ghim băm đã đủ để chặn một nhị phân sai; việc đóng thêm bề mặt phân giải là một lớp "
              "phòng thủ bổ sung."),
        ("p", "Biện pháp thứ tư là **xác minh lại lúc chạy**: hàm khởi tạo bộ điều hợp tính lại băm của "
              "tệp nhị phân và từ chối khởi tạo nếu không khớp. Hai biện pháp cuối là môi trường thực "
              "thi đã được làm cứng và hạn giờ tường, đã trình bày ở mục 3.4."),
        ("p", "Hai khoảng trống của chuỗi này cần được ghi nhận. Thứ nhất, phép kiểm băm chỉ diễn ra một "
              "lần lúc khởi tạo; nếu tệp bị thay thế giữa lần kiểm và lần thực thi, hệ thống không phát "
              "hiện được. Thứ hai, và nghiêm trọng hơn về mặt thực tiễn, gói cài hiện chưa được ký số và "
              "công chứng."),

        ("h3", "6.2. Đóng gói và tư thế phát hành"),
        ("p", "Gói cài được sinh bằng công cụ dựng của khung ứng dụng, với các nhị phân ngoài được khai "
              "báo là tài nguyên của gói. Chế độ đóng gói được bật cho tất cả các định dạng gói mà nền "
              "tảng hỗ trợ."),
        ("p", "Về tư thế phát hành, cần trình bày một cách trung thực và đầy đủ. Gói cài **không được ký "
              "số và không được công chứng**. Dự án tuyên bố rõ rằng đây là công cụ dùng nội bộ nên việc "
              "ký số nằm ngoài phạm vi. Tuy nhiên hệ quả kỹ thuật của quyết định này đã được kiểm chứng "
              "bằng thực nghiệm và không hề nhẹ: trên macOS, một bản sao nhị phân mang nhãn cách ly do "
              "hệ thống gắn khi tải về được xác nhận là **bị chấm dứt bởi cơ chế kiểm soát của hệ điều "
              "hành**, và hệ quả trong sản phẩm là thao tác tạo két thất bại ngay lần chạy đầu tiên."),
        ("p", "Đây là một ví dụ điển hình về khoảng cách giữa “chạy được trên máy của người phát triển” "
              "và “chạy được trên máy của người dùng”: các bản dựng phát triển không mang nhãn cách ly "
              "nên hoàn toàn không gặp vấn đề này. Chương 4 sẽ trình bày chi tiết bằng chứng thực nghiệm."),

        ("h3", "6.3. Quy trình tích hợp liên tục"),
        ("p", "Quy trình tích hợp liên tục gồm năm nhóm việc, được trình bày chi tiết ở Chương 4 cùng "
              "với kết quả chạy thực tế. Ở đây chỉ nêu điểm đáng chú ý nhất về mặt thiết kế quy trình: "
              "nhóm việc chính chạy trên **ma trận ba hệ điều hành** và có bước cài đặt công cụ age thật "
              "để chạy các kiểm thử đầu-cuối vốn bị bỏ qua trên máy phát triển thông thường."),
        ("p", "Chính bước này đã tạo ra bằng chứng đóng lại một giả thuyết rủi ro quan trọng: lo ngại "
              "rằng việc xóa sạch biến môi trường sẽ làm hỏng bộ sinh số ngẫu nhiên hoặc trình nạp thư "
              "viện động của công cụ age trên Windows. Giả thuyết này không thể kiểm chứng trên máy "
              "macOS của người phát triển, và chỉ được giải quyết khi kiểm thử chạy trên một máy Windows "
              "thật trong môi trường tích hợp liên tục."),
    ]

    B += [
        ("h2", "Kết luận chương 3"),
        ("p", "Chương 3 đã trình bày quá trình hiện thực hóa các thiết kế của Chương 2 thành khoảng "
              "16 300 dòng mã Rust. Ba nhóm kết quả nổi bật."),
        ("p", "Thứ nhất, về **tổ chức mã nguồn**, việc tách tầng hợp đồng khỏi tầng hiện thực đã cho "
              "kết quả đúng như thiết kế dự kiến: crate nghiệp vụ của két có đồ thị phụ thuộc hoàn toàn "
              "không chứa FFI, toàn bộ vòng đời của két kiểm thử được bằng một bộ mã hóa giả lập, và "
              "việc bổ sung bốn mô-đun mới sau khi mô-đun két hoàn thiện đã diễn ra hoàn toàn theo cách "
              "cộng thêm, không phải sửa đổi."),
        ("p", "Thứ hai, về **các kỹ thuật hiện thực đáng ghi nhận**, chương đã phân tích một số giải "
              "pháp có giá trị tham khảo: dùng hệ thống kiểu dữ liệu để cưỡng chế thuộc tính an toàn "
              "thay vì dựa vào kỷ luật lập trình; đóng băng các hằng số có ảnh hưởng tới khả năng mở "
              "két bằng kiểm thử; kiến trúc ba luồng để tránh khóa chết giữa các ống dẫn khi điều khiển "
              "tiến trình con; và cơ chế đóng khung tên tệp vào bên trong vùng mã hóa."),
        ("p", "Thứ ba, về **tính trung thực trong tài liệu hóa**, chương đã ghi nhận đầy đủ các trạng "
              "thái chưa hoàn tất: cơ chế hiệu chỉnh tham số theo phần cứng đã có mã nhưng chưa được nối "
              "vào đường tạo két; cổng kiểm tra tương thích chữ ký với công cụ chuẩn đã được thiết kế "
              "nhưng chưa nối dây; việc truyền dòng cho tải trọng chưa được hiện thực; một số chú thích "
              "trong mã đã lỗi thời so với hành vi thật; và gói cài chưa được ký số. Việc phân biệt rành "
              "mạch giữa cái đã làm, cái đã có mã nhưng chưa nối, và cái mới nằm trong kế hoạch là điều "
              "kiện cần để Chương 4 có thể đánh giá hệ thống một cách có căn cứ."),
    ]
    return B
