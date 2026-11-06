# Forensics Suite — Hướng dẫn Sử dụng / Usage Guide

[Tiếng Việt](#tiếng-việt) | [English](#english)

---

<a name="tiếng-việt"></a>
## TIẾNG VIỆT

Bộ công cụ điều tra pháp chứng số chuyên sâu cho ứng dụng nhắn tin trên Windows, hỗ trợ thu thập dấu vết, phục hồi tin nhắn cache, trích xuất token/session và xuất báo cáo chuẩn HTML & Autopsy.

### 1. Dành cho người dùng GUI (Ứng dụng Đồ họa)

1. Tải bộ cài đặt `ForensicsSuite_Setup.exe` từ [GitHub Releases](https://github.com/Azynora/Forensic-Tools/releases/latest).
2. Chạy file cài đặt, sau đó mở **Forensics Suite** từ Start Menu hoặc màn hình Desktop.
3. Không cần cài đặt Python hay cấu hình môi trường; toàn bộ thư viện cần thiết đã được đóng gói sẵn.
4. Bạn có thể chuyển đổi ngôn ngữ linh hoạt giữa Tiếng Việt và Tiếng Anh ở góc dưới bên trái giao diện.
5. Xem tab **Demo dữ liệu** để tìm hiểu quy trình điều tra mẫu hoàn chỉnh (dữ liệu giả lập an toàn, không can thiệp vào máy).

### 2. Dành cho Kỹ thuật viên / Nhà nghiên cứu dùng CLI (Terminal)

Yêu cầu Windows 10/11 và Python 3.10 trở lên:

```powershell
# 1. Tải mã nguồn về máy
git clone https://github.com/Azynora/Forensic-Tools.git
cd Forensic-Tools

# 2. Khởi tạo môi trường ảo Python và cài đặt thư viện
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

# 3. Mở Menu Điều tra Dòng lệnh Tương tác
.\fdctl.cmd menu
```

#### Các lệnh CLI điều tra Discord thường dùng:

```powershell
# Quét và kiểm tra trạng thái Discord trên máy
.\fdctl.cmd apps detect

# Tạo hồ sơ điều tra mới
.\fdctl.cmd case create --app discord --id case_discord_001

# Thu thập chứng cứ và trích xuất cache/session
.\fdctl.cmd collect --case case_discord_001

# Phân tích dấu vết và trích xuất tin nhắn
.\fdctl.cmd analyze --case case_discord_001

# Xây dựng báo cáo điều tra HTML và gói Autopsy
.\fdctl.cmd report build --case case_discord_001
.\fdctl.cmd report open --case case_discord_001
```

### 3. Quản lý Bản quyền (License)

- **Xem mã định danh phần cứng (Hardware Fingerprint):**
  ```powershell
  .\fdctl.cmd license machine
  ```
- **Kích hoạt mã bản quyền:**
  ```powershell
  .\fdctl.cmd license activate --key <LICENSE-KEY> --email <GMAIL-ADDRESS>
  ```
- Gửi mã máy và địa chỉ Gmail của bạn cho tác giả qua email: `trieuvy9198@gmail.com` để nhận khóa bản quyền kích hoạt chính thức.

---

<a name="english"></a>
## ENGLISH

Comprehensive Windows digital forensics platform for messaging applications, supporting artifact acquisition, cached message recovery, token/session extraction, and standardized HTML & Autopsy reporting.

### 1. For GUI Desktop Users

1. Download the official installer `ForensicsSuite_Setup.exe` from [GitHub Releases](https://github.com/Azynora/Forensic-Tools/releases/latest).
2. Run the setup wizard and launch **Forensics Suite** from your Start menu or Desktop shortcut.
3. No Python installation or runtime setup is required; all dependencies are bundled into the binary.
4. Easily switch between English and Vietnamese via the bottom-left sidebar toggle.
5. Explore the **Sample Walkthrough (Demo)** tab to inspect an end-to-end synthetic investigation case.

### 2. For Investigators & Developers using CLI (Terminal)

Requirements: Windows 10/11 and Python 3.10+:

```powershell
# 1. Clone repository
git clone https://github.com/Azynora/Forensic-Tools.git
cd Forensic-Tools

# 2. Set up virtual environment and install dependencies
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

# 3. Open Interactive CLI Terminal Menu
.\fdctl.cmd menu
```

#### Canonical Discord Forensic CLI Commands:

```powershell
# Detect installed messaging apps and statuses
.\fdctl.cmd apps detect

# Create a new investigation case
.\fdctl.cmd case create --app discord --id case_discord_001

# Collect raw artifacts, cache databases, and session state
.\fdctl.cmd collect --case case_discord_001

# Analyze evidence and extract structured chat timelines
.\fdctl.cmd analyze --case case_discord_001

# Build canonical HTML forensic report and Autopsy bundle
.\fdctl.cmd report build --case case_discord_001
.\fdctl.cmd report open --case case_discord_001
```

### 3. License Management

- **Inspect local device hardware fingerprint:**
  ```powershell
  .\fdctl.cmd license machine
  ```
- **Activate a signed license key:**
  ```powershell
  .\fdctl.cmd license activate --key <LICENSE-KEY> --email <GMAIL-ADDRESS>
  ```
- To request an active license, send your hardware fingerprint and Gmail address to the author at: `trieuvy9198@gmail.com`.

---

**Author / Tác giả:** Truong Trieu Vy · [trieuvy9198@gmail.com](mailto:trieuvy9198@gmail.com)
