# Hồ sơ sáng kiến — SecureVault

Thư mục này chứa toàn bộ hồ sơ đề nghị công nhận sáng kiến cho **SecureVault** —
*Bộ công cụ bảo đảm an toàn thông tin và quyền riêng tư dữ liệu đa nền tảng*.

> **Tên gọi nói “đa nền tảng”, nhưng trọng tâm vẫn là bản di động.** Sản phẩm dùng chung một
> lõi nghiệp vụ và một định dạng dữ liệu cho cả bản trên máy tính lẫn bản trên Android; bản
> di động là nơi rào cản kỹ thuật thực sự tồn tại và được giải quyết, còn bản máy tính giữ
> vai trò đối chứng và mở rộng phạm vi sử dụng. Cả năm văn bản đều nói rõ ranh giới này.

> Tên sáng kiến và thông tin nhóm tác giả nằm ở một nơi duy nhất: `ten_sang_kien.py`. Cả năm
> văn bản đọc từ đó, nên đổi tên chỉ phải sửa một chỗ.

> **Phạm vi sử dụng mà hồ sơ mô tả** đúng hai kịch bản, không hơn:
> 1. **Huấn luyện** học viên về an toàn thông tin và bảo mật dữ liệu — sản phẩm là học cụ.
> 2. **Tình huống khẩn cấp, bất khả kháng** buộc phải chuyển gấp một số tài liệu đặc thù qua
>    không gian mạng — sản phẩm giúp cán bộ bọc thêm lớp bảo vệ cho tệp trước khi gửi.
>
> Hồ sơ **không** mô tả kịch bản cất giữ tài liệu mật hay tài liệu nội bộ trên thiết bị di
> động: quy định của đơn vị cấm việc này, và sáng kiến không đề xuất thay đổi quy định đó.

> **Cấu trúc hồ sơ** bám theo tệp mẫu `Mau_ho_so_sang_kien_cai_tien.doc` của Phòng Khoa học
> Quân sự: khối tiêu đề hai cột, các mục A/B/C của Đơn, và khung mục B của Thuyết minh
> (hiện trạng → mục đích → mô tả → tự đánh giá) với 4a tách *Điểm mới* và *Điểm sáng tạo*,
> 4c tách *kinh tế / kỹ thuật / quốc phòng-an ninh và xã hội*.
>
> **Nguyên tắc xuyên suốt:** mọi số liệu trong hồ sơ được **sinh tự động** từ mã nguồn và
> nhật ký kiểm thử thật (xem `bang-chung/du-kien.json`). Không có con số nào nhập tay.
> Những hạng mục chưa kiểm chứng được ghi rõ là *chưa kiểm chứng*, không mô tả như đã hoàn thành.

---

## 1. Các văn bản của hồ sơ

| Tệp | Nội dung | Số trang |
|---|---|---|
| `docx/01-Don-dang-ky-sang-kien.docx` | Đơn đăng ký sáng kiến cải tiến kỹ thuật | 2 |
| `docx/02-Thuyet-minh-sang-kien.docx` | **Thuyết minh — bản để hội đồng đọc.** Bám khung mẫu, cô đọng dưới 20 trang | 19 |
| `docx/03-Du-kien-hieu-qua.docx` | Dự kiến hiệu quả khi đưa vào ứng dụng trong thực tiễn | 4 |
| `docx/04-De-cuong-so-bo-sang-kien.docx` | **Đề cương sơ bộ.** Lý do, mục tiêu, phạm vi, cách tiếp cận, khối công việc, kế hoạch kiểm chứng, tiến trình và rủi ro | 22 |
| `docx/05-De-cuong-chi-tiet-sang-kien.docx` | **Đề cương chi tiết.** Toàn bộ lập luận thiết kế, mô tả từng chức năng kèm giao diện, kiểm chứng, ảnh chụp 21 màn hình, quy trình nghiệm thu | 60 |

Bản PDF kèm theo trong cùng thư mục chỉ dùng để **kiểm tra bố cục**; bản nộp là tệp DOCX.

**Ba văn bản nội dung, ba câu hỏi khác nhau.** Thuyết minh phải gọn để hội đồng đọc là nắm ngay
sáng kiến có gì đặc biệt; nhưng cắt gọn thì mất phần chứng minh chiều sâu. Nên hồ sơ tách làm ba
mức, mỗi mức trả lời một câu hỏi:

| Văn bản | Trả lời câu hỏi | Quy mô |
|---|---|---|
| 02 Thuyết minh | *Sáng kiến này là gì và đáng giá ở đâu?* | dưới 20 trang |
| 04 Đề cương sơ bộ | *Định làm gì, làm theo cách nào, lấy gì để chứng minh là đã làm được?* | khoảng 20 trang |
| 05 Đề cương chi tiết | *Đã làm như thế nào, ở mức từng cơ chế?* | khoảng 60 trang |

Đề cương sơ bộ **không phải** bản rút gọn của Đề cương chi tiết: nó là tài liệu của giai đoạn đặt
vấn đề (mục tiêu, phạm vi, khối công việc, kế hoạch kiểm chứng, tiến trình, rủi ro), mỗi phần kèm
cột đối chiếu với kết quả thực tế. Cả ba dùng chung một nguồn số liệu (`du_lieu_ho_so.py`) và
chung nội dung tám nhóm chức năng (`noi_dung_chuc_nang.py`), nên không thể lệch nhau.

**`ban-tac-gia-ra-soat/`** giữ nguyên ba tệp DOCX mà tác giả tự rà soát và chỉnh sửa thủ công —
đây là nguồn văn bản gốc cho lần biên tập này, giữ lại để đối chiếu.

### Việc cần làm trước khi nộp

1. Mở tệp Thuyết minh và Đề cương, nhấn chuột phải vào mục lục → **Cập nhật trường** để mục
   lục hiện ra (trường mục lục chỉ điền khi mở bằng Word/LibreOffice).
2. Rà lại thông tin nhóm tác giả và ngày tháng — nguồn ở `ten_sang_kien.py`.
3. Thực hiện quy trình nghiệm thu 15 bước tại **Phụ lục A của Đề cương** trên điện thoại
   Android, điền kết quả vào cột cuối của bảng.

---

## 2. Hình ảnh và sơ đồ

| Thư mục | Nội dung |
|---|---|
| `hinh-anh/svg/` | Sơ đồ gốc dạng SVG (6 hình) |
| `hinh-anh/drawio/` | **Bản drawio tương ứng** — mở bằng diagrams.net để sửa nếu cần |
| `hinh-anh/png/` | Ảnh PNG độ phân giải cao đã chèn vào DOCX |
| `hinh-anh/screenshot/` | Ảnh chụp giao diện: 21 ảnh màn hình đơn (`GD01`–`GD21`) và 11 hình ghép hai màn hình dùng cho Phụ lục B của Đề cương (`GC01`–`GC11`) |

Sáu sơ đồ: hai nhu cầu thực tiễn, kiến trúc phân lớp, lõi dùng chung, phân cấp khoá,
luồng tệp trên Android, các mức kiểm chứng. Tiêu đề nhúng trong hình **không** mang số hiệu
“Hình N.” — số hiệu do DOCX tự đánh theo thứ tự chèn, để hai bên không lệch nhau khi một hình
bị bỏ ra khỏi văn bản.

**Về ảnh chụp giao diện:** đây là ảnh kết xuất từ *chính mã giao diện của sản phẩm* ở kích
thước màn hình điện thoại, với cầu nối IPC được mô phỏng để trả về đúng giá trị mà gốc hợp
thành Android tạo ra. Nhờ vậy logic giao diện thật được thực thi, không phải ảnh dựng bằng
công cụ thiết kế.

Hồ sơ trình bày **đầy đủ 21 màn hình** của ứng dụng (Phụ lục B của Đề cương), và mỗi nhóm chức
năng trong Đề cương đều có phần *“Giao diện tương ứng”* kèm bảng đối chiếu **màn hình ↔ lệnh
nghiệp vụ**. Việc đối chiếu đã được kiểm tra hai chiều trên mã nguồn: không có lệnh nào của lõi
mà giao diện không gọi tới, và không có nút nào gọi tới lệnh không tồn tại.

---

## 3. Cách tái tạo lại hồ sơ

```bash
cd hoso-sang-kien

python3 thu-thap-du-kien.py <thư-mục-log>   # đọc mã nguồn + log kiểm thử → du-kien.json
python3 sinh-so-do.py                        # sinh SVG + drawio
python3 chup-giao-dien.py                    # chụp 21 màn hình + ghép hình cho Phụ lục B
python3 tao-don-va-hieu-qua.py               # sinh văn bản 01 và 03
python3 tao-thuyet-minh.py                   # sinh văn bản 02 (Thuyết minh, < 20 trang)
python3 tao-de-cuong-so-bo.py                # sinh văn bản 04 (Đề cương sơ bộ)
python3 tao-de-cuong-chi-tiet.py             # sinh văn bản 05 (Đề cương chi tiết)
```

Các mô-đun dùng chung giữa các văn bản:

| Tệp | Vai trò |
|---|---|
| `ten_sang_kien.py` | Tên sáng kiến, lĩnh vực, thông tin nhóm tác giả |
| `du_lieu_ho_so.py` | Mọi số liệu kỹ thuật, đọc từ `bang-chung/*.json` |
| `noi_dung_chuc_nang.py` | Tám nhóm chức năng: bảng chức năng + phần “Giao diện tương ứng” |
| `noi_dung_giao_dien.py` | Danh mục 21 màn hình và hai lệnh mức ứng dụng |
| `dinh_dang.py` | Phông, lề, tiêu đề, bảng, hình, trang bìa, khối ký |

Việc tách dữ kiện ra tệp JSON là có chủ đích: nếu mã nguồn thay đổi, chỉ cần chạy lại
`thu-thap-du-kien.py` là mọi con số trong hồ sơ tự cập nhật, không phải sửa tay từng chỗ.

---

## 4. Các mức kiểm chứng của sản phẩm

| Mức | Nội dung | Kết quả |
|---|---|---|
| 1 | Kiểm thử đơn vị lõi bảo vệ dữ liệu trên máy chủ | 263 đạt / 0 lỗi |
| 2 | Tương thích định dạng, đối chứng với công cụ chuẩn age v1.2.1 | 5 phép đối chứng đạt |
| 3 | Biên dịch chéo toàn bộ lõi sang kiến trúc Android | Thành công |
| 4 | Thực thi lõi trên kiến trúc ARM64 | 146 đạt / 0 lỗi |
| 5 | Đóng gói APK và kiểm tra tĩnh nội dung gói | Đạt — xem `apk/README.md` |
| 6 | Dựng + soát mã + kiểm thử trên ma trận hệ điều hành máy tính | Windows · macOS · Linux — 9/9 hạng mục xanh (biên bản `docs/CI-VALIDATION.md`) |
| 7 | Nghiệm thu trên điện thoại Android | **Chưa thực hiện** — quy trình 15 bước tại Phụ lục A của Đề cương chi tiết |

Phụ lục A của Đề cương chi tiết là quy trình nghiệm thu có tiêu chí đạt cho từng bước và cột
trống để ghi kết quả.

## 4c. Về khả năng đa nền tảng

Sản phẩm không chỉ có bản Android. Cùng một lõi nghiệp vụ chạy trên cả máy tính để bàn, và toàn
bộ khác biệt giữa hai nền tảng gói gọn trong lớp lắp ráp ứng dụng (`app/src/compose/`, đúng hai
tệp). Cái **đổi** theo nền tảng: mô-đun mã hoá nội dung, mô-đun siêu dữ liệu, cách lấy tệp từ bộ
nhớ thiết bị, bố cục giao diện. Cái **không đổi**: định dạng tệp `.svault`, sơ đồ phân cấp khoá,
38 lệnh nghiệp vụ, quy tắc phân loại lỗi, và 15 thành phần của lõi.

Hồ sơ nêu khả năng này ở đúng mức kiểm chứng được, không hơn:

| Tuyên bố | Bằng chứng |
|---|---|
| Mã nguồn dựng + soát mã + chạy kiểm thử đạt trên Windows/macOS/Linux | `.github/workflows/ci.yml` (ma trận 3 hệ điều hành) và `docs/CI-VALIDATION.md` (biên bản lần chạy xanh) |
| Tệp két đọc chéo được giữa hai bản hiện thực | `src-tauri/tests/vault_interop.rs` — hai phép kiểm thử mang đúng tên `desktop_written_vault_opens_with_the_mobile_cipher` và chiều ngược lại |
| **Chưa** có bản cài đặt ký số/công chứng cho Windows và macOS | `docs/VALIDATION-RESULTS.md` — hạng mục H5 còn để mở |

**Trọng tâm của sáng kiến vẫn là bản di động**: đó là nơi rào cản kỹ thuật thực sự tồn tại và
được giải quyết. Bản máy tính đóng vai trò đối chứng và mở rộng phạm vi sử dụng.

## 4b. Về mô-đun siêu dữ liệu

Trên máy tính để bàn, mô-đun này chạy ExifTool như một tiến trình con. ExifTool là chương
trình Perl nên **không thể chạy trên Android** dưới bất kỳ hình thức nào. Vì vậy toàn bộ ba
nghiệp vụ siêu dữ liệu đã được **viết lại bằng Rust thuần** (crate `sv-meta-rs`), chạy ngay
trong tiến trình ứng dụng:

| Nghiệp vụ | Định dạng hỗ trợ |
|---|---|
| Xem siêu dữ liệu | JPEG, PNG, TIFF, WebP, HEIF |
| Xoá siêu dữ liệu | JPEG, PNG (loại EXIF, hồ sơ màu, chú thích, khối văn bản) |
| So sánh hai tệp | Các định dạng đọc được ở trên |

Phạm vi hẹp hơn ExifTool (không xử lý PDF, tài liệu Office, âm thanh/video) và điều đó được
phản ánh trung thực trong mã: định dạng ngoài phạm vi bị từ chối bằng lỗi có mã, **không bao
giờ báo “đã xoá” cho tệp chưa thực sự được xử lý**.

---

## 5. Lưu ý về phạm vi

Hồ sơ **không** đưa ra tuyên bố nào về việc sản phẩm được phép xử lý tài liệu thuộc danh mục
bí mật nhà nước ở bất kỳ cấp độ nào. Việc sử dụng cho từng loại tài liệu phải tuân thủ quy
định hiện hành của cơ quan có thẩm quyền và quy chế của đơn vị.
