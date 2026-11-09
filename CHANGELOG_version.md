# Version Changelog / Nhật ký Thay đổi Phiên bản

[English](#english) | [Tiếng Việt](#tiếng-việt)

---

<a name="english"></a>
## ENGLISH

### 1.4.2 - 2026-11-08
- **Interactive Crime Scene Reconstruction:** Built a zero-dependency HTML5 investigation replay tool (`Interactive_Crime_Scene_Replay.html`) that emulates suspect messaging apps (Telegram, Discord, Zalo, etc.). Includes a Time-Machine chronological slider, multi-source ingestion of volatile RAM messages and disk records, smart pagination, a Forensic Inspector pane displaying memory byte offsets and SHA-256 hashes, phone directory extraction, and a carved media gallery.
- **In-App Auto-Update & Offline Patching:** Added seamless updating capabilities via GUI, CLI (`fdctl update check` / `fdctl update install`), and standalone offline patch runner (`update-offline.cmd`) designed to safely replace application code without revoking or modifying the active `license.key`.
- **Windows 11 Smart App Control Launchers:** Added `launch-gui.cmd` and `launch-analysis-terminal.cmd` to provide safe, policy-compliant execution in environments with strict application control policies (error code 4551).
- **Multi-Scope Investigation Architecture:** Introduced 4 flexible investigation scope modes across chat applications (Telegram & Discord):
  1. 💬 **Direct 1-on-1 Messages (DMs):** Targeted acquisition and analysis of private chats and bot conversations without enforcing group links.
  2. 👥 **Group / Channel Investigation:** Focused analysis of suspected group and channel interactions by URL or channel ID.
  3. 🎯 **Target User UID / Phone / Username Tracing:** Targeted filtering that extracts all messages sent by, to, or mentioning a specific target entity across the platform.
  4. 🌐 **Comprehensive Application Triage:** Full forensic sweep of all volatile RAM, cache, databases, and logs.
- **Dedicated Forensic Deliverables:** Added `07_Exports/direct_messages.csv`, `07_Exports/group_messages.csv`, and `07_Exports/target_user_messages.csv` to Autopsy-compatible schema and chain-of-custody handover documentation.
- **Interactive Scope Selector:** Enhanced both CLI (`--scope-type [all|dm|group|user]`) and Desktop GUI with intuitive scope selection prompts.

### 1.4.1 - 2026-11-07
- **Project Standardization:** Standardized brand and repository identity to **FORENSIC_SUITE**.
- **Telegram Live Process Memory Carving:** Built dedicated volatile memory carver (`TelegramMemoryCarver`) querying committed heap buffers (`MEM_COMMIT`) via Win32 API (`VirtualQueryEx`, `ReadProcessMemory`), recovering real-time chats, dialogue titles, @usernames, phone numbers, and bot interactions.
- **Streamlined UAC Permissions:** Removed forced elevation prompts for user-owned artifact extraction, preventing unexpected terminal window relaunches.

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

### 1.4.2 - 2026-11-08
- **Kiến trúc phân vùng phạm vi điều tra linh hoạt (Multi-Scope Investigation):** Bổ sung 4 chế độ khoanh vùng điều tra trên các ứng dụng chat (Telegram, Discord):
  1. 💬 **Đoạn chat riêng 1-1 (Direct Messages / Private Chats):** Cho phép giám định trực tiếp hội thoại riêng tư với người dùng hoặc bot mong muốn mà không bị ép buộc theo link/ID nhóm.
  2. 👥 **Kênh / Nhóm trò chuyện (Group / Channel):** Khoanh vùng điều tra chuyên sâu các thảo luận và thành viên trong nhóm/kênh nghi vấn.
  3. 🎯 **Truy vết theo định danh đối tượng (Target User UID / SĐT / Username Tracing):** Lọc toàn bộ tin nhắn gửi đến, gửi đi hoặc nhắc tên định danh UID, số điện thoại hoặc tên người dùng mục tiêu.
  4. 🌐 **Toàn bộ ứng dụng (Comprehensive / Toàn diện):** Rà soát toàn bộ bộ nhớ RAM, tệp đệm, lịch sử và nhật ký có thể phục hồi.
- **Bộ sản phẩm giám định xuất chuyên biệt:** Xuất khẩu minh bạch các tệp `07_Exports/direct_messages.csv`, `07_Exports/group_messages.csv`, và `07_Exports/target_user_messages.csv` tích hợp chuẩn Autopsy và biên bản bàn giao điện tử.
- **Giao diện lựa chọn tương tác:** Bổ sung tham số dòng lệnh `--scope-type [all|dm|group|user]` và danh sách chọn phạm vi trực quan trên Giao diện Đồ họa (GUI).

### 1.4.1 - 2026-11-07
- **Chuẩn hóa nhận diện dự án:** Đổi tên và chuẩn hóa nhận diện toàn diện sang **FORENSIC_SUITE**.
- **Trích xuất bộ nhớ tiến trình sống Telegram (Live Memory Carving):** Triển khai module bóc tách bộ nhớ RAM tiến trình `Telegram.exe` (Win32 API `VirtualQueryEx`, `ReadProcessMemory`), trích xuất trực tiếp hội thoại, tên nhóm, tin nhắn bot, @username và số điện thoại từ bộ nhớ đệm.
- **Tối ưu hóa phân quyền UAC:** Loại bỏ thông báo nâng quyền bắt buộc không cần thiết đối với các chứng cứ thuộc sở hữu phiên người dùng, giúp terminal chạy mượt mà liên tục.

### 1.4.0 - 2026-11-07
- **Thu thập chứng cứ Telegram Desktop:** Bổ sung module điều tra trích xuất dữ liệu tài khoản Telegram Desktop, phiên đăng nhập và thư mục tdata (kể cả bản Portable).
- **Kiến trúc bản quyền bền vững & Chống giả mạo:** Nâng cấp hệ thống chứng thực bản quyền 3 lớp với cơ chế đóng dấu bản quyền, nhật ký sử dụng và kiểm tra toàn vẹn tệp.
- **Cách ly bí mật tác giả tuyệt đối:** Xóa sạch toàn bộ mã băm phần hardware và danh tính máy nhà phát triển khỏi Git; cơ chế mở khóa tác giả hoạt động độc lập qua tệp cấu hình cục bộ bảo mật.
