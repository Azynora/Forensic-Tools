# Forensics Suite — Tiếng Việt

Nền tảng Windows có thể mở rộng để điều tra số trên nhiều ứng dụng nhắn tin.

[English](README.en.md) · [Trang chính](README.md)

## Tải ứng dụng

[Tải bản cài hoặc ZIP portable mới nhất tại GitHub Releases](https://github.com/Azynora/Forensic-Tools/releases/latest).

Chạy `ForensicsSuite_Setup.exe`, sau đó mở Forensics Suite từ Start Menu. Python và thư viện cần thiết đã được đóng gói.

## Chạy từ source

```powershell
git clone https://github.com/Azynora/Forensic-Tools.git
cd Forensic-Tools
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
.\fdctl.cmd menu
```

Source mở menu CLI. Bộ cài GUI dành cho người muốn dùng ứng dụng desktop trên Windows.

## Ứng dụng và demo

- Discord hiện hỗ trợ thu thập, phân tích, báo cáo case và xuất dữ liệu cho Autopsy.
- Zalo, Telegram, WhatsApp, Messenger và Signal đang nằm trong lộ trình. Chọn ứng dụng chưa hỗ trợ sẽ hiện thông báo rồi quay lại Discord.
- Trang Demo có sẵn một hồ sơ hư cấu với timeline, tài khoản, tệp minh họa và tóm tắt báo cáo. Toàn bộ dữ liệu đều tổng hợp; demo không đọc dữ liệu người dùng và không tạo chứng cứ.
- Chọn nơi lưu workspace trong Cài đặt. Mặc định là `Documents\Forensics Suite`.

Dự án do một cá nhân duy trì. Quyền thu thập đầy đủ dùng license ký số gắn với thiết bị và được chủ dự án cấp thủ công; không có cửa hàng online hay backend thanh toán.

## Bản quyền và dữ liệu

Mã nguồn và bản phát hành thuộc chủ dự án. Dữ liệu case có thể chứa thông tin phiên nhạy cảm; chỉ sử dụng khi được ủy quyền và bảo vệ thư mục workspace.

**Chủ sở hữu:** Truong Trieu Vy · [trieuvy9198@gmail.com](mailto:trieuvy9198@gmail.com)
