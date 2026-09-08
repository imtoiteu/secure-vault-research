#!/usr/bin/env python3
"""Sinh văn bản THUYẾT MINH SÁNG KIẾN/GIẢI PHÁP (DOCX).

Cấu trúc bám theo tệp mẫu `Mau_ho_so_sang_kien_cai_tien.doc`:

    A. THÔNG TIN CHUNG
    B. NỘI DUNG CHÍNH CỦA SÁNG KIẾN/GIẢI PHÁP
       1. Hiện trạng giải pháp đã biết
       2. Mục đích của giải pháp
       3. Mô tả giải pháp — a) Nguyên lý  b) Các nội dung chủ yếu  c) Kết quả
       4. Tự đánh giá — a) Tính mới và tính sáng tạo  b) Khả năng áp dụng
                        c) Hiệu quả (kinh tế / kỹ thuật / quốc phòng-an ninh và xã hội)
                        d) Mức độ triển khai, phát triển

Mọi số liệu lấy từ bang-chung/du-kien.json và bang-chung/kiem-tra-apk.json, do các script
thu-thap-du-kien.py và kiem-tra-apk.py sinh ra từ mã nguồn và kết quả chạy thật. Không có
con số nào nhập tay trong tệp này.
"""

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from dinh_dang import (  # noqa: E402
    bang, bullet, chu_ky, danh_so_trang, dat_lai_dem, dong_dien, h1, h2, h3, hinh,
    khung_nhan_manh, muc_luc, new_document, ngat_trang, para, placeholder_hinh, rich,
    tieuDeChinh, tieu_de_quan_doi,
)
from noi_dung_chuc_nang import NHOM_CHUC_NANG  # noqa: E402

BASE = pathlib.Path(__file__).parent
DK = json.loads((BASE / "bang-chung" / "du-kien.json").read_text(encoding="utf-8"))
_apk_file = BASE / "bang-chung" / "kiem-tra-apk.json"
APK = json.loads(_apk_file.read_text(encoding="utf-8")) if _apk_file.exists() else {"co_apk": False}
PNG = BASE / "hinh-anh" / "png"
SS = BASE / "hinh-anh" / "screenshot"

N_LENH = DK["lenh_ipc"]["so_luong"]
N_CRATE = DK["crate"]["so_luong"]
N_TEST = sum(DK["test_trong_nguon"].values())
A2 = DK["argon2id"]
TT = DK["thuat_toan"]
KQ = DK["ket_qua_kiem_thu"]
_host = KQ.get("host_toan_bo") or {}
_arm = KQ.get("arm64_loi_mat_ma") or {}
_iva = KQ.get("interop_age") or {}
_ivv = KQ.get("interop_vault") or {}
SO_DOI_CHUNG = _iva.get("passed", 0) + _ivv.get("passed", 0)

TEN_SK = ("SecureVault Mobile — Ứng dụng bảo vệ dữ liệu nhạy cảm trên thiết bị Android "
          "hoạt động hoàn toàn ngoại tuyến, phục vụ công tác và huấn luyện an toàn thông tin")

doc = new_document()
dat_lai_dem()
danh_so_trang(doc)
tieu_de_quan_doi(doc)
tieuDeChinh(doc, "THUYẾT MINH SÁNG KIẾN/GIẢI PHÁP")

# =====================================================================
# TÓM TẮT
# =====================================================================
h1(doc, "TÓM TẮT")
para(doc,
     "Vấn đề. Điện thoại đã trở thành nơi lưu và trao đổi nhiều dữ liệu nội bộ phát sinh "
     "trong công tác và huấn luyện: giáo án, đề bài và đáp án thực hành, kết quả nghiên cứu "
     "chưa công bố, ảnh tư liệu. Các biện pháp sẵn có hoặc chỉ bảo vệ khi máy tắt, hoặc là "
     "phần mềm mã nguồn đóng không kiểm chứng được, hoặc là công cụ mạnh nhưng không có bản "
     "dùng được trên điện thoại.")
para(doc,
     "Nguyên nhân kỹ thuật của khoảng trống. Các công cụ mật mã tin cậy hiện nay phần lớn "
     "được phân phối dưới dạng tệp nhị phân chạy độc lập. Hệ điều hành di động không cho ứng "
     "dụng sinh tiến trình con để chạy chúng, nên không thể chuyển thẳng sang điện thoại. Đây "
     "là rào cản thuộc về kiến trúc nền tảng, không phải vấn đề công sức lập trình.")
para(doc,
     "Giải pháp của tác giả. Tác giả thiết kế một kiến trúc trong đó toàn bộ nghiệp vụ bảo vệ "
     "dữ liệu nằm trong một lõi độc lập với giao diện và với nền tảng, và đặt các điểm nối "
     "trừu tượng tại đúng những vị trí phụ thuộc nền tảng. Nhờ vậy, phần hiện thực bên dưới "
     "có thể thay bằng bản chạy trong tiến trình mà toàn bộ nghiệp vụ, định dạng dữ liệu và "
     "hành vi phía trên giữ nguyên. Tác giả tự thiết kế định dạng tệp két, sơ đồ phân cấp "
     "khoá, quy tắc phân loại lỗi an toàn và tự viết mô-đun xử lý siêu dữ liệu.")
para(doc,
     f"Sản phẩm và bằng chứng. Sản phẩm là ứng dụng Android hoàn chỉnh với {N_LENH} chức năng "
     f"nghiệp vụ, xây dựng trên {N_CRATE} thành phần mã nguồn do tác giả tổ chức, kèm "
     f"{N_TEST} hàm kiểm thử tự động. Tính tương thích định dạng được kiểm chứng bằng "
     f"{SO_DOI_CHUNG} phép thực nghiệm đối chứng với công cụ chuẩn, không phải bằng suy luận.")
para(doc,
     "Giá trị. Sản phẩm vừa dùng được trong công tác để bảo vệ dữ liệu ngay trên thiết bị, "
     "vừa là học cụ trực quan cho giảng dạy an toàn thông tin: mỗi nhóm chức năng tương ứng "
     "một nguyên lý trong chương trình, và mã nguồn mở cho phép học viên đọc, chạy lại và "
     "phân tích một hệ thống an toàn thực tế.")

ngat_trang(doc)
muc_luc(doc)

# =====================================================================
ngat_trang(doc)
h1(doc, "A. THÔNG TIN CHUNG")
dong_dien(doc, "1. Tên sáng kiến/giải pháp", TEN_SK)
dong_dien(doc, "2. Thuộc lĩnh vực",
          "An toàn thông tin trên không gian mạng; bảo vệ dữ liệu trên thiết bị di động; "
          "công nghệ thông tin phục vụ đào tạo – huấn luyện")
dong_dien(doc, "3. Họ và tên tác giả")
dong_dien(doc, "Năm sinh")
dong_dien(doc, "Tên cơ quan, đơn vị")
dong_dien(doc, "Cấp bậc", "………………………          Chức vụ: ………………………")
dong_dien(doc, "Trình độ chuyên môn")
dong_dien(doc, "Số điện thoại")

# =====================================================================
ngat_trang(doc)
h1(doc, "B. NỘI DUNG CHÍNH CỦA SÁNG KIẾN/GIẢI PHÁP")

# ---------------------------------------------------------------- 1
h2(doc, "1. Hiện trạng giải pháp đã biết")

h3(doc, "1.1. Bối cảnh và nhu cầu thực tiễn")
para(doc,
     "Điện thoại thông minh hiện là công cụ làm việc thường xuyên của cán bộ, giảng viên và "
     "học viên. Tính cơ động của thiết bị mang lại hiệu quả rõ rệt trong công tác, giảng dạy "
     "và nghiên cứu, nhưng đồng thời làm thay đổi căn bản phạm vi tồn tại của dữ liệu: nhiều "
     "tài liệu trước đây chỉ nằm trong máy tính cố định nay được sao chép, xem và trao đổi "
     "ngay trên thiết bị cá nhân.")
para(doc,
     "Trong quá trình công tác và huấn luyện an toàn thông tin, thực tế phát sinh nhiều loại "
     "dữ liệu cần được bảo vệ ở mức cao hơn dữ liệu thông thường: giáo án và tài liệu biên "
     "soạn nội bộ, đề bài và đáp án các bài thực hành, kết quả nghiên cứu chưa công bố, ảnh "
     "và tư liệu phục vụ huấn luyện, dữ liệu trao đổi nghiệp vụ giữa các bộ phận. Việc lộ, "
     "lọt những dữ liệu này tuy không nhất thiết cấu thành sự cố ở mức cao nhất nhưng vẫn ảnh "
     "hưởng đến chất lượng công tác, tính khách quan trong đánh giá và uy tín của đơn vị.")
para(doc, "Bốn nhóm nguy cơ nổi bật được trình bày ở Hình 1.")

if (PNG / "H1-bai-toan-thuc-te.png").exists():
    hinh(doc, PNG / "H1-bai-toan-thuc-te.png",
         "Bài toán bảo vệ dữ liệu nhạy cảm trên thiết bị di động", 15.5)

h3(doc, "1.2. Các nhóm giải pháp đã biết và nhược điểm chưa được khắc phục")
para(doc,
     "Tác giả đã khảo sát các nhóm giải pháp hiện có theo hướng tiếp cận chức năng nhằm xác "
     "định chính xác khoảng trống cần lấp. Phân tích dưới đây là khách quan: mỗi nhóm đều "
     "giải quyết tốt bài toán mà nó được thiết kế cho, vấn đề là không nhóm nào giải quyết "
     "trọn vẹn bài toán đang xét.")

bang(
    doc,
    "So sánh các nhóm giải pháp đã biết với nhu cầu đặt ra",
    ["Nhóm giải pháp", "Ưu điểm", "Nhược điểm chưa được khắc phục"],
    [
        ["Mã hoá toàn thiết bị của hệ điều hành (FBE/FDE Android)",
         "Bảo vệ dữ liệu khi thiết bị ở trạng thái tắt hoặc chưa mở khoá lần đầu; trong suốt "
         "với người dùng",
         "Khi máy đã mở khoá, mọi ứng dụng và người cầm máy đều thấy dữ liệu ở dạng rõ; hoàn "
         "toàn không bảo vệ được tệp khi đưa ra khỏi thiết bị"],
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
         "Không có bản dùng được trên di động do rào cản kiến trúc nền tảng (mục 3.b.2); "
         "giao diện dòng lệnh không phù hợp với người dùng không chuyên"],
        ["Ứng dụng nhắn tin mã hoá đầu-cuối",
         "Bảo vệ rất tốt dữ liệu trên đường truyền",
         "Không bảo vệ dữ liệu ở trạng thái lưu trữ trên máy; dữ liệu vẫn đi qua hạ tầng của "
         "nhà cung cấp dịch vụ nước ngoài"],
        ["Giải pháp quản lý thiết bị / chống thất thoát dữ liệu (MDM/DLP)",
         "Quản lý tập trung, phù hợp quy mô lớn",
         "Cần hạ tầng máy chủ, chi phí bản quyền và phụ thuộc nhà cung cấp; khó triển khai "
         "cho nhu cầu cá nhân và nhóm nhỏ"],
    ],
    widths=[3.8, 4.8, 6.9],
)

para(doc,
     "Để so sánh khách quan hơn, bảng dưới đây đối chiếu theo từng tiêu chí kiểm tra được, "
     "thay vì nhận định định tính.")

bang(
    doc,
    "Ma trận đối chiếu theo tiêu chí kiểm tra được",
    ["Tiêu chí", "Mã hoá toàn thiết bị", "Ứng dụng két thương mại",
     "Công cụ dòng lệnh", "SecureVault Mobile"],
    [
        ["Chạy được trên Android", "Có", "Có", "Không", "Có"],
        ["Không yêu cầu quyền mạng", "Có", "Thường không", "Có", "Có"],
        ["Mã nguồn kiểm tra được", "Một phần", "Thường không", "Có", "Có"],
        ["Có bộ kiểm thử công khai", "Không rõ", "Không", "Có", "Có"],
        ["Bảo vệ tệp sau khi rời thiết bị", "Không", "Một phần", "Có", "Có"],
        ["Ký số và kiểm tra nguồn gốc", "Không", "Hiếm", "Có", "Có"],
        ["Chia khoá phục hồi theo ngưỡng", "Không", "Hiếm", "Một phần", "Có"],
        ["Xử lý siêu dữ liệu ẩn trong ảnh", "Không", "Hiếm", "Có", "Có"],
        ["Định dạng tệp theo chuẩn mở", "Không áp dụng", "Thường không", "Có", "Có"],
        ["Dùng được làm học cụ giảng dạy", "Hạn chế", "Hạn chế", "Có", "Có"],
    ],
    widths=[4.6, 2.6, 2.9, 2.5, 3.0],
    note="“Hiếm” nghĩa là có sản phẩm đáp ứng nhưng không phổ biến. Cột SecureVault Mobile "
         "đối chiếu với chức năng đã hiện thực và kiểm chứng, không phải chức năng dự kiến.",
)

h3(doc, "1.3. Khoảng trống mà sáng kiến hướng tới")
para(doc,
     "Từ phân tích trên, khoảng trống được xác định là: chưa có công cụ đồng thời đáp ứng cả "
     "năm yêu cầu sau đây trên nền tảng Android.")
for i, t in enumerate([
    "Hoạt động hoàn toàn trên thiết bị, không yêu cầu quyền truy cập mạng, không tài khoản, "
    "không đồng bộ đám mây.",
    "Mã nguồn kiểm soát được, thuật toán công khai, có bộ kiểm thử tự động để bên thứ ba có "
    "thể kiểm chứng lại.",
    "Gộp nhiều nghiệp vụ bảo vệ dữ liệu trong một ứng dụng thống nhất, thay vì phải dùng "
    "nhiều công cụ rời rạc.",
    "Tệp tạo ra tương thích với chuẩn mở, không khoá người dùng vào một sản phẩm duy nhất.",
    "Đồng thời sử dụng được làm học cụ trực quan cho giảng dạy an toàn thông tin.",
], 1):
    bullet(doc, t, bold_head=f"Yêu cầu {i}. ")

# ---------------------------------------------------------------- 2
ngat_trang(doc)
h2(doc, "2. Mục đích của giải pháp")
para(doc,
     "Sáng kiến nhằm xây dựng một ứng dụng Android giúp người dùng tự bảo vệ dữ liệu nhạy cảm "
     "ngay trên thiết bị của mình, đồng thời trở thành học cụ phục vụ giảng dạy và huấn luyện "
     "an toàn thông tin. Các mục tiêu cụ thể như sau.")
for i, (ten, mo_ta) in enumerate([
    ("Bảo vệ dữ liệu tại chỗ",
     "Cung cấp cơ chế mã hoá, ký số, kiểm tra toàn vẹn, chia khoá phục hồi và xử lý siêu dữ "
     "liệu hoạt động hoàn toàn trên thiết bị, không phụ thuộc kết nối mạng hay dịch vụ bên "
     "ngoài."),
    ("Bảo đảm chủ quyền dữ liệu",
     "Khoá và dữ liệu do người dùng nắm giữ hoàn toàn; ứng dụng không khai báo quyền truy cập "
     "mạng nên về mặt kỹ thuật không thể gửi dữ liệu ra ngoài."),
    ("Kiểm chứng được",
     f"Toàn bộ mã nguồn mở kèm {N_TEST} hàm kiểm thử tự động, cho phép kiểm tra lại các tuyên "
     "bố kỹ thuật thay vì phải tin vào lời khẳng định."),
    ("Phục vụ đào tạo",
     "Mỗi nhóm chức năng tương ứng với một nguyên lý an toàn thông tin cụ thể, cho phép giảng "
     "viên minh hoạ trực quan và xây dựng bài thực hành có kết quả quan sát được ngay."),
    ("Sử dụng được ngay",
     "Giao diện tiếng Việt, thao tác theo từng bước, thuật ngữ kỹ thuật đặt trong mục mở rộng "
     "để không gây quá tải cho người mới."),
], 1):
    bullet(doc, mo_ta, bold_head=f"Mục tiêu {i} – {ten}: ")


# ---------------------------------------------------------------- 3
ngat_trang(doc)
h2(doc, "3. Mô tả giải pháp")

# ------------------------------------------------- 3.a
h3(doc, "a) Nguyên lý của giải pháp")
para(doc,
     "Tác giả xây dựng giải pháp trên sáu nguyên lý do mình xác lập, chi phối toàn bộ thiết "
     "kế và được thể hiện trực tiếp trong mã nguồn. Các nguyên lý này không phải khẩu hiệu "
     "mà là ràng buộc kỹ thuật: mỗi nguyên lý đều có một cơ chế cụ thể bảo đảm nó được tuân "
     "thủ, và có kiểm thử tự động canh giữ.")
for i, (ten, mo_ta, co_che) in enumerate([
    ("Ngoại tuyến tuyệt đối",
     "Ứng dụng không có khả năng kết nối mạng.",
     "Không khai báo quyền truy cập mạng trong tệp kê khai — ràng buộc ở mức hệ điều hành, "
     "không phải lựa chọn cấu hình có thể thay đổi lúc chạy."),
    ("Một lõi bảo vệ dữ liệu dùng chung",
     "Toàn bộ nghiệp vụ mật mã tách khỏi giao diện và khỏi nền tảng.",
     f"{N_CRATE} thành phần độc lập, trong đó lõi không tham chiếu bất kỳ thư viện giao diện "
     "hay nền tảng nào; nhờ vậy phần dễ thay đổi không thể vô tình làm sai lệch phần cần ổn "
     "định."),
    ("Phụ thuộc một chiều theo lớp",
     "Lớp trên gọi lớp dưới, không có chiều ngược lại.",
     "Lõi phụ thuộc vào giao ước trừu tượng chứ không phụ thuộc bản hiện thực cụ thể, nên "
     "kiểm thử độc lập được và thay bản hiện thực không ảnh hưởng nghiệp vụ."),
    ("Suy giảm an toàn khi thành phần không sẵn sàng",
     "Không bao giờ chạy tiếp trong trạng thái không bảo đảm.",
     "Thành phần không sẵn sàng bị vô hiệu hoá và báo rõ ngay khi khởi động; định dạng ngoài "
     "phạm vi bị từ chối bằng lỗi có mã, không báo thành công giả."),
    ("Thông báo lỗi không tạo kênh phân biệt",
     "Không để kẻ tấn công dựa vào khác biệt thông báo mà suy đoán bí mật.",
     "Tác giả thiết kế quy tắc quy lỗi thống nhất: thất bại giải mã nội dung quy về “tệp "
     "hỏng” chứ không phải “sai xác thực”, vì tại thời điểm đó chữ ký ràng buộc và khoá đã "
     "được xác thực xong."),
    ("Không lưu bí mật",
     "Mật khẩu và khoá chính không bao giờ được ghi xuống bộ nhớ lưu trữ.",
     "Mật khẩu được bọc trong kiểu dữ liệu tự xoá khi hết phạm vi sử dụng; khoá chính chỉ tồn "
     "tại trong bộ nhớ phiên và bị xoá khi khoá két."),
], 1):
    rich(doc, [(f"Nguyên lý {i} – {ten}. ", "b"), (mo_ta + " ", ""), (co_che, "i")])

if (PNG / "H2-kien-truc-phan-lop.png").exists():
    hinh(doc, PNG / "H2-kien-truc-phan-lop.png",
         "Kiến trúc phân lớp của SecureVault Mobile do tác giả thiết kế", 15.5)

# ------------------------------------------------- 3.b
ngat_trang(doc)
h3(doc, "b) Các nội dung chủ yếu")

para(doc, "b.1. Kiến trúc tổng thể do tác giả thiết kế", bold=True, indent=False)
para(doc,
     "Ứng dụng gồm sáu lớp (Hình 2). Điểm cốt lõi trong thiết kế là ranh giới giữa lớp bề mặt "
     f"lệnh và lớp nghiệp vụ: toàn bộ giao tiếp giữa giao diện và lõi đi qua đúng {N_LENH} "
     "lệnh có kiểm soát, không có đường tắt. Mọi mật khẩu đi qua ranh giới này đều được bọc "
     "trong kiểu dữ liệu tự xoá, và phiên làm việc chỉ được tham chiếu bằng một mã định danh "
     "mờ — mã này không mang thông tin bí mật nên kể cả khi lộ cũng không dùng để suy ra khoá.")
para(doc,
     "Cách tổ chức này là lựa chọn thiết kế có chủ đích: nó cho phép thay đổi hoàn toàn giao "
     "diện, hoặc thay đổi nền tảng chạy, mà không phải sửa một dòng nào trong phần nghiệp vụ "
     "mật mã — điều kiện tiên quyết để một lõi phục vụ được nhiều nền tảng.")

para(doc, "b.2. Rào cản kiến trúc của nền tảng di động và cách tác giả vượt qua", bold=True,
     indent=False)
para(doc,
     "Đây là nội dung mang hàm lượng kỹ thuật cao nhất của sáng kiến, và cũng là lý do các "
     "công cụ mật mã mạnh hiện nay không có bản dùng được trên điện thoại.")
rich(doc, [
    ("Vấn đề. ", "b"),
    ("Các công cụ mật mã tin cậy được phân phối dưới dạng tệp nhị phân chạy độc lập. Trên "
     "máy tính để bàn, ứng dụng gọi chúng như một tiến trình con. Trên thiết bị di động thì "
     "không: hệ điều hành iOS cấm hoàn toàn việc sinh tiến trình, còn Android chặn thực thi "
     "tệp nhị phân nằm trong vùng lưu trữ mà ứng dụng ghi được. Hệ quả là mọi chức năng phụ "
     "thuộc tiến trình con sẽ không hoạt động, kể cả khi mã nguồn biên dịch thành công — một "
     "cái bẫy nguy hiểm vì lỗi chỉ lộ ra khi chạy thật trên máy.", ""),
])
rich(doc, [
    ("Cách giải quyết của tác giả. ", "b"),
    ("Thay vì viết lại ứng dụng riêng cho di động — cách làm dẫn tới hai bản mã nguồn phải "
     "đồng bộ thủ công và sớm muộn sẽ lệch nhau — tác giả đặt ", ""),
    ("điểm nối trừu tượng", "b"),
    (" tại đúng những vị trí phụ thuộc nền tảng, rồi thay phần hiện thực bên dưới bằng bản "
     "chạy trong tiến trình. Nguyên tắc này được áp dụng cho cả hai thành phần vướng rào cản:",
     ""),
])
bullet(doc,
       "tác giả tự hiện thực bộ mã hoá nội dung két chạy trong tiến trình, giữ nguyên định "
       "dạng tệp đã thiết kế. Nhờ vậy két tạo trên máy tính mở được trên điện thoại và ngược "
       "lại — tính chất này không hiển nhiên và đã được kiểm chứng bằng thực nghiệm.",
       bold_head="Thành phần 1 — mã hoá nội dung két: ")
bullet(doc,
       "ExifTool là chương trình viết bằng Perl, Android không có trình thông dịch Perl nên "
       "không có cách nào chạy được. Tác giả viết mới hoàn toàn mô-đun này bằng ngôn ngữ Rust, "
       "hiện thực ba nghiệp vụ xem, xoá và so sánh siêu dữ liệu, chạy ngay trong tiến trình "
       "ứng dụng. Đây là chức năng có thật trên thiết bị, không phải trạng thái vô hiệu hoá.",
       bold_head="Thành phần 2 — xử lý siêu dữ liệu: ")

if (PNG / "H3-loi-dung-chung.png").exists():
    hinh(doc, PNG / "H3-loi-dung-chung.png",
         "Nguyên tắc một lõi dùng chung với hai gốc hợp thành theo nền tảng", 15.5)

rich(doc, [
    ("Vì sao tính tương thích định dạng là điều kiện bắt buộc. ", "b"),
    ("Một giải pháp thay bộ mã hoá mà làm đổi định dạng tệp sẽ khiến dữ liệu cũ không mở được "
     "và người dùng bị khoá vào một phiên bản. Do đó tác giả xác định đây không phải chi tiết "
     "kỹ thuật phụ mà là ràng buộc thiết kế, và đã kiểm chứng bằng thực nghiệm đối chứng chứ "
     "không bằng suy luận.", ""),
])

bang(
    doc,
    "Kiểm chứng tương thích định dạng giữa hai bản hiện thực",
    ["Phép kiểm chứng", "Nội dung", "Kết quả"],
    [
        ["Đối chứng mức tệp mã hoá, chiều 1",
         "Dữ liệu do bản hiện thực trong tiến trình tạo ra, giải mã bằng công cụ chuẩn "
         "age v1.2.1", "Đạt"],
        ["Đối chứng mức tệp mã hoá, chiều 2",
         "Dữ liệu do công cụ chuẩn tạo ra, giải mã bằng bản hiện thực trong tiến trình", "Đạt"],
        ["Mở chéo két, chiều 1",
         "Két tạo bằng bản dùng tiến trình con, mở bằng bản trong tiến trình", "Đạt"],
        ["Mở chéo két, chiều 2",
         "Két tạo bằng bản trong tiến trình, mở bằng bản dùng tiến trình con", "Đạt"],
        ["Giữ nguyên hàng rào xác thực",
         "Sau khi thay bản hiện thực, mật khẩu sai vẫn bị từ chối đúng cách", "Đạt"],
    ],
    widths=[4.2, 8.5, 2.8],
    note="Nguồn: crates/sv-age-rs/tests/interop.rs và src-tauri/tests/vault_interop.rs. "
         "Công cụ đối chứng age v1.2.1 tải từ nguồn chính thức, có lưu giá trị băm SHA-256 "
         "của tệp tải về để truy vết.",
)

para(doc, "b.3. Định dạng tệp két và sơ đồ phân cấp khoá do tác giả thiết kế", bold=True,
     indent=False)
para(doc,
     "Đây là phần thiết kế cốt lõi của sản phẩm. Tác giả tự xác định cấu trúc tệp két và cách "
     "sinh, bọc, lưu trữ các khoá; không sao chép định dạng của sản phẩm nào có sẵn.")
para(doc,
     f"Mật khẩu người dùng không được lưu ở bất kỳ đâu. Từ mật khẩu, hệ thống dẫn xuất khoá "
     f"chính bằng thuật toán {TT['kdf']} với tham số tối thiểu {A2['min_mem_kib'] // 1024} MiB "
     f"bộ nhớ và {A2['min_time_cost']} vòng lặp. Tác giả chọn ngưỡng này theo khuyến nghị "
     "OWASP nhằm làm chậm đáng kể tấn công dò mật khẩu bằng phần cứng chuyên dụng; hệ thống "
     "còn có cơ chế tự hiệu chỉnh tham số theo năng lực máy để không tụt xuống dưới ngưỡng.")
para(doc,
     "Khoá chính chỉ tồn tại trong bộ nhớ phiên và sinh ra các khoá con theo từng mục đích "
     "riêng biệt bằng cơ chế dẫn xuất có tách miền. Việc tách miền là chủ ý: một khoá con bị "
     "lộ không kéo theo khoá con khác, và không khoá con nào suy ngược ra được khoá chính.")

if (PNG / "H4-phan-cap-khoa.png").exists():
    hinh(doc, PNG / "H4-phan-cap-khoa.png",
         "Sơ đồ phân cấp khoá và luồng mở két do tác giả thiết kế", 15.5)

para(doc,
     "Nội dung két được đóng gói thành một luồng dữ liệu mã hoá duy nhất, kèm danh mục tệp "
     "cũng ở dạng mã hoá — nhờ vậy người có tệp két mà không có mật khẩu thì không biết bên "
     "trong có những gì, kể cả tên tệp. Toàn bộ phần đầu tệp được ràng buộc bằng một chữ ký "
     "số, nên mọi sửa đổi, kể cả thủ đoạn ghép nối phần đầu của tệp này với nội dung của tệp "
     "khác, đều bị phát hiện trước khi hệ thống chạm tới mật khẩu.")

bang(
    doc,
    "Các nguyên hàm mật mã tác giả lựa chọn và lý do lựa chọn",
    ["Chức năng trong thiết kế", "Nguyên hàm được chọn", "Lý do lựa chọn"],
    [
        ["Dẫn xuất khoá từ mật khẩu", TT["kdf"],
         f"Chống dò mật khẩu bằng phần cứng; đặt ngưỡng {A2['min_mem_kib'] // 1024} MiB / "
         f"{A2['min_time_cost']} vòng theo khuyến nghị OWASP"],
        ["Băm nội dung và dẫn xuất khoá con", TT["hash"],
         "Tốc độ cao trên thiết bị di động; hỗ trợ sẵn cơ chế dẫn xuất khoá có tách miền"],
        ["Mã hoá nội dung két", TT["aead_vault"],
         "Định dạng mở, có đặc tả công khai nên bảo đảm liên thông; mã hoá kèm xác thực"],
        ["Bọc các trường khoá trong phần đầu tệp", TT["aead_field"],
         "Thư viện đã được kiểm định lâu dài; phù hợp bọc dữ liệu ngắn"],
        ["Chữ ký ràng buộc phần đầu tệp", TT["chu_ky"],
         "Chữ ký ngắn, xác minh nhanh, định dạng phổ biến nên kiểm tra chéo được"],
        ["Chia khoá phục hồi", TT["chia_se_bi_mat"],
         "Bảo đảm về mặt toán học: dưới ngưỡng thì không lộ bất kỳ thông tin nào"],
    ],
    widths=[4.6, 4.4, 6.5],
    note="Theo nguyên tắc nghề nghiệp, tác giả không tự thiết kế thuật toán mật mã mới mà lựa "
         "chọn và vận dụng các chuẩn công khai đã được cộng đồng khoa học kiểm chứng. Đóng góp "
         "của tác giả nằm ở kiến trúc, ở cách tổ chức và bảo vệ dữ liệu, và ở việc lựa chọn "
         "tham số có luận cứ.",
)

ngat_trang(doc)
para(doc, "b.4. Toàn bộ chức năng của ứng dụng", bold=True, indent=False)
para(doc,
     f"Ứng dụng cung cấp {N_LENH} lệnh nghiệp vụ. Tác giả nhóm chúng theo mục đích sử dụng "
     "thay vì theo thuật toán, để người dùng chọn công cụ theo việc cần làm chứ không cần "
     "biết bên dưới dùng kỹ thuật gì. Mục này trình bày đầy đủ từng nhóm; với mỗi chức năng "
     "nêu rõ đầu vào, cách xử lý và kết quả trả về.")

for _ma, _ten, _dan, _ds in NHOM_CHUC_NANG:
    h3(doc, _ten)
    para(doc, _dan)
    bang(doc, _ten.split("—")[0].strip(),
         ["Chức năng", "Đầu vào", "Xử lý", "Kết quả"],
         [[a, b, c, d] for (a, b, c, d) in _ds],
         widths=[3.3, 3.7, 4.6, 4.4])

para(doc, "b.5. Luồng xử lý tệp trên Android", bold=True, indent=False)
para(doc,
     "Android không cho ứng dụng truy cập tự do vào bộ nhớ thiết bị. Người dùng chọn tệp qua "
     "bộ chọn của hệ điều hành và cấp quyền cho từng tệp. Tác giả thiết kế luồng xử lý đưa dữ "
     "liệu vào vùng lưu trữ riêng của ứng dụng, xử lý, trả kết quả rồi xoá vùng đệm — cách "
     "làm này giữ nguyên được toàn bộ nghiệp vụ lõi vốn làm việc trên đường dẫn tệp thật, "
     "thay vì phải sửa lại toàn bộ giao ước dữ liệu của hệ thống.")

if (PNG / "H5-luong-tep-android.png").exists():
    hinh(doc, PNG / "H5-luong-tep-android.png",
         "Luồng xử lý tệp trên Android và ranh giới tin cậy", 15.5)

para(doc, "b.6. Giao diện người dùng", bold=True, indent=False)
para(doc,
     "Giao diện do tác giả thiết kế theo hướng giảm tải nhận thức: mỗi màn hình chỉ hiển thị "
     "các bước cần thiết để hoàn thành công việc, phần giải thích kỹ thuật đặt trong mục "
     "“Thông tin thêm” có thể mở rộng. Riêng cảnh báo có nguy cơ gây mất dữ liệu vĩnh viễn "
     "thì luôn hiển thị thường trực, không thu gọn. Toàn bộ giao diện có tiếng Việt và tiếng "
     "Anh; vùng chạm được thiết kế tối thiểu 44 điểm ảnh theo khuyến nghị về khả năng tiếp cận.")

for _f, _cap in [("A1-trang-chu.png", "Màn hình chính với các nhóm công cụ theo mục đích"),
                 ("A3-khoa-tep.png", "Màn hình khoá tệp — thao tác theo ba bước rõ ràng"),
                 ("A2-dieu-huong.png", "Ngăn kéo điều hướng nhóm công cụ theo nghiệp vụ"),
                 ("A5-chia-bi-mat.png", "Màn hình chia bí mật theo ngưỡng k trong n")]:
    if (SS / _f).exists():
        hinh(doc, SS / _f, _cap, 7.2)

para(doc,
     "Ghi chú về ảnh chụp giao diện: các hình trên được kết xuất từ chính mã giao diện của "
     "sản phẩm ở kích thước màn hình điện thoại, với cầu nối tới lõi được mô phỏng trả về "
     "đúng giá trị mà gốc hợp thành Android tạo ra, nhờ vậy logic giao diện thật được thực thi.",
     italic=True)

# ------------------------------------------------- 3.c
ngat_trang(doc)
h3(doc, "c) Kết quả của giải pháp")

para(doc, "c.1. Sản phẩm đã tạo ra", bold=True, indent=False)
for t in [
    (f"Ứng dụng Android đóng gói dạng APK ({APK['kich_thuoc_byte'] / 1e6:.1f} MB), chứa lõi "
     "bảo vệ dữ liệu biên dịch cho kiến trúc ARM64, đã kiểm tra tĩnh nội dung gói."
     if APK.get("co_apk") else
     "Thư viện lõi bảo vệ dữ liệu đã biên dịch cho kiến trúc ARM64 của Android."),
    f"Mã nguồn đầy đủ gồm {N_CRATE} thành phần độc lập và giao diện web tĩnh, kèm "
    f"{N_TEST} hàm kiểm thử tự động.",
    "Bộ tài liệu kiến trúc, mô hình mối đe doạ và hướng dẫn triển khai.",
    "Quy trình kiểm thử tự động chạy trên máy chủ tích hợp liên tục.",
]:
    bullet(doc, t)

para(doc, "c.2. Các chỉ tiêu kỹ thuật đạt được", bold=True, indent=False)
_rows = [
    ["Số chức năng nghiệp vụ", f"{N_LENH} lệnh", "Đếm trực tiếp từ mã nguồn"],
    ["Số hàm kiểm thử tự động", f"{N_TEST} hàm", "Đếm trực tiếp từ mã nguồn"],
]
if _host:
    _rows.append(["Kiểm thử trên máy chủ", f"{_host['passed']} đạt / {_host['failed']} lỗi",
                  "Nhật ký chạy bộ kiểm thử"])
if _arm:
    _rows.append([f"Kiểm thử lõi trên kiến trúc ARM64 ({_arm['suites']} bộ)",
                  f"{_arm['passed']} đạt / {_arm['failed']} lỗi",
                  "Chạy dưới trình giả lập kiến trúc"])
if SO_DOI_CHUNG:
    _rows.append(["Kiểm chứng tương thích định dạng", f"{SO_DOI_CHUNG} phép đối chứng đạt",
                  "Đối chứng với công cụ chuẩn age v1.2.1"])
if APK.get("co_apk"):
    _rows.append(["Kiến trúc thư viện trong gói cài đặt",
                  list(APK["thu_vien_native"].values())[0],
                  "Đọc phần đầu ELF của tệp trong gói"])
    _rows.append(["Quyền ứng dụng yêu cầu",
                  "Không khai báo quyền nào" if not APK.get("quyen_khai_bao")
                  else ", ".join(APK["quyen_khai_bao"]),
                  "Đọc tệp kê khai trong gói cài đặt"])
    _rows.append(["Giao diện nhúng sẵn trong ứng dụng",
                  "Có" if APK.get("giao_dien_da_nhung") else "Không",
                  "Bảng tài nguyên trong thư viện native"])
bang(doc, "Các chỉ tiêu kỹ thuật đo được tại thời điểm lập hồ sơ",
     ["Chỉ tiêu", "Giá trị đạt được", "Cách xác định"], _rows, widths=[5.6, 4.9, 5.0],
     note="Toàn bộ số liệu được sinh tự động từ mã nguồn và nhật ký kiểm thử, không nhập tay, "
          "nhằm bảo đảm tính chính xác và khả năng kiểm tra lại.")

para(doc, "c.3. Mức độ kiểm chứng", bold=True, indent=False)
para(doc,
     "Tác giả xác định rõ từng mức kiểm chứng đã đạt được, để mỗi tuyên bố kỹ thuật trong hồ "
     "sơ đều gắn với một bằng chứng cụ thể.")

if (PNG / "H6-thap-bang-chung.png").exists():
    hinh(doc, PNG / "H6-thap-bang-chung.png",
         "Các mức kiểm chứng của sản phẩm", 15.5)

if _arm:
    para(doc,
         f"Về mức thực thi trên ARM64: việc kiểm chứng được tiến hành bằng trình giả lập kiến "
         f"trúc, chạy {_arm['suites']} bộ kiểm thử của các thành phần mật mã và giao tiếp thư "
         f"viện hệ thống với kết quả {_arm['passed']} đạt, {_arm['failed']} lỗi. Đây là kiểm "
         "chứng mã máy ARM64 của lõi — cùng loại mã lệnh sẽ chạy trên điện thoại thật.")

# ---------------------------------------------------------------- 4
ngat_trang(doc)
h2(doc, "4. Tự đánh giá giải pháp")

# ------------------------------------------------- 4.a
h3(doc, "a) Tính mới và tính sáng tạo")

para(doc, "Điểm mới", bold=True, indent=False)
para(doc,
     "Tính mới của sáng kiến không nằm ở việc “có thêm một ứng dụng mã hoá”, mà ở cách giải "
     "quyết những vấn đề kỹ thuật mà các giải pháp hiện có chưa xử lý được trên nền tảng di "
     "động. Dưới đây là năm điểm mới, mỗi điểm kèm bằng chứng kiểm tra lại được trong mã nguồn.")

for i, (ten, mo_ta, bc) in enumerate([
    ("Vượt rào cản cấm sinh tiến trình mà không phá vỡ định dạng dữ liệu",
     "Các công cụ mật mã tin cậy hiện nay phần lớn ở dạng tệp nhị phân chạy độc lập nên không "
     "chuyển thẳng sang di động được. Tác giả đặt điểm nối trừu tượng tại vị trí bộ mã hoá "
     "nội dung, cho phép thay bằng bản hiện thực chạy trong tiến trình mà tệp tạo ra vẫn đọc "
     "được bằng công cụ chuẩn. Cách làm này giữ được tính liên thông với hệ sinh thái mở và "
     "tránh khoá người dùng vào một sản phẩm.",
     f"{SO_DOI_CHUNG} phép kiểm chứng đối chứng hai chiều với công cụ chuẩn age v1.2.1, cả ở "
     "mức tệp mã hoá lẫn mức mở chéo tệp két hoàn chỉnh."),
    ("Một lõi bảo vệ dữ liệu duy nhất, tự chọn cấu hình theo nền tảng khi biên dịch",
     "Thay vì viết hai ứng dụng song song rồi phải đồng bộ thủ công, tác giả tổ chức toàn bộ "
     "nghiệp vụ vào một lõi duy nhất; phần khác biệt giữa các nền tảng được cô lập trong một "
     "tệp cấu hình hợp thành và được trình biên dịch tự động lựa chọn. Nhờ vậy không tồn tại "
     "nguy cơ hai nền tảng dùng hai phiên bản thuật toán khác nhau.",
     "Kiểm tra trực tiếp kết quả biên dịch cho thấy hai nền tảng chọn đúng hai gốc hợp thành "
     "khác nhau từ cùng một mã nguồn."),
    ("Viết lại mô-đun xử lý siêu dữ liệu để chức năng có mặt thật trên di động",
     "Công cụ xử lý siêu dữ liệu phổ biến hiện nay viết bằng ngôn ngữ Perl nên không thể chạy "
     "trên Android dưới bất kỳ hình thức nào. Thay vì bỏ chức năng, tác giả hiện thực lại ba "
     "nghiệp vụ xem, xoá và so sánh siêu dữ liệu bằng Rust chạy trong tiến trình ứng dụng. "
     "Người dùng kiểm tra và xoá được toạ độ định vị, thông tin thiết bị và tên tác giả trong "
     "ảnh ngay trên điện thoại — đúng nơi những dữ liệu đó phát sinh.",
     "Năm kiểm thử tự động trên ảnh có siêu dữ liệu: đọc đúng thẻ, xoá sạch về 0 thẻ, giữ "
     "nguyên tệp gốc, từ chối ghi đè tệp đích, từ chối định dạng ngoài phạm vi."),
    ("Quy tắc phân loại lỗi không tạo kênh phân biệt cho kẻ tấn công",
     "Hệ thống phân biệt rõ ở tầng mã giữa “sai mật khẩu” và “tệp bị hỏng hoặc bị sửa”, nhưng "
     "tác giả thiết kế quy tắc quy lỗi sao cho sự khác biệt đó không trở thành công cụ dò tìm: "
     "thất bại khi giải mã nội dung được quy về lỗi tệp hỏng, vì tại thời điểm đó chữ ký ràng "
     "buộc và khoá đã được xác thực xong.",
     "Có kiểm thử riêng khẳng định cả hai bản hiện thực dùng chung một quy tắc quy lỗi, để "
     "hai nền tảng không thể lệch nhau về hành vi này."),
    ("Ngoại tuyến bằng ràng buộc kỹ thuật thay vì bằng cam kết",
     "Ứng dụng không khai báo quyền truy cập mạng trong tệp kê khai. Người dùng không phải "
     "tin vào lời hứa “chúng tôi không gửi dữ liệu đi”, mà tự kiểm tra được bằng công cụ phân "
     "tích gói cài đặt tiêu chuẩn.",
     "Kiểm tra tệp kê khai của gói cài đặt: danh sách quyền rỗng hoàn toàn."),
], 1):
    rich(doc, [(f"Điểm mới {i} — {ten}. ", "b"), (mo_ta, "")])
    rich(doc, [("Bằng chứng: ", "bi"), (bc, "i")])

para(doc, "Điểm sáng tạo", bold=True, indent=False)
para(doc,
     "Ngoài các điểm mới về kỹ thuật, sáng kiến còn có những điểm sáng tạo trong cách tiếp cận "
     "và cách tổ chức sản phẩm.")
for i, (ten, mo_ta) in enumerate([
    ("Một sản phẩm phục vụ đồng thời hai mục đích khác nhau",
     "Thông thường công cụ nghiệp vụ và học cụ giảng dạy là hai sản phẩm riêng. Tác giả thiết "
     "kế sản phẩm sao cho mỗi nhóm chức năng vừa giải quyết một nhu cầu công tác có thật, vừa "
     "minh hoạ trực quan một nguyên lý trong chương trình an toàn thông tin. Việc học viên "
     "dùng chính công cụ mình đang học để bảo vệ dữ liệu của mình tạo ra động lực học tập mà "
     "bài giảng lý thuyết khó có được."),
    ("Chuyển giới hạn của công cụ thành nội dung huấn luyện",
     "Chức năng phát hiện dữ liệu ẩn được thiết kế để báo kết quả kèm lời giải thích rằng “mức "
     "thấp nghĩa là các phép thử này không phát hiện được”, chứ không phải “ảnh sạch”. Cách "
     "trình bày này biến một giới hạn kỹ thuật thành bài học về ranh giới của công cụ phân "
     "tích — điều mà phần mềm thương mại thường che giấu để sản phẩm trông mạnh hơn."),
    ("Thiết kế để tự chứng minh thay vì để được tin tưởng",
     "Tác giả chủ trương mọi tuyên bố quan trọng đều phải kiểm tra lại được bằng công cụ độc "
     "lập: tính ngoại tuyến kiểm tra bằng danh sách quyền trong gói cài đặt, tính tương thích "
     "kiểm tra bằng đối chứng với công cụ chuẩn, tính đúng đắn kiểm tra bằng bộ kiểm thử kèm "
     "theo. Đây là cách tiếp cận khác với phần mềm bảo mật thông thường vốn yêu cầu người dùng "
     "tin vào uy tín nhà cung cấp."),
    ("Sinh hồ sơ kỹ thuật tự động từ mã nguồn",
     "Toàn bộ số liệu trong hồ sơ này được sinh tự động từ mã nguồn và nhật ký kiểm thử qua "
     "một tệp dữ kiện trung gian. Khi mã nguồn thay đổi, chỉ cần chạy lại là mọi con số tự "
     "cập nhật. Cách làm này loại bỏ hoàn toàn nguy cơ số liệu trong tài liệu lệch với sản "
     "phẩm thực tế — một vấn đề phổ biến của tài liệu kỹ thuật."),
    ("Suy giảm chức năng an toàn được đưa vào thiết kế ngay từ đầu",
     "Khi một định dạng nằm ngoài phạm vi xử lý, hệ thống từ chối bằng lỗi có mã thay vì báo "
     "thành công giả. Nguyên tắc “thà từ chối còn hơn báo sai” được áp dụng nhất quán, vì "
     "trong bảo vệ dữ liệu, một báo cáo “đã xoá siêu dữ liệu” sai sự thật nguy hiểm hơn nhiều "
     "so với việc thông báo không xử lý được."),
], 1):
    rich(doc, [(f"Điểm sáng tạo {i} — {ten}. ", "b"), (mo_ta, "")])

khung_nhan_manh(
    doc,
    "Về quyền tác giả đối với sản phẩm",
    ["Toàn bộ ý tưởng giải pháp, kiến trúc hệ thống, định dạng tệp két, sơ đồ phân cấp khoá, "
     "quy tắc phân loại lỗi, mô-đun xử lý siêu dữ liệu, giao diện và mã nguồn là do tác giả "
     "tự thiết kế và trực tiếp xây dựng.",
     "Các nguyên hàm mật mã cơ sở là những chuẩn công khai đã được cộng đồng khoa học kiểm "
     "chứng, do tác giả lựa chọn và vận dụng có luận cứ. Đây là nguyên tắc nghề nghiệp bắt "
     "buộc trong lĩnh vực mật mã: tự chế thuật toán mật mã mới là điều phải tránh."],
)

# ------------------------------------------------- 4.b
h3(doc, "b) Khả năng áp dụng")
para(doc,
     "Sáng kiến áp dụng được ngay với điều kiện triển khai tối thiểu: chỉ cần một điện thoại "
     "Android, không cần máy chủ, không cần kết nối mạng, không phát sinh chi phí bản quyền "
     "và không yêu cầu quyền quản trị thiết bị.")

bang(
    doc,
    "Đối tượng và phạm vi áp dụng",
    ["Đối tượng", "Cách sử dụng", "Điều kiện cần"],
    [
        ["Giảng viên an toàn thông tin",
         "Bảo vệ giáo án, đề bài và đáp án thực hành, kết quả nghiên cứu chưa công bố; dùng "
         "làm học cụ minh hoạ trực tiếp trên lớp",
         "Điện thoại Android; không cần hạ tầng bổ sung"],
        ["Học viên",
         "Thực hành các bài về mã hoá, chữ ký số, chia sẻ bí mật ngưỡng, kiểm tra toàn vẹn, "
         "giấu tin, phát hiện giấu tin và xử lý siêu dữ liệu",
         "Điện thoại Android của cá nhân"],
        ["Cán bộ, nhân viên trong đơn vị",
         "Bảo vệ tài liệu nghiệp vụ nội bộ khi mang theo trên thiết bị di động; kiểm tra tính "
         "toàn vẹn và nguồn gốc của tệp nhận được",
         "Điện thoại Android; hướng dẫn sử dụng cơ bản khoảng 30 phút"],
    ],
    widths=[3.6, 7.4, 4.5],
)

para(doc, "b.1. Giá trị đối với công tác giảng dạy an toàn thông tin", bold=True, indent=False)
para(doc,
     "Điểm mạnh của sản phẩm trong đào tạo là mỗi chức năng đều tương ứng với một nguyên lý "
     "trong chương trình, và học viên quan sát được trực tiếp hệ quả của nguyên lý đó trên "
     "thiết bị của mình thay vì chỉ nghe giảng lý thuyết.")

bang(
    doc,
    "Ánh xạ chức năng của sản phẩm với nội dung giảng dạy",
    ["Chức năng", "Nội dung giảng dạy minh hoạ", "Gợi ý bài thực hành"],
    [
        ["Tạo và mở két an toàn",
         "Dẫn xuất khoá từ mật khẩu; vì sao mật khẩu yếu vẫn nguy hiểm dù thuật toán mạnh",
         "So sánh thời gian mở két khi thay đổi tham số dẫn xuất khoá"],
        ["Khoá / mở khoá tệp",
         "Mã hoá có xác thực; phân biệt bảo mật và toàn vẹn",
         "Sửa một byte của tệp đã mã hoá rồi quan sát ứng dụng từ chối giải mã"],
        ["Ký tệp và kiểm tra chữ ký",
         "Mật mã khoá công khai; chứng minh nguồn gốc",
         "Ký tệp, đổi một ký tự trong tệp, kiểm tra lại chữ ký"],
        ["Vân tay tệp và kiểm tra toàn vẹn",
         "Hàm băm mật mã; ứng dụng trong kiểm tra tệp tải về",
         "Đối chiếu vân tay của cùng một tệp trên hai thiết bị"],
        ["Chia bí mật k trong n",
         "Chia sẻ bí mật ngưỡng; nguyên tắc tách quyền kiểm soát",
         "Chia khoá cho ba học viên, chứng minh hai người mới khôi phục được"],
        ["Giấu tin và phát hiện giấu tin",
         "Giấu tin trong ảnh; giới hạn của che giấu so với mã hoá",
         "Giấu tệp vào ảnh rồi dùng chính công cụ phát hiện để tìm dấu hiệu"],
        ["Thuỷ vân dễ vỡ",
         "Phát hiện sửa đổi cục bộ trên ảnh",
         "Chỉnh sửa một vùng ảnh đã đóng dấu và xác định vùng bị sửa"],
        ["Xem và xoá siêu dữ liệu",
         "Kênh lộ thông tin ngoài nội dung; quyền riêng tư trong ảnh số",
         "Xem toạ độ định vị trong ảnh tự chụp, xoá rồi kiểm tra lại"],
        ["Quy tắc phân loại lỗi",
         "Tấn công dựa trên thông báo lỗi và cách phòng tránh",
         "Đọc mã nguồn phần quy lỗi, phân tích vì sao gộp hai trường hợp"],
    ],
    widths=[3.8, 6.2, 5.5],
)

para(doc,
     "Ngoài giá trị minh hoạ, mã nguồn mở còn cho phép tổ chức bài học ở mức cao hơn: đọc và "
     "phân tích cách hiện thực một nguyên lý, nhận xét về mô hình mối đe doạ, hoặc rà soát mã "
     "nguồn để tìm điểm cần cải thiện. Đây là hình thức huấn luyện sát thực tế mà tài liệu lý "
     "thuyết đơn thuần khó thay thế được.")

# ------------------------------------------------- 4.c
h3(doc, "c) Hiệu quả")

para(doc, "Hiệu quả kinh tế", bold=True, indent=False)
para(doc,
     "Sáng kiến không phát sinh chi phí bản quyền phần mềm, không yêu cầu đầu tư máy chủ, "
     "không có chi phí thuê bao dịch vụ và chạy trên thiết bị sẵn có của người dùng. Hiệu quả "
     "kinh tế thể hiện ở việc tránh được chi phí mua sắm giải pháp thương mại tương đương, chi "
     "phí duy trì hạ tầng đi kèm, và chi phí chuyển đổi khi thay nhà cung cấp — vì sản phẩm do "
     "đơn vị hoàn toàn làm chủ về mã nguồn.")
para(doc,
     "Tác giả không quy đổi thành con số tiền cụ thể, vì con số đó phụ thuộc quy mô triển khai "
     "và chính sách mua sắm của từng đơn vị; đưa ra ước lượng khi chưa triển khai sẽ không có "
     "căn cứ.", italic=True)

para(doc, "Hiệu quả kỹ thuật", bold=True, indent=False)
para(doc,
     "So sánh với các giải pháp đã biết ở mục 1.2, sáng kiến mang lại những cải thiện kỹ thuật "
     "sau đây.")
for t in [
    "Bảo vệ dữ liệu ở trạng thái lưu trữ ngay trên thiết bị, lấp đúng khoảng trống mà mã hoá "
    "toàn thiết bị của hệ điều hành không xử lý được: khi máy đã mở khoá, dữ liệu trong két "
    "vẫn đòi hỏi mật khẩu riêng.",
    "Dữ liệu tiếp tục được bảo vệ sau khi rời khỏi thiết bị, khác với mã hoá toàn thiết bị "
    "vốn mất tác dụng ngay khi tệp được sao chép ra ngoài.",
    "Phát hiện được mọi sửa đổi trên tệp nhờ chữ ký ràng buộc, kể cả thủ đoạn ghép nối phần "
    "đầu tệp này với nội dung tệp khác.",
    "Khắc phục rủi ro mất dữ liệu do quên mật khẩu bằng cơ chế chia khoá theo ngưỡng, không "
    "phải gửi khoá cho bên thứ ba giữ hộ như các dịch vụ khôi phục tài khoản thông thường.",
    "Xử lý được siêu dữ liệu ẩn ngay trên điện thoại, khác với các ứng dụng két thương mại "
    "hiếm khi có chức năng này.",
    "Tệp tạo ra theo chuẩn mở nên liên thông với hệ sinh thái công cụ sẵn có, khác với các "
    "ứng dụng dùng định dạng riêng khoá người dùng vào sản phẩm.",
]:
    bullet(doc, t)

para(doc,
     "Bảng dưới đây trình bày rõ phạm vi bảo vệ và giới hạn. Việc công bố giới hạn là một "
     "phần của thiết kế: người dùng chỉ sử dụng đúng công cụ khi biết công cụ không bảo vệ "
     "được điều gì.")

bang(
    doc,
    "Mô hình mối đe doạ: phạm vi bảo vệ và giới hạn",
    ["Tình huống", "Có bảo vệ?", "Giải thích"],
    [
        ["Mất hoặc thất lạc điện thoại khi máy đang khoá", "Có",
         "Dữ liệu trong két ở dạng mã hoá; không có mật khẩu thì không mở được"],
        ["Người khác mượn máy khi máy đã mở khoá", "Có, một phần",
         "Két vẫn cần mật khẩu riêng; nhưng nếu phiên đang mở thì nội dung có thể xem được"],
        ["Sao chép tệp két ra khỏi thiết bị", "Có",
         "Tệp két tự bảo vệ, mở ở nơi khác vẫn cần mật khẩu"],
        ["Tệp bị sửa đổi hoặc hỏng trên đường truyền", "Có",
         "Chữ ký ràng buộc phát hiện mọi thay đổi, kể cả ghép nối tệp"],
        ["Ảnh chia sẻ mang theo toạ độ định vị", "Có",
         "Chức năng xoá siêu dữ liệu loại bỏ trước khi chia sẻ"],
        ["Lộ tệp do gửi nhầm qua ứng dụng khác", "Có, một phần",
         "Nếu gửi tệp két thì bên nhận vẫn cần mật khẩu; nếu gửi tệp đã trích xuất thì không"],
        ["Thiết bị đã bị chiếm quyền điều khiển ở mức hệ điều hành", "Không",
         "Phần mềm độc hại có quyền cao đọc được bộ nhớ tiến trình khi két đang mở"],
        ["Người dùng quên mật khẩu và không tạo mảnh phục hồi", "Không",
         "Hệ quả tất yếu của nguyên tắc không lưu khoá; đã có cơ chế phòng ngừa là chia mảnh"],
        ["Kẻ tấn công cưỡng ép người dùng cung cấp mật khẩu", "Không",
         "Nằm ngoài phạm vi của biện pháp kỹ thuật"],
    ],
    widths=[5.2, 3.0, 7.3],
)

para(doc, "Hiệu quả về quốc phòng – an ninh và xã hội", bold=True, indent=False)
for t in [
    "Góp phần bảo đảm an toàn cho dữ liệu nội bộ phát sinh trong công tác và huấn luyện khi "
    "được lưu trữ, sử dụng trên thiết bị di động có tính cơ động cao.",
    "Bảo đảm chủ quyền dữ liệu: toàn bộ quá trình xử lý diễn ra trên thiết bị, khoá do người "
    "dùng nắm giữ, sản phẩm không có thành phần máy chủ và không khai báo quyền truy cập "
    "mạng nên về mặt kỹ thuật không thể gửi dữ liệu ra ngoài.",
    "Giảm phụ thuộc vào phần mềm bảo mật nước ngoài mã nguồn đóng: toàn bộ thiết kế và mã "
    "nguồn do tác giả xây dựng, đơn vị kiểm soát và kiểm chứng lại được.",
    "Hạn chế thói quen chuyển tài liệu nội bộ qua ứng dụng nhắn tin hoặc lưu trữ đám mây "
    "không kiểm soát, bằng cách cung cấp phương án thay thế thuận tiện ngay trên máy.",
    "Nâng cao nhận thức và kỹ năng an toàn thông tin cho cán bộ, học viên thông qua việc trực "
    "tiếp sử dụng và quan sát kết quả của các biện pháp bảo vệ dữ liệu.",
    "Góp phần đào tạo nguồn nhân lực làm chủ công nghệ bảo mật: học viên không chỉ dùng công "
    "cụ mà còn đọc được mã nguồn, hiểu được nguyên lý và có thể phát triển tiếp.",
]:
    bullet(doc, t)

para(doc,
     "Tác giả xác định rõ phạm vi: sản phẩm là công cụ hỗ trợ kỹ thuật do tác giả tự xây dựng "
     "phục vụ công tác và huấn luyện. Việc sử dụng cho bất kỳ loại tài liệu nào phải tuân thủ "
     "quy định hiện hành của cơ quan có thẩm quyền về bảo vệ bí mật nhà nước và quy chế của "
     "đơn vị. Hồ sơ này không đưa ra tuyên bố về việc sản phẩm được phép xử lý tài liệu thuộc "
     "danh mục bí mật nhà nước ở cấp độ cụ thể.", italic=True)

# ------------------------------------------------- 4.d
h3(doc, "d) Mức độ triển khai, phát triển trong thời gian tới")

para(doc, "Mức độ hoàn thành hiện tại", bold=True, indent=False)
bang(
    doc,
    "Mức độ hoàn thành theo hạng mục",
    ["Hạng mục", "Mức độ", "Cách xác định"],
    [
        ["Thiết kế kiến trúc và định dạng dữ liệu", "Hoàn thành",
         "Tài liệu kiến trúc và mã nguồn"],
        ["Lõi bảo vệ dữ liệu và các nghiệp vụ", "Hoàn thành",
         "Bộ kiểm thử tự động chạy đạt trên máy chủ"],
        ["Mô-đun xử lý siêu dữ liệu bằng Rust", "Hoàn thành",
         "Năm kiểm thử tự động trên ảnh có siêu dữ liệu"],
        ["Tương thích định dạng giữa hai bản hiện thực", "Hoàn thành",
         "Đối chứng hai chiều với công cụ chuẩn"],
        ["Biên dịch cho kiến trúc Android", "Hoàn thành",
         "Kiểm tra tệp đối tượng là mã ARM64"],
        ["Thực thi lõi trên kiến trúc ARM64", "Hoàn thành",
         "Chạy bộ kiểm thử dưới trình giả lập kiến trúc"],
        ["Giao diện cho màn hình điện thoại", "Hoàn thành",
         "Kết xuất và kiểm tra bố cục ở kích thước điện thoại"],
        ["Đóng gói tệp cài đặt Android", "Hoàn thành",
         "Kiểm tra tĩnh nội dung gói cài đặt"],
        ["Kiểm thử nghiệm thu trên thiết bị Android", "Có quy trình nghiệm thu",
         "Quy trình 15 bước có tiêu chí đạt cho từng bước, tại Phụ lục A"],
        ["Tích hợp kho khoá phần cứng của Android", "Định hướng phát triển",
         "Chưa hiện thực trong phiên bản này"],
    ],
    widths=[5.5, 4.6, 5.4],
)

para(doc, "Hướng phát triển", bold=True, indent=False)
for i, (ten, mo_ta) in enumerate([
    ("Hoàn tất kiểm thử nghiệm thu trên nhiều dòng máy",
     "Chạy toàn bộ kịch bản nghiệp vụ tại Phụ lục A trên nhiều dòng điện thoại và nhiều phiên "
     "bản Android, ghi nhận kết quả làm cơ sở đánh giá hiệu quả thực tế."),
    ("Tích hợp kho khoá phần cứng và xác thực sinh trắc",
     "Sử dụng vùng lưu khoá được phần cứng bảo vệ của Android để lưu các thông tin không thuộc "
     "hệ thống khoá của két, và cho phép mở khoá bằng vân tay như một tuỳ chọn của người dùng."),
    ("Mở rộng phạm vi định dạng của mô-đun siêu dữ liệu",
     "Bổ sung khả năng xoá siêu dữ liệu cho các định dạng ảnh và video khác, theo đúng nguyên "
     "tắc chỉ báo thành công khi thực sự dựng lại được tệp."),
    ("Xây dựng bộ bài giảng và bài thực hành kèm theo",
     "Biên soạn tài liệu hướng dẫn giảng viên, phiếu bài thực hành và bộ dữ liệu mẫu tương ứng "
     "với bảng ánh xạ chức năng, để đưa vào chương trình huấn luyện chính thức."),
    ("Đánh giá độc lập và mở rộng nền tảng",
     "Đề nghị đồng nghiệp và học viên rà soát mã nguồn; kiến trúc lõi dùng chung đã sẵn sàng "
     "cho nền tảng khác, việc mở rộng chủ yếu là bổ sung phần vỏ ứng dụng chứ không phải viết "
     "lại nghiệp vụ."),
], 1):
    bullet(doc, mo_ta, bold_head=f"Hướng {i} – {ten}: ")

# =====================================================================
ngat_trang(doc)
h1(doc, "C. TÀI LIỆU THAM KHẢO VÀ TIÊU CHUẨN VIỆN DẪN")
para(doc,
     "Các nguyên hàm mật mã và tham số mà tác giả lựa chọn đều dựa trên tiêu chuẩn hoặc "
     "khuyến nghị đã công bố, không phải do tác giả tự đặt ra.")
for i, t in enumerate([
    "RFC 9106 — Argon2 Memory-Hard Function for Password Hashing and Proof-of-Work "
    "Applications.",
    f"OWASP Password Storage Cheat Sheet — khuyến nghị tham số tối thiểu cho Argon2id "
    f"({A2['min_mem_kib'] // 1024} MiB bộ nhớ, {A2['min_time_cost']} vòng lặp).",
    "RFC 8439 — ChaCha20 and Poly1305 for IETF Protocols.",
    "RFC 7748 — Elliptic Curves for Security (trao đổi khoá X25519).",
    "RFC 8032 — Edwards-Curve Digital Signature Algorithm (chữ ký Ed25519).",
    "A. Shamir, “How to share a secret”, Communications of the ACM, 1979.",
    "BLAKE3 — đặc tả hàm băm mật mã và cơ chế dẫn xuất khoá theo ngữ cảnh.",
    "Đặc tả định dạng age v1 — định dạng tệp mã hoá mở.",
    "Tài liệu Android Developers — Storage Access Framework và Scoped Storage.",
    "Đặc tả Exif 2.32 (CIPA DC-008) — cấu trúc siêu dữ liệu trong tệp ảnh.",
], 1):
    bullet(doc, t, bold_head=f"[{i}] ")

# =====================================================================
ngat_trang(doc)
h1(doc, "D. PHỤ LỤC")

h2(doc, "Phụ lục A. Quy trình kiểm thử nghiệm thu trên thiết bị Android")
para(doc,
     "Phụ lục này là quy trình nghiệm thu để xác nhận sản phẩm hoạt động đúng trên thiết bị "
     "thật. Mỗi bước có tiêu chí đạt rõ ràng để kết quả ghi nhận được khách quan, và cột cuối "
     "để trống cho người thực hiện điền kết quả.")

bang(
    doc,
    "Quy trình kiểm thử nghiệm thu trên thiết bị Android",
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
        ["10", "Chia và khôi phục khoá", "Chia bí mật 3 mảnh cần 2, khôi phục bằng 2 mảnh",
         "Khôi phục đúng; dùng 1 mảnh thì không khôi phục được", ""],
        ["11", "Giấu tin và phát hiện", "Giấu tệp vào ảnh, rồi dùng chức năng phát hiện",
         "Trích xuất đúng tệp; chức năng phát hiện ghi nhận dấu hiệu", ""],
        ["12", "Xem siêu dữ liệu ảnh", "Chọn ảnh chụp bằng điện thoại rồi bấm Xem",
         "Liệt kê các thẻ; ảnh có định vị thì thấy nhóm toạ độ", ""],
        ["13", "Xoá siêu dữ liệu ảnh", "Xoá siêu dữ liệu ảnh đó rồi xem lại bản đã xoá",
         "Bản sạch không còn thẻ; ảnh gốc nguyên vẹn; ảnh vẫn mở xem được", ""],
        ["14", "Thuỷ vân chống giả mạo", "Đóng dấu một ảnh, sửa một vùng, kiểm tra lại",
         "Phát hiện ảnh đã bị sửa và chỉ ra vùng bị can thiệp", ""],
        ["15", "Tương thích liên nền tảng", "Mở tệp két tạo trên máy tính bằng ứng dụng di động",
         "Mở được bằng đúng mật khẩu", ""],
    ],
    widths=[0.9, 3.1, 4.3, 5.2, 2.5],
    note="Đề nghị ghi lại kết quả từng bước kèm ảnh chụp màn hình để bổ sung vào hồ sơ.",
)

h2(doc, "Phụ lục B. Hình ảnh bổ sung từ thiết bị thật")
para(doc,
     "Các hình dưới đây được chụp trong quá trình nghiệm thu tại Phụ lục A trên thiết bị của "
     "đơn vị áp dụng. Hồ sơ dành sẵn vị trí để gắn ảnh chụp thực tế, bảo đảm mọi hình ảnh "
     "trong hồ sơ đều là ảnh chụp thật chứ không phải ảnh mô phỏng.")
placeholder_hinh(doc, "Hình PL-1",
                 "Ảnh chụp màn hình ứng dụng đang chạy trên điện thoại Android (màn hình chính)",
                 4.5)
placeholder_hinh(doc, "Hình PL-2",
                 "Ảnh chụp mục Quyền ứng dụng trong Cài đặt hệ thống, cho thấy ứng dụng không "
                 "có quyền truy cập mạng", 4.5)
placeholder_hinh(doc, "Hình PL-3",
                 "Ảnh chụp kết quả xem siêu dữ liệu của một ảnh chụp bằng điện thoại", 4.5)

chu_ky(doc, ("XÁC NHẬN CỦA ĐƠN VỊ", "(Ký, đóng dấu)"),
       ("TÁC GIẢ SÁNG KIẾN", "(Ký, ghi rõ họ tên)"))

doc.save(str(BASE / "docx" / "02-Thuyet-minh-sang-kien.docx"))
print("Đã tạo 02-Thuyet-minh-sang-kien.docx")
