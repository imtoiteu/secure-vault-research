#!/usr/bin/env python3
"""Sinh hai văn bản còn lại của bộ hồ sơ:

  01. ĐƠN ĐĂNG KÝ SÁNG KIẾN CẢI TIẾN KỸ THUẬT
  03. DỰ KIẾN HIỆU QUẢ SÁNG KIẾN KHI ĐƯA VÀO ỨNG DỤNG TRONG THỰC TIỄN

Cấu trúc, thứ tự mục và khối ký đối chiếu với tệp mẫu `Mau_ho_so_sang_kien_cai_tien.doc`
và với bản tác giả đã trực tiếp rà soát. Thông tin tác giả lấy từ ten_sang_kien.py, số liệu
lấy từ du_lieu_ho_so.py — không nhập tay ở tệp này.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from dinh_dang import (  # noqa: E402
    bang, bullet, chu_ky, danh_so_trang, dat_lai_dem, dong_dien, h1, h2,
    khung_nhan_manh, new_document, o_danh_dau, para, rich, tieuDeChinh,
    tieu_de_quan_doi,
)
from du_lieu_ho_so import (  # noqa: E402
    APK, MB_APK, N_CRATE, N_LENH, N_TEST, SO_DOI_CHUNG, arm, host,
)
from noi_dung_giao_dien import DANH_MUC_MAN_HINH  # noqa: E402
from ten_sang_kien import (  # noqa: E402
    CHI_HUY_DON_VI, CHU_NHIEM, DIA_DANH_NGAY, DONG_TAC_GIA, LINH_VUC, NAM, TEN_SANG_KIEN,
)

BASE = pathlib.Path(__file__).parent

# =====================================================================
# VĂN BẢN 1 — ĐƠN ĐĂNG KÝ
# =====================================================================
doc = new_document()
dat_lai_dem()
danh_so_trang(doc)
tieu_de_quan_doi(doc)

tieuDeChinh(doc, f"ĐƠN ĐĂNG KÝ\nSÁNG KIẾN CẢI TIẾN KỸ THUẬT NĂM {NAM}")

dong_dien(doc, "Họ và tên", CHU_NHIEM["ho_ten"], cach_sau=3)
dong_dien(doc, "Đơn vị", CHU_NHIEM["don_vi"], cach_sau=3)
dong_dien(doc, "Cấp bậc", CHU_NHIEM["cap_bac"], cach_sau=3)
dong_dien(doc, "Trình độ", CHU_NHIEM["trinh_do"], cach_sau=3)
dong_dien(doc, "Ngày tháng năm sinh", CHU_NHIEM["ngay_sinh"], cach_sau=3)
dong_dien(doc, "Địa chỉ liên hệ", CHU_NHIEM["dia_chi"], cach_sau=3)
dong_dien(doc, "Điện thoại",
          f"{CHU_NHIEM['dien_thoai']}          e-mail: {CHU_NHIEM['email']}", cach_sau=8)

rich(doc, [
    ("Là tác giả (đại diện nhóm tác giả) của sáng kiến/giải pháp: ", ""),
    (f"“{TEN_SANG_KIEN}”.", "b"),
], indent=False)
dong_dien(doc, "Thuộc lĩnh vực", LINH_VUC)

h2(doc, "B. HỒ SƠ KÈM THEO GỒM")
o_danh_dau(doc, "Đơn đăng ký sáng kiến")
o_danh_dau(doc, "Thuyết minh sáng kiến")
o_danh_dau(doc, "Dự kiến đánh giá hiệu quả mang lại của sáng kiến")
o_danh_dau(doc, "Đề cương sơ bộ về sáng kiến")
o_danh_dau(doc, "Đề cương chi tiết về sáng kiến")
o_danh_dau(doc, "Sản phẩm phần mềm: tệp cài đặt Android (APK) và toàn bộ mã nguồn dùng "
                "chung cho bản di động và bản máy tính")

h2(doc, "C. DANH SÁCH CÁC ĐỒNG TÁC GIẢ")
bang(doc, "",
     ["TT", "Họ và tên", "Đơn vị", "Cấp bậc, chức vụ", "Tỷ lệ đóng góp"],
     [[str(i), ng["ho_ten"], ng["don_vi"], f"{ng['cap_bac']}, {ng['chuc_vu']}", ng["ty_le"]]
      for i, ng in enumerate(DONG_TAC_GIA, start=1)],
     widths=[1.2, 3.8, 4.6, 3.6, 2.8])

para(doc,
     "Chúng tôi xin cam đoan sáng kiến nói trên là do chúng tôi nghiên cứu, thiết kế và trực "
     "tiếp xây dựng. Toàn bộ ý tưởng giải pháp, kiến trúc hệ thống, cách tổ chức và bảo vệ "
     "dữ liệu, định dạng tệp két, cùng toàn bộ mã nguồn của sản phẩm là kết quả nghiên cứu "
     "của nhóm tác giả. Các nguyên hàm mật mã cơ sở sử dụng trong sản phẩm là những chuẩn "
     "công khai đã được cộng đồng khoa học kiểm chứng, do chúng tôi lựa chọn và vận dụng có "
     "luận cứ vào thiết kế của mình — đúng theo nguyên tắc nghề nghiệp là không tự chế thuật "
     "toán mật mã. Chúng tôi hoàn toàn chịu trách nhiệm trước pháp luật về nội dung đã kê "
     "khai.", indent=False)

chu_ky(doc,
       ("TÁC GIẢ SÁNG KIẾN", f"{CHU_NHIEM['cap_bac']} {CHU_NHIEM['ho_ten']}"),
       ("CHỈ HUY ĐƠN VỊ", CHI_HUY_DON_VI),
       dia_danh=DIA_DANH_NGAY)

doc.save(str(BASE / "docx" / "01-Don-dang-ky-sang-kien.docx"))
print("Đã tạo 01-Don-dang-ky-sang-kien.docx")

# =====================================================================
# VĂN BẢN 3 — DỰ KIẾN HIỆU QUẢ
# =====================================================================
doc = new_document()
dat_lai_dem()
danh_so_trang(doc)
tieu_de_quan_doi(doc)

tieuDeChinh(doc, "DỰ KIẾN HIỆU QUẢ SÁNG KIẾN\nKHI ĐƯA VÀO ỨNG DỤNG TRONG THỰC TIỄN")

h1(doc, "I. THÔNG TIN CHUNG VÀ CƠ SỞ ĐÁNH GIÁ")
dong_dien(doc, "Tên sáng kiến", TEN_SANG_KIEN, cach_sau=3)
dong_dien(doc, "Chủ nhiệm sáng kiến",
          f"{CHU_NHIEM['cap_bac']} {CHU_NHIEM['ho_ten']} — {CHU_NHIEM['don_vi']}", cach_sau=3)
dong_dien(doc, "Đơn vị áp dụng", "Học viện Khoa học Quân sự", cach_sau=8)
para(doc,
     "Văn bản này đánh giá hiệu quả của sáng kiến trên hai nhóm tách bạch: *hiệu quả đã đo "
     "được* bằng số liệu khách quan tại thời điểm lập hồ sơ, và *hiệu quả dự kiến* khi đưa "
     "vào sử dụng thực tế. Việc tách bạch nhằm tránh trình bày một dự kiến như thể đã là kết "
     "quả đo được.")

h1(doc, "II. HIỆU QUẢ ĐÃ ĐO ĐƯỢC BẰNG SỐ LIỆU KHÁCH QUAN")
para(doc,
     "Các chỉ số dưới đây được sinh tự động từ mã nguồn và nhật ký kiểm thử của sản phẩm, "
     "không phải số liệu ước lượng, và kiểm tra lại được bằng cách chạy lại bộ kiểm thử kèm "
     "theo mã nguồn.")

_rows = [
    ["Số chức năng nghiệp vụ cung cấp", f"{N_LENH} chức năng", "Đếm trực tiếp từ mã nguồn"],
    ["Số màn hình giao diện", f"{len(DANH_MUC_MAN_HINH)} màn hình",
     "Đếm trực tiếp từ mã giao diện"],
    ["Quy mô mã nguồn do nhóm tác giả xây dựng", f"{N_CRATE} thành phần độc lập",
     "Cấu hình vùng làm việc của dự án"],
    ["Số hàm kiểm thử tự động", f"{N_TEST} hàm", "Đếm trực tiếp từ mã nguồn"],
]
if host:
    _rows.append(["Kết quả kiểm thử trên máy chủ",
                  f"{host['passed']} đạt / {host['failed']} lỗi",
                  "Nhật ký chạy bộ kiểm thử"])
if arm:
    _rows.append([f"Kiểm thử lõi mật mã trên kiến trúc ARM64 ({arm['suites']} bộ)",
                  f"{arm['passed']} đạt / {arm['failed']} lỗi",
                  "Chạy dưới trình giả lập kiến trúc"])
if SO_DOI_CHUNG:
    _rows.append(["Kiểm chứng tương thích định dạng dữ liệu",
                  f"{SO_DOI_CHUNG} phép đối chứng đạt",
                  "Đối chứng với công cụ chuẩn age v1.2.1"])
if APK.get("co_apk"):
    _rows.append(["Sản phẩm đóng gói hoàn chỉnh", f"Tệp cài đặt Android {MB_APK} MB",
                  "Kiểm tra tĩnh nội dung gói cài đặt"])
    _rows.append(["Quyền truy cập mạng ứng dụng yêu cầu", "Không khai báo quyền nào",
                  "Đọc tệp kê khai trong gói cài đặt"])
_rows += [
    ["Chi phí bản quyền phần mềm", "0 đồng", "Toàn bộ thành phần dùng giấy phép mở"],
    ["Chi phí đầu tư hạ tầng máy chủ", "0 đồng", "Thiết kế không có thành phần máy chủ"],
]
bang(doc, "Các chỉ số đã đo được tại thời điểm lập hồ sơ",
     ["Chỉ số", "Giá trị", "Nguồn số liệu"], _rows, widths=[6.4, 4.6, 4.5])

h1(doc, "III. HIỆU QUẢ DỰ KIẾN KHI ĐƯA VÀO ỨNG DỤNG")

h2(doc, "1. Hiệu quả đối với công tác giảng dạy và huấn luyện")
for t in [
    "Cung cấp học cụ cho các nội dung mã hoá, chữ ký số, hàm băm, chia sẻ bí mật ngưỡng, "
    "giấu tin và phát hiện giấu tin — học viên thao tác trực tiếp trên thiết bị di động, "
    "đúng môi trường sẽ gặp nhiều nhất sau khi ra trường.",
    "Cho phép xây dựng bài thực hành có kết quả quan sát được ngay, thay cho ví dụ lý thuyết.",
    "Giúp học viên hiểu đúng *giới hạn* của từng biện pháp: sản phẩm chủ động nêu rõ phạm vi "
    "kết luận của các chức năng phân tích thay vì đưa ra kết luận tuyệt đối.",
    "Mở ra hình thức huấn luyện nâng cao: đọc, phân tích và nhận xét mã nguồn của một hệ "
    "thống an toàn thực tế — điều mà phần mềm thương mại mã nguồn đóng không đáp ứng được.",
]:
    bullet(doc, t)

h2(doc, "2. Hiệu quả đối với bảo vệ dữ liệu trong tình huống đặc thù")
for t in [
    "Giảm rủi ro lộ lọt khi phát sinh tình huống khẩn cấp, bất khả kháng buộc phải chuyển "
    "gấp tài liệu qua không gian mạng và đã được cấp có thẩm quyền cho phép: tệp được mã "
    "hoá, ký số và làm sạch siêu dữ liệu trước khi rời thiết bị, nên nếu bị chặn bắt trên "
    "đường truyền thì bên chặn bắt thu được bản mã chứ không phải nội dung.",
    "Cho phép bên nhận tự kiểm tra nguồn gốc và tính toàn vẹn của tệp bằng chữ ký số, không "
    "phải tin vào kênh truyền.",
    "Bảo đảm chủ quyền dữ liệu: toàn bộ quá trình xử lý diễn ra trên thiết bị, khoá do người "
    "dùng nắm giữ, sản phẩm không có thành phần máy chủ và không khai báo quyền truy cập "
    "mạng nên về mặt kỹ thuật không thể gửi dữ liệu ra ngoài.",
    "Giảm phụ thuộc vào phần mềm bảo mật nước ngoài mã nguồn đóng: toàn bộ thiết kế và mã "
    "nguồn do nhóm tác giả xây dựng, đơn vị kiểm soát được và có bộ kiểm thử để kiểm chứng.",
]:
    bullet(doc, t)

h2(doc, "3. Hiệu quả kinh tế")
para(doc,
     "Sáng kiến không phát sinh chi phí bản quyền phần mềm, không yêu cầu đầu tư máy chủ, "
     "không phát sinh chi phí thuê bao dịch vụ và chạy trên thiết bị sẵn có của người dùng. "
     "Hiệu quả kinh tế thể hiện ở việc tránh được chi phí mua sắm giải pháp thương mại tương "
     "đương và chi phí duy trì hạ tầng đi kèm, đồng thời tránh chi phí chuyển đổi khi đổi "
     "nhà cung cấp vì sản phẩm do đơn vị hoàn toàn làm chủ.")
para(doc,
     "Nhóm tác giả không quy đổi thành con số tiền cụ thể, vì con số đó phụ thuộc quy mô "
     "triển khai và chính sách mua sắm của từng đơn vị; đưa ra ước lượng khi chưa triển khai "
     "sẽ không có căn cứ và làm giảm độ tin cậy của hồ sơ.", italic=True)

h1(doc, "IV. PHẠM VI, ĐIỀU KIỆN ÁP DỤNG VÀ GIỚI HẠN")
para(doc,
     "Sản phẩm áp dụng được ngay với điều kiện tối thiểu: một điện thoại chạy hệ điều hành "
     "Android, không cần quyền quản trị thiết bị, không cần máy chủ và không cần kết nối "
     "mạng. Người dùng chỉ cần hướng dẫn sử dụng cơ bản và nắm nguyên tắc bảo quản mật khẩu.")
para(doc, "Để bảo đảm sử dụng đúng và tránh chủ quan, cần nêu rõ các giới hạn sau:")
for t in [
    "Sản phẩm không bảo vệ được dữ liệu nếu thiết bị đã bị chiếm quyền điều khiển ở mức hệ "
    "điều hành.",
    "Nếu người dùng quên mật khẩu và không tạo trước các mảnh khoá phục hồi thì dữ liệu "
    "không thể khôi phục — đây là đánh đổi có chủ ý của nguyên tắc không lưu mật khẩu lâu "
    "dài, không phải thiếu sót.",
    "Việc nghiệm thu trên thiết bị Android thật chưa thực hiện tại thời điểm lập hồ sơ; quy "
    "trình nghiệm thu 15 bước đã được soạn sẵn tại Phụ lục A của Đề cương chi tiết để đơn vị "
    "tự xác nhận trước khi đưa vào sử dụng rộng rãi.",
    "Việc sử dụng sản phẩm cho bất kỳ loại tài liệu nào phải tuân thủ quy định hiện hành về "
    "bảo vệ bí mật nhà nước và quy chế của đơn vị. Hồ sơ này không đưa ra tuyên bố về việc "
    "sản phẩm được phép xử lý tài liệu thuộc danh mục bí mật nhà nước ở cấp độ cụ thể.",
]:
    bullet(doc, t)

khung_nhan_manh(doc, "Kết luận", [
    "Sáng kiến đã có sản phẩm hoàn chỉnh, đóng gói được và kiểm chứng bằng số liệu khách "
    "quan ở nhiều mức, mang lại đồng thời giá trị phục vụ đào tạo an toàn thông tin và giá "
    "trị sử dụng trong những tình huống công tác đặc thù đã được cho phép.",
    "Phần chưa kiểm chứng được nêu rõ, kèm quy trình nghiệm thu để đơn vị tự xác nhận trên "
    "thiết bị thật trước khi đưa vào sử dụng rộng rãi.",
])

chu_ky(doc,
       ("XÁC NHẬN CỦA ĐƠN VỊ", ""),
       ("CHỦ NHIỆM SÁNG KIẾN", f"{CHU_NHIEM['cap_bac']} {CHU_NHIEM['ho_ten']}"),
       dia_danh=DIA_DANH_NGAY)

doc.save(str(BASE / "docx" / "03-Du-kien-hieu-qua.docx"))
print("Đã tạo 03-Du-kien-hieu-qua.docx")
