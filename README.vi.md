# FORENSICS_DISCORD — Tiếng Việt

Ứng dụng Windows hỗ trợ thu thập, phân tích và lập báo cáo forensic Discord.

[English](README.en.md) · [Trang chính](README.md)

## Tải và cài đặt

[Tải Setup.exe hoặc ZIP mới nhất tại GitHub Releases](https://github.com/Azynora/Forensic-Tools/releases/latest).

Chạy `FORENSICS_DISCORD_Setup.exe`, sau đó mở ứng dụng từ Start Menu. Python và thư viện đã được đóng gói sẵn; không cần cài Python hoặc chạy pip.

## Chạy từ mã nguồn bằng CLI

```powershell
git clone https://github.com/Azynora/Forensic-Tools.git
cd Forensic-Tools
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
.\fdctl.cmd menu
```

Source mở menu terminal. Xem [USAGE_GUIDE.md](USAGE_GUIDE.md) để biết các lệnh CLI.

## Tính năng

- Thu thập artifact Discord, phân tích, tạo báo cáo và xuất dữ liệu cho Autopsy.
- Demo dữ liệu tổng hợp có nhãn `SAMPLE`, không đọc dữ liệu Discord hoặc Chrome thật.
- Zalo đang phát triển; nếu chọn Zalo, ứng dụng sẽ quay lại lựa chọn Discord.
- Có thể chọn workspace trong phần Cài đặt; mặc định là Documents.

Trial cục bộ 7 ngày chỉ mở demo tổng hợp. License trả phí dùng key có chữ ký, gắn với thiết bị và do chủ dự án cấp thủ công. Dự án cá nhân này không dùng cửa hàng online hoặc backend thanh toán.

## Mã nguồn và dữ liệu

Repo public có mã nguồn. Bộ cài đóng gói Python/runtime để dễ chạy, nhưng không thể đảm bảo tuyệt đối chống phân tích ngược. Chỉ sử dụng khi được ủy quyền; dữ liệu case có thể chứa thông tin phiên nhạy cảm.

**Chủ sở hữu:** Truong Trieu Vy · [trieuvy9198@gmail.com](mailto:trieuvy9198@gmail.com)

**Phiên bản:** 1.2.0
