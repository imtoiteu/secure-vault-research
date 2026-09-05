# FIGURE_INDEX — Chỉ mục hình vẽ và truy vết tới mã nguồn

> **Ghi chú đường dẫn (04-09-2026):** thư mục vỏ Tauri `desktop/` đã được đổi tên thành `app/`
> khi nó trở thành crate dùng chung cho desktop + Android + iOS. Các đường dẫn trích dẫn bên dưới
> là đường dẫn tại thời điểm viết tài liệu và được giữ nguyên để bảo toàn tính chính xác của hồ sơ;
> hãy đọc `desktop/...` là `app/...` của hiện tại.


Tài liệu này gắn **từng hình** trong báo cáo `BAO_CAO_DE_TAI_SECURE_VAULT_RESEARCH.docx` với **tệp mã nguồn** đã được đọc để dựng hình đó, cùng đường dẫn tới bản Draw.io chỉnh sửa được và bản SVG dùng để chèn vào Word.

Nguyên tắc áp dụng khi dựng hình:

- Mọi khối, mũi tên, nhãn và thứ tự thao tác đều được lấy từ mã nguồn thật trong `secure-vault-research/`. **Không có thành phần, kênh truyền, máy chủ, API, cơ sở dữ liệu hay bước mật mã nào được vẽ thêm.**
- Khi tài liệu thiết kế của dự án và mã nguồn mâu thuẫn nhau, **mã nguồn là chuẩn**.
- Bản `.drawio` được dựng từ **shape gốc của diagrams.net** (rounded rectangle, cylinder, note, umlActor, ellipse, rhombus, hexagon, connector…), **không phải** ảnh SVG nhúng vào khung, nên mở bằng diagrams.net là sửa được từng phần tử.
- Bản `.svg` là bản được chèn vào Word (kèm ảnh PNG dự phòng theo cơ chế `asvg:svgBlip`, nên Word hiển thị lớp vector).

Thư mục: `report_figures/drawio/`, `report_figures/svg/`, `report_figures/png/`, `report_figures/screenshots/`; các bản sao theo chương nằm trong `chapter2/`, `chapter3/`, `chapter4/`.

---

## Bảng chỉ mục

| Hình | Tiêu đề | Tệp mã nguồn / bằng chứng | Draw.io | SVG | Trong Word | Trạng thái |
|---|---|---|---|---|---|---|
| Hình 2.1 | Biểu đồ ca sử dụng tổng quát của hệ thống Secure Vault Research | desktop/src/lib.rs (generate_handler!), src-tauri/src/{lib,platform,stego,meta,watermark}.rs, docs/architecture/02-requirements-analysis.md §2.2 | `drawio/Hinh-2-01-use-case-tong-quat.drawio` | `svg/Hinh-2-01-use-case-tong-quat.svg` | Có (SVG + PNG dự phòng) | Đã sinh từ mã nguồn |
| Hình 2.2 | Biểu đồ ngữ cảnh của hệ thống Secure Vault Research | docs/architecture/01-system-overview.md §1.4; desktop/tauri.conf.json (CSP default-src 'self'); desktop/src/lib.rs resolve_binary | `drawio/Hinh-2-02-ngu-canh-he-thong.drawio` | `svg/Hinh-2-02-ngu-canh-he-thong.svg` | Có (SVG + PNG dự phòng) | Đã sinh từ mã nguồn |
| Hình 2.3 | Bốn ranh giới tin cậy và cơ chế kiểm soát tương ứng | src-tauri/src/passphrase.rs; crates/sv-age/src/lib.rs:62,108,147; crates/sv-core/src/container.rs:333; Cargo.toml (exclude=["desktop"]) | `drawio/Hinh-2-03-ranh-gioi-tin-cay.drawio` | `svg/Hinh-2-03-ranh-gioi-tin-cay.svg` | Có (SVG + PNG dự phòng) | Đã sinh từ mã nguồn |
| Hình 2.4 | Kiến trúc phân tầng của hệ thống từ L0 đến L5 | docs/architecture/03-system-architecture.md §3.2; Cargo.toml; crates/*/Cargo.toml | `drawio/Hinh-2-04-kien-truc-phan-tang.drawio` | `svg/Hinh-2-04-kien-truc-phan-tang.svg` | Có (SVG + PNG dự phòng) | Đã sinh từ mã nguồn |
| Hình 2.5 | Đồ thị phụ thuộc giữa các crate trong bản dựng sản phẩm | Cargo.toml và crates/*/Cargo.toml, src-tauri/Cargo.toml, desktop/Cargo.toml | `drawio/Hinh-2-05-do-thi-phu-thuoc-crate.drawio` | `svg/Hinh-2-05-do-thi-phu-thuoc-crate.svg` | Có (SVG + PNG dự phòng) | Đã sinh từ mã nguồn |
| Hình 2.6 | Kiến trúc triển khai và thực thi trên máy người dùng | desktop/tauri.conf.json (bundle.resources), desktop/src/lib.rs run()/resolve_binary, docs/DEPLOYMENT.md | `drawio/Hinh-2-06-kien-truc-trien-khai.drawio` | `svg/Hinh-2-06-kien-truc-trien-khai.svg` | Có (SVG + PNG dự phòng) | Đã sinh từ mã nguồn |
| Hình 2.7 | Biểu đồ tuần tự quá trình thêm một tệp vào két | src-tauri/src/service.rs add_item/write_vault/decrypt_archive; crates/sv-core/src/container.rs pack_archive/encode/write_atomic | `drawio/Hinh-2-07-tuan-tu-them-tep.drawio` | `svg/Hinh-2-07-tuan-tu-them-tep.svg` | Có (SVG + PNG dự phòng) | Đã sinh từ mã nguồn |
| Hình 2.8 | Ngăn xếp nguyên thủy mật mã: mục đích, cổng, bộ điều hợp và nền tảng | crates/sv-crypto-traits/src/lib.rs; crates/sv-crypto/src/{lib,secretbox,minisign,policy}.rs; crates/sv-age/src/lib.rs; docs/architecture/06-security-design.md §6.7 | `drawio/Hinh-2-08-ngan-xep-nguyen-thuy.drawio` | `svg/Hinh-2-08-ngan-xep-nguyen-thuy.svg` | Có (SVG + PNG dự phòng) | Đã sinh từ mã nguồn |
| Hình 2.9 | Phân cấp khóa của két an toàn và cơ chế bọc khóa theo trường | crates/sv-core/src/keys.rs (wrap_context, SUITE_VERSION); crates/sv-crypto/src/secretbox.rs; src-tauri/src/service.rs create/unlock | `drawio/Hinh-2-09-phan-cap-khoa.drawio` | `svg/Hinh-2-09-phan-cap-khoa.svg` | Có (SVG + PNG dự phòng) | Đã sinh từ mã nguồn |
| Hình 2.10 | Quy trình mã hóa và niêm phong két theo đường ghi | src-tauri/src/service.rs write_vault; crates/sv-core/src/container.rs pack_archive/encode/binding_root/write_atomic | `drawio/Hinh-2-10-quy-trinh-niem-phong.drawio` | `svg/Hinh-2-10-quy-trinh-niem-phong.svg` | Có (SVG + PNG dự phòng) | Đã sinh từ mã nguồn |
| Hình 2.11 | Quy trình mở khóa và thứ tự các cổng kiểm tra | src-tauri/src/service.rs unlock/decrypt_archive; crates/sv-core/src/container.rs parse_framing/decode; crates/sv-core/src/error.rs | `drawio/Hinh-2-11-quy-trinh-mo-khoa.drawio` | `svg/Hinh-2-11-quy-trinh-mo-khoa.svg` | Có (SVG + PNG dự phòng) | Đã sinh từ mã nguồn |
| Hình 2.12 | Bố cục byte của container .svault và phạm vi chữ ký | crates/sv-core/src/format.rs (MAGIC, FORMAT_VERSION); crates/sv-core/src/container.rs (HEADER_OFFSET, MAX_HEADER_LEN, binding_root) | `drawio/Hinh-2-12-bo-cuc-svault.drawio` | `svg/Hinh-2-12-bo-cuc-svault.svg` | Có (SVG + PNG dự phòng) | Đã sinh từ mã nguồn |
| Hình 2.13 | Mô hình dữ liệu của header CBOR và danh mục tệp | crates/sv-core/src/format.rs (VaultHeader, KdfRecord, WrappedSecret, SharePolicyRecord, ContentLayout, ItemDirectory, ItemEntry) | `drawio/Hinh-2-13-mo-hinh-du-lieu-header.drawio` | `svg/Hinh-2-13-mo-hinh-du-lieu-header.svg` | Có (SVG + PNG dự phòng) | Đã sinh từ mã nguồn |
| Hình 2.14 | Kiến trúc phòng thủ theo chiều sâu bảo vệ dữ liệu người dùng | docs/architecture/06-security-design.md §6.1–6.8; docs/M7-HARDENING.md | `drawio/Hinh-2-14-phong-thu-chieu-sau.drawio` | `svg/Hinh-2-14-phong-thu-chieu-sau.svg` | Có (SVG + PNG dự phòng) | Đã sinh từ mã nguồn |
| Hình 2.15 | Ánh xạ lỗi nội bộ sang mã lỗi công khai chống dò oracle | crates/sv-types/src/lib.rs (ApiError, ALL_CODES, io_generic); crates/sv-core/src/error.rs; crates/sv-platform/src/error.rs; crates/sv-stego/src/error.rs | `drawio/Hinh-2-15-anh-xa-loi-chong-oracle.drawio` | `svg/Hinh-2-15-anh-xa-loi-chong-oracle.svg` | Có (SVG + PNG dự phòng) | Đã sinh từ mã nguồn |
| Hình 2.16 | Vòng đời của bí mật trong bộ nhớ và cơ chế xóa | crates/sv-crypto-traits/src/lib.rs (Key32/SecretBytes/KeyShare); src-tauri/src/{passphrase,service}.rs; crates/sv-core/src/container.rs (UnpackedArchive::drop) | `drawio/Hinh-2-16-vong-doi-bi-mat.drawio` | `svg/Hinh-2-16-vong-doi-bi-mat.svg` | Có (SVG + PNG dự phòng) | Đã sinh từ mã nguồn |
| Hình 3.1 | Cấu trúc mã nguồn của workspace Secure Vault Research | Cargo.toml (members, exclude), cây thư mục crates/, src-tauri/, desktop/, docs/ | `drawio/Hinh-3-01-cau-truc-ma-nguon.drawio` | `svg/Hinh-3-01-cau-truc-ma-nguon.svg` | Có (SVG + PNG dự phòng) | Đã sinh từ mã nguồn |
| Hình 3.2 | Sơ đồ lớp của tầng hợp đồng mật mã và các bộ điều hợp hiện thực | crates/sv-crypto-traits/src/lib.rs; crates/sv-crypto/src/lib.rs | `drawio/Hinh-3-02-abi-mat-ma.drawio` | `svg/Hinh-3-02-abi-mat-ma.svg` | Có (SVG + PNG dự phòng) | Đã sinh từ mã nguồn |
| Hình 3.3 | Biểu đồ tuần tự quá trình khởi tạo két mới | src-tauri/src/service.rs create(); src-tauri/src/payload.rs generate_identity(); crates/sv-crypto/src/lib.rs SodiumMinisignSigner::generate | `drawio/Hinh-3-03-tuan-tu-tao-ket.drawio` | `svg/Hinh-3-03-tuan-tu-tao-ket.svg` | Có (SVG + PNG dự phòng) | Đã sinh từ mã nguồn |
| Hình 3.4 | Chia và khôi phục khóa chủ của két theo ngưỡng k trong n | src-tauri/src/service.rs split_key/recover, build_share_envelope/parse_share_envelope; crates/sv-crypto/src/lib.rs SssSharer | `drawio/Hinh-3-04-chia-khoi-phuc-khoa-chu.drawio` | `svg/Hinh-3-04-chia-khoi-phuc-khoa-chu.svg` | Có (SVG + PNG dự phòng) | Đã sinh từ mã nguồn |
| Hình 3.5 | Mã hóa và giải mã tệp độc lập bằng mật khẩu (định dạng SVENC) | crates/sv-platform/src/crypto.rs encrypt_file/decrypt_file; crates/sv-platform/src/artifact.rs seal_with_passphrase/open_with_passphrase | `drawio/Hinh-3-05-ma-hoa-tep-doc-lap.drawio` | `svg/Hinh-3-05-ma-hoa-tep-doc-lap.svg` | Có (SVG + PNG dự phòng) | Đã sinh từ mã nguồn |
| Hình 3.6 | Lược đồ chia sẻ bí mật lai: Shamir trên khóa dữ liệu kết hợp AEAD trên tải trọng | crates/sv-platform/src/sharing.rs split_core/recover_core/derive_payload_key, encode_share_string; crates/sv-qr/src/lib.rs | `drawio/Hinh-3-06-chia-se-bi-mat.drawio` | `svg/Hinh-3-06-chia-se-bi-mat.svg` | Có (SVG + PNG dự phòng) | Đã sinh từ mã nguồn |
| Hình 3.7 | Kiến trúc giấu tin theo nguyên tắc mã hóa rồi nhúng | crates/sv-stego/src/{pipeline,seal,envelope,capacity,selector,embed}.rs; crates/sv-stego/src/carrier/{spatial,jpeg}.rs | `drawio/Hinh-3-07-giau-tin-encrypt-then-embed.drawio` | `svg/Hinh-3-07-giau-tin-encrypt-then-embed.svg` | Có (SVG + PNG dự phòng) | Đã sinh từ mã nguồn |
| Hình 3.8 | Bảng các bộ dò giấu tin và cơ chế hợp nhất mức nghi ngờ | crates/sv-stego/src/detect/{mod,appended,chi_square,rs,jpeg_dct}.rs; sv_types::{StegoSignal, StegoDetectReport, Suspicion} | `drawio/Hinh-3-08-phat-hien-giau-tin.drawio` | `svg/Hinh-3-08-phat-hien-giau-tin.svg` | Có (SVG + PNG dự phòng) | Đã sinh từ mã nguồn |
| Hình 3.9 | Thủy vân vô hình, có khóa, dễ vỡ: nhúng và kiểm tra | crates/sv-watermark/src/lib.rs (BLOCK, PRESENCE_THRESHOLD, BLOCK_CONTEXT, PRESENCE_CONTEXT, WATERMARK_SALT) | `drawio/Hinh-3-09-thuy-van-de-vo.drawio` | `svg/Hinh-3-09-thuy-van-de-vo.svg` | Có (SVG + PNG dự phòng) | Đã sinh từ mã nguồn |
| Hình 3.10 | Bản đồ ba mươi tám lệnh IPC và năm trạng thái quản lý | desktop/src/lib.rs generate_handler! + run(); src-tauri/src/{lib,platform,stego,meta,watermark}.rs | `drawio/Hinh-3-10-ban-do-lenh-ipc.drawio` | `svg/Hinh-3-10-ban-do-lenh-ipc.svg` | Có (SVG + PNG dự phòng) | Đã sinh từ mã nguồn |
| Hình 3.11 | Sơ đồ điều hướng chính của giao diện người dùng | desktop/frontend/index.html (data-screen), main.js showScreen/wireSidebar, i18n.js | `drawio/Hinh-3-12-so-do-dieu-huong-giao-dien.drawio` | `svg/Hinh-3-12-so-do-dieu-huong-giao-dien.svg` | Có (SVG + PNG dự phòng) | Đã sinh từ mã nguồn |
| Hình 3.12 | Màn hình Trang chủ với ba thẻ bắt đầu nhanh và lưới toàn bộ công cụ | desktop/frontend/index.html + main.js + i18n.js + styles.css (kết xuất trực tiếp mã giao diện thật, không có lõi Rust chạy phía sau) | — | — | Có (PNG) | Ảnh chụp thật, trạng thái biểu mẫu trống |
| Hình 3.13 | Màn hình Két an toàn ở trạng thái đã khóa | desktop/frontend/index.html + main.js + i18n.js + styles.css (kết xuất trực tiếp mã giao diện thật, không có lõi Rust chạy phía sau) | — | — | Có (PNG) | Ảnh chụp thật, trạng thái biểu mẫu trống |
| (chỗ dành sẵn 1) | CHỖ DÀNH SẴN – CHÈN ẢNH CHỤP MÀN HÌNH KÉT AN TOÀN Ở TRẠNG THÁI ĐÃ MỞ KHÓA | — | — | — | Có (khối đỏ + hướng dẫn) | **Cần chụp thủ công** |
| Hình 3.14 | Màn hình Khóa tệp — mã hóa một tệp bằng mật khẩu | desktop/frontend/index.html + main.js + i18n.js + styles.css (kết xuất trực tiếp mã giao diện thật, không có lõi Rust chạy phía sau) | — | — | Có (PNG) | Ảnh chụp thật, trạng thái biểu mẫu trống |
| Hình 3.15 | Màn hình Ký tệp — tạo cặp khóa ký và ký tệp | desktop/frontend/index.html + main.js + i18n.js + styles.css (kết xuất trực tiếp mã giao diện thật, không có lõi Rust chạy phía sau) | — | — | Có (PNG) | Ảnh chụp thật, trạng thái biểu mẫu trống |
| Hình 3.16 | Màn hình Xác minh tệp tải về — kiểm theo giá trị băm và/hoặc chữ ký | desktop/frontend/index.html + main.js + i18n.js + styles.css (kết xuất trực tiếp mã giao diện thật, không có lõi Rust chạy phía sau) | — | — | Có (PNG) | Ảnh chụp thật, trạng thái biểu mẫu trống |
| Hình 3.17 | Màn hình Chia nhỏ bí mật theo ngưỡng k trong n | desktop/frontend/index.html + main.js + i18n.js + styles.css (kết xuất trực tiếp mã giao diện thật, không có lõi Rust chạy phía sau) | — | — | Có (PNG) | Ảnh chụp thật, trạng thái biểu mẫu trống |
| Hình 3.18 | Màn hình Khôi phục từ các mảnh — nhận cả tệp mảnh và chuỗi dán vào | desktop/frontend/index.html + main.js + i18n.js + styles.css (kết xuất trực tiếp mã giao diện thật, không có lõi Rust chạy phía sau) | — | — | Có (PNG) | Ảnh chụp thật, trạng thái biểu mẫu trống |
| (chỗ dành sẵn 2) | CHỖ DÀNH SẴN – CHÈN ẢNH CHỤP DANH SÁCH MẢNH SAU KHI CHIA THÀNH CÔNG | — | — | — | Có (khối đỏ + hướng dẫn) | **Cần chụp thủ công** |
| Hình 3.19 | Màn hình Giấu dữ liệu trong ảnh | desktop/frontend/index.html + main.js + i18n.js + styles.css (kết xuất trực tiếp mã giao diện thật, không có lõi Rust chạy phía sau) | — | — | Có (PNG) | Ảnh chụp thật, trạng thái biểu mẫu trống |
| Hình 3.20 | Màn hình Phát hiện dữ liệu ẩn | desktop/frontend/index.html + main.js + i18n.js + styles.css (kết xuất trực tiếp mã giao diện thật, không có lõi Rust chạy phía sau) | — | — | Có (PNG) | Ảnh chụp thật, trạng thái biểu mẫu trống |
| (chỗ dành sẵn 3) | CHỖ DÀNH SẴN – CHÈN ẢNH CHỤP BÁO CÁO PHÁT HIỆN GIẤU TIN | — | — | — | Có (khối đỏ + hướng dẫn) | **Cần chụp thủ công** |
| Hình 3.21 | Màn hình Chống giả mạo tệp — nhúng và kiểm tra thủy vân | desktop/frontend/index.html + main.js + i18n.js + styles.css (kết xuất trực tiếp mã giao diện thật, không có lõi Rust chạy phía sau) | — | — | Có (PNG) | Ảnh chụp thật, trạng thái biểu mẫu trống |
| Hình 3.22 | Màn hình Chuyển mảnh qua mã QR an toàn | desktop/frontend/index.html + main.js + i18n.js + styles.css (kết xuất trực tiếp mã giao diện thật, không có lõi Rust chạy phía sau) | — | — | Có (PNG) | Ảnh chụp thật, trạng thái biểu mẫu trống |
| Hình 3.23 | Màn hình Xem siêu dữ liệu ở trạng thái mô-đun chưa sẵn sàng | desktop/frontend/index.html + main.js + i18n.js + styles.css (kết xuất trực tiếp mã giao diện thật, không có lõi Rust chạy phía sau) | — | — | Có (PNG) | Ảnh chụp thật, trạng thái biểu mẫu trống |
| Hình 3.24 | Ghim băm nhị phân ngoài lúc biên dịch và phân giải lúc chạy | desktop/build.rs (emit_pin, detect_staged_target, check_staged_arch); desktop/src/lib.rs resolve_binary/build_backend/build_meta; crates/sv-age/src/lib.rs new_pinned | `drawio/Hinh-3-11-ghim-bam-nhi-phan.drawio` | `svg/Hinh-3-11-ghim-bam-nhi-phan.svg` | Có (SVG + PNG dự phòng) | Đã sinh từ mã nguồn |
| Hình 4.1 | Phân bố hàm kiểm thử theo crate | docs/architecture/08-testing-and-validation.md §8.2 (đo bằng cargo test --workspace, ngày 17-6-2026); đối chiếu bằng cách đếm chú thích #[test] trong cây mã | `drawio/Hinh-4-01-phan-bo-kiem-thu.drawio` | `svg/Hinh-4-01-phan-bo-kiem-thu.svg` | Có (SVG + PNG dự phòng) | Đã sinh từ mã nguồn |
| Hình 4.2 | Năm nhóm việc trong quy trình tích hợp liên tục | .github/workflows/ci.yml; docs/CI-VALIDATION.md (lần chạy xanh trên commit 780444d, ngày 15-6-2026) | `drawio/Hinh-4-02-cong-ci.drawio` | `svg/Hinh-4-02-cong-ci.svg` | Có (SVG + PNG dự phòng) | Đã sinh từ mã nguồn |
| Hình 4.3 | Thông lượng mã hóa và giải mã tải trọng qua tiến trình con age | docs/VALIDATION-RESULTS.md §H1 (mã hóa 1,35 s; giải mã 1,69 s cho 512 MiB). Đây là số đo thực tế, KHÔNG phải ước lượng. | `drawio/Hinh-4-03-thong-luong-age.drawio` | `svg/Hinh-4-03-thong-luong-age.svg` | Có (SVG + PNG dự phòng) | Đã sinh từ mã nguồn |
| Hình 4.4 | Đỉnh bộ nhớ thường trú khi thêm một tệp vào két | docs/VALIDATION-RESULTS.md §H1: thêm tệp 1024 MiB đạt đỉnh 2 852 782 080 byte ≈ 2,66 GiB (đo bằng /usr/bin/time -l, bản dựng release) | `drawio/Hinh-4-04-dinh-bo-nho.drawio` | `svg/Hinh-4-04-dinh-bo-nho.svg` | Có (SVG + PNG dự phòng) | Đã sinh từ mã nguồn |
| Hình 4.5 | Trạng thái bảy giả thuyết rủi ro sau đợt sửa chữa | docs/VALIDATION-PLAN.md và docs/VALIDATION-RESULTS.md (bảng trạng thái sau khi sửa) | `drawio/Hinh-4-05-trang-thai-gia-thuyet-rui-ro.drawio` | `svg/Hinh-4-05-trang-thai-gia-thuyet-rui-ro.svg` | Có (SVG + PNG dự phòng) | Đã sinh từ mã nguồn |

---

## Ghi chú về nguồn số liệu của các hình Chương 4

| Hình | Số liệu | Nguồn | Loại |
|---|---|---|---|
| Hình 4.1 | 253 hàm kiểm thử (249 đạt, 4 bỏ qua); phân bố theo 13 crate | `docs/architecture/08-testing-and-validation.md` §8.2, đo bằng `cargo test --workspace` ngày 17-6-2026; đối chiếu bằng đếm chú thích `#[test]` | **Số đo thật** |
| Hình 4.2 | 5 nhóm việc, 9 lượt chạy | `.github/workflows/ci.yml`; kết quả xanh ghi trong `docs/CI-VALIDATION.md` cho commit `780444d` (15-6-2026) | **Sự kiện có thật** |
| Hình 4.3 | 512 MiB: mã hóa 1,35 s (≈379 MiB/s); giải mã 1,69 s (≈303 MiB/s) | `docs/VALIDATION-RESULTS.md` §H1 | **Số đo thật** (1 cấu hình, 1 lần đo) |
| Hình 4.3 | Ngưỡng chạm hạn giờ ≈44 GiB / ≈35 GiB | Suy ra từ thông lượng đo được | *Ngoại suy, có ghi nhãn* |
| Hình 4.4 | 1024 MiB → đỉnh 2 852 782 080 B ≈ 2,66 GiB (≈2,7×) | `docs/VALIDATION-RESULTS.md` §H1, đo bằng `/usr/bin/time -l`, bản release | **Số đo thật** |
| Hình 4.4 | Các cột 256 MiB / 512 MiB / 2 GiB / 4 GiB | Ngoại suy tuyến tính từ hệ số 2,7× | *Ngoại suy, có ghi nhãn trên hình* |
| Hình 4.5 | Trạng thái H1–H7 trước và sau khi sửa; 8/8 và 12/12 lượt mất dữ liệu; 0/12 sau khi sửa | `docs/VALIDATION-PLAN.md` và `docs/VALIDATION-RESULTS.md` | **Kết quả thực nghiệm** |

**Không có con số hiệu năng nào trong báo cáo được bịa ra hoặc ước lượng mà không ghi nhãn.**

---

## Các mô-đun mã nguồn chính được dùng làm bằng chứng

| Mô-đun | Vai trò trong báo cáo |
|---|---|
| `crates/sv-crypto-traits/src/lib.rs` | Tầng ABI: 6 trait, kiểu bí mật/không bí mật, định danh thuật toán — Hình 2.8, 3.2, 2.16 |
| `crates/sv-crypto/src/{lib,secretbox,minisign,policy}.rs` | Bộ điều hợp BLAKE3/Argon2id/minisign/Shamir, bọc khóa, sàn tham số — Hình 2.8, 3.2 |
| `crates/sv-core/src/format.rs` | Bố cục `.svault`, `VaultHeader`, `ItemDirectory`, `CipherSuite` — Hình 2.12, 2.13 |
| `crates/sv-core/src/container.rs` | `encode`/`decode`/`parse_framing`/`binding_root`/`pack_archive`/`write_atomic` — Hình 2.10, 2.11, 2.12 |
| `crates/sv-core/src/keys.rs` | `wrap_context`, `SUITE_VERSION`, `StdKeyHierarchy` — Hình 2.9 |
| `crates/sv-core/src/error.rs` | Ánh xạ `VaultError` → `ApiError` — Hình 2.15 |
| `crates/sv-age/src/lib.rs` | Điều khiển tiến trình con age: ghim băm, 3 luồng, hạn giờ, tệp danh tính 0600 — Hình 2.3, 3.24 |
| `crates/sv-platform/src/{lib,artifact,crypto,integrity,sharing}.rs` | Dịch vụ mức tệp, SVENC/SVKEY, lược đồ chia sẻ lai — Hình 3.5, 3.6 |
| `crates/sv-stego/src/{pipeline,seal,envelope,capacity,selector,embed}.rs` | Mã hóa-rồi-nhúng, khung SVSTEG — Hình 3.7 |
| `crates/sv-stego/src/detect/*.rs` | Bảng bộ dò và hợp nhất mức nghi ngờ — Hình 3.8 |
| `crates/sv-watermark/src/lib.rs` | Thủy vân dễ vỡ có khóa, dấu hiệu hiện diện — Hình 3.9 |
| `crates/sv-meta/src/lib.rs` | ExifTool đã ghim băm, `-config ""`, phân loại mức bảo đảm khi xóa |
| `crates/sv-qr/src/lib.rs` | Bộ mã hóa/giải mã QR thuần Rust, chỉ vận chuyển |
| `crates/sv-types/src/lib.rs` | DTO, `ApiError` 12 mã, `nameframe` — Hình 2.15 |
| `src-tauri/src/service.rs` | `VaultBackend`: create/unlock/add_item/split_key/recover, khóa ghi, trần kích thước — Hình 2.7, 3.3, 3.4 |
| `src-tauri/src/{lib,platform,stego,meta,watermark}.rs` | Năm bề mặt lệnh — Hình 3.10 |
| `src-tauri/src/passphrase.rs` | `IpcPassphrase` và rủi ro tồn đọng N1 — Hình 2.3, 2.16 |
| `desktop/build.rs` | Nạp và ghim băm nhị phân, kiểm kiến trúc — Hình 3.24 |
| `desktop/src/lib.rs` | 38 `#[tauri::command]`, `resolve_binary`, `run()` — Hình 2.6, 3.10 |
| `desktop/frontend/*` | 20 màn hình, i18n tiếng Việt — Hình 3.11 và các ảnh chụp 3.12–3.23 |
| `Cargo.toml` + `crates/*/Cargo.toml` | Đồ thị phụ thuộc, `exclude = ["desktop"]` — Hình 2.4, 2.5, 3.1 |
| `.github/workflows/ci.yml` | Năm nhóm việc CI — Hình 4.2 |
| `docs/` (18 tệp) + `docs/architecture/` (10 chương) | Mô hình đe dọa, quyết định lược đồ, kết quả kiểm chứng |

---

## Cách tái tạo các hình

Các hình được sinh bằng bộ mã Python đi kèm (`figlib.py`, `fig_ch2.py`, `fig_ch3.py`, `fig_ch4.py` trong `report_figures/generator/`). Mỗi hình được mô tả **một lần** bằng một DSL nhỏ (Node/Edge/Zone) rồi kết xuất **đồng thời** ra `.drawio` và `.svg`, nên hai bản luôn khớp nhau.

```sh
cd report_figures/generator
python3 fig_ch2.py && python3 fig_ch3.py && python3 fig_ch4.py
python3 -c "import cairosvg,glob,os;[cairosvg.svg2png(url=p,write_to='../png/'+os.path.basename(p)[:-4]+'.png',scale=2.0) for p in glob.glob('../svg/*.svg')]"
```
