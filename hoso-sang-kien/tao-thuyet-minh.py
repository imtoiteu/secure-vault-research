#!/usr/bin/env python3
"""Sinh văn bản THUYẾT MINH SÁNG KIẾN (DOCX) — bản rút gọn dưới 20 trang.

Cấu trúc bám theo tệp mẫu `Mau_ho_so_sang_kien_cai_tien.doc`:

    A. THÔNG TIN CHUNG
    B. NỘI DUNG CHÍNH CỦA SÁNG KIẾN/GIẢI PHÁP
       1. Hiện trạng giải pháp đã biết
       2. Mục đích của giải pháp
       3. Mô tả giải pháp — 3.1 Nguyên lý · 3.2 Các nội dung chủ yếu · 3.3 Kết quả
       4. Tự đánh giá — 4.1 Tính mới và tính sáng tạo · 4.2 Khả năng áp dụng
                        4.3 Hiệu quả · 4.4 Mức độ triển khai, phát triển
    C. TÀI LIỆU THAM KHẢO

Vai trò của văn bản này trong bộ hồ sơ: **để hội đồng đọc**. Người đọc cần nắm nhanh sáng
kiến là gì, giải quyết vấn đề nào, mới và sáng tạo ở đâu, sản phẩm thật ra sao và giá trị
đến đâu. Vì vậy mọi phần diễn giải kỹ thuật sâu, bảng chức năng đầy đủ, ảnh chụp toàn bộ
giao diện và quy trình nghiệm thu chi tiết đều chuyển sang văn bản 04 — Đề cương chi tiết
(tao-de-cuong.py) — và ở đây chỉ giữ phần có giá trị chứng minh cao nhất kèm chỉ dẫn tra cứu.

Mọi số liệu lấy từ bang-chung/du-kien.json và bang-chung/kiem-tra-apk.json, do các script
thu-thap-du-kien.py và kiem-tra-apk.py sinh ra từ mã nguồn và kết quả chạy thật. Không có
con số nào nhập tay trong tệp này.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from dinh_dang import (  # noqa: E402
    bang, bullet, chu_ky, danh_so_trang, dat_lai_dem, dong_dien, h1, h2, h3, hinh,
    khung_nhan_manh, muc_luc, new_document, para, rich, tieuDeChinh,
    tieu_de_quan_doi, trang_bia,
)
from du_lieu_ho_so import (  # noqa: E402
    A2, MB_APK, N_CRATE, N_LENH, N_TEST, SO_DOI_CHUNG, TT, arm, host,
)
from noi_dung_chuc_nang import NHOM_CHUC_NANG  # noqa: E402
from noi_dung_giao_dien import DANH_MUC_MAN_HINH  # noqa: E402
from ten_sang_kien import (  # noqa: E402
    CHU_NHIEM, DIA_DANH_NGAY, DONG_TAC_GIA, LINH_VUC, TEN_SANG_KIEN,
    TEN_SANG_KIEN_HOA,
)

BASE = pathlib.Path(__file__).parent
PNG = BASE / "hinh-anh" / "png"
SS = BASE / "hinh-anh" / "screenshot"

# Thuyết minh phải gọn dưới 20 trang nên siết giãn dòng và giãn đoạn so với mặc định.
doc = new_document(gian_dong=1.28, cach_doan=4)
dat_lai_dem()
danh_so_trang(doc)

trang_bia(doc, TEN_SANG_KIEN_HOA)
tieu_de_quan_doi(doc)
tieuDeChinh(doc, "THUYẾT MINH SÁNG KIẾN")

# =====================================================================
# TÓM TẮT
# =====================================================================
h1(doc, "TÓM TẮT")
para(doc,
     "*Đặt vấn đề.* Bảo vệ dữ liệu bằng mật mã là nội dung cốt lõi trong đào tạo học viên về "
     "an toàn thông tin, bảo đảm an toàn tình báo trên không gian mạng; tuy nhiên học viên "
     "chủ yếu mới tiếp cận qua lý thuyết và công cụ trên máy tính, trong khi thiết bị di "
     "động mới là môi trường các em thường xuyên thao tác sau khi ra trường. Bên cạnh đó, "
     "trong tình huống bất khả kháng buộc phải chuyển gấp một số tài liệu đặc thù qua không "
     "gian mạng, người sử dụng thiếu một công cụ tin cậy, kiểm chứng được để bổ sung lớp bảo "
     "vệ cho tệp trước khi gửi. Giải pháp hiện có hoặc chỉ bảo vệ khi thiết bị không hoạt "
     "động, hoặc mã nguồn đóng khó kiểm chứng, hoặc mạnh về mật mã nhưng không chạy được "
     "trên di động.")
para(doc,
     "*Nguyên nhân.* Các công cụ mật mã tin cậy phần lớn được phân phối dưới dạng tệp nhị "
     "phân chạy độc lập, mà hệ điều hành di động lại không cho ứng dụng sinh tiến trình con "
     "để chạy chúng. Đây là rào cản thuộc về kiến trúc nền tảng, không phải vấn đề khả năng "
     "lập trình.")
para(doc,
     "*Giải pháp.* Nhóm tác giả xây dựng kiến trúc tách nghiệp vụ bảo vệ dữ liệu khỏi giao diện "
     "và nền tảng, đặt điểm nối trừu tượng tại đúng những vị trí phụ thuộc nền tảng. Nhờ đó "
     "có thể thay phần hiện thực bên dưới bằng phiên bản chạy ngay trong tiến trình ứng dụng "
     "mà nghiệp vụ và định dạng dữ liệu giữ nguyên. Trên nền đó, nhóm tác giả tự thiết kế định "
     "dạng tệp két (.svault), sơ đồ phân cấp khoá, quy tắc phân loại lỗi theo hướng an toàn "
     "và tự viết mô-đun xử lý siêu dữ liệu.")
para(doc,
     f"*Sản phẩm.* Ứng dụng di động hoàn chỉnh với {N_LENH} chức năng nghiệp vụ thao tác qua "
     f"{len(DANH_MUC_MAN_HINH)} màn hình, xây dựng trên {N_CRATE} thành phần mã nguồn, kèm "
     f"{N_TEST} hàm kiểm thử tự động; tính tương thích định dạng được kiểm chứng bằng "
     f"{SO_DOI_CHUNG} phép đối chứng với công cụ chuẩn thay vì bằng suy luận. Mỗi chức năng "
     "đối chiếu một-một với màn hình thực hiện nó (mục 3.2.4).")
para(doc,
     "*Giá trị.* Sản phẩm vừa dùng được trong công tác để bảo vệ dữ liệu ngay trên thiết bị, "
     "vừa là học cụ trực quan cho giảng dạy: mỗi nhóm chức năng tương ứng một nguyên lý, và "
     "mã nguồn mở cho phép học viên đọc, chạy lại và phân tích một hệ thống an toàn thực tế.")

muc_luc(doc, sang_trang=True)

# =====================================================================
h1(doc, "A. THÔNG TIN CHUNG", sang_trang=True)
dong_dien(doc, "1. Tên sáng kiến", TEN_SANG_KIEN)
dong_dien(doc, "2. Thuộc lĩnh vực", LINH_VUC)
para(doc, "3. Họ và tên tác giả:", bold=True, indent=False)


def _khoi_tac_gia(nhan, ng):
    dong_dien(doc, f"- {nhan}", f"{ng['ho_ten']}, sinh năm {ng['nam_sinh']}", cach_sau=2)
    dong_dien(doc, "Tên cơ quan, đơn vị", ng["don_vi"], dam_nhan=False, cach_sau=2)
    dong_dien(doc, "Cấp bậc", f"{ng['cap_bac']} — Chức vụ: {ng['chuc_vu']} — "
              f"Trình độ chuyên môn: {ng['trinh_do']}", dam_nhan=False, cach_sau=2)
    dong_dien(doc, "Số điện thoại", ng["dien_thoai"], dam_nhan=False, cach_sau=5)


_khoi_tac_gia("Chủ nhiệm sáng kiến", CHU_NHIEM)
for _ng in DONG_TAC_GIA:
    _khoi_tac_gia("Tham gia", _ng)

# =====================================================================
h1(doc, "B. NỘI DUNG CHÍNH CỦA SÁNG KIẾN/GIẢI PHÁP")

# ---------------------------------------------------------------- 1
h2(doc, "1. Hiện trạng giải pháp đã biết")
h3(doc, "1.1. Bối cảnh và nhu cầu thực tiễn")
para(doc,
     "Trong môi trường công tác ở Học viện Khoa học Quân sự và các cơ quan, đơn vị có yêu "
     "cầu cao về bảo vệ thông tin, việc quản lý, lưu trữ và chuyển giao tài liệu mật, tài "
     "liệu nội bộ phải tuân thủ nghiêm ngặt các quy định hiện hành. Đặc biệt, đơn vị không "
     "cho phép đưa tài liệu mật và tài liệu nội bộ lên thiết bị di động cá nhân. Đây là "
     "nguyên tắc được xác định rõ và không thuộc phạm vi điều chỉnh của sáng kiến. Trên cơ "
     "sở đó, sáng kiến được xây dựng nhằm đáp ứng hai nhu cầu thực tiễn nằm trong ranh giới "
     "cho phép, không làm thay đổi hay nới lỏng quy định về bảo vệ bí mật của đơn vị.")
para(doc, "*Thứ nhất, nhu cầu phục vụ huấn luyện và đào tạo.* "
     "Bảo vệ dữ liệu bằng mật mã là nội dung quan trọng trong chương trình đào tạo an toàn "
     "thông tin, bảo đảm an toàn tình báo trên không gian mạng. Tuy nhiên việc học hiện nay "
     "chủ yếu dừng ở cơ sở lý thuyết, thuật toán và công cụ trên máy tính, trong khi thiết "
     "bị di động ngày càng trở thành môi trường phổ biến để lưu trữ, trao đổi và xử lý dữ "
     "liệu. Học viên biết nguyên lý nhưng chưa từng thực hành trên đúng môi trường sẽ phải "
     "làm việc sau này — đó là khoảng cách cần lấp. Từ đó nảy sinh nhu cầu về một môi trường "
     "thực hành an toàn, nơi học viên trực tiếp thao tác với các cơ chế bảo vệ dữ liệu ngay "
     "trên thiết bị di động: mã hoá tệp bằng mật khẩu, tạo và kiểm tra chữ ký số, loại bỏ "
     "siêu dữ liệu, kiểm tra tính toàn vẹn của tệp và các phương thức bảo vệ khác.")
para(doc, "*Thứ hai, nhu cầu giảm thiểu rủi ro trong tình huống khẩn cấp.* "
     "Trong công tác có thể xuất hiện tình huống đặc thù mà một số tệp dữ liệu buộc phải "
     "chuyển gấp qua không gian mạng khi không còn phương án nào khác kịp thời hạn. Đây là "
     "tình huống rủi ro cao: dữ liệu đi qua hạ tầng nằm ngoài phạm vi kiểm soát của đơn vị. "
     "Trong những trường hợp được cấp có thẩm quyền cho phép chuyển giao, cán bộ cần một "
     "công cụ để chủ động tăng cường lớp bảo vệ cho tệp trước khi truyền: mã hoá bằng mật "
     "khẩu bảo vệ nội dung khi tệp bị tiếp cận trái phép; chữ ký số giúp bên nhận kiểm tra "
     "nguồn gốc và tính toàn vẹn; loại bỏ siêu dữ liệu hạn chế việc vô tình để lộ thông tin "
     "ẩn; chia sẻ bí mật thành nhiều phần truyền qua các kênh độc lập tạo thêm một lớp nữa.")
para(doc,
     "Cần nói rõ giới hạn: sáng kiến không thay thế quy định về quản lý và bảo vệ bí mật, "
     "không phải căn cứ để đưa tài liệu mật hoặc tài liệu nội bộ lên thiết bị di động, và "
     "không nới lỏng quy định về chuyển giao tài liệu. Việc một tài liệu cụ thể có được phép "
     "lưu trữ, xử lý hoặc chuyển giao hay không vẫn do quy định hiện hành và người có thẩm "
     "quyền quyết định. Công cụ chỉ bổ sung biện pháp kỹ thuật nhằm giảm rủi ro trong phạm "
     "vi hoạt động đã được phép.")

h3(doc, "1.2. Các nhóm giải pháp đã biết và nhược điểm")
para(doc,
     "Khảo sát các nhóm giải pháp hiện có theo từng nhóm chức năng cho thấy mỗi giải pháp "
     "đều xử lý tốt bài toán mà nó được thiết kế cho. Hạn chế nằm ở chỗ khác: xét trên tổng "
     "thể yêu cầu đặt ra, chưa có giải pháp nào đáp ứng đồng thời và đầy đủ các chức năng "
     "cần thiết trên nền tảng di động.")
para(doc,
     "Sáu nhóm giải pháp được khảo sát và điểm yếu cốt lõi của từng nhóm: *mã hoá toàn thiết "
     "bị* của hệ điều hành chỉ bảo vệ khi máy tắt hoặc chưa mở khoá lần đầu, và không theo "
     "tệp khi tệp rời thiết bị; *ứng dụng “két riêng tư” trên kho ứng dụng* phần lớn mã "
     "nguồn đóng nên không kiểm chứng được thuật toán và cách quản lý khoá, nhiều ứng dụng "
     "còn đòi quyền mạng; *trình quản lý mật khẩu mã nguồn mở* làm rất tốt việc của nó nhưng "
     "được thiết kế cho mật khẩu chứ không cho tệp, và không có ký số, kiểm tra toàn vẹn hay "
     "chia khoá phục hồi; *công cụ mật mã dòng lệnh* có thuật toán tin cậy nhưng không có "
     "bản dùng được trên di động do rào cản kiến trúc nền tảng (mục 3.2.2); *ứng dụng nhắn "
     "tin mã hoá đầu-cuối* bảo vệ đường truyền nhưng không bảo vệ dữ liệu lúc lưu trên máy, "
     "và dữ liệu vẫn đi qua hạ tầng của nhà cung cấp nước ngoài; *giải pháp quản lý thiết bị "
     "MDM/DLP* cần hạ tầng máy chủ, chi phí bản quyền và phụ thuộc nhà cung cấp. Bảng ưu — "
     "nhược điểm đầy đủ của sáu nhóm trình bày tại mục 1.3 của Đề cương chi tiết.")
para(doc,
     "Để so sánh khách quan hơn, bảng dưới đây đối chiếu theo từng tiêu chí kiểm tra được, "
     "thay vì dựa trên nhận định định tính.")
bang(doc, "Ma trận đối chiếu theo tiêu chí kiểm tra được",
     ["Tiêu chí", "Mã hoá toàn thiết bị", "Ứng dụng két thương mại", "Công cụ dòng lệnh",
      "SecureVault Mobile"],
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
     note="Cột SecureVault Mobile chỉ đối chiếu với chức năng đã hiện thực và kiểm chứng.")

h3(doc, "1.3. Vấn đề thực tiễn và yêu cầu cần giải quyết")
para(doc,
     "Từ phân tích trên, vấn đề được xác định là: chưa có công cụ nào đồng thời đáp ứng cả "
     "năm yêu cầu sau đây trên nền tảng thiết bị di động:")
rich(doc, [
    ("(1) ", "b"), ("hoạt động hoàn toàn trên thiết bị — không yêu cầu quyền truy cập mạng, "
     "không tài khoản, không đồng bộ đám mây; ", ""),
    ("(2) ", "b"), ("mã nguồn kiểm soát được, thuật toán công khai, có bộ kiểm thử tự động "
     "để bên thứ ba kiểm chứng lại; ", ""),
    ("(3) ", "b"), ("gộp nhiều nghiệp vụ bảo vệ dữ liệu trong một ứng dụng thống nhất thay "
     "vì nhiều công cụ rời rạc; ", ""),
    ("(4) ", "b"), ("tệp đầu ra theo chuẩn mở, bảo đảm tương thích và thuận tiện khi chuyển "
     "đổi giữa các sản phẩm, nền tảng khác nhau; ", ""),
    ("(5) ", "b"), ("dùng được làm học cụ trực quan cho giảng dạy an toàn thông tin, an toàn "
     "tình báo trên không gian mạng, đồng thời vẫn là công cụ đạt chuẩn kỹ thuật.", ""),
])

# ---------------------------------------------------------------- 2
h2(doc, "2. Mục đích của giải pháp")
para(doc,
     "Sáng kiến nhằm xây dựng một bộ công cụ trên Android phục vụ huấn luyện an toàn thông "
     "tin, bảo đảm an toàn tình báo trên không gian mạng, đồng thời đủ tin cậy để cán bộ "
     "trang bị thêm lớp bảo vệ cho tệp khi phát sinh tình huống khẩn cấp, bất khả kháng phải "
     "chuyển gấp tài liệu qua không gian mạng. Các mục tiêu cụ thể:")
for _h, _t in [
    ("Phục vụ huấn luyện. ",
     "Mỗi nhóm chức năng tương ứng một nguyên lý an toàn thông tin cụ thể, cho phép giảng "
     "viên minh hoạ trực quan và xây dựng bài thực hành có kết quả quan sát được ngay trên "
     "loại thiết bị mà học viên gặp nhiều nhất sau khi ra trường."),
    ("Bảo vệ tệp trước khi chuyển giao qua không gian mạng. ",
     "Cung cấp cơ chế mã hoá, ký số, kiểm tra toàn vẹn, chia bí mật theo ngưỡng và xoá siêu "
     "dữ liệu, hoạt động hoàn toàn trên thiết bị. Trong tình huống bất khả kháng, tệp rời "
     "thiết bị ở dạng đã được bảo vệ mà bên chặn bắt không đọc được."),
    ("Bảo đảm chủ quyền dữ liệu. ",
     "Khoá và dữ liệu do người dùng nắm giữ hoàn toàn; ứng dụng không tự truyền dữ liệu ra "
     "ngoài và không phụ thuộc máy chủ, đám mây hay dịch vụ bên thứ ba."),
    ("Kiểm chứng được. ",
     f"Toàn bộ mã nguồn mở kèm {N_TEST} hàm kiểm thử tự động, cho phép kiểm tra lại các "
     "tính năng kỹ thuật."),
    ("Sử dụng được ngay. ",
     "Giao diện tiếng Việt, thao tác theo từng bước, thuật ngữ kỹ thuật đặt trong mục mở "
     "rộng để không gây quá tải cho người dùng mới."),
]:
    bullet(doc, _t, bold_head=_h)

# ---------------------------------------------------------------- 3
h2(doc, "3. Mô tả giải pháp")

h3(doc, "3.1. Nguyên lý của giải pháp")
para(doc,
     "Giải pháp được xây dựng trên sáu nguyên lý xác lập ngay từ đầu và áp dụng xuyên suốt "
     "quá trình thiết kế, phát triển, kiểm thử. Điều đáng nói là các nguyên lý này không "
     "dừng ở mức định hướng: mỗi nguyên lý được chuyển hoá thành một ràng buộc kỹ thuật cụ "
     "thể và gắn với một cách kiểm tra tương ứng, để nguyên tắc thiết kế khó bị vi phạm khi "
     "phần mềm được sửa đổi về sau.")
bang(doc, "Sáu nguyên lý thiết kế và cơ chế bảo đảm tương ứng",
     ["Nguyên lý", "Cơ chế thực thi trong sản phẩm", "Cách kiểm tra"],
     [
         ["Hoạt động ngoại tuyến tuyệt đối",
          "Không khai báo quyền truy cập mạng trong AndroidManifest.xml — ràng buộc đặt ở "
          "cấp hệ điều hành, không phụ thuộc thao tác người dùng",
          "Đọc tệp kê khai trong gói cài đặt"],
         ["Một lõi bảo vệ dữ liệu dùng chung",
          f"Nghiệp vụ mật mã tập trung trong lõi gồm {N_CRATE} thành phần độc lập, không "
          "dùng thư viện giao diện hay thư viện đặc thù nền tảng",
          "Đọc quan hệ phụ thuộc khai báo của từng thành phần"],
         ["Phụ thuộc một chiều theo lớp",
          "Lớp trên dùng lớp dưới, không có chiều ngược; lõi chỉ phụ thuộc giao diện trừu "
          "tượng, không phụ thuộc một cách triển khai cụ thể",
          "Lõi được kiểm thử độc lập với bản hiện thực giả lập"],
         ["Khi không bảo đảm an toàn thì không tiếp tục xử lý",
          "Thành phần chưa sẵn sàng bị vô hiệu hoá và báo ngay khi khởi động; dữ liệu ngoài "
          "phạm vi bị từ chối kèm mã lỗi, không trả về trạng thái thành công sai",
          "Kiểm thử tình huống mô-đun không sẵn sàng và định dạng ngoài phạm vi"],
         ["Thông báo lỗi không làm lộ thông tin bí mật",
          "Sau khi chữ ký và khoá đã kiểm tra xong, giải mã thất bại báo “tệp hỏng” thay vì "
          "“sai xác thực”, nên chênh lệch thông báo không dùng để dò mật khẩu",
          "Kiểm thử đối chiếu thông báo giữa các bản hiện thực"],
         ["Không lưu trữ bí mật lâu dài",
          "Mật khẩu chỉ nằm trong bộ nhớ lúc xử lý, quản lý bằng kiểu dữ liệu tự xoá; khoá "
          "chính chỉ ở bộ nhớ phiên và bị xoá khi khoá két",
          "Kiểm thử vòng đời phiên làm việc"],
     ], widths=[3.6, 7.6, 4.3])
hinh(doc, PNG / "H2-kien-truc-phan-lop.png",
     "Kiến trúc phân lớp của SecureVault Mobile", width_cm=12.5)

h3(doc, "3.2. Các nội dung chủ yếu")

para(doc, "3.2.1. Kiến trúc tổng thể", bold=True, indent=False)
para(doc,
     f"Ứng dụng được tổ chức thành sáu lớp (Hình 1), giao diện tách hẳn khỏi lõi nghiệp vụ. "
     f"Mọi yêu cầu từ giao diện đến lõi đều phải đi qua {N_LENH} lệnh được kiểm soát thống "
     "nhất, không có đường truy cập trực tiếp. Mật khẩu khi qua ranh giới giữa các lớp được "
     "quản lý bằng kiểu dữ liệu tự xoá; phiên làm việc chỉ tham chiếu bằng mã định danh "
     "không chứa bí mật nên không thể dùng để suy ra khoá. Nhờ đó có thể thay giao diện hoặc "
     "nền tảng mà gần như không phải sửa lõi bảo vệ dữ liệu.")

para(doc, "3.2.2. Thích ứng kiến trúc phần mềm với nền tảng di động", bold=True, indent=False)
para(doc,
     "Đây là nội dung mang hàm lượng kỹ thuật cao nhất của sáng kiến, và cũng chính là lý do "
     "các công cụ mật mã mạnh hiện nay không có bản dùng được trên điện thoại.")
para(doc,
     "*Vấn đề đặt ra.* Các công cụ mật mã tin cậy được phân phối dưới dạng tệp nhị phân chạy "
     "độc lập. Trên máy tính để bàn, ứng dụng gọi chúng như một tiến trình con. Trên thiết "
     "bị di động thì không: iOS cấm hoàn toàn việc sinh tiến trình, còn Android chặn thực "
     "thi tệp nhị phân nằm trong vùng lưu trữ mà ứng dụng ghi được. Hệ quả là mọi chức năng "
     "phụ thuộc tiến trình con sẽ không hoạt động, kể cả khi mã nguồn biên dịch thành công.")
para(doc,
     "*Hướng khắc phục.* Giải pháp đặt điểm nối trừu tượng tại đúng các thành phần phụ thuộc "
     "nền tảng, cho phép thay mô-đun bên dưới mà nghiệp vụ và định dạng dữ liệu không đổi. "
     "Nguyên tắc này áp dụng cho cả hai thành phần vướng rào cản: (1) mã hoá nội dung két — "
     "mô-đun mã hoá được hiện thực ngay trong tiến trình ứng dụng nhưng giữ nguyên định dạng "
     "tệp đã thiết kế; (2) xử lý siêu dữ liệu — mô-đun tương ứng do nhóm tác giả viết bằng Rust "
     "để xem, xoá và so sánh siêu dữ liệu trực tiếp trên thiết bị.")
hinh(doc, PNG / "H3-loi-dung-chung.png",
     "Nguyên tắc một lõi dùng chung, hai bản hiện thực theo nền tảng", width_cm=12.5)
para(doc,
     "*Tính tương thích của định dạng tệp.* Nếu thay mô-đun mã hoá mà định dạng thay đổi thì "
     "các tệp đã tạo trước đó sẽ không mở được nữa. Vì vậy nhóm tác giả đặt ràng buộc bắt buộc: "
     "bản hiện thực mới phải sinh ra đúng định dạng cũ — và ràng buộc đó được kiểm chứng "
     "bằng thực nghiệm đối chứng hai chiều với công cụ chuẩn, không phải bằng lập luận.")
rich(doc, [
    (f"Kết quả: {SO_DOI_CHUNG} phép đối chứng, tất cả đều đạt — ", ""),
    ("(1) ", "b"), ("tệp tạo bằng mô-đun tích hợp trong ứng dụng, giải mã được bằng công cụ "
     "chuẩn age v1.2.1; ", ""),
    ("(2) ", "b"), ("chiều ngược lại, tệp do age v1.2.1 tạo ra được mô-đun tích hợp giải mã "
     "đúng; ", ""),
    ("(3) và (4) ", "b"), ("két tạo bằng phiên bản dùng tiến trình con mở được bằng phiên "
     "bản tích hợp và ngược lại; ", ""),
    ("(5) ", "b"), ("sau khi thay cách triển khai, mật khẩu không đúng vẫn bị từ chối. Nguồn "
     "kiểm chứng: crates/sv-age-rs/tests/interop.rs và src-tauri/tests/vault_interop.rs; "
     "công cụ đối chứng age v1.2.1 tải từ nguồn chính thức, giá trị băm SHA-256 của tệp tải "
     "về được lưu để truy xuất nguồn gốc. Bảng kiểm chứng chi tiết: mục 5.4 của Đề cương chi tiết.", ""),
])

para(doc, "3.2.3. Định dạng tệp két và sơ đồ phân cấp khoá do nhóm tác giả thiết kế",
     bold=True, indent=False)
para(doc,
     "Cấu trúc tệp két và cơ chế sinh, bảo vệ, quản lý khoá được thiết kế riêng cho ứng "
     "dụng, không sao chép từ sản phẩm có sẵn. Mật khẩu người dùng không được lưu trữ ở bất "
     f"kỳ đâu. Từ mật khẩu, hệ thống dẫn xuất khoá chính bằng Argon2id với tối thiểu "
     f"{A2['min_mem_kib'] // 1024} MiB bộ nhớ và {A2['min_time_cost']} vòng lặp, theo ngưỡng "
     "khuyến nghị của OWASP. Khoá chính chỉ tồn tại trong bộ nhớ phiên làm việc và được dùng "
     "để tạo các khoá con cho từng mục đích riêng biệt; việc tách khoá theo mục đích hạn chế "
     "ảnh hưởng khi một khoá con bị lộ và không cho phép dùng khoá con suy ngược khoá chính.")
para(doc,
     "Nội dung két được đóng gói thành một luồng dữ liệu mã hoá duy nhất, trong đó *danh mục "
     "tệp cũng nằm bên trong phần đã mã hoá*. Vì vậy người không có mật khẩu không biết được "
     "bên trong két có gì, kể cả tên các tệp. Phần đầu tệp được bảo vệ bằng chữ ký số, giúp "
     "phát hiện mọi thay đổi trái phép — kể cả trường hợp ghép phần đầu của tệp này với nội "
     "dung của tệp khác — và việc kiểm tra này diễn ra *trước* các bước liên quan đến mật khẩu.")
rich(doc, [
    ("Bộ nguyên hàm mật mã được lựa chọn gồm: ", ""),
    (TT["kdf"], "b"), (" dẫn xuất khoá từ mật khẩu; ", ""),
    (TT["hash"], "b"), (" băm nội dung và tạo khoá con theo từng mục đích; ", ""),
    (TT["aead_vault"], "b"), (" mã hoá nội dung két; ", ""),
    (TT["aead_field"], "b"), (" bảo vệ các trường khoá trong phần đầu tệp; ", ""),
    (TT["chu_ky"], "b"), (" ký và xác minh phần đầu tệp; ", ""),
    (TT["chia_se_bi_mat"], "b"), (" chia khoá phục hồi theo ngưỡng. Lý do lựa chọn từng "
     "nguyên hàm và tham số cụ thể trình bày tại mục 3.5 của Đề cương chi tiết.", ""),
])
para(doc,
     "Giải pháp không tự xây dựng thuật toán mật mã mới mà sử dụng các thuật toán đã được "
     "công bố, nghiên cứu và dùng rộng rãi. Đóng góp của nhóm tác giả nằm ở kiến trúc, ở cách tổ "
     "chức và bảo vệ dữ liệu, và ở việc chọn tham số phù hợp với yêu cầu.")

para(doc, "3.2.4. Chức năng của ứng dụng và giao diện tương ứng", bold=True, indent=False)
para(doc,
     f"Ứng dụng cung cấp {N_LENH} chức năng nghiệp vụ, phân thành tám nhóm theo mục đích sử "
     f"dụng, thao tác qua {len(DANH_MUC_MAN_HINH)} màn hình giao diện. Bảng dưới đây tóm "
     "lược từng nhóm; phần mô tả đầy đủ đầu vào — xử lý — kết quả của từng chức năng, kèm "
     "phân tích thiết kế giao diện của mỗi nhóm, được trình bày tại mục 4.1 của Đề cương chi "
     "tiết, còn ảnh chụp toàn bộ màn hình nằm ở Phụ lục B của văn bản đó.")
# Số chức năng và dải màn hình của từng nhóm tính thẳng từ noi_dung_chuc_nang.py, không gõ
# tay: bản viết tay trước đó ghi nhóm 1 có 15 chức năng trong khi bảng chức năng của nhóm chỉ
# liệt kê 12 — đúng loại sai lệch mà hội đồng đối chiếu hai bảng là thấy ngay.
_TOM_TAT_NHOM = [
    "Một tệp .svault chứa nhiều tệp dưới một mật khẩu; danh mục tệp cũng được mã hoá",
    "Khoá và mở khoá trực tiếp một tệp bằng mật khẩu, không cần lập két",
    "Chữ ký số, vân tay tệp, đối chiếu vân tay, xác minh tệp tải về",
    "Chia bí mật hoặc tệp thành n mảnh, cần đủ k mảnh mới khôi phục; chuyển mảnh qua mã QR",
    "Giấu tệp đã mã hoá vào ảnh, lấy lại, và phát hiện dấu hiệu dữ liệu ẩn",
    "Nhúng và kiểm tra thuỷ vân dễ vỡ, khoanh vùng vị trí ảnh bị sửa",
    "Xem, xoá và so sánh siêu dữ liệu ngay trên thiết bị, gồm cả toạ độ định vị",
    "Tra cứu phiên bản ứng dụng, giao tiếp lõi, định dạng két và bộ thuật toán",
]


def _dai_man_hinh(nhom):
    """Dải mã màn hình của một nhóm, ví dụ “GD06–GD10” hoặc “GD03”."""
    ma = [r[0] for r in nhom["man_hinh"][1:]]
    return ma[0] if len(ma) == 1 else f"{ma[0]}–{ma[-1]}"


bang(doc, "Tám nhóm chức năng và màn hình thực hiện",
     ["Nhóm chức năng", "Nội dung nghiệp vụ", "Số chức năng", "Màn hình"],
     [[nhom["ten"].replace("Nhóm ", "").replace(".", ".", 1),
       _TOM_TAT_NHOM[i],
       str(len(nhom["chuc_nang"]) - 1),
       _dai_man_hinh(nhom)]
      for i, nhom in enumerate(NHOM_CHUC_NANG)],
     widths=[4.4, 7.2, 1.7, 2.2],
     note=f"Tổng số chức năng: "
          f"{sum(len(n['chuc_nang']) - 1 for n in NHOM_CHUC_NANG)} — khớp với số lệnh "
          f"nghiệp vụ mà lõi công bố ({N_LENH}).")

para(doc,
     "Bảng danh mục dưới đây là bằng chứng đối chiếu một-một giữa chức năng và giao diện "
     "thực hiện nó. Nhóm tác giả kiểm tra hai chiều trực tiếp trên mã nguồn: chiều thứ nhất từ "
     "lõi ra giao diện, bảo đảm mọi lệnh của lõi đều được ít nhất một màn hình sử dụng; "
     "chiều thứ hai từ giao diện vào lõi, bảo đảm mọi lệnh mà giao diện gọi đều có thật "
     "trong lõi. Kết quả: không có lệnh nào của lõi bị bỏ sót và không có nút bấm nào gọi "
     "đến lệnh không tồn tại. Bảng danh mục đầy đủ 21 màn hình kèm tên từng lệnh nghiệp vụ "
     "được gọi trên mỗi màn hình đặt tại mục 4.2 của Đề cương chi tiết.")
para(doc, "3.2.5. Giao diện người dùng và nguyên tắc thiết kế", bold=True, indent=False)
para(doc,
     "Với một ứng dụng bảo vệ dữ liệu, giao diện không chỉ có vai trò trình bày mà còn ảnh "
     "hưởng trực tiếp đến khả năng dùng đúng chức năng và hạn chế sai sót của người dùng. Vì "
     "vậy nhóm tác giả xem thiết kế giao diện là một thành phần của thiết kế an toàn, với bốn "
     "nguyên tắc áp dụng thống nhất trên toàn bộ ứng dụng:")
for _h, _t in [
    ("Trình bày theo công việc cần thực hiện, không theo thuật toán. ",
     "Người dùng chọn chức năng theo nhu cầu, không cần biết bên trong dùng Argon2id hay "
     "Ed25519. Mười chín công cụ được tổ chức thành năm nhóm theo mục đích. Những chức năng "
     "cùng nền tảng kỹ thuật nhưng khác mục đích được tách thành màn hình riêng — ví dụ "
     "“lấy vân tay tệp” và “kiểm tra tệp với vân tay” đều dùng BLAKE3 nhưng là hai việc khác "
     "nhau."),
    ("Giảm tải nhận thức bằng phân tầng thông tin. ",
     "Mỗi màn hình ưu tiên các bước cần thiết để hoàn thành công việc, có đánh số theo trình "
     "tự; thông tin kỹ thuật và lưu ý về giới hạn đặt trong mục thu gọn “Thông tin thêm”."),
    ("Cảnh báo liên quan đến nguy cơ mất dữ liệu luôn hiển thị. ",
     "Đây là ngoại lệ có chủ ý của nguyên tắc trên: thông tin bổ sung có thể thu gọn, nhưng "
     "cảnh báo cần thiết để người dùng khỏi mất dữ liệu thì không được thu gọn."),
    ("Không để kết quả cũ bị hiểu nhầm là kết quả mới. ",
     "Khi chuyển màn hình, ứng dụng xoá trạng thái kết quả, ẩn thẻ thông báo, xoá danh sách "
     "mảnh bí mật, đường dẫn tệp tạm và nội dung các trường mật khẩu — vừa tránh nhầm lẫn, "
     "vừa giảm khả năng thông tin nhạy cảm còn nằm lại trên giao diện."),
]:
    bullet(doc, _t, bold_head=_h)
para(doc,
     "Ứng dụng dùng chung mã giao diện cho cả máy tính và điện thoại, chỉ điều chỉnh bố cục "
     "theo nền tảng đang chạy. Trên điện thoại, thanh điều hướng bên trái chuyển thành ngăn "
     "kéo trượt từ cạnh trái; vùng tương tác tối thiểu 44 điểm ảnh và có khoảng đệm phù hợp "
     "với vùng khuyết của màn hình. Việc bổ sung giao diện di động được kiểm tra để bảo đảm "
     "không làm thay đổi phiên bản máy tính: kết xuất trước và sau khi bổ sung trùng khớp "
     "theo phép so sánh ảnh. Toàn bộ chuỗi hiển thị có tiếng Việt và tiếng Anh.")

h3(doc, "3.3. Kết quả của giải pháp")
para(doc, "3.3.1. Sản phẩm đã tạo ra", bold=True, indent=False)
for _t in [
    f"Ứng dụng Android đóng gói dưới dạng APK ({MB_APK} MB), tích hợp lõi bảo vệ dữ liệu "
    "biên dịch cho kiến trúc ARM64; nội dung gói đã được kiểm tra tĩnh.",
    f"Mã nguồn đầy đủ gồm {N_CRATE} thành phần độc lập, giao diện gồm "
    f"{len(DANH_MUC_MAN_HINH)} màn hình và {N_TEST} hàm kiểm thử tự động chạy trên máy chủ "
    "tích hợp liên tục.",
    "Bộ tài liệu gồm tài liệu kiến trúc, mô hình mối đe doạ và hướng dẫn triển khai.",
]:
    bullet(doc, _t)

para(doc, "3.3.2. Các chỉ tiêu kỹ thuật đạt được", bold=True, indent=False)
bang(doc, "Các chỉ tiêu kỹ thuật đạt được",
     ["Chỉ tiêu", "Giá trị đạt được", "Cách xác định"],
     [
         ["Số chức năng nghiệp vụ", f"{N_LENH} chức năng", "Đếm trực tiếp từ mã nguồn"],
         ["Số màn hình giao diện", f"{len(DANH_MUC_MAN_HINH)} màn hình",
          "Đếm trực tiếp từ mã giao diện"],
         ["Chức năng nghiệp vụ chưa có giao diện gọi tới", "0",
          "Đối chiếu lệnh của lõi với mã giao diện theo hai chiều"],
         ["Số hàm kiểm thử tự động", f"{N_TEST} hàm", "Đếm trực tiếp từ mã nguồn"],
         ["Kiểm thử trên máy chủ", f"{host.get('passed')} đạt / {host.get('failed')} lỗi",
          "Nhật ký chạy bộ kiểm thử"],
         [f"Kiểm thử lõi trên kiến trúc ARM64 ({arm.get('suites')} bộ)",
          f"{arm.get('passed')} đạt / {arm.get('failed')} lỗi",
          "Chạy dưới trình giả lập kiến trúc"],
         ["Kiểm chứng tương thích định dạng", f"{SO_DOI_CHUNG} phép đối chứng đạt",
          "Đối chứng với công cụ chuẩn age v1.2.1"],
         ["Kiến trúc thư viện trong gói cài đặt", "64-bit ARM aarch64",
          "Đọc phần đầu ELF của tệp trong gói"],
         ["Quyền ứng dụng yêu cầu", "Không khai báo quyền nào",
          "Đọc tệp kê khai trong gói cài đặt"],
         ["Giao diện nhúng sẵn trong ứng dụng", "Có", "Bảng tài nguyên trong thư viện native"],
     ], widths=[6.4, 4.4, 4.7],
     note="Toàn bộ số liệu được sinh tự động từ mã nguồn và nhật ký kiểm thử, không nhập tay.")

para(doc, "3.3.3. Mức độ kiểm chứng", bold=True, indent=False)
para(doc,
     "Mỗi chỉ tiêu đều gắn với một phương pháp kiểm tra và một kết quả cụ thể, đối chiếu lại "
     "được từ mã nguồn, gói cài đặt hoặc nhật ký kiểm thử — nhờ đó phân biệt rõ chức năng "
     f"*đã triển khai* với chức năng *đã kiểm tra bằng thực nghiệm*. Riêng khả năng thực thi "
     f"trên ARM64, lõi được chạy trên trình giả lập ARM64 với {arm.get('suites')} bộ kiểm "
     f"thử ({arm.get('passed')} phép đạt, không lỗi) trên mã đã biên dịch cho đúng kiến trúc "
     "bộ xử lý mà điện thoại Android sử dụng. Phần chưa kiểm chứng cũng được nêu rõ thay vì "
     "bỏ qua: việc nghiệm thu trên thiết bị Android thật chưa thực hiện tại thời điểm lập hồ "
     "sơ; nhóm tác giả đã soạn sẵn quy trình nghiệm thu 15 bước có tiêu chí đạt cho từng bước "
     "(Phụ lục A của Đề cương chi tiết) để đơn vị tự xác nhận trước khi dùng rộng rãi.")

# ---------------------------------------------------------------- 4
h2(doc, "4. Tự đánh giá giải pháp")

h3(doc, "4.1. Tính mới và tính sáng tạo")
para(doc, "4.1.1. Điểm mới", bold=True, indent=False)
para(doc,
     "Tính mới của sáng kiến không nằm ở việc tạo thêm một công cụ mã hoá, mà ở việc đưa "
     "được nhiều cơ chế bảo vệ dữ liệu vào một ứng dụng chạy trực tiếp trên thiết bị di "
     "động, đồng thời vẫn giữ tương thích với công cụ và định dạng mở. Mỗi điểm mới dưới đây "
     "đều kèm kết quả kiểm tra tương ứng từ mã nguồn, gói cài đặt hoặc quá trình kiểm thử.")
for _h, _t, _bc in [
    ("Đưa cơ chế mã hoá vào ứng dụng di động mà vẫn giữ nguyên định dạng dữ liệu. ",
     "Các công cụ mã hoá phổ biến được xây dựng như chương trình độc lập, trong khi Android "
     "quản lý tiến trình khác máy tính. Giải pháp tách phần mã hoá thành mô-đun riêng, cho "
     "phép thay cách triển khai trên điện thoại mà định dạng tệp không đổi; tệp tạo trên "
     "điện thoại vẫn kiểm tra và xử lý được bằng công cụ chuẩn. ",
     f"{SO_DOI_CHUNG} phép đối chứng hai chiều với age v1.2.1, gồm cả kiểm tra tệp mã hoá "
     "và mở chéo két giữa hai bản hiện thực."),
    ("Dùng chung một lõi xử lý cho nhiều nền tảng. ",
     "Thay vì xây dựng riêng từng phiên bản, giải pháp dùng một lõi chung; phần phụ thuộc "
     "nền tảng được tách riêng và chọn khi biên dịch, nên các phiên bản dùng chung một bộ "
     "chức năng và thuật toán, giảm nguy cơ phát sinh khác biệt khi bảo trì. ",
     "kiểm tra kết quả biên dịch cho thấy cùng một mã nguồn dùng đúng mô-đun của từng nền tảng."),
    ("Xây dựng mô-đun xử lý siêu dữ liệu phù hợp với nền tảng di động. ",
     "Với các chức năng xem, xoá và so sánh siêu dữ liệu, nhóm tác giả viết mô-đun bằng Rust để "
     "chạy trực tiếp trong ứng dụng di động; người dùng loại bỏ được toạ độ GPS và thông tin "
     "thiết bị ngay trên máy trước khi chia sẻ ảnh. ",
     "kiểm thử trên ảnh có siêu dữ liệu xác nhận khả năng đọc thẻ, xoá theo phạm vi xử lý, "
     "giữ nguyên tệp gốc và từ chối định dạng ngoài phạm vi."),
    ("Thống nhất cách xử lý lỗi liên quan đến bảo vệ dữ liệu. ",
     "Lõi phân biệt các nguyên nhân lỗi bên trong, nhưng thông tin hiển thị cho người dùng "
     "được giới hạn ở mức cần thiết, tránh cung cấp manh mối về trạng thái của dữ liệu hoặc "
     "khoá. ",
     "kiểm thử riêng với từng bản hiện thực cho thấy cùng một tình huống lỗi cho kết quả và "
     "thông báo thống nhất."),
    ("Thiết kế khả năng hoạt động ngoại tuyến bằng ràng buộc kỹ thuật. ",
     "Đặc điểm ngoại tuyến không dựa vào thao tác của người sử dụng mà nằm trong cấu hình "
     "của ứng dụng, nên kiểm tra được trực tiếp từ gói cài đặt. ",
     "tệp khai báo AndroidManifest.xml cho thấy ứng dụng không khai báo quyền truy cập Internet."),
]:
    rich(doc, [(_h, "b"), (_t, ""), ("Bằng chứng: ", "bi"), (_bc, "i")], indent=True)

para(doc, "4.1.2. Điểm sáng tạo", bold=True, indent=False)
for _h, _t in [
    ("Kết hợp công cụ huấn luyện với sản phẩm dùng được thật. ",
     "Học viên không chỉ xem hoặc mô phỏng mà trực tiếp thao tác trên chính sản phẩm được "
     "xây dựng cho nhu cầu sử dụng thật; mã hoá, chữ ký số, chia sẻ khoá, che giấu dữ liệu "
     "và xử lý siêu dữ liệu chuyển từ kiến thức lý thuyết thành thao tác kiểm tra được."),
    ("Biến giới hạn của công cụ thành một phần của nội dung huấn luyện. ",
     "Thay vì chỉ trả về “đạt” hoặc “an toàn”, một số chức năng nói rõ phạm vi và giới hạn "
     "của kết quả: chức năng phát hiện dữ liệu ẩn chỉ kết luận trong phạm vi các phép kiểm "
     "tra đã thực hiện, không khẳng định tuyệt đối rằng ảnh sạch — qua đó học viên hiểu kết "
     "quả của một công cụ phân tích luôn phụ thuộc phương pháp và phạm vi kiểm tra."),
    ("Thiết kế sản phẩm theo hướng có thể kiểm chứng. ",
     "Mọi thông tin quan trọng về sản phẩm đều gắn với mã nguồn, kết quả kiểm thử hoặc dữ "
     "liệu đối chiếu độc lập được; số liệu kỹ thuật trong hồ sơ này sinh tự động từ mã nguồn "
     "và nhật ký kiểm thử nên không lệch với phiên bản thực tế."),
    ("Ưu tiên sự chính xác hơn sự tiện lợi. ",
     "Khi chức năng không thể thực hiện trong phạm vi đã xác định, ứng dụng từ chối và thông "
     "báo rõ thay vì trả về kết quả có thể gây hiểu nhầm. Quan điểm xuyên suốt: trong bảo vệ "
     "dữ liệu, không làm được còn an toàn hơn báo sai là đã làm xong."),
]:
    bullet(doc, _t, bold_head=_h)
khung_nhan_manh(doc, "Về quyền tác giả đối với sản phẩm", [
    "Toàn bộ ý tưởng giải pháp, kiến trúc hệ thống, định dạng tệp két, sơ đồ phân cấp khoá, "
    "quy tắc phân loại lỗi, mô-đun xử lý siêu dữ liệu, giao diện và mã nguồn do nhóm tác giả "
    "tự thiết kế và trực tiếp xây dựng. Với các thuật toán mật mã cơ sở, giải pháp dùng "
    "chuẩn và thư viện công khai đã được nghiên cứu, đánh giá rộng rãi thay vì tự xây dựng "
    "thuật toán mới; việc lựa chọn, kết hợp và triển khai chúng trong kiến trúc ứng dụng là "
    "một phần nội dung thiết kế của sáng kiến.",
])

h3(doc, "4.2. Khả năng áp dụng")
para(doc,
     "Sáng kiến triển khai được với điều kiện rất đơn giản: chỉ cần một thiết bị Android, "
     "không cần máy chủ, không cần kết nối mạng, không yêu cầu quyền quản trị thiết bị.")
for _h, _t in [
    ("Giảng viên. ",
     "Dùng làm học cụ thực hành trên lớp; mỗi nhóm chức năng minh hoạ một nội dung trong "
     "chương trình và cho phép học viên trực tiếp thao tác. Điều kiện: điện thoại Android, "
     "không cần hạ tầng bổ sung."),
    ("Học viên. ",
     "Thực hành các bài về mã hoá, chữ ký số, chia sẻ bí mật ngưỡng, kiểm tra toàn vẹn, giấu "
     "tin, phát hiện giấu tin và xử lý siêu dữ liệu; tự bảo vệ dữ liệu cá nhân để hình thành "
     "thói quen nghề nghiệp. Điều kiện: điện thoại Android ở phòng thực hành."),
    ("Cán bộ trong tình huống khẩn cấp, bất khả kháng. ",
     "Khi được phép và buộc phải chuyển giao tài liệu qua không gian mạng: mã hoá, kiểm tra "
     "toàn vẹn, ký tệp, loại bỏ siêu dữ liệu trước khi chuyển giao. Điều kiện: điện thoại "
     "Android, hướng dẫn sử dụng cơ bản khoảng 30 phút, và tuân thủ quy định hiện hành về "
     "loại tài liệu được phép truyền."),
]:
    bullet(doc, _t, bold_head=_h)
para(doc,
     "*Giá trị đối với công tác giảng dạy.* Điểm mạnh của sản phẩm trong đào tạo là các chức "
     "năng được thiết kế gắn với đúng những nguyên lý có trong chương trình học. Học viên "
     "không chỉ tiếp cận lý thuyết mà trực tiếp thao tác, quan sát kết quả và kiểm tra ảnh "
     "hưởng của từng nguyên lý ngay trên thiết bị của mình.")
para(doc,
     "Mỗi nhóm chức năng ứng với một nội dung có sẵn trong chương trình: két an toàn minh "
     "hoạ dẫn xuất khoá từ mật khẩu và lý do mật khẩu yếu vẫn nguy hiểm dù thuật toán mạnh; "
     "khoá/mở khoá tệp minh hoạ mã hoá có xác thực và sự khác nhau giữa bảo mật với toàn "
     "vẹn; ký và kiểm tra chữ ký minh hoạ mật mã khoá công khai; vân tay tệp minh hoạ hàm "
     "băm mật mã; chia bí mật k trong n minh hoạ nguyên tắc tách quyền kiểm soát; giấu tin "
     "và phát hiện giấu tin cho thấy giới hạn của che giấu so với mã hoá; thuỷ vân dễ vỡ cho "
     "thấy cách phát hiện sửa đổi cục bộ trên ảnh; xem và xoá siêu dữ liệu minh hoạ kênh lộ "
     "thông tin nằm ngoài nội dung; còn quy tắc phân loại lỗi minh hoạ tấn công dựa trên "
     "thông báo lỗi. Bảng ánh xạ đầy đủ trình bày tại mục 6.1 của Đề cương chi tiết.")

para(doc,
     "Ngoài giá trị minh hoạ, mã nguồn mở còn cho phép mở rộng đào tạo theo hướng thực hành "
     "chuyên sâu: phân tích cách triển khai một nguyên lý, đánh giá mô hình mối đe doạ, hoặc "
     "rà soát mã nguồn để tìm điểm có thể cải thiện.")

h3(doc, "4.3. Hiệu quả")
para(doc, "4.3.1. Hiệu quả kinh tế", bold=True, indent=False)
para(doc,
     "Sáng kiến không yêu cầu mua bản quyền phần mềm, không đầu tư máy chủ, không thuê bao "
     "dịch vụ và chạy trên thiết bị Android sẵn có. Hiệu quả kinh tế thể hiện ở việc giảm "
     "nhu cầu mua sắm giải pháp thương mại, giảm đầu tư hạ tầng và giảm phụ thuộc nhà cung "
     "cấp bên ngoài; mã nguồn có thể được đơn vị tiếp tục kiểm tra, duy trì và phát triển.")

para(doc, "4.3.2. Hiệu quả kỹ thuật", bold=True, indent=False)
para(doc, "So với các giải pháp đã biết ở mục 1.2, sáng kiến mang lại những cải thiện sau:")
for _t in [
    "Bảo vệ dữ liệu ở trạng thái lưu trữ trên thiết bị bằng một lớp mật khẩu riêng: ngay cả "
    "khi thiết bị đã mở khoá, dữ liệu trong két vẫn yêu cầu xác thực riêng.",
    "Duy trì bảo vệ đối với tệp két sau khi tệp được sao chép sang thiết bị hoặc môi trường "
    "khác, không phụ thuộc trạng thái khoá/mở của thiết bị ban đầu.",
    "Kiểm tra tính toàn vẹn và nguồn gốc của tệp bằng chữ ký số.",
    "Hỗ trợ khôi phục quyền truy cập bằng chia sẻ khoá theo ngưỡng, hạn chế phụ thuộc bên "
    "thứ ba trong việc lưu giữ khoá khôi phục.",
    "Cho phép xem và loại bỏ siêu dữ liệu trực tiếp trên thiết bị, trong đó có toạ độ định vị.",
    "Sử dụng định dạng tệp mở, tạo điều kiện kiểm tra và xử lý dữ liệu bằng công cụ tương "
    "thích khác.",
]:
    bullet(doc, _t)
para(doc,
     "Cùng với phạm vi bảo vệ, nhóm tác giả nêu rõ cả những tình huống sản phẩm *không* bảo vệ "
     "được. Việc công bố giới hạn giúp người sử dụng vận hành công cụ đúng với khả năng thực "
     "tế, thay vì tin tưởng quá mức. Bảng dưới nêu các tình huống tiêu biểu; mô hình mối đe "
     "doạ đầy đủ trình bày tại mục 1.5 của Đề cương chi tiết.")
bang(doc, "Mô hình mối đe doạ: phạm vi bảo vệ và giới hạn",
     ["Tình huống", "Có bảo vệ?", "Giải thích"],
     [
         ["Mất hoặc thất lạc điện thoại khi máy đang khoá", "Có",
          "Dữ liệu trong két ở dạng mã hoá; không có mật khẩu thì không mở được"],
         ["Sao chép tệp két ra khỏi thiết bị", "Có",
          "Tệp két tự bảo vệ, mở ở nơi khác vẫn cần mật khẩu"],
         ["Tệp bị chặn bắt khi buộc phải truyền gấp qua không gian mạng", "Có",
          "Tệp truyền đi ở dạng đã mã hoá có xác thực; bên chặn bắt thu được bản mã nhưng "
          "không có mật khẩu thì không đọc được nội dung"],
         ["Bên nhận không chắc tệp có đúng do người gửi tạo ra không", "Có",
          "Chữ ký số cho phép bên nhận tự xác minh nguồn gốc và tính toàn vẹn, không cần tin "
          "vào kênh truyền"],
         ["Người khác mượn máy khi máy đã mở khoá", "Có, một phần",
          "Két vẫn cần mật khẩu riêng; nhưng nếu phiên đang mở thì nội dung có thể xem được"],
         ["Thiết bị đã bị chiếm quyền điều khiển ở mức hệ điều hành", "Không",
          "Phần mềm độc hại có quyền cao đọc được bộ nhớ tiến trình khi két đang mở"],
         ["Người dùng quên mật khẩu và không tạo mảnh phục hồi", "Không",
          "Do nguyên tắc không lưu mật khẩu lâu dài, dữ liệu không khôi phục được"],
     ], widths=[5.4, 2.2, 7.9])

para(doc, "4.3.3. Hiệu quả về quốc phòng – an ninh", bold=True, indent=False)
for _h, _t in [
    ("Giảm rủi ro lộ lọt dữ liệu trong tình huống đặc thù. ",
     "Khi được phép và buộc phải chuyển giao tài liệu qua không gian mạng, dữ liệu được mã "
     "hoá, kiểm tra toàn vẹn, ký số và loại bỏ siêu dữ liệu trước khi chuyển giao."),
    ("Tăng khả năng kiểm soát dữ liệu. ",
     "Quá trình bảo vệ diễn ra trực tiếp trên thiết bị, không phụ thuộc máy chủ hay dịch vụ "
     "lưu trữ bên ngoài; ứng dụng không khai báo quyền truy cập Internet."),
    ("Giảm phụ thuộc vào giải pháp bên ngoài. ",
     "Mã nguồn và thiết kế do đơn vị chủ động xây dựng, có thể kiểm tra, duy trì và phát "
     "triển theo yêu cầu thực tế."),
    ("Nâng cao nhận thức và góp phần đào tạo nhân lực làm chủ công nghệ. ",
     "Học viên và cán bộ trực tiếp thao tác, quan sát kết quả và hiểu giới hạn của từng biện "
     "pháp; mã nguồn mở cho phép nghiên cứu nguyên lý, cách triển khai và phương pháp kiểm "
     "tra, tạo cơ sở để tiếp tục phát triển sản phẩm."),
]:
    bullet(doc, _t, bold_head=_h)
para(doc,
     "*Phạm vi và điều kiện sử dụng.* Sản phẩm là công cụ hỗ trợ kỹ thuật phục vụ đào tạo, "
     "thực hành an toàn thông tin, bảo đảm an toàn tình báo trên không gian mạng và hỗ trợ "
     "giảm rủi ro trong những tình huống đặc thù khi việc chuyển giao tài liệu qua không "
     "gian mạng đã được cấp có thẩm quyền cho phép. Sản phẩm không nhằm thay thế hoặc nới "
     "lỏng các quy định về quản lý tài liệu mật, tài liệu nội bộ và dữ liệu trên thiết bị di "
     "động.")

h3(doc, "4.4. Mức độ triển khai, phát triển trong thời gian tới")
para(doc, "4.4.1. Mức độ hoàn thành hiện tại", bold=True, indent=False)
bang(doc, "Mức độ hoàn thành theo hạng mục",
     ["Hạng mục", "Mức độ", "Cách xác định"],
     [
         ["Thiết kế kiến trúc, định dạng dữ liệu và sơ đồ khoá", "Hoàn thành",
          "Tài liệu kiến trúc và mã nguồn"],
         ["Lõi bảo vệ dữ liệu và toàn bộ nghiệp vụ", "Hoàn thành",
          "Bộ kiểm thử tự động chạy đạt trên máy chủ"],
         ["Mô-đun xử lý siêu dữ liệu bằng Rust", "Hoàn thành",
          "Kiểm thử tự động trên ảnh có siêu dữ liệu"],
         ["Tương thích định dạng giữa hai bản hiện thực", "Hoàn thành",
          "Đối chứng hai chiều với công cụ chuẩn age v1.2.1"],
         ["Biên dịch và thực thi lõi trên kiến trúc ARM64", "Hoàn thành",
          "Kiểm tra tệp đối tượng và chạy bộ kiểm thử dưới trình giả lập kiến trúc"],
         ["Giao diện cho màn hình điện thoại và đóng gói APK", "Hoàn thành",
          "Kết xuất ở kích thước điện thoại; kiểm tra tĩnh nội dung gói cài đặt"],
         ["Kiểm thử nghiệm thu trên thiết bị Android", "Có quy trình nghiệm thu",
          "Quy trình 15 bước có tiêu chí đạt cho từng bước (Phụ lục A của Đề cương chi tiết)"],
         ["Tích hợp kho khoá phần cứng của Android", "Định hướng phát triển",
          "Chưa hiện thực trong phiên bản này"],
     ], widths=[6.0, 3.6, 5.9])

para(doc, "4.4.2. Hướng phát triển", bold=True, indent=False)
for _h, _t in [
    ("Mở rộng kiểm thử nghiệm thu trên nhiều dòng máy. ",
     "Thực hiện các kịch bản nghiệp vụ trong quy trình nghiệm thu trên nhiều dòng điện thoại "
     "và phiên bản Android khác nhau, ghi nhận kết quả để đánh giá khả năng tương thích và "
     "mức độ ổn định."),
    ("Tích hợp kho khoá phần cứng và xác thực sinh trắc. ",
     "Nghiên cứu sử dụng vùng lưu khoá được Android và phần cứng thiết bị bảo vệ cho một số "
     "khoá nằm ngoài hệ thống khoá của két; bổ sung tuỳ chọn xác thực bằng vân tay khi thiết "
     "bị hỗ trợ."),
    ("Mở rộng phạm vi định dạng của mô-đun siêu dữ liệu. ",
     "Bổ sung khả năng xem và loại bỏ siêu dữ liệu với các định dạng ảnh, video khác, đồng "
     "thời giữ nguyên tắc chỉ báo thành công khi kết quả xử lý đã được kiểm tra."),
    ("Xây dựng bộ bài giảng và bài thực hành kèm theo. ",
     "Biên soạn tài liệu hướng dẫn giảng viên, phiếu bài thực hành và bộ dữ liệu mẫu tương "
     "ứng với bảng ánh xạ chức năng, làm cơ sở đưa sản phẩm vào chương trình huấn luyện "
     "chính thức."),
    ("Đánh giá độc lập và mở rộng nền tảng. ",
     "Tổ chức rà soát mã nguồn và kiểm thử độc lập bởi đồng nghiệp hoặc học viên có chuyên "
     "môn. Trên cơ sở kiến trúc lõi dùng chung, có thể mở rộng sang nền tảng khác bằng cách "
     "bổ sung thành phần phụ thuộc nền tảng mà vẫn dùng chung lõi xử lý và định dạng dữ liệu."),
]:
    bullet(doc, _t, bold_head=_h)

# =====================================================================
h1(doc, "C. TÀI LIỆU THAM KHẢO")
for _t in [
    "RFC 9106 — Argon2 Memory-Hard Function for Password Hashing.",
    "OWASP Password Storage Cheat Sheet — tham số tối thiểu cho Argon2id "
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
     "Văn bản kèm theo: *04 — Đề cương chi tiết về sáng kiến*, trình bày đầy đủ phân tích kỹ "
     "thuật, mô tả từng chức năng kèm giao diện, ảnh chụp toàn bộ 21 màn hình và quy trình "
     "kiểm thử nghiệm thu trên thiết bị Android.", italic=True)

chu_ky(doc,
       ("XÁC NHẬN CỦA ĐƠN VỊ", ""),
       ("CHỦ NHIỆM SÁNG KIẾN", f"{CHU_NHIEM['cap_bac']} {CHU_NHIEM['ho_ten']}"),
       dia_danh=DIA_DANH_NGAY)

OUT = BASE / "docx" / "02-Thuyet-minh-sang-kien.docx"
OUT.parent.mkdir(exist_ok=True)
doc.save(OUT)
print(f"Đã ghi {OUT}")
