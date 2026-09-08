#!/usr/bin/env python3
"""Sinh hai văn bản theo đúng mẫu hồ sơ sáng kiến cải tiến kỹ thuật:

  1. ĐƠN ĐĂNG KÝ SÁNG KIẾN CẢI TIẾN KỸ THUẬT
  3. XÁC NHẬN ĐÁNH GIÁ HIỆU QUẢ MANG LẠI CỦA SÁNG KIẾN

Cấu trúc, thứ tự mục và khối ký được đối chiếu với tệp mẫu
`Mau_ho_so_sang_kien_cai_tien.doc`. Số liệu lấy từ bang-chung/du-kien.json.
"""

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from dinh_dang import (  # noqa: E402
    bang, bullet, chu_ky, danh_so_trang, dat_lai_dem, dong_dien, h1, h2,
    khung_nhan_manh, new_document, o_danh_dau, para, rich, tieuDeChinh,
    tieu_de_quan_doi,
)

BASE = pathlib.Path(__file__).parent
DK = json.loads((BASE / "bang-chung" / "du-kien.json").read_text(encoding="utf-8"))
_apk_file = BASE / "bang-chung" / "kiem-tra-apk.json"
APK = json.loads(_apk_file.read_text(encoding="utf-8")) if _apk_file.exists() else {"co_apk": False}

N_LENH = DK["lenh_ipc"]["so_luong"]
N_CRATE = DK["crate"]["so_luong"]
N_TEST = sum(DK["test_trong_nguon"].values())
KQ = DK["ket_qua_kiem_thu"]
_host = KQ.get("host_toan_bo") or {}
_arm = KQ.get("arm64_loi_mat_ma") or {}
_iva = KQ.get("interop_age") or {}
_ivv = KQ.get("interop_vault") or {}

TEN_SK = ("SecureVault Mobile — Ứng dụng bảo vệ dữ liệu nhạy cảm trên thiết bị Android "
          "hoạt động hoàn toàn ngoại tuyến, phục vụ công tác và huấn luyện an toàn thông tin")
LINH_VUC = ("An toàn thông tin trên không gian mạng; bảo vệ dữ liệu trên thiết bị di động; "
            "công nghệ thông tin phục vụ đào tạo – huấn luyện")

# =====================================================================
# VĂN BẢN 1 — ĐƠN ĐĂNG KÝ
# =====================================================================
doc = new_document()
dat_lai_dem()
danh_so_trang(doc)
tieu_de_quan_doi(doc)

tieuDeChinh(doc, "ĐƠN ĐĂNG KÝ\nSÁNG KIẾN CẢI TIẾN KỸ THUẬT NĂM ……")

h2(doc, "A. THÔNG TIN TÁC GIẢ")
for nhan in ["Họ và tên", "Đơn vị", "Cấp bậc", "Trình độ",
             "Ngày tháng năm sinh", "Địa chỉ liên hệ"]:
    dong_dien(doc, nhan)
dong_dien(doc, "Điện thoại", "……………………………          e-mail: ……………………………")

para(doc, "", indent=False)
rich(doc, [
    ("Là tác giả (đại diện nhóm tác giả) của sáng kiến/giải pháp: ", ""),
    (f"“{TEN_SK}”.", "b"),
], indent=False)
dong_dien(doc, "Thuộc lĩnh vực", LINH_VUC)

h2(doc, "B. HỒ SƠ KÈM THEO GỒM")
o_danh_dau(doc, "Đơn đăng ký sáng kiến")
o_danh_dau(doc, "Thuyết minh sáng kiến")
o_danh_dau(doc, "Xác nhận đánh giá hiệu quả mang lại của sáng kiến/giải pháp")
o_danh_dau(doc, "Sản phẩm phần mềm: tệp cài đặt Android (APK) và toàn bộ mã nguồn")
o_danh_dau(doc, "Phụ lục sơ đồ kiến trúc, ảnh chụp giao diện và quy trình kiểm thử")

h2(doc, "C. DANH SÁCH CÁC ĐỒNG TÁC GIẢ (NẾU CÓ)")
bang(doc, "",
     ["TT", "Họ và tên", "Cấp bậc", "Đơn vị công tác", "Tỷ lệ đóng góp"],
     [["1", "……………………", "…………", "……………………", "100%"],
      ["2", "", "", "", ""]],
     widths=[1.2, 4.2, 2.6, 4.8, 3.2])

para(doc,
     "Tôi xin cam đoan sáng kiến/giải pháp nói trên là do tôi nghiên cứu, thiết kế và trực "
     "tiếp xây dựng. Toàn bộ ý tưởng giải pháp, kiến trúc hệ thống, thuật toán tổ chức và bảo "
     "vệ dữ liệu, định dạng tệp két, cùng toàn bộ mã nguồn của sản phẩm là kết quả nghiên cứu "
     "của cá nhân tôi. Các nguyên hàm mật mã cơ sở sử dụng trong sản phẩm là những chuẩn công "
     "khai đã được cộng đồng khoa học kiểm chứng, do tôi lựa chọn và vận dụng có luận cứ vào "
     "thiết kế của mình — đúng theo nguyên tắc nghề nghiệp là không tự chế thuật toán mật mã. "
     "Tôi hoàn toàn chịu trách nhiệm trước pháp luật về nội dung đã kê khai.", indent=False)

chu_ky(doc, ("TÁC GIẢ SÁNG KIẾN", "(Ký, ghi rõ họ tên)"),
       ("CHỈ HUY ĐƠN VỊ", "(Ký, đóng dấu)"))

doc.save(str(BASE / "docx" / "01-Don-dang-ky-sang-kien.docx"))
print("Đã tạo 01-Don-dang-ky-sang-kien.docx")

# =====================================================================
# VĂN BẢN 3 — XÁC NHẬN ĐÁNH GIÁ HIỆU QUẢ
# =====================================================================
doc = new_document()
dat_lai_dem()
danh_so_trang(doc)
tieu_de_quan_doi(doc)

tieuDeChinh(
    doc,
    "XÁC NHẬN ĐÁNH GIÁ HIỆU QUẢ MANG LẠI\nCỦA SÁNG KIẾN/GIẢI PHÁP",
)

h1(doc, "I. THÔNG TIN CHUNG")
dong_dien(doc, "Tên sáng kiến", TEN_SK)
dong_dien(doc, "Tác giả")
dong_dien(doc, "Đơn vị áp dụng")
dong_dien(doc, "Thời gian bắt đầu áp dụng")

h1(doc, "II. HIỆU QUẢ ĐÃ ĐO ĐƯỢC BẰNG SỐ LIỆU KHÁCH QUAN")
para(doc,
     "Các chỉ số dưới đây được sinh tự động từ mã nguồn và nhật ký kiểm thử của sản phẩm, "
     "không phải số liệu ước lượng. Mọi chỉ số đều kiểm tra lại được bằng cách chạy lại bộ "
     "kiểm thử kèm theo mã nguồn.")

_rows = [
    ["Số chức năng nghiệp vụ cung cấp", f"{N_LENH} lệnh", "Đếm trực tiếp từ mã nguồn"],
    ["Quy mô mã nguồn do tác giả xây dựng", f"{N_CRATE} thành phần độc lập",
     "Cấu hình vùng làm việc của dự án"],
    ["Số hàm kiểm thử tự động", f"{N_TEST} hàm", "Đếm trực tiếp từ mã nguồn"],
]
if _host:
    _rows.append(["Kết quả kiểm thử trên máy chủ",
                  f"{_host['passed']} đạt / {_host['failed']} lỗi",
                  "Nhật ký chạy bộ kiểm thử"])
if _arm:
    _rows.append([f"Kiểm thử lõi mật mã trên kiến trúc ARM64 ({_arm['suites']} bộ)",
                  f"{_arm['passed']} đạt / {_arm['failed']} lỗi",
                  "Chạy dưới trình giả lập kiến trúc"])
if _iva or _ivv:
    _rows.append(["Kiểm chứng tương thích định dạng dữ liệu",
                  f"{_iva.get('passed', 0) + _ivv.get('passed', 0)} phép đối chứng đạt",
                  "Đối chứng với công cụ chuẩn age v1.2.1"])
if APK.get("co_apk"):
    _rows.append(["Sản phẩm đóng gói hoàn chỉnh",
                  f"Tệp cài đặt Android {APK['kich_thuoc_byte'] / 1e6:.1f} MB",
                  "Kiểm tra tĩnh nội dung gói cài đặt"])
    _rows.append(["Quyền truy cập mạng ứng dụng yêu cầu",
                  "Không khai báo quyền nào",
                  "Đọc tệp kê khai trong gói cài đặt"])
_rows += [
    ["Chi phí bản quyền phần mềm", "0 đồng", "Toàn bộ thành phần dùng giấy phép mở"],
    ["Chi phí đầu tư hạ tầng máy chủ", "0 đồng", "Thiết kế không có thành phần máy chủ"],
]
bang(doc, "Các chỉ số đã đo được tại thời điểm lập hồ sơ",
     ["Chỉ số", "Giá trị", "Nguồn số liệu"], _rows, widths=[6.4, 4.6, 4.5])

h1(doc, "III. HIỆU QUẢ MANG LẠI KHI ÁP DỤNG")

h2(doc, "1. Hiệu quả kinh tế")
para(doc,
     "Sáng kiến không phát sinh chi phí bản quyền phần mềm, không yêu cầu đầu tư máy chủ, "
     "không phát sinh chi phí thuê bao dịch vụ và chạy trên thiết bị sẵn có của người dùng. "
     "Hiệu quả kinh tế thể hiện ở việc tránh được chi phí mua sắm giải pháp thương mại tương "
     "đương và chi phí duy trì hạ tầng đi kèm, đồng thời tránh chi phí đào tạo lại khi đổi "
     "nhà cung cấp vì sản phẩm do đơn vị hoàn toàn làm chủ.")
para(doc,
     "Tác giả không quy đổi thành con số tiền cụ thể, vì con số đó phụ thuộc quy mô triển khai "
     "và chính sách mua sắm của từng đơn vị; đưa ra ước lượng khi chưa triển khai sẽ không có "
     "căn cứ và làm giảm độ tin cậy của hồ sơ.", italic=True)

h2(doc, "2. Hiệu quả kỹ thuật")
for t in [
    "Bảo vệ dữ liệu ở trạng thái lưu trữ ngay trên thiết bị, lấp khoảng trống mà cơ chế mã "
    "hoá toàn thiết bị của hệ điều hành không xử lý được: khi máy đã mở khoá, dữ liệu trong "
    "két vẫn đòi hỏi mật khẩu riêng.",
    "Dữ liệu tiếp tục được bảo vệ sau khi rời khỏi thiết bị: tệp két tự mang cơ chế bảo vệ "
    "nên mở ở máy khác vẫn phải có mật khẩu.",
    "Phát hiện được mọi sửa đổi trên tệp nhờ chữ ký ràng buộc do tác giả thiết kế, kể cả thủ "
    "đoạn ghép nối tệp từ nhiều nguồn.",
    "Khắc phục rủi ro mất dữ liệu do quên mật khẩu bằng cơ chế chia khoá theo ngưỡng, không "
    "phải gửi khoá cho bên thứ ba giữ hộ.",
    "Loại bỏ được siêu dữ liệu ẩn trong ảnh ngay trên điện thoại — nơi dữ liệu đó phát sinh — "
    "thay vì phải chuyển ảnh sang máy tính để xử lý.",
    "Tệp tạo ra theo chuẩn mở nên liên thông được với hệ sinh thái công cụ sẵn có, không khoá "
    "người dùng vào một sản phẩm duy nhất.",
]:
    bullet(doc, t)

h2(doc, "3. Hiệu quả về quốc phòng – an ninh và xã hội")
for t in [
    "Góp phần bảo đảm an toàn cho dữ liệu nội bộ phát sinh trong công tác và huấn luyện khi "
    "được lưu trữ, sử dụng trên thiết bị di động có tính cơ động cao.",
    "Bảo đảm chủ quyền dữ liệu: toàn bộ quá trình xử lý diễn ra trên thiết bị, khoá do người "
    "dùng nắm giữ, sản phẩm không có thành phần máy chủ và không khai báo quyền truy cập "
    "mạng nên về mặt kỹ thuật không thể gửi dữ liệu ra ngoài.",
    "Giảm phụ thuộc vào phần mềm bảo mật nước ngoài mã nguồn đóng: toàn bộ thiết kế và mã "
    "nguồn do tác giả xây dựng, đơn vị kiểm soát được và có bộ kiểm thử để kiểm chứng lại.",
    "Hạn chế thói quen chuyển tài liệu nội bộ qua ứng dụng nhắn tin hoặc lưu trữ đám mây "
    "không kiểm soát, bằng cách cung cấp phương án thay thế thuận tiện ngay trên máy.",
    "Nâng cao nhận thức và kỹ năng an toàn thông tin cho cán bộ, học viên thông qua việc trực "
    "tiếp sử dụng và quan sát kết quả của các biện pháp bảo vệ dữ liệu.",
    "Phục vụ trực tiếp công tác đào tạo: sản phẩm là học cụ minh hoạ nhiều nội dung trong "
    "chương trình an toàn thông tin, đồng thời mã nguồn mở cho phép tổ chức các bài học phân "
    "tích mã nguồn của một hệ thống an toàn thực tế — hình thức huấn luyện sát thực tế mà "
    "phần mềm thương mại không đáp ứng được.",
]:
    bullet(doc, t)

h1(doc, "IV. PHẠM VI VÀ ĐIỀU KIỆN ÁP DỤNG")
para(doc,
     "Sản phẩm áp dụng được ngay với điều kiện tối thiểu: một điện thoại chạy hệ điều hành "
     "Android, không cần quyền quản trị thiết bị, không cần máy chủ và không cần kết nối "
     "mạng. Người dùng chỉ cần hướng dẫn sử dụng cơ bản và nắm nguyên tắc bảo quản mật khẩu.")
para(doc,
     "Việc sử dụng sản phẩm cho từng loại tài liệu phải tuân thủ quy định hiện hành của cơ "
     "quan có thẩm quyền về bảo vệ bí mật nhà nước và quy chế của đơn vị. Hồ sơ này không "
     "đưa ra tuyên bố về việc sản phẩm được phép xử lý tài liệu thuộc danh mục bí mật nhà "
     "nước ở cấp độ cụ thể.", italic=True)

khung_nhan_manh(
    doc,
    "Kết luận",
    ["Sáng kiến đã có sản phẩm hoàn chỉnh, đóng gói được và kiểm chứng bằng số liệu khách quan "
     "ở nhiều mức, mang lại đồng thời giá trị sử dụng trong công tác và giá trị phục vụ đào "
     "tạo an toàn thông tin.",
     "Toàn bộ ý tưởng giải pháp, kiến trúc hệ thống, thuật toán tổ chức dữ liệu và mã nguồn "
     "là kết quả nghiên cứu của tác giả."],
)

chu_ky(doc, ("CÁN BỘ THỰC HIỆN", "(Ký, ghi rõ họ tên)"),
       ("THỦ TRƯỞNG ĐƠN VỊ CHỦ TRÌ THỰC HIỆN", "(Ký, đóng dấu)"))

doc.save(str(BASE / "docx" / "03-Xac-nhan-danh-gia-hieu-qua.docx"))
print("Đã tạo 03-Xac-nhan-danh-gia-hieu-qua.docx")
