# MANUAL_SCREENSHOTS — Hướng dẫn chụp bổ sung các ảnh màn hình còn thiếu

> **Ghi chú đường dẫn (04-09-2026):** thư mục vỏ Tauri `desktop/` đã được đổi tên thành `app/`
> khi nó trở thành crate dùng chung cho desktop + Android + iOS. Các đường dẫn trích dẫn bên dưới
> là đường dẫn tại thời điểm viết tài liệu và được giữ nguyên để bảo toàn tính chính xác của hồ sơ;
> hãy đọc `desktop/...` là `app/...` của hiện tại.


Tài liệu này dành cho người hoàn thiện báo cáo `BAO_CAO_DE_TAI_SECURE_VAULT_RESEARCH.docx`.

---

## 0. Tình trạng hiện tại của các ảnh màn hình

### Những gì đã có (chụp tự động, ảnh **thật**)

Hai mươi màn hình của giao diện đã được chụp và nằm trong `report_figures/screenshots/`.
Mười hai trong số đó đã được chèn vào báo cáo (Hình 3.12 – 3.23).

**Điều kiện chụp — cần biết để đánh giá đúng giá trị của các ảnh này:**

- Nguồn: **chính mã giao diện thật** của hệ thống —
  `secure-vault-research/desktop/frontend/{index.html, main.js, i18n.js, styles.css}`.
  Không có phần nào được vẽ lại, mô phỏng hay chỉnh sửa.
- Cách chụp: kết xuất bằng trình duyệt Chromium ở chế độ không giao diện, khung nhìn
  1440 × 900, hệ số tỉ lệ 1,5 (ảnh ra 2160 × 1350).
- **Không có lõi Rust chạy phía sau.** Một lớp bọc tối thiểu được nạp trước `main.js` để
  `window.__TAURI__.core.invoke` tồn tại; lớp bọc này chỉ trả về đúng các hằng số **kiểm chứng
  được tại thời điểm biên dịch** cho lệnh `app_info` (phiên bản ứng dụng `0.1.0` lấy từ
  `desktop/Cargo.toml`; `contract_version = 1`; `max_format_version = 1`; `suite_version = 1`),
  và **từ chối mọi lệnh khác**. **Không có kết quả thao tác nào được bịa ra.**
- Hệ quả: các ảnh này thể hiện **chính xác** bố cục, nhãn tiếng Việt, cấu trúc biểu mẫu và
  trạng thái mặc định của từng màn hình; nhưng chúng **không** thể hiện kết quả của một thao
  tác thực (danh sách tệp trong két, thẻ phán quyết ĐẠT/KHÔNG ĐẠT, danh sách mảnh đã cắt,
  báo cáo dò giấu tin…).
- Riêng Hình 3.23 (Xem siêu dữ liệu) hiển thị trạng thái **mô-đun chưa sẵn sàng**. Đây là trạng
  thái **đúng và trung thực** cho một bản dựng từ cây mã hiện tại, vì thư mục `desktop/binaries/`
  chỉ chứa tài liệu hướng dẫn chứ chưa có nhị phân ExifTool.

### Những gì còn thiếu

Ba chỗ dành sẵn (khối chữ đỏ trong báo cáo) tương ứng ba trạng thái **có kết quả**, chỉ chụp được
khi chạy ứng dụng đầy đủ. Mục 2 mô tả chi tiết từng chỗ.

---

## 1. Chuẩn bị môi trường để chụp

### 1.1. Yêu cầu

| Thành phần | Ghi chú |
|---|---|
| Bộ công cụ Rust | Phiên bản tối thiểu 1.96 |
| Trình biên dịch C | Bắt buộc — hai crate FFI biên dịch `hazmat.c` và dựng libsodium từ mã nguồn |
| Bộ công cụ Tauri | `cargo install tauri-cli`; kèm thư viện webview của hệ điều hành |
| Nhị phân `age` và `age-keygen` | **Bắt buộc.** Đặt vào `desktop/binaries/` theo hướng dẫn trong `desktop/binaries/README.md` |
| Nhị phân `exiftool` | Tùy chọn — chỉ cần nếu muốn chụp mô-đun Phân tích ở trạng thái hoạt động |
| Màn hình | Khuyến nghị 1440 × 900 trở lên, tỉ lệ hiển thị 100 % hoặc 150 % |

### 1.2. Khởi chạy

```sh
cd secure-vault-research/desktop
cargo tauri dev
```

Trong bản dựng gỡ lỗi, có thể trỏ đường dẫn nhị phân bằng biến môi trường thay vì đặt tệp vào
`desktop/binaries/`:

```sh
SV_AGE_BIN=/duong/dan/age SV_AGE_KEYGEN_BIN=/duong/dan/age-keygen \
SV_EXIFTOOL_BIN=/duong/dan/exiftool cargo tauri dev
```

> Lưu ý: các biến này **chỉ có hiệu lực trong bản dựng gỡ lỗi**. Bản phát hành cố ý bỏ qua chúng
> và chỉ phân giải nhị phân từ thư mục tài nguyên của gói cài.

### 1.3. Chuẩn bị dữ liệu mẫu

Tạo một thư mục làm việc riêng, **không dùng dữ liệu thật**:

```sh
mkdir -p ~/sv-demo && cd ~/sv-demo
printf 'Bao cao ky thuat - ban nhap\n' > tai-lieu-mau.txt
printf 'Danh sach lien he noi bo\n'    > danh-ba.txt
head -c 262144 /dev/urandom            > du-lieu-mau.bin
```

Cần thêm một ảnh PNG hoặc BMP cho các màn hình giấu tin và thủy vân (khuyến nghị ≥ 800 × 600).

### 1.4. Quy ước chụp

- Chụp **toàn bộ cửa sổ ứng dụng**, giữ nguyên thanh điều hướng bên trái để người đọc định vị được
  màn hình đang xem.
- Không cắt xén phần đầu (tiêu đề và bộ chọn ngôn ngữ) vì đó là ngữ cảnh cần thiết.
- Ngôn ngữ đặt ở **Tiếng Việt** để đồng nhất với các ảnh đã có.
- Định dạng PNG, không nén mất mát.
- Đặt tên tệp theo mẫu ở cột "Tên tệp" của mục 2 và lưu vào `report_figures/screenshots/`.
- **Trước khi chụp, kiểm tra kỹ để không có đường dẫn, tên tệp hay nội dung nhạy cảm thật nào lọt
  vào khung hình.** Toàn bộ dữ liệu trong ảnh phải là dữ liệu mẫu.

---

## 2. Danh mục ảnh cần chụp bổ sung

### 2.1. Két an toàn ở trạng thái đã mở khóa

| Mục | Nội dung |
|---|---|
| **Vị trí trong báo cáo** | Chương 3, mục 5.3, ngay sau Hình 3.13 |
| **Số hình đề xuất** | Hình 3.13b (hoặc đánh lại số toàn chương) |
| **Tên tệp** | `screen-vault-unlocked.png` |
| **Màn hình** | Két an toàn (mục "Két an toàn" trên thanh điều hướng) |

**Các bước tái hiện**

1. Mở màn hình Két an toàn.
2. Ở thẻ "Tạo két mới": chọn nơi lưu là `~/sv-demo/demo.svault`; nhập mật khẩu vào **cả hai ô**;
   mở mục "Thiết lập khôi phục (tùy chọn)" và đặt tổng số mảnh 5, ngưỡng 3. Nhấn **Tạo két**.
3. Sau khi tạo, ở thẻ "Mở két an toàn": chọn `demo.svault`, nhập mật khẩu, nhấn **Mở két**.
4. Thêm lần lượt `tai-lieu-mau.txt` và `danh-ba.txt` vào két.
5. Chụp màn hình.

**Những gì bắt buộc phải thấy trong ảnh**

- Dải trạng thái ở góc trên bên phải chuyển thành **ĐÃ MỞ**.
- Danh sách hai tệp, mỗi dòng có tên, kích thước và vân tay nội dung ở dạng rút gọn.
- Các nút thao tác dành cho két đã mở: thêm tệp, trích xuất, đổi mật khẩu, chia khóa.
- Khối siêu dữ liệu của két nếu giao diện có hiển thị (định danh két, phiên bản định dạng, tham số
  hàm dẫn xuất khóa, chính sách khôi phục 3/5).

**Khung hình khuyến nghị** — toàn bộ cửa sổ; nếu danh sách tệp dài thì cuộn sao cho thấy đủ dải
trạng thái ở trên và ít nhất hai dòng tệp.

---

### 2.2. Kết quả sau khi chia một bí mật thành các mảnh

| Mục | Nội dung |
|---|---|
| **Vị trí trong báo cáo** | Chương 3, mục 5.3, ngay sau Hình 3.18 |
| **Số hình đề xuất** | Hình 3.18b |
| **Tên tệp** | `screen-split-secret-result.png` |
| **Màn hình** | Chia nhỏ bí mật |

**Các bước tái hiện**

1. Mở màn hình "Chia nhỏ bí mật".
2. Nhập một bí mật mẫu, ví dụ `MAT-KHAU-KET-DEMO-2026` (**không dùng bí mật thật**).
3. Đặt tổng số mảnh là 5, số mảnh cần để khôi phục là 3.
4. Chọn thư mục xuất là `~/sv-demo/`.
5. Nhấn nút chia và chờ hoàn tất.
6. Chụp màn hình.

**Những gì bắt buộc phải thấy trong ảnh**

- Đường dẫn tệp tải trọng (`{group_id}.payload.svss`).
- Danh sách **năm** tệp mảnh (`{group_id}.share1.svss` … `share5.svss`).
- **Năm chuỗi Base64** dạng chép tay được, mỗi chuỗi 124 ký tự.
- Dòng nhắc người dùng phân phát các mảnh tới những nơi cất giữ khác nhau, nếu giao diện có.

**Khung hình khuyến nghị** — cuộn sao cho thấy đủ ít nhất ba chuỗi mảnh; nếu không đủ chỗ, chụp
thành hai ảnh và ghép dọc.

---

### 2.3. Báo cáo phát hiện dữ liệu ẩn

| Mục | Nội dung |
|---|---|
| **Vị trí trong báo cáo** | Chương 3, mục 5.3, ngay sau Hình 3.20 |
| **Số hình đề xuất** | Hình 3.20b |
| **Tên tệp** | `screen-detect-result.png` |
| **Màn hình** | Phát hiện dữ liệu ẩn |

**Các bước tái hiện** — nên chụp **hai** trường hợp để minh họa cả hai đầu của thang đánh giá.

*Trường hợp A — mức nghi ngờ cao:*

```sh
cd ~/sv-demo
zip -q noi-dung.zip tai-lieu-mau.txt
cat anh-goc.png noi-dung.zip > anh-co-du-lieu-noi-them.png
```

Chạy dò trên `anh-co-du-lieu-noi-them.png`. Kết quả mong đợi là mức nghi ngờ **High**, do bộ dò
dữ liệu nối thêm phát hiện khối dữ liệu nằm sau điểm kết thúc hợp lệ của ảnh.

*Trường hợp B — không quan sát thấy:*

Chạy dò trên `anh-goc.png` chưa qua xử lý. Kết quả mong đợi là **NotObserved**.

**Những gì bắt buộc phải thấy trong ảnh**

- Mức nghi ngờ được hiển thị nổi bật.
- Danh sách từng bộ dò kèm điểm số và diễn giải ngắn.
- **Câu cảnh báo cố định** về giới hạn của phương pháp thực nghiệm. Đây là chi tiết quan trọng nhất
  của ảnh này vì báo cáo trích dẫn trực tiếp nguyên tắc "không bao giờ kết luận ảnh là sạch"; ảnh
  phải cho thấy giao diện thực sự hiển thị cảnh báo đó.

**Khung hình khuyến nghị** — cần thấy đủ cả mức nghi ngờ, bảng điểm từng bộ dò và câu cảnh báo.

---

## 3. Các ảnh tùy chọn nên bổ sung nếu có điều kiện

Những ảnh sau **không** có chỗ dành sẵn trong báo cáo nhưng sẽ làm phần trình bày mạnh hơn nếu
được chèn thêm.

| Nội dung | Màn hình | Cách tái hiện | Vì sao có giá trị |
|---|---|---|---|
| Thẻ kết quả kiểm chữ ký **ĐẠT** | Kiểm tra chữ ký | Ký một tệp rồi kiểm bằng đúng khóa công khai | Minh họa mô hình "kết quả sai lệch là câu trả lời hợp lệ, không phải lỗi" |
| Thẻ kết quả kiểm chữ ký **KHÔNG ĐẠT** | Kiểm tra chữ ký | Sửa một byte của tệp rồi kiểm lại | Cặp với ảnh trên, cho thấy hệ thống phân biệt hai kết quả |
| Thông báo **SV-OUTPUT-EXISTS** | Két an toàn | Trích xuất một tệp ra đúng đường dẫn đã có tệp | Bằng chứng trực quan cho cơ chế từ chối ghi đè (giả thuyết H3) |
| Thông báo **SV-TOO-LARGE** | Két an toàn | Thử thêm một tệp thưa lớn hơn 2 GiB | Bằng chứng trực quan cho rào kích thước (giả thuyết H1) |
| Thông báo **SV-UNAUTHORIZED** | Két an toàn | Mở két bằng mật khẩu sai | Minh họa mô hình lỗi chống dò kênh lỗi |
| Thông báo thiếu mảnh | Khôi phục từ các mảnh | Cung cấp 2 mảnh cho lược đồ ngưỡng 3 | Cho thấy mã lỗi riêng kèm số hiện có và số cần |
| Phán quyết thủy vân **Bị sửa** | Chống giả mạo tệp | Nhúng dấu, sửa một vùng nhỏ bằng phần mềm ảnh, kiểm lại | Minh họa khả năng định vị vùng bị can thiệp |
| Bảng siêu dữ liệu đã đọc | Xem siêu dữ liệu | Cần bản dựng có nhị phân ExifTool | Thay thế Hình 3.23 hiện đang ở trạng thái mô-đun chưa sẵn sàng |
| Báo cáo xóa siêu dữ liệu trên PDF | Xóa siêu dữ liệu | Chọn một tệp PDF mẫu | Cho thấy hệ thống báo cáo **trung thực** rằng PDF chỉ được sửa đổi tăng dần chứ không xóa thật |
| Bản dựng phát hành trên máy sạch | — | Cài gói phát hành trên tài khoản mới | Bằng chứng cho tình trạng chưa ký số (giả thuyết H5) |

---

## 4. Cách chèn ảnh vào báo cáo Word

1. Mở `BAO_CAO_DE_TAI_SECURE_VAULT_RESEARCH.docx` bằng Microsoft Word.
2. Dùng chức năng tìm kiếm với chuỗi `[CHỖ DÀNH SẴN` để tới từng vị trí.
3. Chọn **toàn bộ đoạn chữ đỏ nền hồng** và đoạn hướng dẫn in nghiêng ngay dưới nó, rồi xóa.
4. Chèn ảnh: **Insert → Pictures → This Device**, chọn tệp trong `report_figures/screenshots/`.
5. Đặt chiều rộng ảnh **16,2 cm** để khớp với các hình khác; căn giữa đoạn.
6. Thêm chú thích ngay dưới ảnh, in đậm, căn giữa, cỡ 12,5 pt, theo mẫu:
   `Hình 3.13b. Màn hình Két an toàn ở trạng thái đã mở khóa`
7. Bổ sung dòng tương ứng vào **DANH MỤC HÌNH VẼ** ở đầu tài liệu.
8. Nhấn **Ctrl+A** rồi **F9** để cập nhật lại mục lục tự động.

> Nếu chọn cách đánh số lại toàn bộ hình của Chương 3 thay vì dùng hậu tố `b`, hãy nhớ cập nhật cả
> các tham chiếu trong phần thân bài (báo cáo dẫn hình theo số ở nhiều chỗ).

---

## 5. Nguyên tắc bắt buộc

- **Tuyệt đối không dựng lại giao diện bằng công cụ thiết kế.** Nếu một trạng thái không chụp được,
  hãy giữ nguyên khối chỗ dành sẵn — một chỗ trống trung thực có giá trị hơn một hình minh họa
  không phản ánh phần mềm thật.
- **Không chỉnh sửa nội dung hiển thị trong ảnh.** Được phép cắt xén và thay đổi kích thước; không
  được phép sửa chữ, sửa số hay ghép các phần từ nhiều lần chạy khác nhau thành một thẻ kết quả.
- **Không đưa dữ liệu thật vào ảnh.** Mọi tệp, đường dẫn và bí mật xuất hiện trong ảnh phải là dữ
  liệu mẫu tạo riêng cho việc chụp.
- **Ghi lại điều kiện chụp.** Nếu ảnh được chụp trên một bản dựng khác với bản mô tả trong báo cáo
  (ví dụ có nhị phân ExifTool trong khi báo cáo mô tả bản không có), hãy ghi chú điều đó ngay trong
  chú thích hình.
