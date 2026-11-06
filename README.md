// When I wrote this code, only God and I understood what it did.
// Now, only God knows....

# FORENSICS_DISCORD

**Bộ công cụ DFIR portable cho Windows 11**

Thu thập và rà soát artifact Discord trên máy Windows, tạo case, timeline, báo cáo và gói xuất để làm việc với Autopsy.

<div align="center">

[**⬇ Tải bản Windows (.zip)**](https://github.com/Azynora/Forensic-Tools/releases/latest)

**Windows 11 · CLI · Không cần cài Python để chạy bản phát hành**

</div>

[Tiếng Việt](./README.vi.md) · [English](./README.en.md)

## Bắt đầu

1. Tải file ZIP ở mục [Releases](https://github.com/Azynora/Forensic-Tools/releases/latest).
2. Giải nén vào thư mục có quyền ghi.
3. Mở `launch-analysis-terminal.cmd` để dùng menu, hoặc mở PowerShell và chạy:

```powershell
.\fdctl.cmd --help
```

## Chạy từ mã nguồn

Clone repo rồi xem [hướng dẫn CLI](./USAGE_GUIDE.md). Cài môi trường và chạy:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
.\fdctl.cmd --help
```

Repo public chứa mã nguồn để clone và đọc. Bản ZIP trong Releases giúp chạy nhanh nhưng không làm mã nguồn trong repo trở thành riêng tư. **Phiên bản: 1.1.9.**

## Tính năng

- Thu thập artifact Discord desktop, một số dữ liệu Chrome và live response.
- Phân tích dấu vết, lập timeline và tạo báo cáo case.
- Xuất gói dữ liệu sẵn sàng nhập/đối chiếu trong Autopsy.

> Đây là công cụ triage và phân tích sơ bộ. Kết quả tự động cần được xác minh với dữ liệu gốc. Gói Autopsy xuất ra không phải native Autopsy case. Chỉ thu thập dữ liệu khi được ủy quyền; artifact có thể chứa cookie hoặc dữ liệu phiên nhạy cảm.

## Phạm vi hỗ trợ

Discord là adapter chính. Zalo hiện là placeholder; Firefox chưa nằm trong pipeline. Bản phát hành là portable bundle gồm executable và runtime cần thiết. Đóng gói không thể bảo đảm tuyệt đối chống trích xuất hoặc phân tích ngược.
