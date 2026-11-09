# Forensics Suite — Hướng dẫn Cài đặt & Sử dụng / Installation & Usage Guide

[Tiếng Việt](#tiếng-việt) | [English](#english)

---

<a name="tiếng-việt"></a>
## TIẾNG VIỆT

Forensics Suite là bộ công cụ phần mềm hỗ trợ nghiên cứu và điều tra kỹ thuật số (DFIR) trên Windows, hỗ trợ thu thập dấu vết, bóc tách tin nhắn bộ nhớ đệm, trích xuất khóa phiên và xuất báo cáo với quy trình được thiết kế định hướng theo các nguyên tắc của tiêu chuẩn ISO/IEC 27037 & TCVN ISO/IEC 27037:2019.

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
Yêu cầu: Máy tính cài **Windows 10/11** hoặc **Linux (Ubuntu, Debian, Fedora, Arch, Kali)** và **Python 3.10** trở lên.

##### Trên Windows:
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

##### Trên Linux (Ubuntu, Debian, Fedora, Arch, Kali Linux):
1. Mở Terminal và clone repository:
   ```bash
   git clone https://github.com/Azynora/Forensic-Tools.git
   cd Forensic-Tools
   ```
2. Khởi tạo môi trường ảo Python:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Cấp quyền thực thi và mở Menu Điều tra Tương tác:
   ```bash
   chmod +x fdctl fdctl.sh
   ./fdctl menu
   ```
   *(Hoặc: `python3 -m fdctl menu`)*

---

### PHẦN 2: HƯỚNG DẪN SỬ DỤNG CHI TIẾT

#### 1. Sử dụng Menu Điều tra Tương tác (Khuyên dùng)
Khi chạy lệnh `.\fdctl.cmd menu`, hệ thống sẽ hiển thị bảng điều khiển trực quan:
* **[1] Discord Desktop**: Quét tài khoản, trích xuất LevelDB, token, tin nhắn đệm, lịch sử TCP socket.
* **[2] Telegram Desktop**: Quét thư mục `tdata`, phiên đăng nhập, tài khoản, voice notes, hình ảnh đệm.
* **[3] Chạy Chế độ Demo Giả lập**: Khảo sát quy trình điều tra hoàn chỉnh bằng dữ liệu giả lập an toàn (dành cho người mới).
* **[4] Quản lý & Kích hoạt Bản quyền**: Kiểm tra trạng thái máy, kích hoạt License Key.

---

#### 2. Tùy Chọn Khoanh Vùng Phạm Vi Điều Tra (Investigation Scope Modes)
Forensics Suite cho phép điều tra viên linh hoạt khoanh vùng phạm vi thu thập, không bắt buộc phải có link nhóm:

| Chế độ điều tra | Tham số CLI | Ý nghĩa & Mục đích sử dụng |
| :--- | :--- | :--- |
| 💬 **Đoạn chat riêng 1-1** | --scope-type dm --target-user <username/UID> | Thu thập & trích xuất hội thoại riêng tư với người dùng hoặc bot cụ thể. Xuất direct_messages.csv. |
| 👥 **Kênh / Nhóm trò chuyện** | --scope-type group --channel-url <link/ID nhóm> | Điều tra các tin nhắn, tệp đính kèm trong nhóm hoặc kênh nghi vấn. Xuất group_messages.csv. |
| 🎯 **Truy vết định danh UID** | --scope-type user --target-user <UID/SĐT/username> | Rà soát toàn bộ tin nhắn gửi đến, gửi đi hoặc nhắc tên UID/SĐT đối tượng. Xuất 	arget_user_messages.csv. |
| 🌐 **Toàn bộ ứng dụng** | --scope-type all | Rà soát toàn bộ bộ nhớ RAM, tệp đệm, lịch sử và nhật ký có thể phục hồi. |

#### 3. Quy trình Điều tra Dòng lệnh (CLI Commands)

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
  * Facebook: [https://www.facebook.com/azynora.vn](https://www.facebook.com/azynora.vn)

---
---

<a name="english"></a>
## ENGLISH

Forensics Suite is a specialized Windows digital forensics and incident response (DFIR) research toolkit designed to acquire artifacts, parse cached chat messages, extract session tokens, and generate standardized investigation reports designed with reference to ISO/IEC 27037 principles.

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
Requirements: **Windows 10/11** or **Linux (Ubuntu, Debian, Fedora, Arch, Kali)** and **Python 3.10+**.

##### On Windows:
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

##### On Linux (Ubuntu, Debian, Fedora, Arch, Kali Linux):
1. Clone repository from GitHub:
   ```bash
   git clone https://github.com/Azynora/Forensic-Tools.git
   cd Forensic-Tools
   ```
2. Create virtual environment and install dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Make launchers executable and launch the Interactive CLI Menu:
   ```bash
   chmod +x fdctl fdctl.sh
   ./fdctl menu
   ```
   *(Or: `python3 -m fdctl menu`)*

---

### SECTION 2: STEP-BY-STEP FORENSIC WORKFLOW

#### 1. Interactive CLI Menu
Running `.\fdctl.cmd menu` launches an intuitive guided triage console:
* **[1] Discord Desktop**: Audit user accounts, LevelDB chat store, authentication tokens, and active socket connections.
* **[2] Telegram Desktop**: Acquire `tdata` session maps, active accounts, encrypted cache databases, and voice notes.
* **[3] Run Synthetic Demo Case**: Safe simulation mode demonstrating complete end-to-end investigation workflows.
* **[4] License Management**: Inspect HWID, activate official license keys.

---

#### 2. Multi-Scope Investigation Modes
Forensics Suite allows investigators to flexibly target evidence acquisition without enforcing group links:

| Scope Mode | CLI Arguments | Purpose & Outputs |
| :--- | :--- | :--- |
| 💬 **Direct 1-on-1 Chat** | --scope-type dm --target-user <username/UID> | Investigates private conversation with a specific user or bot. Exports direct_messages.csv. |
| 👥 **Group / Channel** | --scope-type group --channel-url <link/channel_id> | Concentrates on suspect group or channel messages. Exports group_messages.csv. |
| 🎯 **Target User UID Tracing** | --scope-type user --target-user <UID/phone/username> | Filters all messages sent to, from, or mentioning a specific target entity. Exports 	arget_user_messages.csv. |
| 🌐 **Full Application Triage** | --scope-type all | Sweeps all volatile RAM, cache, history, and carved records. |

#### 3. Direct CLI Commands

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
  * Facebook: [https://www.facebook.com/azynora.vn](https://www.facebook.com/azynora.vn)

---

**Author / Tác giả:** Trương Triệu Vỹ (Truong Trieu Vy)
* Email: [trieuvy9198@gmail.com](mailto:trieuvy9198@gmail.com)
* Telegram: [@azynora](https://t.me/azynora) · Facebook: [azynora.vn](https://www.facebook.com/azynora.vn)

> ⚠️ **Khuyến cáo Pháp lý / Legal Disclaimer**:
> Phần mềm được phát triển cho mục đích học tập, nghiên cứu khoa học, kiểm thử an toàn thông tin và phục vụ công tác điều tra số (DFIR) của các cá nhân, tổ chức có thẩm quyền. Người sử dụng tự chịu hoàn toàn trách nhiệm pháp lý khi vận hành công cụ, bảo đảm tuân thủ nghiêm ngặt Luật An toàn thông tin mạng 2015, Luật An ninh mạng 2018 và các quy định pháp luật hiện hành. Dự án không đưa ra bất kỳ cam kết hay tuyên bố mang tính tuyệt đối nào theo quy định của Luật Quảng cáo 2012.


---

### SECTION 4: INTERACTIVE CRIME SCENE RECONSTRUCTION & IN-APP UPDATER

#### 1. Interactive Crime Scene Reconstruction (`Interactive_Crime_Scene_Replay.html`)
Every investigation report now automatically compiles a zero-dependency, self-contained HTML5 Crime Scene Reconstruction application in `08_Report/Interactive_Crime_Scene_Replay.html`:
* **Multi-Channel Emulation**: Faithfully reproduces the target messaging interface (Telegram, Discord, Zalo, etc.) with real carved conversation channels, direct messages, and groups.
* **Carved Phone & Username Directory**: Dedicated channel tab categorizing all discovered phone numbers and user handles with verification confidence scores.
* **Carved Media Gallery**: Visual grid of recovered cached images, audio, and attachments with computed SHA-256 integrity hashes.
* **Forensic Inspector Pane**: Clicking on any dialogue or message immediately displays forensic provenance, including process ID, memory byte offset (`RAM:PID:0x...`), integrity verification status, and decoded plaintext.
* **Time-Machine Slider**: Drag the chronological slider to replay the exact communication sequence step-by-step.

#### 2. In-App Updates & Offline Patching (License-Preserving)
Updating Forensics Suite does **not** revoke, overwrite, or delete your activated `license.key`:
* **Online Check (CLI & GUI)**:
  ```powershell
  .\fdctl.cmd update check
  .\fdctl.cmd update install
  ```
  Or navigate to **Trợ giúp (Help) -> Kiểm tra cập nhật (Check for Updates)** in the GUI.
* **Offline Patching via `update-offline.cmd`**:
  For isolated lab workstations or air-gapped forensic environments:
  ```powershell
  .\update-offline.cmd path\to\ForensicsSuite_Patch_vX.X.X.zip
  ```
  The updater securely replaces program binaries and scripts while keeping your configuration, cases, and `license.key` intact.

#### 3. Windows 11 Smart App Control Notice
If Windows 11 Smart App Control blocks the compiled `.exe` (`CreateProcess failed: code 4551`), run Forensics Suite using the pre-configured script launchers:
* **`launch-gui.cmd`**: Runs the forensic GUI safely through the trusted Python runtime.
* **`launch-analysis-terminal.cmd`**: Runs the CLI analysis terminal.
