# -*- coding: utf-8 -*-
"""MO DAU."""


def blocks():
    return [
        ("h1", "MỞ ĐẦU"),

        ("h2", "1. Tính cấp thiết của đề tài"),
        ("p", "Trong khoảng một thập niên trở lại đây, trọng tâm của bài toán bảo vệ dữ liệu đã dịch "
              "chuyển đáng kể. Nếu như trước đây phần lớn nỗ lực được đặt vào việc bảo vệ đường truyền và "
              "bảo vệ máy chủ, thì hiện nay một tỷ lệ rất lớn dữ liệu nhạy cảm lại nằm rải rác trên các "
              "thiết bị đầu cuối: máy tính xách tay của cán bộ, ổ cứng di động, thẻ nhớ, máy tính cá nhân "
              "dùng chung. Đây chính là nhóm tài sản dễ bị đánh mất, dễ bị thu giữ và cũng khó áp đặt "
              "chính sách quản trị nhất. Một tệp tài liệu được truyền đi an toàn qua kênh mã hóa nhưng "
              "sau đó nằm nguyên dạng rõ trong thư mục Tải xuống của máy nhận thì rốt cuộc vẫn là một "
              "lỗ hổng."),
        ("p", "Song song với đó, nhu cầu chia sẻ tệp giữa các cá nhân và tổ chức ngày càng thường xuyên, "
              "kéo theo một nhóm rủi ro khác mà các giải pháp mã hóa toàn đĩa không giải quyết được. Mã "
              "hóa toàn đĩa chỉ bảo vệ dữ liệu khi máy tắt; ngay khi hệ điều hành đã khởi động và người "
              "dùng đã đăng nhập, mọi tệp đều ở dạng rõ đối với bất kỳ tiến trình nào đang chạy. Hơn nữa, "
              "mã hóa toàn đĩa không đi theo tệp: khi người dùng sao chép một tệp sang thẻ nhớ hoặc gửi "
              "qua thư điện tử, lớp bảo vệ đó biến mất hoàn toàn."),
        ("p", "Một khoảng trống thứ ba, ít được chú ý hơn nhưng gây hậu quả rất thực tế, là **tính toàn "
              "vẹn và xuất xứ**. Người dùng thường xuyên nhận được tệp từ nguồn không hoàn toàn tin cậy — "
              "một bản cài đặt tải về từ Internet, một tài liệu được chuyển tiếp qua nhiều khâu — nhưng "
              "lại không có công cụ đủ đơn giản để trả lời câu hỏi rất cơ bản: “tệp này có đúng là tệp mà "
              "người gửi đã tạo ra hay không?”. Các công cụ dòng lệnh cho việc này đã tồn tại từ lâu, "
              "song rào cản sử dụng khiến chúng gần như không được dùng ngoài giới kỹ thuật."),
        ("p", "Khoảng trống thứ tư nằm ở khâu **sao lưu và khôi phục vật liệu khóa**. Mọi hệ thống mã hóa "
              "nghiêm túc đều đặt người dùng trước một tình thế nan giải: nếu mật khẩu đủ mạnh để chống "
              "được tấn công vét cạn thì nó cũng đủ khó để người dùng quên; mà một khi đã quên thì dữ "
              "liệu mất vĩnh viễn. Ghi mật khẩu ra giấy và cất một chỗ là giải pháp phổ biến nhưng tạo "
              "ra một điểm hỏng đơn lẻ mới. Lý thuyết chia sẻ bí mật theo ngưỡng đã đưa ra lời giải toán "
              "học cho vấn đề này từ năm 1979, nhưng số phần mềm dân dụng thực sự đưa nó tới tay người "
              "dùng cuối vẫn rất ít."),
        ("p", "Cuối cùng, một loạt rủi ro riêng tư “ngoài nội dung” hầu như bị bỏ qua trong các bộ công cụ "
              "phổ thông: siêu dữ liệu nhúng trong ảnh và tài liệu có thể tiết lộ tọa độ chụp, thiết bị, "
              "tên tài khoản và lịch sử chỉnh sửa; một tấm ảnh được chia sẻ có thể đã bị chèn dữ liệu ẩn "
              "mà người nhận không hề hay biết; một tệp được phát tán lại có thể đã bị sửa nội dung ở một "
              "vùng nhỏ mà mắt thường không phát hiện. Những rủi ro này đòi hỏi các công cụ chuyên biệt, "
              "và hiện chúng nằm phân tán ở nhiều phần mềm khác nhau, phần lớn là công cụ dòng lệnh."),
        ("p", "Từ năm nhóm khoảng trống nêu trên, đề tài đặt vấn đề xây dựng một bộ công cụ thống nhất, "
              "chạy hoàn toàn ngoại tuyến trên máy người dùng, gom các năng lực bảo mật thiết yếu vào một "
              "giao diện duy nhất, đồng thời tuân thủ nghiêm ngặt nguyên tắc **chỉ lắp ghép các nguyên "
              "thủy mật mã đã được kiểm chứng**, tuyệt đối không tự thiết kế thuật toán mới. Tính cấp "
              "thiết của đề tài do đó không nằm ở việc phát minh ra kỹ thuật mật mã mới, mà nằm ở bài "
              "toán kỹ thuật hệ thống: lắp ghép đúng, ràng buộc đúng, xử lý lỗi đúng và trình bày đúng "
              "mức độ bảo đảm cho người dùng."),

        ("h2", "2. Mục tiêu nghiên cứu"),
        ("p", "Mục tiêu tổng quát của đề tài là nghiên cứu, thiết kế và xây dựng một hệ thống phần mềm "
              "máy tính để bàn cung cấp các dịch vụ bảo mật và riêng tư thiết yếu cho dữ liệu tại chỗ, "
              "hoạt động hoàn toàn ngoại tuyến, có kiến trúc an toàn rõ ràng và có khả năng chứng minh "
              "được các thuộc tính an toàn mà nó tuyên bố."),
        ("p", "Các mục tiêu cụ thể bao gồm: xây dựng một định dạng container mã hóa có xác thực và có "
              "chữ ký, che giấu được cả siêu dữ liệu về nội dung bên trong; thiết kế một phân cấp khóa "
              "trong đó khóa chủ không bao giờ chạm đĩa và mọi khóa dẫn xuất đều bị ràng buộc theo ngữ "
              "cảnh; hiện thực hóa cơ chế sao lưu và khôi phục khóa theo ngưỡng k trong n; cung cấp các "
              "dịch vụ mật mã mức tệp độc lập với két; bổ sung các mô-đun riêng tư gồm giấu tin, thủy vân "
              "dễ vỡ và xử lý siêu dữ liệu; và cuối cùng là thiết lập một mô hình lỗi không tạo ra kênh "
              "rò rỉ cho kẻ tấn công."),
        ("p", "Về phương diện học thuật, đề tài còn hướng tới một mục tiêu thứ hai: xây dựng một hồ sơ "
              "kiến trúc và kiểm chứng có thể truy vết được tới mã nguồn, trong đó mỗi tuyên bố an toàn "
              "đều gắn với một cơ chế hiện thực cụ thể và, nếu có thể, gắn với một hàm kiểm thử chứng "
              "minh cơ chế đó hoạt động."),

        ("h2", "3. Nhiệm vụ nghiên cứu"),
        ("p", "Để đạt được các mục tiêu trên, đề tài xác định các nhiệm vụ sau. Thứ nhất, nghiên cứu cơ "
              "sở lý thuyết về mã hóa có xác thực, hàm băm mật mã, hàm dẫn xuất khóa từ mật khẩu, chữ ký "
              "số, chia sẻ bí mật theo ngưỡng, giấu tin và thủy vân số, cùng với các mô hình đe dọa "
              "thường gặp đối với dữ liệu tại chỗ."),
        ("p", "Thứ hai, khảo sát các công cụ hiện có trong từng nhóm chức năng, phân tích ưu điểm, nhược "
              "điểm và khoảng trống, từ đó xác định phạm vi chức năng của hệ thống cần xây dựng."),
        ("p", "Thứ ba, phân tích yêu cầu chức năng và phi chức năng, xây dựng mô hình đe dọa, xác định "
              "ranh giới tin cậy và thiết kế kiến trúc hệ thống theo hướng phân tầng, tiêm phụ thuộc và "
              "tách biệt rõ giữa hợp đồng và hiện thực."),
        ("p", "Thứ tư, thiết kế các định dạng dữ liệu trên đĩa, phân cấp khóa và các quy trình xử lý, "
              "trong đó đặc biệt chú ý tới thứ tự các cổng kiểm tra để bảo đảm tính chống dò kênh lỗi."),
        ("p", "Thứ năm, hiện thực hóa hệ thống bằng ngôn ngữ Rust với kỷ luật cấm mã không an toàn, tích "
              "hợp các thư viện mật mã đã được cộng đồng kiểm chứng, và làm cứng các tiến trình con ngoài."),
        ("p", "Thứ sáu, xây dựng bộ kiểm thử ở nhiều mức, tổ chức chiến dịch kiểm chứng các giả thuyết "
              "rủi ro trên đúng đường mã sản phẩm, đo đạc hiệu năng và tiêu thụ tài nguyên, sau đó đánh "
              "giá trung thực những gì đã đạt được và những gì còn tồn đọng."),

        ("h2", "4. Đối tượng nghiên cứu"),
        ("p", "Đối tượng nghiên cứu của đề tài là hệ thống phần mềm Secure Vault Research: kiến trúc "
              "phần mềm, kiến trúc mật mã, mô hình dữ liệu trên đĩa, cơ chế quản lý khóa, mô hình đe dọa "
              "cùng các cơ chế phòng vệ, và phương pháp kiểm chứng các thuộc tính an toàn của hệ thống."),
        ("p", "Cùng với đó, đề tài cũng nghiên cứu các nguyên thủy mật mã mà hệ thống sử dụng — Argon2id, "
              "BLAKE3, XSalsa20-Poly1305, age (X25519 kết hợp ChaCha20-Poly1305), Ed25519 ở định dạng "
              "minisign và lược đồ chia sẻ bí mật Shamir — không phải để cải tiến chúng, mà để hiểu đúng "
              "giả thiết an toàn, phạm vi áp dụng và cách lắp ghép chúng sao cho không phá vỡ các giả "
              "thiết đó."),

        ("h2", "5. Phạm vi nghiên cứu"),
        ("p", "Về phạm vi chức năng, đề tài giới hạn ở sáu mô-đun đã được hiện thực hóa: Két an toàn, "
              "Mật mã tệp, Chia sẻ bí mật, Giấu tin trong ảnh, Thủy vân dễ vỡ và Phân tích siêu dữ liệu. "
              "Các hướng như thủy vân bền vững, tích hợp mô-đun bảo mật phần cứng, đồng bộ đám mây hay "
              "quản lý khóa phân tán được xác định rõ là **nằm ngoài phạm vi** và chỉ được nhắc tới "
              "trong phần hướng phát triển."),
        ("p", "Về phạm vi triển khai, hệ thống hướng tới mô hình một người dùng, một máy, không có máy "
              "chủ, không có tài khoản và không có kênh mạng. Đơn vị chia sẻ duy nhất là một tệp mà "
              "người dùng tự di chuyển bằng phương tiện của mình."),
        ("p", "Về phạm vi bảo đảm an toàn, hệ thống chống lại kẻ tấn công có được tệp ở trạng thái tĩnh, "
              "kẻ tấn công sửa đổi tệp, tệp đầu vào độc hại và kẻ tấn công dò kênh lỗi ở biên giao tiếp. "
              "Hệ thống **không** đặt mục tiêu chống lại kẻ tấn công đã chiếm được quyền đọc bộ nhớ của "
              "tiến trình đang chạy hoặc đã kiểm soát hệ điều hành; đây là giới hạn được tuyên bố công "
              "khai chứ không phải điều bị bỏ sót."),
        ("p", "Về phạm vi đánh giá hiệu năng, các số đo trong báo cáo được lấy từ tài liệu kiểm chứng của "
              "dự án, thực hiện trên một cấu hình duy nhất. Báo cáo không ngoại suy các số đo này thành "
              "kết luận tổng quát về hiệu năng, và mọi giá trị mang tính ngoại suy đều được ghi nhãn rõ."),

        ("h2", "6. Phương pháp nghiên cứu"),
        ("p", "Đề tài kết hợp bốn phương pháp. **Phương pháp nghiên cứu tài liệu** được dùng để hệ thống "
              "hóa cơ sở lý thuyết về mật mã ứng dụng và các khuyến nghị tham số hiện hành, đặc biệt là "
              "sàn tham số Argon2id do OWASP khuyến nghị mà hệ thống áp dụng trực tiếp trong mã."),
        ("p", "**Phương pháp phân tích mã nguồn** là phương pháp chủ đạo. Toàn bộ nội dung kỹ thuật của "
              "báo cáo được tái dựng từ khoảng 16 300 dòng mã Rust trong mười ba crate của workspace, "
              "cộng với crate vỏ giao diện. Nguyên tắc làm việc là: khi tài liệu thiết kế và mã nguồn mâu "
              "thuẫn nhau thì mã nguồn là chuẩn."),
        ("p", "**Phương pháp thực nghiệm** được áp dụng ở hai mức. Mức thứ nhất là bộ kiểm thử tự động "
              "gắn liền với từng crate, chạy trên ma trận ba hệ điều hành. Mức thứ hai là các chiến dịch "
              "kiểm chứng giả thuyết rủi ro, trong đó từng giả thuyết được cố gắng **tái hiện hoặc bác "
              "bỏ** trên đúng đường mã sản phẩm với tiến trình con age thật, chứ không phải trên bản giả "
              "lập dùng cho kiểm thử."),
        ("p", "**Phương pháp mô hình hóa** được dùng để dựng các sơ đồ kiến trúc, sơ đồ luồng dữ liệu và "
              "sơ đồ tuần tự. Mọi hình vẽ trong báo cáo đều được sinh từ mô tả có cấu trúc và được đối "
              "chiếu ngược lại với các mô-đun, hàm và thứ tự gọi có thật trong mã; không có thành phần, "
              "kênh truyền hay bước mật mã nào được vẽ thêm cho “đẹp sơ đồ”."),

        ("h2", "7. Đóng góp của đề tài"),
        ("p", "Đóng góp thứ nhất mang tính hệ thống: đề tài đưa ra một kiến trúc lắp ghép các nguyên thủy "
              "mật mã đã được kiểm chứng thành một sản phẩm hoàn chỉnh, trong đó tầng hợp đồng mật mã "
              "được tách hẳn khỏi tầng hiện thực, cho phép các crate nghiệp vụ hoàn toàn không phụ thuộc "
              "vào FFI và kiểm thử được độc lập."),
        ("p", "Đóng góp thứ hai nằm ở thiết kế định dạng container: cơ chế **gốc ràng buộc** cho phép một "
              "chữ ký duy nhất bảo vệ đồng thời phần header và phần tải trọng, đồng thời chống được kiểu "
              "tấn công ghép header của tệp này với tải trọng của tệp khác; và việc đặt danh mục tệp "
              "nằm bên trong vùng đã mã hóa khiến một két đang khóa không để lộ tên, kích thước hay số lượng "
              "tệp bên trong."),
        ("p", "Đóng góp thứ ba là một mô hình lỗi được thiết kế có chủ đích để không trở thành kênh rò "
              "rỉ: mọi thất bại chứng thực hội tụ về đúng một mã lỗi, trong khi các tình huống lành tính "
              "vẫn giữ được tính hành động được để người dùng biết phải làm gì."),
        ("p", "Đóng góp thứ tư là một khuôn mẫu làm cứng tiến trình con ngoài: ghim băm nhị phân tại thời "
              "điểm biên dịch, kiểm tra kiến trúc tệp mà không thực thi, đóng bề mặt phân giải đường dẫn "
              "trong bản phát hành, xác minh lại băm trước khi dùng, và bao vây quá trình thực thi bằng "
              "môi trường đã xóa, không qua shell và có hạn giờ tường."),
        ("p", "Đóng góp thứ năm mang tính phương pháp luận: đề tài chứng minh rằng một chiến dịch kiểm "
              "chứng giả thuyết rủi ro trên đúng đường mã sản phẩm có thể phát hiện những khiếm khuyết "
              "mà bộ kiểm thử đơn vị hoàn toàn bỏ sót — cụ thể là bảy giả thuyết được đặt ra thì sáu "
              "được xác nhận, và trong đó có một khiếm khuyết ở mức nghiêm trọng dẫn tới mất dữ liệu "
              "vĩnh viễn."),

        ("h2", "8. Kết cấu đề tài"),
        ("p", "Ngoài phần mở đầu, kết luận và danh mục tài liệu tham khảo, báo cáo được kết cấu thành "
              "bốn chương."),
        ("p", "**Chương 1 — Cơ sở khoa học và thực tiễn** trình bày nền tảng lý thuyết về các nguyên "
              "thủy mật mã và mô hình an toàn liên quan, sau đó khảo sát thực trạng công cụ hiện có, "
              "xác định khoảng trống và giới thiệu bộ công nghệ được lựa chọn."),
        ("p", "**Chương 2 — Phân tích và thiết kế hệ thống** phân tích bài toán, xác lập yêu cầu chức "
              "năng và phi chức năng, dựng mô hình đe dọa và ranh giới tin cậy, rồi trình bày kiến trúc "
              "phân tầng, kiến trúc mật mã, phân cấp khóa, các quy trình xử lý dữ liệu, thiết kế dữ liệu "
              "trên đĩa và kiến trúc an ninh nhiều lớp."),
        ("p", "**Chương 3 — Xây dựng và triển khai hệ thống** mô tả môi trường và tổ chức mã nguồn, quá "
              "trình hiện thực hóa từng tầng và từng mô-đun, bề mặt lệnh giữa giao diện và lõi, giao "
              "diện người dùng, cùng các biện pháp làm cứng và đóng gói."),
        ("p", "**Chương 4 — Thử nghiệm và đánh giá hệ thống** trình bày môi trường và phương pháp thử "
              "nghiệm, kết quả kiểm thử chức năng, kiểm thử các thuộc tính an toàn, kết quả đo hiệu năng "
              "và tài nguyên, kết quả chiến dịch kiểm chứng giả thuyết rủi ro, và cuối cùng là nhận xét "
              "chung về những gì đạt được cùng những hạn chế còn lại."),
    ]
