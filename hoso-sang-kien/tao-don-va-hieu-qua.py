#!/usr/bin/env python3
"""Sinh hai văn bản: ĐƠN ĐĂNG KÝ SÁNG KIẾN và XÁC NHẬN/DỰ KIẾN HIỆU QUẢ."""

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from dinh_dang import (  # noqa: E402
    bang, bullet, chu_ky, danh_so_trang, h1, h2, h3, khung_nhan_manh, new_document,
    ngat_trang, para, quocHieu, rich, tieuDeChinh,
)
from docx.enum.text import WD_ALIGN_PARAGRAPH  # noqa: E402

BASE = pathlib.Path(__file__).parent
DK = json.loads((BASE / "bang-chung" / "du-kien.json").read_text(encoding="utf-8"))
N_LENH = DK["lenh_ipc"]["so_luong"]
N_CRATE = DK["crate"]["so_luong"]
N_TEST = sum(DK["test_trong_nguon"].values())
A2 = DK["argon2id"]
KQ = DK["ket_qua_kiem_thu"]

TEN_SK = ("SecureVault Mobile — Ứng dụng bảo vệ dữ liệu nhạy cảm trên thiết bị Android, "
          "hoạt động hoàn toàn ngoại tuyến, phục vụ công tác và huấn luyện an toàn thông tin")

DONG_KE = "……………………………………………………………………"

# =====================================================================
# VĂN BẢN 1 — ĐƠN ĐĂNG KÝ SÁNG KIẾN
# =====================================================================
doc = new_document()
danh_so_trang(doc)
quocHieu(doc)
tieuDeChinh(doc, "ĐƠN ĐĂNG KÝ SÁNG KIẾN")

para(doc, "Kính gửi: Hội đồng xét, công nhận sáng kiến ………………………………………",
     bold=True, indent=False)
doc.add_paragraph()

para(doc, "Tôi ghi tên dưới đây:", indent=False)
bang(doc, "",
     ["Họ và tên", "Ngày sinh", "Nơi công tác", "Chức danh", "Trình độ chuyên môn",
      "Tỷ lệ đóng góp"],
     [["……………", "…/…/……", "……………", "……………", "……………", "100%"]],
     widths=[3.0, 1.9, 3.2, 2.4, 2.6, 1.9])

para(doc, "1. Là tác giả đề nghị xét công nhận sáng kiến:", bold=True, indent=False)
para(doc, TEN_SK, italic=True)

para(doc, "2. Chủ đầu tư tạo ra sáng kiến:", bold=True, indent=False)
para(doc, "Tác giả tự đầu tư thời gian, công sức và phương tiện cá nhân để nghiên cứu và "
          "xây dựng sản phẩm.")

para(doc, "3. Lĩnh vực áp dụng sáng kiến:", bold=True, indent=False)
para(doc, "An toàn thông tin trên không gian mạng; bảo vệ dữ liệu trên thiết bị di động; "
          "công tác đào tạo, huấn luyện. Sáng kiến giải quyết vấn đề bảo vệ dữ liệu nội bộ, "
          "dữ liệu nhạy cảm phát sinh trong quá trình công tác và giảng dạy khi các dữ liệu "
          "này được lưu trữ và sử dụng trên điện thoại thông minh.")

para(doc, "4. Ngày sáng kiến được áp dụng lần đầu hoặc áp dụng thử:", bold=True, indent=False)
para(doc, f"Ngày …… tháng …… năm 202…  {DONG_KE}")

para(doc, "5. Mô tả bản chất của sáng kiến:", bold=True, indent=False)
para(doc,
     "Sáng kiến là một ứng dụng Android cho phép người dùng mã hoá, ký số, kiểm tra tính toàn "
     "vẹn, chia khoá phục hồi và xử lý an toàn dữ liệu ngay trên thiết bị, không cần kết nối "
     "mạng và không sử dụng bất kỳ dịch vụ máy chủ nào.")
para(doc,
     "Điểm cốt lõi về mặt kỹ thuật là kiến trúc một lõi bảo mật dùng chung, được tổ chức sao "
     "cho phần nghiệp vụ mật mã hoàn toàn độc lập với giao diện và với nền tảng. Trên nền tảng "
     "di động, hệ điều hành không cho phép ứng dụng sinh tiến trình con để chạy các công cụ "
     "mật mã dạng tệp nhị phân — đây chính là rào cản khiến nhiều công cụ tin cậy trên máy "
     "tính để bàn không có bản dùng được trên điện thoại. Sáng kiến giải quyết rào cản này "
     "bằng cách đặt một điểm nối trừu tượng tại vị trí bộ mã hoá nội dung, cho phép thay thế "
     "bộ mã hoá mà không làm thay đổi định dạng tệp, và đã kiểm chứng tính tương thích bằng "
     "thực nghiệm đối chứng hai chiều với công cụ chuẩn.")
para(doc,
     f"Sản phẩm cung cấp {N_LENH} lệnh nghiệp vụ thuộc sáu nhóm chức năng, được xây dựng trên "
     f"{N_CRATE} thành phần mã nguồn độc lập kèm {N_TEST} hàm kiểm thử tự động. Nội dung chi "
     "tiết được trình bày trong Thuyết minh sáng kiến kèm theo.")

para(doc, "6. Những thông tin cần được bảo mật:", bold=True, indent=False)
para(doc, "Không. Toàn bộ thuật toán sử dụng đều là thuật toán công khai, đã được cộng đồng "
          "khoa học kiểm chứng. Mã nguồn được công bố để có thể kiểm tra lại.")

para(doc, "7. Các điều kiện cần thiết để áp dụng sáng kiến:", bold=True, indent=False)
for t in ["Một điện thoại chạy hệ điều hành Android (không yêu cầu quyền quản trị thiết bị).",
          "Không cần máy chủ, không cần kết nối mạng, không phát sinh chi phí bản quyền.",
          "Người dùng được hướng dẫn sử dụng cơ bản (khoảng 30 phút) và hiểu nguyên tắc "
          "bảo quản mật khẩu."]:
    bullet(doc, t)

para(doc, "8. Đánh giá lợi ích thu được:", bold=True, indent=False)
para(doc,
     "Sáng kiến mang lại giá trị kép: vừa là công cụ bảo vệ dữ liệu sử dụng được trong công "
     "tác, vừa là học cụ trực quan phục vụ giảng dạy an toàn thông tin. Đánh giá chi tiết "
     "được trình bày tại văn bản “Dự kiến hiệu quả khi đưa vào ứng dụng trong thực tiễn” "
     "kèm theo hồ sơ.")

para(doc,
     "Tôi xin cam đoan mọi thông tin nêu trong đơn là trung thực, đúng sự thật và hoàn toàn "
     "chịu trách nhiệm trước pháp luật.", indent=False)

chu_ky(doc, ("XÁC NHẬN CỦA ĐƠN VỊ", "(ký, ghi rõ họ tên, đóng dấu)"),
       ("NGƯỜI NỘP ĐƠN", "(ký, ghi rõ họ tên)"))

doc.save(str(BASE / "docx" / "01-Don-dang-ky-sang-kien.docx"))
print("Đã tạo 01-Don-dang-ky-sang-kien.docx")

# =====================================================================
# VĂN BẢN 3 — DỰ KIẾN HIỆU QUẢ
# =====================================================================
doc = new_document()
danh_so_trang(doc)
quocHieu(doc)
tieuDeChinh(
    doc,
    "DỰ KIẾN HIỆU QUẢ KHI ĐƯA VÀO ỨNG DỤNG TRONG THỰC TIỄN",
    "Kèm theo hồ sơ đề nghị công nhận sáng kiến “SecureVault Mobile”",
)

h1(doc, "I. CƠ SỞ ĐÁNH GIÁ")
para(doc,
     "Văn bản này đánh giá hiệu quả của sáng kiến trên hai nhóm: hiệu quả đã đo được bằng số "
     "liệu khách quan tại thời điểm lập hồ sơ, và hiệu quả dự kiến khi đưa vào sử dụng thực "
     "tế. Tác giả không đưa ra số liệu ước lượng thiếu căn cứ; những nội dung chỉ có thể xác "
     "định sau khi triển khai được ghi rõ là dự kiến.")

h1(doc, "II. HIỆU QUẢ ĐÃ ĐO ĐƯỢC")
_rows = [
    ["Số lệnh nghiệp vụ cung cấp", f"{N_LENH}", "Đếm tự động từ mã nguồn"],
    ["Số hàm kiểm thử tự động", f"{N_TEST}", "Đếm tự động từ mã nguồn"],
]
if KQ.get("host_toan_bo"):
    h = KQ["host_toan_bo"]
    _rows.append(["Kết quả kiểm thử trên máy chủ", f"{h['passed']} đạt / {h['failed']} lỗi",
                  "Nhật ký chạy kiểm thử"])
if KQ.get("arm64_loi_mat_ma"):
    a = KQ["arm64_loi_mat_ma"]
    _rows.append([f"Kiểm thử lõi mật mã trên ARM64 ({a['suites']} bộ kiểm thử)",
                  f"{a['passed']} đạt / {a['failed']} lỗi", "Chạy dưới trình giả lập kiến trúc"])
if KQ.get("interop_vault"):
    v = KQ["interop_vault"]
    _rows.append(["Kiểm chứng tương thích định dạng", f"{v['passed']} đạt / {v['failed']} lỗi",
                  "Đối chứng với công cụ age v1.2.1"])
_rows += [
    ["Chi phí bản quyền phần mềm", "0 đồng", "Toàn bộ thành phần dùng giấy phép mở"],
    ["Chi phí hạ tầng máy chủ", "0 đồng", "Thiết kế không có thành phần máy chủ"],
    ["Quyền truy cập mạng ứng dụng yêu cầu", "Không có", "Kiểm tra tệp kê khai gói cài đặt"],
]
bang(doc, "Bảng 1. Các chỉ số đã đo được", ["Chỉ số", "Giá trị", "Nguồn"], _rows,
     widths=[6.2, 4.3, 5.0])

h1(doc, "III. HIỆU QUẢ DỰ KIẾN KHI ĐƯA VÀO ỨNG DỤNG")

h2(doc, "1. Hiệu quả đối với công tác giảng dạy và huấn luyện")
for t in [
    "Cung cấp học cụ cho các nội dung mã hoá, chữ ký số, hàm băm, chia sẻ bí mật ngưỡng, giấu "
    "tin và phát hiện giấu tin — học viên thao tác trực tiếp trên thiết bị cá nhân.",
    "Cho phép xây dựng bài thực hành có kết quả quan sát được ngay, thay cho ví dụ lý thuyết.",
    "Giảm nhu cầu chuẩn bị phòng máy chuyên dụng cho một số bài thực hành.",
    "Mở ra hình thức huấn luyện nâng cao: đọc, phân tích và nhận xét mã nguồn của một hệ "
    "thống an toàn thực tế.",
]:
    bullet(doc, t)

h2(doc, "2. Hiệu quả đối với bảo vệ dữ liệu của cơ quan, đơn vị")
for t in [
    "Cung cấp phương án bảo vệ dữ liệu ngay trên thiết bị, hạn chế thói quen chuyển tài liệu "
    "nội bộ qua ứng dụng nhắn tin hoặc lưu trữ đám mây không kiểm soát.",
    "Bảo đảm chủ quyền dữ liệu: khoá và dữ liệu do người dùng nắm giữ, không có thành phần "
    "máy chủ, ứng dụng không có khả năng kỹ thuật để gửi dữ liệu ra ngoài.",
    "Cho phép kiểm tra tính toàn vẹn và nguồn gốc của tệp nhận được, phục vụ công tác xác "
    "minh tài liệu.",
    "Nâng cao nhận thức về an toàn thông tin thông qua việc sử dụng công cụ hằng ngày.",
]:
    bullet(doc, t)

h2(doc, "3. Hiệu quả kinh tế")
para(doc,
     "Sáng kiến không phát sinh chi phí bản quyền phần mềm và không yêu cầu đầu tư hạ tầng "
     "máy chủ. Sản phẩm chạy trên thiết bị sẵn có của người dùng. Do đó hiệu quả kinh tế chủ "
     "yếu thể hiện ở việc tránh được chi phí mua sắm giải pháp thương mại tương đương và chi "
     "phí duy trì hạ tầng, thay vì ở khoản tiết kiệm trực tiếp có thể quy đổi.")
para(doc,
     "Tác giả không đưa ra con số quy đổi thành tiền cụ thể, vì con số đó phụ thuộc quy mô "
     "triển khai và chính sách mua sắm của từng đơn vị; việc ước lượng khi chưa triển khai sẽ "
     "không có căn cứ.", italic=True)

h1(doc, "IV. PHẠM VI VÀ GIỚI HẠN")
para(doc, "Để bảo đảm sử dụng đúng và tránh chủ quan, tác giả nêu rõ những giới hạn sau.")
for t in [
    "Sản phẩm chưa được kiểm thử trên thiết bị Android thật tại thời điểm lập hồ sơ; các kết "
    "quả kiểm chứng hiện có là kiểm thử tự động, biên dịch chéo, thực thi lõi trên kiến trúc "
    "ARM64 bằng trình giả lập và kiểm tra tĩnh gói cài đặt.",
    "Sản phẩm không bảo vệ được dữ liệu nếu thiết bị đã bị chiếm quyền điều khiển ở mức hệ "
    "điều hành.",
    "Nếu người dùng quên mật khẩu và không tạo trước các mảnh khoá phục hồi thì dữ liệu không "
    "thể khôi phục — đây là hệ quả tất yếu của nguyên tắc không lưu khoá.",
    "Việc sử dụng sản phẩm cho bất kỳ loại tài liệu nào phải tuân thủ quy định hiện hành về "
    "bảo vệ bí mật nhà nước và quy chế của đơn vị. Hồ sơ không đưa ra tuyên bố về việc sản "
    "phẩm được phép xử lý tài liệu thuộc danh mục bí mật nhà nước ở cấp độ cụ thể.",
]:
    bullet(doc, t)

khung_nhan_manh(
    doc,
    "Kết luận",
    ["Sáng kiến đã có sản phẩm thực tế, có bằng chứng kiểm chứng bằng máy ở nhiều mức, có giá "
     "trị sử dụng trong công tác và giá trị phục vụ đào tạo an toàn thông tin.",
     "Phần chưa kiểm chứng được nêu rõ, kèm quy trình kiểm thử để đơn vị có thể tự xác nhận "
     "trên thiết bị thật trước khi đưa vào sử dụng rộng rãi."],
)

chu_ky(doc, ("XÁC NHẬN CỦA ĐƠN VỊ", "(ký, ghi rõ họ tên, đóng dấu)"),
       ("TÁC GIẢ SÁNG KIẾN", "(ký, ghi rõ họ tên)"))

doc.save(str(BASE / "docx" / "03-Du-kien-hieu-qua.docx"))
print("Đã tạo 03-Du-kien-hieu-qua.docx")
