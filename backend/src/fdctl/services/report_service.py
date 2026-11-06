from __future__ import annotations

from pathlib import Path

from fdctl.console import StageProgress, print_kv, print_section, print_status
from fdctl.models import CaseContext
from fdctl.services.autopsy_service import build_autopsy_bundle
from fdctl.services.license_service import require_bundle_access
from fdctl.services.report_layout import case_snapshot_path
from fdctl.services.report_documents import write_handover_report, write_report_index
from fdctl.services.schema_builder import build_case_schema
from fdctl.services.supplement_service import run_supplemental_checks, validate_report_bundle
from fdctl.utils import ensure_dir, remove_tree, write_json


def refresh_report_outputs(case: CaseContext) -> Path:
    ensure_dir(case.report_dir)
    print_status("step", "Refreshing case snapshot for terminal review...", f"Report root: {case.report_dir}")
    run_supplemental_checks(case)
    schema = build_case_schema(case)
    write_report_index(case, schema)
    write_handover_report(case, schema)
    snapshot_path = case_snapshot_path(case)
    write_json(snapshot_path, schema)
    build_autopsy_bundle(case)
    validate_report_bundle(case)
    schema = build_case_schema(case)
    write_report_index(case, schema)
    write_handover_report(case, schema)
    write_json(snapshot_path, schema)
    print_status("ok", "Case snapshot synchronized.", str(snapshot_path))
    return snapshot_path


def build_report(case: CaseContext) -> Path:
    require_bundle_access("report-build")
    print_section("Report Builder", f"Case {case.case_id} | Report root {case.report_dir}")
    progress = StageProgress(3)
    report_web = case.report_dir / "web"
    if report_web.exists():
        remove_tree(report_web)
    progress.advance("Legacy web artifacts removed", str(report_web))
    snapshot_path = refresh_report_outputs(case)
    progress.advance("Case snapshot written", str(snapshot_path))
    entry_path = case.report_dir / "Muc_luc_bao_cao.md"
    progress.finish("Terminal report bundle completed", str(entry_path))
    return entry_path


def _print_report_summary(case: CaseContext, schema: dict) -> None:
    summary = schema.get("summary", {}) if isinstance(schema.get("summary"), dict) else {}
    scope = schema.get("scope", {}) if isinstance(schema.get("scope"), dict) else {}
    print_section("Report Summary", f"Case {case.case_id}")
    print_kv("Case root", str(case.root))
    print_kv("Report root", str(case.report_dir))
    print_kv("Target user", str(scope.get("targetUser", "")))
    print_kv("Channel URL", str(scope.get("channelUrl", "")))
    print_kv("Recovered messages", str(summary.get("recoveredMessages", 0)))
    print_kv("Timeline rows", str(summary.get("timelineRows", 0)))
    print_kv("Attachments", str(summary.get("attachments", 0)))
    print_kv("Chrome history rows", str(summary.get("chromeHistoryRows", 0)))
    print_kv("Desktop cookie rows", str(summary.get("desktopCookieRows", 0)))
    print_kv("Artifact count", str(summary.get("artifactCount", 0)))
    print_kv("Report index", str(case.report_dir / "Muc_luc_bao_cao.md"))
    print_kv("Handover report", str(case.report_dir / "Bien_ban_ban_giao.md"))
    print_kv("Case snapshot", str(case_snapshot_path(case)))


def open_report(case: CaseContext) -> Path:
    require_bundle_access("report-open")
    snapshot = case_snapshot_path(case)
    if not snapshot.exists():
        raise FileNotFoundError("Report snapshot has not been built for this case.")
    schema = build_case_schema(case)
    _print_report_summary(case, schema)
    return case.report_dir / "Muc_luc_bao_cao.md"
