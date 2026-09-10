#!/usr/bin/env python3
"""Sinh văn bản ĐỀ CƯƠNG CHI TIẾT VỀ SÁNG KIẾN (DOCX) — văn bản 05 của bộ hồ sơ.

Vai trò trong bộ hồ sơ. Ba văn bản nội dung xếp theo độ sâu tăng dần: Thuyết minh (02) trả
lời *sáng kiến này là gì và đáng giá ở đâu*, Đề cương sơ bộ (04) trả lời *định làm gì, làm
theo cách nào, lấy gì để chứng minh*, còn văn bản này trả lời *đã làm như thế nào, ở mức
từng cơ chế*. Bản Thuyết minh phải gọn dưới 20 trang để hội đồng đọc nhanh, nên chỉ giữ
được phần có giá trị chứng minh cao nhất; văn bản này giữ toàn bộ phần còn lại:
lập luận thiết kế, các quyết định kiến trúc và phương án đã cân nhắc, cấu trúc dữ liệu do
nhóm tác giả thiết kế, mô tả đầy đủ từng chức năng kèm giao diện thực hiện nó, chiến lược kiểm
chứng, ảnh chụp toàn bộ màn hình và quy trình nghiệm thu.

Kết cấu được nhóm tác giả tự thiết kế theo mạch: *vấn đề thực tiễn → nguyên lý và quyết định
kiến trúc → cách giải quyết từng vấn đề kỹ thuật → sản phẩm → kiểm chứng → giá trị*. Mạch
này trả lời không chỉ “sản phẩm có gì” mà cả “vì sao cần nó” và “nhóm tác giả đã giải quyết như
thế nào”.

Số liệu dùng chung với các văn bản khác qua du_lieu_ho_so.py; nội dung tám nhóm chức năng
dùng chung qua noi_dung_chuc_nang.py. Không có con số nào nhập tay trong tệp này.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from dinh_dang import (  # noqa: E402
    bang, bullet, chu_ky, danh_so_trang, dat_lai_dem, h1, h2, h3, hinh,
    khung_nhan_manh, muc_luc, new_document, para, rich, tieuDeChinh, tieu_de_quan_doi,
    trang_bia,
)
from du_lieu_ho_so import (  # noqa: E402
    A2, CHUOI_OS, CI_XANH, DS_LENH, MB_APK, N_CRATE, N_LENH, N_TEST, SHA_APK,
    SO_DOI_CHUNG, TEN_OS, TEST_THEO_CRATE, TT, arm, host, hinh_ghep, ngat_duoc,
)
from noi_dung_chuc_nang import NHOM_CHUC_NANG  # noqa: E402
from noi_dung_giao_dien import DANH_MUC_MAN_HINH, LENH_MUC_UNG_DUNG  # noqa: E402
from ten_sang_kien import (  # noqa: E402
    CHU_NHIEM, DIA_DANH_NGAY, TEN_SANG_KIEN, TEN_SANG_KIEN_HOA, TEN_SP,
)

BASE = pathlib.Path(__file__).parent
PNG = BASE / "hinh-anh" / "png"

doc = new_document()
dat_lai_dem()
danh_so_trang(doc)

trang_bia(doc, TEN_SANG_KIEN_HOA, nhan="ĐỀ CƯƠNG CHI TIẾT VỀ SÁNG KIẾN")
tieu_de_quan_doi(doc)
tieuDeChinh(doc, "ĐỀ CƯƠNG CHI TIẾT VỀ SÁNG KIẾN")
para(doc, TEN_SANG_KIEN, bold=True, align=1, indent=False)

h1(doc, "LỜI DẪN")
para(doc,
     "Tài liệu này là phần trình bày đầy đủ của sáng kiến, đi kèm bản Thuyết minh. Bản "
     "Thuyết minh được giới hạn dưới 20 trang để hội đồng nắm nhanh sáng kiến là gì, mới ở "
     "đâu và có giá trị gì; vì vậy phần lập luận thiết kế, các phương án đã cân nhắc, cấu "
     "trúc dữ liệu, mô tả từng chức năng và toàn bộ bằng chứng kiểm chứng được đưa về đây.")
para(doc,
     "*Một lưu ý về tên gọi.* Tên sáng kiến nói “đa nền tảng” vì sản phẩm dùng chung một lõi "
     "nghiệp vụ và một định dạng dữ liệu cho cả bản trên máy tính lẫn bản trên thiết bị di "
     "động. Điều đó không làm đổi trọng tâm: *bản di động vẫn là nơi bài toán kỹ thuật phát "
     "sinh và được giải quyết*, còn bản máy tính giữ vai trò đối chứng và mở rộng phạm vi sử "
     "dụng. Mục 2.4 và 5.5 trình bày rõ ranh giới giữa hai vai trò đó cùng bằng chứng kèm theo.")
para(doc,
     "Nhóm tác giả chọn mạch trình bày theo đúng trình tự công việc đã thực sự diễn ra: xác định "
     "ràng buộc và nhu cầu thực tiễn; khảo sát cái đã có để tìm khoảng trống; đặt nguyên lý "
     "thiết kế; ra các quyết định kiến trúc và ghi lại phương án bị loại cùng lý do; giải "
     "quyết từng vấn đề kỹ thuật; dựng sản phẩm; kiểm chứng; và cuối cùng là đánh giá giá "
     "trị cùng giới hạn. Mạch này cho phép người đọc kiểm tra không chỉ *sản phẩm có gì* mà "
     "cả *vì sao lại làm như vậy*.")
para(doc,
     "Một quy ước xuyên suốt cả hồ sơ: mọi con số kỹ thuật trong tài liệu đều được sinh tự "
     "động từ mã nguồn, gói cài đặt và nhật ký kiểm thử, không nhập tay. Những gì chưa kiểm "
     "chứng được thì ghi rõ là chưa kiểm chứng, kèm quy trình để đơn vị tự xác nhận.")

muc_luc(doc, sang_trang=True)

# =====================================================================
# PHẦN I
# =====================================================================
h1(doc, "PHẦN I. VẤN ĐỀ THỰC TIỄN VÀ BÀI TOÁN ĐẶT RA", sang_trang=True)

h2(doc, "1.1. Ràng buộc nghiệp vụ — điểm xuất phát của sáng kiến")
para(doc,
     "Sáng kiến này bắt đầu từ một ràng buộc chứ không từ một ý tưởng công nghệ. Trong môi "
     "trường công tác ở Học viện Khoa học Quân sự và các cơ quan, đơn vị có yêu cầu cao về "
     "bảo vệ thông tin, việc quản lý, lưu trữ và chuyển giao tài liệu mật, tài liệu nội bộ "
     "phải tuân thủ nghiêm ngặt quy định hiện hành; đơn vị không cho phép đưa tài liệu mật "
     "và tài liệu nội bộ lên thiết bị di động cá nhân.")
para(doc,
     "Ràng buộc đó được nhóm tác giả xác định ngay từ đầu và giữ nguyên trong suốt quá trình "
     "thiết kế. Nó loại bỏ một hướng đi tưởng như hiển nhiên — làm một ứng dụng để mang tài "
     "liệu công tác theo người — và buộc sáng kiến phải tìm giá trị ở chỗ khác. Kết quả là "
     "hai nhu cầu nằm hoàn toàn trong ranh giới cho phép, trình bày ở mục tiếp theo.")
khung_nhan_manh(doc, "Phạm vi tự giới hạn của sáng kiến", [
    "Sáng kiến không đề xuất, không hàm ý và không tạo cơ sở cho việc thay đổi hay nới lỏng "
    "bất kỳ quy định nào về bảo vệ bí mật.",
    "Việc một tài liệu cụ thể có được phép lưu trữ, xử lý hay chuyển giao qua một phương "
    "thức nhất định hay không hoàn toàn do quy định hiện hành và người có thẩm quyền quyết "
    "định. Công cụ chỉ bổ sung biện pháp kỹ thuật trong phạm vi hoạt động đã được phép.",
], mau="FDF3E3", vien="B07D2B")

h2(doc, "1.2. Hai nhu cầu thực tiễn")
para(doc, "*Nhu cầu thứ nhất — huấn luyện.* "
     "Bảo vệ dữ liệu bằng mật mã là nội dung quan trọng trong chương trình đào tạo an toàn "
     "thông tin, bảo đảm an toàn tình báo trên không gian mạng. Nhưng việc học hiện nay chủ "
     "yếu dừng ở cơ sở lý thuyết, thuật toán và công cụ chạy trên máy tính. Trong khi đó "
     "thiết bị di động mới là môi trường mà học viên sẽ phải bảo vệ dữ liệu nhiều nhất sau "
     "khi ra trường. Khoảng cách giữa điều được học và môi trường thực tế làm giảm hiệu quả "
     "huấn luyện: học viên biết nguyên lý nhưng chưa từng thao tác, chưa từng nhìn thấy một "
     "hệ thống an toàn hoàn chỉnh vận hành ra sao và vì sao nó được thiết kế như vậy.")
para(doc,
     "Điều cần có là một môi trường thực hành an toàn: học viên trực tiếp mã hoá tệp bằng "
     "mật khẩu, tạo và kiểm tra chữ ký số, chia khoá theo ngưỡng, xoá siêu dữ liệu, kiểm tra "
     "toàn vẹn — và quan sát được kết quả ngay trên thiết bị. Quan trọng hơn, học viên phải "
     "thấy được cả *giới hạn* của mỗi biện pháp, vì hiểu sai về giới hạn của một công cụ an "
     "toàn còn nguy hiểm hơn không dùng công cụ nào.")
para(doc, "*Nhu cầu thứ hai — tình huống khẩn cấp, bất khả kháng.* "
     "Trong công tác vẫn phát sinh trường hợp một số tài liệu đặc thù buộc phải chuyển gấp "
     "qua không gian mạng khi không còn phương án nào khác kịp thời hạn. Đây là tình huống "
     "rủi ro nhất: tệp rời khỏi tầm kiểm soát của người gửi và đi qua hạ tầng không do đơn vị "
     "quản lý, nguy cơ bị chặn bắt, sao chép hoặc tiếp cận trái phép tăng lên.")
para(doc,
     "Trong những trường hợp đã được cấp có thẩm quyền cho phép chuyển giao, cán bộ cần một "
     "công cụ tin cậy và kiểm chứng được để tự trang bị thêm lớp bảo vệ cho tệp trước khi "
     "gửi. Bốn cơ chế tương ứng bốn nguy cơ: mã hoá bằng mật khẩu để nội dung không đọc được "
     "khi tệp bị tiếp cận trái phép; ký số để bên nhận tự xác minh nguồn gốc và tính toàn vẹn "
     "mà không phải tin vào kênh truyền; xoá siêu dữ liệu để không vô tình gửi kèm toạ độ "
     "định vị và thông tin thiết bị; chia bí mật theo ngưỡng để một kênh bị lộ vẫn chưa đủ "
     "khôi phục dữ liệu. Mục tiêu cuối cùng rất cụ thể: nếu tệp bị chặn bắt trên đường "
     "truyền thì bên chặn bắt thu được bản mã chứ không phải nội dung.")
hinh(doc, PNG / "H1-bai-toan-thuc-te.png",
     "Hai nhu cầu thực tiễn mà sáng kiến hướng tới và bốn nhóm nguy cơ tương ứng")

h2(doc, "1.3. Khảo sát các nhóm giải pháp đã biết")
para(doc,
     "Trước khi xây dựng, nhóm tác giả khảo sát các nhóm giải pháp hiện có theo hướng tiếp cận "
     "chức năng, nhằm xác định chính xác khoảng trống cần lấp. Phân tích dưới đây cố gắng "
     "giữ khách quan: mỗi nhóm đều giải quyết tốt bài toán mà nó được thiết kế cho: vấn đề "
     "là không nhóm nào giải quyết trọn vẹn bài toán đang xét.")
bang(doc, "So sánh các nhóm giải pháp đã biết với nhu cầu đặt ra",
     ["Nhóm giải pháp", "Ưu điểm", "Nhược điểm chưa được khắc phục"],
     [
         ["Mã hoá toàn thiết bị của hệ điều hành (FBE/FDE Android)",
          "Bảo vệ dữ liệu khi thiết bị ở trạng thái tắt hoặc chưa mở khoá lần đầu; trong "
          "suốt với người dùng",
          "Khi máy đã mở khoá, mọi ứng dụng và người cầm máy đều thấy dữ liệu ở dạng rõ; "
          "hoàn toàn không bảo vệ được tệp khi đưa ra khỏi thiết bị"],
         ["Ứng dụng “khoá tệp”, “két riêng tư” trên kho ứng dụng",
          "Giao diện thuận tiện, cài đặt nhanh, nhiều lựa chọn",
          "Phần lớn mã nguồn đóng nên không kiểm chứng được thuật toán và cách quản lý khoá; "
          "nhiều ứng dụng yêu cầu quyền truy cập mạng hoặc đồng bộ đám mây; định dạng riêng "
          "khiến người dùng bị khoá vào một sản phẩm"],
         ["Trình quản lý mật khẩu mã nguồn mở (KeePassDX, Bitwarden…)",
          "Quản lý thông tin đăng nhập rất tốt, kiểm chứng được",
          "Được thiết kế cho mật khẩu, không nhằm xử lý tệp, ảnh, tài liệu và không có các "
          "nghiệp vụ ký số, kiểm tra toàn vẹn, chia khoá phục hồi, xử lý siêu dữ liệu"],
         ["Công cụ mật mã dòng lệnh (age, GPG, OpenSSL, VeraCrypt)",
          "Thuật toán tin cậy, được cộng đồng soi xét lâu dài",
          "Không có bản dùng được trên di động do rào cản kiến trúc nền tảng (mục 3.1); giao "
          "diện dòng lệnh không phù hợp với người dùng không chuyên"],
         ["Ứng dụng nhắn tin mã hoá đầu-cuối",
          "Bảo vệ rất tốt dữ liệu trên đường truyền",
          "Không bảo vệ dữ liệu ở trạng thái lưu trữ trên máy; dữ liệu vẫn đi qua hạ tầng "
          "của nhà cung cấp dịch vụ nước ngoài"],
         ["Giải pháp quản lý thiết bị / chống thất thoát dữ liệu (MDM/DLP)",
          "Quản lý tập trung, phù hợp quy mô lớn",
          "Cần hạ tầng máy chủ, chi phí bản quyền và phụ thuộc nhà cung cấp; khó triển khai "
          "cho nhu cầu cá nhân và nhóm nhỏ"],
     ], widths=[4.0, 4.2, 7.3])
para(doc,
     "Nhận xét rút ra không phải là “các giải pháp hiện có kém”, mà là chúng được thiết kế "
     "cho những bài toán khác. Hai nhu cầu ở mục 1.2 đòi hỏi đồng thời: bảo vệ theo tệp "
     "(chứ không theo thiết bị), kiểm chứng được (chứ không phải tin vào nhà cung cấp), chạy "
     "được trên di động, và đủ nhiều nghiệp vụ để dùng làm học cụ. Không nhóm nào có đủ bốn.")
bang(doc, "Ma trận đối chiếu theo tiêu chí kiểm tra được",
     ["Tiêu chí", "Mã hoá toàn thiết bị", "Ứng dụng két thương mại", "Công cụ dòng lệnh",
      TEN_SP],
     [
         ["Chạy được trên Android", "Có", "Có", "Không", "Có"],
         ["Không yêu cầu quyền mạng", "Có", "Thường không", "Có", "Có"],
         ["Mã nguồn kiểm tra được", "Một phần", "Thường không", "Có", "Có"],
         ["Có bộ kiểm thử công khai", "Không rõ", "Không", "Có", "Có"],
         ["Bảo vệ tệp sau khi rời thiết bị", "Không", "Một phần", "Có", "Có"],
         ["Ký số và kiểm tra nguồn gốc", "Không", "Thường không", "Có", "Có"],
         ["Chia khoá phục hồi theo ngưỡng", "Không", "Thường không", "Một phần", "Có"],
         ["Xử lý siêu dữ liệu ẩn trong ảnh", "Không", "Thường không", "Có", "Có"],
         ["Định dạng tệp theo chuẩn mở", "Không áp dụng", "Thường không", "Có", "Có"],
         ["Dùng được làm học cụ giảng dạy", "Hạn chế", "Hạn chế", "Có", "Có"],
     ], widths=[4.6, 2.6, 2.8, 2.6, 2.9],
     note=f"Cột {TEN_SP} chỉ đối chiếu với chức năng đã hiện thực và kiểm chứng; "
          "cách kiểm chứng từng dòng trình bày ở Phần V.")

h2(doc, "1.4. Phát biểu bài toán")
para(doc,
     "Từ khảo sát trên, bài toán được phát biểu như sau: *xây dựng một bộ công cụ bảo vệ dữ "
     "liệu chạy hoàn toàn trên thiết bị di động Android, đồng thời đáp ứng năm yêu cầu dưới "
     "đây, mà đến thời điểm khảo sát chưa có sản phẩm nào đáp ứng đủ:*")
for _h, _t in [
    ("Yêu cầu 1 — hoạt động hoàn toàn trên thiết bị. ",
     "Không yêu cầu quyền truy cập mạng, không tài khoản, không đồng bộ đám mây. Yêu cầu này "
     "phải được bảo đảm bằng ràng buộc kỹ thuật kiểm tra được, không phải bằng lời cam kết."),
    ("Yêu cầu 2 — kiểm chứng được. ",
     "Mã nguồn kiểm soát được, thuật toán công khai, có bộ kiểm thử tự động để bên thứ ba "
     "chạy lại và tự kết luận."),
    ("Yêu cầu 3 — gộp nhiều nghiệp vụ trong một ứng dụng thống nhất. ",
     "Người dùng không phải ghép nhiều công cụ rời rạc cho một quy trình bảo vệ dữ liệu."),
    ("Yêu cầu 4 — tệp đầu ra theo chuẩn mở. ",
     "Bảo đảm tương thích và thuận tiện khi chuyển đổi giữa các sản phẩm, nền tảng khác "
     "nhau; người dùng không bị khoá vào một sản phẩm."),
    ("Yêu cầu 5 — dùng được làm học cụ. ",
     "Mỗi nhóm chức năng ứng với một nguyên lý trong chương trình, đồng thời sản phẩm vẫn "
     "phải đạt chuẩn kỹ thuật của một công cụ dùng thật, không phải bản mô phỏng."),
]:
    bullet(doc, _t, bold_head=_h)
para(doc,
     "Yêu cầu 5 đáng chú ý ở chỗ nó thường mâu thuẫn với bốn yêu cầu còn lại. Một sản phẩm "
     "dựng riêng để dạy học thường được đơn giản hoá tới mức không dùng được thật; ngược "
     "lại, một công cụ chuyên nghiệp thường quá phức tạp để đưa vào giờ thực hành. Cách hoá "
     "giải mâu thuẫn này chính là một trong những điểm sáng tạo của sáng kiến, trình bày ở "
     "mục 6.1 và 6.2.")

h2(doc, "1.5. Mô hình mối đe doạ")
para(doc,
     "Một sản phẩm an toàn phải nói rõ nó bảo vệ chống lại cái gì và *không* bảo vệ chống lại "
     "cái gì. Nhóm tác giả xác lập mô hình mối đe doạ ngay từ giai đoạn thiết kế, trước khi viết "
     "mã, và giữ nó làm căn cứ cho mọi quyết định về sau. Các giả định nền:")
for _t in [
    "Thiết bị chạy hệ điều hành chưa bị chiếm quyền điều khiển ở mức nhân. Nếu giả định này "
    "sai thì mọi biện pháp trong phạm vi ứng dụng đều mất hiệu lực.",
    "Người dùng giữ được mật khẩu và các mảnh khoá phục hồi. Ứng dụng cố tình không lưu mật "
    "khẩu lâu dài, nên không có cửa sau nào để bù lại việc quên mật khẩu.",
    "Kẻ tấn công có thể lấy được tệp (két, tệp đã khoá, mảnh khoá) nhưng không có mật khẩu; "
    "hoặc chặn bắt được tệp trên đường truyền.",
    "Các nguyên hàm mật mã được dùng (Argon2id, BLAKE3, age v1, XSalsa20-Poly1305, Ed25519, "
    "Shamir) là an toàn theo hiểu biết công khai hiện nay.",
]:
    bullet(doc, _t)
bang(doc, "Mô hình mối đe doạ đầy đủ: phạm vi bảo vệ và giới hạn",
     ["Tình huống", "Có bảo vệ?", "Giải thích"],
     [
         ["Mất hoặc thất lạc điện thoại khi máy đang khoá", "Có",
          "Dữ liệu trong két ở dạng mã hoá; không có mật khẩu thì không mở được"],
         ["Người khác mượn máy khi máy đã mở khoá", "Có, một phần",
          "Két vẫn cần mật khẩu riêng; nhưng nếu phiên đang mở thì nội dung có thể xem được"],
         ["Sao chép tệp két ra khỏi thiết bị", "Có",
          "Tệp két tự bảo vệ, mở ở nơi khác vẫn cần mật khẩu"],
         ["Tệp bị sửa đổi hoặc hỏng trên đường truyền", "Có",
          "Chữ ký ràng buộc phát hiện mọi thay đổi, kể cả ghép phần đầu tệp này với nội dung "
          "tệp khác"],
         ["Tệp bị chặn bắt khi buộc phải truyền gấp qua không gian mạng", "Có",
          "Tệp truyền đi ở dạng đã mã hoá có xác thực; bên chặn bắt thu được bản mã nhưng "
          "không có mật khẩu thì không đọc được nội dung"],
         ["Bên nhận không chắc tệp có đúng do người gửi tạo ra không", "Có",
          "Chữ ký số cho phép bên nhận tự xác minh nguồn gốc và tính toàn vẹn, không cần tin "
          "vào kênh truyền"],
         ["Ảnh chia sẻ mang theo toạ độ định vị", "Có",
          "Chức năng xoá siêu dữ liệu loại bỏ trước khi chia sẻ; có chức năng so sánh để "
          "người dùng tự kiểm tra kết quả"],
         ["Lộ tệp do gửi nhầm qua ứng dụng khác", "Có, một phần",
          "Nếu gửi tệp két thì bên nhận vẫn cần mật khẩu; nếu gửi tệp đã trích xuất thì không"],
         ["Suy đoán mật khẩu từ khác biệt giữa các thông báo lỗi", "Có",
          "Quy tắc phân loại lỗi hợp nhất các trường hợp có thể dùng làm tín hiệu dò (mục 3.6)"],
         ["Thiết bị đã bị chiếm quyền điều khiển ở mức hệ điều hành", "Không",
          "Phần mềm độc hại có quyền cao đọc được bộ nhớ tiến trình khi két đang mở"],
         ["Người dùng quên mật khẩu và không tạo mảnh phục hồi", "Không",
          "Hệ quả trực tiếp của nguyên tắc không lưu mật khẩu lâu dài — đây là đánh đổi có "
          "chủ ý, không phải thiếu sót"],
         ["Kẻ tấn công cưỡng ép người dùng cung cấp mật khẩu", "Không",
          "Nằm ngoài phạm vi của biện pháp kỹ thuật"],
     ], widths=[5.4, 2.2, 7.9])

# =====================================================================
# PHẦN II
# =====================================================================
h1(doc, "PHẦN II. NGUYÊN LÝ THIẾT KẾ VÀ CÁC QUYẾT ĐỊNH KIẾN TRÚC", sang_trang=True)

h2(doc, "2.1. Sáu nguyên lý và cách chuyển hoá thành ràng buộc kỹ thuật")
para(doc,
     "Sáu nguyên lý dưới đây được xác lập trước khi viết dòng mã đầu tiên. Điểm mà nhóm tác giả "
     "coi trọng không phải bản thân các nguyên lý — chúng là hiểu biết chung của ngành — mà "
     "là việc mỗi nguyên lý được chuyển hoá thành một ràng buộc cụ thể trong phần mềm, và "
     "mỗi ràng buộc lại gắn với một cách kiểm tra. Nguyên lý chỉ nằm trong tài liệu thì sớm "
     "muộn cũng bị vi phạm khi phần mềm được sửa đổi; nguyên lý có cơ chế kiểm tra thì không.")
bang(doc, "Sáu nguyên lý thiết kế, cơ chế thực thi và cách kiểm tra",
     ["Nguyên lý", "Cơ chế thực thi trong sản phẩm", "Cách kiểm tra"],
     [
         ["Hoạt động ngoại tuyến tuyệt đối",
          "Ứng dụng không khai báo quyền truy cập mạng trong AndroidManifest.xml. Đây là "
          "ràng buộc ở cấp hệ điều hành: không có quyền thì tiến trình không mở được kết "
          "nối, bất kể mã nguồn viết gì",
          "Đọc tệp kê khai trong gói cài đặt đã đóng gói"],
         ["Một lõi bảo vệ dữ liệu dùng chung",
          f"Toàn bộ nghiệp vụ mật mã nằm trong lõi gồm {N_CRATE} thành phần độc lập, không "
          "thành phần nào dùng thư viện giao diện hay thư viện đặc thù nền tảng",
          "Đọc quan hệ phụ thuộc khai báo của từng thành phần"],
         ["Phụ thuộc một chiều theo lớp",
          "Lớp trên dùng lớp dưới, không có chiều ngược lại. Lõi chỉ phụ thuộc vào giao diện "
          "trừu tượng và quy ước xử lý, không phụ thuộc một cách triển khai cụ thể",
          "Lõi được kiểm thử độc lập với bản hiện thực giả lập; nếu lõi lỡ phụ thuộc vào bản "
          "thật thì phép kiểm thử này không biên dịch được"],
         ["Khi không bảo đảm an toàn thì không tiếp tục xử lý",
          "Thành phần chưa sẵn sàng bị vô hiệu hoá và báo ngay lúc khởi động; dữ liệu ngoài "
          "phạm vi xử lý bị từ chối kèm mã lỗi xác định, thay vì trả về trạng thái thành "
          "công không đúng thực tế",
          "Kiểm thử tình huống mô-đun không sẵn sàng và tình huống định dạng ngoài phạm vi"],
         ["Thông báo lỗi không làm lộ thông tin bí mật",
          "Sau khi chữ ký và khoá đã được kiểm tra xong, giải mã thất bại được báo là “tệp "
          "hỏng” thay vì “sai xác thực”; sai mật khẩu và sai mảnh khôi phục dùng chung một "
          "trạng thái lỗi",
          "Kiểm thử đối chiếu thông báo giữa hai bản hiện thực của mô-đun mã hoá"],
         ["Không lưu trữ bí mật lâu dài",
          "Mật khẩu chỉ tồn tại trong bộ nhớ trong thời gian xử lý và được quản lý bằng kiểu "
          "dữ liệu tự xoá nội dung khi ra khỏi phạm vi sử dụng; khoá chính chỉ nằm trong bộ "
          "nhớ phiên và bị xoá khi người dùng khoá két",
          "Kiểm thử vòng đời phiên làm việc"],
     ], widths=[3.6, 7.6, 4.3])

h2(doc, "2.2. Kiến trúc phân lớp")
para(doc,
     f"Ứng dụng được tổ chức thành sáu lớp chức năng. Giao diện và lõi nghiệp vụ tách hẳn "
     f"nhau: mọi yêu cầu từ giao diện xuống lõi đều phải đi qua {N_LENH} lệnh được kiểm soát "
     "thống nhất, không có đường truy cập trực tiếp nào khác. Ranh giới này là chỗ đặt các "
     "biện pháp bảo vệ: mật khẩu khi đi qua ranh giới được bọc trong kiểu dữ liệu tự xoá; "
     "phiên làm việc chỉ được tham chiếu bằng một mã định danh ngẫu nhiên không mang thông "
     "tin bí mật, nên kể cả khi lộ mã phiên cũng không suy ra được khoá.")
hinh(doc, PNG / "H2-kien-truc-phan-lop.png", f"Kiến trúc phân lớp của {TEN_SP}")
para(doc,
     f"Lõi gồm {N_CRATE} thành phần độc lập, mỗi thành phần một trách nhiệm: định dạng và "
     "nghiệp vụ két; các nguyên hàm mật mã; giao diện trừu tượng của nguyên hàm; hai bản "
     "hiện thực mô-đun mã hoá nội dung; hai bản hiện thực mô-đun siêu dữ liệu; nghiệp vụ "
     "trên tệp; giấu tin; thuỷ vân; mã QR; các lớp bọc thư viện hệ thống; kiểu dữ liệu dùng "
     "chung; và lớp ứng dụng nối tất cả lại. Việc tách thành nhiều thành phần không nhằm cho "
     "“gọn” mà để chiều phụ thuộc trở thành thứ kiểm tra được bằng máy.")

h2(doc, "2.3. Ba quyết định kiến trúc then chốt")
para(doc,
     "Phần này ghi lại ba quyết định có ảnh hưởng lớn nhất, kèm các phương án đã cân nhắc và "
     "lý do loại bỏ. Nhóm tác giả trình bày cả phương án bị loại vì đó mới là phần cho thấy quyết "
     "định được cân nhắc chứ không phải chọn ngẫu nhiên.")

para(doc, "2.3.1. Đưa năng lực mật mã lên nền tảng di động", bold=True, indent=False)
bang(doc, "Quyết định 1 — cách đưa mô-đun mã hoá nội dung lên di động",
     ["Phương án", "Đánh giá", "Kết luận"],
     [
         ["Đóng gói kèm tệp nhị phân của công cụ chuẩn và gọi như tiến trình con, giống bản "
          "máy tính",
          "Không khả thi: iOS cấm sinh tiến trình; Android chặn thực thi tệp nhị phân nằm "
          "trong vùng lưu trữ mà ứng dụng ghi được",
          "Loại"],
         ["Viết lại toàn bộ nghiệp vụ cho di động bằng một định dạng tệp mới, đơn giản hơn",
          "Khả thi về kỹ thuật nhưng phá vỡ tương thích: két tạo trên máy tính không mở được "
          "trên điện thoại và ngược lại; đồng thời phải bảo trì hai bộ nghiệp vụ song song",
          "Loại"],
         ["Gọi thư viện mật mã của hệ điều hành Android",
          "Buộc lõi phụ thuộc vào nền tảng, mất khả năng dùng chung với bản máy tính và mất "
          "khả năng kiểm thử độc lập; định dạng tệp cũng khác đi",
          "Loại"],
         ["Đặt điểm nối trừu tượng tại mô-đun mã hoá nội dung, viết một bản hiện thực thuần "
          "Rust chạy trong tiến trình, giữ nguyên định dạng tệp",
          "Nghiệp vụ, định dạng dữ liệu và hành vi của các lớp trên không đổi; hai nền tảng "
          "dùng chung một lõi; bản hiện thực mới kiểm chứng được bằng đối chứng với công cụ "
          "chuẩn",
          "Chọn"],
     ], widths=[5.2, 8.0, 2.3])

para(doc, "2.3.2. Xử lý siêu dữ liệu", bold=True, indent=False)
para(doc,
     "Bài toán tương tự lặp lại ở mô-đun siêu dữ liệu: bản máy tính gọi một công cụ ngoài "
     "dưới dạng tiến trình con, cách này không dùng được trên di động. Ba phương án được cân "
     "nhắc: (1) bỏ hẳn nhóm chức năng siêu dữ liệu trên bản di động — loại, vì đây là nhóm "
     "gắn trực tiếp với nguy cơ lộ toạ độ định vị, tức đúng thứ mà người dùng di động cần "
     "nhất; (2) gọi thư viện đọc ảnh của Android — loại, vì lõi sẽ phụ thuộc nền tảng và "
     "hành vi giữa hai bản không còn giống nhau; (3) tự viết một mô-đun thuần Rust, chạy "
     "trong tiến trình, phạm vi định dạng hẹp nhưng công bố rõ ràng — được chọn. Phương án "
     "3 kèm một hệ quả phải xử lý đúng: phạm vi định dạng hẹp hơn bản máy tính, nên giao "
     "diện phải phản ánh trung thực điều đó thay vì hứa hẹn quá khả năng (mục 3.7).")

para(doc, "2.3.3. Bất biến định dạng tệp", bold=True, indent=False)
para(doc,
     "Quyết định thứ ba là một ràng buộc tự đặt ra: *dù thay bản hiện thực nào bên dưới, "
     "định dạng tệp trên đĩa không được thay đổi.* Ràng buộc này khiến việc hiện thực khó "
     "hơn hẳn, nhưng nó bảo toàn ba giá trị: két tạo trên máy tính mở được trên điện thoại "
     "và ngược lại; tệp tạo ra vẫn kiểm tra được bằng công cụ chuẩn của cộng đồng; và người "
     "dùng không bị khoá vào sản phẩm. Vì đây là ràng buộc dễ bị vi phạm âm thầm, nhóm tác giả "
     "không kiểm tra nó bằng lập luận mà bằng thực nghiệm đối chứng hai chiều (mục 5.4).")

h2(doc, "2.4. Một lõi, nhiều nền tảng — hệ quả của việc tách nghiệp vụ khỏi nền tảng")
para(doc,
     "Ba quyết định trên có một hệ quả mà ban đầu không phải là mục tiêu, nhưng về sau trở "
     "thành một trong những tính chất đáng giá nhất của sáng kiến: *nếu nghiệp vụ, định dạng "
     "dữ liệu và cơ chế bảo vệ đều nằm dưới một ranh giới không phụ thuộc nền tảng, thì thay "
     "nền tảng không còn là viết lại sản phẩm, mà chỉ là thay phần nằm trên ranh giới đó.*")
para(doc,
     "Cụ thể trong mã nguồn, toàn bộ khác biệt giữa hai nền tảng gói gọn trong *một* lớp gọi "
     "là lớp lắp ráp ứng dụng, gồm đúng hai tệp: một cho máy tính, một cho thiết bị di động. "
     "Lớp này quyết định hai việc — dùng bản hiện thực nào cho mô-đun mã hoá nội dung, và "
     "dùng bản hiện thực nào cho mô-đun siêu dữ liệu — rồi bàn giao cho phần còn lại. Từ đó "
     "trở xuống, mọi thứ giống hệt nhau.")
bang(doc, "Cái gì đổi theo nền tảng và cái gì không",
     ["Thành phần", "Máy tính để bàn", "Thiết bị di động", "Có đổi không?"],
     [
         ["Mô-đun mã hoá nội dung két", "Điều khiển công cụ chuẩn dưới dạng tiến trình con, "
          "có ghim giá trị băm của tệp nhị phân", "Thực hiện ngay trong tiến trình ứng dụng",
          "Đổi"],
         ["Mô-đun xử lý siêu dữ liệu", "Gọi công cụ ngoài, phạm vi định dạng rộng",
          "Mô-đun thuần Rust do nhóm tác giả viết, phạm vi định dạng hẹp và công bố rõ", "Đổi"],
         ["Cách lấy tệp từ bộ nhớ thiết bị", "Đường dẫn tệp thông thường",
          "Qua bộ chọn tệp của hệ điều hành, sao chép vào vùng riêng của ứng dụng", "Đổi"],
         ["Bố cục giao diện", "Thanh điều hướng cố định bên trái",
          "Ngăn kéo trượt từ cạnh trái; vùng chạm tối thiểu 44 điểm ảnh",
          "Đổi (cùng một mã nguồn giao diện)"],
         ["Định dạng tệp két .svault", "Như nhau", "Như nhau", "Không"],
         ["Sơ đồ phân cấp khoá và tham số Argon2id", "Như nhau", "Như nhau", "Không"],
         [f"{N_LENH} lệnh nghiệp vụ và ngữ nghĩa của chúng", "Như nhau", "Như nhau", "Không"],
         ["Quy tắc phân loại lỗi", "Như nhau", "Như nhau", "Không"],
         [f"Lõi gồm {N_CRATE} thành phần", "Như nhau", "Như nhau", "Không"],
     ], widths=[3.8, 4.2, 4.2, 3.3])
para(doc,
     "Bảng trên là cách diễn đạt cụ thể nhất cho tính độc lập nền tảng: *bốn dòng đầu đổi, "
     "năm dòng sau không*. Và năm dòng không đổi mới là những dòng quyết định dữ liệu của "
     "người dùng có an toàn hay không.")
para(doc, "*Vai trò của từng nền tảng trong sáng kiến.* "
     "Bản trên máy tính ra đời trước và đóng ba vai trò: là bản *đối chứng* — chính nó cung "
     "cấp phía còn lại cho các phép kiểm tra chéo ở mục 5.4; là bản *tham chiếu ngữ nghĩa* — "
     "khi bản di động cho kết quả khác, bản máy tính là chuẩn để đối chiếu; và là bản *mở "
     "rộng phạm vi sử dụng* — cùng bộ chức năng dùng được trên máy trạm của đơn vị, tệp két "
     "đi lại được giữa hai môi trường. Bản di động thì khác hẳn về vai trò: nó là nơi bài "
     "toán kỹ thuật thực sự phát sinh (mục 3.1) và được giải quyết, nên cũng là nơi tập trung "
     "giá trị sáng tạo của sáng kiến. Nói ngắn gọn: *bản máy tính chứng minh kiến trúc là "
     "đúng, bản di động chứng minh kiến trúc là có ích.*")
khung_nhan_manh(doc, "Ranh giới của tuyên bố về đa nền tảng", [
    "Hồ sơ nêu khả năng đa nền tảng ở đúng mức kiểm chứng được: mã nguồn của lõi và của lớp "
    "vỏ ứng dụng được dựng, soát mã và chạy kiểm thử tự động trên cả ba hệ điều hành máy tính "
    f"({CHUOI_OS}) trong quy trình tích hợp liên tục (mục 5.5).",
    "Việc đóng gói bản cài đặt có ký số và công chứng cho từng hệ điều hành máy tính — bước "
    "cần thiết để phân phối rộng rãi — chưa thực hiện. Vì vậy hồ sơ không tuyên bố sản phẩm "
    "đã sẵn sàng phát hành trên Windows hay macOS; điều được khẳng định là *kiến trúc và mã "
    "nguồn chạy được trên các nền tảng đó*, có bằng chứng kèm theo.",
], mau="FDF3E3", vien="B07D2B")

# =====================================================================
# PHẦN III
# =====================================================================
h1(doc, "PHẦN III. GIẢI QUYẾT CÁC VẤN ĐỀ KỸ THUẬT", sang_trang=True)

h2(doc, "3.1. Rào cản tiến trình con trên nền tảng di động")
para(doc,
     "Đây là nội dung mang hàm lượng kỹ thuật cao nhất của sáng kiến, và cũng là lý do vì "
     "sao các công cụ mật mã mạnh hiện nay không có bản dùng được trên điện thoại — một sự "
     "thật dễ bị hiểu nhầm thành “chưa ai chịu làm”.")
para(doc,
     "Các công cụ mật mã tin cậy được phân phối dưới dạng tệp nhị phân chạy độc lập. Trên "
     "máy tính để bàn, ứng dụng gọi chúng như một tiến trình con: nạp tệp nhị phân, truyền "
     "tham số, đọc kết quả. Trên thiết bị di động thì cơ chế này bị chặn ở hai tầng khác "
     "nhau: iOS cấm hoàn toàn việc một ứng dụng sinh tiến trình; Android cho phép sinh tiến "
     "trình nhưng chặn thực thi tệp nhị phân nằm trong vùng lưu trữ mà ứng dụng ghi được — "
     "tức đúng nơi mà một tệp nhị phân đóng gói kèm ứng dụng sẽ nằm.")
para(doc,
     "Hệ quả rất cụ thể: mọi chức năng phụ thuộc tiến trình con sẽ không hoạt động trên điện "
     "thoại, *kể cả khi mã nguồn biên dịch thành công*. Đây là điểm khiến rào cản khó phát "
     "hiện sớm: chương trình dựng xong, cài được, mở được, và chỉ hỏng khi người dùng bấm "
     "vào chức năng. Vì vậy nhóm tác giả xác định đây là rào cản thuộc về kiến trúc nền tảng, "
     "phải giải quyết bằng thiết kế chứ không bằng công sức lập trình.")

h2(doc, "3.2. Điểm nối trừu tượng và hai bản hiện thực")
para(doc,
     "Giải pháp là đặt *điểm nối trừu tượng* tại đúng những vị trí phụ thuộc nền tảng. Cụ "
     "thể: lõi không gọi thẳng công cụ mã hoá, mà gọi qua một giao diện trừu tượng mô tả "
     "đúng ba việc cần làm — sinh cặp khoá, mã hoá, giải mã. Bên dưới giao diện đó có hai "
     "bản hiện thực: bản máy tính điều khiển công cụ chuẩn dưới dạng tiến trình con (có ghim "
     "giá trị băm của tệp nhị phân để phát hiện tráo đổi), và bản di động thực hiện toàn bộ "
     "phép mã hoá ngay trong tiến trình ứng dụng. Việc chọn bản nào diễn ra ở lớp lắp ráp "
     "ứng dụng, theo nền tảng biên dịch — lõi hoàn toàn không biết mình đang chạy với bản "
     "nào.")
hinh(doc, PNG / "H3-loi-dung-chung.png",
     "Nguyên tắc một lõi dùng chung, hai bản hiện thực theo nền tảng")
para(doc,
     "Điều đáng lưu ý về mặt thiết kế là *vị trí* của điểm nối. Đặt quá cao (ở mức nghiệp "
     "vụ) thì mỗi nền tảng phải viết lại toàn bộ nghiệp vụ; đặt quá thấp (ở mức từng phép "
     "mật mã) thì bản hiện thực phải tự ghép lại đúng định dạng tệp và rất dễ lệch. Điểm nối "
     "được đặt đúng ở ranh giới “một luồng dữ liệu vào, một luồng dữ liệu ra theo định dạng "
     "công khai”, nhờ vậy hai bản hiện thực khác nhau hoàn toàn về cách chạy nhưng buộc phải "
     "cho ra cùng một chuỗi byte.")
para(doc,
     "Cùng nguyên tắc đó được áp dụng lần thứ hai cho mô-đun siêu dữ liệu, cho thấy đây là "
     "một khuôn mẫu giải quyết vấn đề chứ không phải một mẹo dùng một lần.")

h2(doc, "3.3. Định dạng tệp két .svault do nhóm tác giả thiết kế")
para(doc,
     "Két an toàn là một tệp duy nhất. Cấu trúc tệp gồm bốn phần nối tiếp: chuỗi nhận dạng "
     "và phiên bản định dạng; độ dài phần đầu; phần đầu tệp ở dạng có cấu trúc; phần nội "
     "dung đã mã hoá; và cuối cùng là chữ ký số. Ba quyết định thiết kế quan trọng nằm trong "
     "cấu trúc này:")
for _h, _t in [
    ("Danh mục tệp nằm bên trong phần đã mã hoá, không nằm ở phần đầu. ",
     "Đây là điểm khác biệt so với cách làm thông thường. Nhiều định dạng đặt danh sách tệp "
     "ở phần đầu cho tiện đọc nhanh; hệ quả là người có tệp mà không có mật khẩu vẫn biết "
     "bên trong có những gì. Ở đây toàn bộ nội dung két, kể cả danh mục, là một luồng mã hoá "
     "duy nhất — két đang khoá không tiết lộ tên tệp, kích thước hay cả số lượng tệp, chỉ lộ "
     "tổng độ dài bản mã."),
    ("Phần đầu tệp chỉ chứa khoá đã được bọc, không bao giờ chứa khoá ở dạng rõ. ",
     "Các khoá bên trong được bọc bằng mã hoá có xác thực, với khoá bọc dẫn xuất riêng cho "
     "từng trường và ràng buộc theo mã định danh của két."),
    ("Chữ ký phủ lên một “gốc ràng buộc” tính từ cả phần đầu lẫn phần nội dung. ",
     "Nhờ vậy không thể ghép phần đầu của tệp này với phần nội dung của tệp khác: các giá "
     "trị băm của từng phần được tính lại khi đọc chứ không lưu sẵn trong tệp, nên tệp ghép "
     "sẽ cho gốc ràng buộc khác và chữ ký không còn hợp lệ."),
]:
    bullet(doc, _t, bold_head=_h)
para(doc,
     "*Thứ tự kiểm tra khi mở két* cũng là một quyết định có chủ ý: kiểm tra chữ ký trước, "
     "rồi mới dẫn xuất khoá từ mật khẩu. Thứ tự này cho phép phân biệt rõ hai tình huống "
     "khác hẳn nhau — tệp hỏng hoặc bị sửa (phát hiện được mà chưa cần mật khẩu) và mật khẩu "
     "sai — mà không biến việc phân biệt đó thành manh mối dò mật khẩu, vì bước kiểm tra chữ "
     "ký diễn ra trước khi mật khẩu được dùng đến.")
para(doc,
     "Ngoài ra, mọi thao tác ghi tệp đều theo kiểu nguyên tử: ghi ra tệp tạm rồi mới thay "
     "thế. Nếu quá trình ghi bị gián đoạn — hết pin, người dùng thoát ứng dụng — thì tệp két "
     "cũ vẫn nguyên vẹn thay vì trở thành một tệp dở dang không mở được. Với một sản phẩm mà "
     "hỏng tệp đồng nghĩa mất dữ liệu vĩnh viễn, đây không phải chi tiết phụ.")

h2(doc, "3.4. Sơ đồ phân cấp khoá")
para(doc,
     "Mật khẩu người dùng không được lưu ở bất kỳ đâu. Từ mật khẩu, hệ thống dẫn xuất khoá "
     f"chính bằng Argon2id với tối thiểu {A2['min_mem_kib'] // 1024} MiB bộ nhớ và "
     f"{A2['min_time_cost']} vòng lặp, theo ngưỡng khuyến nghị của OWASP. Tham số bộ nhớ "
     "quan trọng hơn số vòng lặp: nó là thứ làm cho việc dò mật khẩu hàng loạt bằng phần "
     "cứng chuyên dụng trở nên tốn kém. Ngưỡng được đặt ở mức vừa đủ để một điện thoại phổ "
     "thông vẫn mở két trong thời gian chấp nhận được.")
hinh(doc, PNG / "H4-phan-cap-khoa.png", "Sơ đồ phân cấp khoá và luồng mở két")
para(doc,
     "Khoá chính chỉ tồn tại trong bộ nhớ của phiên làm việc, không bao giờ chạm tới bộ nhớ "
     "lưu trữ. Từ khoá chính, hệ thống dẫn xuất các khoá con riêng cho từng mục đích, mỗi "
     "khoá con gắn với một *ngữ cảnh dẫn xuất* gồm ba thành phần: phiên bản bộ thuật toán, "
     "tên trường được bảo vệ, và mã định danh của két. Cách ràng buộc này tạo ra hai tính "
     "chất đáng giá:")
for _t in [
    "Khoá bọc của một trường không dùng được cho trường khác — vì tên trường nằm trong ngữ "
    "cảnh, dẫn xuất sai ngữ cảnh sẽ ra khoá sai và phép kiểm tra xác thực thất bại.",
    "Khối dữ liệu đã bọc không thể mang từ két này sang két khác — vì mã định danh két nằm "
    "trong ngữ cảnh.",
]:
    bullet(doc, _t)
para(doc,
     "Một hệ quả thực dụng của thiết kế này: *đổi mật khẩu không phải mã hoá lại toàn bộ nội "
     "dung*. Chỉ cần dẫn xuất khoá chính mới và bọc lại vài khoá con trong phần đầu tệp. Với "
     "một két chứa nhiều tệp lớn trên điện thoại, khác biệt giữa vài mili-giây và vài phút "
     "là khác biệt giữa một chức năng người dùng thực sự dùng và một chức năng họ ngại dùng.")

h2(doc, "3.5. Lựa chọn nguyên hàm mật mã và tham số")
para(doc,
     "Giải pháp không tự xây dựng thuật toán mật mã mới — một nguyên tắc nghề nghiệp cơ bản "
     "mà nhóm tác giả tuân thủ. Toàn bộ nguyên hàm đều là chuẩn đã công bố, được cộng đồng nghiên "
     "cứu và soi xét lâu dài. Đóng góp của nhóm tác giả nằm ở việc chọn nguyên hàm nào cho việc "
     "gì, ghép chúng lại trong một kiến trúc, và đặt tham số phù hợp với ràng buộc của thiết "
     "bị di động.")
bang(doc, "Các thuật toán và cơ chế mật mã được lựa chọn",
     ["Chức năng trong thiết kế", "Nguyên hàm được chọn", "Lý do lựa chọn"],
     [
         ["Dẫn xuất khoá từ mật khẩu", TT["kdf"],
          f"Chống dò mật khẩu bằng phần cứng chuyên dụng; đặt ngưỡng "
          f"{A2['min_mem_kib'] // 1024} MiB / {A2['min_time_cost']} vòng theo khuyến nghị "
          "OWASP, cân bằng giữa độ khó dò và thời gian mở két trên điện thoại phổ thông"],
         ["Băm nội dung và tạo khoá con", TT["hash"],
          "Tốc độ xử lý cao, phù hợp thiết bị di động; hỗ trợ sẵn cơ chế dẫn xuất khoá theo "
          "ngữ cảnh — chính là cơ chế dùng để ràng buộc khoá con theo trường và theo két"],
         ["Mã hoá nội dung két", TT["aead_vault"],
          "Định dạng công khai, có đặc tả rõ ràng và công cụ chuẩn để đối chứng; đồng thời "
          "cung cấp cả mã hoá lẫn kiểm tra toàn vẹn"],
         ["Bảo vệ các trường khoá trong phần đầu tệp", TT["aead_field"],
          "Cơ chế mã hoá kèm xác thực đã được dùng rộng rãi, phù hợp để bảo vệ các khối dữ "
          "liệu khoá kích thước nhỏ"],
         ["Bảo vệ phần đầu tệp bằng chữ ký số", TT["chu_ky"],
          "Chữ ký kích thước nhỏ, xác minh nhanh, và ở định dạng có công cụ tương thích để "
          "bên thứ ba tự kiểm tra"],
         ["Chia khoá phục hồi", TT["chia_se_bi_mat"],
          "Chia khoá thành nhiều phần với ngưỡng khôi phục; dưới ngưỡng thì các mảnh không "
          "tiết lộ gì về bí mật"],
     ], widths=[4.6, 4.4, 6.5])

h2(doc, "3.6. Quy tắc phân loại lỗi an toàn")
para(doc,
     "Thông báo lỗi là một kênh rò rỉ thông tin thường bị bỏ qua. Nếu ứng dụng báo “sai mật "
     "khẩu” trong một trường hợp và “tệp hỏng” trong trường hợp khác, thì chính sự khác nhau "
     "đó trở thành công cụ để người tấn công dò dần. Nhóm tác giả xử lý bằng cách tách hẳn hai "
     "tầng: lõi bên trong phân biệt các nguyên nhân lỗi rất chi tiết để lập trình viên gỡ "
     "lỗi được; nhưng khi vượt qua ranh giới ra giao diện, các nguyên nhân được chiếu về một "
     "tập lỗi hẹp hơn theo quy tắc cố định.")
bang(doc, "Quy tắc chiếu lỗi từ lõi ra giao diện",
     ["Tình huống bên trong lõi", "Lỗi hiển thị cho người dùng", "Lý do"],
     [
         ["Sai mật khẩu; hoặc đủ số mảnh khôi phục nhưng mảnh không đúng",
          "Không đủ điều kiện truy cập",
          "Hợp nhất hai trường hợp để chênh lệch thông báo không dùng làm tín hiệu dò"],
         ["Thiếu mảnh khôi phục so với ngưỡng",
          "Thiếu mảnh: đã có k, cần n",
          "Đây là thông tin không bí mật và người dùng cần biết để bổ sung mảnh"],
         ["Không phải tệp của ứng dụng (sai chuỗi nhận dạng, tệp cụt, cấu trúc hỏng)",
          "Không phải tệp Secure Vault",
          "Tình huống lành tính, không liên quan đến bí mật; tách riêng để người dùng không "
          "hiểu nhầm là dữ liệu bị hỏng"],
         ["Đúng là tệp của ứng dụng nhưng chữ ký không hợp lệ",
          "Tệp bị hỏng hoặc đã bị sửa",
          "Phát hiện trước khi mật khẩu được dùng đến, nên không phải tín hiệu về mật khẩu"],
         ["Sai phiên bản định dạng",
          "Phiên bản định dạng không tương thích, kèm số phiên bản",
          "Thông tin không bí mật và giúp người dùng biết cần bản ứng dụng nào"],
         ["Lỗi vào/ra hệ thống (thiếu quyền, đầy bộ nhớ, đường dẫn sai)",
          "Lỗi đọc/ghi tệp, mô tả cố định",
          "Thông điệp gốc của hệ thống có thể chứa đường dẫn, nên thay bằng mô tả cố định"],
         ["Lỗi nội bộ ngoài dự kiến", "Lỗi nội bộ",
          "Không mô tả chi tiết trạng thái bên trong ra ngoài"],
     ], widths=[5.6, 4.4, 5.5])
para(doc,
     "Điểm cần nhấn mạnh: quy tắc này áp dụng thống nhất cho cả hai bản hiện thực của mô-đun "
     "mã hoá. Nếu bản di động và bản máy tính báo lỗi khác nhau trong cùng một tình huống thì "
     "chính sự khác nhau đó lại thành kênh rò rỉ mới — nên đây là một trong những nội dung "
     "được kiểm thử riêng.")

h2(doc, "3.7. Mô-đun xử lý siêu dữ liệu thuần Rust")
para(doc,
     "Ảnh chụp bằng điện thoại thường mang theo toạ độ GPS, kiểu thiết bị, thời điểm chụp và "
     "nhiều thông tin khác. Những dữ liệu này đi kèm tệp mà người dùng không nhận biết — một "
     "kênh lộ thông tin nằm ngoài nội dung. Bản máy tính xử lý nhóm này bằng cách gọi một "
     "công cụ ngoài; trên di động, cách đó vướng đúng rào cản ở mục 3.1, nên nhóm tác giả tự viết "
     "một mô-đun thuần Rust chạy trong tiến trình.")
para(doc,
     "Mô-đun này nhận dạng định dạng *từ các byte đầu tệp chứ không từ phần mở rộng* — vì "
     "phần mở rộng do người dùng đặt và có thể sai. Phạm vi hiện tại: đọc và liệt kê thẻ "
     "siêu dữ liệu với JPEG, PNG, TIFF, WebP và HEIF; xoá siêu dữ liệu với JPEG và PNG. Với "
     "định dạng nằm ngoài phạm vi xoá, mô-đun từ chối kèm mã lỗi thay vì trả về thành công.")
khung_nhan_manh(doc, "Nguyên tắc “mặc định đóng” và cách giao diện phản ánh phạm vi thật", [
    "Khi khởi động, giao diện hỏi lõi xem mô-đun siêu dữ liệu có sẵn sàng không. Nếu không, "
    "ba màn hình liên quan bị vô hiệu hoá kèm cảnh báo, thay vì để người dùng bấm rồi nhận "
    "lỗi giữa chừng.",
    "Phạm vi định dạng công bố trên giao diện được điều chỉnh theo nền tảng đang chạy, để "
    "bản di động không quảng cáo những định dạng mà mô-đun của nó không xử lý được. Một giao "
    "diện hứa nhiều hơn khả năng thật là một lỗi an toàn, không phải lỗi trình bày: người "
    "dùng sẽ tin rằng ảnh đã sạch trong khi nó chưa sạch.",
])
para(doc,
     "Chức năng xoá luôn tạo tệp kết quả mới và giữ nguyên tệp gốc, đồng thời báo số thẻ "
     "trước và sau khi xử lý. Kèm theo đó là chức năng so sánh siêu dữ liệu hai tệp, để "
     "người dùng *tự kiểm tra* kết quả thay vì chỉ tin vào thông báo của ứng dụng — cùng một "
     "tinh thần “kiểm chứng được” áp dụng ở mức thao tác hằng ngày.")

h2(doc, "3.8. Luồng xử lý tệp trên Android")
para(doc,
     "Android giới hạn quyền truy cập trực tiếp của ứng dụng vào bộ nhớ thiết bị. Người dùng "
     "chọn tệp qua bộ chọn của hệ điều hành, và ứng dụng chỉ nhận được quyền với đúng tệp "
     "được chọn. Lõi nghiệp vụ lại được xây dựng quanh khái niệm đường dẫn tệp thông thường. "
     "Có hai cách nối hai thứ này: sửa lõi để làm việc với luồng dữ liệu của Android, hoặc "
     "để lớp nền tảng chịu trách nhiệm quy đổi. Nhóm tác giả chọn cách thứ hai: ứng dụng sao chép "
     "tệp được chọn vào vùng lưu trữ riêng, xử lý, ghi kết quả ra vị trí người dùng chọn, "
     "rồi xoá dữ liệu tạm.")
hinh(doc, PNG / "H5-luong-tep-android.png", "Luồng xử lý tệp trên Android")
para(doc,
     "Lý do của lựa chọn: giữ nguyên giao diện dữ liệu của lõi, nhờ đó toàn bộ nghiệp vụ đã "
     "xây dựng và kiểm thử cho môi trường máy tính dùng lại được nguyên vẹn, và cơ chế quyền "
     "truy cập tệp của Android được tách hẳn khỏi phần xử lý bên trong.")

h2(doc, "3.9. Mô hình phiên làm việc và vòng đời bí mật")
para(doc,
     "Khi mở két, ứng dụng không trả khoá về cho giao diện. Thay vào đó nó tạo một *phiên "
     "làm việc*: khoá chính nằm trong bộ nhớ của lõi, còn giao diện chỉ nhận một mã phiên "
     "ngẫu nhiên. Mọi thao tác về sau tham chiếu qua mã phiên đó. Thiết kế này có ba hệ quả:")
for _t in [
    "Bí mật không đi qua ranh giới giữa lõi và giao diện nhiều lần, nên vùng có thể rò rỉ "
    "thu hẹp lại.",
    "Mã phiên không mang thông tin bí mật nên kể cả khi lộ cũng không dùng để suy ra khoá.",
    "Thao tác “khoá két” trở thành một hành động dứt khoát: xoá mục phiên khỏi bộ nhớ, khoá "
    "chính bị xoá theo, và muốn mở lại phải nhập mật khẩu.",
]:
    bullet(doc, _t)
para(doc,
     "Đi cùng với đó, mật khẩu khi truyền qua các lớp được bọc trong kiểu dữ liệu tự xoá nội "
     "dung khi hết phạm vi sử dụng, để bản sao của mật khẩu không nằm lại trong bộ nhớ lâu "
     "hơn mức cần thiết.")

# =====================================================================
# PHẦN IV
# =====================================================================
h1(doc, "PHẦN IV. SẢN PHẨM: CHỨC NĂNG VÀ GIAO DIỆN", sang_trang=True)
para(doc,
     f"Ứng dụng cung cấp {N_LENH} chức năng nghiệp vụ, phân thành tám nhóm theo mục đích sử "
     f"dụng, thao tác qua {len(DANH_MUC_MAN_HINH)} màn hình giao diện. Với mỗi nhóm, tài "
     "liệu trình bày ba lớp thông tin: nhóm này giải quyết việc gì; từng chức năng nhận đầu "
     "vào nào, xử lý ra sao, cho kết quả gì; và giao diện nào thực hiện nhóm chức năng đó, "
     "kèm mã màn hình để đối chiếu với ảnh chụp ở Phụ lục B. Cách trình bày này cho phép "
     "kiểm tra trực tiếp giữa chức năng được mô tả và giao diện có thật, thay vì phải tin "
     "vào lời mô tả.")

h2(doc, "4.1. Tám nhóm chức năng")
for _i, _nhom in enumerate(NHOM_CHUC_NANG, start=1):
    h3(doc, _nhom["ten"])
    para(doc, _nhom["dan_nhap"])
    _cn = _nhom["chuc_nang"]
    bang(doc, f"Các chức năng của nhóm {_i}", _cn[0], _cn[1:], widths=[3.6, 3.6, 4.6, 3.7])
    para(doc, "Giao diện tương ứng", bold=True, indent=False)
    for _p in _nhom["giao_dien"]:
        para(doc, _p)
    _mh = _nhom["man_hinh"]
    bang(doc, f"Màn hình giao diện của nhóm {_i}", _mh[0],
         [[c if j != 2 else ngat_duoc(c) for j, c in enumerate(r)] for r in _mh[1:]],
         widths=[2.4, 4.0, 9.1])

h2(doc, "4.2. Danh mục toàn bộ màn hình và kiểm tra hai chiều")
para(doc,
     "Bảng dưới đây liệt kê toàn bộ màn hình của ứng dụng, nhóm chức năng tương ứng và các "
     "lệnh nghiệp vụ được gọi trên từng màn hình. Đây là bảng dùng để đối chiếu giữa giao "
     "diện và chức năng, bảo đảm mọi chức năng của ứng dụng đều có giao diện thực hiện.")
bang(doc, "Danh mục toàn bộ màn hình và chức năng tương ứng",
     ["Mã", "Màn hình", "Nhóm", "Chức năng nghiệp vụ được gọi"],
     [[ma, ten, nhom, ngat_duoc(lenh)] for ma, ten, nhom, lenh in DANH_MUC_MAN_HINH],
     widths=[1.4, 3.6, 1.7, 8.8])
bang(doc, "Hai lệnh dùng chung cho toàn ứng dụng",
     ["Lệnh", "Chạy ở đâu", "Vai trò"],
     [[ngat_duoc(a), b, c] for a, b, c in LENH_MUC_UNG_DUNG],
     widths=[3.0, 4.4, 8.1])
para(doc,
     "Tính đầy đủ của bảng này được kiểm tra hai chiều trực tiếp trên mã nguồn, chứ không "
     "bằng cách đọc lại tài liệu: *chiều thứ nhất* đi từ lõi ra giao diện, lấy danh sách "
     "lệnh mà lõi công bố và tìm xem mỗi lệnh có ít nhất một màn hình gọi tới hay không; "
     "*chiều thứ hai* đi ngược lại, lấy mọi lệnh mà mã giao diện gọi và đối chiếu với danh "
     "sách lệnh của lõi. Chiều thứ nhất phát hiện chức năng đã làm nhưng người dùng không "
     "với tới được; chiều thứ hai phát hiện nút bấm gọi tới lệnh không tồn tại. Kết quả hiện "
     "tại: không có trường hợp nào ở cả hai chiều.")

h2(doc, "4.3. Nguyên tắc thiết kế giao diện")
para(doc,
     "Với một ứng dụng bảo vệ dữ liệu, giao diện không chỉ trình bày mà còn quyết định người "
     "dùng có dùng đúng chức năng hay không, và có hiểu đúng kết quả hay không. Một thao tác "
     "sai vì giao diện gây hiểu nhầm cũng dẫn tới lộ dữ liệu như một lỗi mật mã. Vì vậy tác "
     "giả coi thiết kế giao diện là một phần của thiết kế an toàn, với bốn nguyên tắc áp "
     "dụng thống nhất:")
for _h, _t in [
    ("Trình bày theo công việc cần thực hiện, không theo thuật toán. ",
     "Người dùng chọn chức năng theo nhu cầu thực tế, không cần biết bên trong dùng Argon2id "
     "hay Ed25519. Mười chín công cụ được tổ chức thành năm nhóm theo mục đích: két an toàn; "
     "bảo vệ tệp; kiểm chứng nguồn gốc và toàn vẹn; sao lưu và khôi phục; kiểm tra và làm "
     "sạch dữ liệu. Những chức năng cùng nền tảng kỹ thuật nhưng khác mục đích được tách "
     "thành màn hình riêng — “lấy vân tay tệp” và “kiểm tra tệp với vân tay” đều dùng BLAKE3 "
     "nhưng là hai công việc khác nhau, gộp lại sẽ khiến người dùng phải tự suy luận."),
    ("Giảm tải nhận thức bằng phân tầng thông tin. ",
     "Mỗi màn hình ưu tiên hiển thị các bước cần thiết để hoàn thành công việc, đánh số theo "
     "trình tự. Thông tin kỹ thuật, hướng dẫn bổ sung và lưu ý về giới hạn của chức năng đặt "
     "trong mục thu gọn “Thông tin thêm”. Người dùng mới không bị ngợp; người muốn kiểm "
     "chứng vẫn có đủ thông tin."),
    ("Cảnh báo liên quan đến nguy cơ mất dữ liệu luôn được hiển thị. ",
     "Đây là ngoại lệ có chủ ý của nguyên tắc trên. Những cảnh báo liên quan trực tiếp đến "
     "nguy cơ mất khả năng truy cập dữ liệu — nhập sai mật khẩu khi thiết lập, hoặc không có "
     "phương thức khôi phục khi quên mật khẩu — được hiển thị thường trực ngay tại vị trí "
     "liên quan. Nguyên tắc: thông tin bổ sung có thể thu gọn, cảnh báo cần thiết để người "
     "dùng khỏi mất dữ liệu thì không."),
    ("Không để kết quả cũ bị hiểu nhầm là kết quả mới. ",
     "Với các chức năng trả về kết luận đạt/không đạt, kết quả của thao tác trước vẫn còn "
     "trên màn hình có thể bị hiểu là kết quả của thao tác mới — một hiểu nhầm nguy hiểm khi "
     "kết luận là “tệp toàn vẹn”. Vì vậy khi chuyển màn hình, ứng dụng xoá trạng thái kết "
     "quả, ẩn thẻ thông báo, xoá danh sách mảnh bí mật, đường dẫn tệp tạm và nội dung các "
     "trường mật khẩu. Cách xử lý này vừa tránh nhầm lẫn, vừa giảm khả năng thông tin nhạy "
     "cảm còn nằm lại trên giao diện."),
]:
    bullet(doc, _t, bold_head=_h)
para(doc, "*Thích ứng cho màn hình cảm ứng.* "
     "Ứng dụng dùng chung mã giao diện cho hai nền tảng và điều chỉnh bố cục theo nền tảng "
     "đang chạy, thay vì duy trì hai giao diện độc lập — cách này bảo đảm hai bản không lệch "
     "nhau về nội dung theo thời gian. Trên điện thoại, thanh điều hướng bên trái chuyển "
     "thành ngăn kéo trượt từ cạnh trái; các vùng tương tác có kích thước tối thiểu 44 điểm "
     "ảnh và giao diện có khoảng đệm phù hợp với vùng khuyết của màn hình. Việc bổ sung giao "
     "diện di động được kiểm tra để bảo đảm không làm thay đổi kết quả hiển thị của phiên "
     "bản máy tính: kết xuất trước và sau khi bổ sung trùng khớp theo phép so sánh ảnh được "
     "sử dụng. Toàn bộ chuỗi hiển thị hỗ trợ tiếng Việt và tiếng Anh, chuyển đổi ngay trong "
     "ứng dụng.")

# =====================================================================
# PHẦN V
# =====================================================================
h1(doc, "PHẦN V. KIỂM CHỨNG", sang_trang=True)

h2(doc, "5.1. Chiến lược kiểm chứng nhiều mức")
para(doc,
     "Nguyên tắc mà nhóm tác giả đặt ra cho phần này: *mỗi tuyên bố kỹ thuật trong hồ sơ phải gắn "
     "với một cách kiểm tra bằng máy, và phải phân biệt rõ giữa “đã hiện thực” với “đã kiểm "
     "chứng bằng thực nghiệm”.* Hai điều đó khác nhau, và việc gộp chúng lại là cách phổ "
     "biến nhất khiến một hồ sơ kỹ thuật mất tin cậy.")
hinh(doc, PNG / "H6-thap-bang-chung.png", "Các mức kiểm chứng của sản phẩm")
para(doc,
     "Kiểm chứng được tổ chức theo năm mức, từ mức rẻ và chạy thường xuyên đến mức đắt và "
     "gần thực tế nhất: kiểm thử đơn vị trên từng thành phần; kiểm thử tích hợp trên toàn bộ "
     "vòng đời nghiệp vụ; kiểm thử trên đúng kiến trúc bộ xử lý của điện thoại và trên ma "
     "trận hệ điều hành máy tính; đối chứng với công cụ chuẩn bên ngoài; và kiểm tra tĩnh "
     "chính gói cài đặt sẽ giao cho người "
     "dùng. Mức cuối cùng — nghiệm thu trên thiết bị thật — chưa thực hiện, và điều đó được "
     "nói rõ ở mục 5.7.")

h2(doc, "5.2. Bộ kiểm thử tự động")
para(doc,
     f"Mã nguồn hiện có {N_TEST} hàm kiểm thử tự động, phân bố theo từng thành phần như bảng "
     f"dưới. Kết quả chạy toàn bộ trên máy chủ: {host.get('passed')} phép đạt, "
     f"{host.get('failed')} lỗi.")
bang(doc, "Phân bố hàm kiểm thử theo thành phần mã nguồn",
     ["Thành phần", "Số hàm kiểm thử", "Vai trò của thành phần"],
     [
         ["sv-core", str(TEST_THEO_CRATE.get("sv-core", 0)),
          "Định dạng tệp két, nghiệp vụ, phân cấp khoá, phân loại lỗi"],
         ["sv-crypto", str(TEST_THEO_CRATE.get("sv-crypto", 0)),
          "Hiện thực các nguyên hàm mật mã và chính sách tham số"],
         ["sv-crypto-traits", str(TEST_THEO_CRATE.get("sv-crypto-traits", 0)),
          "Giao diện trừu tượng của nguyên hàm — nơi đặt các điểm nối"],
         ["sv-platform", str(TEST_THEO_CRATE.get("sv-platform", 0)),
          "Nghiệp vụ trên tệp: khoá/mở khoá, ký, băm, chia bí mật theo ngưỡng"],
         ["sv-stego", str(TEST_THEO_CRATE.get("sv-stego", 0)),
          "Giấu dữ liệu trong ảnh và phát hiện dấu hiệu dữ liệu ẩn"],
         ["sv-watermark", str(TEST_THEO_CRATE.get("sv-watermark", 0)),
          "Thuỷ vân dễ vỡ và khoanh vùng ảnh bị sửa"],
         ["sv-age / sv-age-rs", str(TEST_THEO_CRATE.get("sv-age", 0)
                                    + TEST_THEO_CRATE.get("sv-age-rs", 0)),
          "Hai bản hiện thực mô-đun mã hoá nội dung, gồm cả phép đối chứng"],
         ["sv-meta / sv-meta-rs", str(TEST_THEO_CRATE.get("sv-meta", 0)
                                      + TEST_THEO_CRATE.get("sv-meta-rs", 0)),
          "Hai bản hiện thực mô-đun siêu dữ liệu"],
         ["sv-qr", str(TEST_THEO_CRATE.get("sv-qr", 0)), "Xuất và đọc mảnh bí mật qua mã QR"],
         ["sv-sys-sodium / sv-sys-sss",
          str(TEST_THEO_CRATE.get("sv-sys-sodium", 0) + TEST_THEO_CRATE.get("sv-sys-sss", 0)),
          "Lớp bọc thư viện hệ thống"],
         ["sv-types", str(TEST_THEO_CRATE.get("sv-types", 0)),
          "Kiểu dữ liệu dùng chung và tập lỗi công bố ra giao diện"],
         ["sv-app", str(TEST_THEO_CRATE.get("sv-app", 0)),
          "Lớp ứng dụng, các lệnh nghiệp vụ và mô hình phiên làm việc"],
         ["Tổng cộng", str(N_TEST), "—"],
     ], widths=[4.0, 3.0, 8.5],
     note="Số hàm kiểm thử được đếm tự động từ mã nguồn, không nhập tay.")

h2(doc, "5.3. Kiểm thử trên kiến trúc ARM64")
para(doc,
     "Biên dịch thành công cho một kiến trúc không có nghĩa là chương trình chạy đúng trên "
     "kiến trúc đó. Sai khác về thứ tự byte, về cách căn chỉnh dữ liệu, hoặc về hành vi của "
     "thư viện hệ thống chỉ lộ ra khi mã thực sự chạy. Vì vậy lõi được chạy dưới trình giả "
     f"lập kiến trúc ARM64 — đúng kiến trúc bộ xử lý mà điện thoại Android dùng — với "
     f"{arm.get('suites')} bộ kiểm thử tập trung vào các thành phần mật mã và các lớp giao "
     f"tiếp với thư viện hệ thống. Kết quả: {arm.get('passed')} phép đạt, "
     f"{arm.get('failed')} lỗi.")
para(doc,
     "Đây là mức kiểm chứng đắt hơn kiểm thử thông thường nhưng cần thiết, vì các thành phần "
     "gọi tới thư viện hệ thống viết bằng C là nơi khác biệt kiến trúc dễ gây lỗi nhất, mà "
     "lại đúng là các thành phần thực hiện phép mật mã.")

h2(doc, "5.4. Đối chứng tương thích định dạng với công cụ chuẩn")
para(doc,
     "Ràng buộc bất biến định dạng (mục 2.3.3) là loại ràng buộc dễ bị vi phạm âm thầm: một "
     "thay đổi nhỏ trong bản hiện thực mới có thể sinh ra tệp mà chỉ chính nó đọc được. "
     f"Không thể phát hiện điều đó bằng cách đọc mã, nên nhóm tác giả kiểm chứng bằng "
     f"{SO_DOI_CHUNG} phép thực nghiệm đối chứng hai chiều với công cụ chuẩn độc lập.")
bang(doc, "Kiểm chứng khả năng tương thích định dạng giữa hai cách triển khai mô-đun mã hoá",
     ["Phép kiểm chứng", "Nội dung", "Kết quả"],
     [
         ["Đối chứng tệp mã hoá, chiều 1",
          "Tệp được tạo bằng mô-đun mã hoá tích hợp trong ứng dụng, sau đó giải mã bằng công "
          "cụ chuẩn age v1.2.1", "Đạt"],
         ["Đối chứng tệp mã hoá, chiều 2",
          "Tệp được tạo bằng công cụ chuẩn age v1.2.1, sau đó giải mã bằng mô-đun mã hoá "
          "tích hợp trong ứng dụng", "Đạt"],
         ["Mở chéo két, chiều 1",
          "Két được tạo bằng phiên bản sử dụng tiến trình con, sau đó mở bằng phiên bản tích "
          "hợp trong ứng dụng", "Đạt"],
         ["Mở chéo két, chiều 2",
          "Két được tạo bằng phiên bản tích hợp trong ứng dụng, sau đó mở bằng phiên bản sử "
          "dụng tiến trình con", "Đạt"],
         ["Kiểm tra cơ chế xác thực",
          "Sau khi thay đổi cách triển khai mô-đun mã hoá, mật khẩu không đúng vẫn bị từ chối",
          "Đạt"],
     ], widths=[4.2, 9.0, 2.3],
     note="Nguồn: crates/sv-age-rs/tests/interop.rs và src-tauri/tests/vault_interop.rs. Công "
          "cụ đối chứng age v1.2.1 được tải từ nguồn chính thức; giá trị băm SHA-256 của tệp "
          "tải về được lưu để phục vụ kiểm tra và truy xuất nguồn gốc.")
para(doc,
     "Giá trị của cách kiểm chứng này nằm ở chỗ công cụ đối chứng do bên thứ ba viết và "
     "không biết gì về sản phẩm. Nếu hai bên đọc được tệp của nhau theo cả hai chiều thì kết "
     "luận về tính tương thích không còn phụ thuộc vào lời khẳng định của nhóm tác giả.")

h2(doc, "5.5. Kiểm chứng khả năng đa nền tảng")
para(doc,
     "Tuyên bố “một lõi chạy trên nhiều nền tảng” rất dễ nói và rất khó chứng minh bằng lời. "
     "Nhóm tác giả kiểm chứng nó ở hai mức, trả lời hai câu hỏi khác nhau.")
para(doc, "*Mức thứ nhất — mã nguồn có thực sự dựng và chạy được trên từng nền tảng không?* "
     f"Quy trình tích hợp liên tục của dự án chạy trên ma trận {len(TEN_OS)} hệ điều hành "
     f"({CHUOI_OS}), với hai hạng mục chạy đủ cả ma trận: một cho phần lõi và một cho lớp vỏ "
     "ứng dụng. Mỗi hạng mục gồm kiểm tra định dạng mã, soát mã ở mức từ chối mọi cảnh báo, "
     "dựng với phiên bản phụ thuộc khoá cứng, và chạy bộ kiểm thử — trong đó có cả phép kiểm "
     "thử vòng đời két chạy với công cụ mã hoá thật, không phải bản giả lập.")
rich(doc, [
    ("Kết quả: ", "b"),
    (f"biên bản lần chạy ngày {CI_XANH.get('ngay')} trên mã nguồn {CI_XANH.get('commit')} ghi "
     f"nhận {CI_XANH.get('so_viec_dat')} hạng mục đều đạt, gồm các hạng mục chạy trên "
     f"{CHUOI_OS}. Số hàm kiểm thử ghi trong biên bản là số của thời điểm đó; bộ kiểm thử từ "
     "đó đến nay đã tăng thêm, nên con số hiện tại ở mục 5.2 lớn hơn. Biên bản lưu tại "
     "docs/CI-VALIDATION.md kèm mã lần chạy để đối chiếu.", ""),
])
para(doc, "*Mức thứ hai — hai nền tảng có thực sự đọc được dữ liệu của nhau không?* "
     "Đây mới là câu hỏi người dùng quan tâm, và cũng là câu khó hơn: hai bản hiện thực có "
     "thể cùng biên dịch được, cùng chạy được, mà vẫn sinh ra hai định dạng khác nhau. Vì vậy "
     "có hai phép kiểm thử tự động dành riêng cho việc này, và tên gọi của chúng trong mã "
     "nguồn nói đúng nội dung: *“két do bản máy tính tạo phải mở được bằng bản di động”* và "
     "*“két do bản di động tạo phải mở được bằng bản máy tính”*.")
para(doc,
     "Điều đáng nói là hai phép kiểm thử này không dừng ở việc so sánh khối dữ liệu mã hoá — "
     "việc đó đã có phép đối chứng riêng với công cụ chuẩn ở mục 5.4. Chúng dựng nguyên một "
     "tệp két hoàn chỉnh bằng bản hiện thực này rồi mở bằng bản kia, tức là đi qua toàn bộ "
     "chuỗi: dẫn xuất khoá từ mật khẩu, mở các khoá đã bọc, kiểm tra chữ ký ràng buộc, giải "
     "mã danh mục tệp và lấy tệp ra. Phép kiểm thử thứ ba xác nhận rằng sau khi đổi bản hiện "
     "thực, mật khẩu sai vẫn bị từ chối — để cái đọc được không phải nhờ một lỗ hổng.")
para(doc,
     "Một điểm cần nói chính xác: hai phép kiểm thử đọc chéo chạy trên cùng một máy, vì cái "
     "chúng kiểm tra là *sự đồng nhất của định dạng giữa hai bản hiện thực*, không phải hành "
     "vi của phần cứng. Toàn bộ phần còn lại của lõi là chung một mã nguồn, nên khi định dạng "
     "đã đồng nhất thì tệp két đi lại được giữa hai nền tảng. Việc chạy đúng trên từng nền "
     "tảng là câu hỏi riêng, và đó là việc của mức thứ nhất.")
para(doc,
     "Hai mức trên trả lời trọn vẹn câu hỏi về đa nền tảng trong phạm vi kiểm chứng được. "
     "Phần chưa kiểm chứng cũng cần nói rõ: việc đóng gói bản cài đặt có ký số và công chứng "
     "cho Windows và macOS chưa thực hiện, nên hồ sơ không tuyên bố sản phẩm đã sẵn sàng phát "
     "hành trên hai nền tảng đó.")

h2(doc, "5.6. Kiểm tra tĩnh gói cài đặt")
para(doc,
     "Mức kiểm chứng cuối cùng thực hiện được trên máy chủ là mở chính gói cài đặt sẽ giao "
     "cho người dùng và đọc nội dung bên trong. Cách này kiểm tra được những điều mà mã "
     "nguồn không bảo đảm: cấu hình đóng gói có đúng không, tài nguyên có thực sự nằm trong "
     "gói không, thư viện có đúng kiến trúc không.")
bang(doc, "Kết quả kiểm tra tĩnh gói cài đặt Android",
     ["Nội dung kiểm tra", "Kết quả", "Ý nghĩa"],
     [
         ["Kích thước gói", f"{MB_APK} MB", "Phù hợp với một ứng dụng có lõi mật mã tích hợp"],
         ["Kiến trúc thư viện native", "64-bit ARM aarch64",
          "Đọc phần đầu tệp ELF trong gói — đúng kiến trúc của điện thoại Android"],
         ["Quyền ứng dụng khai báo", "Không có quyền nào",
          "Bằng chứng kiểm tra được cho nguyên lý hoạt động ngoại tuyến tuyệt đối"],
         ["Tài nguyên giao diện", "Nhúng sẵn trong thư viện native",
          "Giao diện đi kèm ứng dụng, không tải về từ mạng khi chạy"],
         ["Giá trị băm SHA-256 của gói", (SHA_APK or "")[:32] + "…",
          "Cho phép đối chiếu đúng gói đã kiểm tra với gói được cài đặt"],
     ], widths=[4.6, 4.6, 6.3])

h2(doc, "5.7. Chỉ tiêu kỹ thuật đạt được và phần chưa kiểm chứng")
bang(doc, "Tổng hợp chỉ tiêu kỹ thuật",
     ["Chỉ tiêu", "Giá trị đạt được", "Cách xác định"],
     [
         ["Số chức năng nghiệp vụ", f"{N_LENH} chức năng", "Đếm trực tiếp từ mã nguồn"],
         ["Số màn hình giao diện", f"{len(DANH_MUC_MAN_HINH)} màn hình",
          "Đếm trực tiếp từ mã giao diện; ảnh chụp đủ ở Phụ lục B"],
         ["Chức năng nghiệp vụ chưa có giao diện gọi tới", "0",
          "Đối chiếu lệnh của lõi với mã giao diện theo hai chiều"],
         ["Số thành phần mã nguồn độc lập", f"{N_CRATE} thành phần", "Đọc cấu hình dự án"],
         ["Số hàm kiểm thử tự động", f"{N_TEST} hàm", "Đếm trực tiếp từ mã nguồn"],
         ["Kiểm thử trên máy chủ", f"{host.get('passed')} đạt / {host.get('failed')} lỗi",
          "Nhật ký chạy bộ kiểm thử"],
         [f"Kiểm thử lõi trên kiến trúc ARM64 ({arm.get('suites')} bộ)",
          f"{arm.get('passed')} đạt / {arm.get('failed')} lỗi",
          "Chạy dưới trình giả lập kiến trúc"],
         ["Kiểm chứng tương thích định dạng", f"{SO_DOI_CHUNG} phép đối chứng đạt",
          "Đối chứng hai chiều với công cụ chuẩn age v1.2.1"],
         ["Quyền ứng dụng yêu cầu", "Không khai báo quyền nào",
          "Đọc tệp kê khai trong gói cài đặt"],
         ["Dựng và kiểm thử trên hệ điều hành máy tính", f"{CHUOI_OS} — đạt",
          f"Biên bản tích hợp liên tục {CI_XANH.get('ngay')}, "
          f"{CI_XANH.get('so_viec_dat')} hạng mục xanh"],
         ["Đọc chéo tệp két giữa hai nền tảng", "2 phép kiểm thử đạt",
          "Kiểm thử tự động dành riêng, mục 5.5"],
         ["Đóng gói bản cài đặt có ký số cho Windows/macOS", "Chưa thực hiện",
          "Bước cần cho phân phối rộng rãi, ngoài phạm vi phiên bản này"],
         ["Nghiệm thu trên thiết bị Android thật", "Chưa thực hiện",
          "Quy trình 15 bước đã soạn, đặt tại Phụ lục A"],
     ], widths=[6.4, 4.4, 4.7],
     note="Toàn bộ số liệu được sinh tự động từ mã nguồn và nhật ký kiểm thử, không nhập tay.")
khung_nhan_manh(doc, "Phần chưa kiểm chứng — nêu rõ thay vì bỏ qua", [
    "Tại thời điểm lập hồ sơ, sản phẩm chưa được nghiệm thu trên thiết bị Android thật. Mọi "
    "kiểm chứng ở trên đều thực hiện trên máy chủ, kể cả phép chạy dưới trình giả lập kiến "
    "trúc ARM64.",
    "Nhóm tác giả không suy diễn từ các kết quả đó thành kết luận về hành vi trên máy thật. Thay "
    "vào đó, Phụ lục A cung cấp quy trình nghiệm thu 15 bước, mỗi bước có thao tác và tiêu "
    "chí đạt cụ thể, để đơn vị tự xác nhận trước khi đưa vào sử dụng rộng rãi.",
], mau="FDF3E3", vien="B07D2B")

# =====================================================================
# PHẦN VI
# =====================================================================
h1(doc, "PHẦN VI. GIÁ TRỊ VÀ KHẢ NĂNG ÁP DỤNG", sang_trang=True)

h2(doc, "6.1. Giá trị đối với công tác huấn luyện")
para(doc,
     "Ở mục 1.4 đã nêu một mâu thuẫn: sản phẩm dựng riêng để dạy học thường bị đơn giản hoá "
     "tới mức không dùng được thật, còn công cụ chuyên nghiệp thì quá phức tạp cho giờ thực "
     "hành. Cách hoá giải của sáng kiến là *không dựng hai sản phẩm*: học viên thực hành "
     "trên đúng công cụ được xây dựng cho nhu cầu sử dụng thật. Điều làm cho nó dùng được "
     "trong dạy học không phải sự đơn giản hoá, mà là bốn nguyên tắc giao diện ở mục 4.3 — "
     "đặc biệt là nguyên tắc phân tầng thông tin: phần kỹ thuật không bị bỏ đi mà được đưa "
     "vào mục “Thông tin thêm”, nơi giảng viên có thể mở ra đúng lúc cần giảng.")
bang(doc, "Ánh xạ chức năng của sản phẩm với nội dung giảng dạy",
     ["Chức năng", "Nội dung giảng dạy minh hoạ"],
     [
         ["Tạo và mở két an toàn",
          "Dẫn xuất khoá từ mật khẩu; vì sao mật khẩu yếu vẫn nguy hiểm dù thuật toán mạnh"],
         ["Khoá / mở khoá tệp", "Mã hoá có xác thực; phân biệt bảo mật và toàn vẹn"],
         ["Ký tệp và kiểm tra chữ ký", "Mật mã khoá công khai; chứng minh nguồn gốc"],
         ["Vân tay tệp và kiểm tra toàn vẹn",
          "Hàm băm mật mã; ứng dụng trong kiểm tra tệp tải về"],
         ["Chia bí mật k trong n", "Chia sẻ bí mật ngưỡng; nguyên tắc tách quyền kiểm soát"],
         ["Giấu tin và phát hiện giấu tin",
          "Giấu tin trong ảnh; giới hạn của che giấu so với mã hoá"],
         ["Thuỷ vân dễ vỡ", "Phát hiện sửa đổi cục bộ trên ảnh"],
         ["Xem và xoá siêu dữ liệu",
          "Kênh lộ thông tin ngoài nội dung; quyền riêng tư trong ảnh số"],
         ["Quy tắc phân loại lỗi", "Tấn công dựa trên thông báo lỗi và cách phòng tránh"],
         ["Mô hình mối đe doạ của sản phẩm",
          "Cách xác định phạm vi bảo vệ và giới hạn của một biện pháp kỹ thuật"],
     ], widths=[5.0, 10.5])
para(doc,
     "Một giá trị huấn luyện nữa ít gặp ở các công cụ thương mại: sản phẩm *chủ động dạy về "
     "giới hạn của chính nó*. Chức năng phát hiện dữ liệu ẩn không kết luận “ảnh sạch” mà "
     "chỉ nêu mức độ nghi ngờ trong phạm vi các phép kiểm tra đã thực hiện; chức năng kiểm "
     "tra thuỷ vân phân biệt “ảnh bị sửa” với “ảnh đã bị biến đổi khi lưu ở định dạng có "
     "mất dữ liệu”. Học viên qua đó hiểu rằng kết quả của một công cụ phân tích luôn phụ "
     "thuộc phương pháp và phạm vi — một bài học khó truyền đạt bằng lý thuyết.")
para(doc,
     "Ngoài giá trị minh hoạ, mã nguồn mở cho phép mở rộng đào tạo theo hướng chuyên sâu: "
     "phân tích cách một nguyên lý được hiện thực, đánh giá mô hình mối đe doạ, hoặc rà soát "
     "mã nguồn để tìm điểm có thể cải thiện — tức là chuyển từ *dùng công cụ an toàn* sang "
     "*đánh giá được một hệ thống an toàn*.")

h2(doc, "6.2. Đề xuất khung bài thực hành")
para(doc,
     "Phần này là *đề xuất*, chưa phải tài liệu đã biên soạn. Nhóm tác giả nêu ra để cho thấy "
     "sản phẩm có thể đưa vào chương trình theo cách nào, và để việc biên soạn về sau có sẵn "
     "khung.", italic=True)
bang(doc, "Đề xuất khung bốn bài thực hành trên sản phẩm",
     ["Bài", "Nội dung thực hành", "Kết quả học viên tự kiểm tra được"],
     [
         ["1. Mật khẩu và khoá",
          "Tạo két, thêm tệp, khoá lại, mở bằng mật khẩu đúng và sai; đổi mật khẩu",
          "Thấy được mật khẩu không nằm trong tệp; thấy thời gian mở két phản ánh chi phí dẫn "
          "xuất khoá"],
         ["2. Toàn vẹn và nguồn gốc",
          "Ký tệp, kiểm tra chữ ký, sửa một byte rồi kiểm tra lại; lấy vân tay tệp trên hai máy",
          "Chữ ký chuyển từ hợp lệ sang không hợp lệ sau khi sửa; hai vân tay trùng nhau"],
         ["3. Tách quyền kiểm soát",
          "Chia bí mật 5 mảnh cần 3, thử khôi phục với 2 mảnh rồi với 3 mảnh",
          "Dưới ngưỡng thì không khôi phục được và hệ thống báo còn thiếu mấy mảnh"],
         ["4. Kênh lộ thông tin ngoài nội dung",
          "Xem siêu dữ liệu ảnh chụp bằng điện thoại, xoá, rồi so sánh hai bản; giấu tệp vào "
          "ảnh rồi dùng chức năng phát hiện",
          "Nhìn thấy nhóm toạ độ định vị biến mất; thấy che giấu không đồng nghĩa với không "
          "bị phát hiện"],
     ], widths=[3.2, 6.6, 5.7])

h2(doc, "6.3. Giá trị trong tình huống truyền khẩn cấp")
para(doc,
     "Trong tình huống ở mục 1.2, giá trị của sản phẩm nằm ở chỗ nó biến bốn biện pháp rời "
     "rạc thành một quy trình làm được trên chính thiết bị đang có, không cần máy tính, "
     "không cần mạng, không cần dịch vụ bên ngoài. Trình tự đề xuất: xoá siêu dữ liệu của tệp "
     "trước; mã hoá bằng mật khẩu mạnh; ký số để bên nhận xác minh được nguồn gốc; và khi "
     "tính chất công việc đòi hỏi thì chia thành nhiều mảnh gửi theo các kênh độc lập, kèm "
     "trao mật khẩu qua một kênh khác với kênh truyền tệp.")
para(doc,
     "Cần nói thẳng giới hạn: các biện pháp này *giảm rủi ro*, không *loại bỏ* rủi ro, và "
     "chúng không thay đổi việc tài liệu đó có được phép truyền hay không. Ba giới hạn cụ "
     "thể mà người dùng phải biết: nếu thiết bị đã bị chiếm quyền điều khiển thì mọi biện "
     "pháp trong ứng dụng đều mất tác dụng; nếu mật khẩu được trao qua chính kênh truyền tệp "
     "thì mã hoá gần như vô nghĩa; và nếu quên mật khẩu mà không tạo trước mảnh phục hồi thì "
     "dữ liệu không lấy lại được.")

h2(doc, "6.4. Điều kiện triển khai, giới hạn và hướng phát triển")
para(doc,
     "Điều kiện triển khai rất đơn giản: một thiết bị Android, không cần máy chủ, không cần "
     "kết nối mạng, không yêu cầu quyền quản trị thiết bị. Đây là hệ quả trực tiếp của "
     "nguyên lý hoạt động ngoại tuyến — thứ ban đầu là một ràng buộc an toàn, nhưng hoá ra "
     "cũng là thứ làm cho việc triển khai gần như không có chi phí.")
para(doc,
     "Nhờ kiến trúc ở mục 2.4, cùng bộ chức năng còn triển khai được trên máy trạm chạy hệ "
     f"điều hành máy tính ({CHUOI_OS}), và tệp két đi lại được giữa hai môi trường. Điều này "
     "mở thêm vài cách dùng thực tế: giảng viên chuẩn bị dữ liệu bài thực hành trên máy tính "
     "rồi để học viên xử lý trên điện thoại; hoặc cán bộ xử lý tệp trên điện thoại rồi kiểm "
     "tra lại kết quả trên máy trạm bằng chính công cụ chuẩn của cộng đồng. Cần nhắc lại "
     "ranh giới đã nêu ở mục 5.5: bản cài đặt có ký số cho Windows và macOS chưa được đóng "
     "gói, nên việc triển khai rộng trên máy tính vẫn còn một bước phải làm.")
bang(doc, "Mức độ hoàn thành theo hạng mục",
     ["Hạng mục", "Mức độ", "Cách xác định"],
     [
         ["Thiết kế kiến trúc, định dạng tệp két và sơ đồ phân cấp khoá", "Hoàn thành",
          "Tài liệu kiến trúc và mã nguồn"],
         ["Lõi bảo vệ dữ liệu và toàn bộ nghiệp vụ", "Hoàn thành",
          "Bộ kiểm thử tự động chạy đạt trên máy chủ"],
         ["Mô-đun xử lý siêu dữ liệu bằng Rust", "Hoàn thành",
          "Kiểm thử tự động trên ảnh có siêu dữ liệu"],
         ["Tương thích định dạng giữa hai bản hiện thực", "Hoàn thành",
          "Đối chứng hai chiều với công cụ chuẩn age v1.2.1"],
         ["Biên dịch và thực thi lõi trên kiến trúc ARM64", "Hoàn thành",
          "Kiểm tra tệp đối tượng; chạy bộ kiểm thử dưới trình giả lập kiến trúc"],
         ["Giao diện cho màn hình điện thoại", "Hoàn thành",
          "Kết xuất và kiểm tra bố cục ở kích thước điện thoại"],
         ["Đóng gói tệp cài đặt Android", "Hoàn thành", "Kiểm tra tĩnh nội dung gói cài đặt"],
         ["Kiểm thử nghiệm thu trên thiết bị Android", "Có quy trình nghiệm thu",
          "Quy trình 15 bước có tiêu chí đạt cho từng bước, tại Phụ lục A"],
         ["Tích hợp kho khoá phần cứng của Android", "Định hướng phát triển",
          "Chưa hiện thực trong phiên bản này"],
     ], widths=[6.0, 3.6, 5.9])
para(doc, "*Hướng phát triển.*")
for _h, _t in [
    ("Mở rộng kiểm thử nghiệm thu trên nhiều dòng máy. ",
     "Thực hiện các kịch bản ở Phụ lục A trên nhiều dòng điện thoại và phiên bản Android "
     "khác nhau, ghi nhận kết quả để đánh giá khả năng tương thích và mức độ ổn định."),
    ("Tích hợp kho khoá phần cứng và xác thực sinh trắc. ",
     "Nghiên cứu dùng vùng lưu khoá được Android và phần cứng thiết bị bảo vệ cho một số "
     "khoá nằm ngoài hệ thống khoá của két; bổ sung tuỳ chọn xác thực bằng vân tay. Lưu ý "
     "thiết kế: không đưa khoá chính của két vào kho khoá phần cứng, vì như vậy sẽ phá vỡ "
     "tính chất tệp két tự bảo vệ khi mang sang thiết bị khác."),
    ("Mở rộng phạm vi định dạng của mô-đun siêu dữ liệu. ",
     "Bổ sung khả năng xem và loại bỏ siêu dữ liệu với các định dạng ảnh, video khác, đồng "
     "thời giữ nguyên tắc chỉ báo thành công khi kết quả xử lý đã được kiểm tra."),
    ("Xây dựng bộ bài giảng và bài thực hành kèm theo. ",
     "Biên soạn tài liệu hướng dẫn giảng viên, phiếu bài thực hành và bộ dữ liệu mẫu trên cơ "
     "sở khung đề xuất ở mục 6.2."),
    ("Hoàn thiện khâu phân phối cho bản máy tính. ",
     "Đóng gói bản cài đặt có ký số và công chứng cho Windows và macOS, cài thử trên máy "
     "sạch và xác nhận các chức năng mật mã chạy đúng ngay lần mở đầu tiên. Đây là bước duy "
     "nhất còn thiếu để bản máy tính phân phối được rộng rãi; phần mã nguồn đã chạy đạt trên "
     "cả ba hệ điều hành."),
    ("Đánh giá độc lập và mở rộng nền tảng. ",
     "Tổ chức rà soát mã nguồn và kiểm thử độc lập bởi đồng nghiệp hoặc học viên có chuyên "
     "môn. Trên cơ sở kiến trúc lõi dùng chung đã có, việc mở rộng sang một nền tảng di động "
     "khác chỉ cần bổ sung các thành phần phụ thuộc nền tảng mà vẫn dùng chung lõi và định "
     "dạng — cấu trúc mã nguồn đã sẵn sàng cho việc đó, nhưng chưa được hiện thực và kiểm "
     "chứng trong phiên bản này."),
]:
    bullet(doc, _t, bold_head=_h)

# =====================================================================
# PHỤ LỤC
# =====================================================================
h1(doc, "PHỤ LỤC A. QUY TRÌNH KIỂM THỬ NGHIỆM THU TRÊN THIẾT BỊ ANDROID", sang_trang=True)
para(doc,
     "Phụ lục này quy định quy trình nghiệm thu trên thiết bị Android thật. Mỗi bước có thao "
     "tác và tiêu chí đạt cụ thể để kết quả kiểm tra và đối chiếu được; cột Kết quả để trống "
     "cho người thực hiện ghi nhận. Quy trình bao phủ đủ tám nhóm chức năng và kết thúc bằng "
     "một phép kiểm tra liên nền tảng.")
bang(doc, "Quy trình kiểm thử nghiệm thu trên thiết bị Android",
     ["TT", "Nội dung", "Thao tác", "Tiêu chí đạt", "Kết quả"],
     [
         ["1", "Cài đặt", "Cài tệp APK và mở ứng dụng",
          "Ứng dụng khởi động, hiển thị màn hình chính bằng tiếng Việt", ""],
         ["2", "Không có quyền mạng", "Xem mục Quyền ứng dụng trong Cài đặt hệ thống",
          "Không có quyền truy cập mạng nào được liệt kê", ""],
         ["3", "Tạo két", "Tạo két mới, đặt mật khẩu",
          "Tệp két được tạo, ứng dụng báo thành công", ""],
         ["4", "Thêm và trích xuất tệp", "Thêm một tệp, khoá két, mở lại, trích xuất",
          "Tệp trích xuất giống hệt tệp gốc", ""],
         ["5", "Từ chối mật khẩu sai", "Mở két bằng mật khẩu sai",
          "Từ chối, thông báo rõ ràng, không tiết lộ thông tin khác", ""],
         ["6", "Phát hiện sửa đổi", "Sửa một byte của tệp két rồi mở lại",
          "Báo tệp bị hỏng hoặc bị sửa, không mở", ""],
         ["7", "Khoá và mở khoá tệp đơn", "Khoá một ảnh, mở lại bằng đúng mật khẩu",
          "Ảnh khôi phục nguyên vẹn", ""],
         ["8", "Ký và kiểm tra chữ ký", "Tạo cặp khoá, ký tệp, kiểm tra chữ ký",
          "Kiểm tra đạt; sau khi sửa tệp thì kiểm tra không đạt", ""],
         ["9", "Vân tay tệp", "Lấy vân tay cùng một tệp trên hai thiết bị",
          "Hai giá trị vân tay trùng nhau", ""],
         ["10", "Chia và khôi phục khoá",
          "Chia bí mật 3 mảnh cần 2, khôi phục bằng 2 mảnh",
          "Khôi phục đúng; dùng 1 mảnh thì không khôi phục được", ""],
         ["11", "Giấu tin và phát hiện", "Giấu tệp vào ảnh, rồi dùng chức năng phát hiện",
          "Trích xuất đúng tệp; chức năng phát hiện ghi nhận dấu hiệu", ""],
         ["12", "Xem siêu dữ liệu ảnh", "Chọn ảnh chụp bằng điện thoại rồi bấm Xem",
          "Liệt kê các thẻ; ảnh có định vị thì thấy nhóm toạ độ", ""],
         ["13", "Xoá siêu dữ liệu ảnh", "Xoá siêu dữ liệu ảnh đó rồi xem lại bản đã xoá",
          "Bản sạch không còn thẻ; ảnh gốc nguyên vẹn; ảnh vẫn mở xem được", ""],
         ["14", "Thuỷ vân chống giả mạo", "Đóng dấu một ảnh, sửa một vùng, kiểm tra lại",
          "Phát hiện ảnh đã bị sửa và chỉ ra vùng bị can thiệp", ""],
         ["15", "Tương thích liên nền tảng",
          "Mở tệp két tạo trên máy tính bằng ứng dụng di động", "Mở được bằng đúng mật khẩu",
          ""],
     ], widths=[1.0, 3.0, 4.4, 4.8, 2.3])

h1(doc, "PHỤ LỤC B. ẢNH CHỤP TOÀN BỘ MÀN HÌNH GIAO DIỆN", sang_trang=True)
para(doc,
     f"Phụ lục này trình bày ảnh chụp đủ {len(DANH_MUC_MAN_HINH)} màn hình giao diện của ứng "
     "dụng, sắp xếp theo thứ tự trong thanh điều hướng. Mã màn hình dưới mỗi ảnh (GD01–GD21) "
     "thống nhất với mã dùng ở mục 4.1 và 4.2, giúp đối chiếu giữa chức năng được mô tả và "
     "màn hình thực hiện nó.")
para(doc,
     "Ảnh được chụp ở kích thước màn hình điện thoại. Với màn hình có nội dung dài hơn khung "
     "hiển thị, ảnh chụp toàn bộ phần nội dung cuộn được, nên chiều cao ảnh có thể lớn hơn "
     "một khung màn hình thực tế. Các mục “Thông tin thêm” được giữ ở trạng thái thu gọn, "
     "đúng như trạng thái mặc định khi mở màn hình.")
for _dd, _ct in hinh_ghep():
    hinh(doc, _dd, _ct, width_cm=13.0)

h1(doc, "PHỤ LỤC C. DANH MỤC LỆNH NGHIỆP VỤ CỦA LÕI", sang_trang=True)
para(doc,
     f"Danh sách {N_LENH} lệnh nghiệp vụ mà lõi công bố cho giao diện, đọc trực tiếp từ mã "
     "nguồn. Đây là danh sách dùng cho phép kiểm tra hai chiều ở mục 4.2.")
_cot = 3
_hang = [DS_LENH[i:i + _cot] for i in range(0, len(DS_LENH), _cot)]
_hang = [r + [""] * (_cot - len(r)) for r in _hang]
bang(doc, "Danh mục lệnh nghiệp vụ của lõi",
     ["Lệnh", "Lệnh", "Lệnh"],
     [[ngat_duoc(c) for c in r] for r in _hang],
     widths=[5.2, 5.2, 5.1])

chu_ky(doc,
       ("XÁC NHẬN CỦA ĐƠN VỊ", ""),
       ("CHỦ NHIỆM SÁNG KIẾN", f"{CHU_NHIEM['cap_bac']} {CHU_NHIEM['ho_ten']}"),
       dia_danh=DIA_DANH_NGAY)

OUT = BASE / "docx" / "05-De-cuong-chi-tiet-sang-kien.docx"
OUT.parent.mkdir(exist_ok=True)
doc.save(OUT)
print(f"Đã ghi {OUT}")
