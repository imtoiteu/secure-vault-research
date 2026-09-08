# Hồ sơ sáng kiến — SecureVault Mobile (Android)

Thư mục này chứa toàn bộ hồ sơ đề nghị công nhận sáng kiến cho **SecureVault Mobile**,
ứng dụng bảo vệ dữ liệu nhạy cảm trên thiết bị Android hoạt động hoàn toàn ngoại tuyến.

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
| `docx/02-Thuyet-minh-sang-kien.docx` | Thuyết minh đầy đủ (mục B: hiện trạng → mục đích → mô tả → tự đánh giá), kèm phụ lục | 31 |
| `docx/03-Xac-nhan-danh-gia-hieu-qua.docx` | Xác nhận đánh giá hiệu quả mang lại của sáng kiến | 4 |

Bản PDF kèm theo trong cùng thư mục chỉ dùng để **kiểm tra bố cục**; bản nộp là tệp DOCX.

### Việc cần làm trước khi nộp

1. Điền thông tin cá nhân vào các ô để trống (họ tên, đơn vị, ngày tháng) trong cả ba văn bản.
2. Mở tệp Thuyết minh, nhấn chuột phải vào mục lục → **Cập nhật trường** để mục lục hiện ra.
3. Thực hiện quy trình nghiệm thu 15 bước tại **Phụ lục A** trên điện thoại Android, điền
   kết quả vào cột cuối của bảng, chụp ảnh và thay vào ba ô **Hình PL-1, PL-2, PL-3**.

---

## 2. Hình ảnh và sơ đồ

| Thư mục | Nội dung |
|---|---|
| `hinh-anh/svg/` | Sơ đồ gốc dạng SVG (6 hình) |
| `hinh-anh/drawio/` | **Bản drawio tương ứng** — mở bằng diagrams.net để sửa nếu cần |
| `hinh-anh/png/` | Ảnh PNG độ phân giải cao đã chèn vào DOCX |
| `hinh-anh/screenshot/` | Ảnh chụp giao diện ứng dụng |

Sáu sơ đồ: bài toán thực tế, kiến trúc phân lớp, lõi dùng chung, phân cấp khoá,
luồng tệp trên Android, tháp bằng chứng kiểm chứng.

**Về ảnh chụp giao diện:** đây là ảnh kết xuất từ *chính mã giao diện của sản phẩm* ở kích
thước màn hình điện thoại, với cầu nối IPC được mô phỏng để trả về đúng giá trị mà gốc hợp
thành Android tạo ra. Nhờ vậy logic giao diện thật được thực thi (ví dụ cơ chế tắt an toàn ở
Hình 9 là hành vi thật, không phải ảnh dựng). Ảnh chụp trên **thiết bị Android thật** vẫn cần
bổ sung — xem Phụ lục B.

---

## 3. Cách tái tạo lại hồ sơ

```bash
cd hoso-sang-kien

python3 thu-thap-du-kien.py <thư-mục-log>   # đọc mã nguồn + log kiểm thử → du-kien.json
python3 sinh-so-do.py                        # sinh SVG + drawio
python3 tao-don-va-hieu-qua.py               # sinh văn bản 1 và 3
python3 tao-thuyet-minh.py                   # sinh văn bản 2
```

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
| 6 | Nghiệm thu trên điện thoại Android | Quy trình 15 bước tại Phụ lục A |

Phụ lục A của Thuyết minh là quy trình nghiệm thu có tiêu chí đạt cho từng bước và cột trống
để ghi kết quả; Phụ lục B dành sẵn vị trí gắn ảnh chụp từ thiết bị.

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
