# Hồ sơ sáng kiến — SecureVault Mobile (Android)

Thư mục này chứa toàn bộ hồ sơ đề nghị công nhận sáng kiến cho **SecureVault Mobile**,
ứng dụng bảo vệ dữ liệu nhạy cảm trên thiết bị Android hoạt động hoàn toàn ngoại tuyến.

> **Nguyên tắc xuyên suốt:** mọi số liệu trong hồ sơ được **sinh tự động** từ mã nguồn và
> nhật ký kiểm thử thật (xem `bang-chung/du-kien.json`). Không có con số nào nhập tay.
> Những hạng mục chưa kiểm chứng được ghi rõ là *chưa kiểm chứng*, không mô tả như đã hoàn thành.

---

## 1. Các văn bản của hồ sơ

| Tệp | Nội dung | Số trang |
|---|---|---|
| `docx/01-Don-dang-ky-sang-kien.docx` | Đơn đăng ký sáng kiến theo mẫu | 3 |
| `docx/02-Thuyet-minh-sang-kien.docx` | Thuyết minh đầy đủ (mục B: hiện trạng → mục đích → mô tả → tự đánh giá), kèm phụ lục | 31 |
| `docx/03-Du-kien-hieu-qua.docx` | Dự kiến hiệu quả khi đưa vào ứng dụng thực tiễn | 3 |

Bản PDF kèm theo trong cùng thư mục chỉ dùng để **kiểm tra bố cục**; bản nộp là tệp DOCX.

### Việc cần làm trước khi nộp

1. Điền thông tin cá nhân vào các ô để trống (họ tên, đơn vị, ngày tháng) trong cả ba văn bản.
2. Mở tệp Thuyết minh, nhấn chuột phải vào mục lục → **Cập nhật trường** để mục lục hiện ra.
3. Thực hiện quy trình tại **Phụ lục A** trên điện thoại Android thật, chụp ảnh và thay vào
   ba ô **Hình PL-1, PL-2, PL-3** ở Phụ lục B.

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

## 4. Mức độ kiểm chứng của sản phẩm

Đây là phần quan trọng nhất cần đọc kỹ, vì nó phân định rõ điều đã chứng minh được và
điều chưa.

| Mức | Nội dung | Trạng thái |
|---|---|---|
| 1 | Kiểm thử đơn vị lõi mật mã và nghiệp vụ trên máy chủ | Đã thực hiện |
| 2 | Tương thích định dạng, đối chứng hai chiều với công cụ age v1.2.1 | Đã thực hiện |
| 3 | Biên dịch chéo toàn bộ lõi sang kiến trúc Android | Đã thực hiện |
| 4 | Thực thi lõi trên kiến trúc ARM64 bằng trình giả lập QEMU | Đã thực hiện |
| 5 | Đóng gói APK và kiểm tra tĩnh | Xem `apk/README.md` |
| 6 | **Chạy trên điện thoại Android thật** | **Chưa thực hiện** |

Mức 6 chưa thực hiện được vì máy chủ dùng để xây dựng không có ảo hoá lồng nhau
(`/dev/kvm` không tồn tại) nên không khởi động được trình giả lập Android. Đây là giới hạn
của môi trường xây dựng, không phải của sản phẩm. Quy trình để tự kiểm chứng nằm ở
**Phụ lục A** của Thuyết minh.

---

## 5. Lưu ý về phạm vi

Hồ sơ **không** đưa ra tuyên bố nào về việc sản phẩm được phép xử lý tài liệu thuộc danh mục
bí mật nhà nước ở bất kỳ cấp độ nào. Việc sử dụng cho từng loại tài liệu phải tuân thủ quy
định hiện hành của cơ quan có thẩm quyền và quy chế của đơn vị.
