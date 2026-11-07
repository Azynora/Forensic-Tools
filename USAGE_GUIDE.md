# Forensics Suite — Hướng dẫn Cài đặt & Sử dụng / Installation & Usage Guide

[Tiếng Việt](#tiếng-việt) | [English](#english)

---

<a name="tiếng-việt"></a>
## TIẾNG VIỆT

Forensics Suite là bộ công cụ điều tra kỹ thuật số và phản ứng sự cố (DFIR) chuyên nghiệp dành cho Windows, hỗ trợ thu thập dấu vết, phục hồi tin nhắn cache, trích xuất khóa phiên/token và xuất báo cáo giám định theo chuẩn quốc tế ISO/IEC 27037:2012.

---

### PHẦN 1: CÁC PHƯƠNG THỨC CÀI ĐẶT & CHẠY TOOL

#### Cách 1: Sử dụng Bản Đóng Gói Sẵn (.EXE / .ZIP) — *Khuyên dùng cho người dùng & điều tra viên*
Không cần cài đặt Python, không cần cấu hình dòng lệnh phức tạp.

1. Truy cập mục **[GitHub Releases](https://github.com/Azynora/Forensic-Tools/releases/latest)** và tải:
   * **`ForensicsSuite_Setup.exe`**: Trình cài đặt đồ họa tự động (tạo shortcut ngoài Desktop và Start Menu).
   * **`ForensicsSuite_portable.zip`**: Bản Portable không cần cài đặt, giải nén trực tiếp vào USB hiện trường để điều tra Offline mà không để lại dấu vết trên máy đối tượng.
2. Nhấp đúp vào `ForensicsSuite.exe` để mở ứng dụng đồ họa GUI, hoặc chạy `fdctl.cmd` để vào terminal.
3. Chuyển đổi ngôn ngữ Tiếng Việt / Tiếng Anh dễ dàng ở thanh điều hướng.

---

#### Cách 2: Chạy Từ Mã Nguồn CLI (Terminal) — *Dành cho chuyên gia DFIR & Developer*
Yêu cầu: Máy tính cài **Windows 10/11** và **Python 3.10** trở lên.

1. Mở PowerShell hoặc Command Prompt, tải mã nguồn về:
   ```powershell
   git clone https://github.com/Azynora/Forensic-Tools.git
   cd Forensic-Tools
   ```
2. Khởi tạo môi trường ảo Python và cài đặt các thư viện cần thiết:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   ```
3. Mở Menu Điều tra Tương tác:
   ```powershell
   .\fdctl.cmd menu
   ```
   *(Hoặc: `python -m fdctl menu`)*

---

### PHẦN 2: HƯỚNG DẪN SỬ DỤNG CHI TIẾT

#### 1. Sử dụng Menu Điều tra Tương tác (Khuyên dùng)
Khi chạy lệnh `.\fdctl.cmd menu`, hệ thống sẽ hiển thị bảng điều khiển trực quan:
* **[1] Discord Desktop**: Quét tài khoản, trích xuất LevelDB, token, tin nhắn đệm, lịch sử TCP socket.
* **[2] Telegram Desktop**: Quét thư mục `tdata`, phiên đăng nhập, tài khoản, voice notes, hình ảnh đệm.
* **[3] Chạy Chế độ Demo Giả lập**: Khảo sát quy trình điều tra hoàn chỉnh bằng dữ liệu giả lập an toàn (dành cho người mới).
* **[4] Quản lý & Kích hoạt Bản quyền**: Kiểm tra trạng thái máy, kích hoạt License Key.

---

#### 2. Quy trình Điều tra Dòng lệnh (CLI Commands)

##### A. Điều tra Telegram Desktop:
```powershell
# 1. Quét và phát hiện các thư mục tdata (Cài đặt máy hoặc Portable)
.\fdctl.cmd apps detect

# 2. Khởi tạo hồ sơ vụ án Telegram
.\fdctl.cmd case create --app telegram --id case_tele_001

# 3. Thu thập toàn bộ chứng cứ (tdata, session maps, accounts, media cache)
.\fdctl.cmd collect --case case_tele_001

# 4. Phân tích dữ liệu phiên và liên kết dấu vết
.\fdctl.cmd analyze --case case_tele_001

# 5. Xuất báo cáo kết quả và mở xem trực tiếp
.\fdctl.cmd report build --case case_tele_001
.\fdctl.cmd report open --case case_tele_001
```

##### B. Điều tra Discord Desktop:
```powershell
# 1. Khởi tạo hồ sơ vụ án Discord
.\fdctl.cmd case create --app discord --id case_discord_001

# 2. Thu thập dữ liệu LevelDB, Local Storage, Token và TCP Socket
.\fdctl.cmd collect --case case_discord_001

# 3. Phân tích tin nhắn cache và khôi phục ảnh/media
.\fdctl.cmd analyze --case case_discord_001

# 4. Xuất báo cáo HTML và xuất bộ nạp tương thích với Autopsy
.\fdctl.cmd report build --case case_discord_001
.\fdctl.cmd report open --case case_discord_001
```

---

### PHẦN 3: QUẢN LÝ BẢN QUYỀN (LICENSE)

Forensics Suite áp dụng công nghệ chữ ký số mật mã Ed25519 quân sự để đảm bảo bản quyền:

* **Xem mã băm phần cứng máy (Hardware Fingerprint):**
  ```powershell
  .\fdctl.cmd license machine
  ```
* **Kích hoạt mã bản quyền bằng lệnh:**
  ```powershell
  .\fdctl.cmd license activate --key <LICENSE-KEY> --email <GMAIL-ADDRESS>
  ```
* **Kích hoạt tự động trên USB Hiện trường (Portable Triage):**
  * Chỉ cần chép file `license.key` được cấp vào thư mục gốc của tool (hoặc trên USB). Phần mềm sẽ tự động nhận diện và mở khóa 100% tính năng mà không cần gõ lệnh.
* **Liên hệ cấp bản quyền:**
  * Tác giả: **Trương Triệu Vỹ** (`Truong Trieu Vy`)
  * Email: [trieuvy9198@gmail.com](mailto:trieuvy9198@gmail.com)
  * Telegram: [@azynora](https://t.me/azynora)
  * Zalo: [https://zalo.me/0364228378](https://zalo.me/0364228378)
  * Facebook: [https://www.facebook.com/azynora.vn](https://www.facebook.com/azynora.vn)

---
---

<a name="english"></a>
## ENGLISH

Forensics Suite is an enterprise-grade Windows digital forensics and incident response (DFIR) platform designed to acquire artifacts, recover cached chat messages, extract session tokens, and generate court-ready reports adhering to ISO/IEC 27037:2012 standards.

---

### SECTION 1: INSTALLATION & RUNNING OPTIONS

#### Option 1: Standalone Compiled Executable (.EXE / .ZIP) — *Recommended for Investigators*
No Python installation or command-line configuration required.

1. Go to **[GitHub Releases](https://github.com/Azynora/Forensic-Tools/releases/latest)** and download:
   * **`ForensicsSuite_Setup.exe`**: Automatic installer with Start Menu and Desktop shortcuts.
   * **`ForensicsSuite_portable.zip`**: Zero-install standalone zip designed for field USB triage drives (runs 100% offline without leaving host traces).
2. Double-click `ForensicsSuite.exe` to launch the GUI, or execute `fdctl.cmd` for console triage.
3. Switch between English and Vietnamese anytime via the navigation sidebar.

---

#### Option 2: Run from Source CLI (Terminal) — *For Developers & DFIR Engineers*
Requirements: **Windows 10/11** and **Python 3.10+**.

1. Clone repository from GitHub:
   ```powershell
   git clone https://github.com/Azynora/Forensic-Tools.git
   cd Forensic-Tools
   ```
2. Create virtual environment and install dependencies:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   ```
3. Launch the Interactive CLI Menu:
   ```powershell
   .\fdctl.cmd menu
   ```
   *(Or: `python -m fdctl menu`)*

---

### SECTION 2: STEP-BY-STEP FORENSIC WORKFLOW

#### 1. Interactive CLI Menu
Running `.\fdctl.cmd menu` launches an intuitive guided triage console:
* **[1] Discord Desktop**: Audit user accounts, LevelDB chat store, authentication tokens, and active socket connections.
* **[2] Telegram Desktop**: Acquire `tdata` session maps, active accounts, encrypted cache databases, and voice notes.
* **[3] Run Synthetic Demo Case**: Safe simulation mode demonstrating complete end-to-end investigation workflows.
* **[4] License Management**: Inspect HWID, activate official license keys.

---

#### 2. Direct CLI Commands

##### A. Telegram Desktop Forensics:
```powershell
# 1. Detect installed Telegram client or portable tdata roots
.\fdctl.cmd apps detect

# 2. Create investigation case
.\fdctl.cmd case create --app telegram --id case_tele_001

# 3. Collect raw artifacts, tdata maps, and media caches
.\fdctl.cmd collect --case case_tele_001

# 4. Analyze session tokens and account activity
.\fdctl.cmd analyze --case case_tele_001

# 5. Build and view canonical HTML report
.\fdctl.cmd report build --case case_tele_001
.\fdctl.cmd report open --case case_tele_001
```

##### B. Discord Desktop Forensics:
```powershell
# 1. Create investigation case
.\fdctl.cmd case create --app discord --id case_discord_001

# 2. Acquire LevelDB, Local Storage, User Tokens, and live TCP Sockets
.\fdctl.cmd collect --case case_discord_001

# 3. Analyze cached messages and carve embedded attachments
.\fdctl.cmd analyze --case case_discord_001

# 4. Generate report and export Autopsy ingest bundle
.\fdctl.cmd report build --case case_discord_001
.\fdctl.cmd report open --case case_discord_001
```

---

### SECTION 3: LICENSING & DEPLOYMENT

Forensics Suite employs asymmetric Ed25519 digital signatures:

* **Inspect Device Hardware Fingerprint (HWID):**
  ```powershell
  .\fdctl.cmd license machine
  ```
* **Activate License Key via Command:**
  ```powershell
  .\fdctl.cmd license activate --key <LICENSE-KEY> --email <GMAIL-ADDRESS>
  ```
* **Drop-in Portable License (Field USB Triage):**
  * Simply place `license.key` into the root directory of Forensics Suite on your USB drive. The application detects and validates it automatically on any suspect workstation.
* **Request an Official License:**
  * Author: **Trương Triệu Vỹ** (`Truong Trieu Vy`)
  * Email: [trieuvy9198@gmail.com](mailto:trieuvy9198@gmail.com)
  * Telegram: [@azynora](https://t.me/azynora)
  * Zalo: [https://zalo.me/0364228378](https://zalo.me/0364228378)
  * Facebook: [https://www.facebook.com/azynora.vn](https://www.facebook.com/azynora.vn)

---

**Author / Tác giả:** Trương Triệu Vỹ (Truong Trieu Vy)
* Email: [trieuvy9198@gmail.com](mailto:trieuvy9198@gmail.com)
* Telegram: [@azynora](https://t.me/azynora) · Zalo: [0364.228.378](https://zalo.me/0364228378) · Facebook: [azynora.vn](https://www.facebook.com/azynora.vn)
