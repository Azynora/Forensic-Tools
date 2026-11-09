# FORENSIC_SUITE — Tiếng Việt

[![Tác giả](https://img.shields.io/badge/Tác%20giả-Trương%20Triệu%20Vỹ-blue?style=for-the-badge)](mailto:trieuvy9198@gmail.com)
[![Bản quyền](https://img.shields.io/badge/Bản%20quyền-Độc%20quyền-red?style=for-the-badge)](LICENSE_PROPRIETARY.md)
[![Định hướng kỹ thuật](https://img.shields.io/badge/Định%20hướng-ISO%2FIEC%2027037-blue?style=for-the-badge)](#)
[![Hệ điều hành](https://img.shields.io/badge/Nền%20tảng-Windows%20%7C%20Linux-brightgreen?style=for-the-badge)](#)

> Bộ công cụ phần mềm hỗ trợ nghiên cứu và điều tra kỹ thuật số (DFIR) trên các ứng dụng nhắn tin cho hệ điều hành Windows và Linux.

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
| **Discord Desktop** | **Hỗ trợ đầy đủ** | Tin nhắn LevelDB, user token, localStorage, cache, GPUCache, đối chiếu lịch sử Chrome, snapshot socket TCP |
| **Telegram Desktop** | **Hỗ trợ đầy đủ** | **Trích xuất RAM tiến trình sống (Live Memory Carving)**, khóa phiên `tdata`, bản đồ hex, bộ nhớ đệm media, đối chiếu Chrome, socket TCP |
| **Zalo** | *Lộ trình kế tiếp* | Đã định vị cấu trúc, nằm trong bản cập nhật kế tiếp |
| **WhatsApp / Signal** | *Lộ trình kế tiếp* | Module trích xuất cơ động đa nền tảng |

### Các Năng Lực Kỹ Thuật:
* **Tái Hiện Hiện Trường Điều Tra Trực Quan (Interactive Crime Scene Reconstruction)**: Mô phỏng không gian hiện trường giao tiếp thực tế của ứng dụng (Telegram, Discord, Zalo...) dưới dạng ứng dụng web HTML5 ngoại tuyến. Tích hợp thanh tua thời gian (Time-Machine Slider), bảng Thanh tra Giám định Bằng chứng (Forensic Inspector) chi tiết đến từng địa chỉ Offset RAM/Disk và mã băm SHA-256, danh bạ số điện thoại và thư viện media bóc tách từ hiện trường.
* **Cập Nhật Phần Mềm Liền Mạch (Bảo Toàn Bản Quyền)**: Hỗ trợ tự động cập nhật online 1-chạm qua GUI hoặc lệnh `fdctl update check`, cũng như cơ chế vá lỗi ngoại tuyến (`update-offline.cmd`) mà không làm thay đổi hoặc mất bản quyền `license.key` đã kích hoạt.
* **Khoanh vùng điều tra linh hoạt (Multi-Scope Investigation)**: Cho phép điều tra linh hoạt từ đoạn chat riêng 1-1 (--scope-type dm), kênh/nhóm (--scope-type group), hoặc truy vết theo UID/SĐT người dùng (--scope-type user), không ép buộc phải có link nhóm.
* **Định hướng theo nguyên tắc ISO/IEC 27037 & TCVN ISO/IEC 27037:2019**: Thiết kế quy trình thu thập dữ liệu hướng tới giảm thiểu can thiệp hệ thống (Zero-footprint), tính toán mã băm SHA-256 đối chiếu tính toàn vẹn của tệp sao chép.
* **Chụp màn hình cửa sổ ứng dụng mục tiêu**: Tự động nhận diện và chỉ chụp cửa sổ Telegram/Discord, bảo vệ quyền riêng tư hình nền desktop của người dùng.
* **Bảng tổng hợp hình ảnh phục hồi (Carved Media Gallery)**: Hỗ trợ trích xuất các tệp hình ảnh từ bộ nhớ đệm, tạo bảng danh mục ảnh kèm mã băm SHA-256 phục vụ rà soát đối chiếu.
* **Gói xuất dữ liệu định hướng tương thích Autopsy (Autopsy-compatible evidence export)**: Hỗ trợ xuất cấu trúc hồ sơ vụ án và lược đồ CSV chuẩn hóa, sẵn sàng nạp vào phần mềm Autopsy để phân tích chuyên sâu.

---

## 💻 Chạy Từ Mã Nguồn (Giao Diện CLI Terminal)

Điều tra viên và lập trình viên có thể khởi chạy giao diện dòng lệnh tương tác từ mã nguồn trên Windows hoặc Linux:

### 1. Trên Windows:
```powershell
git clone https://github.com/Azynora/Forensic-Tools.git
cd Forensic-Tools
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

# Khởi chạy menu điều tra tương tác
.\fdctl.cmd menu

# Hoặc chạy lệnh điều tra trực tiếp:
.\fdctl.cmd case create --app telegram --id case_tele_01
.\fdctl.cmd collect --case case_tele_01
.\fdctl.cmd report build --case case_tele_01
```

### 2. Trên Linux (Ubuntu, Debian, Fedora, Arch, Kali Linux):
```bash
git clone https://github.com/Azynora/Forensic-Tools.git
cd Forensic-Tools
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Cấp quyền thực thi và khởi chạy menu:
chmod +x fdctl fdctl.sh
./fdctl menu

# Hoặc chạy lệnh trực tiếp:
./fdctl apps detect
./fdctl case create --app discord --id case_discord_01
./fdctl collect --case case_discord_01
./fdctl report build --case case_discord_01
```

> Chi tiết các lệnh và hướng dẫn từng bước: xem tại [📖 USAGE_GUIDE.md (Hướng dẫn sử dụng chi tiết)](USAGE_GUIDE.md).

*(Mã nguồn chạy giao diện CLI terminal đa nền tảng. Bản ứng dụng Desktop GUI hoàn chỉnh được phân phối độc quyền qua mục GitHub Releases).*

---

## 🔑 Cơ Chế Cấp Phép & Bản Quyền

Forensics Suite ứng dụng chữ ký số mật mã bất đối xứng Ed25519 để quản lý bản quyền:

1. **Bản dùng thử (Trial 7 ngày)**: Đi kèm chế độ demo dữ liệu vụ án giả lập để trải nghiệm quy trình.
2. **Bản Portable USB Hiện trường (Khuyên dùng)**: Thả trực tiếp file `license.key` vào USB. Cắm chạy trên bất kỳ máy tính hiện trường nào mà không bị khóa phần cứng hay đòi lại key.
3. **Bản Doanh nghiệp**: Ký số theo tên miền công ty kèm cơ chế đóng dấu Watermark danh tính pháp lý trên mọi báo cáo chứng cứ.

> **Liên hệ cấp bản quyền**:
> Liên hệ trực tiếp tác giả **Trương Triệu Vỹ**:
> * 📧 **Email**: [trieuvy9198@gmail.com](mailto:trieuvy9198@gmail.com)
> * 💬 **Telegram**: [@azynora](https://t.me/azynora)
> * 🌐 **Facebook**: [facebook.com/azynora.vn](https://www.facebook.com/azynora.vn)

---

## ⚖️ Tuyên Bố Quyền Sở Hữu Trí Tuệ & Khuyến Cáo Pháp Lý

Bản quyền (c) 2026 **Trương Triệu Vỹ** (`Truong Trieu Vy`). Mọi quyền được bảo lưu.

* **Chủ sở hữu & Tác giả**: **Trương Triệu Vỹ** (`Truong Trieu Vy`)
* **Email liên hệ**: [trieuvy9198@gmail.com](mailto:trieuvy9198@gmail.com)
* **Telegram**: [@azynora](https://t.me/azynora)
* **Facebook**: [https://www.facebook.com/azynora.vn](https://www.facebook.com/azynora.vn)
* **Quy chế cấp phép**: [LICENSE_PROPRIETARY.md](LICENSE_PROPRIETARY.md)
* **Thỏa thuận người dùng**: [EULA.md](EULA.md) · [COPYRIGHT_NOTICE.md](COPYRIGHT_NOTICE.md)

> ⚠️ **Khuyến cáo Pháp lý & Giới hạn Trách nhiệm**:
> 1. Phần mềm được thiết kế và phát triển phục vụ mục đích nghiên cứu khoa học, giáo dục đào tạo, kiểm thử an toàn thông tin và hỗ trợ công tác phản ứng nhanh sự cố (DFIR) của các cá nhân, tổ chức có thẩm quyền.
> 2. Người sử dụng tự chịu hoàn toàn trách nhiệm pháp lý khi vận hành công cụ trên các hệ thống mục tiêu, bảo đảm tuân thủ nghiêm ngặt Luật An toàn thông tin mạng 2015, Luật An ninh mạng 2018 và Bộ luật Tố tụng Hình sự hiện hành của nước Cộng hòa Xã hội Chủ nghĩa Việt Nam.
> 3. Dự án không đưa ra bất kỳ cam kết hay tuyên bố mang tính tuyệt đối nào theo quy định của Luật Quảng cáo 2012. Mọi kết quả phân tích cần được đối chiếu chéo với các nguồn chứng cứ độc lập trước khi đưa vào kết luận pháp lý.
