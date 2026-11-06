from __future__ import annotations

import io
import json
import sys
import threading
import urllib.parse
import webbrowser
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from fdctl import __contact__, __release__
from fdctl.app_catalog import APP_CATALOG, app_label, get_app
from fdctl.paths import workspace_root
from fdctl.services.license_service import (
    OWNER_EMAIL,
    OWNER_NAME,
    activate_license_token,
    current_license_status,
    machine_fingerprint,
    require_active_license,
    support_root,
)
from fdctl.utils import is_admin, rerun_as_admin


PRODUCT_NAME = "Forensics Suite"
COLORS = {
    "navy": "#101828",
    "navy_light": "#1D2939",
    "blue": "#175CD3",
    "blue_hover": "#1849A9",
    "canvas": "#F2F4F7",
    "white": "#FFFFFF",
    "ink": "#101828",
    "muted": "#667085",
    "line": "#EAECF0",
    "green": "#067647",
    "green_bg": "#ECFDF3",
    "amber": "#B54708",
    "amber_bg": "#FFFAEB",
    "red": "#B42318",
}

TEXT = {
    "vi": {
        "window": "Forensics Suite | Điều tra số",
        "brand_subtitle": "NỀN TẢNG ĐIỀU TRA SỐ",
        "nav": ["Tổng quan", "Demo dữ liệu", "Cases & báo cáo", "License", "Cài đặt", "Trợ giúp"],
        "page_subtitles": [
            "Không gian làm việc cho quy trình thu thập và phân tích số.",
            "Khám phá giao diện bằng một hồ sơ mô phỏng có dữ liệu sẵn.",
            "Duyệt hồ sơ điều tra và báo cáo trong workspace.",
            "Kích hoạt quyền sử dụng gắn với thiết bị này.",
            "Tùy chỉnh vị trí lưu hồ sơ và ngôn ngữ giao diện.",
            "Thông tin phiên bản, quyền riêng tư và hướng dẫn sử dụng.",
        ],
        "overview": "Không gian điều tra",
        "hero_title": "Digital Forensics Workspace",
        "hero_subtitle": "Một giao diện thống nhất cho các ứng dụng forensic hiện tại và tương lai.",
        "choose_app": "Ứng dụng cần điều tra",
        "app_supported": "ĐÃ HỖ TRỢ",
        "app_planned": "ĐANG PHÁT TRIỂN",
        "app_details": "Chọn một ứng dụng để xem trạng thái hỗ trợ và bắt đầu quy trình.",
        "start": "Bắt đầu điều tra",
        "supported_now": "Ứng dụng sẵn sàng",
        "planned_apps": "Ứng dụng trong lộ trình",
        "workspace": "Workspace",
        "current_license": "Quyền sử dụng",
        "open_workspace": "Mở workspace",
        "demo_title": "Demo dữ liệu",
        "demo_subtitle": "Hồ sơ mẫu tích hợp sẵn — không truy cập dữ liệu trên máy.",
        "sample_badge": "DỮ LIỆU MÔ PHỎNG · SAMPLE",
        "sample_case": "Hồ sơ mô phỏng",
        "sample_case_name": "Tabletop Response Exercise",
        "sample_case_id": "CASE-SAMPLE-0142",
        "sample_scope": "Kênh #ops-tabletop · 08:15–09:05 · 12/05/2026",
        "metric_messages": "Tin nhắn mẫu",
        "metric_participants": "Tài khoản giả lập",
        "metric_files": "Tệp minh họa",
        "metric_events": "Sự kiện timeline",
        "timeline": "Timeline hội thoại",
        "time": "Thời gian",
        "participant": "Tài khoản giả lập",
        "message": "Nội dung mô phỏng",
        "channel": "Kênh",
        "artifacts": "Tệp minh họa",
        "file_name": "Tên tệp",
        "file_type": "Loại",
        "file_note": "Mục đích",
        "report_preview": "Tóm tắt hồ sơ",
        "report_text": "Kịch bản tabletop hư cấu. Tài khoản, hội thoại và tệp chỉ dùng minh họa; không phải người dùng hay chứng cứ thật.",
        "demo_notice": "SAMPLE — dữ liệu tổng hợp cố định, không đọc Discord, Zalo, trình duyệt hoặc tệp cá nhân; không tạo chứng cứ forensic.",
        "cases": "Cases & báo cáo",
        "case_folder": "Thư mục cases",
        "recent_cases": "Hồ sơ gần đây",
        "no_cases": "Chưa có hồ sơ trong workspace này.",
        "open_folder": "Mở thư mục",
        "license": "License",
        "license_state": "Trạng thái license",
        "email": "Gmail đăng ký",
        "key": "License key",
        "activate": "Kích hoạt license",
        "trial": "Bắt đầu dùng thử 7 ngày",
        "request_key": "Gửi yêu cầu cấp license",
        "device": "Mã thiết bị",
        "owner": f"Chủ sở hữu: {OWNER_NAME} · {OWNER_EMAIL}",
        "settings": "Cài đặt",
        "workspace_path": "Thư mục lưu case và báo cáo",
        "browse": "Chọn thư mục…",
        "save": "Lưu cài đặt",
        "language": "Ngôn ngữ giao diện",
        "help": "Trợ giúp & thông tin",
        "about_text": "Forensics Suite được thiết kế để mở rộng theo từng adapter ứng dụng. Hiện Discord là adapter forensic sẵn sàng; các tích hợp khác được bổ sung theo từng giai đoạn.",
        "cli_title": "Dành cho người dùng source",
        "cli_help": "Clone repository, cài requirements.txt rồi chạy fdctl.cmd menu trong terminal.",
        "version": f"Phiên bản {__release__}",
        "ready": "Sẵn sàng",
        "run": "Đang chạy quy trình…",
        "done": "Quy trình hoàn tất.",
        "admin": "Thu thập có thể cần quyền Administrator. Ứng dụng sẽ yêu cầu mở lại với quyền phù hợp.",
        "unsupported_title": "Ứng dụng chưa được hỗ trợ",
        "unsupported": "Ứng dụng này đang trong giai đoạn phát triển. Hiện chưa có quy trình thu thập hoặc phân tích cụ thể. Bạn có thể chọn Discord để tiếp tục.",
        "need_license": "Cần license có quyền thu thập để bắt đầu điều tra.",
        "confirm_start": "Bắt đầu quy trình thu thập trên thiết bị này? Chỉ thu thập dữ liệu mà bạn có quyền truy cập.",
        "saved": "Đã lưu cài đặt.",
        "activated": "Kích hoạt license thành công.",
        "missing_email": "Hãy nhập Gmail trước.",
        "license_request_subject": "Yêu cầu license Forensics Suite",
    },
    "en": {
        "window": "Forensics Suite | Digital Investigations",
        "brand_subtitle": "DIGITAL FORENSICS PLATFORM",
        "nav": ["Overview", "Data demo", "Cases & reports", "License", "Settings", "Help"],
        "page_subtitles": [
            "Workspace for digital collection, analysis, and reporting.",
            "Explore the interface with a populated sample investigation.",
            "Browse investigation cases and reports in your workspace.",
            "Activate access for this device.",
            "Choose where cases are stored and set the interface language.",
            "Version, privacy, and usage information.",
        ],
        "overview": "Investigation workspace",
        "hero_title": "Digital Forensics Workspace",
        "hero_subtitle": "One interface for current and future application forensics.",
        "choose_app": "Application to investigate",
        "app_supported": "SUPPORTED",
        "app_planned": "IN DEVELOPMENT",
        "app_details": "Select an application to view its support status and start a workflow.",
        "start": "Start investigation",
        "supported_now": "Available apps",
        "planned_apps": "On the roadmap",
        "workspace": "Workspace",
        "current_license": "Access status",
        "open_workspace": "Open workspace",
        "demo_title": "Data demo",
        "demo_subtitle": "Built-in sample case — no data on this computer is accessed.",
        "sample_badge": "SYNTHETIC DATA · SAMPLE",
        "sample_case": "Sample investigation",
        "sample_case_name": "Tabletop Response Exercise",
        "sample_case_id": "CASE-SAMPLE-0142",
        "sample_scope": "Channel #ops-tabletop · 08:15–09:05 · May 12, 2026",
        "metric_messages": "Sample messages",
        "metric_participants": "Synthetic accounts",
        "metric_files": "Illustrative files",
        "metric_events": "Timeline events",
        "timeline": "Conversation timeline",
        "time": "Time",
        "participant": "Synthetic account",
        "message": "Synthetic message",
        "channel": "Channel",
        "artifacts": "Illustrative files",
        "file_name": "File name",
        "file_type": "Type",
        "file_note": "Purpose",
        "report_preview": "Case summary",
        "report_text": "Fictional tabletop scenario. Accounts, messages, and files are illustrative only; they are not real users or evidence.",
        "demo_notice": "SAMPLE — fixed synthetic content. The demo does not read Discord, Zalo, browsers, or personal files and does not create forensic evidence.",
        "cases": "Cases & reports",
        "case_folder": "Cases folder",
        "recent_cases": "Recent cases",
        "no_cases": "There are no cases in this workspace yet.",
        "open_folder": "Open folder",
        "license": "License",
        "license_state": "License status",
        "email": "Registered Gmail",
        "key": "License key",
        "activate": "Activate license",
        "trial": "Start 7-day trial",
        "request_key": "Request a license",
        "device": "Device ID",
        "owner": f"Owner: {OWNER_NAME} · {OWNER_EMAIL}",
        "settings": "Settings",
        "workspace_path": "Case and report storage folder",
        "browse": "Choose folder…",
        "save": "Save settings",
        "language": "Interface language",
        "help": "Help & about",
        "about_text": "Forensics Suite is designed to expand through per-application adapters. Discord is the currently available forensic adapter; other integrations will be added in stages.",
        "cli_title": "For source users",
        "cli_help": "Clone the repository, install requirements.txt, and run fdctl.cmd menu in a terminal.",
        "version": f"Version {__release__}",
        "ready": "Ready",
        "run": "Running workflow…",
        "done": "Workflow complete.",
        "admin": "Collection may require Administrator privileges. The app will request a restart with the required access.",
        "unsupported_title": "Application not supported yet",
        "unsupported": "This integration is under development. Collection and analysis workflows are not available yet. Select Discord to continue.",
        "need_license": "An active collection license is required to start an investigation.",
        "confirm_start": "Start collection on this device? Only collect data you are authorized to access.",
        "saved": "Settings saved.",
        "activated": "License activated successfully.",
        "missing_email": "Enter your Gmail address first.",
        "license_request_subject": "Forensics Suite license request",
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
    ("sample-note.txt", "Text", "Demo note"),
    ("sample-map.png", "Image", "Illustration"),
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
        self.selected_app_var = tk.StringVar()
        self.license_badge_var = tk.StringVar()
        self.status_var = tk.StringVar(value=TEXT[self.lang]["ready"])
        self.progress: ttk.Progressbar | None = None
        self.nav_buttons: list[ttk.Button] = []
        self._configure_style()
        self._build_shell()
        self.show_page(0)

    def _configure_style(self) -> None:
        self.title(TEXT[self.lang]["window"])
        self.geometry("1180x780")
        self.minsize(1000, 680)
        self.configure(background=COLORS["canvas"])
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background=COLORS["canvas"])
        style.configure("Canvas.TFrame", background=COLORS["canvas"])
        style.configure("Card.TFrame", background=COLORS["white"], relief="flat")
        style.configure("Sidebar.TFrame", background=COLORS["navy"])
        style.configure("TLabel", background=COLORS["canvas"], foreground=COLORS["ink"], font=("Segoe UI", 10))
        style.configure("Card.TLabel", background=COLORS["white"], foreground=COLORS["ink"], font=("Segoe UI", 10))
        style.configure("Sidebar.TLabel", background=COLORS["navy"], foreground="#D0D5DD", font=("Segoe UI", 9))
        style.configure("Brand.TLabel", background=COLORS["navy"], foreground=COLORS["white"], font=("Segoe UI", 17, "bold"))
        style.configure("BrandSub.TLabel", background=COLORS["navy"], foreground="#98A2B3", font=("Segoe UI", 8, "bold"))
        style.configure("PageTitle.TLabel", background=COLORS["canvas"], foreground=COLORS["ink"], font=("Segoe UI", 22, "bold"))
        style.configure("SectionTitle.TLabel", background=COLORS["white"], foreground=COLORS["ink"], font=("Segoe UI", 12, "bold"))
        style.configure("Muted.TLabel", background=COLORS["white"], foreground=COLORS["muted"], font=("Segoe UI", 9))
        style.configure("CanvasMuted.TLabel", background=COLORS["canvas"], foreground=COLORS["muted"], font=("Segoe UI", 9))
        style.configure("MetricValue.TLabel", background=COLORS["white"], foreground=COLORS["ink"], font=("Segoe UI", 22, "bold"))
        style.configure("Badge.TLabel", background=COLORS["green_bg"], foreground=COLORS["green"], font=("Segoe UI", 8, "bold"), padding=(9, 5))
        style.configure("SampleBadge.TLabel", background=COLORS["amber_bg"], foreground=COLORS["amber"], font=("Segoe UI", 8, "bold"), padding=(10, 5))
        style.configure("Nav.TButton", background=COLORS["navy"], foreground="#D0D5DD", anchor="w", padding=(14, 11), borderwidth=0, font=("Segoe UI", 10))
        style.map("Nav.TButton", background=[("active", COLORS["navy_light"])], foreground=[("active", COLORS["white"])])
        style.configure("NavActive.TButton", background=COLORS["navy_light"], foreground=COLORS["white"], anchor="w", padding=(14, 11), borderwidth=0, font=("Segoe UI", 10, "bold"))
        style.map("NavActive.TButton", background=[("active", COLORS["navy_light"])])
        style.configure("Primary.TButton", background=COLORS["blue"], foreground=COLORS["white"], padding=(16, 10), borderwidth=0, font=("Segoe UI", 10, "bold"))
        style.map("Primary.TButton", background=[("active", COLORS["blue_hover"])], foreground=[("disabled", "#D0D5DD")])
        style.configure("Secondary.TButton", background=COLORS["white"], foreground=COLORS["ink"], padding=(13, 9), borderwidth=1, relief="solid", font=("Segoe UI", 9, "bold"))
        style.configure("TEntry", padding=(9, 8), fieldbackground=COLORS["white"], bordercolor=COLORS["line"])
        style.configure("TCombobox", padding=(8, 7), fieldbackground=COLORS["white"])
        style.configure("Treeview", background=COLORS["white"], fieldbackground=COLORS["white"], foreground=COLORS["ink"], rowheight=32, borderwidth=0, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", background="#F9FAFB", foreground=COLORS["muted"], relief="flat", font=("Segoe UI", 8, "bold"), padding=(8, 8))
        style.map("Treeview", background=[("selected", "#EFF8FF")], foreground=[("selected", COLORS["ink"])])

    def _build_shell(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.sidebar = ttk.Frame(self, style="Sidebar.TFrame", width=244, padding=(15, 18))
        self.sidebar.grid(row=0, column=0, sticky="ns")
        self.sidebar.grid_propagate(False)
        self.main = ttk.Frame(self, style="Canvas.TFrame")
        self.main.grid(row=0, column=1, sticky="nsew")
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(1, weight=1)

        brand = ttk.Frame(self.sidebar, style="Sidebar.TFrame")
        brand.pack(fill="x", pady=(4, 27))
        icon = tk.Label(brand, text="FS", bg=COLORS["blue"], fg="white", font=("Segoe UI", 13, "bold"), width=3, height=1, pady=8)
        icon.pack(side="left", padx=(0, 10))
        brand_text = ttk.Frame(brand, style="Sidebar.TFrame")
        brand_text.pack(side="left", fill="x", expand=True)
        ttk.Label(brand_text, text="FORENSICS SUITE", style="Brand.TLabel").pack(anchor="w")
        ttk.Label(brand_text, text=TEXT[self.lang]["brand_subtitle"], style="BrandSub.TLabel").pack(anchor="w", pady=(2, 0))

        self.nav_container = ttk.Frame(self.sidebar, style="Sidebar.TFrame")
        self.nav_container.pack(fill="x")
        self.lang_button = ttk.Button(self.sidebar, text="English", style="Nav.TButton", command=self.toggle_language)
        self.lang_button.pack(side="bottom", fill="x", pady=(14, 0))
        ttk.Separator(self.sidebar).pack(side="bottom", fill="x", pady=12)
        self.sidebar_status = ttk.Label(self.sidebar, textvariable=self.status_var, style="Sidebar.TLabel", wraplength=200)
        self.sidebar_status.pack(side="bottom", anchor="w", pady=(0, 2))

        self.header = ttk.Frame(self.main, style="Canvas.TFrame", padding=(30, 23, 30, 13))
        self.header.grid(row=0, column=0, sticky="ew")
        self.header.grid_columnconfigure(0, weight=1)
        title_stack = ttk.Frame(self.header, style="Canvas.TFrame")
        title_stack.grid(row=0, column=0, sticky="w")
        self.page_title_var = tk.StringVar()
        self.page_subtitle_var = tk.StringVar()
        ttk.Label(title_stack, textvariable=self.page_title_var, style="PageTitle.TLabel").pack(anchor="w")
        ttk.Label(title_stack, textvariable=self.page_subtitle_var, style="CanvasMuted.TLabel").pack(anchor="w", pady=(4, 0))
        self.license_badge = ttk.Label(self.header, textvariable=self.license_badge_var, style="Badge.TLabel")
        self.license_badge.grid(row=0, column=1, sticky="e", padx=(12, 8))
        self.lang_toggle_top = ttk.Button(self.header, text="EN", style="Secondary.TButton", command=self.toggle_language)
        self.lang_toggle_top.grid(row=0, column=2, sticky="e")

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
            button = ttk.Button(self.nav_container, text=label, style="Nav.TButton", command=lambda i=index: self.show_page(i))
            button.pack(fill="x", pady=3)
            self.nav_buttons.append(button)
        self.lang_button.configure(text="Tiếng Việt" if self.lang == "en" else "English")
        self.lang_toggle_top.configure(text="VI" if self.lang == "en" else "EN")

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
            self.license_badge.configure(style="Badge.TLabel" if status.get("active") else "SampleBadge.TLabel")

    def clear_content(self) -> None:
        for widget in self.content.winfo_children():
            widget.destroy()

    def set_page_header(self, index: int) -> None:
        titles = TEXT[self.lang]["nav"]
        self.page_title_var.set(titles[index])
        self.page_subtitle_var.set(TEXT[self.lang]["page_subtitles"][index])
        for current, button in enumerate(self.nav_buttons):
            button.configure(style="NavActive.TButton" if current == index else "Nav.TButton")

    @staticmethod
    def card(parent: ttk.Widget, padding: int = 18) -> ttk.Frame:
        return ttk.Frame(parent, style="Card.TFrame", padding=padding)

    def section_label(self, parent: ttk.Widget, text: str, style: str = "SectionTitle.TLabel") -> ttk.Label:
        label = ttk.Label(parent, text=text, style=style)
        label.pack(anchor="w")
        return label

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

    def _show_overview(self) -> None:
        t = TEXT[self.lang]
        hero = self.card(self.content, padding=23)
        hero.pack(fill="x", pady=(0, 17))
        hero.grid_columnconfigure(0, weight=1)
        ttk.Label(hero, text=t["hero_title"], style="SectionTitle.TLabel", font=("Segoe UI", 18, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(hero, text=t["hero_subtitle"], style="Muted.TLabel", wraplength=650).grid(row=1, column=0, sticky="w", pady=(7, 15))
        ttk.Label(hero, text=t["choose_app"], style="Card.TLabel", font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky="w", pady=(0, 6))
        self.app_combo = ttk.Combobox(hero, state="readonly", textvariable=self.selected_app_var, width=38)
        self.app_combo.grid(row=3, column=0, sticky="w")
        self._set_app_options()
        self.app_combo.bind("<<ComboboxSelected>>", self._on_app_selected)
        self.app_status_label = ttk.Label(hero, text="", style="Badge.TLabel")
        self.app_status_label.grid(row=3, column=1, sticky="w", padx=(11, 0))
        ttk.Label(hero, text=t["app_details"], style="Muted.TLabel").grid(row=4, column=0, sticky="w", pady=(8, 0))
        actions = ttk.Frame(hero, style="Card.TFrame")
        actions.grid(row=5, column=0, sticky="w", pady=(17, 0))
        ttk.Button(actions, text=t["start"], style="Primary.TButton", command=self.start_workflow).pack(side="left")
        ttk.Button(actions, text=t["open_workspace"], style="Secondary.TButton", command=lambda: self.open_path(Path(self.workspace_var.get()))).pack(side="left", padx=9)

        metrics = ttk.Frame(self.content, style="Canvas.TFrame")
        metrics.pack(fill="x", pady=(0, 17))
        for col in range(3):
            metrics.grid_columnconfigure(col, weight=1, uniform="metric")
        self._metric(metrics, 0, str(sum(1 for item in APP_CATALOG if item["status"] == "available")), t["supported_now"], "●", COLORS["green"])
        self._metric(metrics, 1, str(sum(1 for item in APP_CATALOG if item["status"] != "available")), t["planned_apps"], "◷", COLORS["amber"])
        short_workspace = Path(self.workspace_var.get()).name or str(self.workspace_var.get())
        self._metric(metrics, 2, short_workspace, t["workspace"], "▣", COLORS["blue"], small=True)

        note = self.card(self.content, padding=17)
        note.pack(fill="x")
        ttk.Label(note, text=t["about_text"], style="Muted.TLabel", wraplength=840, justify="left").pack(anchor="w")
        self._update_selected_app_status()

    def _metric(self, parent: ttk.Frame, column: int, value: str, label: str, icon: str, accent: str, small: bool = False) -> None:
        card = self.card(parent, padding=16)
        card.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 7, 7 if column < 2 else 0))
        tk.Label(card, text=icon, bg=COLORS["white"], fg=accent, font=("Segoe UI", 13, "bold")).pack(anchor="w")
        ttk.Label(card, text=value, style="MetricValue.TLabel", font=("Segoe UI", 14 if small else 22, "bold")).pack(anchor="w", pady=(7, 1))
        ttk.Label(card, text=label, style="Muted.TLabel").pack(anchor="w")

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
        if not hasattr(self, "app_status_label"):
            return
        app = get_app(self.selected_app_id)
        text = TEXT[self.lang]["app_supported"] if app["status"] == "available" else TEXT[self.lang]["app_planned"]
        style = "Badge.TLabel" if app["status"] == "available" else "SampleBadge.TLabel"
        self.app_status_label.configure(text=text, style=style)

    def _show_demo(self) -> None:
        t = TEXT[self.lang]
        head = ttk.Frame(self.content, style="Canvas.TFrame")
        head.pack(fill="x", pady=(0, 15))
        head.grid_columnconfigure(0, weight=1)
        ttk.Label(head, text=t["demo_subtitle"], style="CanvasMuted.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(head, text=t["sample_badge"], style="SampleBadge.TLabel").grid(row=0, column=1, sticky="e")

        case_card = self.card(self.content, padding=18)
        case_card.pack(fill="x", pady=(0, 12))
        case_card.grid_columnconfigure(0, weight=1)
        ttk.Label(case_card, text=t["sample_case"], style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(case_card, text=t["sample_case_name"], style="SectionTitle.TLabel", font=("Segoe UI", 15, "bold")).grid(row=1, column=0, sticky="w", pady=(3, 2))
        ttk.Label(case_card, text=f"{t['sample_case_id']}  ·  Discord  ·  {t['sample_scope']}", style="Muted.TLabel").grid(row=2, column=0, sticky="w")

        metrics = ttk.Frame(self.content, style="Canvas.TFrame")
        metrics.pack(fill="x", pady=(0, 12))
        for col in range(4):
            metrics.grid_columnconfigure(col, weight=1, uniform="demo-metric")
        counts = [
            (str(len(DEMO_MESSAGES)), t["metric_messages"]),
            ("3", t["metric_participants"]),
            (str(len(DEMO_FILES)), t["metric_files"]),
            ("4", t["metric_events"]),
        ]
        for col, (value, label) in enumerate(counts):
            card = self.card(metrics, padding=13)
            card.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 5, 5 if col < 3 else 0))
            ttk.Label(card, text=value, style="MetricValue.TLabel", font=("Segoe UI", 19, "bold")).pack(anchor="w")
            ttk.Label(card, text=label, style="Muted.TLabel", wraplength=150).pack(anchor="w", pady=(3, 0))

        columns = ttk.Frame(self.content, style="Canvas.TFrame")
        columns.pack(fill="both", expand=True, pady=(0, 12))
        columns.grid_columnconfigure(0, weight=3)
        columns.grid_columnconfigure(1, weight=2)
        columns.grid_rowconfigure(0, weight=1)
        timeline = self.card(columns, padding=14)
        timeline.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        self.section_label(timeline, t["timeline"])
        tree = ttk.Treeview(timeline, columns=("time", "participant", "channel", "message"), show="headings", height=7)
        tree.heading("time", text=t["time"])
        tree.heading("participant", text=t["participant"])
        tree.heading("channel", text=t["channel"])
        tree.heading("message", text=t["message"])
        tree.column("time", width=72, stretch=False)
        tree.column("participant", width=135, stretch=False)
        tree.column("channel", width=105, stretch=False)
        tree.column("message", width=310, stretch=True)
        tree.pack(fill="both", expand=True, pady=(12, 0))
        for row in DEMO_MESSAGES:
            message = row[3] if self.lang == "en" else self._translate_demo_message(row[3])
            tree.insert("", "end", values=(row[0], row[1], row[2], message))

        details = ttk.Frame(columns, style="Canvas.TFrame")
        details.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
        files_card = self.card(details, padding=14)
        files_card.pack(fill="x", pady=(0, 10))
        self.section_label(files_card, t["artifacts"])
        files_tree = ttk.Treeview(files_card, columns=("name", "type", "note"), show="headings", height=2)
        for col, title in (("name", t["file_name"]), ("type", t["file_type"]), ("note", t["file_note"])):
            files_tree.heading(col, text=title)
        files_tree.column("name", width=120, stretch=True)
        files_tree.column("type", width=55, stretch=False)
        files_tree.column("note", width=145, stretch=True)
        files_tree.pack(fill="x", pady=(10, 0))
        for filename, file_type, note in DEMO_FILES:
            display_note = self._translate_demo_file_note(note) if self.lang == "vi" else note
            files_tree.insert("", "end", values=(filename, file_type, display_note))

        report_card = self.card(details, padding=14)
        report_card.pack(fill="both", expand=True)
        self.section_label(report_card, t["report_preview"])
        report_text = t["report_text"]
        ttk.Label(report_card, text=report_text, style="Muted.TLabel", wraplength=330, justify="left").pack(anchor="w", pady=(10, 0))

        note = self.card(self.content, padding=12)
        note.pack(fill="x")
        ttk.Label(note, text=t["demo_notice"], style="Muted.TLabel", wraplength=900, justify="left").pack(anchor="w")

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
            "Demo note": "Ghi chú demo",
            "Illustration": "Minh họa",
        }.get(note, note)

    def _show_cases(self) -> None:
        t = TEXT[self.lang]
        folder = Path(self.workspace_var.get()) / "cases"
        top = self.card(self.content, padding=18)
        top.pack(fill="x", pady=(0, 14))
        top.grid_columnconfigure(0, weight=1)
        ttk.Label(top, text=t["case_folder"], style="SectionTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(top, text=str(folder), style="Muted.TLabel", wraplength=750).grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Button(top, text=t["open_folder"], style="Secondary.TButton", command=lambda: self.open_path(folder)).grid(row=0, column=1, rowspan=2, sticky="e")

        recent = self.card(self.content, padding=18)
        recent.pack(fill="both", expand=True)
        self.section_label(recent, t["recent_cases"])
        tree = ttk.Treeview(recent, columns=("case", "modified", "folder"), show="headings", height=12)
        tree.heading("case", text="Case ID")
        tree.heading("modified", text="Modified")
        tree.heading("folder", text=t["case_folder"])
        tree.column("case", width=180, stretch=False)
        tree.column("modified", width=190, stretch=False)
        tree.column("folder", width=440, stretch=True)
        tree.pack(fill="both", expand=True, pady=(11, 0))
        cases = sorted((path for path in folder.iterdir() if path.is_dir()), key=lambda path: path.stat().st_mtime, reverse=True)[:100] if folder.exists() else []
        if not cases:
            tree.insert("", "end", values=(t["no_cases"], "", ""))
        else:
            for path in cases:
                modified = path.stat().st_mtime
                from datetime import datetime
                tree.insert("", "end", values=(path.name, datetime.fromtimestamp(modified).strftime("%Y-%m-%d %H:%M"), str(path)))
        tree.bind("<Double-1>", lambda _event: self._open_selected_case(tree, folder))

    def _open_selected_case(self, tree: ttk.Treeview, cases_dir: Path) -> None:
        selection = tree.selection()
        if selection:
            values = tree.item(selection[0], "values")
            if values and values[0] != TEXT[self.lang]["no_cases"]:
                self.open_path(cases_dir / str(values[0]))

    def _show_license(self) -> None:
        t = TEXT[self.lang]
        status = current_license_status(selected_email=self.email_var.get())
        top = self.card(self.content, padding=20)
        top.pack(fill="x", pady=(0, 14))
        ttk.Label(top, text=t["license_state"], style="SectionTitle.TLabel").pack(anchor="w")
        state_text = str(status.get("licenseLabel") or t["ready"])
        ttk.Label(top, text=state_text, style="Badge.TLabel").pack(anchor="w", pady=(9, 5))
        expiry = str(status.get("expiresAt") or "")
        ttk.Label(top, text=expiry, style="Muted.TLabel").pack(anchor="w")

        form = self.card(self.content, padding=20)
        form.pack(fill="x", pady=(0, 14))
        form.grid_columnconfigure(0, weight=1)
        ttk.Label(form, text=t["email"], style="Card.TLabel", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.email_var).grid(row=1, column=0, sticky="ew", pady=(5, 12))
        ttk.Label(form, text=t["key"], style="Card.TLabel", font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.key_var, show="•").grid(row=3, column=0, sticky="ew", pady=(5, 12))
        buttons = ttk.Frame(form, style="Card.TFrame")
        buttons.grid(row=4, column=0, sticky="w")
        ttk.Button(buttons, text=t["activate"], style="Primary.TButton", command=self.activate).pack(side="left")
        ttk.Button(buttons, text=t["trial"], style="Secondary.TButton", command=self.start_trial).pack(side="left", padx=8)
        ttk.Button(buttons, text=t["request_key"], style="Secondary.TButton", command=self.request_key).pack(side="left")

        details = self.card(self.content, padding=17)
        details.pack(fill="x")
        ttk.Label(details, text=f"{t['device']}: {machine_fingerprint()}", style="Muted.TLabel", wraplength=850).pack(anchor="w")
        ttk.Label(details, text=t["owner"], style="Muted.TLabel", wraplength=850).pack(anchor="w", pady=(9, 0))

    def _show_settings(self) -> None:
        t = TEXT[self.lang]
        card = self.card(self.content, padding=20)
        card.pack(fill="x", pady=(0, 14))
        ttk.Label(card, text=t["workspace_path"], style="SectionTitle.TLabel").pack(anchor="w")
        row = ttk.Frame(card, style="Card.TFrame")
        row.pack(fill="x", pady=(10, 0))
        ttk.Entry(row, textvariable=self.workspace_var).pack(side="left", fill="x", expand=True)
        ttk.Button(row, text=t["browse"], style="Secondary.TButton", command=self.browse_workspace).pack(side="left", padx=(9, 0))
        ttk.Label(card, text=t["language"], style="Card.TLabel", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(18, 6))
        lang_selector = ttk.Combobox(card, state="readonly", values=["Tiếng Việt", "English"], width=22)
        lang_selector.current(0 if self.lang == "vi" else 1)
        lang_selector.pack(anchor="w")
        lang_selector.bind("<<ComboboxSelected>>", lambda _event: self._change_language("vi" if lang_selector.current() == 0 else "en"))
        ttk.Button(card, text=t["save"], style="Primary.TButton", command=self.save_settings).pack(anchor="w", pady=(17, 0))

    def _change_language(self, language: str) -> None:
        if language != self.lang:
            self.lang = language
            self.settings["language"] = language
            self._write_settings()
            self.title(TEXT[self.lang]["window"])
            self._rebuild_nav()
            self.show_page(4)

    def _show_help(self) -> None:
        t = TEXT[self.lang]
        about = self.card(self.content, padding=20)
        about.pack(fill="x", pady=(0, 13))
        ttk.Label(about, text="Forensics Suite", style="SectionTitle.TLabel", font=("Segoe UI", 16, "bold")).pack(anchor="w")
        ttk.Label(about, text=t["about_text"], style="Muted.TLabel", wraplength=850, justify="left").pack(anchor="w", pady=(8, 15))
        ttk.Label(about, text=t["version"], style="Muted.TLabel").pack(anchor="w")
        ttk.Label(about, text=t["owner"], style="Muted.TLabel", wraplength=850).pack(anchor="w", pady=(6, 0))
        ttk.Label(about, text=f"Contact: {__contact__}", style="Muted.TLabel").pack(anchor="w", pady=(5, 0))

        cli = self.card(self.content, padding=20)
        cli.pack(fill="x")
        ttk.Label(cli, text=t["cli_title"], style="SectionTitle.TLabel").pack(anchor="w")
        ttk.Label(cli, text=t["cli_help"], style="Muted.TLabel", wraplength=850).pack(anchor="w", pady=(8, 0))
        command = tk.Text(cli, height=2, wrap="none", bg="#F9FAFB", fg=COLORS["ink"], relief="flat", font=("Cascadia Code", 10), padx=10, pady=8)
        command.insert("1.0", ".\\fdctl.cmd menu")
        command.configure(state="disabled")
        command.pack(fill="x", pady=(12, 0))

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
        self.progress = ttk.Progressbar(self.content, mode="indeterminate", length=390)
        self.progress.pack(anchor="w", pady=(13, 0))
        self.progress.start(12)
        threading.Thread(target=self._run_pipeline, args=(str(selected["id"]),), daemon=True).start()

    def _run_pipeline(self, app_id: str) -> None:
        try:
            if sys.platform == "win32" and not is_admin():
                self.after(0, lambda: self.status_var.set(TEXT[self.lang]["admin"]))
                rerun_as_admin(["--gui-elevated", "--app", app_id])
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                from fdctl.services.analysis_service import analyze_case
                from fdctl.services.case_service import create_case, save_case
                from fdctl.services.collection_service import collect_case
                from fdctl.services.report_service import build_report

                context = create_case(app_id)
                collect_case(context, elevated=self.elevated_launch)
                analyze_case(context)
                build_report(context)
                saved = save_case(context.case_id)
            self.after(0, lambda: self._finish_workflow(TEXT[self.lang]["done"]))
            self.after(0, lambda: self.open_path(saved.root))
        except SystemExit:
            self.after(0, lambda: self._finish_workflow(TEXT[self.lang]["admin"]))
        except Exception as exc:
            msg = str(exc)
            if "administrator" in msg.lower() or "access is denied" in msg.lower():
                msg = f"{TEXT[self.lang]['admin']}\n\n{msg}"
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

    def activate(self) -> None:
        try:
            status = activate_license_token(self.key_var.get(), self.email_var.get())
            messagebox.showinfo(TEXT[self.lang]["license"], f"{TEXT[self.lang]['activated']}\n{status.get('licenseLabel')}\n{status.get('expiresAt', '')}")
            self.key_var.set("")
            self.refresh_status()
        except Exception as exc:
            messagebox.showerror(TEXT[self.lang]["license"], str(exc))

    def start_trial(self) -> None:
        try:
            status = current_license_status(selected_email=self.email_var.get(), force_enforced=True)
            if not status.get("active"):
                raise ValueError(str(status.get("reason", "Could not start trial.")))
            self.refresh_status()
            messagebox.showinfo(TEXT[self.lang]["license"], f"{status.get('licenseLabel')}\n{status.get('expiresAt')}")
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
        if self.current_page == 0:
            self.show_page(0)

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
