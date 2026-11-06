# FORENSICS_DISCORD — Tiếng Việt

Công cụ DFIR dòng lệnh portable cho Windows 11, tập trung thu thập và rà soát artifact Discord cục bộ.

[English](./README.en.md) · [Trang chính](./README.md) · [Tải bản Windows (.zip)](https://github.com/Azynora/Forensic-Tools/releases/latest)

## Chạy bản tải về

1. Tải ZIP mới nhất từ [GitHub Releases](https://github.com/Azynora/Forensic-Tools/releases/latest).
2. Giải nén vào thư mục có quyền ghi.
3. Chạy `launch-analysis-terminal.cmd`, hoặc mở PowerShell tại thư mục đó:

```powershell
.\fdctl.cmd --help
.\fdctl.cmd apps detect
```

Không cần cài Python. Thu thập có thể yêu cầu quyền Administrator. Dữ liệu case mặc định lưu cạnh bundle trong `workspace`.

## Chạy từ source

Cài Python 3.10+, clone repo rồi chạy tại thư mục gốc:

```powershell
git clone https://github.com/Azynora/Forensic-Tools.git
cd Forensic-Tools
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
.\fdctl.cmd --help
```

Repository public có mã nguồn để xem và clone. ZIP trong Releases chỉ là bản chạy portable, không ẩn mã nguồn đang được public. **Phiên bản: 1.1.9.**

Hướng dẫn các lệnh điều tra nằm trong [USAGE_GUIDE.md](./USAGE_GUIDE.md).

## Tạo case và báo cáo

```powershell
.\fdctl.cmd case create --app discord --id case_001
.\fdctl.cmd collect --case case_001
.\fdctl.cmd analyze --case case_001
.\fdctl.cmd report build --case case_001
.\fdctl.cmd case save --case case_001
```

## Phạm vi và lưu ý

Discord là adapter chính; Zalo là placeholder và Firefox chưa được hỗ trợ trong pipeline. Công cụ phục vụ triage, kết quả khôi phục cần được xác minh với dữ liệu gốc. Artifact có thể chứa cookie/dữ liệu phiên, hãy bảo vệ case và chỉ thu thập trong phạm vi được ủy quyền.

Executable được phân phối trong portable bundle kèm runtime. Đóng gói không thể bảo đảm tuyệt đối chống trích xuất hoặc phân tích ngược.
