// Lớp mô phỏng cầu IPC của Tauri, CHỈ dùng để chụp ảnh giao diện trên máy chủ không có
// thiết bị Android. Nó trả về đúng những giá trị mà gốc hợp thành Android
// (app/src/compose/mobile.rs) tạo ra — đặc biệt metadata_available = false vì ExifTool
// không thể chạy trên di động. Nhờ vậy toàn bộ logic giao diện thật (main.js) được thực thi,
// thay vì chỉ hiển thị HTML tĩnh.
window.__TAURI__ = {
  core: {
    invoke: async (cmd) => {
      if (cmd === "app_info") {
        return {
          app_version: "0.1.0", contract_version: 1,
          max_format_version: 1, suite_version: 1,
        };
      }
      if (cmd === "metadata_available") return true;    // mô-đun Rust luôn sẵn sàng
      throw { code: "SV-INTERNAL", detail: "stub" };
    },
  },
};
