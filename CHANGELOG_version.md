# Version Changelog / Nhật ký Thay đổi Phiên bản

[English](#english) | [Tiếng Việt](#tiếng-việt)

---

<a name="english"></a>
## ENGLISH

### 1.4.0 - 2026-11-07
- **Telegram Forensic Acquisition:** Integrated deep forensics support for Telegram Desktop, parsing active sessions, accounts, and portable tdata storage.
- **Sustainable Licensing Architecture:** Upgraded licensing subsystem with watermarking, usage auditing, and tamper verification.
- **Isolated Author Secrets:** Completely purged developer machine fingerprints and author credentials from public repository. Author bypass operates dynamically through external local secrets.
- **Bilingual CLI Experience:** Enhanced terminal workflow supporting seamless switching between Vietnamese and English.

### 1.3.0 - 2026-11-06
- **Architecture separation:** Open-core model with pure CLI toolkit published on GitHub and proprietary GUI packaged as binary releases.
- **Enhanced Security:** Private key issuance and author machine fingerprints completely removed from the public client repository.
- **High-DPI GUI:** Crisp typography using Windows High-DPI awareness, clean BMP icons, and solved text truncation in case browser and help views.
- **Multi-app Roadmap:** Added integrated application catalog with Discord active and planned modules for Zalo, Telegram, WhatsApp, Messenger, and Signal.
- **Synthetic Walkthrough:** Built-in fictional demo case allowing investigators to evaluate workflow safely without reading local user data.

### 1.2.0 - 2026-11-06
- Added bilingual desktop GUI with Discord workflow, case browser, license activation, and settings.
- Enforced cryptographic feature entitlements at collection boundaries with local device-bound Ed25519 verification.
- Integrated Inno Setup installer builder.

### 1.1.9 - 2026-11-06
- Streamlined documentation, bilingual READMEs, and eliminated local dev paths.
- Updated `fdctl` core command-line suite and secured case directories.

---

<a name="tiếng-việt"></a>
## TIẾNG VIỆT

### 1.4.0 - 2026-11-07
- **Thu thập chứng cứ Telegram Desktop:** Bổ sung module điều tra trích xuất dữ liệu tài khoản Telegram Desktop, phiên đăng nhập và thư mục tdata (kể cả bản Portable).
- **Kiến trúc bản quyền bền vững & Chống giả mạo:** Nâng cấp hệ thống chứng thực bản quyền 3 lớp với cơ chế đóng dấu bản quyền, nhật ký sử dụng và kiểm tra toàn vẹn tệp.
- **Cách ly bí mật tác giả tuyệt đối:** Xóa sạch toàn bộ mã băm phần cứng và danh tính máy nhà phát triển khỏi Git; cơ chế mở khóa tác giả hoạt động độc lập qua tệp cấu hình cục bộ bảo mật.
- **Nâng cấp CLI Song ngữ:** Tối ưu hóa trải nghiệm dòng lệnh mượt mà giữa Tiếng Việt và Tiếng Anh.

### 1.3.0 - 2026-11-06
- **Tách bạch kiến trúc an toàn:** Mô hình mã nguồn mở cho bộ công cụ CLI Terminal trên GitHub, ứng dụng đồ họa GUI được đóng gói độc quyền dưới dạng file cài đặt `.exe`.
- **Bảo mật tuyệt đối hệ thống bản quyền:** Loại bỏ hoàn toàn mã tạo key, thuật toán ký số Private Key và mã máy tác giả khỏi mã nguồn công khai; chuyển chức năng cấp key vào công cụ nội bộ riêng.
- **Nâng cấp giao diện GUI sắc nét (High-DPI):** Bật chế độ DPI Awareness trên Windows, sử dụng bộ biểu tượng BMP chuẩn chống vỡ hình, sửa triệt để lỗi hiển thị bảng case và căn lề văn bản tab Trợ giúp.
- **Lộ trình hỗ trợ đa nền tảng:** Tích hợp danh mục ứng dụng với Discord hoạt động chính thức và lộ trình các ứng dụng Zalo, Telegram, WhatsApp, Messenger, Signal.
- **Chế độ Demo trực quan:** Cung cấp hồ sơ mẫu giả lập an toàn giúp kiểm thử toàn diện tính năng mà không can thiệp vào dữ liệu máy thật.

### 1.2.0 - 2026-11-06
- Bổ sung ứng dụng GUI song ngữ cho Discord, quản lý hồ sơ, cấu hình workspace và kích hoạt khóa bản quyền.
- Tích hợp xác thực bản quyền số Ed25519 gắn liền với phần cứng thiết bị.
- Hỗ trợ đóng gói trình cài đặt tự động bằng Inno Setup.

### 1.1.9 - 2026-11-06
- Tối ưu tài liệu song ngữ, làm sạch đường dẫn nhị phân cá nhân khỏi repo.
- Chuẩn hóa bộ công cụ dòng lệnh `fdctl` và tăng cường an toàn dữ liệu case.
