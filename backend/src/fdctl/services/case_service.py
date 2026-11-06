from __future__ import annotations
import shutil
import re
from pathlib import Path
from fdctl.console import print_status
from fdctl.models import CaseContext, WORK_DIR_NAMES
from fdctl.paths import cases_root, runtime_root
from fdctl.utils import ensure_dir, now_iso, now_stamp, read_json, remove_tree, write_json

LEGACY_DIR_ALIASES = {
    "info": ("01_Case_Info", "Case_Info"),
    "exports": ("07_Exports", "Exports"),
    "acquired": ("03_Acquired_Files", "Acquired_Files"),
}
CASE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def _validate_case_id(case_id: str) -> str:
    value = str(case_id or "").strip()
    if not CASE_ID_PATTERN.fullmatch(value) or value in {".", ".."}:
        raise ValueError("Case ID must be 1-64 characters using letters, numbers, dots, underscores, or hyphens.")
    return value


def _case_root(base: Path, case_id: str) -> Path:
    root = base / _validate_case_id(case_id)
    resolved_base = base.resolve()
    resolved_root = root.resolve()
    if resolved_root.parent != resolved_base:
        raise ValueError("Case path must be a direct child of the configured workspace.")
    return root

def case_file(root: Path) -> Path:
    return root / "case.json"

def _first_existing(root: Path, *candidates: str) -> Path | None:
    for candidate in candidates:
        path = root / candidate
        if path.exists():
            return path
    return None

def _infer_app_id(root: Path) -> str:
    info_dir = _first_existing(root, *LEGACY_DIR_ALIASES["info"])
    collection_summary_path = info_dir / "collection_summary.json" if info_dir else None
    if collection_summary_path and collection_summary_path.exists():
        summary = read_json(collection_summary_path)
        app_name = str(summary.get("app", "") or "").strip().lower()
        if app_name == "discord":
            return "discord"
        if app_name == "zalo":
            return "zalo"

    exports_dir = _first_existing(root, *LEGACY_DIR_ALIASES["exports"])
    analysis_summary_path = exports_dir / "analysis_summary.json" if exports_dir else None
    if analysis_summary_path and analysis_summary_path.exists():
        summary = read_json(analysis_summary_path)
        app_id = str(summary.get("appId", "") or "").strip().lower()
        if app_id in {"discord", "zalo"}:
            return app_id

    acquired_dir = _first_existing(root, *LEGACY_DIR_ALIASES["acquired"])
    if acquired_dir and ((acquired_dir / "DiscordRoaming").exists() or (acquired_dir / "DiscordLocal").exists()):
        return "discord"
    if acquired_dir and (acquired_dir / "Zalo").exists():
        return "zalo"
    return "discord"

def _recover_scope(root: Path) -> dict:
    exports_dir = _first_existing(root, *LEGACY_DIR_ALIASES["exports"])
    scope_summary_path = exports_dir / "scope_summary.json" if exports_dir else None
    if scope_summary_path and scope_summary_path.exists():
        summary = read_json(scope_summary_path)
        return {
            "channelUrl": str(summary.get("channelUrl", "") or ""),
            "targetUser": str(summary.get("targetUser", "") or ""),
        }

    return {
        "channelUrl": "",
        "targetUser": "",
    }

def _ensure_case_metadata(root: Path, saved: bool) -> dict:
    metadata_path = case_file(root)
    if metadata_path.exists():
        return read_json(metadata_path)

    recovered = {
        "caseId": root.name,
        "appId": _infer_app_id(root),
        "createdAt": now_iso(),
        "status": "saved" if saved else "runtime",
        "saved": saved,
        "scope": _recover_scope(root),
        "recoveredMetadata": True,
    }
    write_json(metadata_path, recovered)
    return recovered

def create_case(
    app_id: str,
    case_id: str | None = None,
    channel_url: str | None = None,
    target_user: str | None = None,
) -> CaseContext:
    runtime = ensure_dir(runtime_root())
    resolved_case_id = _validate_case_id(case_id or f"{app_id}_analysis_{now_stamp()}")
    root = _case_root(runtime, resolved_case_id)
    if root.exists():
        raise FileExistsError(f"Case already exists: {resolved_case_id}")

    ensure_dir(root)
    for name in WORK_DIR_NAMES:
        ensure_dir(root / name)

    context = CaseContext(case_id=resolved_case_id, app_id=app_id, root=root, saved=False)
    write_json(
        case_file(root),
        {
            "caseId": resolved_case_id,
            "appId": app_id,
            "createdAt": now_iso(),
            "status": "runtime",
            "saved": False,
            "scope": {
                "channelUrl": channel_url or "",
                "targetUser": target_user or "",
            },
        },
    )
    return context

def load_case(case_id: str) -> CaseContext:
    runtime_candidate = _case_root(runtime_root(), case_id)
    saved_candidate = _case_root(cases_root(), case_id)
    root: Path
    saved = False
    if runtime_candidate.exists():
        root = runtime_candidate
    elif saved_candidate.exists():
        root = saved_candidate
        saved = True
    else:
        raise FileNotFoundError(f"Case not found: {case_id}")

    data = _ensure_case_metadata(root, saved)
    return CaseContext(case_id=root.name, app_id=data["appId"], root=root, saved=saved or data.get("saved", False))

def save_case(case_id: str) -> CaseContext:
    context = load_case(case_id)
    if context.saved:
        return context

    destination = ensure_dir(cases_root()) / context.case_id
    if destination.exists():
        raise FileExistsError(f"Saved case already exists: {context.case_id}")
    shutil.move(str(context.root), str(destination))
    write_json(
        case_file(destination),
        {
            **read_json(case_file(destination)),
            "status": "saved",
            "saved": True,
            "savedAt": now_iso(),
        },
    )
    saved_context = CaseContext(case_id=context.case_id, app_id=context.app_id, root=destination, saved=True)
    report_snapshot = saved_context.report_dir / "case_snapshot.json"
    if report_snapshot.exists():
        from fdctl.services.report_service import refresh_report_outputs
        refresh_report_outputs(saved_context)
    return saved_context

def discard_case(case_id: str) -> None:
    context = load_case(case_id)
    print_status("warn", "Discarding case and deleting forensic outputs.", str(context.root))
    remove_tree(context.root)
    print_status("warn", "Case discarded.", case_id)
