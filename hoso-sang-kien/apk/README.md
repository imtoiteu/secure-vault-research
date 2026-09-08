# Gói cài đặt Android (APK)

Thư mục này chứa tệp cài đặt Android của SecureVault Mobile và bằng chứng kiểm tra tĩnh
kèm theo.

> Trạng thái thực tế của gói cài đặt được ghi trong `../bang-chung/kiem-tra-apk.json`,
> do script `../kiem-tra-apk.py` sinh ra từ chính tệp APK. Nếu tệp JSON đó ghi
> `"co_apk": false` thì nghĩa là **chưa có APK** — hồ sơ khi đó cũng tự động ghi
> "chưa hoàn tất" ở phần tương ứng, không tuyên bố vượt quá thực tế.

---

## 1. Cách xây lại APK

Yêu cầu môi trường:

| Thành phần | Phiên bản đã dùng |
|---|---|
| Android NDK | r28c (clang 19.0.1) |
| Android SDK | build-tools 34.0.0, platform android-34 |
| JDK | 17 |
| Rust | 1.96 trở lên, target `aarch64-linux-android` |
| Tauri CLI | 2.11.4 |

```bash
export ANDROID_HOME=/đường/dẫn/android-sdk
export NDK_HOME=/đường/dẫn/android-ndk-r28c
export JAVA_HOME=/đường/dẫn/jdk-17

cd app
cargo tauri android build --debug --target aarch64
```

Trên máy có ít RAM (dưới 8 GB), cần thêm:

```bash
export CARGO_PROFILE_DEV_DEBUG=0   # tắt thông tin gỡ lỗi, giảm mạnh bộ nhớ khi liên kết
export CARGO_BUILD_JOBS=1
```

và bảo đảm có đủ bộ nhớ ảo (khuyến nghị tổng RAM + swap từ 12 GB trở lên). Bước liên kết
thư viện native là bước tốn bộ nhớ nhất của toàn bộ quá trình.

---

## 2. Kiểm tra gói cài đặt trước khi sử dụng

```bash
cd hoso-sang-kien
python3 kiem-tra-apk.py
```

Script kiểm tra ba điều mà hồ sơ có tuyên bố, để mỗi tuyên bố đều có bằng chứng:

1. **Thư viện lõi bảo mật nằm trong gói và đúng kiến trúc ARM64** — đọc trực tiếp phần đầu
   ELF của tệp `.so` trong gói, không dựa vào tên tệp.
2. **Ứng dụng không khai báo quyền truy cập mạng** — đọc tệp kê khai, đối chiếu thêm bằng
   `aapt2` nếu có.
3. **Toàn bộ giao diện được nhúng sẵn** — đếm tệp trong `assets/`, xác nhận có `index.html`.

Kết quả ghi ra `../bang-chung/kiem-tra-apk.json` kèm giá trị băm SHA-256 của gói, để đối
chiếu về sau.

---

## 3. Lưu ý quan trọng

**Đây là bản gỡ lỗi (debug), không phải bản phát hành.** Bản debug được ký bằng khoá gỡ lỗi
mặc định của Android, chỉ dùng để kiểm thử. Trước khi phân phối rộng cần:

- xây bản release (`cargo tauri android build --target aarch64`, bỏ `--debug`);
- ký bằng khoá phát hành của đơn vị và bảo quản khoá đó đúng quy định;
- chạy lại toàn bộ quy trình kiểm thử tại Phụ lục A của Thuyết minh trên thiết bị thật.

**Quyền truy cập mạng đã được gỡ có chủ đích.** Khuôn mẫu mặc định của Tauri khai báo
`android.permission.INTERNET` để phục vụ chế độ nạp lại nóng khi phát triển. SecureVault
hoạt động hoàn toàn ngoại tuyến nên quyền này đã được gỡ khỏi
`app/gen/android/app/src/main/AndroidManifest.xml`. Hệ quả: lệnh `cargo tauri android dev`
sẽ không dùng được; hãy dùng `cargo tauri android build`.

**Cài đặt lên máy thật:**

```bash
adb install -r <tên-tệp>.apk
```

Nếu máy từ chối cài, bật "Cài đặt ứng dụng không rõ nguồn gốc" cho ứng dụng nguồn
(trình quản lý tệp hoặc adb) trong phần Cài đặt bảo mật của điện thoại.
