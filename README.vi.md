# Forensics Suite — Tiếng Việt

[![Tác giả](https://img.shields.io/badge/Tác%20giả-Trương%20Triệu%20Vỹ-blue?style=for-the-badge)](mailto:trieuvy9198@gmail.com)
[![Bản quyền](https://img.shields.io/badge/Bản%20quyền-Độc%20quyền-red?style=for-the-badge)](LICENSE_PROPRIETARY.md)
[![Tiêu chuẩn](https://img.shields.io/badge/Tiêu%20chuẩn-ISO%2FIEC%2027037-orange?style=for-the-badge)](#bảo-toàn-chứng-cứ--tiêu-chuẩn-iso-27037)
[![Hệ điều hành](https://img.shields.io/badge/Nền%20tảng-Windows%2010%20%7C%2011-brightgreen?style=for-the-badge)](#)

> Nền tảng điều tra kỹ thuật số và ứng cứu sự cố (DFIR) cấp doanh nghiệp trên các ứng dụng nhắn tin cho hệ điều hành Windows.

```c
// When I wrote this code, only God and I understood what it did.
// Now, only God knows.
```

[English](README.en.md) · [Trang chủ](README.md) · [Hướng dẫn sử dụng](USAGE_GUIDE.md)

---

## ⚡ Tải Bản Thực Thi Nhanh (Dùng Ngay)

Bản phát hành chính thức đã được đóng gói sẵn toàn bộ môi trường và thư viện mã máy nhị phân, không cần cài đặt Python:

* 📦 **[Tải bản cài đặt Setup và bản nén ZIP tại GitHub Releases](https://github.com/Azynora/Forensic-Tools/releases/latest)**
  * `ForensicsSuite_Setup.exe` — Bộ cài đặt Windows với phím tắt Start Menu và desktop.
  * `ForensicsSuite_portable.zip` — Bản Portable cắm chạy trực tiếp trên USB hiện trường (100% offline, không cần cài đặt).

---

## 🛠️ Các Ứng Dụng Hỗ Trợ & Tính Năng Điều Tra

| Ứng dụng | Cấp độ hỗ trợ | Dữ liệu chứng cứ thu thập & phân tích |
| :--- | :--- | :--- |
| **Discord Desktop** | **Hoàn chỉnh (Full)** | Tin nhắn LevelDB, user token, localStorage, cache, GPUCache, đối chiếu lịch sử Chrome, snapshot socket TCP |
| **Telegram Desktop** | **Hoàn chỉnh (Full)** | Khóa phiên `tdata`, bản đồ hex, bộ nhớ đệm hình ảnh/voice/sticker `user_data`, socket kết nối Data Center |
| **Zalo** | *Lộ trình kế tiếp* | Đã định vị cấu trúc, nằm trong bản cập nhật kế tiếp |
| **WhatsApp / Signal** | *Lộ trình kế tiếp* | Module trích xuất cơ động đa nền tảng |

### Các Năng Lực Kỹ Thuật Nổi Bật:
* **Chuẩn bảo toàn chứng cứ ISO/IEC 27037:2012**: Thu thập trực tiếp trên RAM/Disk với nguyên tắc Zero-footprint, không làm ô nhiễm ổ đĩa máy đối tượng.
* **Chụp màn hình cửa sổ ứng dụng mục tiêu**: Tự động nhận diện và chỉ chụp cửa sổ Telegram/Discord, bảo vệ quyền riêng tư hình nền desktop của người dùng.
* **Bảng tổng hợp hình ảnh phục hồi (Carved Media Evidence Gallery)**: Tự động trích xuất các tệp hình ảnh từ bộ nhớ đệm mã hóa, tạo bảng danh mục ảnh kèm mã băm SHA-256 phục vụ đối chiếu chứng cứ.
* **Tương thích hoàn toàn với Autopsy**: Xuất hồ sơ vụ án và lược đồ CSV chuẩn hóa, sẵn sàng nạp trực tiếp vào phần mềm Autopsy trình trước tòa án.

---

## 💻 Chạy Từ Mã Nguồn (Giao Diện CLI Terminal)

Điều tra viên và lập trình viên có thể khởi chạy giao diện dòng lệnh tương tác từ mã nguồn:

```powershell
git clone https://github.com/Azynora/Forensic-Tools.git
cd Forensic-Tools
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

# Khởi chạy menu điều tra tương tác
.\fdctl.cmd menu

# Hoặc chạy lệnh điều tra trực tiếp:
# 1. Thu thập Telegram:
.\fdctl.cmd case create --app telegram --id case_tele_01
.\fdctl.cmd collect --case case_tele_01
.\fdctl.cmd report build --case case_tele_01

# 2. Thu thập Discord:
.\fdctl.cmd case create --app discord --id case_discord_01
.\fdctl.cmd collect --case case_discord_01
.\fdctl.cmd report build --case case_discord_01
```

> Chi tiết các lệnh và hướng dẫn từng bước: xem tại [📖 USAGE_GUIDE.md (Hướng dẫn sử dụng chi tiết)](USAGE_GUIDE.md).

*(Mã nguồn chạy giao diện CLI terminal. Bản ứng dụng Desktop GUI hoàn chỉnh được phân phối độc quyền qua mục GitHub Releases).*

---

## 🔑 Cơ Chế Cấp Phép & Bản Quyền

Forensics Suite ứng dụng chữ ký số mật mã bất đối xứng Ed25519 quân sự để quản lý bản quyền:

1. **Bản dùng thử (Trial 7 ngày)**: Đi kèm chế độ demo dữ liệu vụ án giả lập để trải nghiệm quy trình.
2. **Bản Portable USB Hiện trường (Khuyên dùng)**: Thả trực tiếp file `license.key` vào USB. Cắm chạy trên bất kỳ máy tính nghi phạm nào mà không bị khóa phần cứng hay đòi lại key.
3. **Bản Doanh nghiệp**: Ký số theo tên miền công ty kèm cơ chế đóng dấu Watermark danh tính pháp lý trên mọi báo cáo chứng cứ.

> **Liên hệ cấp bản quyền thương mại**:
> Liên hệ trực tiếp tác giả **Trương Triệu Vỹ**:
> * 📧 **Email**: [trieuvy9198@gmail.com](mailto:trieuvy9198@gmail.com)
> * 💬 **Telegram**: [@azynora](https://t.me/azynora)
> * 📱 **Zalo**: [0364.228.378](https://zalo.me/0364228378)
> * 🌐 **Facebook**: [facebook.com/azynora.vn](https://www.facebook.com/azynora.vn)

---

## ⚖️ Tuyên Bố Quyền Sở Hữu Trí Tuệ & Pháp Lý

Bản quyền (c) 2026 **Trương Triệu Vỹ** (`Truong Trieu Vy`). Mọi quyền được bảo lưu.

* **Chủ sở hữu & Tác giả duy nhất**: **Trương Triệu Vỹ** (`Truong Trieu Vy`)
* **Email liên hệ**: [trieuvy9198@gmail.com](mailto:trieuvy9198@gmail.com)
* **Telegram**: [@azynora](https://t.me/azynora)
* **Zalo**: [https://zalo.me/0364228378](https://zalo.me/0364228378)
* **Facebook**: [https://www.facebook.com/azynora.vn](https://www.facebook.com/azynora.vn)
* **Quy chế cấp phép**: [LICENSE_PROPRIETARY.md](LICENSE_PROPRIETARY.md)
* **Thỏa thuận người dùng**: [EULA.md](EULA.md) · [COPYRIGHT_NOTICE.md](COPYRIGHT_NOTICE.md)

*Phần mềm này là tài sản sở hữu trí tuệ độc quyền. Dữ liệu chứng cứ trích xuất chứa các thông tin phiên nhạy cảm. Chỉ sử dụng công cụ khi có thẩm quyền pháp lý hợp pháp và tuân thủ các quy định bảo mật dữ liệu hiện hành.*
