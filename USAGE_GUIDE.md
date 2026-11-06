# Hướng dẫn sử dụng

## 1. Yêu cầu

- Bản portable: Windows 11 64-bit; không cần cài Python.
- Mã nguồn: Python 3.10 trở lên.
- Thu thập Discord có thể yêu cầu quyền Administrator.
- Chỉ sử dụng trên thiết bị và dữ liệu mà bạn có thẩm quyền kiểm tra.

## 2. Khởi chạy

Giải nén bundle vào thư mục có quyền ghi, mở PowerShell tại thư mục đó:

```powershell
.\fdctl.cmd --help
.\launch-analysis-terminal.cmd
```

Lệnh `fdctl.cmd` dùng để chạy lệnh trực tiếp; launcher mở menu điều tra tương tác. Kiểm tra ứng dụng được nhận diện:

```powershell
.\fdctl.cmd apps detect
```

## 3. Quy trình case

### Tạo case

```powershell
.\fdctl.cmd case create --app discord --id case_001
```

Có thể ghi scope theo kênh và người dùng:

```powershell
.\fdctl.cmd case create --app discord --id case_001 --channel-url "https://discord.com/channels/GUILD_ID/CHANNEL_ID" --target-user "USER_ID_OR_NAME"
```

Nhập ID/URL cụ thể nếu có. Scope giúp phân tích lọc kết quả; nó không giới hạn toàn bộ artifact mà collector sao chép.

### Thu thập, phân tích và báo cáo

```powershell
.\fdctl.cmd collect --case case_001
.\fdctl.cmd analyze --case case_001
.\fdctl.cmd supplement --case case_001
.\fdctl.cmd report build --case case_001
.\fdctl.cmd report open --case case_001
.\fdctl.cmd case save --case case_001
```

Thu thập có thể tạo ảnh chụp màn hình, inventory tiến trình/kết nối và sao chép artifact từ Discord desktop cùng Chrome profile mặc định. Kiểm tra `copy_errors.csv`, manifest và completeness matrix để biết dữ liệu nào thiếu hoặc không đọc được.

## 4. Nơi lưu dữ liệu

Mặc định workspace nằm cạnh bundle:

```text
workspace\runtime\<case-id>   Case đang làm
workspace\cases\<case-id>     Case đã lưu
```

Để dùng ổ đĩa khác, đặt biến môi trường trong PowerShell trước khi chạy:

```powershell
$env:FDCTL_DATA_ROOT = "E:\DFIR_CASES"
.\fdctl.cmd apps detect
```

## 5. Đầu ra chính

- `01_Case_Info\artifact_manifest.csv`: danh sách file đã thu thập và hash bản sao.
- `01_Case_Info\copy_errors.csv`: lỗi sao chép ghi nhận được.
- `07_Exports\`: kết quả phân tích, timeline và các bảng CSV/JSON.
- `08_Report\Muc_luc_bao_cao.md`: mục lục báo cáo.
- `08_Report\Bien_ban_ban_giao.md`: biên bản bàn giao.
- `08_Report\case_snapshot.json`: snapshot có cấu trúc.
- `05_Autopsy_Case\`: gói xuất để đưa dữ liệu vào Autopsy; đây không phải native Autopsy case database.

## 6. Lưu ý về chứng cứ và quyền riêng tư

- Công cụ phục vụ triage và phân tích sơ bộ. Xác minh phát hiện với artifact gốc và ghi nhận thao tác của điều tra viên.
- Khôi phục tin nhắn và nhận diện ứng viên đã xóa dựa trên dấu vết cục bộ/heuristic; không khẳng định trạng thái xóa chỉ từ nhãn tự động.
- Collector có thể sao chép cơ sở dữ liệu cookie hoặc dữ liệu phiên. Hạn chế quyền truy cập case, mã hóa nơi lưu trữ phù hợp và không chia sẻ ngoài phạm vi được phép.
- Hash trong manifest giúp kiểm tra bản sao sau thu thập; không tự nó chứng minh toàn bộ chuỗi bảo quản hoặc tính nhất quán snapshot của nguồn đang chạy.
- Discord là adapter chính. Zalo mới là placeholder; Firefox chưa nằm trong pipeline đang hoạt động.

## 7. License

Kiểm tra trạng thái hoặc kích hoạt:

```powershell
.\fdctl.cmd license status
.\fdctl.cmd license activate --prompt
```

Bản public dùng trial 3 ngày cho Gmail đầu tiên trên thiết bị và hỗ trợ license ký cho `issued_7d`, `issued_30d`, `issued_365d`. Khi cấp license, chỉ dùng private source workspace và giữ khóa ký ngoài bundle công khai.

Hiển thị fingerprint máy để yêu cầu license:

```powershell
.\fdctl.cmd license machine
```

## 8. Phát triển và đóng gói

Cài package trong source workspace:

```powershell
git clone https://github.com/Azynora/Forensic-Tools.git
cd Forensic-Tools
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
.\fdctl.cmd --help
```

Build bundle nội bộ:

```powershell
powershell -ExecutionPolicy Bypass -File .\build-package.ps1
```

Đầu ra hiện được cấu hình tại `dist\FORENSICS_DISCORD`, `dist\github-release` và `dist\FORENSICS_DISCORD_portable.zip`. Script build xóa các đầu ra cùng tên trước khi tạo lại; sao lưu hoặc kiểm tra chúng trước khi build.

### Đưa source và bản tải lên GitHub

- Commit mã nguồn trong `backend`, launcher, script build, `requirements*.txt`, README và tài liệu pháp lý/vận hành cần thiết.
- Không commit `.venv`, `build`, `dist`, `_runtime`, `workspace`, file case, license khách hàng, khóa riêng hoặc chứng thư ký. Các thư mục sinh ra đã được loại khỏi Git bằng `.gitignore`.
- Tạo ZIP bằng script build, sau đó đính kèm `dist\FORENSICS_DISCORD_portable.zip` vào GitHub Release. README tải từ trang Releases; không commit ZIP/EXE vào lịch sử source.
- Khi source repo public, người dùng có thể đọc và clone mã nguồn. Bản đóng gói không che giấu source đã public.

Bundle executable không chứa trực tiếp các file nguồn Python, nhưng không thể bảo đảm tuyệt đối chống trích xuất hoặc phân tích ngược. Muốn giữ kín tuyệt đối một phần logic thì không phân phối phần đó cho máy người dùng.
