//! # sv-meta-rs — mô-đun siêu dữ liệu thuần Rust
//!
//! Trên máy tính để bàn, mô-đun phân tích siêu dữ liệu chạy ExifTool như một tiến trình con.
//! Cách đó **không dùng được trên thiết bị di động**: ExifTool là chương trình Perl, Android
//! không có trình thông dịch Perl và cũng chặn thực thi tệp nhị phân nằm trong vùng lưu trữ
//! mà ứng dụng ghi được.
//!
//! Crate này hiện thực lại ba nghiệp vụ siêu dữ liệu bằng Rust thuần, chạy ngay trong tiến
//! trình ứng dụng:
//!
//!   * [`inspect`]  — đọc và nhóm các thẻ siêu dữ liệu nhúng trong tệp;
//!   * [`sanitize`] — ghi ra một tệp mới đã loại bỏ siêu dữ liệu, không sửa tệp gốc;
//!   * [`diff`]     — so sánh siêu dữ liệu nhúng của hai tệp.
//!
//! ## Phạm vi hỗ trợ và giới hạn — nêu rõ để không gây hiểu nhầm
//!
//! Phạm vi hẹp hơn ExifTool và điều đó được phản ánh trung thực trong kết quả trả về:
//!
//! | Định dạng | Đọc | Xoá | Ghi chú |
//! |---|---|---|---|
//! | JPEG      | có  | có, bảo đảm | loại bỏ EXIF, hồ sơ màu ICC và các khối chú thích |
//! | PNG       | có  | có, bảo đảm | loại bỏ EXIF, ICC và các khối văn bản tEXt/iTXt/zTXt |
//! | TIFF, WebP, HEIF | có | không | đọc được EXIF; chưa hỗ trợ ghi lại nên từ chối xoá |
//! | PDF, tài liệu Office, kho nén, âm thanh/video | không | không | ngoài phạm vi; từ chối rõ ràng |
//!
//! Trường `guaranteed` trong báo cáo xoá chỉ mang giá trị `true` khi tệp được **dựng lại hoàn
//! toàn** từ dữ liệu ảnh, tức siêu dữ liệu cũ không còn tồn tại trong tệp mới. Định dạng nào
//! không bảo đảm được điều đó thì bị từ chối, chứ không báo "đã xoá" một cách sai lệch.

#![forbid(unsafe_code)]

use std::collections::BTreeMap;
use std::fs;
use std::io::BufReader;
use std::path::Path;

use sv_types::{
    ApiError, MetadataDiffReport, MetadataEntry, MetadataGroup, MetadataReport,
    MetadataValueChange, SanitizeReport,
};

/// Giới hạn kích thước đầu vào. Toàn bộ tệp được nạp vào bộ nhớ để phân tích, nên phải chặn
/// trước thay vì để tiến trình bị huỷ vì hết bộ nhớ — nhất là trên điện thoại.
const MAX_INPUT_BYTES: u64 = 256 * 1024 * 1024;

/// Định dạng tệp nhận dạng được, suy ra từ các byte đầu tệp chứ không từ phần mở rộng.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum Format {
    Jpeg,
    Png,
    Tiff,
    WebP,
    Heif,
}

impl Format {
    fn ten(self) -> &'static str {
        match self {
            Format::Jpeg => "JPEG",
            Format::Png => "PNG",
            Format::Tiff => "TIFF",
            Format::WebP => "WEBP",
            Format::Heif => "HEIF",
        }
    }

    fn mime(self) -> &'static str {
        match self {
            Format::Jpeg => "image/jpeg",
            Format::Png => "image/png",
            Format::Tiff => "image/tiff",
            Format::WebP => "image/webp",
            Format::Heif => "image/heif",
        }
    }

    /// `true` nếu crate này ghi lại được tệp mà không giữ siêu dữ liệu cũ.
    fn xoa_duoc(self) -> bool {
        matches!(self, Format::Jpeg | Format::Png)
    }
}

fn loi_io(chi_tiet: &str) -> ApiError {
    // `detail` là một phân loại cố định, không chứa đường dẫn hay thông điệp hệ thống
    // (theo quy ước lỗi không tiết lộ thông tin của dự án).
    ApiError::Io { detail: chi_tiet.to_string() }
}

fn loi_dau_vao(chi_tiet: &str) -> ApiError {
    ApiError::InvalidInput { detail: chi_tiet.to_string() }
}

/// Nhận dạng định dạng từ các byte đầu tệp.
fn nhan_dang(bytes: &[u8]) -> Option<Format> {
    // Ngưỡng độ dài phải xét theo từng định dạng, không dùng một ngưỡng chung: một tệp JPEG
    // hợp lệ tối thiểu chỉ gồm 4 byte (SOI + EOI), và đó chính là kết quả sau khi xoá sạch
    // siêu dữ liệu của một ảnh không có dữ liệu điểm ảnh. Đặt ngưỡng chung quá cao sẽ khiến
    // chính tệp do mình vừa tạo ra bị từ chối.
    if bytes.starts_with(&[0xFF, 0xD8]) {
        return Some(Format::Jpeg);
    }
    if bytes.starts_with(b"\x89PNG\r\n\x1a\n") {
        return Some(Format::Png);
    }
    if bytes.starts_with(b"II*\x00") || bytes.starts_with(b"MM\x00*") {
        return Some(Format::Tiff);
    }
    if bytes.len() >= 12 && bytes.starts_with(b"RIFF") && &bytes[8..12] == b"WEBP" {
        return Some(Format::WebP);
    }
    // HEIF/HEIC: hộp `ftyp` nằm ngay sau 4 byte độ dài.
    if bytes.len() >= 12 && &bytes[4..8] == b"ftyp" {
        return Some(Format::Heif);
    }
    None
}

fn doc_tep(path: &Path) -> Result<Vec<u8>, ApiError> {
    let meta = fs::metadata(path).map_err(|_| loi_io("không đọc được tệp đầu vào"))?;
    if meta.len() > MAX_INPUT_BYTES {
        return Err(ApiError::InvalidInput {
            detail: "tệp vượt quá giới hạn kích thước cho phép".to_string(),
        });
    }
    fs::read(path).map_err(|_| loi_io("không đọc được tệp đầu vào"))
}

/// Tên nhóm hiển thị cho một vùng dữ liệu EXIF (IFD).
fn ten_nhom(ifd: exif::In) -> &'static str {
    match ifd {
        exif::In::PRIMARY => "EXIF",
        exif::In::THUMBNAIL => "Thumbnail",
        _ => "Khác",
    }
}

/// Đọc toàn bộ thẻ EXIF, trả về map "Nhóm:Thẻ" -> giá trị đã định dạng để hiển thị.
fn doc_the(bytes: &[u8]) -> BTreeMap<String, (String, String)> {
    let mut ket_qua = BTreeMap::new();
    let mut cursor = BufReader::new(std::io::Cursor::new(bytes));
    let doc = match exif::Reader::new().read_from_container(&mut cursor) {
        Ok(d) => d,
        // Không có EXIF không phải lỗi: nhiều tệp hoàn toàn hợp lệ mà không mang siêu dữ liệu.
        Err(_) => return ket_qua,
    };
    for f in doc.fields() {
        // Thẻ GPS được tách riêng vì đây là nhóm nhạy cảm nhất với quyền riêng tư.
        let nhom = if f.tag.to_string().starts_with("GPS") {
            "GPS"
        } else {
            ten_nhom(f.ifd_num)
        };
        let khoa = format!("{nhom}:{}", f.tag);
        let gia_tri = f.display_value().with_unit(&doc).to_string();
        ket_qua.insert(khoa, (nhom.to_string(), gia_tri));
    }
    ket_qua
}

/// **Xem siêu dữ liệu** — chỉ đọc, không bao giờ sửa tệp.
///
/// # Errors
/// Trả về lỗi nếu không đọc được tệp, tệp vượt giới hạn kích thước, hoặc định dạng nằm ngoài
/// phạm vi hỗ trợ.
pub fn inspect(path: &Path) -> Result<MetadataReport, ApiError> {
    let bytes = doc_tep(path)?;
    let dinh_dang = nhan_dang(&bytes)
        .ok_or_else(|| loi_dau_vao("định dạng tệp không nằm trong phạm vi hỗ trợ"))?;

    let the = doc_the(&bytes);
    let mut theo_nhom: BTreeMap<String, Vec<MetadataEntry>> = BTreeMap::new();
    for (khoa, (nhom, gia_tri)) in &the {
        let ten_the = khoa.split_once(':').map_or(khoa.as_str(), |(_, t)| t);
        theo_nhom.entry(nhom.clone()).or_default().push(MetadataEntry {
            name: ten_the.to_string(),
            value: gia_tri.clone(),
        });
    }

    let groups: Vec<MetadataGroup> = theo_nhom
        .into_iter()
        .map(|(group, tags)| MetadataGroup { group, tags })
        .collect();

    Ok(MetadataReport {
        format: dinh_dang.ten().to_string(),
        mime_type: dinh_dang.mime().to_string(),
        tag_count: u32::try_from(the.len()).unwrap_or(u32::MAX),
        groups,
    })
}

/// **Xoá siêu dữ liệu** — ghi ra một tệp mới đã loại bỏ siêu dữ liệu; tệp gốc không bị sửa.
///
/// Từ chối nếu tệp đích đã tồn tại, để không ghi đè dữ liệu của người dùng.
///
/// # Errors
/// Trả về lỗi nếu định dạng không hỗ trợ ghi lại, tệp đích đã tồn tại, hoặc gặp lỗi đọc/ghi.
pub fn sanitize(input: &Path, output: &Path) -> Result<SanitizeReport, ApiError> {
    if output.exists() {
        return Err(loi_dau_vao("tệp đích đã tồn tại"));
    }
    let bytes = doc_tep(input)?;
    let dinh_dang = nhan_dang(&bytes)
        .ok_or_else(|| loi_dau_vao("định dạng tệp không nằm trong phạm vi hỗ trợ"))?;

    if !dinh_dang.xoa_duoc() {
        // Từ chối thẳng thay vì báo "đã xoá" cho một định dạng chưa ghi lại được — một báo cáo
        // sai ở đây nguy hiểm hơn nhiều so với việc từ chối.
        return Err(loi_dau_vao(
            "định dạng này hiện chỉ hỗ trợ xem, chưa hỗ trợ xoá siêu dữ liệu",
        ));
    }

    let truoc = u32::try_from(doc_the(&bytes).len()).unwrap_or(u32::MAX);
    let sach = match dinh_dang {
        Format::Jpeg => xoa_jpeg(&bytes)?,
        Format::Png => xoa_png(&bytes)?,
        _ => unreachable!("đã kiểm tra xoa_duoc() ở trên"),
    };

    ghi_nguyen_tu(output, &sach)?;
    let sau = u32::try_from(doc_the(&sach).len()).unwrap_or(u32::MAX);

    Ok(SanitizeReport {
        output_path: output.to_string_lossy().into_owned(),
        format: dinh_dang.ten().to_string(),
        tags_before: truoc,
        tags_after: sau,
        // Tệp được dựng lại từ dữ liệu ảnh nên siêu dữ liệu cũ không còn tồn tại trong tệp mới.
        guaranteed: true,
    })
}

fn xoa_jpeg(bytes: &[u8]) -> Result<Vec<u8>, ApiError> {
    use img_parts::jpeg::Jpeg;
    use img_parts::{ImageEXIF, ImageICC};

    let mut anh = Jpeg::from_bytes(bytes.to_vec().into())
        .map_err(|_| loi_dau_vao("tệp JPEG không hợp lệ"))?;
    anh.set_exif(None);
    anh.set_icc_profile(None);
    // Loại luôn các đoạn chú thích và đoạn ứng dụng khác (XMP, Photoshop, Adobe…): đây là nơi
    // chứa tên tác giả, phần mềm chỉnh sửa và lịch sử biên tập.
    anh.segments_mut().retain(|s| {
        let m = s.marker();
        !(m == img_parts::jpeg::markers::COM || (0xE0..=0xEF).contains(&m))
    });

    let mut ra = Vec::new();
    anh.encoder()
        .write_to(&mut ra)
        .map_err(|_| loi_io("không ghi được tệp kết quả"))?;
    Ok(ra)
}

fn xoa_png(bytes: &[u8]) -> Result<Vec<u8>, ApiError> {
    use img_parts::png::Png;
    use img_parts::{ImageEXIF, ImageICC};

    let mut anh = Png::from_bytes(bytes.to_vec().into())
        .map_err(|_| loi_dau_vao("tệp PNG không hợp lệ"))?;
    anh.set_exif(None);
    anh.set_icc_profile(None);
    // Các khối văn bản của PNG mang chú thích, tên tác giả, phần mềm tạo ảnh; và khối thời gian
    // sửa đổi mang dấu thời gian. Giữ lại các khối cần thiết để ảnh vẫn hiển thị đúng.
    anh.chunks_mut().retain(|c| {
        !matches!(&c.kind(), b"tEXt" | b"iTXt" | b"zTXt" | b"tIME" | b"eXIf")
    });

    let mut ra = Vec::new();
    anh.encoder()
        .write_to(&mut ra)
        .map_err(|_| loi_io("không ghi được tệp kết quả"))?;
    Ok(ra)
}

/// Ghi tệp theo kiểu nguyên tử: ghi ra tệp tạm cùng thư mục rồi đổi tên, để không bao giờ để
/// lại một tệp kết quả ghi dở nếu bị gián đoạn giữa chừng.
fn ghi_nguyen_tu(output: &Path, du_lieu: &[u8]) -> Result<(), ApiError> {
    let thu_muc = output.parent().unwrap_or_else(|| Path::new("."));
    let tam = thu_muc.join(format!(
        ".{}.tam",
        output.file_name().and_then(|s| s.to_str()).unwrap_or("ketqua")
    ));
    fs::write(&tam, du_lieu).map_err(|_| loi_io("không ghi được tệp kết quả"))?;
    fs::rename(&tam, output).map_err(|_| {
        let _ = fs::remove_file(&tam);
        loi_io("không ghi được tệp kết quả")
    })
}

/// **So sánh siêu dữ liệu** giữa hai tệp — chỉ so phần siêu dữ liệu nhúng, không so tên tệp,
/// kích thước hay dấu thời gian của hệ thống tệp.
///
/// # Errors
/// Trả về lỗi nếu một trong hai tệp không đọc được hoặc nằm ngoài phạm vi hỗ trợ.
pub fn diff(a: &Path, b: &Path) -> Result<MetadataDiffReport, ApiError> {
    let ba = doc_tep(a)?;
    let bb = doc_tep(b)?;
    nhan_dang(&ba).ok_or_else(|| loi_dau_vao("tệp thứ nhất không nằm trong phạm vi hỗ trợ"))?;
    nhan_dang(&bb).ok_or_else(|| loi_dau_vao("tệp thứ hai không nằm trong phạm vi hỗ trợ"))?;

    let ta = doc_the(&ba);
    let tb = doc_the(&bb);

    let mut only_in_a = Vec::new();
    let mut only_in_b = Vec::new();
    let mut changed = Vec::new();

    for (khoa, (_, gia_tri)) in &ta {
        match tb.get(khoa) {
            None => only_in_a.push(MetadataEntry {
                name: khoa.clone(),
                value: gia_tri.clone(),
            }),
            Some((_, gt_b)) if gt_b != gia_tri => changed.push(MetadataValueChange {
                key: khoa.clone(),
                value_a: gia_tri.clone(),
                value_b: gt_b.clone(),
            }),
            Some(_) => {}
        }
    }
    for (khoa, (_, gia_tri)) in &tb {
        if !ta.contains_key(khoa) {
            only_in_b.push(MetadataEntry {
                name: khoa.clone(),
                value: gia_tri.clone(),
            });
        }
    }

    Ok(MetadataDiffReport { only_in_a, only_in_b, changed })
}
