from __future__ import annotations
import argparse
import ctypes
import json
import os
import sys
from typing import Any
from pathlib import Path
from fdctl import __release__
from fdctl.adapters import get_adapters
from fdctl.console import StageProgress, clear_screen, print_banner, print_copyright_notice, print_kv, print_section, print_status, setup_terminal
from fdctl.paths import project_root, workspace_root
from fdctl.services.app_service import open_application
from fdctl.services.analysis_service import analyze_case
from fdctl.services.case_service import create_case, discard_case, load_case, save_case
from fdctl.services.collection_service import collect_case
from fdctl.services.ide_service import open_workspace
from fdctl.services.license_service import (
    activate_license_token,
    current_license_status,
    deactivate_license,
    format_machine_name,
    last_used_email,
    license_types_summary,
    license_usage_history,
    machine_fingerprint,
    require_bundle_access,
    verify_bundle_integrity,
)
from fdctl.services.report_service import build_report, open_report
from fdctl.services.supplement_service import run_supplemental_checks, validate_report_bundle
from fdctl.utils import is_admin, rerun_as_admin

def _print(data: object) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))

def _styled_banner() -> None:
    print_banner("FORENSIC SUITE", "Cross-platform extensible digital forensics workspace")
    sys.stdout.flush()

def _settings_file_path() -> Path:
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    if local_appdata:
        p_suite = Path(local_appdata) / "FORENSIC_SUITE" / "settings.json"
        p_disc = Path(local_appdata) / "FORENSICS_DISCORD" / "settings.json"
        return p_suite if p_suite.exists() or not p_disc.exists() else p_disc
    xdg_config = os.environ.get("XDG_CONFIG_HOME", "")
    if xdg_config:
        p_suite = Path(xdg_config) / "FORENSIC_SUITE" / "settings.json"
        p_disc = Path(xdg_config) / "FORENSICS_DISCORD" / "settings.json"
        return p_suite if p_suite.exists() or not p_disc.exists() else p_disc
    p_suite = Path.home() / ".config" / "FORENSIC_SUITE" / "settings.json"
    p_disc = Path.home() / ".config" / "FORENSICS_DISCORD" / "settings.json"
    return p_suite if p_suite.exists() or not p_disc.exists() else p_disc


def _get_cli_language() -> str:
    p = _settings_file_path()
    if p.exists():
        try:
            import json
            return json.loads(p.read_text(encoding="utf-8")).get("language", "vi")
        except Exception:
            pass
    return "vi"


def _toggle_cli_language() -> str:
    cur = _get_cli_language()
    new_lang = "en" if cur == "vi" else "vi"
    p = _settings_file_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    try:
        import json
        data = {}
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
        data["language"] = new_lang
        p.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass
    return new_lang


def _scan_all_installed_apps() -> list[dict[str, Any]]:
    home = Path.home()
    appdata = home / "AppData"
    roaming = appdata / "Roaming"
    local = appdata / "Local"
    programs = local / "Programs"

    discord_paths = [
        roaming / "discord",
        local / "Discord",
        home / ".config" / "discord",
        home / ".var" / "app" / "com.discordapp.Discord" / "config" / "discord",
        home / "snap" / "discord" / "current" / ".config" / "discord",
    ]
    telegram_paths = [
        roaming / "Telegram Desktop",
        local / "Programs" / "Telegram Desktop",
        home / "Downloads" / "Telegram Desktop",
        home / ".local" / "share" / "TelegramDesktop",
        home / ".local" / "share" / "Telegram Desktop",
        home / ".var" / "app" / "org.telegram.desktop" / "data" / "TelegramDesktop",
        home / "snap" / "telegram-desktop" / "current" / ".local" / "share" / "TelegramDesktop",
    ]
    signal_paths = [
        programs / "signal-desktop",
        roaming / "Signal",
        home / ".config" / "Signal",
        home / ".var" / "app" / "org.signal.Signal",
    ]
    whatsapp_paths = [
        local / "WhatsApp",
        roaming / "WhatsApp",
        home / ".config" / "whatsapp",
    ]
    messenger_paths = [
        programs / "Messenger",
        roaming / "Messenger",
        home / ".config" / "Messenger",
    ]
    zalo_paths = [
        programs / "Zalo",
        roaming / "ZaloData",
        roaming / "Zalo",
        local / "ZaloPC",
        home / ".wine" / "drive_c" / "Program Files" / "Zalo",
    ]

    targets = [
        {
            "id": "discord",
            "name": "Discord Desktop",
            "status": "available",
            "paths": discord_paths,
            "features_vi": "Thu thập đầy đủ (LevelDB, SQLite, Session Tokens, Cache tin nhắn, Chuẩn hóa Autopsy)",
            "features_en": "Full Artifact Acquisition (LevelDB, SQLite, Session Tokens, Message Cache, Autopsy Export)",
        },
        {
            "id": "zalo",
            "name": "Zalo PC",
            "status": "planned",
            "paths": zalo_paths,
            "features_vi": "ZaloData, IndexedDB cache, cơ sở dữ liệu tin nhắn mã hóa (Lộ trình phát triển)",
            "features_en": "ZaloData, IndexedDB cache, encrypted chat database (Roadmap integration)",
        },
        {
            "id": "telegram",
            "name": "Telegram Desktop",
            "status": "available",
            "paths": telegram_paths,
            "features_vi": "Thu thập tdata, giải mã Media Cache (ảnh, voice .ogg, video), bóc tách SĐT & username, xuất Autopsy",
            "features_en": "tdata session extraction, Media Cache (images, voice .ogg, video), phone numbers & usernames, Autopsy",
        },
        {
            "id": "whatsapp",
            "name": "WhatsApp",
            "status": "planned",
            "paths": whatsapp_paths,
            "features_vi": "IndexedDB, tin nhắn đa phương tiện và cơ sở dữ liệu cục bộ (Lộ trình phát triển)",
            "features_en": "IndexedDB, local chat databases and media cache (Roadmap integration)",
        },
        {
            "id": "messenger",
            "name": "Facebook Messenger",
            "status": "planned",
            "paths": messenger_paths,
            "features_vi": "Cookie phiên đăng nhập, cache tin nhắn tạm (Lộ trình phát triển)",
            "features_en": "Session cookies, temporary message cache (Roadmap integration)",
        },
        {
            "id": "signal",
            "name": "Signal Desktop",
            "status": "planned",
            "paths": signal_paths,
            "features_vi": "Cơ sở dữ liệu mã hóa SQLite SQLCipher (Lộ trình phát triển)",
            "features_en": "SQLCipher encrypted database (Roadmap integration)",
        },
    ]

    results = []
    for app in targets:
        found_paths = [str(p) for p in app["paths"] if p.exists()]
        results.append({
            "id": app["id"],
            "name": app["name"],
            "status": app["status"],
            "installed": bool(found_paths),
            "paths": found_paths,
            "features_vi": app["features_vi"],
            "features_en": app["features_en"],
        })
    return results


def _resolve_menu_choice(choice: str, available: list) -> object:
    normalized = choice.strip().lower()

    for detection in available:
        if normalized in {detection.app_id.lower(), detection.display_name.lower()}:
            return detection
    if normalized in {"tg", "tele"}:
        for detection in available:
            if detection.app_id == "telegram":
                return detection

    has_telegram = any(d.app_id == "telegram" for d in available)

    if normalized == "1":
        for d in available:
            if d.app_id == "discord":
                return d
        return available[0] if available else "1"

    if normalized == "2":
        if has_telegram:
            for d in available:
                if d.app_id == "telegram":
                    return d
        else:
            for d in available:
                if d.app_id == "zalo":
                    return d
        return available[1] if len(available) > 1 else "2"

    if normalized == "3":
        if has_telegram:
            for d in available:
                if d.app_id == "zalo":
                    return d
            return "demo"
        else:
            return "demo"

    if normalized in {"4", "demo", "sample"}:
        return "demo"
    if normalized in {"5", "cases", "case"}:
        return "cases"
    if normalized in {"6", "report", "reports"}:
        return "report"
    if normalized in {"7", "apps", "scan"}:
        return "apps"
    if normalized in {"8", "license"}:
        return "license"
    if normalized in {"9", "workspace", "settings", "ws"}:
        return "workspace"
    if normalized in {"l", "lang", "language", "10"}:
        return "lang"
    if normalized in {"0", "exit", "quit", "q"}:
        return "exit"

    raise ValueError(f"Unsupported app selection: {choice}")


def _cli_show_demo() -> None:
    print_section("Synthetic Investigation Demo (SAMPLE)")
    print_status("info", "Scenario: Fictional Tabletop Response Exercise (CASE-SAMPLE-0142)")
    print_status("warn", "NOTICE: All messages, accounts, and files are simulated. No live user data was read.")
    print_kv("Channel", "#ops-tabletop")
    print_kv("Timeline Events", "4 key checkpoints (08:15 to 08:57)")
    print("\n  [Simulated Timeline]")
    events = [
        ("08:15:04", "analyst_sample", "Exercise begins. All events are simulated."),
        ("08:18:27", "responder_mock", "Mock alert received; no live systems involved."),
        ("08:24:10", "observer_demo", "Checkpoint saved to sample-note.txt."),
        ("08:31:52", "analyst_sample", "Review the sample attachment only."),
        ("08:37:16", "responder_mock", "sample-map.png is a demo placeholder."),
        ("08:46:39", "observer_demo", "Simulated handoff complete."),
        ("08:57:03", "analyst_sample", "Exercise closed; no real data accessed."),
    ]
    for time_str, user_str, msg_str in events:
        print(f"    {time_str} | {user_str:<16} | {msg_str}")
    print("\n  [Sample Artifacts]")
    print("    - sample-note.txt  (Text document: Exercise checklist)")
    print("    - sample-map.png   (Image asset: Mock network topology)")
    print_status("ok", "Demo inspection finished.")
    input("\nPress Enter to return to main menu...")


def _cli_show_cases() -> None:
    print_section("Saved Cases Browser")
    cases_dir = workspace_root() / "cases"
    if not cases_dir.exists():
        print_status("info", f"Cases directory does not exist yet: {cases_dir}")
        input("\nPress Enter to return...")
        return
    cases = sorted((p for p in cases_dir.iterdir() if p.is_dir()), key=lambda p: p.stat().st_mtime, reverse=True)
    if not cases:
        print_status("info", f"No saved cases found in {cases_dir}")
        input("\nPress Enter to return...")
        return
    from datetime import datetime
    print_kv("Cases directory", str(cases_dir))
    print(f"\n  {'#':<4} {'Case ID':<30} {'Modified':<20} {'Folders'}")
    print("  " + "-" * 70)
    for idx, case_path in enumerate(cases[:20], start=1):
        mtime = datetime.fromtimestamp(case_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        subfolders = sum(1 for sub in case_path.iterdir() if sub.is_dir())
        print(f"  [{idx:<2}] {case_path.name:<30} {mtime:<20} {subfolders} folders")
    print("\nOptions:")
    print("  - Enter case number to open folder in Windows Explorer")
    print("  - Enter case number with 'r' (e.g. '1r') to open its report")
    print("  - Press Enter to return to main menu")
    choice = input("Your choice: ").strip().lower()
    if not choice:
        return
    open_rep = choice.endswith("r")
    num_part = choice[:-1] if open_rep else choice
    if num_part.isdigit():
        case_idx = int(num_part) - 1
        if 0 <= case_idx < len(cases):
            selected_case = cases[case_idx]
            if open_rep:
                rep_file = selected_case / "08_Report" / "Muc_luc_bao_cao.md"
                if rep_file.exists():
                    import webbrowser
                    webbrowser.open(rep_file.as_uri())
                    print_status("ok", f"Opened report for {selected_case.name}")
                else:
                    print_status("warn", "Report not built for this case yet.")
            else:
                import webbrowser
                webbrowser.open(selected_case.as_uri())
                print_status("ok", f"Opened folder: {selected_case}")
    input("\nPress Enter to return...")


def _cli_show_reports() -> None:
    print_section("Investigation Reports")
    cases_dir = workspace_root() / "cases"
    if not cases_dir.exists():
        print_status("info", "No cases found.")
        input("\nPress Enter to return...")
        return
    reports = []
    for c in cases_dir.iterdir():
        if c.is_dir():
            rep = c / "08_Report" / "Muc_luc_bao_cao.md"
            if rep.exists():
                reports.append((c.stat().st_mtime, c.name, rep))
    if not reports:
        print_status("info", "No built reports found in workspace cases.")
        input("\nPress Enter to return...")
        return
    reports.sort(key=lambda r: r[0], reverse=True)
    latest = reports[0]
    import webbrowser
    print_status("ok", f"Opening latest investigation report: {latest[1]}")
    webbrowser.open(latest[2].as_uri())
    input("\nPress Enter to return...")


def _cli_show_apps(lang: str = "vi") -> None:
    clear_screen()
    _styled_banner()
    title = "KẾT QUẢ QUÉT ỨNG DỤNG NHẮN TIN TRÊN MÁY" if lang == "vi" else "INSTALLED MESSAGING APPLICATIONS SCAN REPORT"
    print_section(title)

    apps = _scan_all_installed_apps()
    installed_count = sum(1 for a in apps if a["installed"])

    summary_text = (
        f"Đã phát hiện {installed_count}/{len(apps)} ứng dụng có mặt trên thiết bị này."
        if lang == "vi"
        else f"Scan complete: Found {installed_count}/{len(apps)} messaging applications on this device."
    )
    print_status("info", summary_text)
    print("  " + "=" * 84)

    for idx, app in enumerate(apps, start=1):
        if app["installed"]:
            state_label = "● ĐÃ CÀI ĐẶT TRÊN MÁY (Installed)"
        else:
            state_label = "○ CHƯA CÀI ĐẶT (Not Installed)"

        if app["status"] == "available":
            support_label = "● ĐÃ HỖ TRỢ HOÀN CHỈNH (Supported & Ready)"
        else:
            support_label = "◷ ĐANG PHÁT TRIỂN / LỘ TRÌNH (Roadmap)"

        print(f"\n  [{idx}] {app['name']}")
        print(f"      Trạng thái cài đặt: {state_label}")
        print(f"      Hỗ trợ pháp chứng:  {support_label}")
        feat = app["features_vi"] if lang == "vi" else app["features_en"]
        print(f"      Khả năng điều tra:  {feat}")
        if app["installed"]:
            print("      Đường dẫn phát hiện:")
            for p in app["paths"]:
                print(f"        -> {p}")
        print("  " + "-" * 84)

    prompt = "\nNhấn [1] để Quét lại, hoặc nhấn [Enter] để quay lại Menu: " if lang == "vi" else "\nPress [1] to Rescan, or press [Enter] to return to Menu: "
    choice = input(prompt).strip()
    if choice == "1":
        _cli_show_apps(lang)


def _cli_show_license(access_status: dict) -> None:
    print_section("License & Device Information")
    from fdctl.services.license_service import current_license_status, machine_fingerprint, format_machine_name, activate_license_token
    status = current_license_status(force_enforced=True)
    print_kv("Active status", str(status.get("licenseLabel", "No active license")))
    print_kv("Registered email", str(status.get("issuedToEmail") or status.get("activatedForEmail") or "(none)"))
    print_kv("Expires at", str(status.get("expiresAt", "N/A")))
    print_kv("Device name", format_machine_name())
    print_kv("Hardware fingerprint", machine_fingerprint())
    print_kv("Allowed features", ", ".join(status.get("features", [])))
    key_input = input("\nEnter new license key to activate (or leave blank to return): ").strip()
    if key_input:
        email = input("Enter associated Gmail address: ").strip()
        if email:
            try:
                res = activate_license_token(key_input, email)
                print_status("ok", "Activated successfully!", res.get("licenseLabel", ""))
            except Exception as e:
                print_status("fail", f"Activation failed: {e}")
    input("\nPress Enter to return...")


def _cli_show_workspace(lang: str = "vi") -> None:
    clear_screen()
    _styled_banner()
    title = "THƯ MỤC LƯU TRỮ HỒ SƠ & BẰNG CHỨNG (CASE STORAGE & WORKSPACE)" if lang == "vi" else "CASE STORAGE & EVIDENCE WORKSPACE DETAILS"
    print_section(title)

    ws_root = workspace_root()
    cases_dir = ws_root / "cases"
    case_count = sum(1 for p in cases_dir.iterdir() if p.is_dir()) if cases_dir.exists() else 0

    if lang == "vi":
        print("""
Mục đích của Thư mục Lưu trữ Hồ sơ & Bằng chứng (Workspace):
- Đây là thư mục an toàn lưu trữ toàn bộ các hồ sơ vụ việc điều tra số (Cases) và chứng cứ kỹ thuật.
- Mỗi vụ việc khi được tạo sẽ có một thư mục riêng biệt (ví dụ: cases/case_discord_001) và được
  phân chia nghiêm ngặt thành 8 thư mục con chuẩn hóa pháp chứng số (DFIR Standard):
    1. 01_Case_Info         : Thông tin giám định viên, thời gian, nhật ký, mã băm sha256 niêm phong.
    2. 02_Live_Response     : Trạng thái tiến trình ứng dụng đang chạy, kết nối mạng, RAM triage.
    3. 03_Acquired_Files    : Toàn bộ file dữ liệu gốc trích xuất từ AppData (LevelDB, SQLite...).
    4. 04_Browser_Artifacts : Lịch sử web, cookie, session liên quan đến tài khoản nhắn tin.
    5. 05_Autopsy_Case      : Gói dữ liệu cấu trúc chuẩn để mở trực tiếp trong phần mềm Autopsy.
    6. 06_Screenshots       : Ảnh chụp màn hình bằng chứng hiện trường vụ việc.
    7. 07_Exports           : Dữ liệu bóc tách được xuất ra file JSON, CSV, bảng tính.
    8. 08_Report            : Báo cáo điều tra chính thức (HTML tương tác, Markdown, Timeline).
""")
    else:
        print("""
Purpose of Case Storage & Evidence Workspace:
- This is the secure directory storing all digital forensics cases and acquired evidence.
- Each investigation case resides in its own isolated folder (e.g. cases/case_discord_001)
  organized into 8 standardized DFIR subdirectories:
    1. 01_Case_Info         : Investigator metadata, timestamps, case notes, cryptographic hashes.
    2. 02_Live_Response     : Running process state, network connections, memory triage artifacts.
    3. 03_Acquired_Files    : Raw files collected from AppData (LevelDB, SQLite databases, cache).
    4. 04_Browser_Artifacts : Browser history and session cookies linked to chat activity.
    5. 05_Autopsy_Case      : Standardized case structure ready for direct ingestion in Autopsy.
    6. 06_Screenshots       : Visual evidence screenshots.
    7. 07_Exports           : Structured tables and exported datasets (JSON, CSV).
    8. 08_Report            : Canonical forensic reports (Interactive HTML, Markdown timeline).
""")
    print("  " + "-" * 78)
    print_kv("Thư mục lưu trữ Case" if lang == "vi" else "Case storage path", str(cases_dir))
    print_kv("Số hồ sơ hiện có" if lang == "vi" else "Saved cases count", f"{case_count} hồ sơ (cases)")
    print_kv("Quyền thực thi" if lang == "vi" else "Elevation state", "Administrator (Quản trị viên)" if is_admin() else "Standard User")
    print_kv("Phiên bản Suite" if lang == "vi" else "Suite version", f"Release {__release__}")
    print("  " + "-" * 78)

    prompt = "\nNhấn [1] để Mở thư mục này trong Windows Explorer, hoặc nhấn [Enter] để quay lại: " if lang == "vi" else "\nPress [1] to Open folder in Windows Explorer, or press [Enter] to return: "
    choice = input(prompt).strip()
    if choice == "1":
        cases_dir.mkdir(parents=True, exist_ok=True)
        import webbrowser
        webbrowser.open(cases_dir.as_uri())
        print_status("ok", "Đã mở thư mục trong Windows Explorer." if lang == "vi" else "Opened folder in Windows Explorer.")
        input("\nBấm Enter để quay lại Menu..." if lang == "vi" else "\nPress Enter to return...")


def _print_detection_card(index: int, detection: object) -> None:
    marker = "primary" if detection.app_id == "discord" else "future"  # type: ignore[attr-defined]
    support = getattr(detection, "support_level", "")
    name = getattr(detection, "display_name", "")
    print_status("step", f"{index}. {name}", f"support={support} | role={marker}")
    install_paths = list(getattr(detection, "install_paths", []) or [])
    if install_paths:
        for install_path in install_paths:
            print_kv("  path", str(install_path))
    else:
        print_kv("  path", "none shown in the current build")


def _numlock_enabled() -> bool | None:
    if sys.platform != "win32":
        return None
    try:
        return bool(ctypes.windll.user32.GetKeyState(0x90) & 1)
    except Exception:
        return None


def _prompt_selection(prompt: str) -> str:
    return input(prompt).strip()


def _ensure_interactive_bundle_access(feature: str) -> dict[str, object]:
    integrity = verify_bundle_integrity()
    if not integrity.get("ok"):
        raise PermissionError(
            f"Official bundle integrity check failed for {feature}: {integrity.get('reason')}. "
            "This build may have been modified or its copyright/integrity markers removed."
        )

    current_status = current_license_status()
    if not current_status.get("enforced") and current_status.get("active"):
        return current_status
    if current_status.get("active"):
        label = current_status.get("licenseLabel") or "Active License"
        mode_str = f" [{current_status.get('licenseMode', 'workstation').upper()}]" if current_status.get("licenseMode") else ""
        lid = current_status.get("licenseId", "")
        id_str = f" | ID: #{lid[:8].upper()}" if lid else ""
        print_status("ok", f"License verified: {label}{mode_str}{id_str}", current_status.get("issuedToEmail", ""))
        return current_status

    print_section("License Activation")
    remembered_email = last_used_email()
    email_prompt = "Enter your email address (Gmail or Corporate)"
    if remembered_email:
        email_prompt += f" [{remembered_email}]"
    email_prompt += ": "
    activation_email = input(email_prompt).strip() or remembered_email
    if not activation_email:
        raise PermissionError("An email address is required before the tool can continue.")
    activated = current_license_status(selected_email=activation_email, force_enforced=True)
    if not activated.get("active"):
        recent_history = license_usage_history(limit=3)
        if recent_history:
            print_status("info", "Recent local email/license history found for this device.")
            for entry in recent_history:
                print_kv(
                    "  history",
                    f"{entry.get('email', '')} | {entry.get('licenseLabel', '')} | expires={entry.get('expiresAt', '')} | key={entry.get('tokenPreview', '') or '(trial)'}",
                )
        license_key = input("Paste the matching license key (leave blank to cancel): ").strip()
        if not license_key:
            raise PermissionError(
                "A valid email address and owner-issued signed license key are required when no active trial or license exists. "
                f"Current status: {activated.get('reason', '')}. "
                "The local 7-day trial is limited to the synthetic demo."
            )
        activated = activate_license_token(license_key, activation_email)
    print_status(
        "ok",
        "Access granted.",
        f"{activated.get('licenseLabel', '')} | email={activated.get('issuedToEmail', '')} | expires={activated.get('expiresAt', '')}",
    )
    return activated

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fdctl", description="CLI-first Windows chat forensics toolkit")
    subparsers = parser.add_subparsers(dest="command", required=True)

    apps = subparsers.add_parser("apps", help="Detect supported apps")
    apps_sub = apps.add_subparsers(dest="apps_command", required=True)
    detect = apps_sub.add_parser("detect", help="Detect installed chat apps")
    detect.add_argument("--json", action="store_true", dest="as_json")

    app_cmd = subparsers.add_parser("app", help="Application launch commands")
    app_sub = app_cmd.add_subparsers(dest="app_command", required=True)
    app_open = app_sub.add_parser("open", help="Open a supported application")
    app_open.add_argument("--app", required=True, choices=sorted(get_adapters().keys()))
    app_open.add_argument("--admin", action="store_true")

    case = subparsers.add_parser("case", help="Case lifecycle commands")
    case_sub = case.add_subparsers(dest="case_command", required=True)
    case_create = case_sub.add_parser("create", help="Create a runtime case")
    case_create.add_argument("--app", required=True, choices=sorted(get_adapters().keys()))
    case_create.add_argument("--id", dest="case_id")
    case_create.add_argument("--channel-url", dest="channel_url")
    case_create.add_argument("--target-user", dest="target_user")

    case_save = case_sub.add_parser("save", help="Save a runtime case")
    case_save.add_argument("--case", required=True, dest="case_id")

    case_discard = case_sub.add_parser("discard", help="Discard a case")
    case_discard.add_argument("--case", required=True, dest="case_id")

    collect = subparsers.add_parser("collect", help="Collect artifacts into a case")
    collect.add_argument("--case", required=True, dest="case_id")
    collect.add_argument("--elevated", action="store_true")

    analyze = subparsers.add_parser("analyze", help="Analyze a collected case")
    analyze.add_argument("--case", required=True, dest="case_id")

    supplement = subparsers.add_parser("supplement", help="Run supplemental completeness checks and legacy-aligned exports")
    supplement.add_argument("--case", required=True, dest="case_id")

    report = subparsers.add_parser("report", help="Report commands")
    report_sub = report.add_subparsers(dest="report_command", required=True)
    report_build = report_sub.add_parser("build", help="Build static report for a case")
    report_build.add_argument("--case", required=True, dest="case_id")
    report_build.add_argument("--no-prompt", action="store_true")
    report_open = report_sub.add_parser("open", help="Open a built report")
    report_open.add_argument("--case", required=True, dest="case_id")

    ide = subparsers.add_parser("ide", help="IDE workspace commands")
    ide_sub = ide.add_subparsers(dest="ide_command", required=True)
    ide_sub.add_parser("open", help="Open the VS Code workspace")

    menu = subparsers.add_parser("menu", help="Open an interactive terminal workflow")
    menu.add_argument("--app", choices=sorted(get_adapters().keys()))
    menu.add_argument("--channel-url", dest="channel_url")
    menu.add_argument("--target-user", dest="target_user")
    menu.add_argument("--skip-open-discord", action="store_true")

    license_cmd = subparsers.add_parser("license", help="License activation and issuance commands")
    license_sub = license_cmd.add_subparsers(dest="license_command", required=True)
    license_status = license_sub.add_parser("status", help="Show current bundle license status")
    license_status.add_argument("--email", required=False)
    license_activate = license_sub.add_parser("activate", help="Activate a license key")
    license_activate.add_argument("--email", required=False)
    license_activate.add_argument("--key")
    license_activate.add_argument("--key-file", dest="key_file")
    license_activate.add_argument("--prompt", action="store_true")
    license_sub.add_parser("deactivate", help="Remove the current local activation")
    license_sub.add_parser("machine", help="Show the current device name and machine fingerprint")


    return parser

def interactive_menu(args: argparse.Namespace | None = None) -> int:
    try:
        setup_terminal()
        clear_screen()
        adapters = get_adapters()
        detections = [adapter.detect() for adapter in adapters.values()] # type: ignore
        workflow_progress = StageProgress(5)
        _styled_banner()
        print_copyright_notice()
        access_status = _ensure_interactive_bundle_access("interactive workflow")

        available = [item for item in detections if item.app_id in {"discord", "telegram", "zalo"}]
        selected = next((item for item in available if args and args.app == item.app_id), None)

        while True:
            lang = _get_cli_language()
            if selected is None:
                clear_screen()
                _styled_banner()
                user_email = str(access_status.get("issuedToEmail", "") or access_status.get("activatedForEmail", "") or "Free Trial")
                lic_label = str(access_status.get("licenseLabel", "Trial"))
                lang_label = "Tiếng Việt (VI)" if lang == "vi" else "English (EN)"
                cases_dir = workspace_root() / "cases"

                print(f" [👤 Email: {user_email} | 🔒 {lic_label} | 💻 {format_machine_name()} | 🌐 {lang_label}]")
                print(f" [📁 Thư mục lưu Case: {cases_dir}]")
                print(" " + "=" * 80)

                if lang == "vi":
                    print("  🎯 ĐIỀU TRA ỨNG DỤNG (APPLICATION FORENSICS):")
                    print("    [1] Discord   ● ĐÃ HỖ TRỢ (LevelDB Carving, Token, Snowflake, Autopsy)")
                    print("    [2] Telegram  ● ĐÃ HỖ TRỢ (tdata Session, Media Cache Carving, Autopsy)")
                    print("    [3] Zalo      ◷ ĐANG PHÁT TRIỂN (Lộ trình tích hợp / Roadmap)")
                    print("")
                    print("  🛠️ CÔNG CỤ & QUẢN LÝ DỮ LIỆU (TOOLS & DATA MANAGEMENT):")
                    print("    [4] 🧪 Chạy Thử nghiệm Dữ liệu Mẫu (Synthetic Sample Walkthrough)")
                    print("    [5] 📂 Quản lý & Xem Danh sách Hồ sơ (Cases & Evidence Browser)")
                    print("    [6] 📊 Mở Báo cáo Điều tra Gần nhất (Open Latest Report HTML)")
                    print("    [7] 🔍 Quét & Kiểm tra Ứng dụng trên Máy (Scan Installed Chat Apps on PC)")
                    print("")
                    print("  ⚙️ CẤU HÌNH & HỆ THỐNG (SETTINGS & SYSTEM):")
                    print("    [8] 🔑 Quản lý Bản quyền & Thiết bị (License Status & Hardware Fingerprint)")
                    print("    [9] 📁 Thư mục Lưu trữ Bằng chứng (Case Storage & Workspace Explorer)")
                    print("    [L] 🌐 Đổi Ngôn ngữ hiển thị / Switch Language (VI / EN)")
                    print("    [0] 🚪 Thoát Chương trình (Exit)")
                else:
                    print("  🎯 APPLICATION FORENSICS:")
                    print("    [1] Discord   ● FULLY SUPPORTED (Token Extraction, SQLite, LevelDB, Autopsy)")
                    print("    [2] Telegram  ● FULLY SUPPORTED (tdata Session, Media Cache Carving, Autopsy)")
                    print("    [3] Zalo      ◷ IN DEVELOPMENT (Planned Integration / Roadmap)")
                    print("")
                    print("  🛠️ TOOLS & DATA MANAGEMENT:")
                    print("    [4] 🧪 Synthetic Investigation Demo (Sample Walkthrough Case)")
                    print("    [5] 📂 Saved Cases & Evidence Browser")
                    print("    [6] 📊 Open Latest Built Report (HTML)")
                    print("    [7] 🔍 Scan Installed Messaging Applications on PC")
                    print("")
                    print("  ⚙️ SETTINGS & SYSTEM:")
                    print("    [8] 🔑 License Status & Hardware Fingerprint")
                    print("    [9] 📁 Case Storage & Workspace Explorer")
                    print("    [L] 🌐 Switch Language (Tiếng Việt / English)")
                    print("    [0] 🚪 Exit Forensics Suite")

                print(" " + "-" * 80)
                sys.stdout.flush()
                prompt_text = "Nhập số lựa chọn (1-9, L đổi ngôn ngữ, 0 để thoát): " if lang == "vi" else "Enter choice number (1-9, L for language, 0 to exit): "
                choice = _prompt_selection(prompt_text)
                selected = _resolve_menu_choice(choice, available)

            if isinstance(selected, str):
                if selected in {"0", "exit", "quit", "q"}:
                    print_status("info", "Tạm biệt! Đã thoát Forensics Suite." if lang == "vi" else "Exiting Forensics Suite.")
                    return 0
                if selected in {"4", "3", "demo"}:
                    _cli_show_demo()
                elif selected in {"5", "cases", "case"}:
                    _cli_show_cases()
                elif selected in {"6", "report", "reports"}:
                    _cli_show_reports()
                elif selected in {"7", "apps", "scan"}:
                    _cli_show_apps(lang)
                elif selected in {"8", "license"}:
                    _cli_show_license(access_status)
                elif selected in {"9", "workspace", "settings", "ws"}:
                    _cli_show_workspace(lang)
                elif selected in {"l", "lang", "language", "10"}:
                    new_l = _toggle_cli_language()
                    print_status("ok", f"Ngôn ngữ hiển thị đã đổi sang: {'Tiếng Việt' if new_l == 'vi' else 'English'}")
                selected = None
                continue

            if selected.app_id != "zalo":
                break
            print_status("info", "Zalo forensic support is under development. No Zalo data will be accessed.")
            print_status("step", "Returning to app selection. Choose Discord to continue.")
            selected = None
            sys.stdout.flush()

        adapter = adapters[selected.app_id] # type: ignore

        print_section("Investigation Scope")
        app_disp = getattr(selected, "display_name", "Target App")
        channel_url = (args.channel_url if args else None) or input(f"Enter {app_disp} channel/chat link to investigate (optional): ").strip()
        target_user = (args.target_user if args else None) or input(f"Enter a target {app_disp} username or ID (optional): ").strip()
        sys.stdout.flush()

        open_choice = "n" if args and args.skip_open_discord else input(f"Open {app_disp} with administrator permission before collection? [Y/n]: ").strip().lower()
        if open_choice not in {"n", "no"}:
            print_status("step", f"Checking / Launching {app_disp} with administrator permission...")
            try:
                launch_result = open_application(selected.app_id, as_admin=True)
                if launch_result.get("alreadyRunning"):
                    print_status("ok", f"{app_disp} is already active on this system.", launch_result.get("executablePath", ""))
                else:
                    print_status("ok", f"{app_disp} launched successfully.", launch_result.get("executablePath", ""))
                print(json.dumps({"appLaunch": launch_result}, ensure_ascii=False, indent=2))
            except Exception as exc:
                print_status("warn", f"Could not launch {app_disp}: {exc}. Proceeding with artifact collection...")
            sys.stdout.flush()

        if adapter.requires_admin_for_collection() and not is_admin(): # type: ignore
            print_status("warn", "Elevation is required for this collection. Relaunching terminal workflow as administrator...")
            print_status("warn", f"Windows will ask the user to allow administrator access so {app_disp} artifacts can be collected.")
            sys.stdout.flush()
            rerun_arguments = ["menu", "--app", selected.app_id, "--skip-open-discord"] # type: ignore
            if channel_url:
                rerun_arguments.extend(["--channel-url", channel_url])
            if target_user:
                rerun_arguments.extend(["--target-user", target_user])
            rerun_as_admin(rerun_arguments)

        context = create_case(
            selected.app_id, # type: ignore
            channel_url=channel_url or None,
            target_user=target_user or None,
        )
        workflow_progress.advance("Case created", f"{context.case_id} -> {context.root}")
        print_status("ok", f"Created case: {context.case_id}")
        sys.stdout.flush()

        print_section("Collection")
        collect_result = collect_case(context)
        workflow_progress.advance("Collection finished", f"Artifacts: {collect_result.get('artifactCount', 0)} | Screenshots: {len(collect_result.get('screenshots', []))}")
        print(json.dumps({"collect": collect_result}, ensure_ascii=False, indent=2))
        sys.stdout.flush()

        print_section("Analysis")
        analyze_result = analyze_case(context)
        workflow_progress.advance("Analysis finished", f"Recovered messages: {analyze_result.get('recoveredMessageRows', 0)} | Timeline rows: {analyze_result.get('timelineRows', 0)}")
        print(json.dumps({"analyze": analyze_result}, ensure_ascii=False, indent=2))
        sys.stdout.flush()

        print_section("Report")
        report_path = build_report(context)
        workflow_progress.advance("Report bundle ready", str(report_path))
        print(json.dumps({"report": str(report_path)}, ensure_ascii=False, indent=2))
        sys.stdout.flush()

        print_status("step", "Auto-saving case after report build...", context.case_id)
        saved = save_case(context.case_id)
        final_report = open_report(saved)
        print_status("ok", "Detailed local report opened.", str(final_report))
        print_status("info", "Canonical saved case root", str(saved.root))
        print_status("info", "Terminal workflow has finished. No background investigation task is still running.")
        workflow_progress.finish("Workflow completed", f"Saved case -> {saved.root}")
        print(
            json.dumps(
                {
                    "status": "saved",
                    "root": str(saved.root),
                    "report": str(final_report),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        sys.stdout.flush()
        return 0

    except KeyboardInterrupt:
        print("\n[!] Operation cancelled by user")
        sys.stdout.flush()
        return 1
    except Exception as e:
        print(f"\n[ERROR] An error occurred in menu: {str(e)}")
        print(f"[ERROR] Type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
        return 1


def main(argv: list[str] | None = None) -> int:
    try:
        setup_terminal()
        parser = build_parser()
        args = parser.parse_args(argv)
        adapters = get_adapters()

        if args.command == "license" and args.license_command == "status":
            _print({
                "license": current_license_status(selected_email=str(getattr(args, "email", "") or "").strip()),
                "integrity": verify_bundle_integrity(),
                "licenseTypes": license_types_summary(),
                "history": license_usage_history(limit=10),
            })
            return 0

        if args.command == "license" and args.license_command == "activate":
            remembered_email = last_used_email()
            activation_email = str(args.email or "").strip()
            token = str(args.key or "").strip()
            if args.key_file:
                token = Path(args.key_file).read_text(encoding="utf-8").strip()
            if args.prompt or not activation_email:
                prompt = "Enter the license Gmail address"
                if remembered_email:
                    prompt += f" [{remembered_email}]"
                prompt += ": "
                activation_email = input(prompt).strip() or remembered_email
            if token:
                status = activate_license_token(token, activation_email)
            else:
                status = current_license_status(selected_email=activation_email, force_enforced=True)
                if not status.get("active"):
                    if args.prompt:
                        token = input("Paste the license key issued by Truong Trieu Vy (leave blank to cancel): ").strip()
                        if token:
                            status = activate_license_token(token, activation_email)
                    if not status.get("active"):
                        raise ValueError("A license key is required for this email on this device.")
            print_status(
                "ok",
                "License activated.",
                f"{status.get('licenseLabel', '')} | email={status.get('issuedToEmail', '')} | expires={status.get('expiresAt', '')}",
            )
            _print({"status": "activated", "license": status})
            return 0

        if args.command == "license" and args.license_command == "deactivate":
            deactivate_license()
            _print({"status": "deactivated"})
            return 0

        if args.command == "license" and args.license_command == "machine":
            _print(
                {
                    "product": "FORENSIC_SUITE",
                    "toolVersion": f"Release {__release__}",
                    "deviceName": format_machine_name(),
                    "machineFingerprint": machine_fingerprint(),
                }
            )
            return 0

        if args.command not in {"menu", "apps"}:
            require_bundle_access(args.command)

        if args.command == "apps" and args.apps_command == "detect":
            rows = []
            for adapter in adapters.values():
                detection = adapter.detect()  # type: ignore
                rows.append(
                    {
                        "appId": detection.app_id,
                        "displayName": detection.display_name,
                        "detected": detection.detected,
                        "supportLevel": detection.support_level,
                        "installPaths": detection.install_paths,
                        "notes": detection.notes,
                    }
                )
            _print(rows)
            return 0

        if args.command == "app" and args.app_command == "open":
            result = open_application(args.app, as_admin=args.admin)
            _print(result)
            return 0

        if args.command == "case" and args.case_command == "create":
            context = create_case(
                args.app,
                args.case_id,
                channel_url=args.channel_url,
                target_user=args.target_user,
            )
            _print({"caseId": context.case_id, "appId": context.app_id, "root": str(context.root), "status": "runtime"})
            return 0

        if args.command == "case" and args.case_command == "save":
            context = save_case(args.case_id)
            _print({"caseId": context.case_id, "root": str(context.root), "status": "saved"})
            return 0

        if args.command == "case" and args.case_command == "discard":
            discard_case(args.case_id)
            _print({"caseId": args.case_id, "status": "discarded"})
            return 0

        if args.command == "collect":
            context = load_case(args.case_id)
            result = collect_case(context, elevated=args.elevated)
            _print({"caseId": context.case_id, "status": "collected", "result": result})
            return 0

        if args.command == "analyze":
            context = load_case(args.case_id)
            result = analyze_case(context)
            _print({"caseId": context.case_id, "status": "analyzed", "result": result})
            return 0

        if args.command == "supplement":
            context = load_case(args.case_id)
            result = run_supplemental_checks(context)
            result["reportValidation"] = validate_report_bundle(context)
            _print({"caseId": context.case_id, "status": "supplemented", "result": result})
            return 0

        if args.command == "report" and args.report_command == "build":
            context = load_case(args.case_id)
            index_path = build_report(context)
            if not context.saved:
                print_status("step", "Auto-saving case after report build...", context.case_id)
                saved = save_case(context.case_id)
                index_path = open_report(saved)
                print_status("ok", "Terminal report summary ready.", str(index_path))
                _print({"caseId": saved.case_id, "status": "saved", "root": str(saved.root), "indexPath": str(index_path)})
            else:
                print_status("ok", "Terminal report bundle ready.", str(index_path))
                _print({"caseId": context.case_id, "status": "report-built", "indexPath": str(index_path)})
            return 0

        if args.command == "report" and args.report_command == "open":
            context = load_case(args.case_id)
            index_path = open_report(context)
            _print({"caseId": context.case_id, "status": "report-summarized", "indexPath": str(index_path)})
            return 0

        if args.command == "ide" and args.ide_command == "open":
            target = open_workspace()
            _print({"status": "opened", "workspace": target})
            return 0

        if args.command == "menu":
            return interactive_menu(args)

        parser.error("Unhandled command")
        return 1
        
    except SystemExit as e:
        """Allow SystemExit from rerun_as_admin and parser.error() to pass through"""
        sys.stdout.flush()
        raise
    except KeyboardInterrupt:
        print("\n[!] Operation cancelled by user")
        sys.stdout.flush()
        return 1
    except PermissionError as e:
        print_status("error", "Access denied by bundle protection.", str(e))
        sys.stdout.flush()
        return 1
    except ValueError as e:
        print_status("error", "Invalid activation data.", str(e))
        sys.stdout.flush()
        return 1
    except FileNotFoundError as e:
        print_status("error", "Missing required file.", str(e))
        sys.stdout.flush()
        return 1
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {str(e)}", file=sys.stderr)
        print(f"[ERROR] Type: {type(e).__name__}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        sys.stdout.flush()
        return 1
