//! Gốc hợp thành cho di động (Android + iOS).
//!
//! Không thể sinh tiến trình con ở đây: iOS cấm hoàn toàn, còn Android chặn thực thi tệp nhị
//! phân nằm trong vùng lưu trữ mà ứng dụng ghi được. Hai thành phần vốn dựa trên tiến trình
//! con trên máy tính để bàn vì vậy được thay bằng hai bản hiện thực chạy **trong tiến trình**,
//! và đó là toàn bộ khác biệt giữa hai nền tảng:
//!
//!   * bộ mã hoá nội dung két dùng [`RustAgePayloadCipher`]. Định dạng vẫn là age v1, đã kiểm
//!     chứng hai chiều với công cụ age chính thức và bằng phép mở chéo tệp .svault, nên két
//!     tạo trên máy tính mở được ở đây và ngược lại;
//!
//!   * mô-đun Phân tích siêu dữ liệu dùng [`RustMetaApp`] (crate `sv-meta-rs`) thay cho
//!     ExifTool. Phạm vi định dạng hẹp hơn ExifTool — hỗ trợ đọc EXIF của JPEG, PNG, TIFF,
//!     WebP, HEIF và xoá siêu dữ liệu của JPEG, PNG — nhưng đây là chức năng **có thật và
//!     chạy được** trên thiết bị, không phải trạng thái vô hiệu hoá. Định dạng ngoài phạm vi
//!     bị từ chối bằng lỗi có mã, không bao giờ báo "đã xoá" cho tệp chưa thực sự được xử lý.
//!
//! Không có tệp nhị phân nào được đóng gói kèm nên cũng không có mã băm nào cần kiểm: cơ chế
//! ghim băm mà `compose::desktop` thực hiện không có đối tượng trên nền tảng này.

use sv_app::{AppVault, RustAgePayloadCipher, RustMetaApp, VaultBackend};

/// Lõi két an toàn cụ thể do Tauri quản lý trên di động.
pub type Backend = AppVault<RustAgePayloadCipher>;

/// Bề mặt Phân tích siêu dữ liệu trên di động: chạy trong tiến trình, không cần ExifTool.
pub type Meta = RustMetaApp;

/// Dựng lõi két. Trên di động thao tác này không thể thất bại: không có gì để phân giải,
/// cũng không có mã băm nào để kiểm.
pub fn backend(_app: &tauri::AppHandle) -> Result<Backend, String> {
    Ok(AppVault::new(VaultBackend::new(RustAgePayloadCipher::new())))
}

/// Dựng bề mặt Phân tích siêu dữ liệu bằng mô-đun thuần Rust.
pub fn meta(_app: &tauri::AppHandle) -> Meta {
    RustMetaApp::new()
}
