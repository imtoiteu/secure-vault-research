//! Kiểm thử mô-đun siêu dữ liệu thuần Rust bằng ảnh do chính kiểm thử dựng ra.
//!
//! Ảnh mẫu được tạo trong bộ nhớ (không phụ thuộc tệp bên ngoài) rồi nhúng khối EXIF chứa tên
//! phần mềm và một khối chú thích — đúng loại dữ liệu người dùng cần xoá trước khi chia sẻ.

use std::path::PathBuf;

use sv_meta_rs::{diff, inspect, sanitize};

/// Thư mục tạm tự dọn sau khi kiểm thử xong.
struct Tam(PathBuf);

impl Tam {
    fn moi(ten: &str) -> Self {
        let d = std::env::temp_dir().join(format!("sv-meta-rs-{ten}-{}", std::process::id()));
        std::fs::create_dir_all(&d).unwrap();
        Self(d)
    }
    fn tep(&self, ten: &str) -> PathBuf {
        self.0.join(ten)
    }
}

impl Drop for Tam {
    fn drop(&mut self) {
        let _ = std::fs::remove_dir_all(&self.0);
    }
}

/// Dựng một JPEG tối giản hợp lệ kèm khối EXIF (thẻ Software) và một khối chú thích.
fn jpeg_co_exif() -> Vec<u8> {
    // Khối EXIF: phần đầu TIFF little-endian + IFD0 với một thẻ Software.
    let mut tiff: Vec<u8> = Vec::new();
    tiff.extend_from_slice(b"II*\x00"); // little-endian, magic 42
    tiff.extend_from_slice(&8u32.to_le_bytes()); // vị trí IFD0
    tiff.extend_from_slice(&1u16.to_le_bytes()); // số mục trong IFD
    tiff.extend_from_slice(&0x0131u16.to_le_bytes()); // thẻ Software
    tiff.extend_from_slice(&2u16.to_le_bytes()); // kiểu ASCII
    tiff.extend_from_slice(&9u32.to_le_bytes()); // độ dài 9 byte
    tiff.extend_from_slice(&26u32.to_le_bytes()); // vị trí giá trị
    tiff.extend_from_slice(&0u32.to_le_bytes()); // không có IFD kế tiếp
    tiff.extend_from_slice(b"SecureVa\0"); // giá trị Software

    let mut exif = Vec::new();
    exif.extend_from_slice(b"Exif\0\0");
    exif.extend_from_slice(&tiff);

    let mut jpeg: Vec<u8> = Vec::new();
    jpeg.extend_from_slice(&[0xFF, 0xD8]); // SOI
    jpeg.extend_from_slice(&[0xFF, 0xE1]); // APP1 (EXIF)
    jpeg.extend_from_slice(&(u16::try_from(exif.len() + 2).unwrap()).to_be_bytes());
    jpeg.extend_from_slice(&exif);
    jpeg.extend_from_slice(&[0xFF, 0xFE]); // COM (chú thích)
    jpeg.extend_from_slice(&7u16.to_be_bytes());
    jpeg.extend_from_slice(b"BIMAT"); // nội dung chú thích
    jpeg.extend_from_slice(&[0xFF, 0xD9]); // EOI
    jpeg
}

#[test]
fn doc_duoc_the_exif_trong_anh() {
    let t = Tam::moi("inspect");
    let p = t.tep("anh.jpg");
    std::fs::write(&p, jpeg_co_exif()).unwrap();

    let bc = inspect(&p).expect("phải đọc được siêu dữ liệu");
    assert_eq!(bc.format, "JPEG");
    assert_eq!(bc.mime_type, "image/jpeg");
    assert!(bc.tag_count > 0, "phải tìm thấy ít nhất một thẻ");
    let co_software = bc
        .groups
        .iter()
        .flat_map(|g| &g.tags)
        .any(|t| t.name.contains("Software"));
    assert!(co_software, "phải đọc được thẻ Software: {:?}", bc.groups);
}

#[test]
fn xoa_sach_sieu_du_lieu_va_giu_nguyen_tep_goc() {
    let t = Tam::moi("sanitize");
    let vao = t.tep("goc.jpg");
    let ra = t.tep("sach.jpg");
    let goc = jpeg_co_exif();
    std::fs::write(&vao, &goc).unwrap();

    let bc = sanitize(&vao, &ra).expect("phải xoá được");
    assert!(bc.tags_before > 0, "tệp gốc phải có siêu dữ liệu");
    assert_eq!(bc.tags_after, 0, "tệp kết quả không được còn thẻ nào");
    assert!(bc.guaranteed, "JPEG phải được đánh dấu xoá bảo đảm");

    // Tệp gốc không bị sửa — cam kết quan trọng với người dùng.
    assert_eq!(std::fs::read(&vao).unwrap(), goc, "tệp gốc phải nguyên vẹn");

    // Chú thích trong khối COM cũng phải biến mất, không chỉ riêng EXIF.
    let sach = std::fs::read(&ra).unwrap();
    assert!(
        !sach.windows(5).any(|w| w == b"BIMAT"),
        "chú thích trong tệp phải bị loại bỏ"
    );
    assert!(sach.starts_with(&[0xFF, 0xD8]), "kết quả phải còn là JPEG");
}

#[test]
fn khong_ghi_de_tep_dich_da_ton_tai() {
    let t = Tam::moi("nooverwrite");
    let vao = t.tep("goc.jpg");
    let ra = t.tep("dich.jpg");
    std::fs::write(&vao, jpeg_co_exif()).unwrap();
    std::fs::write(&ra, b"du lieu cu cua nguoi dung").unwrap();

    assert!(sanitize(&vao, &ra).is_err(), "phải từ chối ghi đè");
    assert_eq!(
        std::fs::read(&ra).unwrap(),
        b"du lieu cu cua nguoi dung",
        "tệp đích phải giữ nguyên"
    );
}

#[test]
fn so_sanh_phat_hien_sieu_du_lieu_da_bi_xoa() {
    let t = Tam::moi("diff");
    let goc = t.tep("goc.jpg");
    let sach = t.tep("sach.jpg");
    std::fs::write(&goc, jpeg_co_exif()).unwrap();
    sanitize(&goc, &sach).unwrap();

    let d = diff(&goc, &sach).expect("phải so sánh được");
    assert!(
        !d.only_in_a.is_empty(),
        "các thẻ chỉ có ở tệp gốc phải được liệt kê"
    );
    assert!(d.only_in_b.is_empty(), "tệp đã xoá không được có thẻ riêng");
}

#[test]
fn tu_choi_dinh_dang_ngoai_pham_vi() {
    let t = Tam::moi("unsupported");
    let p = t.tep("tailieu.pdf");
    std::fs::write(&p, b"%PDF-1.7\n% khong phai anh\n").unwrap();
    assert!(inspect(&p).is_err(), "phải từ chối định dạng ngoài phạm vi");
}
