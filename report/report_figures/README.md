# report_figures — Bộ hình vẽ và tài nguyên của báo cáo

Thư mục này chứa toàn bộ hình vẽ, ảnh chụp màn hình và mã sinh hình đi kèm báo cáo
`../BAO_CAO_DE_TAI_SECURE_VAULT_RESEARCH.docx`.

## Cấu trúc

```
report_figures/
├── FIGURE_INDEX.md        Chỉ mục hình ↔ tệp mã nguồn làm bằng chứng
├── MANUAL_SCREENSHOTS.md  Hướng dẫn chụp bổ sung các ảnh còn thiếu
├── README.md              Tệp này
├── drawio/                33 sơ đồ .drawio — shape gốc diagrams.net, sửa được từng phần tử
├── svg/                   33 bản .svg — bản được chèn vào Word
├── png/                   33 ảnh .png — bản dự phòng đi kèm SVG trong Word
├── screenshots/           20 ảnh chụp giao diện thật (PNG, 2160 × 1350)
├── chapter2/              Bản sao .drawio + .svg của 16 hình Chương 2
├── chapter3/              Bản sao .drawio + .svg của 12 hình Chương 3
├── chapter4/              Bản sao .drawio + .svg của 5 hình Chương 4
├── generator/             Mã Python sinh hình (figlib.py, fig_ch2/3/4.py)
└── docx_build/            Mã Python dựng tài liệu Word (docxlib.py, build_report.py, nội dung)
```

## Con số tổng hợp

| Hạng mục | Số lượng |
|---|---:|
| Sơ đồ kỹ thuật (mỗi sơ đồ có cả `.drawio` và `.svg`) | 33 |
| Ảnh chụp giao diện thật đã chụp | 20 |
| Ảnh chụp được chèn vào báo cáo | 12 |
| Chỗ dành sẵn cần chụp thủ công | 3 |
| Tổng số hình trong báo cáo | 48 |
| Bảng trong báo cáo | 15 |

## Nguyên tắc dựng hình

1. **Chỉ vẽ những gì có trong mã nguồn.** Mọi khối, mũi tên, nhãn và thứ tự thao tác đều truy vết
   được tới một tệp trong `secure-vault-research/`. Không có máy chủ, API, cơ sở dữ liệu, kênh
   truyền hay bước mật mã nào được thêm vào cho "đẹp sơ đồ".
2. **Mã nguồn là chuẩn.** Khi tài liệu thiết kế của dự án mâu thuẫn với mã, hình vẽ theo mã.
3. **Một mô tả, hai kết xuất.** Mỗi hình được mô tả một lần bằng DSL trong `generator/`, rồi kết
   xuất đồng thời ra `.drawio` và `.svg`, nên hai bản luôn khớp nhau.
4. **`.drawio` là sơ đồ gốc, không phải ảnh nhúng.** Kiểm chứng: 33 tệp đều là XML hợp lệ, tổng
   cộng 872 đối tượng và 273 đường nối, dùng shape gốc của diagrams.net (`rounded=1`, `ellipse`,
   `rhombus`, `cylinder3`, `umlActor`, `text`).

## Tái tạo

```sh
# Sinh lại toàn bộ .drawio và .svg
cd generator && python3 fig_ch2.py && python3 fig_ch3.py && python3 fig_ch4.py

# Sinh lại ảnh PNG dự phòng
cd .. && python3 -c "import cairosvg,glob,os;[cairosvg.svg2png(url=p,write_to='png/'+os.path.basename(p)[:-4]+'.png',scale=2.0) for p in glob.glob('svg/*.svg')]"

# Dựng lại tài liệu Word
cd docx_build && python3 build_report.py
```

Yêu cầu: Python 3, các gói `python-docx`, `Pillow`, `lxml`, `cairosvg`.

## Về ảnh chụp màn hình

Các ảnh trong `screenshots/` được kết xuất từ **chính mã giao diện thật** của hệ thống, không có
lõi Rust chạy phía sau, nên chúng thể hiện đúng bố cục và nhãn tiếng Việt nhưng không thể hiện kết
quả của thao tác thực. Chi tiết về điều kiện chụp và danh mục ảnh còn thiếu nằm trong
[`MANUAL_SCREENSHOTS.md`](MANUAL_SCREENSHOTS.md).
