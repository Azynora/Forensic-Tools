# Forensics Suite — Hướng dẫn nhanh

## Cài bản GUI

1. Tải `ForensicsSuite_Setup.exe` từ [GitHub Releases](https://github.com/Azynora/Forensic-Tools/releases/latest).
2. Chạy bộ cài; mở Forensics Suite từ Start Menu.
3. Chọn ngôn ngữ và workspace. Mặc định case được lưu trong `Documents\Forensics Suite`.
4. Mở **Demo dữ liệu** để xem case mẫu. Demo luôn có dữ liệu tổng hợp và không truy cập máy.

Discord là adapter duy nhất hiện có. Zalo, Telegram, WhatsApp, Messenger và Signal đang phát triển; ứng dụng sẽ báo trạng thái rồi quay lại Discord nếu chọn mục chưa hỗ trợ.

## Chạy source qua CLI

Yêu cầu Windows 11 và Python 3.10 trở lên:

```powershell
git clone https://github.com/Azynora/Forensic-Tools.git
cd Forensic-Tools
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
.\fdctl.cmd menu
```

Các lệnh thường dùng:

```powershell
.\fdctl.cmd apps detect
.\fdctl.cmd case create --app discord --id case_001
.\fdctl.cmd collect --case case_001
.\fdctl.cmd analyze --case case_001
.\fdctl.cmd report build --case case_001
.\fdctl.cmd case save --case case_001
```

Đổi workspace cho phiên PowerShell hiện tại:

```powershell
$env:FDCTL_DATA_ROOT = "E:\DFIR_CASES"
.\fdctl.cmd menu
```

## License

- Demo tổng hợp có sẵn, không cần license; nội dung chỉ để xem minh họa.
- Thu thập thật yêu cầu license có quyền collection, ký số và gắn với fingerprint thiết bị.
- Gửi Gmail và mã thiết bị từ trang License cho chủ dự án để yêu cầu cấp key. Hiện không có thanh toán hoặc cấp key tự động.
- License đang được lưu tại `%LOCALAPPDATA%\FORENSICS_DISCORD\license` để tương thích với các key đã cấp trước khi đổi tên giao diện.

## Build bộ cài

Cần Python trên máy build và Inno Setup 6:

```powershell
powershell -ExecutionPolicy Bypass -File .\build-package.ps1
```

Đầu ra gồm `dist\ForensicsSuite_portable.zip`, thư mục `dist\github-release` và `ForensicsSuite_Setup.exe`. Private Ed25519 signing key phải ở ngoài repo và không được đưa vào máy khách hoặc gói phát hành.

**Chủ sở hữu:** Truong Trieu Vy · [trieuvy9198@gmail.com](mailto:trieuvy9198@gmail.com)
