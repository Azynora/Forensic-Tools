# FORENSICS_DISCORD — Hướng dẫn nhanh

## Bản cài đặt GUI

1. Tải `FORENSICS_DISCORD_Setup.exe` từ [GitHub Releases](https://github.com/Azynora/Forensic-Tools/releases/latest).
2. Cài đặt theo người dùng hiện tại, mở app từ Start Menu.
3. Chọn ngôn ngữ, workspace và kích hoạt license trong giao diện.

Python và thư viện được đóng gói trong installer. Case mặc định nằm dưới `Documents\FORENSICS_DISCORD`; có thể đổi nơi lưu trong Cài đặt. Thu thập có thể yêu cầu quyền Administrator.

Trial cục bộ 7 ngày chỉ cho phép xem demo tổng hợp `SAMPLE`. Demo không đọc Discord/Chrome thật, không tạo chứng cứ. License trả phí mở chức năng forensic.

## Source CLI

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

Chọn Zalo trong menu sẽ báo đang phát triển rồi quay lại lựa chọn ứng dụng. Không có luồng thu thập Zalo.

Đổi workspace trong một phiên PowerShell:

```powershell
$env:FDCTL_DATA_ROOT = "E:\DFIR_CASES"
.\fdctl.cmd menu
```

## License

- App tự bắt đầu trial 7 ngày cho email Gmail đầu tiên trên thiết bị; trial chỉ mở demo SAMPLE.
- Để yêu cầu key trả phí, gửi email và mã thiết bị ở trang License cho chủ dự án. Chủ dự án xác nhận rồi cấp signed key gắn với fingerprint thiết bị.
- Kích hoạt bằng email Gmail và key trong trang License. Không có thanh toán hoặc cấp key tự động trong app.
- License lưu tại `%LOCALAPPDATA%\FORENSICS_DISCORD\license`; token được xác minh bằng public key tích hợp trong app.
- License Ed25519 cũ được chấp nhận trong giai đoạn chuyển đổi.

## Cấp license thủ công và build Setup

Giữ private signing key ngoài repo, máy khách và gói phát hành. Người dùng gửi fingerprint qua app; trên máy nguồn riêng, dùng `fdctl.cmd license issue` với email, loại license và fingerprint đó. Trả file key cho người dùng qua email. Trial được cấp cục bộ, không cần private key.

Cần Python trên máy build và Inno Setup 6 để tạo bộ cài:

```powershell
powershell -ExecutionPolicy Bypass -File .\build-package.ps1
```

Đầu ra: `dist\FORENSICS_DISCORD_portable.zip`, thư mục `dist\github-release` và, khi có Inno Setup 6, `FORENSICS_DISCORD_Setup.exe`. Build cần private Ed25519 key ngoài repo để ký manifest integrity. Không commit khóa, dữ liệu case hoặc các thư mục `build`, `dist`, `workspace`, `.venv`.

## Lưu ý

Chỉ thu thập dữ liệu khi được ủy quyền. Case có thể chứa cookie và dữ liệu phiên. Kết quả là triage tự động và cần được xác minh với artifact gốc. Public source vẫn có thể được đọc; đóng gói EXE không thể bảo đảm tuyệt đối chống trích xuất/phân tích ngược.

**Chủ sở hữu:** Truong Trieu Vy · [trieuvy9198@gmail.com](mailto:trieuvy9198@gmail.com)
