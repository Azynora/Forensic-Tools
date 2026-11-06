"""Modern, high-DPI aware, feature-complete GUI for Forensics Suite."""

from __future__ import annotations

import io
import json
import sys
import threading
import urllib.parse
import webbrowser
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from fdctl import __contact__, __release__
from fdctl.app_catalog import APP_CATALOG, app_label, get_app
from fdctl.paths import project_root, workspace_root
from fdctl.services.license_service import (
    OWNER_EMAIL,
    OWNER_NAME,
    activate_license_token,
    current_license_status,
    format_machine_name,
    machine_fingerprint,
    require_active_license,
    support_root,
)
from fdctl.utils import is_admin, rerun_as_admin


PRODUCT_NAME = "Forensics Suite"


def _enable_high_dpi() -> None:
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                import ctypes
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass


COLORS = {
    "navy": "#0B132B",
    "navy_hover": "#1C2541",
    "navy_active": "#243254",
    "accent_blue": "#2563EB",
    "blue_hover": "#1D4ED8",
    "canvas": "#F4F6F9",
    "white": "#FFFFFF",
    "ink": "#0F172A",
    "ink_secondary": "#334155",
    "muted": "#64748B",
    "line": "#E2E8F0",
    "green": "#059669",
    "green_bg": "#ECFDF5",
    "amber": "#D97706",
    "amber_bg": "#FFFBEB",
    "blue_pill": "#1D4ED8",
    "blue_pill_bg": "#EFF6FF",
    "red": "#DC2626",
    "red_bg": "#FEF2F2",
}

TEXT = {
    "vi": {
        "window": "Forensics Suite | Nền tảng Điều tra Pháp chứng Số",
        "brand_title": "FORENSICS SUITE",
        "brand_subtitle": "ĐIỀU TRA PHÁP CHỨNG SỐ",
        "nav": [
            "◈  Tổng quan",
            "◬  Demo dữ liệu",
            "▤  Cases & Báo cáo",
            "🔒  Bản quyền",
            "⚙  Cài đặt",
            "ℹ  Trợ giúp",
        ],
        "page_titles": [
            "Tổng quan Điều tra",
            "Trải nghiệm Dữ liệu Mẫu (Demo)",
            "Quản lý Hồ sơ & Báo cáo (Cases)",
            "Quản lý Bản quyền & Thiết bị",
            "Cài đặt & Môi trường làm việc",
            "Trợ giúp & Thông tin Bản quyền",
        ],
        "page_subtitles": [
            "Không gian làm việc tập trung để thu thập, phân tích và xuất báo cáo pháp chứng số.",
            "Khám phá các tính năng bằng kịch bản diễn tập giả lập có sẵn — không đọc dữ liệu thật trên máy.",
            "Duyệt danh sách các hồ sơ điều tra đã lưu, mở báo cáo HTML và xuất gói Autopsy.",
            "Kích hoạt và quản lý giấy phép bản quyền gắn với thiết bị phần cứng này.",
            "Tùy chỉnh thư mục lưu trữ workspace, ngôn ngữ giao diện và kiểm tra quyền quản trị.",
            "Hướng dẫn quy trình 4 bước điều tra pháp chứng, phím tắt CLI và thông tin tác giả.",
        ],
        "hero_title": "Digital Forensics & Incident Response",
        "hero_subtitle": "Bộ công cụ dòng lệnh và giao diện hợp nhất phục vụ điều tra dấu vết số trên Windows.",
        "quick_actions": "Thao tác Nhanh",
        "scope_title": "Thiết lập Phạm vi Điều tra Mới",
        "choose_app": "Ứng dụng mục tiêu:",
        "channel_url": "Liên kết Kênh / Nhóm (Channel URL):",
        "channel_url_hint": "Ví dụ: https://discord.com/channels/... (tùy chọn)",
        "target_user": "Đối tượng / Người dùng mục tiêu:",
        "target_user_hint": "Tên người dùng hoặc ID cần khoanh vùng (tùy chọn)",
        "app_supported": "● ĐÃ HỖ TRỢ",
        "app_planned": "◷ ĐANG PHÁT TRIỂN",
        "start": "Bắt đầu điều tra",
        "explore_demo": "Khám phá Demo",
        "supported_now": "Ứng dụng sẵn sàng",
        "planned_apps": "Ứng dụng lộ trình",
        "workspace": "Thư mục Workspace",
        "current_license": "Quyền sử dụng",
        "open_workspace": "Mở Workspace",
        "scan_apps": "Quét ứng dụng",
        "catalog_title": "Danh mục Ứng dụng & Lộ trình Tích hợp",
        "live_log_title": "Tiến trình Điều tra & Nhật ký Trực tiếp",
        "demo_title": "Dữ liệu Mẫu (Sample Walkthrough)",
        "demo_subtitle": "Hồ sơ tabletop mô phỏng hoàn chỉnh — hoàn toàn an toàn, không đọc Discord hay Zalo thật.",
        "sample_badge": "DỮ LIỆU MÔ PHỎNG · SAMPLE ONLY",
        "sample_case": "Hồ sơ Diễn tập Mẫu",
        "sample_case_name": "Tabletop Response Exercise",
        "sample_case_id": "CASE-SAMPLE-0142",
        "sample_scope": "Kênh #ops-tabletop · 08:15–09:05 · 12/05/2026",
        "metric_messages": "Tin nhắn mẫu",
        "metric_participants": "Tài khoản giả lập",
        "metric_files": "Tệp minh họa",
        "metric_events": "Sự kiện timeline",
        "timeline": "Timeline Hội thoại & Tương tác",
        "search_filter": "Tìm kiếm nhanh:",
        "time": "Thời gian",
        "participant": "Tài khoản",
        "message": "Nội dung thông điệp mô phỏng",
        "channel": "Kênh",
        "artifacts": "Tệp Dữ liệu Đính kèm",
        "file_name": "Tên tệp",
        "file_type": "Định dạng",
        "file_note": "Mục đích sử dụng",
        "report_preview": "Tóm tắt Kết luận Hồ sơ",
        "report_text": "Kịch bản tabletop hư cấu. Mọi tài khoản, thông điệp và tệp chỉ phục vụ minh họa tính năng; không phải người dùng hay bằng chứng thực tế.",
        "open_sample_report": "Xem Tóm tắt Báo cáo Mẫu",
        "demo_notice": "LƯU Ý: Chế độ Demo sử dụng dữ liệu tổng hợp cố định. Công cụ không đọc Discord, Zalo, trình duyệt hay tệp cá nhân trên máy.",
        "cases": "Danh sách Hồ sơ Điều tra (Cases)",
        "case_folder": "Vị trí lưu trữ:",
        "recent_cases": "Các hồ sơ đã lưu trong Workspace",
        "no_cases": "Trống",
        "open_folder": "Mở Thư mục Case",
        "open_report": "Xem Báo cáo (Report)",
        "open_autopsy": "Gói Autopsy",
        "refresh_cases": "Làm mới danh sách",
        "case_details_title": "Chi tiết Hồ sơ Được chọn",
        "license": "Bản quyền & Giấy phép",
        "license_state": "Trạng thái Quyền hạn",
        "email": "Địa chỉ Gmail đăng ký:",
        "key": "Mã kích hoạt (License Key):",
        "activate": "Kích hoạt Bản quyền",
        "trial": "Bắt đầu Dùng thử 7 Ngày (Demo)",
        "request_key": "Gửi Yêu cầu Cấp License",
        "device": "Mã định danh Thiết bị (Hardware Fingerprint):",
        "copy_device": "Sao chép Mã máy",
        "copied": "✓ Đã sao chép vào bộ nhớ tạm!",
        "owner": f"Chủ sở hữu & Bản quyền: {OWNER_NAME} ({OWNER_EMAIL})",
        "settings": "Cài đặt & Môi trường",
        "workspace_path": "Thư mục lưu trữ Hồ sơ và Báo cáo:",
        "browse": "Chọn thư mục…",
        "reset_workspace": "Đặt lại Mặc định",
        "save": "Lưu Cài đặt",
        "language": "Ngôn ngữ Giao diện:",
        "admin_status": "Quyền thực thi Quản trị viên (Administrator):",
        "admin_yes": "Đang chạy với quyền Administrator (Tối ưu để trích xuất file đang mở)",
        "admin_no": "Đang chạy với quyền người dùng thông thường (Có thể bị hạn chế quyền truy cập)",
        "relaunch_admin": "Khởi động lại với quyền Admin",
        "help": "Trợ giúp & Tài liệu",
        "about_text": "Forensics Suite là giải pháp điều tra pháp chứng số mở rộng, hỗ trợ thu thập dấu vết, phục hồi tin nhắn cache, kiểm tra cookie/session và xuất báo cáo chuẩn Autopsy.",
        "cli_title": "Sử dụng Dòng lệnh (CLI Suite)",
        "cli_help": "Dành cho kỹ thuật viên điều tra nhanh. Bạn có thể mở Terminal và chạy lệnh sau:",
        "version": f"Phiên bản phát hành: {__release__}",
        "ready": "Sẵn sàng làm việc",
        "run": "Đang thực hiện quy trình điều tra...",
        "done": "Quy trình điều tra đã hoàn tất thành công!",
        "admin_req": "Thu thập artifact yêu cầu quyền Administrator. Ứng dụng sẽ yêu cầu mở lại với quyền phù hợp.",
        "unsupported_title": "Ứng dụng Đang trong Giai đoạn Phát triển",
        "unsupported": "Ứng dụng này nằm trong lộ trình phát triển. Hiện tại quy trình thu thập chuyên sâu chưa sẵn sàng. Bạn có thể chọn Discord để thực hiện điều tra ngay.",
        "need_license": "Cần kích hoạt bản quyền hợp lệ để bắt đầu điều tra dữ liệu thực tế.",
        "confirm_start": "Bắt đầu quy trình thu thập và phân tích trên thiết bị này? Bạn cần đảm bảo có thẩm quyền điều tra đối với các dữ liệu này.",
        "saved": "Đã lưu cài đặt thành công.",
        "activated": "Kích hoạt bản quyền thành công!",
        "missing_email": "Vui lòng nhập địa chỉ Gmail đăng ký trước.",
        "license_request_subject": "Yêu cầu cấp License - Forensics Suite",
    },
    "en": {
        "window": "Forensics Suite | Digital Forensics Platform",
        "brand_title": "FORENSICS SUITE",
        "brand_subtitle": "DIGITAL FORENSICS PLATFORM",
        "nav": [
            "◈  Overview",
            "◬  Data Demo",
            "▤  Cases & Reports",
            "🔒  License",
            "⚙  Settings",
            "ℹ  Help",
        ],
        "page_titles": [
            "Investigation Overview",
            "Synthetic Data Demo (Sample)",
            "Cases & Reports Browser",
            "License & Device Management",
            "Settings & Environment",
            "Help & Licensing Information",
        ],
        "page_subtitles": [
            "Unified digital forensics workspace for artifact collection, analysis, and reporting.",
            "Explore capabilities with an integrated tabletop sample case — no real computer data accessed.",
            "Browse saved forensic cases, launch interactive HTML reports, and inspect Autopsy bundles.",
            "Activate and manage hardware-bound entitlements for this investigation machine.",
            "Configure workspace directories, language preferences, and administrative permissions.",
            "Four-stage DFIR methodology, CLI command references, and ownership details.",
        ],
        "hero_title": "Digital Forensics & Incident Response",
        "hero_subtitle": "Unified Windows forensic suite combining CLI automation and modern interactive desktop GUI.",
        "quick_actions": "Quick Actions",
        "scope_title": "New Investigation Scope",
        "choose_app": "Target Application:",
        "channel_url": "Channel / Group URL:",
        "channel_url_hint": "e.g. https://discord.com/channels/... (optional)",
        "target_user": "Target Account / User ID:",
        "target_user_hint": "Username or ID to prioritize (optional)",
        "app_supported": "● SUPPORTED",
        "app_planned": "◷ IN DEVELOPMENT",
        "start": "Start Investigation",
        "explore_demo": "Explore Demo",
        "supported_now": "Available Apps",
        "planned_apps": "Roadmap Apps",
        "workspace": "Workspace Folder",
        "current_license": "Access Status",
        "open_workspace": "Open Workspace",
        "scan_apps": "Detect Apps",
        "catalog_title": "Application Catalog & Roadmap",
        "live_log_title": "Live Investigation Activity & Logs",
        "demo_title": "Synthetic Data Walkthrough",
        "demo_subtitle": "Fictional tabletop exercise scenario — strictly safe, no live application data read.",
        "sample_badge": "SYNTHETIC DATA · SAMPLE ONLY",
        "sample_case": "Sample Investigation Case",
        "sample_case_name": "Tabletop Response Exercise",
        "sample_case_id": "CASE-SAMPLE-0142",
        "sample_scope": "Channel #ops-tabletop · 08:15–09:05 · May 12, 2026",
        "metric_messages": "Sample messages",
        "metric_participants": "Synthetic accounts",
        "metric_files": "Illustrative files",
        "metric_events": "Timeline events",
        "timeline": "Conversation Timeline & Events",
        "search_filter": "Search filter:",
        "time": "Time",
        "participant": "Account",
        "message": "Simulated Message Content",
        "channel": "Channel",
        "artifacts": "Illustrative Artifacts",
        "file_name": "File Name",
        "file_type": "Format",
        "file_note": "Purpose",
        "report_preview": "Investigation Findings Summary",
        "report_text": "Fictional tabletop exercise. Accounts, messages, and files are synthetic illustrations; they are not real users or forensic evidence.",
        "open_sample_report": "View Sample Findings",
        "demo_notice": "NOTICE: Demo mode uses fixed synthetic content. It does not read Discord, Zalo, browsers, or personal files.",
        "cases": "Investigation Cases & Reports",
        "case_folder": "Storage location:",
        "recent_cases": "Saved Cases in Workspace",
        "no_cases": "Empty",
        "open_folder": "Open Case Folder",
        "open_report": "Open Report",
        "open_autopsy": "Autopsy Bundle",
        "refresh_cases": "Refresh List",
        "case_details_title": "Selected Case Details",
        "license": "License & Hardware",
        "license_state": "Entitlement Status",
        "email": "Registered Gmail Address:",
        "key": "License Key:",
        "activate": "Activate License",
        "trial": "Start 7-Day Demo Trial",
        "request_key": "Request Signed License",
        "device": "Hardware Fingerprint:",
        "copy_device": "Copy Machine ID",
        "copied": "✓ Copied to clipboard!",
        "owner": f"Author & Ownership: {OWNER_NAME} ({OWNER_EMAIL})",
        "settings": "Settings & Environment",
        "workspace_path": "Case & Report Storage Root:",
        "browse": "Browse…",
        "reset_workspace": "Reset to Default",
        "save": "Save Settings",
        "language": "Interface Language:",
        "admin_status": "Administrator Execution Privilege:",
        "admin_yes": "Running with Administrator privilege (Recommended for live file locks)",
        "admin_no": "Running as Standard User (Certain file locks may require elevation)",
        "relaunch_admin": "Relaunch as Admin",
        "help": "Help & Documentation",
        "about_text": "Forensics Suite is an extensible digital investigation platform designed for artifact triage, cache message reconstruction, session verification, and Autopsy package generation.",
        "cli_title": "Command-Line Interface (CLI)",
        "cli_help": "Designed for fast automated terminal workflows. Run the following command in terminal:",
        "version": f"Release Version: {__release__}",
        "ready": "Ready for investigation",
        "run": "Running forensic workflow...",
        "done": "Investigation workflow completed successfully!",
        "admin_req": "Evidence collection requires Administrator privilege. The app will relaunch elevated.",
        "unsupported_title": "Application Under Development",
        "unsupported": "This application integration is currently on the product roadmap. Deep parsing is not yet active. Please select Discord to proceed.",
        "need_license": "An active license with collection entitlements is required.",
        "confirm_start": "Start artifact collection on this device? Ensure you have authorization to acquire this evidence.",
        "saved": "Settings saved successfully.",
        "activated": "License activated successfully!",
        "missing_email": "Please enter your Gmail address first.",
        "license_request_subject": "License Request - Forensics Suite",
    },
}

DEMO_MESSAGES = [
    ("08:15:04", "analyst_sample", "#ops-tabletop", "Exercise begins. All events are simulated."),
    ("08:18:27", "responder_mock", "#ops-tabletop", "Mock alert received; no live systems involved."),
    ("08:24:10", "observer_demo", "#ops-tabletop", "Checkpoint saved to sample-note.txt."),
    ("08:31:52", "analyst_sample", "#ops-tabletop", "Review the sample attachment only."),
    ("08:37:16", "responder_mock", "#ops-tabletop", "sample-map.png is a demo placeholder."),
    ("08:46:39", "observer_demo", "#ops-tabletop", "Simulated handoff complete."),
    ("08:57:03", "analyst_sample", "#ops-tabletop", "Exercise closed; no real data accessed."),
]

DEMO_FILES = [
    ("sample-note.txt", "Text/Log", "Incident checklist"),
    ("sample-map.png", "Image/PNG", "Mock topology"),
]


def _settings_path() -> Path:
    return support_root() / "settings.json"


def _load_settings() -> dict:
    try:
        return json.loads(_settings_path().read_text(encoding="utf-8"))
    except Exception:
        return {}


class ForensicsApp(tk.Tk):
    def __init__(self, elevated_launch: bool = False) -> None:
        _enable_high_dpi()
        super().__init__()
        self.elevated_launch = elevated_launch
        self.settings = _load_settings()
        self.lang = str(self.settings.get("language", "vi")).lower()
        if self.lang not in TEXT:
            self.lang = "vi"
        self.current_page = 0
        self.selected_app_id = "discord"

        self.email_var = tk.StringVar(value=str(self.settings.get("licenseEmail", "")))
        self.key_var = tk.StringVar()
        self.workspace_var = tk.StringVar(value=str(self.settings.get("workspace", workspace_root())))
        self.channel_url_var = tk.StringVar()
        self.target_user_var = tk.StringVar()
        self.selected_app_var = tk.StringVar()
        self.license_badge_var = tk.StringVar()
        self.status_var = tk.StringVar(value=TEXT[self.lang]["ready"])
        self.device_copied_var = tk.StringVar()
        self.filter_var = tk.StringVar()

        self.progress: ttk.Progressbar | None = None
        self.nav_buttons: list[tk.Button] = []

        self._configure_style()
        self._build_shell()
        self.show_page(0)

    def _configure_style(self) -> None:
        self.title(TEXT[self.lang]["window"])
        self.geometry("1220x820")
        self.minsize(1050, 700)
        self.configure(background=COLORS["canvas"])

        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        base_font = ("Segoe UI", 10)
        bold_font = ("Segoe UI", 10, "bold")

        style.configure("TFrame", background=COLORS["canvas"])
        style.configure("Canvas.TFrame", background=COLORS["canvas"])
        style.configure("Card.TFrame", background=COLORS["white"])
        style.configure("Sidebar.TFrame", background=COLORS["navy"])

        style.configure("TLabel", background=COLORS["canvas"], foreground=COLORS["ink"], font=base_font)
        style.configure("Card.TLabel", background=COLORS["white"], foreground=COLORS["ink"], font=base_font)
        style.configure("Sidebar.TLabel", background=COLORS["navy"], foreground="#94A3B8", font=("Segoe UI", 9))
        style.configure("Brand.TLabel", background=COLORS["navy"], foreground=COLORS["white"], font=("Segoe UI", 16, "bold"))
        style.configure("BrandSub.TLabel", background=COLORS["navy"], foreground="#64748B", font=("Segoe UI", 8, "bold"))
        style.configure("PageTitle.TLabel", background=COLORS["canvas"], foreground=COLORS["ink"], font=("Segoe UI", 20, "bold"))
        style.configure("SectionTitle.TLabel", background=COLORS["white"], foreground=COLORS["ink"], font=("Segoe UI", 12, "bold"))
        style.configure("Muted.TLabel", background=COLORS["white"], foreground=COLORS["muted"], font=("Segoe UI", 9))
        style.configure("CanvasMuted.TLabel", background=COLORS["canvas"], foreground=COLORS["muted"], font=("Segoe UI", 9))
        style.configure("MetricValue.TLabel", background=COLORS["white"], foreground=COLORS["ink"], font=("Segoe UI", 22, "bold"))

        style.configure("BadgeGreen.TLabel", background=COLORS["green_bg"], foreground=COLORS["green"], font=("Segoe UI", 8, "bold"), padding=(9, 4))
        style.configure("BadgeAmber.TLabel", background=COLORS["amber_bg"], foreground=COLORS["amber"], font=("Segoe UI", 8, "bold"), padding=(9, 4))
        style.configure("BadgeBlue.TLabel", background=COLORS["blue_pill_bg"], foreground=COLORS["blue_pill"], font=("Segoe UI", 8, "bold"), padding=(9, 4))

        style.configure("Primary.TButton", background=COLORS["accent_blue"], foreground=COLORS["white"], padding=(14, 9), borderwidth=0, font=bold_font)
        style.map("Primary.TButton", background=[("active", COLORS["blue_hover"])], foreground=[("disabled", "#94A3B8")])

        style.configure("Secondary.TButton", background=COLORS["white"], foreground=COLORS["ink"], padding=(12, 8), borderwidth=1, relief="solid", font=base_font)
        style.map("Secondary.TButton", background=[("active", "#F1F5F9")])

        style.configure("TEntry", padding=(8, 7), fieldbackground=COLORS["white"])
        style.configure("TCombobox", padding=(8, 7), fieldbackground=COLORS["white"])

        style.configure("Treeview", background=COLORS["white"], fieldbackground=COLORS["white"], foreground=COLORS["ink"], rowheight=34, borderwidth=0, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", background="#F8FAFC", foreground=COLORS["ink_secondary"], relief="flat", font=("Segoe UI", 9, "bold"), padding=(8, 8))
        style.map("Treeview", background=[("selected", "#EFF6FF")], foreground=[("selected", COLORS["accent_blue"])])

    def _build_shell(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ttk.Frame(self, style="Sidebar.TFrame", width=255, padding=(14, 18))
        self.sidebar.grid(row=0, column=0, sticky="ns")
        self.sidebar.grid_propagate(False)

        self.main = ttk.Frame(self, style="Canvas.TFrame")
        self.main.grid(row=0, column=1, sticky="nsew")
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(1, weight=1)

        # Brand header with clean FS monogram
        brand = ttk.Frame(self.sidebar, style="Sidebar.TFrame")
        brand.pack(fill="x", pady=(4, 24))
        icon = tk.Label(brand, text="FS", bg=COLORS["accent_blue"], fg="white", font=("Segoe UI", 12, "bold"), width=3, height=1, pady=6)
        icon.pack(side="left", padx=(0, 10))
        brand_text = ttk.Frame(brand, style="Sidebar.TFrame")
        brand_text.pack(side="left", fill="x", expand=True)
        ttk.Label(brand_text, text=TEXT[self.lang]["brand_title"], style="Brand.TLabel").pack(anchor="w")
        ttk.Label(brand_text, text=TEXT[self.lang]["brand_subtitle"], style="BrandSub.TLabel").pack(anchor="w", pady=(2, 0))

        self.nav_container = ttk.Frame(self.sidebar, style="Sidebar.TFrame")
        self.nav_container.pack(fill="x")

        self.sidebar_bottom = ttk.Frame(self.sidebar, style="Sidebar.TFrame")
        self.sidebar_bottom.pack(side="bottom", fill="x")

        self.lang_btn = tk.Button(
            self.sidebar_bottom,
            text="Tiếng Việt (VI)" if self.lang == "vi" else "English (EN)",
            bg=COLORS["navy_hover"],
            fg="#E2E8F0",
            activebackground=COLORS["navy_active"],
            activeforeground="#FFFFFF",
            relief="flat",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=6,
            command=self.toggle_language,
        )
        self.lang_btn.pack(fill="x", pady=(0, 10))

        self.sidebar_status = ttk.Label(self.sidebar_bottom, textvariable=self.status_var, style="Sidebar.TLabel", wraplength=210)
        self.sidebar_status.pack(anchor="w", pady=(0, 4))

        self.header = ttk.Frame(self.main, style="Canvas.TFrame", padding=(30, 20, 30, 10))
        self.header.grid(row=0, column=0, sticky="ew")
        self.header.grid_columnconfigure(0, weight=1)

        title_stack = ttk.Frame(self.header, style="Canvas.TFrame")
        title_stack.grid(row=0, column=0, sticky="w")
        self.page_title_var = tk.StringVar()
        self.page_subtitle_var = tk.StringVar()
        ttk.Label(title_stack, textvariable=self.page_title_var, style="PageTitle.TLabel").pack(anchor="w")
        ttk.Label(title_stack, textvariable=self.page_subtitle_var, style="CanvasMuted.TLabel").pack(anchor="w", pady=(4, 0))

        top_actions = ttk.Frame(self.header, style="Canvas.TFrame")
        top_actions.grid(row=0, column=1, sticky="e")
        self.license_badge = ttk.Label(top_actions, textvariable=self.license_badge_var, style="BadgeGreen.TLabel")
        self.license_badge.pack(side="right", padx=(8, 0))

        self.content = ttk.Frame(self.main, style="Canvas.TFrame", padding=(30, 10, 30, 25))
        self.content.grid(row=1, column=0, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)

        self._rebuild_nav()
        self.refresh_status()

    def _rebuild_nav(self) -> None:
        for child in self.nav_container.winfo_children():
            child.destroy()
        self.nav_buttons.clear()

        for index, label in enumerate(TEXT[self.lang]["nav"]):
            btn = tk.Button(
                self.nav_container,
                text=label,
                bg=COLORS["navy"],
                fg="#CBD5E1",
                activebackground=COLORS["navy_hover"],
                activeforeground="#FFFFFF",
                anchor="w",
                padx=14,
                pady=10,
                relief="flat",
                font=("Segoe UI", 10),
                borderwidth=0,
                command=lambda i=index: self.show_page(i),
            )
            btn.pack(fill="x", pady=2)
            self.nav_buttons.append(btn)

        self.lang_btn.configure(text="Tiếng Việt (VI)" if self.lang == "vi" else "English (EN)")

    def toggle_language(self) -> None:
        self.lang = "en" if self.lang == "vi" else "vi"
        self.settings["language"] = self.lang
        self._write_settings()
        self.title(TEXT[self.lang]["window"])
        self._rebuild_nav()
        self.show_page(self.current_page)

    def refresh_status(self) -> None:
        status = current_license_status(selected_email=self.email_var.get())
        label = status.get("licenseLabel") or TEXT[self.lang]["ready"]
        self.status_var.set(f"{TEXT[self.lang]['current_license']}: {label}")
        if hasattr(self, "license_badge"):
            self.license_badge_var.set(str(label))
            badge_style = "BadgeGreen.TLabel" if status.get("active") else "BadgeAmber.TLabel"
            self.license_badge.configure(style=badge_style)

    def clear_content(self) -> None:
        for widget in self.content.winfo_children():
            widget.destroy()

    def set_page_header(self, index: int) -> None:
        self.page_title_var.set(TEXT[self.lang]["page_titles"][index])
        self.page_subtitle_var.set(TEXT[self.lang]["page_subtitles"][index])
        for current, btn in enumerate(self.nav_buttons):
            if current == index:
                btn.configure(bg=COLORS["navy_active"], fg="#FFFFFF", font=("Segoe UI", 10, "bold"))
            else:
                btn.configure(bg=COLORS["navy"], fg="#CBD5E1", font=("Segoe UI", 10))

    def card(self, parent: ttk.Widget, padding: int = 18) -> tk.Frame:
        return tk.Frame(parent, bg=COLORS["white"], highlightbackground=COLORS["line"], highlightthickness=1, padx=padding, pady=padding)

    def section_label(self, parent: tk.Widget, text: str) -> tk.Label:
        lbl = tk.Label(parent, text=text, bg=COLORS["white"], fg=COLORS["ink"], font=("Segoe UI", 12, "bold"))
        lbl.pack(anchor="w")
        return lbl

    def show_page(self, page: int) -> None:
        self.current_page = page
        self.clear_content()
        self.set_page_header(page)
        if page == 0:
            self._show_overview()
        elif page == 1:
            self._show_demo()
        elif page == 2:
            self._show_cases()
        elif page == 3:
            self._show_license()
        elif page == 4:
            self._show_settings()
        else:
            self._show_help()

    # -------------------------------------------------------------------------
    # PAGE 0: OVERVIEW
    # -------------------------------------------------------------------------
    def _show_overview(self) -> None:
        t = TEXT[self.lang]

        metrics = ttk.Frame(self.content, style="Canvas.TFrame")
        metrics.pack(fill="x", pady=(0, 16))
        for col in range(4):
            metrics.grid_columnconfigure(col, weight=1, uniform="overview-metric")

        supported_count = sum(1 for item in APP_CATALOG if item["status"] == "available")
        planned_count = sum(1 for item in APP_CATALOG if item["status"] != "available")
        cases_dir = Path(self.workspace_var.get()) / "cases"
        case_count = sum(1 for p in cases_dir.iterdir() if p.is_dir()) if cases_dir.exists() else 0

        self._metric_card(metrics, 0, str(supported_count), t["supported_now"], "●", COLORS["green"])
        self._metric_card(metrics, 1, str(planned_count), t["planned_apps"], "⏱", COLORS["amber"])
        self._metric_card(metrics, 2, str(case_count), "Hồ sơ đã lưu" if self.lang == "vi" else "Saved Cases", "▤", COLORS["accent_blue"])
        short_ws = Path(self.workspace_var.get()).name or "workspace"
        self._metric_card(metrics, 3, short_ws, t["workspace"], "💻", "#6366F1", small=True)

        scope_card = self.card(self.content, padding=20)
        scope_card.pack(fill="x", pady=(0, 16))
        scope_card.grid_columnconfigure(1, weight=1)

        tk.Label(scope_card, text=t["scope_title"], bg=COLORS["white"], fg=COLORS["ink"], font=("Segoe UI", 13, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 14))

        tk.Label(scope_card, text=t["choose_app"], bg=COLORS["white"], fg=COLORS["ink_secondary"], font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky="w", pady=4)
        app_row = tk.Frame(scope_card, bg=COLORS["white"])
        app_row.grid(row=1, column=1, sticky="w", padx=(10, 0), pady=4)
        self.app_combo = ttk.Combobox(app_row, state="readonly", textvariable=self.selected_app_var, width=32)
        self.app_combo.pack(side="left")
        self._set_app_options()
        self.app_combo.bind("<<ComboboxSelected>>", self._on_app_selected)

        self.app_status_badge = tk.Label(app_row, text=t["app_supported"], bg=COLORS["green_bg"], fg=COLORS["green"], font=("Segoe UI", 8, "bold"), padx=8, pady=3)
        self.app_status_badge.pack(side="left", padx=10)

        tk.Label(scope_card, text=t["channel_url"], bg=COLORS["white"], fg=COLORS["ink_secondary"], font=("Segoe UI", 10)).grid(row=2, column=0, sticky="w", pady=6)
        ch_entry = ttk.Entry(scope_card, textvariable=self.channel_url_var, width=54)
        ch_entry.grid(row=2, column=1, sticky="w", padx=(10, 0), pady=6)

        tk.Label(scope_card, text=t["target_user"], bg=COLORS["white"], fg=COLORS["ink_secondary"], font=("Segoe UI", 10)).grid(row=3, column=0, sticky="w", pady=6)
        user_entry = ttk.Entry(scope_card, textvariable=self.target_user_var, width=54)
        user_entry.grid(row=3, column=1, sticky="w", padx=(10, 0), pady=6)

        btn_row = tk.Frame(scope_card, bg=COLORS["white"])
        btn_row.grid(row=4, column=0, columnspan=2, sticky="w", pady=(14, 0))

        start_btn = tk.Button(
            btn_row,
            text=t["start"],
            bg=COLORS["accent_blue"],
            fg="white",
            activebackground=COLORS["blue_hover"],
            activeforeground="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=16,
            pady=8,
            command=self.start_workflow,
        )
        start_btn.pack(side="left", padx=(0, 10))

        demo_btn = tk.Button(
            btn_row,
            text=t["explore_demo"],
            bg=COLORS["white"],
            fg=COLORS["ink"],
            activebackground="#F1F5F9",
            font=("Segoe UI", 9, "bold"),
            relief="solid",
            borderwidth=1,
            padx=12,
            pady=7,
            command=lambda: self.show_page(1),
        )
        demo_btn.pack(side="left", padx=(0, 10))

        ws_btn = tk.Button(
            btn_row,
            text=t["open_workspace"],
            bg=COLORS["white"],
            fg=COLORS["ink"],
            activebackground="#F1F5F9",
            font=("Segoe UI", 9, "bold"),
            relief="solid",
            borderwidth=1,
            padx=12,
            pady=7,
            command=lambda: self.open_path(Path(self.workspace_var.get())),
        )
        ws_btn.pack(side="left")

        log_card = self.card(self.content, padding=16)
        log_card.pack(fill="both", expand=True)
        tk.Label(log_card, text=t["live_log_title"], bg=COLORS["white"], fg=COLORS["ink"], font=("Segoe UI", 11, "bold")).pack(anchor="w")

        self.console_text = tk.Text(
            log_card,
            height=7,
            bg="#0F172A",
            fg="#F8FAFC",
            relief="flat",
            font=("Consolas", 9),
            padx=10,
            pady=8,
            wrap="word",
        )
        self.console_text.pack(fill="both", expand=True, pady=(8, 0))
        self._log("Forensics Suite ready. Target workspace: " + str(self.workspace_var.get()))
        self._log("System elevation: " + ("Administrator (Elevated)" if is_admin() else "Standard User"))

    def _metric_card(self, parent: ttk.Widget, column: int, value: str, label: str, icon: str, accent: str, small: bool = False) -> None:
        card = self.card(parent, padding=14)
        card.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 6, 6 if column < 3 else 0))
        tk.Label(card, text=icon, bg=COLORS["white"], fg=accent, font=("Segoe UI", 14)).pack(anchor="w")
        tk.Label(card, text=value, bg=COLORS["white"], fg=COLORS["ink"], font=("Segoe UI", 14 if small else 20, "bold")).pack(anchor="w", pady=(4, 1))
        tk.Label(card, text=label, bg=COLORS["white"], fg=COLORS["muted"], font=("Segoe UI", 9)).pack(anchor="w")

    def _set_app_options(self) -> None:
        labels = [app_label(item, self.lang) for item in APP_CATALOG]
        self.app_combo.configure(values=labels)
        selected = get_app(self.selected_app_id)
        self.selected_app_var.set(app_label(selected, self.lang))

    def _on_app_selected(self, _event: object = None) -> None:
        selected_label = self.selected_app_var.get()
        selected = next((item for item in APP_CATALOG if app_label(item, self.lang) == selected_label), get_app("discord"))
        self.selected_app_id = str(selected["id"])
        if selected["status"] != "available":
            messagebox.showinfo(TEXT[self.lang]["unsupported_title"], TEXT[self.lang]["unsupported"])
            self.selected_app_id = "discord"
            self._set_app_options()
        self._update_selected_app_status()

    def _update_selected_app_status(self) -> None:
        if not hasattr(self, "app_status_badge"):
            return
        app = get_app(self.selected_app_id)
        if app["status"] == "available":
            self.app_status_badge.configure(text=TEXT[self.lang]["app_supported"], bg=COLORS["green_bg"], fg=COLORS["green"])
        else:
            self.app_status_badge.configure(text=TEXT[self.lang]["app_planned"], bg=COLORS["amber_bg"], fg=COLORS["amber"])

    def _log(self, text: str) -> None:
        if hasattr(self, "console_text"):
            now = datetime.now().strftime("%H:%M:%S")
            self.console_text.insert("end", f"[{now}] {text}\n")
            self.console_text.see("end")

    # -------------------------------------------------------------------------
    # PAGE 1: DATA DEMO
    # -------------------------------------------------------------------------
    def _show_demo(self) -> None:
        t = TEXT[self.lang]

        head = ttk.Frame(self.content, style="Canvas.TFrame")
        head.pack(fill="x", pady=(0, 12))
        head.grid_columnconfigure(0, weight=1)
        ttk.Label(head, text=t["demo_subtitle"], style="CanvasMuted.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(head, text=t["sample_badge"], style="BadgeAmber.TLabel").grid(row=0, column=1, sticky="e")

        metrics = ttk.Frame(self.content, style="Canvas.TFrame")
        metrics.pack(fill="x", pady=(0, 12))
        for col in range(4):
            metrics.grid_columnconfigure(col, weight=1, uniform="demo-metric")

        counts = [
            (str(len(DEMO_MESSAGES)), t["metric_messages"], "💬"),
            ("3", t["metric_participants"], "👥"),
            (str(len(DEMO_FILES)), t["metric_files"], "📎"),
            ("4", t["metric_events"], "⏱"),
        ]
        for col, (value, label, icon) in enumerate(counts):
            card = self.card(metrics, padding=12)
            card.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 5, 5 if col < 3 else 0))
            tk.Label(card, text=icon, bg=COLORS["white"], font=("Segoe UI", 12)).pack(anchor="w")
            tk.Label(card, text=value, bg=COLORS["white"], fg=COLORS["ink"], font=("Segoe UI", 18, "bold")).pack(anchor="w")
            tk.Label(card, text=label, bg=COLORS["white"], fg=COLORS["muted"], font=("Segoe UI", 9)).pack(anchor="w")

        split = ttk.Frame(self.content, style="Canvas.TFrame")
        split.pack(fill="both", expand=True, pady=(0, 12))
        split.grid_columnconfigure(0, weight=3)
        split.grid_columnconfigure(1, weight=2)
        split.grid_rowconfigure(0, weight=1)

        tl_card = self.card(split, padding=14)
        tl_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.section_label(tl_card, t["timeline"])

        tree = ttk.Treeview(tl_card, columns=("time", "participant", "channel", "message"), show="headings", height=8)
        tree.heading("time", text=t["time"])
        tree.heading("participant", text=t["participant"])
        tree.heading("channel", text=t["channel"])
        tree.heading("message", text=t["message"])
        tree.column("time", width=75, stretch=False)
        tree.column("participant", width=125, stretch=False)
        tree.column("channel", width=105, stretch=False)
        tree.column("message", width=310, stretch=True)
        tree.pack(fill="both", expand=True, pady=(10, 0))

        for row in DEMO_MESSAGES:
            msg = row[3] if self.lang == "en" else self._translate_demo_message(row[3])
            tree.insert("", "end", values=(row[0], row[1], row[2], msg))

        right_col = ttk.Frame(split, style="Canvas.TFrame")
        right_col.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        right_col.grid_rowconfigure(1, weight=1)
        right_col.grid_columnconfigure(0, weight=1)

        art_card = self.card(right_col, padding=14)
        art_card.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.section_label(art_card, t["artifacts"])

        files_tree = ttk.Treeview(art_card, columns=("name", "type", "note"), show="headings", height=2)
        files_tree.heading("name", text=t["file_name"])
        files_tree.heading("type", text=t["file_type"])
        files_tree.heading("note", text=t["file_note"])
        files_tree.column("name", width=120, stretch=True)
        files_tree.column("type", width=65, stretch=False)
        files_tree.column("note", width=140, stretch=True)
        files_tree.pack(fill="x", pady=(8, 0))

        for filename, file_type, note in DEMO_FILES:
            display_note = self._translate_demo_file_note(note) if self.lang == "vi" else note
            files_tree.insert("", "end", values=(filename, file_type, display_note))

        summary_card = self.card(right_col, padding=14)
        summary_card.grid(row=1, column=0, sticky="nsew")
        self.section_label(summary_card, t["report_preview"])
        tk.Label(summary_card, text=t["report_text"], bg=COLORS["white"], fg=COLORS["muted"], font=("Segoe UI", 9), wraplength=320, justify="left").pack(anchor="w", pady=(8, 12))

        open_summary_btn = tk.Button(
            summary_card,
            text=t["open_sample_report"],
            bg=COLORS["white"],
            fg=COLORS["ink"],
            activebackground="#F1F5F9",
            font=("Segoe UI", 9, "bold"),
            relief="solid",
            borderwidth=1,
            padx=10,
            pady=6,
            command=self._show_sample_modal,
        )
        open_summary_btn.pack(anchor="w")

        notice_card = self.card(self.content, padding=12)
        notice_card.pack(fill="x")
        tk.Label(notice_card, text=t["demo_notice"], bg=COLORS["white"], fg=COLORS["muted"], font=("Segoe UI", 9), wraplength=650, justify="left").pack(anchor="w")

    def _show_sample_modal(self) -> None:
        title = "Sample Findings · Tabletop Exercise" if self.lang == "en" else "Kết luận Mẫu · Diễn tập Tabletop"
        content = (
            "CASE ID: CASE-SAMPLE-0142\n"
            "Channel: #ops-tabletop\n"
            "Simulated Range: 08:15 to 08:57 UTC\n\n"
            "Key Findings:\n"
            "1. 7 simulated messages exchanged between analyst_sample and responder_mock.\n"
            "2. No anomalies detected; simulation checklist confirmed.\n"
            "3. Artifacts sample-note.txt and sample-map.png verified with mock SHA-256.\n\n"
            "Conclusion: Sample workflow demonstrates successful timeline indexing and artifact tracing."
        )
        messagebox.showinfo(title, content)

    @staticmethod
    def _translate_demo_message(message: str) -> str:
        translations = {
            "Exercise begins. All events are simulated.": "Bắt đầu diễn tập. Tất cả sự kiện đều mô phỏng.",
            "Mock alert received; no live systems involved.": "Đã nhận cảnh báo giả lập; không có hệ thống thật.",
            "Checkpoint saved to sample-note.txt.": "Đã lưu mốc vào sample-note.txt.",
            "Review the sample attachment only.": "Chỉ xem tệp đính kèm mẫu.",
            "sample-map.png is a demo placeholder.": "sample-map.png là ảnh minh họa demo.",
            "Simulated handoff complete.": "Hoàn tất bàn giao mô phỏng.",
            "Exercise closed; no real data accessed.": "Kết thúc diễn tập; không truy cập dữ liệu thật.",
        }
        return translations.get(message, message)

    @staticmethod
    def _translate_demo_file_note(note: str) -> str:
        return {
            "Incident checklist": "Danh mục kiểm tra",
            "Mock topology": "Sơ đồ mạng giả lập",
        }.get(note, note)

    # -------------------------------------------------------------------------
    # PAGE 2: CASES & REPORTS
    # -------------------------------------------------------------------------
    def _show_cases(self) -> None:
        t = TEXT[self.lang]
        folder = Path(self.workspace_var.get()) / "cases"

        top = self.card(self.content, padding=16)
        top.pack(fill="x", pady=(0, 14))
        top.grid_columnconfigure(0, weight=1)

        tk.Label(top, text=t["case_folder"], bg=COLORS["white"], fg=COLORS["ink"], font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w")
        tk.Label(top, text=str(folder), bg=COLORS["white"], fg=COLORS["muted"], font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", pady=(4, 0))

        btn_box = tk.Frame(top, bg=COLORS["white"])
        btn_box.grid(row=0, column=1, rowspan=2, sticky="e")

        refresh_btn = tk.Button(btn_box, text=t["refresh_cases"], bg=COLORS["white"], fg=COLORS["ink"], font=("Segoe UI", 9), relief="solid", borderwidth=1, padx=10, pady=5, command=lambda: self.show_page(2))
        refresh_btn.pack(side="left", padx=(0, 8))

        open_dir_btn = tk.Button(btn_box, text=t["open_folder"], bg=COLORS["white"], fg=COLORS["ink"], font=("Segoe UI", 9, "bold"), relief="solid", borderwidth=1, padx=12, pady=5, command=lambda: self.open_path(folder))
        open_dir_btn.pack(side="left")

        cases_card = self.card(self.content, padding=16)
        cases_card.pack(fill="both", expand=True)

        self.section_label(cases_card, t["recent_cases"])

        # Table with adjusted generous column widths (folders width=130 avoids truncation of "Thư mục con")
        self.cases_tree = ttk.Treeview(cases_card, columns=("case", "modified", "folders", "path"), show="headings", height=10)
        self.cases_tree.heading("case", text="Mã Hồ sơ (Case ID)" if self.lang == "vi" else "Case ID")
        self.cases_tree.heading("modified", text="Thời điểm Sửa đổi" if self.lang == "vi" else "Last Modified")
        self.cases_tree.heading("folders", text="Thư mục con" if self.lang == "vi" else "Subfolders")
        self.cases_tree.heading("path", text="Đường dẫn Đầy đủ" if self.lang == "vi" else "Full Path")

        self.cases_tree.column("case", width=220, stretch=False)
        self.cases_tree.column("modified", width=170, stretch=False)
        self.cases_tree.column("folders", width=130, stretch=False)
        self.cases_tree.column("path", width=360, stretch=True)
        self.cases_tree.pack(fill="both", expand=True, pady=(10, 14))

        cases = sorted((path for path in folder.iterdir() if path.is_dir()), key=lambda path: path.stat().st_mtime, reverse=True)[:100] if folder.exists() else []
        if not cases:
            # Display single word 'Trống' or leave empty as requested
            self.cases_tree.insert("", "end", values=("Trống" if self.lang == "vi" else "Empty", "", "", ""))
        else:
            for path in cases:
                modified = path.stat().st_mtime
                mod_str = datetime.fromtimestamp(modified).strftime("%Y-%m-%d %H:%M")
                subcount = sum(1 for sub in path.iterdir() if sub.is_dir())
                self.cases_tree.insert("", "end", values=(path.name, mod_str, f"{subcount} folders", str(path)))

        self.cases_tree.bind("<Double-1>", lambda _event: self._open_selected_case())

        actions_bar = tk.Frame(cases_card, bg=COLORS["white"])
        actions_bar.pack(fill="x")

        open_case_btn = tk.Button(actions_bar, text=t["open_folder"], bg=COLORS["white"], fg=COLORS["ink"], font=("Segoe UI", 9, "bold"), relief="solid", borderwidth=1, padx=12, pady=6, command=self._open_selected_case)
        open_case_btn.pack(side="left", padx=(0, 8))

        open_report_btn = tk.Button(actions_bar, text=t["open_report"], bg=COLORS["accent_blue"], fg="white", font=("Segoe UI", 9, "bold"), relief="flat", padx=12, pady=6, command=self._open_selected_report)
        open_report_btn.pack(side="left", padx=(0, 8))

        open_autopsy_btn = tk.Button(actions_bar, text=t["open_autopsy"], bg=COLORS["white"], fg=COLORS["ink"], font=("Segoe UI", 9), relief="solid", borderwidth=1, padx=12, pady=6, command=self._open_selected_autopsy)
        open_autopsy_btn.pack(side="left")

    def _get_selected_case_path(self) -> Path | None:
        if not hasattr(self, "cases_tree"):
            return None
        sel = self.cases_tree.selection()
        if not sel:
            return None
        vals = self.cases_tree.item(sel[0], "values")
        if vals and vals[0] not in {"Trống", "Empty", "(Trống)", "", TEXT[self.lang]["no_cases"]} and len(vals) >= 4 and vals[3]:
            return Path(str(vals[3]))
        return None

    def _open_selected_case(self) -> None:
        p = self._get_selected_case_path()
        if p and p.exists():
            self.open_path(p)
        else:
            messagebox.showinfo("Case", "Chưa có hồ sơ nào được chọn." if self.lang == "vi" else "No case selected.")

    def _open_selected_report(self) -> None:
        p = self._get_selected_case_path()
        if p and p.exists():
            rep = p / "08_Report" / "Muc_luc_bao_cao.md"
            if rep.exists():
                webbrowser.open(rep.as_uri())
            else:
                messagebox.showinfo("Report", "Báo cáo chưa được xây dựng cho hồ sơ này." if self.lang == "vi" else "Report not built for this case yet.")
        else:
            messagebox.showinfo("Report", "Chưa có hồ sơ nào được chọn." if self.lang == "vi" else "No case selected.")

    def _open_selected_autopsy(self) -> None:
        p = self._get_selected_case_path()
        if p and p.exists():
            auto = p / "05_Autopsy_Case"
            if auto.exists():
                self.open_path(auto)
            else:
                messagebox.showinfo("Autopsy", "Gói Autopsy chưa được xuất cho hồ sơ này." if self.lang == "vi" else "Autopsy bundle not exported for this case yet.")
        else:
            messagebox.showinfo("Autopsy", "Chưa có hồ sơ nào được chọn." if self.lang == "vi" else "No case selected.")

    # -------------------------------------------------------------------------
    # PAGE 3: LICENSE & DEVICE
    # -------------------------------------------------------------------------
    def _show_license(self) -> None:
        t = TEXT[self.lang]
        status = current_license_status(selected_email=self.email_var.get())

        top = self.card(self.content, padding=18)
        top.pack(fill="x", pady=(0, 14))

        tk.Label(top, text=t["license_state"], bg=COLORS["white"], fg=COLORS["ink"], font=("Segoe UI", 12, "bold")).pack(anchor="w")
        label_text = str(status.get("licenseLabel") or t["ready"])
        badge_style = "BadgeGreen.TLabel" if status.get("active") else "BadgeAmber.TLabel"
        ttk.Label(top, text=label_text, style=badge_style).pack(anchor="w", pady=(8, 4))
        exp_text = f"Hạn dùng: {status.get('expiresAt', 'N/A')}" if self.lang == "vi" else f"Expires: {status.get('expiresAt', 'N/A')}"
        tk.Label(top, text=exp_text, bg=COLORS["white"], fg=COLORS["muted"], font=("Segoe UI", 9)).pack(anchor="w")

        fp_card = self.card(self.content, padding=18)
        fp_card.pack(fill="x", pady=(0, 14))
        fp_card.grid_columnconfigure(0, weight=1)

        tk.Label(fp_card, text=t["device"], bg=COLORS["white"], fg=COLORS["ink"], font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w")
        fp_entry = ttk.Entry(fp_card, font=("Consolas", 9))
        fp_entry.insert(0, machine_fingerprint())
        fp_entry.configure(state="readonly")
        fp_entry.grid(row=1, column=0, sticky="ew", pady=(6, 8))

        copy_btn = tk.Button(
            fp_card,
            text=t["copy_device"],
            bg=COLORS["white"],
            fg=COLORS["ink"],
            font=("Segoe UI", 9, "bold"),
            relief="solid",
            borderwidth=1,
            padx=10,
            pady=5,
            command=self._copy_fingerprint,
        )
        copy_btn.grid(row=1, column=1, sticky="w", padx=(10, 0), pady=(6, 8))

        self.copy_status_lbl = tk.Label(fp_card, text="", bg=COLORS["white"], fg=COLORS["green"], font=("Segoe UI", 9, "bold"))
        self.copy_status_lbl.grid(row=2, column=0, sticky="w")

        form = self.card(self.content, padding=18)
        form.pack(fill="x", pady=(0, 14))
        form.grid_columnconfigure(0, weight=1)

        tk.Label(form, text=t["email"], bg=COLORS["white"], fg=COLORS["ink"], font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.email_var).grid(row=1, column=0, sticky="ew", pady=(4, 10))

        tk.Label(form, text=t["key"], bg=COLORS["white"], fg=COLORS["ink"], font=("Segoe UI", 10, "bold")).grid(row=2, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.key_var).grid(row=3, column=0, sticky="ew", pady=(4, 14))

        buttons = tk.Frame(form, bg=COLORS["white"])
        buttons.grid(row=4, column=0, sticky="w")

        act_btn = tk.Button(buttons, text=t["activate"], bg=COLORS["accent_blue"], fg="white", font=("Segoe UI", 10, "bold"), relief="flat", padx=14, pady=7, command=self.activate)
        act_btn.pack(side="left", padx=(0, 8))

        trial_btn = tk.Button(buttons, text=t["trial"], bg=COLORS["white"], fg=COLORS["ink"], font=("Segoe UI", 9, "bold"), relief="solid", borderwidth=1, padx=12, pady=6, command=self.start_trial)
        trial_btn.pack(side="left", padx=(0, 8))

        req_btn = tk.Button(buttons, text=t["request_key"], bg=COLORS["white"], fg=COLORS["ink"], font=("Segoe UI", 9), relief="solid", borderwidth=1, padx=12, pady=6, command=self.request_key)
        req_btn.pack(side="left")

        owner_card = self.card(self.content, padding=14)
        owner_card.pack(fill="x")
        tk.Label(owner_card, text=t["owner"], bg=COLORS["white"], fg=COLORS["muted"], font=("Segoe UI", 9)).pack(anchor="w")

    def _copy_fingerprint(self) -> None:
        self.clipboard_clear()
        self.clipboard_append(machine_fingerprint())
        self.copy_status_lbl.configure(text=TEXT[self.lang]["copied"])
        self.after(2500, lambda: self.copy_status_lbl.configure(text=""))

    # -------------------------------------------------------------------------
    # PAGE 4: SETTINGS & ENVIRONMENT
    # -------------------------------------------------------------------------
    def _show_settings(self) -> None:
        t = TEXT[self.lang]

        card = self.card(self.content, padding=20)
        card.pack(fill="x", pady=(0, 14))

        tk.Label(card, text=t["workspace_path"], bg=COLORS["white"], fg=COLORS["ink"], font=("Segoe UI", 11, "bold")).pack(anchor="w")
        row = tk.Frame(card, bg=COLORS["white"])
        row.pack(fill="x", pady=(8, 14))
        ttk.Entry(row, textvariable=self.workspace_var).pack(side="left", fill="x", expand=True)

        browse_btn = tk.Button(row, text=t["browse"], bg=COLORS["white"], fg=COLORS["ink"], font=("Segoe UI", 9), relief="solid", borderwidth=1, padx=10, pady=5, command=self.browse_workspace)
        browse_btn.pack(side="left", padx=(8, 0))

        reset_btn = tk.Button(row, text=t["reset_workspace"], bg=COLORS["white"], fg=COLORS["ink"], font=("Segoe UI", 9), relief="solid", borderwidth=1, padx=10, pady=5, command=self._reset_workspace)
        reset_btn.pack(side="left", padx=(8, 0))

        tk.Label(card, text=t["language"], bg=COLORS["white"], fg=COLORS["ink"], font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(8, 4))
        lang_selector = ttk.Combobox(card, state="readonly", values=["Tiếng Việt", "English"], width=22)
        lang_selector.current(0 if self.lang == "vi" else 1)
        lang_selector.pack(anchor="w", pady=(0, 16))
        lang_selector.bind("<<ComboboxSelected>>", lambda _e: self._change_language("vi" if lang_selector.current() == 0 else "en"))

        save_btn = tk.Button(card, text=t["save"], bg=COLORS["accent_blue"], fg="white", font=("Segoe UI", 10, "bold"), relief="flat", padx=16, pady=7, command=self.save_settings)
        save_btn.pack(anchor="w")

        admin_card = self.card(self.content, padding=18)
        admin_card.pack(fill="x")

        tk.Label(admin_card, text=t["admin_status"], bg=COLORS["white"], fg=COLORS["ink"], font=("Segoe UI", 11, "bold")).pack(anchor="w")
        is_elevated = is_admin()
        status_lbl = tk.Label(admin_card, text=t["admin_yes"] if is_elevated else t["admin_no"], bg=COLORS["white"], fg=COLORS["green"] if is_elevated else COLORS["amber"], font=("Segoe UI", 9, "bold"))
        status_lbl.pack(anchor="w", pady=(8, 12))

        if not is_elevated:
            relaunch_btn = tk.Button(admin_card, text=t["relaunch_admin"], bg=COLORS["white"], fg=COLORS["ink"], font=("Segoe UI", 9, "bold"), relief="solid", borderwidth=1, padx=12, pady=6, command=lambda: rerun_as_admin(["--gui-elevated"]))
            relaunch_btn.pack(anchor="w")

    def _reset_workspace(self) -> None:
        def_path = Path.home() / "Documents" / "ForensicsSuite_Workspace"
        self.workspace_var.set(str(def_path))

    def _change_language(self, language: str) -> None:
        if language != self.lang:
            self.lang = language
            self.settings["language"] = language
            self._write_settings()
            self.title(TEXT[self.lang]["window"])
            self._rebuild_nav()
            self.show_page(4)

    # -------------------------------------------------------------------------
    # PAGE 5: HELP & ABOUT
    # -------------------------------------------------------------------------
    def _show_help(self) -> None:
        t = TEXT[self.lang]

        about = self.card(self.content, padding=20)
        about.pack(fill="x", pady=(0, 14))

        tk.Label(about, text=PRODUCT_NAME, bg=COLORS["white"], fg=COLORS["ink"], font=("Segoe UI", 16, "bold")).pack(anchor="w")
        # Ensure wraplength does not exceed card width and fill="x" so text starts at margin
        about_lbl = tk.Label(about, text=t["about_text"], bg=COLORS["white"], fg=COLORS["muted"], font=("Segoe UI", 10), wraplength=650, justify="left")
        about_lbl.pack(fill="x", anchor="w", pady=(8, 14))

        tk.Label(about, text=t["version"], bg=COLORS["white"], fg=COLORS["ink_secondary"], font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Label(about, text=t["owner"], bg=COLORS["white"], fg=COLORS["muted"], font=("Segoe UI", 9)).pack(anchor="w", pady=(4, 0))
        tk.Label(about, text=f"Contact: {__contact__}", bg=COLORS["white"], fg=COLORS["muted"], font=("Segoe UI", 9)).pack(anchor="w", pady=(2, 0))

        cli_card = self.card(self.content, padding=18)
        cli_card.pack(fill="x")

        tk.Label(cli_card, text=t["cli_title"], bg=COLORS["white"], fg=COLORS["ink"], font=("Segoe UI", 12, "bold")).pack(anchor="w")
        tk.Label(cli_card, text=t["cli_help"], bg=COLORS["white"], fg=COLORS["muted"], font=("Segoe UI", 9)).pack(anchor="w", pady=(6, 10))

        cmd_box = tk.Text(cli_card, height=4, bg="#0F172A", fg="#F8FAFC", relief="flat", font=("Consolas", 10), padx=12, pady=10)
        cmd_box.insert("1.0", ".\\fdctl.cmd menu               # Mở menu điều hướng dòng lệnh đầy đủ\n.\\fdctl.cmd apps detect        # Quét và kiểm tra ứng dụng trên máy\n.\\fdctl.cmd report open --case <id>  # Mở báo cáo của một case đã lưu")
        cmd_box.configure(state="disabled")
        cmd_box.pack(fill="x")

    # -------------------------------------------------------------------------
    # WORKFLOW EXECUTION & PIPELINE
    # -------------------------------------------------------------------------
    def start_workflow(self, skip_confirmation: bool = False) -> None:
        selected = get_app(self.selected_app_id)
        if selected["status"] != "available":
            self._on_app_selected()
            return

        try:
            status = current_license_status(selected_email=self.email_var.get())
            if "collection" not in status.get("features", []) and "owner" not in status.get("features", []):
                self.show_page(3)
                messagebox.showwarning("License", TEXT[self.lang]["need_license"])
                return
            require_active_license("collection")
        except Exception as exc:
            messagebox.showerror("License", str(exc))
            self.show_page(3)
            return

        if not skip_confirmation and not messagebox.askyesno(PRODUCT_NAME, TEXT[self.lang]["confirm_start"]):
            return

        self.status_var.set(TEXT[self.lang]["run"])
        self._log(f"Starting investigation for {selected['name']}...")
        if self.channel_url_var.get():
            self._log(f"Target scope channel: {self.channel_url_var.get()}")
        if self.target_user_var.get():
            self._log(f"Target scope user: {self.target_user_var.get()}")

        self.progress = ttk.Progressbar(self.content, mode="indeterminate", length=400)
        self.progress.pack(anchor="w", pady=(12, 0))
        self.progress.start(10)

        threading.Thread(target=self._run_pipeline, args=(str(selected["id"]),), daemon=True).start()

    def _run_pipeline(self, app_id: str) -> None:
        try:
            if sys.platform == "win32" and not is_admin():
                self.after(0, lambda: self.status_var.set(TEXT[self.lang]["admin_req"]))
                rerun_as_admin(["--gui-elevated", "--app", app_id])

            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                from fdctl.services.analysis_service import analyze_case
                from fdctl.services.case_service import create_case, save_case
                from fdctl.services.collection_service import collect_case
                from fdctl.services.report_service import build_report

                ch_url = self.channel_url_var.get().strip() or None
                t_user = self.target_user_var.get().strip() or None

                self.after(0, lambda: self._log("Creating new forensic case directory..."))
                context = create_case(app_id, channel_url=ch_url, target_user=t_user)
                self.after(0, lambda: self._log(f"Case initialized: {context.case_id}"))

                self.after(0, lambda: self._log("Collecting live response and desktop artifacts..."))
                collect_res = collect_case(context, elevated=self.elevated_launch)
                art_count = collect_res.get("artifactCount", 0)
                self.after(0, lambda: self._log(f"Collection complete: {art_count} artifacts acquired."))

                self.after(0, lambda: self._log("Analyzing SQLite databases, cache, and recovering messages..."))
                analyze_res = analyze_case(context)
                rec_msg = analyze_res.get("recoveredMessageRows", 0)
                tl_rows = analyze_res.get("timelineRows", 0)
                self.after(0, lambda: self._log(f"Analysis complete: {rec_msg} messages, {tl_rows} timeline events."))

                self.after(0, lambda: self._log("Building investigation report & Autopsy package..."))
                build_report(context)

                saved = save_case(context.case_id)
                self.after(0, lambda: self._log(f"Saved canonical case: {saved.root}"))

            self.after(0, lambda: self._finish_workflow(TEXT[self.lang]["done"]))
            self.after(0, lambda: self.open_path(saved.root))
        except SystemExit:
            self.after(0, lambda: self._finish_workflow(TEXT[self.lang]["admin_req"]))
        except Exception as exc:
            msg = str(exc)
            if "administrator" in msg.lower() or "access is denied" in msg.lower():
                msg = f"{TEXT[self.lang]['admin_req']}\n\n{msg}"
            self.after(0, lambda m=msg: self._log(f"ERROR: {m}"))
            self.after(0, lambda m=msg: messagebox.showerror(PRODUCT_NAME, m))
            self.after(0, lambda: self._finish_workflow(TEXT[self.lang]["ready"]))

    def _finish_workflow(self, label: str) -> None:
        if self.progress:
            try:
                self.progress.stop()
                self.progress.destroy()
            except tk.TclError:
                pass
            self.progress = None
        self.status_var.set(label)
        self._log(label)

    # -------------------------------------------------------------------------
    # LICENSE ACTIONS
    # -------------------------------------------------------------------------
    def activate(self) -> None:
        try:
            status = activate_license_token(self.key_var.get(), self.email_var.get())
            messagebox.showinfo(TEXT[self.lang]["license"], f"{TEXT[self.lang]['activated']}\n{status.get('licenseLabel')}\n{status.get('expiresAt', '')}")
            self.key_var.set("")
            self.refresh_status()
            if self.current_page == 3:
                self.show_page(3)
        except Exception as exc:
            messagebox.showerror(TEXT[self.lang]["license"], str(exc))

    def start_trial(self) -> None:
        try:
            status = current_license_status(selected_email=self.email_var.get(), force_enforced=True)
            if not status.get("active"):
                raise ValueError(str(status.get("reason", "Could not start trial.")))
            self.refresh_status()
            messagebox.showinfo(TEXT[self.lang]["license"], f"{status.get('licenseLabel')}\n{status.get('expiresAt')}")
            if self.current_page == 3:
                self.show_page(3)
        except Exception as exc:
            messagebox.showerror(TEXT[self.lang]["license"], str(exc))

    def request_key(self) -> None:
        email = self.email_var.get().strip()
        if not email:
            messagebox.showwarning(TEXT[self.lang]["license"], TEXT[self.lang]["missing_email"])
            return
        subject = TEXT[self.lang]["license_request_subject"]
        body = f"Email: {email}\nDevice fingerprint: {machine_fingerprint()}\nRequested: 7 / 30 / 365-day license"
        url = f"mailto:{OWNER_EMAIL}?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
        webbrowser.open(url)

    def browse_workspace(self) -> None:
        selected = filedialog.askdirectory(initialdir=self.workspace_var.get() or str(Path.home() / "Documents"))
        if selected:
            self.workspace_var.set(selected)

    def _write_settings(self) -> None:
        _settings_path().parent.mkdir(parents=True, exist_ok=True)
        _settings_path().write_text(json.dumps(self.settings, ensure_ascii=False, indent=2), encoding="utf-8")

    def save_settings(self) -> None:
        self.settings.update({"workspace": self.workspace_var.get(), "licenseEmail": self.email_var.get(), "language": self.lang})
        self._write_settings()
        self.refresh_status()
        messagebox.showinfo(PRODUCT_NAME, TEXT[self.lang]["saved"])
        if self.current_page in {0, 4}:
            self.show_page(self.current_page)

    @staticmethod
    def open_path(path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)
        webbrowser.open(path.as_uri())


def main() -> int:
    elevated_launch = "--gui-elevated" in sys.argv
    if "--app" in sys.argv:
        try:
            app_index = sys.argv.index("--app") + 1
            app_id = sys.argv[app_index]
        except (IndexError, ValueError):
            app_id = "discord"
    else:
        app_id = "discord"

    app = ForensicsApp(elevated_launch=elevated_launch)
    app.selected_app_id = app_id if get_app(app_id)["status"] == "available" else "discord"
    if elevated_launch:
        app.after(350, lambda: app.start_workflow(skip_confirmation=True))
    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
