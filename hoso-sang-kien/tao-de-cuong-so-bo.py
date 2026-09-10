#!/usr/bin/env python3
"""Sinh văn bản ĐỀ CƯƠNG SƠ BỘ VỀ SÁNG KIẾN (DOCX).

Vị trí trong bộ hồ sơ. Ba văn bản nội dung xếp theo độ sâu tăng dần và mỗi văn bản trả lời
một câu hỏi khác nhau:

    02 Thuyết minh      — *sáng kiến này là gì và đáng giá ở đâu?*   (dưới 20 trang)
    04 Đề cương sơ bộ   — *định làm gì, làm theo cách nào, lấy gì    (khoảng 20 trang)
                           để chứng minh là đã làm được?*
    05 Đề cương chi tiết— *đã làm như thế nào, ở mức từng cơ chế?*   (khoảng 60 trang)

Đề cương sơ bộ *không phải* bản rút gọn của Đề cương chi tiết. Nó là tài liệu của giai đoạn
đặt vấn đề: nêu lý do, mục tiêu, phạm vi, cách tiếp cận, khối lượng công việc, phương pháp
kiểm chứng, sản phẩm dự kiến, tiến trình và rủi ro — tức là *kế hoạch* và *căn cứ của kế
hoạch*. Vì hồ sơ nộp khi công việc đã hoàn thành, mỗi phần kế hoạch đều kèm cột hoặc đoạn
đối chiếu với kết quả thực tế, để người đọc thấy được điều gì đã làm đúng dự kiến và điều gì
chưa.

Số liệu dùng chung với các văn bản khác qua du_lieu_ho_so.py; không có con số nào nhập tay.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from dinh_dang import (  # noqa: E402
    bang, bullet, chu_ky, danh_so_trang, dat_lai_dem, h1, h2, hinh, khung_nhan_manh,
    muc_luc, new_document, para, tieuDeChinh, tieu_de_quan_doi, trang_bia,
)
from du_lieu_ho_so import (  # noqa: E402
    A2, CHUOI_OS, CI_XANH, GIT, MB_APK, N_CRATE, N_LENH, N_TEST, SO_DOI_CHUNG, TT,
    arm, host,
)
from noi_dung_chuc_nang import NHOM_CHUC_NANG  # noqa: E402
from noi_dung_giao_dien import DANH_MUC_MAN_HINH  # noqa: E402
from ten_sang_kien import (  # noqa: E402
    CHU_NHIEM, DIA_DANH_NGAY, TEN_SANG_KIEN, TEN_SANG_KIEN_HOA, TEN_SP,
)

BASE = pathlib.Path(__file__).parent
PNG = BASE / "hinh-anh" / "png"

doc = new_document(gian_dong=1.3, cach_doan=5)
dat_lai_dem()
danh_so_trang(doc)

trang_bia(doc, TEN_SANG_KIEN_HOA, nhan="ĐỀ CƯƠNG SƠ BỘ VỀ SÁNG KIẾN")
tieu_de_quan_doi(doc)
tieuDeChinh(doc, "ĐỀ CƯƠNG SƠ BỘ VỀ SÁNG KIẾN")
para(doc, TEN_SANG_KIEN, bold=True, align=1, indent=False)

para(doc,
     "*Về tên gọi và trọng tâm.* Tên sáng kiến nói “đa nền tảng” vì sản phẩm dùng chung một "
     "lõi nghiệp vụ và một định dạng dữ liệu cho cả bản trên máy tính lẫn bản trên thiết bị "
     "di động. Trọng tâm của sáng kiến vẫn là *bản di động* — nơi tồn tại rào cản kỹ thuật "
     "mà giải pháp phải giải quyết (Phần I mục 4); bản máy tính giữ vai trò đối chứng và mở "
     "rộng phạm vi sử dụng (Phần III mục 4).")
para(doc,
     "*Về tài liệu này.* Đề cương sơ bộ được lập ở giai đoạn đặt vấn đề, nhằm trả lời ba câu "
     "hỏi trước khi bắt tay vào làm: *định làm gì, làm theo cách nào, và lấy gì để chứng minh "
     "là đã làm được?* Vì hồ sơ được nộp khi công việc đã hoàn thành, mỗi phần kế hoạch dưới "
     "đây đều kèm phần đối chiếu với kết quả thực tế — để thấy rõ điều gì diễn ra đúng dự "
     "kiến, điều gì phải điều chỉnh, và điều gì đến nay vẫn còn dang dở. Phần diễn giải kỹ "
     "thuật ở mức từng cơ chế nằm ở văn bản 05 — Đề cương chi tiết.")

muc_luc(doc, sang_trang=True)

# =====================================================================
h1(doc, "I. LÝ DO ĐỀ XUẤT SÁNG KIẾN", sang_trang=True)

h2(doc, "1. Ràng buộc nghiệp vụ — điểm xuất phát")
para(doc,
     "Sáng kiến bắt đầu từ một ràng buộc, không phải từ một ý tưởng công nghệ. Ở Học viện "
     "Khoa học Quân sự và các cơ quan, đơn vị có yêu cầu cao về bảo vệ thông tin, việc quản "
     "lý, lưu trữ và chuyển giao tài liệu mật, tài liệu nội bộ phải tuân thủ nghiêm ngặt quy "
     "định hiện hành; đơn vị *không cho phép* đưa tài liệu mật và tài liệu nội bộ lên thiết "
     "bị di động cá nhân.")
para(doc,
     "Ràng buộc đó loại bỏ ngay một hướng đi tưởng như hiển nhiên — làm một ứng dụng để mang "
     "tài liệu công tác theo người — và buộc sáng kiến phải tìm giá trị ở chỗ khác. Việc xác "
     "định ranh giới này ngay từ đầu, thay vì để lộ ra khi đã làm xong, là quyết định đầu "
     "tiên và cũng là quyết định định hình toàn bộ phần còn lại.")

h2(doc, "2. Hai nhu cầu thực tiễn nằm trong ranh giới cho phép")
para(doc, "*Nhu cầu thứ nhất — huấn luyện.* "
     "Bảo vệ dữ liệu bằng mật mã là nội dung quan trọng trong chương trình đào tạo an toàn "
     "thông tin, bảo đảm an toàn tình báo trên không gian mạng. Nhưng việc học hiện nay chủ "
     "yếu dừng ở lý thuyết, thuật toán và công cụ chạy trên máy tính, trong khi thiết bị di "
     "động mới là môi trường học viên phải bảo vệ dữ liệu nhiều nhất sau khi ra trường. Học "
     "viên biết nguyên lý nhưng chưa từng thao tác, chưa từng thấy một hệ thống an toàn hoàn "
     "chỉnh vận hành ra sao — đó là khoảng cách cần lấp.")
para(doc, "*Nhu cầu thứ hai — tình huống khẩn cấp, bất khả kháng.* "
     "Trong công tác vẫn phát sinh trường hợp một số tài liệu đặc thù buộc phải chuyển gấp "
     "qua không gian mạng khi không còn phương án nào khác kịp thời hạn. Tệp rời khỏi tầm "
     "kiểm soát của người gửi và đi qua hạ tầng không do đơn vị quản lý. Trong những trường "
     "hợp đã được cấp có thẩm quyền cho phép chuyển giao, cán bộ cần một công cụ tin cậy và "
     "kiểm chứng được để tự trang bị thêm lớp bảo vệ cho tệp trước khi gửi.")
hinh(doc, PNG / "H1-bai-toan-thuc-te.png",
     "Hai nhu cầu thực tiễn mà sáng kiến hướng tới và bốn nhóm nguy cơ tương ứng", width_cm=13.5)

h2(doc, "3. Vì sao các giải pháp sẵn có chưa lấp được khoảng trống")
para(doc,
     "Sáu nhóm giải pháp đã được khảo sát trước khi quyết định tự xây dựng. Nhận xét rút ra "
     "không phải là “các giải pháp hiện có kém” — mỗi nhóm đều làm tốt việc mà nó được thiết "
     "kế cho — mà là *không nhóm nào giải quyết trọn vẹn bài toán đang xét*.")
bang(doc, "Khoảng trống của từng nhóm giải pháp so với nhu cầu đặt ra",
     ["Nhóm giải pháp", "Điểm chưa đáp ứng được"],
     [
         ["Mã hoá toàn thiết bị của hệ điều hành",
          "Chỉ bảo vệ khi máy tắt hoặc chưa mở khoá lần đầu; khi máy đã mở khoá thì mọi ứng "
          "dụng đều thấy dữ liệu ở dạng rõ, và tệp rời thiết bị thì không còn được bảo vệ"],
         ["Ứng dụng “khoá tệp”, “két riêng tư” trên kho ứng dụng",
          "Phần lớn mã nguồn đóng nên không kiểm chứng được thuật toán và cách quản lý khoá; "
          "nhiều ứng dụng đòi quyền mạng; định dạng riêng khoá người dùng vào một sản phẩm"],
         ["Trình quản lý mật khẩu mã nguồn mở",
          "Thiết kế cho thông tin đăng nhập, không nhằm xử lý tệp, ảnh, tài liệu; không có ký "
          "số, kiểm tra toàn vẹn, chia khoá phục hồi hay xử lý siêu dữ liệu"],
         ["Công cụ mật mã dòng lệnh",
          "Thuật toán tin cậy nhưng không có bản dùng được trên thiết bị di động — lý do kỹ "
          "thuật nêu ở mục I.4; giao diện dòng lệnh không phù hợp người dùng không chuyên"],
         ["Ứng dụng nhắn tin mã hoá đầu-cuối",
          "Bảo vệ đường truyền nhưng không bảo vệ dữ liệu ở trạng thái lưu trên máy; dữ liệu "
          "vẫn đi qua hạ tầng của nhà cung cấp dịch vụ nước ngoài"],
         ["Giải pháp quản lý thiết bị / chống thất thoát dữ liệu",
          "Cần hạ tầng máy chủ, chi phí bản quyền và phụ thuộc nhà cung cấp; khó triển khai "
          "cho nhu cầu cá nhân và nhóm nhỏ"],
     ], widths=[4.6, 10.9])

h2(doc, "4. Rào cản kỹ thuật khiến khoảng trống tồn tại")
para(doc,
     "Câu hỏi tự nhiên là: nếu đã có công cụ mật mã dòng lệnh rất tốt, vì sao không đưa thẳng "
     "chúng lên điện thoại? Đây là điểm mấu chốt và cũng là lý do sáng kiến có chỗ đứng.")
para(doc,
     "Các công cụ mật mã tin cậy được phân phối dưới dạng *tệp nhị phân chạy độc lập*. Trên "
     "máy tính để bàn, ứng dụng gọi chúng như một tiến trình con: nạp tệp nhị phân, truyền "
     "tham số, đọc kết quả. Trên thiết bị di động thì cơ chế đó bị chặn ở hai tầng khác nhau: "
     "iOS cấm hoàn toàn việc một ứng dụng sinh tiến trình; Android cho phép sinh tiến trình "
     "nhưng chặn thực thi tệp nhị phân nằm trong vùng lưu trữ mà ứng dụng ghi được — tức đúng "
     "nơi mà một tệp nhị phân đóng gói kèm ứng dụng sẽ nằm.")
khung_nhan_manh(doc, "Vì sao rào cản này khó phát hiện sớm", [
    "Mọi chức năng phụ thuộc tiến trình con sẽ không hoạt động trên điện thoại *kể cả khi mã "
    "nguồn biên dịch thành công*. Chương trình dựng xong, cài được, mở được, và chỉ hỏng khi "
    "người dùng bấm vào chức năng.",
    "Vì vậy đây là rào cản thuộc về kiến trúc nền tảng, phải giải quyết bằng thiết kế ngay từ "
    "đầu, không phải bằng công sức lập trình về sau. Đó là căn cứ cho cách tiếp cận ở Phần III.",
])

# =====================================================================
h1(doc, "II. MỤC TIÊU, ĐỐI TƯỢNG VÀ PHẠM VI", sang_trang=True)

h2(doc, "1. Mục tiêu")
para(doc,
     "*Mục tiêu tổng quát:* xây dựng một bộ công cụ bảo vệ dữ liệu hoạt động hoàn toàn trên "
     "thiết bị, vừa dùng được làm học cụ trực quan cho huấn luyện an toàn thông tin, vừa đủ "
     "tin cậy để cán bộ trang bị thêm lớp bảo vệ cho tệp trong tình huống khẩn cấp, bất khả "
     "kháng đã được cho phép chuyển giao.")
para(doc, "*Năm mục tiêu cụ thể được đặt ra ngay từ đầu, và mỗi mục tiêu kèm một cách kiểm "
     "tra để về sau đối chiếu được:*")
bang(doc, "Mục tiêu cụ thể và cách kiểm tra tương ứng",
     ["Mục tiêu đặt ra", "Cách kiểm tra đã dự kiến", "Kết quả"],
     [
         ["Hoạt động hoàn toàn trên thiết bị: không quyền mạng, không tài khoản, không đồng "
          "bộ đám mây", "Đọc tệp kê khai trong gói cài đặt đã đóng gói", "Đạt"],
         ["Kiểm chứng được: mã nguồn mở, thuật toán công khai, có bộ kiểm thử tự động",
          "Đếm và chạy lại bộ kiểm thử", f"Đạt — {N_TEST} hàm"],
         ["Gộp nhiều nghiệp vụ bảo vệ dữ liệu trong một ứng dụng thống nhất",
          "Đếm số chức năng nghiệp vụ từ mã nguồn", f"Đạt — {N_LENH} chức năng"],
         ["Tệp đầu ra theo chuẩn mở, không khoá người dùng vào một sản phẩm",
          "Đối chứng hai chiều với công cụ chuẩn độc lập", f"Đạt — {SO_DOI_CHUNG} phép"],
         ["Dùng được làm học cụ mà vẫn đạt chuẩn kỹ thuật của công cụ dùng thật",
          "Ánh xạ từng nhóm chức năng với nội dung trong chương trình đào tạo",
          "Đạt — bảng ánh xạ tại Phần VIII"],
     ], widths=[6.0, 5.6, 3.9])
para(doc,
     "Mục tiêu thứ năm đáng chú ý vì nó *thường mâu thuẫn* với bốn mục tiêu còn lại. Sản phẩm "
     "dựng riêng để dạy học hay bị đơn giản hoá tới mức không dùng được thật; ngược lại, công "
     "cụ chuyên nghiệp lại quá phức tạp cho giờ thực hành. Cách hoá giải mâu thuẫn này được "
     "trình bày ở Phần III mục 2 và Phần VIII.")

h2(doc, "2. Đối tượng phục vụ")
for _h, _t in [
    ("Giảng viên. ",
     "Dùng sản phẩm làm học cụ thực hành trên lớp; mỗi nhóm chức năng minh hoạ một nội dung "
     "có sẵn trong chương trình."),
    ("Học viên. ",
     "Thực hành trực tiếp các nội dung mã hoá, chữ ký số, chia sẻ bí mật theo ngưỡng, kiểm "
     "tra toàn vẹn, giấu tin và xử lý siêu dữ liệu; đồng thời tự bảo vệ dữ liệu cá nhân để "
     "hình thành thói quen nghề nghiệp."),
    ("Cán bộ trong tình huống khẩn cấp, bất khả kháng. ",
     "Khi được phép và buộc phải chuyển giao tài liệu qua không gian mạng, dùng sản phẩm để "
     "mã hoá, ký số, kiểm tra toàn vẹn và loại bỏ siêu dữ liệu trước khi chuyển giao."),
]:
    bullet(doc, _t, bold_head=_h)

h2(doc, "3. Phạm vi thực hiện và những gì nằm ngoài phạm vi")
para(doc,
     "Xác định rõ cái *không* làm cũng quan trọng như xác định cái sẽ làm — nó giữ cho khối "
     "lượng công việc nằm trong tầm và giữ cho hồ sơ không tuyên bố quá phạm vi.")
bang(doc, "Phạm vi thực hiện",
     ["Trong phạm vi", "Ngoài phạm vi"],
     [
         ["Thiết kế kiến trúc, định dạng tệp dữ liệu và sơ đồ phân cấp khoá",
          "Tự xây dựng thuật toán mật mã mới — dùng chuẩn công khai đã được soi xét"],
         ["Hiện thực toàn bộ nghiệp vụ bảo vệ dữ liệu trong một lõi độc lập nền tảng",
          "Thay đổi hoặc nới lỏng bất kỳ quy định nào về bảo vệ bí mật"],
         ["Ứng dụng chạy trên thiết bị di động Android — trọng tâm của sáng kiến",
          "Tuyên bố sản phẩm được phép xử lý tài liệu ở một cấp độ mật cụ thể"],
         ["Bản trên máy tính để bàn dùng chung lõi, đóng vai trò đối chứng và mở rộng",
          "Đóng gói bản cài đặt có ký số, công chứng để phân phối rộng rãi"],
         ["Bộ kiểm thử tự động và quy trình nghiệm thu trên thiết bị thật",
          "Bảo vệ dữ liệu khi thiết bị đã bị chiếm quyền điều khiển ở mức hệ điều hành"],
     ], widths=[7.7, 7.8])
khung_nhan_manh(doc, "Phạm vi tự giới hạn", [
    "Sáng kiến là công cụ hỗ trợ kỹ thuật nhằm giảm rủi ro trong phạm vi hoạt động đã được "
    "phép. Việc một tài liệu cụ thể có được lưu trữ, xử lý hay chuyển giao qua một phương "
    "thức nhất định hay không vẫn hoàn toàn do quy định hiện hành và người có thẩm quyền "
    "quyết định.",
], mau="FDF3E3", vien="B07D2B")

# =====================================================================
h1(doc, "III. Ý TƯỞNG GIẢI PHÁP VÀ CÁCH TIẾP CẬN", sang_trang=True)

h2(doc, "1. Ý tưởng cốt lõi")
para(doc,
     "Từ rào cản ở Phần I mục 4, ý tưởng của nhóm tác giả không phải là “tìm cách chạy công "
     "cụ dòng lệnh trên điện thoại” — hướng đó bị hệ điều hành chặn và không thể vòng qua. Ý "
     "tưởng là *đảo ngược chỗ đặt vấn đề*:")
khung_nhan_manh(doc, "Ý tưởng cốt lõi của sáng kiến", [
    "Đưa toàn bộ nghiệp vụ bảo vệ dữ liệu — định dạng tệp, sơ đồ khoá, quy tắc lỗi, các phép "
    "mật mã — vào một lõi *độc lập với giao diện và độc lập với nền tảng*.",
    "Đặt điểm nối trừu tượng tại đúng những vị trí phải phụ thuộc nền tảng, và chỉ ở đó.",
    "Khi đổi nền tảng, chỉ thay phần nằm *trên* các điểm nối ấy. Nghiệp vụ, định dạng dữ liệu "
    "và cơ chế bảo vệ nằm *dưới* nên giữ nguyên — kể cả khi cách hiện thực bên dưới thay đổi "
    "hoàn toàn.",
])
para(doc,
     "Điểm khó của ý tưởng nằm ở chỗ *đặt điểm nối ở đâu*. Đặt quá cao, ở mức nghiệp vụ, thì "
     "mỗi nền tảng phải viết lại toàn bộ nghiệp vụ và hai bản sẽ trôi xa nhau theo thời gian. "
     "Đặt quá thấp, ở mức từng phép mật mã, thì mỗi bản hiện thực phải tự ghép lại đúng định "
     "dạng tệp và rất dễ lệch. Điểm nối được chọn đặt tại ranh giới *“một luồng dữ liệu vào, "
     "một luồng dữ liệu ra theo định dạng công khai”* — nhờ vậy hai bản hiện thực khác nhau "
     "hoàn toàn về cách chạy nhưng buộc phải cho ra cùng một chuỗi byte.")

h2(doc, "2. Sáu nguyên lý được chọn làm ràng buộc thiết kế")
para(doc,
     "Trước khi viết dòng mã đầu tiên, sáu nguyên lý được xác lập. Điều nhóm tác giả coi "
     "trọng không phải bản thân các nguyên lý — chúng là hiểu biết chung của ngành — mà là "
     "yêu cầu tự đặt ra: *mỗi nguyên lý phải được chuyển hoá thành một ràng buộc kỹ thuật "
     "kiểm tra được bằng máy*. Nguyên lý chỉ nằm trong tài liệu thì sớm muộn cũng bị vi phạm "
     "khi phần mềm được sửa đổi; nguyên lý có cơ chế kiểm tra thì không.")
for _t in [
    "*Hoạt động ngoại tuyến tuyệt đối* — ứng dụng không khai báo quyền truy cập mạng, nên "
    "ràng buộc nằm ở cấp hệ điều hành chứ không phụ thuộc thao tác người dùng.",
    "*Một lõi bảo vệ dữ liệu dùng chung* — toàn bộ nghiệp vụ mật mã nằm trong lõi, không dùng "
    "thư viện giao diện hay thư viện đặc thù nền tảng.",
    "*Phụ thuộc một chiều theo lớp* — lớp trên dùng lớp dưới, không có chiều ngược lại; lõi "
    "chỉ phụ thuộc vào giao diện trừu tượng.",
    "*Khi không bảo đảm an toàn thì không tiếp tục xử lý* — thà từ chối kèm mã lỗi còn hơn "
    "báo thành công cho một việc chưa chắc đã làm được.",
    "*Thông báo lỗi không làm lộ thông tin bí mật* — chênh lệch giữa các thông báo không được "
    "dùng làm tín hiệu dò mật khẩu.",
    "*Không lưu trữ bí mật lâu dài* — mật khẩu và khoá chính không bao giờ chạm tới bộ nhớ "
    "lưu trữ của thiết bị.",
]:
    bullet(doc, _t)
para(doc,
     "Cách chuyển hoá từng nguyên lý thành cơ chế cụ thể và cách kiểm tra tương ứng được "
     "trình bày ở mục 2.1 của Đề cương chi tiết.")

h2(doc, "3. Kiến trúc dự kiến")
para(doc,
     f"Ứng dụng được tổ chức thành sáu lớp chức năng, trong đó giao diện tách hẳn khỏi lõi "
     f"nghiệp vụ: mọi yêu cầu từ giao diện xuống lõi phải đi qua một tập lệnh được kiểm soát "
     f"thống nhất, không có đường truy cập trực tiếp nào khác. Lõi được chia thành {N_CRATE} "
     "thành phần độc lập, mỗi thành phần một trách nhiệm. Việc chia nhỏ không nhằm cho “gọn” "
     "mà để chiều phụ thuộc giữa các thành phần trở thành thứ kiểm tra được bằng máy.")
hinh(doc, PNG / "H2-kien-truc-phan-lop.png",
     f"Kiến trúc phân lớp dự kiến của {TEN_SP}", width_cm=13.5)

h2(doc, "4. Triển khai trên hai nền tảng và vai trò của từng bản")
para(doc,
     "Kiến trúc trên có một hệ quả mà ban đầu không phải là mục tiêu, nhưng về sau trở thành "
     "một trong những tính chất đáng giá nhất: *nếu nghiệp vụ và định dạng dữ liệu đều nằm "
     "dưới ranh giới không phụ thuộc nền tảng, thì thay nền tảng không còn là viết lại sản "
     "phẩm, mà chỉ là thay phần nằm trên ranh giới đó.* Kế hoạch vì vậy đặt ra hai bản hiện "
     "thực dùng chung một lõi, với vai trò khác hẳn nhau.")
bang(doc, "Vai trò của hai bản trong sáng kiến",
     ["", "Bản trên máy tính để bàn", "Bản trên thiết bị di động"],
     [
         ["Mô-đun mã hoá nội dung",
          "Điều khiển công cụ chuẩn dưới dạng tiến trình con, có ghim giá trị băm tệp nhị phân",
          "Thực hiện ngay trong tiến trình ứng dụng"],
         ["Mô-đun siêu dữ liệu", "Gọi công cụ ngoài, phạm vi định dạng rộng",
          "Mô-đun thuần Rust do nhóm tác giả viết, phạm vi hẹp và công bố rõ"],
         ["Bài toán kỹ thuật phải giải", "Không có rào cản đặc thù",
          "Rào cản tiến trình con của hệ điều hành di động — trọng tâm của sáng kiến"],
         ["Vai trò trong hồ sơ",
          "Bản đối chứng và tham chiếu ngữ nghĩa; mở rộng phạm vi sử dụng",
          "Nơi tập trung giá trị sáng tạo"],
         ["Nghiệp vụ, định dạng tệp, sơ đồ khoá, quy tắc lỗi", "Như nhau", "Như nhau"],
     ], widths=[3.6, 6.2, 5.7])
para(doc,
     "Nói ngắn gọn: *bản máy tính chứng minh kiến trúc là đúng, bản di động chứng minh kiến "
     "trúc là có ích.* Trọng tâm của sáng kiến nằm ở bản di động, vì đó là nơi rào cản kỹ "
     "thuật thực sự tồn tại và được giải quyết.")
hinh(doc, PNG / "H3-loi-dung-chung.png",
     "Nguyên tắc một lõi dùng chung, hai bản hiện thực theo nền tảng", width_cm=13.5)

# =====================================================================
h1(doc, "IV. NỘI DUNG THỰC HIỆN", sang_trang=True)

h2(doc, "1. Các khối công việc")
bang(doc, "Khối công việc và sản phẩm của từng khối",
     ["Khối công việc", "Nội dung chính", "Sản phẩm của khối"],
     [
         ["A. Thiết kế nền móng",
          "Xác định mô hình mối đe doạ, sáu nguyên lý thiết kế, ranh giới giữa các lớp và giao "
          "diện trừu tượng của các nguyên hàm mật mã",
          "Tài liệu kiến trúc và tập giao diện trừu tượng"],
         ["B. Thiết kế dữ liệu",
          "Cấu trúc tệp két, sơ đồ phân cấp khoá, ngữ cảnh dẫn xuất khoá, cơ chế chữ ký ràng "
          "buộc phần đầu tệp với nội dung",
          "Đặc tả định dạng tệp và sơ đồ khoá"],
         ["C. Hiện thực lõi nghiệp vụ",
          "Nghiệp vụ két, bảo vệ tệp đơn lẻ, ký số và kiểm tra toàn vẹn, chia bí mật theo "
          "ngưỡng, giấu tin, thuỷ vân, siêu dữ liệu",
          f"Lõi gồm {N_CRATE} thành phần cùng bộ kiểm thử"],
         ["D. Quy tắc lỗi và ranh giới lệnh",
          "Phân loại lỗi nội bộ, quy tắc chiếu ra giao diện sao cho không lộ thông tin, mô "
          "hình phiên làm việc",
          f"Tập {N_LENH} lệnh nghiệp vụ có ngữ nghĩa ổn định"],
         ["E. Bản trên máy tính để bàn",
          "Lớp lắp ráp cho máy tính, giao diện, đóng gói; đóng vai trò bản đối chứng",
          "Ứng dụng chạy trên máy tính"],
         ["F. Bản trên thiết bị di động",
          "Giải rào cản tiến trình con: bản hiện thực trong tiến trình cho mô-đun mã hoá và "
          "mô-đun siêu dữ liệu; luồng tệp theo cơ chế của Android; giao diện cảm ứng",
          "Ứng dụng Android đóng gói được"],
         ["G. Kiểm chứng",
          "Bộ kiểm thử tự động, kiểm thử trên kiến trúc bộ xử lý của điện thoại, đối chứng "
          "với công cụ chuẩn, kiểm tra tĩnh gói cài đặt, quy trình nghiệm thu",
          "Bằng chứng kiểm chứng nhiều mức"],
     ], widths=[3.4, 7.4, 4.7])

h2(doc, "2. Các nhóm chức năng dự kiến")
para(doc,
     f"Chức năng được nhóm theo *mục đích sử dụng* chứ không theo thuật toán, để người dùng "
     f"chọn được chức năng mà không cần biết bên trong dùng gì. Tám nhóm dưới đây là kế "
     f"hoạch ban đầu, và cũng là cấu trúc của sản phẩm cuối cùng với tổng cộng {N_LENH} chức "
     f"năng nghiệp vụ.")
_TOM_TAT = [
    "Một tệp .svault chứa nhiều tệp dưới một mật khẩu; danh mục tệp cũng được mã hoá",
    "Khoá và mở khoá trực tiếp một tệp bằng mật khẩu, không cần lập két",
    "Chữ ký số, vân tay tệp, đối chiếu vân tay, xác minh tệp tải về",
    "Chia bí mật hoặc tệp thành n mảnh, cần đủ k mảnh mới khôi phục; chuyển mảnh qua mã QR",
    "Giấu tệp đã mã hoá vào ảnh, lấy lại, và phát hiện dấu hiệu dữ liệu ẩn",
    "Nhúng và kiểm tra thuỷ vân dễ vỡ, khoanh vùng vị trí ảnh bị sửa",
    "Xem, xoá và so sánh siêu dữ liệu ngay trên thiết bị, gồm cả toạ độ định vị",
    "Tra cứu phiên bản ứng dụng, giao tiếp lõi, định dạng két và bộ thuật toán",
]
_NGUYEN_LY = [
    "Dẫn xuất khoá từ mật khẩu",
    "Mã hoá có xác thực",
    "Mật mã khoá công khai và hàm băm",
    "Chia sẻ bí mật theo ngưỡng",
    "Giấu tin và giới hạn của che giấu",
    "Phát hiện sửa đổi cục bộ trên ảnh",
    "Kênh lộ thông tin ngoài nội dung",
    "—",
]
bang(doc, "Tám nhóm chức năng và nguyên lý an toàn thông tin tương ứng",
     ["Nhóm", "Nội dung nghiệp vụ", "Số chức năng", "Nguyên lý minh hoạ"],
     [[nhom["ten"].replace("Nhóm ", ""), _TOM_TAT[i], str(len(nhom["chuc_nang"]) - 1),
       _NGUYEN_LY[i]]
      for i, nhom in enumerate(NHOM_CHUC_NANG)],
     widths=[3.6, 5.6, 1.7, 4.6],
     note="Cột cuối là căn cứ cho mục tiêu thứ năm ở Phần II: mỗi nhóm chức năng gắn với một "
          "nội dung có sẵn trong chương trình đào tạo.")

h2(doc, "3. Thiết kế dữ liệu và cơ chế bảo vệ")
para(doc,
     "Ba quyết định thiết kế dữ liệu được xác định ngay ở khối công việc B, vì chúng khó sửa "
     "về sau: mỗi thay đổi đều làm hỏng những tệp đã tạo trước đó.")
for _h, _t in [
    ("Danh mục tệp nằm bên trong phần đã mã hoá. ",
     "Nhiều định dạng đặt danh sách tệp ở phần đầu cho tiện đọc nhanh; hệ quả là người có tệp "
     "mà không có mật khẩu vẫn biết bên trong có những gì. Ở đây toàn bộ nội dung két, kể cả "
     "danh mục, là một luồng mã hoá duy nhất — két đang khoá không tiết lộ tên tệp, kích "
     "thước hay cả số lượng tệp."),
    ("Khoá chỉ được lưu ở dạng đã bọc, với khoá bọc ràng buộc theo từng trường và từng két. ",
     "Nhờ vậy một khối dữ liệu đã bọc không dùng được cho trường khác, cũng không mang được "
     "từ két này sang két khác. Một hệ quả thực dụng: đổi mật khẩu chỉ phải bọc lại vài khoá "
     "con, không phải mã hoá lại toàn bộ nội dung."),
    ("Chữ ký phủ lên một “gốc ràng buộc” tính từ cả phần đầu lẫn phần nội dung. ",
     "Nhờ vậy không thể ghép phần đầu của tệp này với nội dung của tệp khác. Việc kiểm tra "
     "chữ ký diễn ra *trước* khi mật khẩu được dùng đến, nên phân biệt được “tệp hỏng” với "
     "“mật khẩu sai” mà không biến sự phân biệt đó thành manh mối dò mật khẩu."),
]:
    bullet(doc, _t, bold_head=_h)
para(doc,
     f"Về nguyên hàm mật mã, nguyên tắc nghề nghiệp được tuân thủ tuyệt đối: *không tự xây "
     f"dựng thuật toán mới*. Bộ nguyên hàm gồm {TT['kdf']} dẫn xuất khoá từ mật khẩu với "
     f"ngưỡng {A2['min_mem_kib'] // 1024} MiB bộ nhớ và {A2['min_time_cost']} vòng lặp theo "
     f"khuyến nghị OWASP; {TT['hash']} băm nội dung và tạo khoá con theo ngữ cảnh; "
     f"{TT['aead_vault']} mã hoá nội dung két; {TT['aead_field']} bảo vệ các trường khoá; "
     f"{TT['chu_ky']} ký phần đầu tệp; và {TT['chia_se_bi_mat']} chia khoá phục hồi. Đóng góp "
     "của nhóm tác giả nằm ở việc chọn nguyên hàm nào cho việc gì, ghép chúng trong một kiến "
     "trúc, và đặt tham số phù hợp với ràng buộc của thiết bị di động.")
hinh(doc, PNG / "H4-phan-cap-khoa.png", "Sơ đồ phân cấp khoá và luồng mở két", width_cm=13.0)

h2(doc, "4. Yêu cầu đặt ra cho giao diện")
para(doc,
     "Với một ứng dụng bảo vệ dữ liệu, một thao tác sai vì giao diện gây hiểu nhầm cũng dẫn "
     "tới lộ dữ liệu như một lỗi mật mã. Vì vậy giao diện được xem là một phần của thiết kế "
     "an toàn, với bốn yêu cầu đặt ra từ đầu: trình bày theo *công việc cần làm* chứ không "
     "theo thuật toán; phân tầng thông tin để người dùng mới không bị ngợp mà người muốn kiểm "
     "chứng vẫn đủ dữ kiện; cảnh báo liên quan đến nguy cơ mất dữ liệu thì *không được thu "
     "gọn*; và không để kết quả của thao tác trước bị hiểu nhầm là kết quả của thao tác mới.")

# =====================================================================
h1(doc, "V. PHƯƠNG PHÁP VÀ KẾ HOẠCH KIỂM CHỨNG", sang_trang=True)

h2(doc, "1. Nguyên tắc kiểm chứng")
para(doc,
     "Nguyên tắc đặt ra cho toàn bộ công việc: *mỗi tuyên bố kỹ thuật trong hồ sơ phải gắn "
     "với một cách kiểm tra bằng máy, và phải phân biệt rõ giữa “đã hiện thực” với “đã kiểm "
     "chứng bằng thực nghiệm”.* Hai điều đó khác nhau, và việc gộp chúng lại là cách phổ biến "
     "nhất khiến một hồ sơ kỹ thuật mất tin cậy. Nguyên tắc này cũng áp dụng cho chính hồ sơ: "
     "mọi con số trong các văn bản đều được sinh tự động từ mã nguồn và nhật ký kiểm thử.")

h2(doc, "2. Các mức kiểm chứng và kết quả")
bang(doc, "Kế hoạch kiểm chứng và kết quả thực tế",
     ["Mức", "Cách làm", "Tiêu chí đạt", "Kết quả"],
     [
         ["1. Kiểm thử đơn vị và tích hợp",
          "Bộ kiểm thử tự động chạy trên máy chủ tích hợp liên tục",
          "Không có phép kiểm thử nào lỗi",
          f"{host.get('passed')} đạt / {host.get('failed')} lỗi"],
         ["2. Đúng kiến trúc bộ xử lý của điện thoại",
          "Chạy lõi dưới trình giả lập kiến trúc ARM64 trên mã đã biên dịch cho kiến trúc đó",
          "Các thành phần mật mã và lớp gọi thư viện hệ thống chạy đúng",
          f"{arm.get('passed')} đạt / {arm.get('failed')} lỗi"],
         ["3. Đa nền tảng",
          f"Dựng, soát mã và chạy kiểm thử trên ma trận hệ điều hành ({CHUOI_OS})",
          "Mọi hạng mục đều xanh trên cả ba hệ điều hành",
          f"{CI_XANH.get('so_viec_dat')} hạng mục đạt ({CI_XANH.get('ngay')})"],
         ["4. Tương thích định dạng",
          "Đối chứng hai chiều với công cụ chuẩn độc lập và mở chéo két giữa hai bản hiện thực",
          "Cả hai chiều đều đọc được tệp của nhau; mật khẩu sai vẫn bị từ chối",
          f"{SO_DOI_CHUNG} phép đối chứng đạt"],
         ["5. Kiểm tra gói cài đặt",
          "Mở gói cài đặt sẽ giao cho người dùng và đọc nội dung bên trong",
          "Đúng kiến trúc thư viện; không khai báo quyền mạng; giao diện nhúng sẵn",
          "Đạt"],
         ["6. Nghiệm thu trên thiết bị thật",
          "Quy trình 15 bước có tiêu chí đạt cho từng bước",
          "Từng bước đạt tiêu chí đã ghi",
          "Chưa thực hiện — đã có quy trình"],
     ], widths=[3.2, 4.8, 4.2, 3.3])

h2(doc, "3. Kiểm chứng tương thích giữa các nền tảng")
para(doc,
     "Trong sáu mức trên, mức 4 đáng nói riêng vì nó kiểm chứng đúng tuyên bố trung tâm của "
     "kiến trúc. Ràng buộc tự đặt ra là: *dù thay bản hiện thực nào bên dưới, định dạng tệp "
     "trên đĩa không được thay đổi.* Đây là loại ràng buộc dễ bị vi phạm âm thầm — một thay "
     "đổi nhỏ có thể sinh ra tệp mà chỉ chính nó đọc được — và không thể phát hiện bằng cách "
     "đọc mã.")
para(doc,
     "Vì vậy kế hoạch đặt ra hai loại phép kiểm chứng. Loại thứ nhất đối chứng với *công cụ "
     "chuẩn do bên thứ ba viết*: tệp do sản phẩm tạo phải giải mã được bằng công cụ đó và "
     "ngược lại — khi đó kết luận về tính tương thích không còn phụ thuộc vào lời khẳng định "
     "của nhóm tác giả. Loại thứ hai dựng nguyên một tệp két hoàn chỉnh bằng bản hiện thực "
     "của nền tảng này rồi mở bằng bản của nền tảng kia, đi qua toàn bộ chuỗi từ dẫn xuất "
     f"khoá tới giải mã danh mục và lấy tệp ra. Cả hai loại đã thực hiện: {SO_DOI_CHUNG} "
     "phép, tất cả đạt.")

h2(doc, "4. Phần chưa kiểm chứng")
khung_nhan_manh(doc, "Nêu rõ thay vì bỏ qua", [
    "Nghiệm thu trên thiết bị Android thật chưa thực hiện tại thời điểm lập hồ sơ. Mọi kiểm "
    "chứng đều trên máy chủ, kể cả phép chạy dưới trình giả lập kiến trúc ARM64. Quy trình "
    "nghiệm thu 15 bước đã soạn sẵn tại Phụ lục A của Đề cương chi tiết.",
    "Việc đóng gói bản cài đặt có ký số và công chứng cho Windows và macOS chưa thực hiện, "
    "nên hồ sơ không tuyên bố sản phẩm đã sẵn sàng phát hành trên hai nền tảng đó; điều được "
    "khẳng định là mã nguồn dựng và chạy kiểm thử đạt trên các nền tảng đó.",
], mau="FDF3E3", vien="B07D2B")

# =====================================================================
h1(doc, "VI. SẢN PHẨM VÀ CHỈ TIÊU", sang_trang=True)

h2(doc, "1. Danh mục sản phẩm")
for _t in [
    f"Ứng dụng Android đóng gói dưới dạng APK ({MB_APK} MB), tích hợp lõi bảo vệ dữ liệu biên "
    "dịch cho kiến trúc ARM64.",
    f"Mã nguồn đầy đủ: lõi gồm {N_CRATE} thành phần độc lập, giao diện gồm "
    f"{len(DANH_MUC_MAN_HINH)} màn hình, kèm {N_TEST} hàm kiểm thử tự động.",
    f"Bản trên máy tính để bàn dùng chung lõi, dựng và chạy kiểm thử đạt trên {CHUOI_OS}.",
    "Bộ tài liệu: tài liệu kiến trúc, mô hình mối đe doạ, hướng dẫn triển khai và quy trình "
    "nghiệm thu trên thiết bị thật.",
]:
    bullet(doc, _t)

h2(doc, "2. Chỉ tiêu đặt ra và kết quả đạt được")
bang(doc, "Đối chiếu chỉ tiêu dự kiến với kết quả thực tế",
     ["Chỉ tiêu", "Dự kiến ban đầu", "Đạt được", "Cách xác định"],
     [
         ["Số chức năng nghiệp vụ", "Đủ cho tám nhóm nghiệp vụ", f"{N_LENH} chức năng",
          "Đếm trực tiếp từ mã nguồn"],
         ["Chức năng chưa có giao diện gọi tới", "Không có", "0",
          "Đối chiếu hai chiều giữa lõi và mã giao diện"],
         ["Số hàm kiểm thử tự động", "Đủ phủ từng thành phần", f"{N_TEST} hàm",
          "Đếm trực tiếp từ mã nguồn"],
         ["Quyền ứng dụng yêu cầu", "Không quyền nào", "Không khai báo quyền nào",
          "Đọc tệp kê khai trong gói cài đặt"],
         ["Tương thích định dạng", "Đọc được cả hai chiều",
          f"{SO_DOI_CHUNG} phép đối chứng đạt", "Đối chứng với công cụ chuẩn độc lập"],
         ["Chạy trên hệ điều hành máy tính", "Cả ba hệ điều hành phổ biến",
          f"{CHUOI_OS} — đạt",
          f"Biên bản tích hợp liên tục {CI_XANH.get('ngay')}"],
         ["Nghiệm thu trên thiết bị Android thật", "Có quy trình và thực hiện",
          "Đã có quy trình 15 bước, chưa thực hiện", "Phụ lục A của Đề cương chi tiết"],
     ], widths=[4.0, 3.8, 4.0, 3.7])

# =====================================================================
h1(doc, "VII. TIẾN TRÌNH THỰC HIỆN", sang_trang=True)
para(doc,
     f"Công việc được chia thành các giai đoạn theo thứ tự phụ thuộc: giai đoạn sau chỉ bắt "
     f"đầu khi giai đoạn trước đã chốt được thứ mà nó cần. Toàn bộ quá trình diễn ra trong "
     f"khoảng từ {GIT.get('ngay_dau')} đến {GIT.get('ngay_cuoi')}, ghi nhận qua lịch sử kho "
     "mã nguồn.")
bang(doc, "Các giai đoạn thực hiện",
     ["Giai đoạn", "Nội dung", "Điều kiện để chuyển giai đoạn"],
     [
         ["Nền móng",
          "Chốt giao ước giữa các lớp, giao diện trừu tượng của nguyên hàm mật mã, mô hình "
          "mối đe doạ và sáu nguyên lý thiết kế",
          "Giao diện trừu tượng đủ để lõi kiểm thử được độc lập với bản hiện thực thật"],
         ["Nguyên hàm mật mã",
          "Hiện thực và kiểm thử từng nguyên hàm; chốt chính sách tham số",
          "Từng nguyên hàm có kiểm thử riêng và đối chiếu với vector chuẩn"],
         ["Định dạng dữ liệu và phân cấp khoá",
          "Chốt cấu trúc tệp két, ngữ cảnh dẫn xuất khoá, cơ chế chữ ký ràng buộc",
          "Định dạng được coi là đóng băng — mọi thay đổi về sau đều phá vỡ tệp cũ"],
         ["Nghiệp vụ và ranh giới lệnh",
          "Hiện thực các nghiệp vụ; chốt quy tắc phân loại lỗi và mô hình phiên làm việc",
          "Tập lệnh có ngữ nghĩa ổn định để giao diện dựa vào"],
         ["Bản trên máy tính và làm cứng",
          "Lớp lắp ráp cho máy tính, giao diện, đóng gói; rà soát và khắc phục các điểm yếu "
          "phát hiện qua thực nghiệm",
          "Bộ kiểm thử xanh trên ma trận ba hệ điều hành"],
         ["Bản trên thiết bị di động",
          "Giải rào cản tiến trình con; mô-đun mã hoá và mô-đun siêu dữ liệu chạy trong tiến "
          "trình; luồng tệp theo cơ chế Android; giao diện cảm ứng; đóng gói APK",
          "Tệp két đọc chéo được giữa hai nền tảng; gói cài đặt kiểm tra tĩnh đạt"],
         ["Kiểm chứng và lập hồ sơ",
          "Chạy kiểm thử trên kiến trúc ARM64, đối chứng định dạng, kiểm tra gói cài đặt, "
          "soạn quy trình nghiệm thu và bộ hồ sơ sáng kiến",
          "Mọi số liệu trong hồ sơ sinh tự động từ mã nguồn và nhật ký"],
     ], widths=[3.2, 6.6, 5.7])
para(doc,
     "Một điều chỉnh đáng kể so với kế hoạch ban đầu cần được ghi nhận: nhóm mô-đun siêu dữ "
     "liệu ban đầu dự kiến dùng lại cách làm của bản máy tính. Khi triển khai lên di động mới "
     "phát hiện cách đó vướng đúng rào cản đã nêu ở Phần I mục 4, nên phải bổ sung một khối "
     "công việc không có trong kế hoạch: tự viết mô-đun xử lý siêu dữ liệu bằng Rust. Đây "
     "cũng là ví dụ cho thấy vì sao rào cản đó khó lường trước.")

# =====================================================================
h1(doc, "VIII. DỰ KIẾN HIỆU QUẢ, RỦI RO VÀ KHẢ NĂNG ÁP DỤNG", sang_trang=True)

h2(doc, "1. Hiệu quả đối với công tác huấn luyện")
para(doc,
     "Ở Phần II đã nêu mâu thuẫn giữa “dùng được để dạy” và “dùng được thật”. Cách hoá giải "
     "là *không dựng hai sản phẩm*: học viên thực hành trên đúng công cụ được xây dựng cho "
     "nhu cầu sử dụng thật. Điều làm cho nó dùng được trong dạy học không phải sự đơn giản "
     "hoá, mà là bốn yêu cầu giao diện ở Phần IV mục 4 — đặc biệt là phân tầng thông tin: "
     "phần kỹ thuật không bị bỏ đi mà đưa vào mục mở rộng, nơi giảng viên mở ra đúng lúc cần "
     "giảng.")
para(doc,
     "Một giá trị huấn luyện nữa ít gặp ở công cụ thương mại: sản phẩm *chủ động dạy về giới "
     "hạn của chính nó*. Chức năng phát hiện dữ liệu ẩn không kết luận “ảnh sạch” mà chỉ nêu "
     "mức độ nghi ngờ trong phạm vi các phép kiểm tra đã làm; chức năng kiểm tra thuỷ vân "
     "phân biệt “ảnh bị sửa” với “ảnh đã bị biến đổi khi lưu ở định dạng có mất dữ liệu”. Học "
     "viên qua đó hiểu rằng kết quả của một công cụ phân tích luôn phụ thuộc phương pháp và "
     "phạm vi — một bài học khó truyền đạt bằng lý thuyết.")

h2(doc, "2. Hiệu quả kỹ thuật, kinh tế và quốc phòng – an ninh")
for _h, _t in [
    ("Kỹ thuật. ",
     "Bảo vệ dữ liệu ở trạng thái lưu trữ bằng một lớp mật khẩu riêng, kể cả khi thiết bị đã "
     "mở khoá; duy trì bảo vệ sau khi tệp rời thiết bị; phát hiện sửa đổi bằng chữ ký số; "
     "khôi phục quyền truy cập bằng chia khoá theo ngưỡng mà không phải gửi khoá cho bên thứ "
     "ba; loại bỏ siêu dữ liệu ngay tại nơi nó phát sinh; và dùng định dạng mở nên liên thông "
     "được với công cụ sẵn có."),
    ("Kinh tế. ",
     "Không phát sinh chi phí bản quyền, không đầu tư máy chủ, không thuê bao dịch vụ, chạy "
     "trên thiết bị sẵn có. Nhóm tác giả không quy đổi thành con số tiền cụ thể vì con số đó "
     "phụ thuộc quy mô triển khai và chính sách mua sắm của từng đơn vị; ước lượng khi chưa "
     "triển khai sẽ không có căn cứ."),
    ("Quốc phòng – an ninh. ",
     "Giảm rủi ro lộ lọt trong tình huống đặc thù đã được cho phép chuyển giao; tăng khả năng "
     "kiểm soát dữ liệu vì toàn bộ xử lý diễn ra trên thiết bị; giảm phụ thuộc vào giải pháp "
     "bên ngoài vì thiết kế và mã nguồn do đơn vị làm chủ; và góp phần đào tạo nhân lực làm "
     "chủ công nghệ."),
]:
    bullet(doc, _t, bold_head=_h)

h2(doc, "3. Rủi ro đã lường trước và cách xử lý")
para(doc,
     "Một đề cương trung thực phải nêu cả những rủi ro có thể làm hỏng kết quả. Bảng dưới ghi "
     "các rủi ro được nhận diện từ đầu, cách xử lý đã chọn và trạng thái hiện nay.")
bang(doc, "Rủi ro, cách xử lý và trạng thái",
     ["Rủi ro", "Cách xử lý đã chọn", "Trạng thái"],
     [
         ["Rào cản tiến trình con khiến chức năng mật mã không chạy trên di động",
          "Đặt điểm nối trừu tượng và viết bản hiện thực chạy trong tiến trình",
          "Đã xử lý; kiểm chứng bằng đối chứng định dạng"],
         ["Thay bản hiện thực làm đổi định dạng, tệp cũ không mở được",
          "Đặt bất biến định dạng thành ràng buộc bắt buộc và kiểm chứng bằng thực nghiệm hai "
          "chiều", "Đã xử lý"],
         ["Người dùng quên mật khẩu, dữ liệu không lấy lại được",
          "Cung cấp cơ chế chia khoá phục hồi theo ngưỡng; hiển thị cảnh báo thường trực, "
          "không thu gọn",
          "Đã giảm thiểu; vẫn là giới hạn có chủ ý của thiết kế"],
         ["Giao diện hứa nhiều hơn khả năng thật của mô-đun siêu dữ liệu trên di động",
          "Công bố phạm vi định dạng theo đúng nền tảng đang chạy; từ chối kèm mã lỗi với "
          "định dạng ngoài phạm vi", "Đã xử lý"],
         ["Thông báo lỗi trở thành manh mối dò mật khẩu",
          "Quy tắc chiếu lỗi từ lõi ra giao diện, áp dụng thống nhất cho cả hai bản hiện thực",
          "Đã xử lý; có kiểm thử đối chiếu"],
         ["Số liệu trong hồ sơ lệch với sản phẩm thực tế",
          "Sinh toàn bộ số liệu tự động từ mã nguồn và nhật ký kiểm thử",
          "Đã xử lý"],
         ["Hành vi trên máy thật khác với môi trường kiểm thử",
          "Soạn quy trình nghiệm thu 15 bước có tiêu chí đạt cho từng bước",
          "Còn tồn tại — quy trình đã có, chưa thực hiện"],
         ["Thiết bị bị chiếm quyền điều khiển ở mức hệ điều hành",
          "Nằm ngoài khả năng của biện pháp trong phạm vi ứng dụng; công bố rõ trong mô hình "
          "mối đe doạ", "Chấp nhận, có công bố"],
     ], widths=[5.2, 6.6, 3.7])

h2(doc, "4. Khả năng áp dụng và hướng phát triển")
para(doc,
     "Điều kiện triển khai rất đơn giản: một thiết bị Android, không cần máy chủ, không cần "
     "kết nối mạng, không yêu cầu quyền quản trị thiết bị — hệ quả trực tiếp của nguyên lý "
     "hoạt động ngoại tuyến. Nhờ kiến trúc dùng chung, cùng bộ chức năng còn triển khai được "
     "trên máy trạm và tệp két đi lại được giữa hai môi trường, mở thêm cách dùng thực tế cho "
     "công tác giảng dạy.")
para(doc, "*Hướng phát triển tiếp theo, xếp theo thứ tự ưu tiên:*")
for _t in [
    "Thực hiện quy trình nghiệm thu trên nhiều dòng điện thoại và phiên bản Android khác "
    "nhau, ghi nhận kết quả để đánh giá mức độ ổn định.",
    "Hoàn thiện khâu đóng gói có ký số và công chứng cho bản trên máy tính — bước duy nhất "
    "còn thiếu để bản đó phân phối được rộng rãi.",
    "Nghiên cứu dùng kho khoá phần cứng của thiết bị cho một số khoá nằm ngoài hệ thống khoá "
    "của két, kèm tuỳ chọn xác thực bằng vân tay.",
    "Mở rộng phạm vi định dạng của mô-đun siêu dữ liệu, giữ nguyên tắc chỉ báo thành công khi "
    "kết quả đã được kiểm tra.",
    "Biên soạn bộ bài giảng và phiếu bài thực hành đi kèm, làm cơ sở đưa sản phẩm vào chương "
    "trình huấn luyện chính thức.",
]:
    bullet(doc, _t)

# =====================================================================
h1(doc, "IX. TÀI LIỆU THAM KHẢO")
for _t in [
    "RFC 9106 — Argon2 Memory-Hard Function for Password Hashing.",
    f"OWASP Password Storage Cheat Sheet — tham số tối thiểu cho Argon2id "
    f"({A2['min_mem_kib'] // 1024} MiB bộ nhớ, {A2['min_time_cost']} vòng lặp).",
    "RFC 8439 — ChaCha20 and Poly1305 for IETF Protocols.",
    "RFC 7748 — Elliptic Curves for Security (trao đổi khoá X25519).",
    "RFC 8032 — Edwards-Curve Digital Signature Algorithm (chữ ký Ed25519).",
    "A. Shamir, “How to share a secret”, Communications of the ACM, 1979.",
    "BLAKE3 — đặc tả hàm băm mật mã và dẫn xuất khoá theo ngữ cảnh.",
    "Đặc tả định dạng age v1 — định dạng tệp mã hoá mở.",
    "Android Developers — Storage Access Framework và Scoped Storage.",
    "Đặc tả Exif 2.32 (CIPA DC-008) — cấu trúc siêu dữ liệu trong tệp ảnh.",
]:
    bullet(doc, _t)
para(doc,
     "Các văn bản khác của hồ sơ: *02 — Thuyết minh sáng kiến* (bản cô đọng để đọc nhanh) và "
     "*05 — Đề cương chi tiết về sáng kiến* (diễn giải kỹ thuật đầy đủ, mô tả từng chức năng "
     "kèm giao diện, ảnh chụp toàn bộ màn hình và quy trình kiểm thử nghiệm thu).", italic=True)

chu_ky(doc,
       ("XÁC NHẬN CỦA ĐƠN VỊ", ""),
       ("CHỦ NHIỆM SÁNG KIẾN", f"{CHU_NHIEM['cap_bac']} {CHU_NHIEM['ho_ten']}"),
       dia_danh=DIA_DANH_NGAY)

OUT = BASE / "docx" / "04-De-cuong-so-bo-sang-kien.docx"
OUT.parent.mkdir(exist_ok=True)
doc.save(OUT)
print(f"Đã ghi {OUT}")
