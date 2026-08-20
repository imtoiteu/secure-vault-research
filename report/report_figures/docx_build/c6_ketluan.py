# -*- coding: utf-8 -*-
"""KET LUAN va TAI LIEU THAM KHAO."""


def blocks():
    B = [
        ("h1", "KẾT LUẬN"),

        ("h2", "1. Kết quả đạt được"),
        ("p", "Đề tài đã hoàn thành mục tiêu tổng quát đặt ra ở phần mở đầu: nghiên cứu, thiết kế và xây "
              "dựng một hệ thống phần mềm máy tính để bàn cung cấp các dịch vụ bảo mật và riêng tư thiết "
              "yếu cho dữ liệu tại chỗ, hoạt động hoàn toàn ngoại tuyến, có kiến trúc an toàn rõ ràng và "
              "có khả năng truy vết mọi tuyên bố an toàn tới mã nguồn."),
        ("p", "**Về sản phẩm phần mềm**, hệ thống gồm khoảng 16 300 dòng mã Rust tổ chức trong mười ba "
              "crate của workspace cộng với một crate vỏ giao diện, cung cấp sáu mô-đun chức năng thông "
              "qua ba mươi tám lệnh và hai mươi màn hình giao diện được bản địa hóa hoàn toàn sang tiếng "
              "Việt. Cả sáu mô-đun đều đã được hiện thực hóa với mã vượt qua toàn bộ cổng chất lượng "
              "trên ma trận ba hệ điều hành."),
        ("p", "**Về đóng góp thiết kế**, ba kết quả đáng ghi nhận. Thứ nhất là cơ chế **gốc ràng buộc** "
              "trong định dạng container: bằng cách ký lên giá trị băm của cặp giá trị băm thành phần, "
              "và bằng cách tính lại các giá trị thành phần này ở mỗi lần đọc thay vì lưu chúng, hệ "
              "thống đạt được tính toàn vẹn cho cả header lẫn tải trọng với đúng một chữ ký, đồng thời "
              "chống được tấn công ghép header của tệp này với tải trọng của tệp khác. Thứ hai là cơ "
              "chế **ràng buộc ngữ cảnh** trong dẫn xuất khóa bọc, thay thế hiệu quả cho dữ liệu liên "
              "kết mà hàm mã hóa được chọn không hỗ trợ, chống được cả cấy ghép giữa các két lẫn nhầm "
              "lẫn giữa các trường. Thứ ba là quyết định đặt **danh mục tệp vào bên trong vùng đã mã "
              "hóa**, nhờ đó một két đang khóa không để lộ tên, kích thước hay số lượng tệp bên trong."),
        ("p", "**Về đóng góp trong mô hình an toàn**, hệ thống xây dựng được một mô hình lỗi vừa chống "
              "được dò kênh lỗi vừa giữ được tính hữu dụng: mọi thất bại chứng thực hội tụ về một mã duy "
              "nhất, trong khi mười một tình huống lành tính vẫn giữ nguyên tính phân biệt và tính hành "
              "động được. Điều kiện tiên quyết cho mô hình này — việc đặt cổng chữ ký **trước** cổng mật "
              "khẩu và bảo đảm cổng chữ ký không sử dụng bất kỳ thông tin bí mật nào — là một quyết định "
              "kiến trúc chứ không phải một thủ thuật hiện thực."),
        ("p", "**Về đóng góp trong kỹ thuật hệ thống**, đề tài đưa ra một khuôn mẫu làm cứng tiến trình "
              "con ngoài gồm sáu biện pháp nối tiếp từ thời điểm biên dịch tới thời điểm thực thi, và "
              "một cách tổ chức workspace cho phép cách ly cây phụ thuộc nặng của giao diện khỏi cổng "
              "kiểm toán chuỗi cung ứng của phần lõi mật mã."),
        ("p", "**Về đóng góp phương pháp luận**, chiến dịch kiểm chứng giả thuyết rủi ro đã chứng minh "
              "một luận điểm có giá trị vượt ra ngoài dự án này: một bộ kiểm thử tự động dày đặc, dù "
              "được thiết kế tốt, vẫn có thể bỏ sót toàn bộ một lớp khiếm khuyết nghiêm trọng nếu nó "
              "chạy trên bản giả lập thay vì trên đường mã sản phẩm. Trong bảy giả thuyết được đặt ra, "
              "sáu được xác nhận, và không một khiếm khuyết nào trong số đó là lỗi mật mã."),

        ("h2", "2. Hạn chế"),
        ("p", "Đề tài còn một số hạn chế cần được nêu rõ, chia thành ba nhóm theo bản chất."),
        ("p", "**Nhóm hạn chế về kỹ thuật hiện thực.** Đường xử lý tải trọng vẫn nạp toàn bộ dữ liệu vào "
              "bộ nhớ, dẫn tới đỉnh tiêu thụ khoảng 2,7 lần kích thước dữ liệu và buộc phải áp một trần "
              "hai gigabyte; đây là hạn chế có ảnh hưởng thực tế lớn nhất. Việc thêm một tệp buộc phải "
              "mã hóa lại toàn bộ két. Cơ chế bảo vệ chống ghi đồng thời mới chỉ có hiệu lực trong cùng "
              "một tiến trình. Việc ràng buộc khối bọc vào ngữ cảnh vẫn là gián tiếp qua khóa thay vì "
              "trực tiếp qua dữ liệu liên kết. Còn tồn tại một khoảng trống TOCTOU trong cơ chế ghim băm "
              "nhị phân."),
        ("p", "**Nhóm hạn chế về bằng chứng.** Hệ thống chưa được kiểm định độc lập bởi bên thứ ba; toàn "
              "bộ đánh giá trong báo cáo là đánh giá nội bộ. Chưa có bằng chứng thực nghiệm về khả năng "
              "tương thích byte của chữ ký với công cụ chuẩn. Chưa có kiểm thử tự động cho giao diện ở "
              "mức chạy thật. Dữ liệu hiệu năng còn thưa, chỉ trên một cấu hình và thiếu hẳn phép đo cho "
              "hàm dẫn xuất khóa. Bằng chứng về vệ sinh bí mật trong bộ nhớ là bằng chứng cấu trúc do "
              "trình biên dịch cưỡng chế, không phải bằng chứng đo đạc. Và không có bất kỳ thuộc tính "
              "nào của hệ thống được chứng minh bằng phương pháp hình thức."),
        ("p", "**Nhóm hạn chế về phạm vi.** Gói cài chưa được ký số và công chứng, và hậu quả của điều "
              "này đã được xác nhận bằng thực nghiệm trên macOS. Hệ thống không đặt mục tiêu chống lại "
              "kẻ tấn công đã chiếm được quyền đọc bộ nhớ tiến trình. Các bản sao mật khẩu do khung ứng "
              "dụng tạo ra trước khi mã hệ thống chạy nằm ngoài tầm kiểm soát. Các nguyên thủy được sử "
              "dụng đều thuộc thế hệ trước lượng tử, và hệ thống **không** tích hợp bất kỳ thuật toán "
              "hậu lượng tử nào."),
        ("p", "Cuối cùng, cần nêu một hạn chế mang tính nguyên tắc: việc lắp ghép các nguyên thủy đã được "
              "kiểm chứng làm giảm đáng kể nhưng **không loại bỏ** rủi ro mật mã. Rủi ro chuyển từ tầng "
              "thuật toán sang tầng lắp ghép, và tầng đó chỉ có thể được bảo đảm bằng rà soát, kiểm thử "
              "và kiểm định — những việc mà đề tài mới thực hiện được hai trong ba."),

        ("h2", "3. Hướng phát triển"),
        ("p", "**Hướng thứ nhất — hoàn thiện các hạn chế đã xác định.** Ưu tiên cao nhất là chuyển đường "
              "xử lý tải trọng sang mô hình truyền dòng, vì nó giải quyết đồng thời hai hạn chế lớn nhất "
              "và mở đường cho việc bỏ trần kích thước. Tiếp theo là bổ sung khóa ở mức hệ điều hành, "
              "nối cổng kiểm tra tương thích chữ ký, nối cơ chế hiệu chỉnh tham số vào giao diện, và bổ "
              "sung mục tiêu fuzz có dẫn hướng."),
        ("p", "**Hướng thứ hai — hợp nhất hai đường dịch vụ mật mã.** Hiện mô-đun két và tầng dịch vụ "
              "mức tệp có hai đường băng, ký và kiểm tra riêng biệt, dẫn tới sự khác biệt về hành vi mà "
              "người dùng khó hiểu — chẳng hạn cùng là thao tác tính vân tay nhưng một đường có trần "
              "kích thước còn một đường thì không. Việc hợp nhất sẽ loại bỏ một nguồn không nhất quán và "
              "thu hẹp bề mặt mã cần kiểm toán."),
        ("p", "**Hướng thứ ba — bổ sung ràng buộc bằng dữ liệu liên kết.** Chuyển sang một hàm mã hóa có "
              "hỗ trợ dữ liệu liên kết và ràng buộc mỗi khối bọc vào định danh két, nhãn trường và số "
              "phiên bản bộ thuật toán. Đây là thay đổi ở tầng lược đồ nên đòi hỏi tăng phiên bản và một "
              "quy trình chuyển đổi cho các két đã tồn tại."),
        ("p", "**Hướng thứ tư — mở rộng năng lực quản lý khóa.** Hai khả năng đáng cân nhắc là tích hợp "
              "kho khóa của hệ điều hành để giảm số lần người dùng phải gõ mật khẩu, và hỗ trợ khóa phần "
              "cứng cho vai trò khóa ký. Cả hai đều là **hướng nghiên cứu chưa được hiện thực hóa** và "
              "đều làm thay đổi mô hình đe dọa, nên cần được phân tích lại từ đầu chứ không thể thêm vào "
              "như một tính năng."),
        ("p", "**Hướng thứ năm — nghiên cứu chuẩn bị cho giai đoạn hậu lượng tử.** Kiến trúc hiện tại có "
              "một thuận lợi cho việc này: định danh thuật toán đã tường minh ở cả biên hợp đồng lẫn "
              "trên đĩa, và ba trục phiên bản đã được tách rời, nên việc bổ sung một bộ thuật toán thứ "
              "hai theo mô hình lai là khả thi về mặt cấu trúc. Tuy nhiên cần nói rõ rằng đây là hướng "
              "nghiên cứu, hiện **chưa có bất kỳ dòng mã nào** liên quan tới mật mã hậu lượng tử trong "
              "hệ thống."),
        ("p", "**Hướng thứ sáu — thủy vân bền vững.** Họ kỹ thuật kết hợp biến đổi sóng con, biến đổi "
              "cosin rời rạc và phân tích giá trị kỳ dị là hướng tự nhiên để bổ sung năng lực chứng minh "
              "quyền sở hữu bên cạnh năng lực chứng minh tính nguyên vẹn hiện có. Trở ngại đã được xác "
              "định cụ thể là chưa có thư viện biến đổi sóng con hai chiều thuần Rust đủ tin cậy; việc "
              "tự hiện thực hóa một biến đổi như vậy sẽ mâu thuẫn với nguyên tắc chỉ lắp ghép các thành "
              "phần đã được kiểm chứng, nên hướng này phụ thuộc vào sự trưởng thành của hệ sinh thái thư "
              "viện."),
        ("p", "**Hướng thứ bảy — kiểm định độc lập.** Đây là hướng có giá trị cao nhất đối với độ tin cậy "
              "của sản phẩm và cũng là hướng mà bản thân nhóm phát triển không thể tự thực hiện. Một "
              "cuộc kiểm định tập trung vào tầng lắp ghép — thứ tự thao tác, ràng buộc ngữ cảnh, xử lý "
              "lỗi và biên tiến trình con — sẽ mang lại giá trị lớn hơn nhiều so với việc kiểm định các "
              "nguyên thủy vốn đã được cộng đồng kiểm chứng rộng rãi."),
        ("p", "Tóm lại, đề tài đã xây dựng được một hệ thống hoàn chỉnh, có kiến trúc rõ ràng, có bằng "
              "chứng kiểm thử đáng kể và có một hồ sơ hạn chế trung thực. Chính hồ sơ hạn chế đó, chứ "
              "không phải danh sách tính năng, mới là cơ sở để đánh giá đúng mức độ sẵn sàng của hệ "
              "thống và để định hướng các bước phát triển tiếp theo."),
    ]

    # =================================================== tai lieu tham khao
    refs = [
        "Bernstein D. J., Duif N., Lange T., Schwabe P., Yang B.-Y. (2012), “High-speed high-security "
        "signatures”, Journal of Cryptographic Engineering, 2(2), tr. 77–89.",
        "Bernstein D. J. (2008), “ChaCha, a variant of Salsa20”, Workshop Record of SASC 2008: "
        "The State of the Art of Stream Ciphers.",
        "Bernstein D. J. (2005), “The Poly1305-AES message-authentication code”, Fast Software "
        "Encryption (FSE 2005), LNCS 3557, Springer, tr. 32–49.",
        "Biryukov A., Dinu D., Khovratovich D. (2016), “Argon2: New Generation of Memory-Hard "
        "Functions for Password Hashing and Other Applications”, IEEE European Symposium on Security "
        "and Privacy, tr. 292–302.",
        "Shamir A. (1979), “How to share a secret”, Communications of the ACM, 22(11), tr. 612–613.",
        "Blakley G. R. (1979), “Safeguarding cryptographic keys”, Proceedings of the National Computer "
        "Conference, AFIPS, tr. 313–317.",
        "O’Connor J., Aumasson J.-P., Neves S., Wilcox-O’Hearn Z. (2021), BLAKE3: One Function, Fast "
        "Everywhere, đặc tả kỹ thuật, https://github.com/BLAKE3-team/BLAKE3-specs.",
        "Aumasson J.-P., Neves S., Wilcox-O’Hearn Z., Winnerlein C. (2013), “BLAKE2: Simpler, Smaller, "
        "Fast as MD5”, Applied Cryptography and Network Security (ACNS 2013), LNCS 7954, tr. 119–135.",
        "Valsorda F., Cartwright-Cox B., Hansen A. (2021), The age file encryption format, đặc tả kỹ "
        "thuật, https://age-encryption.org/v1.",
        "Denis F. (2015–), minisign: A dead simple tool to sign files and verify digital signatures, "
        "https://jedisct1.github.io/minisign/.",
        "Denis F. (2013–), The Sodium cryptography library (libsodium), tài liệu kỹ thuật, "
        "https://doc.libsodium.org/.",
        "Sprenkels D. (2017), sss: Library for the Shamir secret sharing scheme, "
        "https://github.com/dsprenkels/sss.",
        "Bormann C., Hoffman P. (2020), Concise Binary Object Representation (CBOR), RFC 8949, "
        "Internet Engineering Task Force.",
        "OWASP Foundation (2024), Password Storage Cheat Sheet, https://cheatsheetseries.owasp.org/.",
        "Fridrich J., Goljan M., Du R. (2001), “Detecting LSB steganography in color and gray-scale "
        "images”, IEEE Multimedia, 8(4), tr. 22–28.",
        "Westfeld A., Pfitzmann A. (1999), “Attacks on Steganographic Systems”, Information Hiding, "
        "LNCS 1768, Springer, tr. 61–76.",
        "Provos N., Honeyman P. (2003), “Hide and Seek: An Introduction to Steganography”, IEEE "
        "Security & Privacy, 1(3), tr. 32–44.",
        "Fridrich J. (2009), Steganography in Digital Media: Principles, Algorithms, and Applications, "
        "Cambridge University Press.",
        "Cox I. J., Miller M. L., Bloom J. A., Fridrich J., Kalker T. (2007), Digital Watermarking and "
        "Steganography, xuất bản lần thứ hai, Morgan Kaufmann.",
        "Vaudenay S. (2002), “Security Flaws Induced by CBC Padding — Applications to SSL, IPSEC, "
        "WTLS…”, EUROCRYPT 2002, LNCS 2332, Springer, tr. 534–545.",
        "Rogaway P. (2002), “Authenticated-encryption with associated-data”, Proceedings of the 9th ACM "
        "Conference on Computer and Communications Security, tr. 98–107.",
        "Klabnik S., Nichols C. (2023), The Rust Programming Language, xuất bản lần thứ hai, "
        "No Starch Press.",
        "Harkins P. và cộng sự (2020–), ExifTool by Phil Harvey — Read, Write and Edit Meta "
        "Information, https://exiftool.org/.",
        "Tauri Working Group (2024), Tauri v2 Documentation, https://v2.tauri.app/.",
        "International Organization for Standardization (2022), ISO/IEC 27001:2022 — Information "
        "security, cybersecurity and privacy protection — Information security management systems.",
        "National Institute of Standards and Technology (2020), NIST SP 800-175B Rev. 1 — Guideline "
        "for Using Cryptographic Standards in the Federal Government: Cryptographic Mechanisms.",
    ]
    B += [("h1", "TÀI LIỆU THAM KHẢO")]
    for i, r in enumerate(refs, 1):
        B.append(("pn", "[%d]  %s" % (i, r)))
    return B
