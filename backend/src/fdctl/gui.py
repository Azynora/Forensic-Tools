from __future__ import annotations

import json
import io
import sys
import threading
import urllib.parse
import webbrowser
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from fdctl import __contact__, __release__
from fdctl.paths import workspace_root
from fdctl.services.license_service import (
    OWNER_EMAIL, OWNER_NAME, activate_license_token, current_license_status,
    machine_fingerprint, support_root, require_active_license,
)
from fdctl.utils import is_admin, rerun_as_admin


TEXT = {
    "vi": {
        "title": "FORENSICS_DISCORD | Công cụ điều tra số", "nav": ["Bắt đầu điều tra", "Demo", "Cases & Reports", "License / Mua license", "Cài đặt", "Hướng dẫn / About"],
        "home": "Điều tra Discord", "app": "Ứng dụng", "start": "Bắt đầu quy trình Discord", "zalo": "Zalo đang trong giai đoạn phát triển. Hiện chưa hỗ trợ thu thập hoặc phân tích Zalo. Bạn có thể chọn Discord forensic để tiếp tục.",
        "demo": "Demo dữ liệu tổng hợp (SAMPLE)", "demo_note": "Demo chỉ hiển thị dữ liệu giả lập trong ứng dụng. Không đọc Discord, Chrome hoặc thu thập chứng cứ.",
        "demo_unlock": "Nhập Gmail và bắt đầu trial tại trang License để mở demo SAMPLE.",
        "cases": "Thư mục case và báo cáo", "open": "Mở thư mục", "license": "License / yêu cầu cấp key", "email": "Gmail", "key": "License key", "activate": "Kích hoạt license", "buy": "Yêu cầu license qua email", "trial": "Bắt đầu trial 7 ngày", "device": "Mã thiết bị", "settings": "Thư mục workspace", "browse": "Chọn thư mục…", "save": "Lưu cài đặt", "help": "FORENSICS_DISCORD", "owner": f"Chủ sở hữu: {OWNER_NAME} <{OWNER_EMAIL}>", "version": f"Release {__release__}", "status": "Trạng thái", "ready": "Sẵn sàng", "bad": "Chưa có license hợp lệ", "activated": "Đã kích hoạt", "saved": "Đã lưu cài đặt.", "choose": "Chọn Discord forensic để tiếp tục.", "need_paid": "License hiện tại chỉ cho phép xem demo SAMPLE. Kích hoạt license trả phí để thu thập chứng cứ thật.", "run": "Đang chạy quy trình…", "done": "Đã hoàn tất quy trình.", "admin": "Thu thập có thể cần quyền Administrator. Hãy khởi chạy lại ứng dụng bằng Run as administrator.",
    },
    "en": {
        "title": "FORENSICS_DISCORD | Digital Forensics", "nav": ["Start Investigation", "Demo", "Cases & Reports", "License / Buy", "Settings", "Guide / About"],
        "home": "Discord investigation", "app": "Application", "start": "Start Discord workflow", "zalo": "Zalo support is under development. Zalo collection and analysis are not available yet. Select Discord forensic to continue.",
        "demo": "Synthetic data demo (SAMPLE)", "demo_note": "The demo displays synthetic data only. It never reads Discord or Chrome and does not collect evidence.",
        "demo_unlock": "Enter a Gmail address and start the trial on the License page to unlock the SAMPLE demo.",
        "cases": "Cases and reports folder", "open": "Open folder", "license": "License / request a key", "email": "Gmail address", "key": "License key", "activate": "Activate license", "buy": "Request license by email", "trial": "Start 7-day trial", "device": "Device code", "settings": "Workspace folder", "browse": "Choose folder…", "save": "Save settings", "help": "FORENSICS_DISCORD", "owner": f"Owner: {OWNER_NAME} <{OWNER_EMAIL}>", "version": f"Release {__release__}", "status": "Status", "ready": "Ready", "bad": "No valid license", "activated": "License activated", "saved": "Settings saved.", "choose": "Select Discord forensic to continue.", "need_paid": "The current license only unlocks the SAMPLE demo. Activate a paid license to collect real evidence.", "run": "Running workflow…", "done": "Workflow complete.", "admin": "Collection may require Administrator privileges. Restart the app using Run as administrator.",
    },
}


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
        saved_language = str(self.settings.get("language", "vi")).lower()
        self.lang = saved_language if saved_language in {"vi", "en"} else "vi"
        self.email_var = tk.StringVar(value=str(self.settings.get("licenseEmail", "")))
        self.key_var = tk.StringVar()
        self.workspace_var = tk.StringVar(value=str(self.settings.get("workspace", workspace_root())))
        self.status_var = tk.StringVar()
        self.progress: ttk.Progressbar | None = None
        self.nav_buttons: list[ttk.Button] = []
        self.body = ttk.Frame(self, padding=20)
        self.body.pack(fill="both", expand=True)
        self.sidebar = ttk.Frame(self, padding=(12, 16))
        self.sidebar.pack(side="left", fill="y", before=self.body)
        self.body.pack(side="right", fill="both", expand=True)
        self._build_nav()
        self.show_page(0)

    def _build_nav(self) -> None:
        self.title(TEXT[self.lang]["title"])
        self.geometry("980x650")
        self.minsize(780, 520)
        self.sidebar_title = ttk.Label(self.sidebar, text="FORENSICS\nDISCORD", font=("Segoe UI", 16, "bold"))
        self.sidebar_title.pack(anchor="w", pady=(0, 20))
        self.nav_container = ttk.Frame(self.sidebar)
        self.nav_container.pack(fill="x")
        for index, label in enumerate(TEXT[self.lang]["nav"]):
            btn = ttk.Button(self.nav_container, text=label, command=lambda i=index: self.show_page(i))
            btn.pack(fill="x", pady=3)
            self.nav_buttons.append(btn)
        ttk.Separator(self.sidebar).pack(fill="x", pady=14)
        self.lang_button = ttk.Button(self.sidebar, text="English", command=self.toggle_language)
        self.lang_button.pack(fill="x")
        self.status_label = ttk.Label(self.sidebar, textvariable=self.status_var, wraplength=180)
        self.status_label.pack(anchor="w", pady=16)
        self.refresh_status()

    def toggle_language(self) -> None:
        self.lang = "en" if self.lang == "vi" else "vi"
        self.settings["language"] = self.lang
        _settings_path().write_text(json.dumps(self.settings, ensure_ascii=False, indent=2), encoding="utf-8")
        for child in self.nav_container.winfo_children():
            child.destroy()
        self.nav_buttons.clear()
        for index, label in enumerate(TEXT[self.lang]["nav"]):
            btn = ttk.Button(self.nav_container, text=label, command=lambda i=index: self.show_page(i))
            btn.pack(fill="x", pady=3)
            self.nav_buttons.append(btn)
        self.title(TEXT[self.lang]["title"])
        self.lang_button.configure(text="Tiếng Việt" if self.lang == "en" else "English")
        self.show_page(0)

    def refresh_status(self) -> None:
        status = current_license_status(selected_email=self.email_var.get())
        self.status_var.set(f"{TEXT[self.lang]['status']}: {status.get('licenseLabel') or TEXT[self.lang]['bad']}\n{status.get('issuedToEmail', '')}")

    def clear_body(self) -> None:
        for widget in self.body.winfo_children():
            widget.destroy()

    def heading(self, text: str) -> None:
        ttk.Label(self.body, text=text, font=("Segoe UI", 20, "bold")).pack(anchor="w", pady=(0, 18))

    def show_page(self, page: int) -> None:
        self.clear_body()
        t = TEXT[self.lang]
        if page == 0:
            self.heading(t["home"])
            row = ttk.Frame(self.body); row.pack(fill="x", pady=8)
            ttk.Label(row, text=t["app"]).pack(side="left", padx=(0, 10))
            app = ttk.Combobox(row, state="readonly", values=["Discord forensic", "Zalo (đang phát triển)" if self.lang == "vi" else "Zalo (in development)"])
            app.current(0); app.pack(side="left")
            def selected(_event: object = None) -> None:
                if app.current() == 1:
                    messagebox.showinfo("Zalo", t["zalo"])
                    app.current(0)
            app.bind("<<ComboboxSelected>>", selected)
            ttk.Button(self.body, text=t["start"], command=self.start_workflow).pack(anchor="w", pady=16)
            ttk.Label(self.body, text=t["owner"]).pack(anchor="w", pady=(30, 4))
            ttk.Label(self.body, text=t["version"]).pack(anchor="w")
        elif page == 1:
            self.heading(t["demo"])
            ttk.Label(self.body, text=t["demo_note"], wraplength=680).pack(anchor="w", pady=(0, 14))
            status = current_license_status(selected_email=self.email_var.get())
            if not status.get("active"):
                ttk.Label(self.body, text=t["demo_unlock"], foreground="#a33", wraplength=680).pack(anchor="w")
                ttk.Button(self.body, text=t["nav"][3], command=lambda: self.show_page(3)).pack(anchor="w", pady=8)
                return
            ttk.Button(self.body, text="Show SAMPLE" if self.lang == "en" else "Xem SAMPLE", command=self.show_sample).pack(anchor="w")
        elif page == 2:
            self.heading(t["cases"])
            cases_dir = Path(self.workspace_var.get()) / "cases"
            ttk.Label(self.body, text=str(cases_dir), wraplength=680).pack(anchor="w", pady=8)
            ttk.Button(self.body, text=t["open"], command=lambda: self.open_path(cases_dir)).pack(anchor="w", pady=(0, 12))
            for case_path in sorted((p for p in cases_dir.iterdir() if p.is_dir()), key=lambda p: p.name, reverse=True)[:30] if cases_dir.exists() else []:
                ttk.Button(self.body, text=case_path.name, command=lambda p=case_path: self.open_path(p)).pack(anchor="w", fill="x", pady=2)
        elif page == 3:
            self.heading(t["license"])
            ttk.Label(self.body, text=t["email"]).pack(anchor="w")
            ttk.Entry(self.body, textvariable=self.email_var, width=50).pack(anchor="w", pady=(2, 10))
            ttk.Label(self.body, text=t["key"]).pack(anchor="w")
            ttk.Entry(self.body, textvariable=self.key_var, width=50, show="•").pack(anchor="w", pady=(2, 10))
            ttk.Button(self.body, text=t["activate"], command=self.activate).pack(anchor="w", pady=4)
            ttk.Button(self.body, text=t["trial"], command=self.start_trial).pack(anchor="w", pady=4)
            ttk.Button(self.body, text=t["buy"], command=self.request_key).pack(anchor="w", pady=4)
            ttk.Label(self.body, text=f"{t['device']}: {machine_fingerprint()}", wraplength=680).pack(anchor="w", pady=(12, 4))
            ttk.Label(self.body, text=t["owner"]).pack(anchor="w", pady=(24, 4))
        elif page == 4:
            self.heading(t["settings"])
            row = ttk.Frame(self.body); row.pack(fill="x")
            ttk.Entry(row, textvariable=self.workspace_var).pack(side="left", fill="x", expand=True)
            ttk.Button(row, text=t["browse"], command=self.browse_workspace).pack(side="left", padx=8)
            ttk.Button(self.body, text=t["save"], command=self.save_settings).pack(anchor="w", pady=12)
        else:
            self.heading(t["help"])
            ttk.Label(self.body, text=t["version"]).pack(anchor="w", pady=3)
            ttk.Label(self.body, text=t["owner"]).pack(anchor="w", pady=3)
            ttk.Label(self.body, text=f"Contact: {__contact__}" if self.lang == "en" else f"Liên hệ: {__contact__}").pack(anchor="w", pady=3)
            ttk.Label(self.body, text="CLI: fdctl.cmd menu" if self.lang == "en" else "CLI: fdctl.cmd menu").pack(anchor="w", pady=3)

    def show_sample(self) -> None:
        if self.lang == "vi":
            rows = "[SAMPLE] 2026-01-12 08:21 | user_demo_01 | Chào bạn\n[SAMPLE] 2026-01-12 08:23 | user_demo_02 | Đây là dữ liệu giả lập."
        else:
            rows = "[SAMPLE] 2026-01-12 08:21 | user_demo_01 | Hello\n[SAMPLE] 2026-01-12 08:23 | user_demo_02 | This is synthetic data."
        messagebox.showinfo("SAMPLE", rows)

    def start_workflow(self, skip_confirmation: bool = False) -> None:
        try:
            status = current_license_status(selected_email=self.email_var.get())
            if "collection" not in status.get("features", []) and "owner" not in status.get("features", []):
                self.show_page(3); messagebox.showwarning("License", TEXT[self.lang]["need_paid"]); return
            require_active_license("collection")
        except Exception as exc:
            messagebox.showerror("License", str(exc)); self.show_page(3); return
        if not skip_confirmation and not messagebox.askyesno("FORENSICS_DISCORD", "Start Discord collection on this device?\nOnly collect data you are authorized to access."):
            return
        self.status_var.set(TEXT[self.lang]["run"])
        self.progress = ttk.Progressbar(self.body, mode="indeterminate", length=360)
        self.progress.pack(anchor="w", pady=12)
        self.progress.start(12)
        threading.Thread(target=self._run_pipeline, daemon=True).start()

    def _run_pipeline(self) -> None:
        try:
            if sys.platform == "win32" and not is_admin():
                self.after(0, lambda: self.status_var.set(TEXT[self.lang]["admin"]))
                rerun_as_admin(["--gui-elevated"])
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                from fdctl.services.analysis_service import analyze_case
                from fdctl.services.case_service import create_case, save_case
                from fdctl.services.collection_service import collect_case
                from fdctl.services.report_service import build_report
                context = create_case("discord")
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
            self.after(0, lambda m=msg: messagebox.showerror("FORENSICS_DISCORD", m))
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
            messagebox.showinfo("License", f"{TEXT[self.lang]['activated']}\n{status.get('licenseLabel')}\n{status.get('expiresAt', '')}")
            self.key_var.set("")
            self.refresh_status()
        except Exception as exc:
            messagebox.showerror("License", str(exc))

    def start_trial(self) -> None:
        try:
            status = current_license_status(selected_email=self.email_var.get(), force_enforced=True)
            if not status.get("active"):
                raise ValueError(str(status.get("reason", "Could not start trial.")))
            self.refresh_status()
            messagebox.showinfo("License", f"{status.get('licenseLabel')}\n{status.get('expiresAt')}")
        except Exception as exc:
            messagebox.showerror("License", str(exc))

    def request_key(self) -> None:
        email = self.email_var.get().strip()
        if not email:
            messagebox.showwarning("License", "Enter your Gmail address first.")
            return
        subject = "FORENSICS_DISCORD license request"
        body = f"Email: {email}\nDevice fingerprint: {machine_fingerprint()}\nRequested: 7 / 30 / 365-day license"
        url = f"mailto:{OWNER_EMAIL}?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
        webbrowser.open(url)

    def browse_workspace(self) -> None:
        selected = filedialog.askdirectory(initialdir=self.workspace_var.get() or str(Path.home() / "Documents"))
        if selected:
            self.workspace_var.set(selected)

    def save_settings(self) -> None:
        self.settings.update({"workspace": self.workspace_var.get(), "licenseEmail": self.email_var.get()})
        _settings_path().write_text(json.dumps(self.settings, ensure_ascii=False, indent=2), encoding="utf-8")
        self.refresh_status()
        messagebox.showinfo("FORENSICS_DISCORD", TEXT[self.lang]["saved"])

    @staticmethod
    def open_path(path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)
        webbrowser.open(path.as_uri())


def main() -> int:
    elevated_launch = len(sys.argv) > 1 and sys.argv[1] == "--gui-elevated"
    app = ForensicsApp(elevated_launch=elevated_launch)
    if elevated_launch:
        app.after(350, lambda: app.start_workflow(skip_confirmation=True))
    app.mainloop()
    return 0
