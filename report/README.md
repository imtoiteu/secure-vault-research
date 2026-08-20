# report — Báo cáo đề tài Secure Vault Research

Thư mục này chứa báo cáo kỹ thuật/học thuật đầy đủ về hệ thống Secure Vault Research, cùng toàn bộ
hình vẽ và mã sinh hình đi kèm.

## Nội dung

| Tệp / thư mục | Mô tả |
|---|---|
| [`BAO_CAO_DE_TAI_SECURE_VAULT_RESEARCH.docx`](BAO_CAO_DE_TAI_SECURE_VAULT_RESEARCH.docx) | Báo cáo hoàn chỉnh — 128 trang A4, tiếng Việt, ~47 700 từ |
| [`report_figures/`](report_figures/) | 33 sơ đồ (`.drawio` + `.svg` + `.png`), 20 ảnh chụp giao diện, mã sinh hình |
| [`report_figures/FIGURE_INDEX.md`](report_figures/FIGURE_INDEX.md) | Chỉ mục truy vết từng hình tới tệp mã nguồn làm bằng chứng |
| [`report_figures/MANUAL_SCREENSHOTS.md`](report_figures/MANUAL_SCREENSHOTS.md) | Hướng dẫn chụp bổ sung ba ảnh màn hình còn thiếu |

## Kết cấu báo cáo

- **MỞ ĐẦU** — tính cấp thiết, mục tiêu, nhiệm vụ, đối tượng, phạm vi, phương pháp, đóng góp
- **Chương 1 — Cơ sở khoa học và thực tiễn**: nền tảng mật mã ứng dụng, khảo sát công cụ hiện có,
  nguyên tắc chỉ lắp ghép nguyên thủy đã được kiểm chứng
- **Chương 2 — Phân tích và thiết kế hệ thống**: yêu cầu, mô hình đe dọa, ranh giới tin cậy, kiến
  trúc phân tầng, kiến trúc mật mã, phân cấp khóa, định dạng dữ liệu, kiến trúc an ninh nhiều lớp
  (16 hình)
- **Chương 3 — Xây dựng và triển khai hệ thống**: tổ chức mã nguồn, hiện thực từng tầng và từng
  mô-đun, bề mặt lệnh IPC, giao diện, làm cứng và đóng gói (12 sơ đồ + 12 ảnh chụp)
- **Chương 4 — Thử nghiệm và đánh giá**: bộ kiểm thử, cổng CI, thẩm định thuộc tính an toàn, đo
  hiệu năng, chiến dịch kiểm chứng giả thuyết rủi ro H1–H7 (5 hình)
- **KẾT LUẬN** và **TÀI LIỆU THAM KHẢO** (26 mục)

Tổng cộng: 48 hình, 15 bảng.

## Nguyên tắc biên soạn

1. **Mã nguồn là chuẩn.** Toàn bộ nội dung kỹ thuật được tái dựng từ ~16 300 dòng Rust trong
   workspace này. Khi tài liệu thiết kế mâu thuẫn với mã, báo cáo theo mã.
2. **Phân biệt rõ trạng thái hiện thực.** Báo cáo tách bạch cái *đã hiện thực hóa*, cái *đã có mã
   nhưng chưa nối vào đường sản phẩm* (hiệu chỉnh tham số Argon2id, cổng kiểm tra tương thích chữ
   ký), và cái *mới nằm trong kế hoạch* (truyền dòng, thủy vân bền vững, mật mã hậu lượng tử, khóa
   phần cứng).
3. **Không phóng đại bảo đảm.** Báo cáo phân biệt bốn loại phát biểu có giá trị chứng minh khác
   nhau: mục tiêu thiết kế, cơ chế đã hiện thực, thuộc tính đã được kiểm thử, và thuộc tính được
   giả định từ nguyên thủy. Không có thuộc tính nào được chứng minh hình thức, và báo cáo nói rõ
   điều đó.
4. **Không bịa số liệu.** Mọi con số hiệu năng đều lấy từ `docs/VALIDATION-RESULTS.md`; các giá trị
   ngoại suy đều được ghi nhãn ngay trên hình.
5. **Không bịa ảnh chụp.** Ảnh giao diện được kết xuất từ chính mã frontend thật; ba trạng thái có
   kết quả không chụp được đã để chỗ dành sẵn kèm hướng dẫn thay vì dựng hình giả.

## Tái tạo

```sh
cd report/report_figures/generator
python3 fig_ch2.py && python3 fig_ch3.py && python3 fig_ch4.py
cd ../docx_build && python3 build_report.py
```

Yêu cầu: Python 3 với `python-docx`, `Pillow`, `lxml`, `cairosvg`.
