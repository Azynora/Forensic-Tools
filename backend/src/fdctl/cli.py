from __future__ import annotations
import argparse
import ctypes
import json
import sys
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
    issue_license_key,
    issued_key_storage_root,
    last_used_email,
    license_issue_allowed,
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
    print_banner("FORENSICS SUITE", "Extensible digital forensics workspace for Windows")
    sys.stdout.flush()

def _resolve_menu_choice(choice: str, available: list) -> object:
    normalized = choice.strip().lower()
    if normalized.isdigit():
        index = int(normalized) - 1
        if 0 <= index < len(available):
            return available[index]
    for detection in available:
        if normalized in {detection.app_id.lower(), detection.display_name.lower()}:
            return detection
    raise ValueError(f"Unsupported app selection: {choice}")


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
    print_section("License Activation")
    remembered_email = last_used_email()
    email_prompt = "Enter your Gmail address"
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
                "A valid Gmail address and owner-issued signed license key are required when no active trial or license exists. "
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
    license_issue = license_sub.add_parser("issue", help="Issue a signed local license key from the private source workspace")
    license_issue.add_argument("--email", required=True)
    license_issue.add_argument("--type", dest="license_type", choices=[item["key"] for item in license_types_summary()], required=True)
    license_issue.add_argument("--days", dest="days_valid", type=int)
    license_issue.add_argument("--max-seats", dest="max_seats", type=int, default=1)
    license_issue.add_argument("--feature", action="append", dest="features")
    license_issue.add_argument("--machine", required=True, help="Target device fingerprint provided by the end user")
    license_issue.add_argument("--notes", default="")
    license_issue.add_argument("--out", dest="output_path")
    license_issue_owner = license_sub.add_parser("issue-owner", help="Issue a private unlimited owner key from the source workspace")
    license_issue_owner.add_argument("--email", default="trieuvy9198@gmail.com")
    license_issue_owner.add_argument("--machine", required=True, help="Target owner device fingerprint")
    license_issue_owner.add_argument("--notes", default="Owner unlimited activation key")
    license_issue_owner.add_argument("--out", dest="output_path")

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
        print_section("Workspace")
        print_kv("Tool version", f"Release {__release__}")
        print_kv("Run folder", str(project_root()))
        print_kv("Case data root", str(workspace_root()))
        print_kv("Device name", format_machine_name())
        print_kv("Active email", str(access_status.get("issuedToEmail", "") or access_status.get("activatedForEmail", "") or ""))
        print_kv("Storage layout", "8 standard case folders")
        for folder_name in [
            "01_Case_Info",
            "02_Live_Response",
            "03_Acquired_Files",
            "04_Browser_Artifacts",
            "05_Autopsy_Case",
            "06_Screenshots",
            "07_Exports",
            "08_Report",
        ]:
            print(f"  - {folder_name}")
        numlock_state = _numlock_enabled()
        if numlock_state is False:
            print_status(
                "warn",
                "Num Lock is OFF. You can still type normally and paste text; keypad number entry may need Num Lock ON.",
            )
        elif numlock_state is True:
            print_status("info", "Normal typing, copy/paste, and keypad selection are available.")
        sys.stdout.flush()
        
        available = [item for item in detections if item.app_id in {"discord", "zalo"}]
        selected = next((item for item in available if args and args.app == item.app_id), None)
        while True:
            if selected is None:
                print_section("Available investigation apps")
                for index, detection in enumerate(available, start=1):
                    _print_detection_card(index, detection)
                sys.stdout.flush()
                choice = _prompt_selection("Select app number to investigate or type app name: ")
                selected = _resolve_menu_choice(choice, available)
            if selected.app_id != "zalo":
                break
            print_status("info", "Zalo forensic support is under development. No Zalo data will be accessed.")
            print_status("step", "Returning to app selection. Choose Discord to continue.")
            selected = None
            sys.stdout.flush()
        
        adapter = adapters[selected.app_id] # type: ignore

        print_section("Investigation Scope")
        channel_url = (args.channel_url if args else None) or input("Enter Discord channel link to investigate (optional): ").strip()
        target_user = (args.target_user if args else None) or input("Enter a Discord username or user id to focus on (optional): ").strip()
        sys.stdout.flush()

        open_choice = "n" if args and args.skip_open_discord else input("Open Discord with administrator permission before collection? [Y/n]: ").strip().lower()
        if open_choice not in {"n", "no"}:
            print_status("step", "Launching Discord with administrator permission...")
            launch_result = open_application("discord", as_admin=True)
            print(json.dumps({"appLaunch": launch_result}, ensure_ascii=False, indent=2))
            sys.stdout.flush()

        if adapter.requires_admin_for_collection() and not is_admin(): # type: ignore
            print_status("warn", "Elevation is required for this collection. Relaunching terminal workflow as administrator...")
            print_status("warn", "Windows will ask the user to allow administrator access so Discord artifacts can be collected.")
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
                    "product": "FORENSICS_DISCORD",
                    "toolVersion": f"Release {__release__}",
                    "deviceName": format_machine_name(),
                    "machineFingerprint": machine_fingerprint(),
                    "issuedKeyStorageRoot": str(issued_key_storage_root()),
                }
            )
            return 0

        if args.command == "license" and args.license_command == "issue":
            if not license_issue_allowed():
                raise PermissionError(
                    "License issuance is only available from the owner's private source machine, not from the distributed bundle or an untrusted source checkout."
                )
            issued = issue_license_key(
                args.email,
                args.license_type,
                days_valid=args.days_valid,
                max_seats=args.max_seats,
                features=args.features,
                notes=args.notes,
                bound_machine=args.machine,
            )
            output_path = Path(args.output_path) if args.output_path else issued_key_storage_root() / (
                f"{str(args.email).replace('@', '_at_').replace('.', '_')}_{args.license_type}.key"
            )
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(issued["token"], encoding="utf-8")
            _print({"status": "issued", "outputPath": str(output_path), **issued})
            return 0

        if args.command == "license" and args.license_command == "issue-owner":
            if not license_issue_allowed():
                raise PermissionError(
                    "Owner key issuance is only available from the owner's private source machine."
                )
            issued = issue_license_key(
                args.email,
                "owner_unlimited",
                max_seats=1,
                notes=args.notes,
                bound_machine=args.machine,
                release_channel="owner-issued",
            )
            output_path = Path(args.output_path) if args.output_path else issued_key_storage_root() / "owner_unlimited.key"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(issued["token"], encoding="utf-8")
            _print({"status": "issued", "outputPath": str(output_path), **issued})
            return 0

        if args.command != "menu":
            require_bundle_access(args.command)

        if args.command == "apps" and args.apps_command == "detect":
            rows = []
            for adapter in adapters.values():
                detection = adapter.detect() # type: ignore
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
