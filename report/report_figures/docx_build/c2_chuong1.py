# -*- coding: utf-8 -*-
"""CHUONG 1 — Co so khoa hoc va thuc tien."""


def blocks():
    return [
        ("h1", "CHƯƠNG 1\nCƠ SỞ KHOA HỌC VÀ THỰC TIỄN"),

        # ==================================================== 1. Co so ly luan
        ("h2", "1. Cơ sở lý luận"),

        ("h3", "1.1. Bảo vệ dữ liệu tại chỗ và giới hạn của các lớp bảo vệ hiện có"),
        ("p", "An toàn dữ liệu thường được phân tách theo ba trạng thái của dữ liệu: dữ liệu khi truyền, "
              "dữ liệu khi lưu trữ và dữ liệu khi xử lý. Trong hơn hai thập niên qua, hạ tầng bảo vệ dữ "
              "liệu khi truyền đã trưởng thành rất nhanh nhờ sự phổ cập của các giao thức truyền an toàn "
              "và hạ tầng khóa công khai. Ngược lại, bảo vệ dữ liệu khi lưu trữ trên thiết bị đầu cuối "
              "vẫn còn nhiều khoảng trống, phần lớn không phải vì thiếu công cụ mật mã mà vì thiếu công "
              "cụ đủ dùng cho người không chuyên."),
        ("p", "Lớp bảo vệ phổ biến nhất hiện nay là mã hóa toàn đĩa. Kỹ thuật này giải quyết rất tốt một "
              "mô hình đe dọa cụ thể: kẻ tấn công có được thiết bị ở trạng thái tắt máy. Tuy nhiên phạm "
              "vi bảo vệ của nó dừng lại ngay tại ranh giới đó. Khi hệ điều hành đã khởi động và người "
              "dùng đã đăng nhập, toàn bộ hệ thống tệp trở về dạng rõ đối với mọi tiến trình đang chạy "
              "với quyền của người dùng đó — bao gồm cả phần mềm độc hại vừa được cài đặt. Quan trọng "
              "hơn, lớp bảo vệ này **không đi theo tệp**: chép tệp sang thẻ nhớ, tải lên dịch vụ lưu trữ "
              "hay đính kèm vào thư điện tử đều làm nó biến mất."),
        ("p", "Lớp bảo vệ thứ hai là mã hóa ở mức tệp hoặc mức thư mục. Cách tiếp cận này khắc phục được "
              "nhược điểm “không đi theo tệp”, nhưng lại làm nảy sinh một nhóm vấn đề mới liên quan tới "
              "quản lý khóa: khóa được sinh ra từ đâu, cất ở đâu, sao lưu thế nào và khôi phục ra sao khi "
              "người dùng quên mật khẩu. Rất nhiều sự cố mất dữ liệu trong thực tế không bắt nguồn từ "
              "việc mật mã bị phá, mà từ việc quản lý khóa không được thiết kế tử tế."),
        ("p", "Lớp bảo vệ thứ ba, thường bị bỏ quên, là **tính toàn vẹn**. Mã hóa bảo đảm tính bí mật "
              "nhưng bản thân nó, nếu dùng ở chế độ không xác thực, hoàn toàn không bảo đảm rằng dữ liệu "
              "không bị sửa. Lịch sử mật mã ứng dụng ghi nhận rất nhiều lỗ hổng nghiêm trọng phát sinh "
              "chính từ việc tách rời hai thuộc tính này, mà điển hình là các tấn công padding oracle "
              "trên chế độ CBC không có mã xác thực. Đó là lý do vì sao mọi thiết kế hiện đại đều lấy "
              "**mã hóa có xác thực** làm mặc định thay vì mã hóa thuần túy."),
        ("p", "Cuối cùng, còn một lớp rủi ro nằm ngoài nội dung tệp: siêu dữ liệu. Ngay cả khi nội dung "
              "được mã hóa hoàn hảo, các thông tin phụ trợ như tên tệp, kích thước, số lượng tệp, thời "
              "điểm sửa đổi hay các trường EXIF nhúng trong ảnh vẫn có thể tiết lộ rất nhiều. Một thiết "
              "kế nghiêm túc phải xác định rõ những thông tin nào chấp nhận để lộ và những thông tin nào "
              "bắt buộc phải giấu."),

        ("h3", "1.2. Mã hóa có xác thực và mô hình bí mật gắn với toàn vẹn"),
        ("p", "Mã hóa có xác thực, viết tắt là AEAD, là một cấu trúc mật mã nhận vào khóa, một số dùng "
              "một lần (nonce), bản rõ và tùy chọn một khối dữ liệu liên kết không bí mật, rồi trả về bản "
              "mã kèm một thẻ xác thực. Khi giải mã, nếu bất kỳ byte nào của bản mã, nonce hoặc dữ liệu "
              "liên kết bị thay đổi, phép kiểm tra thẻ sẽ thất bại và toàn bộ thao tác bị hủy bỏ. Tính "
              "chất then chốt ở đây là **thất bại toàn phần**: hệ thống không bao giờ trả về một phần bản "
              "rõ chưa được xác thực."),
        ("p", "Trong hệ thống được nghiên cứu, hai họ AEAD được sử dụng. Họ thứ nhất là "
              "**XSalsa20-Poly1305**, hiện thực bởi hàm `crypto_secretbox` của thư viện libsodium. Đây là "
              "một cấu trúc kết hợp bộ mã dòng XSalsa20 với mã xác thực Poly1305 theo mô hình mã-hóa-rồi-"
              "xác-thực. Ưu điểm nổi bật của biến thể XSalsa20 là nonce dài 24 byte, đủ lớn để có thể "
              "sinh ngẫu nhiên mà xác suất trùng lặp là không đáng kể trên thực tế — một tính chất rất "
              "quan trọng đối với phần mềm không có bộ đếm trạng thái bền vững. Một hạn chế cần ghi nhận "
              "là `crypto_secretbox` **không nhận dữ liệu liên kết**, nên việc ràng buộc phần header vào "
              "bản mã phải được thực hiện bằng cơ chế khác, như sẽ trình bày ở mục 1.5."),
        ("p", "Họ thứ hai là **ChaCha20-Poly1305 trong khuôn khổ định dạng age**, được dùng cho phần tải "
              "trọng dung lượng lớn. Định dạng age kết hợp trao đổi khóa X25519 với mã hóa dòng có xác "
              "thực theo từng đoạn, cho phép xử lý tệp lớn mà không phải nạp toàn bộ vào bộ nhớ ở tầng "
              "định dạng. Việc lựa chọn hai họ AEAD khác nhau cho hai nhiệm vụ khác nhau không phải là "
              "sự thiếu nhất quán mà là một quyết định thiết kế có chủ đích: bọc khóa là thao tác trên "
              "vài chục byte và cần chạy hoàn toàn trong tiến trình, còn mã hóa tải trọng là thao tác "
              "trên hàng trăm megabyte và được ủy thác cho một công cụ chuyên biệt đã được cộng đồng "
              "kiểm chứng."),

        ("h3", "1.3. Hàm băm mật mã, mã xác thực thông điệp và dẫn xuất khóa theo miền"),
        ("p", "Hàm băm mật mã ánh xạ một chuỗi byte độ dài tùy ý thành một chuỗi byte độ dài cố định sao "
              "cho việc tìm nghịch ảnh, tìm nghịch ảnh thứ hai hay tìm va chạm đều khó về mặt tính toán. "
              "Trong hệ thống được nghiên cứu, hàm băm được dùng ở ba vai trò khác biệt, và việc phân "
              "biệt ba vai trò này rất quan trọng để hiểu thiết kế."),
        ("p", "Vai trò thứ nhất là **vân tay nội dung**: tính một giá trị đại diện cho tệp để so sánh, "
              "phát hiện thay đổi hoặc ghim danh tính của một tệp nhị phân. Vai trò thứ hai là **mã xác "
              "thực thông điệp có khóa**: khi hàm băm được cấp thêm một khóa bí mật, giá trị đầu ra chỉ "
              "có thể tính được bởi bên nắm khóa, do đó nó chứng minh cả tính toàn vẹn lẫn quyền sở hữu "
              "khóa. Vai trò thứ ba là **dẫn xuất khóa con theo miền**: từ một khóa gốc, sinh ra nhiều "
              "khóa con độc lập, mỗi khóa gắn với một chuỗi ngữ cảnh mô tả mục đích sử dụng."),
        ("p", "Hệ thống sử dụng **BLAKE3** cho cả ba vai trò. BLAKE3 là hàm băm mật mã hiện đại xây dựng "
              "trên cấu trúc cây Merkle, cung cấp sẵn ba chế độ hoạt động tương ứng với ba vai trò nêu "
              "trên: chế độ băm thường, chế độ băm có khóa và chế độ dẫn xuất khóa. Việc một hàm duy nhất "
              "phục vụ cả ba nhu cầu giúp giảm số nguyên thủy phải kiểm toán, đồng thời loại bỏ nguy cơ "
              "lắp ghép sai vốn hay xảy ra khi lập trình viên tự chế cấu trúc MAC từ một hàm băm thường."),
        ("p", "Khái niệm **tách miền** (domain separation) cần được nhấn mạnh vì nó là xương sống của "
              "toàn bộ thiết kế khóa trong hệ thống. Ý tưởng rất đơn giản: hai khóa con dùng cho hai mục "
              "đích khác nhau phải khác nhau, và cách bảo đảm điều đó là đưa một chuỗi mô tả mục đích vào "
              "đầu vào của hàm dẫn xuất. Hệ quả về mặt an toàn cũng rất trực tiếp: nếu một khóa con bị "
              "lộ, nó không giúp gì cho việc suy ra các khóa con khác, và một khối dữ liệu được bảo vệ "
              "bằng khóa của ngữ cảnh này không thể được mở bằng khóa của ngữ cảnh khác."),

        ("h3", "1.4. Dẫn xuất khóa từ mật khẩu và bài toán chi phí tính toán"),
        ("p", "Mọi hệ thống mã hóa dựa trên mật khẩu đều đối mặt với một thực tế bất lợi: entropy của mật "
              "khẩu do con người chọn thường thấp hơn nhiều so với entropy của một khóa 256 bit sinh ngẫu "
              "nhiên. Do đó, khóa không bao giờ được lấy trực tiếp từ mật khẩu bằng một hàm băm nhanh; nó "
              "phải đi qua một **hàm dẫn xuất khóa từ mật khẩu** được thiết kế để đắt đỏ một cách có kiểm "
              "soát."),
        ("p", "Các thế hệ hàm dẫn xuất khóa đã tiến hóa qua ba giai đoạn. Thế hệ đầu chỉ làm tăng chi phí "
              "theo thời gian bằng cách lặp lại hàm băm hàng chục nghìn lần; điểm yếu của chúng là kẻ tấn "
              "công có thể song song hóa gần như hoàn hảo trên GPU hoặc mạch chuyên dụng. Thế hệ thứ hai "
              "đưa vào chi phí bộ nhớ, buộc mỗi phép thử phải chiếm một lượng RAM đáng kể, qua đó thu hẹp "
              "lợi thế của phần cứng chuyên dụng. Thế hệ thứ ba, tiêu biểu là họ Argon2 — kết quả thắng "
              "cuộc của Cuộc thi Băm Mật khẩu năm 2015 — cho phép điều chỉnh độc lập ba tham số: dung "
              "lượng bộ nhớ, số vòng lặp và mức song song."),
        ("p", "Trong ba biến thể của Argon2, biến thể **Argon2id** là lựa chọn được khuyến nghị cho hầu "
              "hết các tình huống vì nó lai giữa Argon2i — truy cập bộ nhớ độc lập dữ liệu, chống tấn "
              "công kênh kề — và Argon2d — truy cập bộ nhớ phụ thuộc dữ liệu, chống tấn công đánh đổi "
              "thời gian–bộ nhớ. Hệ thống được nghiên cứu sử dụng Argon2id với tham số mặc định 256 MiB "
              "bộ nhớ, ba vòng lặp và một luồng, đồng thời áp một sàn tối thiểu theo khuyến nghị của "
              "OWASP là 19 MiB bộ nhớ và hai vòng lặp."),
        ("p", "Một chi tiết thiết kế đáng chú ý là sự phân tách giữa **kiểm tra cấu trúc tham số** và "
              "**chính sách cường độ**. Bản thân nguyên thủy chỉ từ chối những tham số không hợp lệ về "
              "mặt cấu trúc; còn sàn cường độ được đặt ở một mô-đun chính sách riêng và chỉ áp dụng khi "
              "**tạo mới** két. Lý do rất thực tế: một thiết bị yếu vẫn phải mở được két đã tạo trên "
              "thiết bị mạnh, nên khâu xác minh không được phép áp sàn."),
        ("p", "Hệ thống còn hiện thực hóa một cơ chế **hiệu chỉnh thích ứng**: hàm hiệu chỉnh đo thời "
              "gian thực thi Argon2id ngay trên máy đang chạy và tăng dần số vòng lặp cho tới khi đạt "
              "một mốc thời gian mục tiêu, nhưng không bao giờ xuống dưới sàn chính sách và không vượt "
              "quá một trần đã định. Nhờ đó chi phí tấn công bám theo phần cứng thực tế thay vì một con "
              "số phỏng đoán cố định. Cần ghi nhận rằng cơ chế này **đã tồn tại trong mã và có kiểm "
              "thử**, nhưng đường tạo két hiện vẫn dùng bộ tham số mặc định cố định; việc đưa hiệu chỉnh "
              "vào giao diện thiết lập là một bước còn để ngỏ."),

        ("h3", "1.5. Phân cấp khóa, bọc khóa và ràng buộc theo ngữ cảnh"),
        ("p", "Khi một hệ thống cần nhiều khóa cho nhiều mục đích, cách tổ chức tệ nhất là dùng chung một "
              "khóa cho tất cả, còn cách tổ chức tốt nhất là xây dựng một **phân cấp khóa** trong đó khóa "
              "gốc chỉ dùng để sinh ra các khóa con, và các khóa con mới là thứ trực tiếp tham gia vào "
              "các thao tác mật mã."),
        ("p", "Mô hình phổ biến gồm ba mức. Mức trên cùng là khóa dẫn xuất từ mật khẩu, gọi là khóa chủ. "
              "Mức giữa là các **khóa bọc**, mỗi khóa gắn với một loại bí mật cần cất giữ. Mức dưới cùng "
              "là các bí mật thực sự được dùng để mã hóa dữ liệu hoặc ký, và chúng được cất trên đĩa ở "
              "dạng đã bọc. Mô hình này mang lại một lợi ích vận hành rất lớn: khi người dùng đổi mật "
              "khẩu, hệ thống chỉ cần dẫn xuất lại khóa chủ và bọc lại vài chục byte bí mật, hoàn toàn "
              "không phải mã hóa lại toàn bộ dữ liệu."),
        ("p", "Vấn đề tinh tế hơn là **ràng buộc ngữ cảnh**. Giả sử một khối bí mật đã bọc bị sao chép từ "
              "két A sang két B, hoặc bị hoán đổi vị trí giữa hai trường trong cùng một két. Nếu khóa bọc "
              "chỉ phụ thuộc vào khóa chủ, những thao tác đó có thể không bị phát hiện và có thể dẫn tới "
              "các hệ quả an toàn khó lường. Giải pháp là đưa cả **định danh của két** và **nhãn của "
              "trường** vào chuỗi ngữ cảnh dẫn xuất khóa. Khi đó, một khối bị cấy ghép sai chỗ sẽ được "
              "mở bằng khóa dẫn xuất từ ngữ cảnh khác, và thẻ xác thực AEAD lập tức thất bại."),
        ("p", "Cần lưu ý rằng đây là cách **thay thế** cho việc dùng dữ liệu liên kết trong AEAD. Vì hàm "
              "`crypto_secretbox` không hỗ trợ dữ liệu liên kết, việc gấp ngữ cảnh vào khóa trở thành cơ "
              "chế ràng buộc duy nhất. Tài liệu của dự án ghi nhận rõ rằng việc bổ sung một AEAD có hỗ "
              "trợ dữ liệu liên kết là một cải tiến **đã hoãn lại**, và mức bảo đảm hiện tại được đánh "
              "giá là “phòng thủ theo chiều sâu bị hoãn” chứ không phải một lỗ hổng khai thác được."),

        ("h3", "1.6. Chữ ký số: phân biệt tính toàn vẹn và tính xuất xứ"),
        ("p", "Chữ ký số dùng cặp khóa bất đối xứng để tạo ra một giá trị mà chỉ bên nắm khóa bí mật mới "
              "sinh được, còn bất kỳ ai có khóa công khai đều kiểm tra được. Trong hệ thống được nghiên "
              "cứu, lược đồ được dùng là **Ed25519** — chữ ký trên đường cong Edwards xoắn, nổi bật ở tốc "
              "độ cao, kích thước nhỏ, tính xác định (không cần nguồn ngẫu nhiên khi ký) và khả năng "
              "hiện thực hóa với thời gian chạy không phụ thuộc dữ liệu bí mật."),
        ("p", "Định dạng lưu trữ chữ ký được chọn là định dạng của công cụ **minisign**, một định dạng "
              "văn bản gọn gồm bốn dòng: một dòng chú thích không tin cậy, một dòng chữ ký chính được mã "
              "hóa base64, một dòng chú thích tin cậy và một dòng chữ ký toàn cục. Điểm đáng chú ý về mặt "
              "thiết kế là chữ ký toàn cục ký lên chuỗi ghép của chữ ký chính với chú thích tin cậy, nhờ "
              "đó chú thích tin cậy không thể bị sửa đổi mà không bị phát hiện. Chữ ký chính không ký "
              "trực tiếp lên thông điệp mà ký lên giá trị tiền băm BLAKE2b-512 của thông điệp, cho phép "
              "ký các tệp lớn mà không cần nạp toàn bộ vào bộ nhớ ở tầng chữ ký."),
        ("p", "Một sự phân biệt khái niệm rất quan trọng, và được hệ thống thể hiện thành hai chế độ vận "
              "hành riêng biệt, là **tính toàn vẹn** so với **tính xuất xứ**. Nếu chữ ký được kiểm bằng "
              "chính khóa công khai nằm trong tệp, kết quả “hợp lệ” chỉ chứng minh rằng tệp không bị sửa "
              "kể từ khi được ký — đây là tính toàn vẹn, hay tính minh chứng chống sửa đổi. Nếu chữ ký "
              "được kiểm bằng một khóa công khai do người kiểm cung cấp từ bên ngoài và khóa trong tệp "
              "phải trùng khớp với khóa đó, kết quả “hợp lệ” mới chứng minh được tệp do đúng chủ thể nắm "
              "khóa tạo ra — đây mới là tính xuất xứ. Một tệp tự ký không bao giờ chứng minh được xuất xứ, "
              "và việc lẫn lộn hai khái niệm này là một sai lầm phổ biến trong các tài liệu kỹ thuật."),

        ("h3", "1.7. Chia sẻ bí mật theo ngưỡng"),
        ("p", "Lược đồ chia sẻ bí mật của Shamir, công bố năm 1979, giải quyết bài toán: chia một bí mật "
              "thành n mảnh sao cho bất kỳ k mảnh nào cũng khôi phục được bí mật, còn k trừ một mảnh thì "
              "**không cung cấp bất kỳ thông tin nào** về bí mật. Ý tưởng dựa trên một quan sát đại số "
              "đơn giản: một đa thức bậc k trừ một được xác định duy nhất bởi k điểm phân biệt. Đặt bí "
              "mật làm hệ số tự do, sinh ngẫu nhiên các hệ số còn lại, rồi phát cho mỗi bên giữ mảnh một "
              "điểm trên đa thức."),
        ("p", "Tính chất an toàn của lược đồ là **an toàn tuyệt đối theo nghĩa lý thuyết thông tin**: với "
              "ít hơn k mảnh, phân bố xác suất của bí mật vẫn hoàn toàn không đổi. Đây là một trong số "
              "rất ít cơ chế trong mật mã ứng dụng có được tính chất này, và nó không phụ thuộc vào bất "
              "kỳ giả thiết tính toán nào."),
        ("p", "Tuy vậy, lược đồ Shamir thuần túy có hai hạn chế thực tế mà bất kỳ hiện thực nào cũng phải "
              "xử lý. Thứ nhất, nó chỉ chia được một giá trị có kích thước cố định; muốn chia một tệp dài "
              "thì phải kết hợp với mã hóa, tức là sinh một khóa ngẫu nhiên, chia khóa đó và mã hóa tệp "
              "bằng khóa đó. Thứ hai, và nguy hiểm hơn, lược đồ thuần túy **không tự phát hiện được mảnh "
              "sai**: nếu một bên giữ mảnh cung cấp một mảnh giả, phép nội suy vẫn cho ra một giá trị 32 "
              "byte trông hoàn toàn bình thường nhưng sai hoàn toàn. Do đó hiện thực đúng đắn bắt buộc "
              "phải có một cơ chế xác thực đứng phía sau — và trong hệ thống được nghiên cứu, cơ chế đó "
              "chính là phép mở bọc AEAD, như sẽ phân tích ở Chương 2."),
        ("p", "Một cạm bẫy hiện thực nữa là **trùng hoành độ**: nếu hai mảnh được cấp cùng một hoành độ, "
              "hệ phương trình nội suy trở nên suy biến và kết quả là một khóa sai được sinh ra một cách "
              "âm thầm. Tương tự, một mảnh có hoành độ bằng không là mảnh giả mạo hoặc hỏng, vì bí mật "
              "nằm chính tại điểm đó. Cả hai trường hợp đều phải bị từ chối một cách tường minh trước khi "
              "chạy bất kỳ phép tính mật mã nào."),

        ("h3", "1.8. Giấu tin, phân tích giấu tin và thủy vân số"),
        ("p", "Giấu tin (steganography) và mật mã (cryptography) giải quyết hai bài toán khác nhau. Mật "
              "mã làm cho nội dung không đọc được nhưng không giấu **sự tồn tại** của thông điệp; giấu "
              "tin nhằm che giấu chính sự tồn tại đó. Trong thực hành hiện đại, hai kỹ thuật này luôn "
              "được dùng chồng lên nhau theo thứ tự **mã hóa rồi mới nhúng**, bởi vì một tải trọng chưa "
              "mã hóa mà bị phát hiện thì coi như mất trắng, trong khi một tải trọng đã mã hóa bị phát "
              "hiện thì vẫn giữ được tính bí mật."),
        ("p", "Kỹ thuật giấu tin trong ảnh phổ biến nhất là thay thế bit có trọng số nhỏ nhất của các mẫu "
              "màu. Với ảnh không mất mát như PNG hay BMP, kỹ thuật này áp dụng trực tiếp lên giá trị "
              "điểm ảnh. Với ảnh JPEG, việc thay đổi giá trị điểm ảnh sau giải nén là vô nghĩa vì khâu "
              "nén lại sẽ phá hủy chúng; do đó phải nhúng vào **hệ số biến đổi cosin rời rạc đã lượng "
              "tử hóa** rồi mã hóa lại một cách không mất mát."),
        ("p", "Phân tích giấu tin (steganalysis) là bài toán ngược. Hai họ phương pháp kinh điển được sử "
              "dụng rộng rãi là kiểm định khi bình phương trên phân bố cặp giá trị mẫu, và phân tích "
              "Regular–Singular dựa trên hành vi của một hàm lật áp lên các nhóm điểm ảnh. Cả hai đều là "
              "phương pháp **thực nghiệm, mang tính thống kê**, và điều này dẫn tới một hệ quả nhận thức "
              "luận quan trọng: chúng có thể làm tăng mức nghi ngờ nhưng **không bao giờ chứng minh được "
              "một tấm ảnh là sạch**. Một hệ thống trung thực phải phản ánh đúng giới hạn này trong cách "
              "trình bày kết quả, thay vì đưa ra phán quyết nhị phân “có” hay “không”."),
        ("p", "Thủy vân số là một họ kỹ thuật khác, thường bị nhầm với giấu tin. Thủy vân không nhằm "
              "truyền tải một tải trọng bí mật mà nhằm gắn một dấu hiệu vào chính nội dung. Thủy vân được "
              "chia thành hai nhóm theo mục đích: thủy vân **bền vững**, phải sống sót qua nén, cắt xén "
              "và biến đổi hình học, phục vụ mục đích chứng minh quyền sở hữu; và thủy vân **dễ vỡ**, "
              "phải hỏng ngay khi nội dung bị chỉnh sửa, phục vụ mục đích chứng minh nội dung chưa bị can "
              "thiệp. Hai mục đích này mâu thuẫn nhau về bản chất nên không thể đạt đồng thời bằng một cơ "
              "chế duy nhất."),

        ("h3", "1.9. Siêu dữ liệu tệp và rủi ro rò rỉ ngoài nội dung"),
        ("p", "Các định dạng tệp hiện đại mang theo một khối lượng siêu dữ liệu lớn hơn nhiều so với hình "
              "dung thông thường của người dùng. Một tấm ảnh chụp bằng điện thoại có thể chứa tọa độ định "
              "vị, kiểu máy, số sê-ri thiết bị, thời điểm chụp chính xác tới giây và cả ảnh thu nhỏ của "
              "bản gốc trước khi chỉnh sửa. Một tệp văn bản có thể chứa tên tác giả, tên tổ chức, đường "
              "dẫn thư mục cục bộ và lịch sử sửa đổi."),
        ("p", "Việc làm sạch siêu dữ liệu tưởng đơn giản nhưng lại vướng một vấn đề đáng chú ý về mặt "
              "**tính trung thực của bảo đảm**. Với một số định dạng, công cụ có thể viết lại tệp một "
              "cách thực sự và loại bỏ hoàn toàn các khối siêu dữ liệu. Với một số định dạng khác, tiêu "
              "biểu là PDF, cơ chế sửa đổi tăng dần khiến thao tác “xóa” thực chất chỉ là ghi thêm một "
              "bản cập nhật đánh dấu các trường cũ là không dùng nữa — dữ liệu gốc vẫn còn nằm trong tệp "
              "và vẫn trích xuất được bằng công cụ phân tích. Với một họ định dạng thứ ba, công cụ hoàn "
              "toàn không có khả năng ghi. Một hệ thống thiết kế tử tế phải phân biệt ba trường hợp này "
              "và báo cáo trung thực mức bảo đảm đạt được, thay vì luôn hiển thị thông báo “đã làm sạch”."),

        ("h3", "1.10. Mô hình đe dọa, ranh giới tin cậy và phòng thủ theo chiều sâu"),
        ("p", "Một hệ thống an toàn không thể được đánh giá nếu không có mô hình đe dọa. Mô hình đe dọa "
              "trả lời ba câu hỏi: **tài sản** nào cần bảo vệ, **kẻ tấn công** có những năng lực gì, và "
              "cái gì nằm **ngoài phạm vi** bảo vệ. Câu hỏi thứ ba quan trọng không kém hai câu đầu: một "
              "hệ thống tuyên bố chống lại mọi loại tấn công thực chất là một hệ thống chưa được phân "
              "tích nghiêm túc."),
        ("p", "Khái niệm **ranh giới tin cậy** giúp cụ thể hóa mô hình đe dọa thành các điểm kiểm soát. "
              "Mỗi lần dữ liệu hoặc quyền điều khiển đi qua ranh giới giữa hai vùng có mức tin cậy khác "
              "nhau, cần đặt ra câu hỏi: cái gì đi qua, ai kiểm tra, và điều gì xảy ra nếu phía bên kia "
              "cư xử ác ý. Trong một ứng dụng máy tính để bàn hiện đại có giao diện web nhúng, các ranh "
              "giới điển hình gồm: giữa mã giao diện và lõi xử lý, giữa lõi và các tiến trình con bên "
              "ngoài, giữa lõi và hệ thống tệp, và giữa phần mã đã được kiểm toán với cây phụ thuộc bên "
              "thứ ba."),
        ("p", "Nguyên tắc **phòng thủ theo chiều sâu** bổ sung một chiều nữa: không đặt toàn bộ hy vọng "
              "vào một cơ chế duy nhất. Nếu một khối bí mật đã được bọc bằng AEAD, việc bổ sung ràng "
              "buộc ngữ cảnh không phải là thừa; nếu container đã được ký, việc từ chối các trường lạ "
              "trong quá trình giải mã cấu trúc dữ liệu không phải là thừa; nếu tiến trình con đã được "
              "ghim băm, việc chạy nó với môi trường đã xóa và có hạn giờ cũng không phải là thừa. Mỗi "
              "lớp che một loại giả thiết có thể sai."),

        ("h3", "1.11. Rò rỉ qua kênh lỗi và nguyên tắc thiết kế thông điệp lỗi"),
        ("p", "Một kênh rò rỉ tinh vi và thường bị bỏ qua là chính **thông điệp lỗi**. Nếu hệ thống trả "
              "về “sai mật khẩu” khi mật khẩu sai và “tệp bị hỏng” khi tệp bị sửa, thì kẻ tấn công có "
              "được một phép thử phân biệt: bằng cách sửa tệp theo các cách khác nhau và quan sát loại "
              "lỗi trả về, hắn có thể suy ra thông tin về trạng thái nội bộ mà lẽ ra phải được giữ kín. "
              "Kiểu tấn công này được gọi chung là tấn công oracle, và nó đã từng phá vỡ nhiều giao thức "
              "được coi là an toàn về mặt lý thuyết."),
        ("p", "Nguyên tắc thiết kế đúng gồm hai vế bổ sung cho nhau. Vế thứ nhất: mọi thất bại liên quan "
              "tới **chứng thực** phải hội tụ về đúng một mã lỗi duy nhất — sai mật khẩu, sai mảnh khôi "
              "phục, bản mã bị sửa đều phải trả về cùng một câu trả lời. Vế thứ hai, và đây là phần dễ bị "
              "làm quá đà: các tình huống **lành tính và không bí mật** thì phải giữ nguyên tính phân biệt "
              "để người dùng còn biết phải làm gì. Chọn nhầm tệp, tệp thuộc phiên bản định dạng không hỗ "
              "trợ, thiếu mảnh khôi phục, tệp quá lớn, hết hạn giờ, tệp đích đã tồn tại — tất cả đều là "
              "**sự thật về tệp** chứ không phải sự thật về bí mật, nên việc phân biệt chúng không tạo ra "
              "oracle nào."),
        ("p", "Ngoài nội dung mã lỗi, **thứ tự các cổng kiểm tra** cũng là một yếu tố thiết kế. Nếu phép "
              "kiểm tra tính toàn vẹn của tệp được thực hiện **trước** và hoàn toàn không dùng tới bất kỳ "
              "thông tin bí mật nào, thì kết quả của nó không thể mang thông tin về mật khẩu. Ngược lại, "
              "nếu hai phép kiểm tra bị trộn lẫn, việc phân tách hệ quả trở nên rất khó."),

        # =================================================== 2. Co so thuc tien
        ("h2", "2. Cơ sở thực tiễn"),

        ("h3", "2.1. Thực trạng nhu cầu bảo vệ dữ liệu ngoại tuyến"),
        ("p", "Trong môi trường công tác thực tế, một tỷ lệ đáng kể tài liệu nhạy cảm được xử lý trên máy "
              "tính cá nhân không nối mạng hoặc chỉ nối mạng nội bộ. Việc dùng các dịch vụ lưu trữ đám "
              "mây để bảo vệ tài liệu, ngoài các vấn đề pháp lý và chính sách, còn vướng một trở ngại kỹ "
              "thuật cơ bản: mô hình tin cậy bị dịch chuyển sang một bên thứ ba mà người dùng không kiểm "
              "soát được. Điều này lý giải nhu cầu bền bỉ đối với các công cụ hoạt động hoàn toàn tại chỗ."),
        ("p", "Nhu cầu này không chỉ dừng ở việc mã hóa. Qua quan sát các tình huống sử dụng thực tế, có "
              "thể nhận diện năm nhóm tác vụ thường xuyên lặp lại: cất giữ một nhóm tệp trong một hộp "
              "chứa có mật khẩu; mã hóa một tệp đơn lẻ trước khi gửi đi; kiểm tra một tệp nhận về có "
              "đúng như bên gửi công bố hay không; sao lưu vật liệu khóa để phòng trường hợp quên mật "
              "khẩu; và làm sạch dấu vết riêng tư trước khi chia sẻ tệp ra ngoài. Điểm chung của cả năm "
              "nhóm là chúng đều có công cụ chuyên dụng, nhưng các công cụ đó nằm rải rác, giao diện "
              "không đồng nhất và phần lớn là công cụ dòng lệnh."),

        ("h3", "2.2. Khảo sát một số giải pháp hiện có và khoảng trống còn lại"),
        ("p", "Ở nhóm hộp chứa mã hóa, các giải pháp phổ biến gồm phần mềm tạo ổ đĩa ảo mã hóa và các "
              "công cụ nén có mật khẩu. Nhóm thứ nhất cung cấp mức bảo vệ tốt cho khối lượng dữ liệu lớn "
              "nhưng thường yêu cầu quyền quản trị để gắn kết ổ đĩa ảo, và tệp ổ đĩa có kích thước cố "
              "định khiến việc trao đổi trở nên bất tiện. Nhóm thứ hai rất tiện dụng nhưng có một điểm "
              "yếu ít được người dùng nhận ra: ở nhiều định dạng nén phổ biến, **danh sách tệp bên trong "
              "vẫn nằm ở dạng rõ**, nghĩa là kẻ tấn công có được tệp nén vẫn đọc được tên tất cả tài liệu "
              "bên trong."),
        ("p", "Ở nhóm mã hóa tệp đơn lẻ, công cụ `age` đại diện cho một xu hướng thiết kế hiện đại rất "
              "đáng học hỏi: bề mặt sử dụng tối giản, không có tùy chọn cấu hình nguy hiểm, định dạng "
              "được đặc tả rõ ràng. Tuy nhiên age là công cụ dòng lệnh thuần túy, không có cơ chế quản "
              "lý khóa ở mức người dùng cuối và không giải quyết bài toán sao lưu khóa."),
        ("p", "Ở nhóm kiểm tra toàn vẹn, các công cụ tính băm và công cụ chữ ký như minisign đều rất "
              "trưởng thành. Điểm nghẽn ở đây hoàn toàn nằm ở khả năng tiếp cận: một người dùng không "
              "chuyên rất khó tự mình so sánh một chuỗi hex 64 ký tự, và càng khó hơn để hiểu sự khác "
              "biệt giữa “tệp không bị sửa” và “tệp đúng là do người đó tạo ra”."),
        ("p", "Ở nhóm chia sẻ bí mật, số lượng công cụ dân dụng rất hạn chế; phần lớn hiện thực tồn tại "
              "dưới dạng thư viện hoặc tiện ích dòng lệnh, và nhiều hiện thực không xử lý các cạm bẫy đã "
              "nêu ở mục 1.7. Ở nhóm giấu tin và thủy vân, các công cụ sẵn có thường thiếu tầng mã hóa "
              "đứng trước hoặc tự chế cơ chế mã hóa riêng. Ở nhóm siêu dữ liệu, công cụ ExifTool gần như "
              "là chuẩn mực về độ bao phủ định dạng, nhưng bản thân nó là một chương trình Perl có cơ chế "
              "cấu hình bằng mã thực thi — một bề mặt tấn công cần được xử lý cẩn thận nếu muốn nhúng vào "
              "một ứng dụng khác."),
        ("p", "Tổng hợp lại, khoảng trống mà đề tài nhắm tới không phải là thiếu thuật toán, mà là thiếu "
              "một **sản phẩm tích hợp**: một ứng dụng duy nhất, giao diện thống nhất, chạy ngoại tuyến, "
              "lắp ghép đúng các nguyên thủy đã được kiểm chứng, xử lý đầy đủ các cạm bẫy hiện thực, và "
              "trình bày cho người dùng đúng mức bảo đảm mà nó thực sự đạt được."),

        ("h3", "2.3. Nguyên tắc không tự thiết kế nguyên thủy mật mã"),
        ("p", "Một trong những bài học đắt giá nhất của lịch sử mật mã ứng dụng là: các nguyên thủy mật "
              "mã tự chế hầu như luôn bị phá, kể cả khi tác giả của chúng là người có trình độ. Lý do "
              "không nằm ở năng lực cá nhân mà ở bản chất của bài toán — độ an toàn của một nguyên thủy "
              "chỉ được thiết lập sau nhiều năm bị cộng đồng chuyên gia tấn công công khai, và không có "
              "cách rút ngắn nào."),
        ("p", "Đề tài do đó áp dụng một ràng buộc thiết kế cứng: **chỉ lắp ghép, không phát minh**. Ràng "
              "buộc này được ghi thẳng vào quy ước phát triển của dự án. Trong toàn bộ hệ thống, phần "
              "logic mật mã do dự án tự viết chỉ gồm đúng hai thứ: mã hóa và giải mã **định dạng lưu trữ** "
              "của chữ ký minisign — tức là cách sắp xếp byte, không phải thuật toán ký; và cách xây dựng "
              "các **chuỗi ngữ cảnh tách miền** cho hàm dẫn xuất khóa. Mọi phép tính mật mã thực sự đều "
              "được ủy thác cho blake3, argon2, libsodium, thư viện Shamir hazmat và công cụ age."),
        ("p", "Cần nhấn mạnh rằng nguyên tắc này không loại bỏ mọi rủi ro. Việc lắp ghép sai các nguyên "
              "thủy đúng vẫn có thể tạo ra hệ thống sai — dùng lại nonce, thiếu ràng buộc ngữ cảnh, sai "
              "thứ tự mã hóa và xác thực, hoặc để lộ thông tin qua kênh lỗi. Vì vậy phần lớn nội dung "
              "Chương 2 của báo cáo tập trung chính xác vào các quyết định lắp ghép này."),

        ("h3", "2.4. Công nghệ và công cụ sử dụng để xây dựng hệ thống"),
        ("p", "**Ngôn ngữ lõi** là Rust, phiên bản tối thiểu được hỗ trợ là 1.96 và được cưỡng chế bằng "
              "một nhóm việc riêng trong quy trình tích hợp liên tục. Lý do lựa chọn Rust đối với một hệ "
              "thống xử lý dữ liệu không tin cậy là khá hiển nhiên: mô hình sở hữu và kiểm tra biên tại "
              "thời điểm biên dịch loại bỏ được toàn bộ họ lỗi tràn bộ đệm và dùng-sau-khi-giải-phóng, "
              "vốn là nguồn gốc của phần lớn lỗ hổng nghiêm trọng trong các bộ phân tích định dạng viết "
              "bằng C. Dự án còn đi xa hơn bằng cách **cấm mã không an toàn ở phạm vi toàn workspace**, "
              "chỉ mở lại đúng tại hai crate làm nhiệm vụ gọi thư viện C."),
        ("p", "**Vỏ giao diện** dùng Tauri phiên bản 2, một khung ứng dụng máy tính để bàn kết hợp lõi "
              "Rust với thành phần webview có sẵn của hệ điều hành. So với phương án đóng gói cả một "
              "trình duyệt vào ứng dụng, cách này cho kích thước gói nhỏ hơn nhiều và bề mặt tấn công "
              "hẹp hơn. Giao diện được viết bằng HTML, CSS và JavaScript tĩnh, không dùng công cụ đóng "
              "gói nào, với chính sách an toàn nội dung giới hạn ở nguồn nội bộ."),
        ("p", "**Các thư viện mật mã** gồm: `blake3` và `argon2` là hai thư viện thuần Rust; `libsodium` "
              "được gọi qua FFI để dùng các hàm ký Ed25519, băm BLAKE2b và mã hóa có xác thực "
              "`crypto_secretbox`; và thư viện `sss` của Daan Sprenkels được nhúng ở dạng mã nguồn C cho "
              "phần chia sẻ bí mật, với hàm sinh số ngẫu nhiên được thay bằng nguồn của hệ điều hành."),
        ("p", "**Các nhị phân ngoài** gồm `age` cùng `age-keygen` cho phần mã hóa tải trọng, và "
              "`exiftool` cho mô-đun siêu dữ liệu. Đây là các chương trình độc lập được đóng gói kèm ứng "
              "dụng chứ không phải phụ thuộc hệ thống, và chúng được ghim theo giá trị băm BLAKE3 ngay "
              "tại thời điểm biên dịch."),
        ("p", "**Định dạng tuần tự hóa** cho phần header của container là CBOR theo RFC 8949, thông qua "
              "thư viện `ciborium`. CBOR được chọn thay cho JSON vì nó là định dạng nhị phân gọn, có bộ "
              "phân tích đơn giản và ít bề mặt mơ hồ; và thay cho các định dạng cần bộ sinh mã vì nó giữ "
              "được sự đơn giản của chuỗi công cụ."),
        ("p", "**Các cổng chất lượng** gồm kiểm tra định dạng mã, phân tích tĩnh với mọi cảnh báo được "
              "nâng thành lỗi, biên dịch với tệp khóa phiên bản, chạy toàn bộ kiểm thử, và hai công cụ "
              "kiểm tra chuỗi cung ứng là `cargo deny` cùng `cargo audit`. Toàn bộ được chạy trên ma "
              "trận ba hệ điều hành."),

        ("h3", "2.5. Căn cứ tiêu chuẩn và yêu cầu bảo đảm an toàn thông tin"),
        ("p", "Về mặt tham số mật mã, hệ thống bám theo các khuyến nghị đang được cộng đồng thừa nhận "
              "rộng rãi. Sàn tham số Argon2id được lấy trực tiếp từ khuyến nghị của OWASP về lưu trữ mật "
              "khẩu, với 19 MiB bộ nhớ và hai vòng lặp là mức tối thiểu tuyệt đối; giá trị mặc định của "
              "hệ thống cao hơn sàn này hơn mười ba lần về bộ nhớ."),
        ("p", "Về mặt lựa chọn nguyên thủy, các thuật toán được sử dụng đều nằm trong nhóm được khuyến "
              "nghị hiện hành: Ed25519 cho chữ ký, X25519 cho trao đổi khóa, ChaCha20-Poly1305 và "
              "XSalsa20-Poly1305 cho mã hóa có xác thực, BLAKE3 và BLAKE2b cho hàm băm. Cần nêu rõ một "
              "giới hạn: các nguyên thủy này thuộc thế hệ **trước lượng tử**. Hệ thống hiện **không** "
              "tích hợp bất kỳ thuật toán hậu lượng tử nào, và báo cáo này không đưa ra bất kỳ tuyên bố "
              "nào về khả năng chống lại máy tính lượng tử."),
        ("p", "Về mặt quy trình, hệ thống áp dụng một nguyên tắc mà các tiêu chuẩn quản lý an toàn thông "
              "tin đều nhấn mạnh: **khả năng kiểm toán**. Điều này thể hiện qua việc cây phụ thuộc của "
              "phần lõi được cách ly khỏi cây phụ thuộc rất nặng của webview, để hai công cụ kiểm tra "
              "chuỗi cung ứng có thể soi phần lõi một cách có ý nghĩa; qua việc mọi định dạng trên đĩa "
              "đều tự mô tả và có phiên bản; và qua việc ba trục phiên bản — hợp đồng giao tiếp, cấu trúc "
              "container và bộ thuật toán — được tách rời và tiến hóa độc lập."),
        ("p", "Cuối cùng, cần ghi nhận một giới hạn về tư thế phát hành. Gói cài đặt do hệ thống sinh ra "
              "hiện **chưa được ký số và chưa được công chứng**. Dự án tuyên bố rõ rằng đây là công cụ "
              "dùng nội bộ nên việc ký số nằm ngoài phạm vi; tuy nhiên đây vẫn là một điểm chặn thực sự "
              "đối với việc phân phối rộng rãi, và Chương 4 sẽ trình bày bằng chứng thực nghiệm cho thấy "
              "hậu quả cụ thể của nó trên hệ điều hành macOS."),

        # ============================================================ ket luan
        ("h2", "Kết luận chương 1"),
        ("p", "Chương 1 đã xác lập nền tảng lý luận và thực tiễn cho toàn bộ phần còn lại của báo cáo. Về "
              "mặt lý luận, chương đã hệ thống hóa các nguyên thủy mật mã mà hệ thống sử dụng — mã hóa có "
              "xác thực, hàm băm đa vai trò, hàm dẫn xuất khóa từ mật khẩu có kiểm soát chi phí, chữ ký "
              "số, chia sẻ bí mật theo ngưỡng — cùng với các khái niệm kiến trúc an toàn then chốt là "
              "tách miền, phân cấp khóa, ràng buộc ngữ cảnh, ranh giới tin cậy và phòng thủ theo chiều "
              "sâu. Ba sự phân biệt khái niệm được nhấn mạnh vì chúng sẽ chi phối toàn bộ thiết kế ở "
              "Chương 2: bí mật khác với toàn vẹn; toàn vẹn khác với xuất xứ; và che giấu khác với bí mật."),
        ("p", "Về mặt thực tiễn, chương đã chỉ ra rằng khoảng trống cần lấp không nằm ở tầng thuật toán "
              "mà nằm ở tầng sản phẩm tích hợp, và đã xác lập ràng buộc thiết kế cứng nhất của đề tài: "
              "chỉ lắp ghép các nguyên thủy đã được kiểm chứng, tuyệt đối không tự thiết kế thuật toán "
              "mới. Ràng buộc này chuyển trọng tâm của công việc kỹ thuật sang các quyết định lắp ghép — "
              "thứ tự thao tác, cách ràng buộc, cách xử lý lỗi và cách bao vây các thành phần bên ngoài "
              "— và chính đó là nội dung của Chương 2."),
    ]
