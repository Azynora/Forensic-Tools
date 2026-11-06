from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import Image

from fdctl.models import CaseContext, WORK_DIR_NAMES
from fdctl.services.report_layout import case_snapshot_path
from fdctl.utils import copy_file_preserve, ensure_dir, iter_files, now_iso, query_sqlite_rows, read_csv, relative_to, write_csv, write_json


DESKTOP_COOKIE_QUERY = """
SELECT
  host_key,
  name,
  path,
  is_secure,
  is_httponly,
  has_expires,
  expires_utc,
  last_access_utc
FROM cookies
WHERE host_key LIKE '%discord%'
ORDER BY last_access_utc DESC;
"""


AUDIT_LOG_ACTIONS = {"72", "73"}
AUDIT_IMPORT_DROP_DIRNAME = "External_Audit_Logs"


def _normalize_time(value: Any) -> str:
    if value in {"", None}:
        return ""
    text = str(value)
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        return datetime.fromisoformat(text).astimezone().isoformat()
    except ValueError:
        return str(value)


def _folder_inventory(case: CaseContext) -> list[dict]:
    rows: list[dict] = []
    for folder_name in WORK_DIR_NAMES:
        folder = case.root / folder_name
        files = list(iter_files(folder)) if folder.exists() else []
        newest = ""
        if files:
            newest = datetime.fromtimestamp(max(path.stat().st_mtime for path in files)).astimezone().isoformat()
        rows.append(
            {
                "Folder": folder_name,
                "Exists": folder.exists(),
                "FileCount": len(files),
                "TotalBytes": sum(path.stat().st_size for path in files),
                "Newest": newest,
            }
        )
    return rows


def _screenshot_validation(case: CaseContext) -> list[dict]:
    rows: list[dict] = []
    for image_path in sorted(iter_files(case.images_dir)) if case.images_dir.exists() else []:
        if image_path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".bmp"}:
            continue
        valid = True
        width = ""
        height = ""
        error = ""
        try:
            with Image.open(image_path) as image:
                width = image.width
                height = image.height
                image.verify()
        except Exception as exc:
            valid = False
            error = str(exc)
        size_bytes = image_path.stat().st_size
        rows.append(
            {
                "Path": str(image_path),
                "Length": size_bytes,
                "Valid": valid,
                "Width": width,
                "Height": height,
                "Error": error,
                "NeedsRefresh": (not valid) or size_bytes < 7000,
            }
        )
    return rows


def _looks_like_audit_log_export(path: Path) -> bool:
    if not path.exists() or path.suffix.lower() != ".json":
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return False
    return isinstance(payload, dict) and isinstance(payload.get("audit_log_entries"), list)


def _audit_search_roots(case: CaseContext) -> list[tuple[Path, str]]:
    dropped_dir = ensure_dir(case.info_dir / AUDIT_IMPORT_DROP_DIRNAME)
    import_cache_dir = ensure_dir(case.exports_dir / "audit_logs")
    return [
        (dropped_dir, "case_drop_folder"),
        (Path.home() / "Downloads", "downloads"),
        (Path.home() / "Desktop", "desktop"),
        (import_cache_dir, "import_cache"),
    ]


def _destination_for_audit_log(import_dir: Path, candidate: Path) -> Path:
    destination = import_dir / candidate.name
    if not destination.exists():
        return destination
    try:
        if destination.resolve() == candidate.resolve():
            return destination
    except OSError:
        pass
    if destination.stat().st_size == candidate.stat().st_size:
        return destination
    stem = candidate.stem
    suffix = candidate.suffix
    counter = 1
    while True:
        numbered = import_dir / f"{stem}_{counter}{suffix}"
        if not numbered.exists():
            return numbered
        counter += 1


def import_external_audit_logs(case: CaseContext) -> list[dict]:
    import_dir = ensure_dir(case.exports_dir / "audit_logs")
    rows: list[dict] = []
    seen_sources: set[str] = set()
    seen_destinations: set[str] = set()
    for root, source_kind in _audit_search_roots(case):
        if not root.exists():
            continue
        for candidate in root.rglob("*.json"):
            if not candidate.is_file():
                continue
            if candidate.stat().st_size > 8 * 1024 * 1024:
                continue
            source_key = str(candidate.resolve())
            if source_key in seen_sources:
                continue
            if import_dir in candidate.resolve().parents:
                if _looks_like_audit_log_export(candidate):
                    seen_sources.add(source_key)
                    destination_key = str(candidate.resolve())
                    if destination_key in seen_destinations:
                        continue
                    seen_destinations.add(destination_key)
                    rows.append(
                        {
                            "sourcePath": str(candidate),
                            "copiedPath": str(candidate),
                            "fileName": candidate.name,
                            "sizeBytes": candidate.stat().st_size,
                            "sourceKind": source_kind,
                        }
                    )
                continue
            if not any(token in candidate.name.lower() for token in ("audit", "discord", "delete", "message")):
                if not _looks_like_audit_log_export(candidate):
                    continue
            elif not _looks_like_audit_log_export(candidate):
                continue

            seen_sources.add(source_key)
            destination = _destination_for_audit_log(import_dir, candidate)
            if not destination.exists():
                copy_file_preserve(candidate, destination)
            destination_key = str(destination.resolve())
            if destination_key in seen_destinations:
                continue
            seen_destinations.add(destination_key)
            rows.append(
                {
                    "sourcePath": str(candidate),
                    "copiedPath": str(destination),
                    "fileName": candidate.name,
                    "sizeBytes": destination.stat().st_size,
                    "sourceKind": source_kind,
                }
            )

    write_csv(
        case.exports_dir / "audit_log_import_manifest.csv",
        rows,
        ["sourcePath", "copiedPath", "fileName", "sizeBytes", "sourceKind"],
    )
    return rows


def _discord_snowflake_to_iso(snowflake: str) -> str:
    try:
        milliseconds = (int(str(snowflake)) >> 22) + 1420070400000
        return datetime.fromtimestamp(milliseconds / 1000).astimezone().isoformat()
    except Exception:
        return ""


def normalize_audit_log_exports(case: CaseContext) -> list[dict]:
    audit_imports = import_external_audit_logs(case)
    rows: list[dict] = []
    seen_entries: set[tuple[str, str]] = set()
    for item in audit_imports:
        copied_path = Path(str(item.get("copiedPath", "") or ""))
        if not copied_path.exists():
            continue
        try:
            payload = json.loads(copied_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        users = {str(user.get("id", "") or ""): user for user in payload.get("users", []) if isinstance(user, dict)}
        for entry in payload.get("audit_log_entries", []) if isinstance(payload, dict) else []:
            if not isinstance(entry, dict):
                continue
            action_type = str(entry.get("action_type", "") or "")
            if action_type not in AUDIT_LOG_ACTIONS:
                continue
            entry_id = str(entry.get("id", "") or "")
            entry_key = (
                entry_id,
                action_type,
                str(entry.get("target_id", "") or ""),
                str(entry.get("user_id", "") or ""),
                str((entry.get("options", {}) or {}).get("channel_id", "") or ""),
            )
            if entry_key in seen_entries:
                continue
            seen_entries.add(entry_key)
            options = entry.get("options", {}) if isinstance(entry.get("options", {}), dict) else {}
            deleter = users.get(str(entry.get("user_id", "") or ""), {})
            target = users.get(str(entry.get("target_id", "") or ""), {})
            rows.append(
                {
                    "AuditEntryId": str(entry.get("id", "") or ""),
                    "ActionType": action_type,
                    "ChannelId": str(options.get("channel_id", "") or ""),
                    "Count": str(options.get("count", "") or ""),
                    "DeleterUserId": str(entry.get("user_id", "") or ""),
                    "DeleterUsername": str(deleter.get("username", "") or ""),
                    "DeleterGlobalName": str(deleter.get("global_name", "") or ""),
                    "TargetUserId": str(entry.get("target_id", "") or ""),
                    "TargetUsername": str(target.get("username", "") or ""),
                    "TargetGlobalName": str(target.get("global_name", "") or ""),
                    "CreatedAtLocal": _discord_snowflake_to_iso(str(entry.get("id", "") or "")),
                    "SourceFile": str(copied_path),
                    "SourceKind": str(item.get("sourceKind", "") or ""),
                }
            )
    rows.sort(key=lambda row: str(row.get("CreatedAtLocal", "") or ""))
    write_csv(
        case.exports_dir / "audit_log_delete_normalized.csv",
        rows,
        [
            "AuditEntryId",
            "ActionType",
            "ChannelId",
            "Count",
            "DeleterUserId",
            "DeleterUsername",
            "DeleterGlobalName",
            "TargetUserId",
            "TargetUsername",
            "TargetGlobalName",
            "CreatedAtLocal",
            "SourceFile",
            "SourceKind",
        ],
    )
    return rows


def _desktop_cookie_rows(case: CaseContext) -> list[dict]:
    cookie_db = case.acquired_dir / "DiscordRoaming" / "Network" / "Cookies"
    rows = query_sqlite_rows(cookie_db, DESKTOP_COOKIE_QUERY)
    for row in rows:
        row["sourceDatabase"] = str(cookie_db)
    return rows


def _recovered_trace_rows(case: CaseContext) -> list[dict]:
    recovered = read_csv(case.exports_dir / "recovered_messages.csv")
    deleted = {
        str(row.get("messageId", "") or ""): row for row in read_csv(case.exports_dir / "deleted_message_candidate.csv")
    }
    rows: list[dict] = []
    for row in recovered:
        message_id = str(row.get("messageId", "") or "")
        deletion_hit = deleted.get(message_id)
        if deletion_hit:
            current_state = "candidate_deleted"
            reason = str(deletion_hit.get("reason", "") or "deletion_candidate")
        else:
            current_state = "recovered_local"
            reason = "present_in_local_case_exports"
        rows.append(
            {
                "MessageId": message_id,
                "ChannelId": row.get("channelId", ""),
                "AuthorUsername": row.get("authorDisplayName", "") or row.get("authorUsername", ""),
                "TimestampUtc": _normalize_time(row.get("timestamp", "")),
                "Content": row.get("content", ""),
                "AttachmentNames": row.get("attachmentNames", ""),
                "CurrentState": current_state,
                "TraceReason": reason,
                "MessageLink": row.get("messageLink", ""),
                "TargetMatched": row.get("targetMatched", ""),
                "ScopeMatched": row.get("scopeMatched", ""),
                "SourcePath": row.get("sourcePath", ""),
            }
        )
    return rows


def _key_artifact_rows(case: CaseContext) -> list[dict]:
    candidates = [
        ("Case metadata", case.root / "case.json", "Case scope and lifecycle metadata"),
        ("Collection summary", case.info_dir / "collection_summary.json", "Collection status and detection snapshot"),
        ("Artifact manifest", case.info_dir / "artifact_manifest.csv", "Copied evidence inventory"),
        ("Folder inventory", case.info_dir / "folder_inventory.csv", "Eight-folder case inventory"),
        ("Screenshot validation", case.info_dir / "screenshot_validation.csv", "Screenshot health check"),
        ("Process inventory", case.live_dir / "process_inventory.csv", "Live triage process list"),
        ("TCP connections", case.live_dir / "tcp_connections.csv", "Live triage TCP snapshot"),
        ("Recovered messages", case.exports_dir / "recovered_messages.csv", "Recovered Discord messages"),
        ("Recovered trace", case.exports_dir / "recovered_message_trace.csv", "Recovered message trace with state labels"),
        ("Discord desktop Cookies DB", case.acquired_dir / "DiscordRoaming" / "Network" / "Cookies", "Acquired Chromium SQLite database for Discord desktop network cookies"),
        ("Desktop cookies", case.exports_dir / "discord_desktop_cookies_metadata.csv", "Discord desktop cookie metadata"),
        ("Chrome cookies", case.exports_dir / "chrome_discord_cookies_metadata.csv", "Chrome Discord cookie metadata"),
        ("Browser scope", case.exports_dir / "browser_scope_summary.csv", "Scoped browser URL summary"),
        ("Deleted candidates", case.exports_dir / "deleted_message_candidate.csv", "Best-effort deleted message candidates"),
        ("Audit log normalized", case.exports_dir / "audit_log_delete_normalized.csv", "Normalized delete audit data"),
        ("Audit log imports", case.exports_dir / "audit_log_import_manifest.csv", "Imported audit-log JSON manifest"),
        ("Audit log drop folder", case.info_dir / AUDIT_IMPORT_DROP_DIRNAME, "Drop real exported Discord audit-log JSON files here before or after collection"),
        ("Analysis summary", case.exports_dir / "analysis_summary.json", "Analysis roll-up"),
        ("Supplement summary", case.info_dir / "supplement_summary.json", "Supplemental completeness roll-up"),
        ("Report snapshot", case_snapshot_path(case), "In-app report snapshot"),
    ]
    return [
        {
            "label": label,
            "path": str(path),
            "href": path.resolve().as_uri() if path.exists() else "",
            "exists": path.exists(),
            "note": note,
        }
        for label, path, note in candidates
    ]


def _count_rows_for_path(path: Path) -> int | str:
    if not path.exists():
        return ""
    if path.suffix.lower() == ".csv":
        return len(read_csv(path))
    if path.suffix.lower() == ".json":
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return ""
        if isinstance(payload, dict):
            return len(payload.keys())
        if isinstance(payload, list):
            return len(payload)
    return ""


def _completeness_rows(case: CaseContext) -> list[dict]:
    expected = [
        ("collection_summary", case.info_dir / "collection_summary.json", "legacy core"),
        ("artifact_manifest", case.info_dir / "artifact_manifest.csv", "legacy core"),
        ("process_inventory", case.live_dir / "process_inventory.csv", "legacy core"),
        ("tcp_connections", case.live_dir / "tcp_connections.csv", "legacy core"),
        ("folder_inventory", case.info_dir / "folder_inventory.csv", "legacy supplemental"),
        ("screenshot_validation", case.info_dir / "screenshot_validation.csv", "legacy supplemental"),
        ("recovered_messages", case.exports_dir / "recovered_messages.csv", "legacy core"),
        ("recovered_message_trace", case.exports_dir / "recovered_message_trace.csv", "legacy supplemental"),
        ("discord_desktop_cookies_metadata", case.exports_dir / "discord_desktop_cookies_metadata.csv", "legacy supplemental"),
        ("chrome_discord_history", case.exports_dir / "chrome_discord_history.csv", "legacy core"),
        ("chrome_discord_cookies_metadata", case.exports_dir / "chrome_discord_cookies_metadata.csv", "legacy core"),
        ("browser_scope_summary", case.exports_dir / "browser_scope_summary.csv", "legacy supplemental"),
        ("top_authors", case.exports_dir / "top_authors.csv", "legacy supplemental"),
        ("messages_with_attachments", case.exports_dir / "messages_with_attachments.csv", "legacy supplemental"),
        ("deleted_message_candidate", case.exports_dir / "deleted_message_candidate.csv", "legacy supplemental"),
        ("audit_log_delete_normalized", case.exports_dir / "audit_log_delete_normalized.csv", "legacy supplemental"),
        ("audit_log_import_manifest", case.exports_dir / "audit_log_import_manifest.csv", "current supplemental"),
        ("analysis_summary", case.exports_dir / "analysis_summary.json", "current core"),
        ("report_snapshot", case_snapshot_path(case), "current core"),
        ("validation_summary_md", case.report_dir / "validation_summary.md", "current supplemental"),
        ("validation_summary_json", case.report_dir / "validation_summary.json", "current supplemental"),
    ]
    rows: list[dict] = []
    for label, path, source in expected:
        exists = path.exists()
        rows.append(
            {
                "label": label,
                "path": str(path),
                "exists": exists,
                "status": "present" if exists else "missing",
                "rowCount": _count_rows_for_path(path),
                "baselineSource": source,
            }
        )
    return rows


def _supplement_markdown(case: CaseContext, summary: dict) -> Path:
    output = case.report_dir / "Bo_sung_kiem_tra_case.md"
    ensure_dir(output.parent)
    lines = [
        "# Supplemental Case Inspection",
        "",
        f"- Case: {case.case_id}",
        f"- App: {case.app_id}",
        f"- Generated: {now_iso()}",
        "",
        "## Summary",
        "",
        f"- Eight-folder inventory rows: {summary.get('folderInventoryRows', 0)}",
        f"- Screenshot validation rows: {summary.get('screenshotValidationRows', 0)}",
        f"- Screenshot refresh candidates: {summary.get('screenshotRefreshCandidates', 0)}",
        f"- Discord desktop cookie rows: {summary.get('desktopCookieRows', 0)}",
        f"- Audit-log delete rows: {summary.get('auditLogRows', 0)}",
        f"- Recovered message trace rows: {summary.get('recoveredTraceRows', 0)}",
        f"- Completeness present: {summary.get('completenessPresent', 0)}",
        f"- Completeness missing: {summary.get('completenessMissing', 0)}",
        "",
        "## Key outputs",
        "",
        f"- {case.info_dir / 'folder_inventory.csv'}",
        f"- {case.info_dir / 'screenshot_validation.csv'}",
        f"- {case.exports_dir / 'discord_desktop_cookies_metadata.csv'}",
        f"- {case.exports_dir / 'recovered_message_trace.csv'}",
        f"- {case.exports_dir / 'key_artifact_paths.csv'}",
        f"- {case.exports_dir / 'completeness_matrix.csv'}",
        f"- {case.info_dir / 'supplement_summary.json'}",
    ]
    output.write_text("\n".join(lines), encoding="utf-8")
    return output


def run_supplemental_checks(case: CaseContext) -> dict:
    audit_rows = normalize_audit_log_exports(case)
    folder_rows = _folder_inventory(case)
    screenshot_rows = _screenshot_validation(case)
    desktop_cookie_rows = _desktop_cookie_rows(case)
    recovered_trace_rows = _recovered_trace_rows(case)
    key_artifact_rows = _key_artifact_rows(case)

    write_csv(case.info_dir / "folder_inventory.csv", folder_rows, ["Folder", "Exists", "FileCount", "TotalBytes", "Newest"])
    write_csv(
        case.info_dir / "screenshot_validation.csv",
        screenshot_rows,
        ["Path", "Length", "Valid", "Width", "Height", "Error", "NeedsRefresh"],
    )
    write_csv(
        case.exports_dir / "discord_desktop_cookies_metadata.csv",
        desktop_cookie_rows,
        ["host_key", "name", "path", "is_secure", "is_httponly", "has_expires", "expires_utc", "last_access_utc", "sourceDatabase"],
    )
    write_csv(
        case.exports_dir / "recovered_message_trace.csv",
        recovered_trace_rows,
        [
            "MessageId",
            "ChannelId",
            "AuthorUsername",
            "TimestampUtc",
            "Content",
            "AttachmentNames",
            "CurrentState",
            "TraceReason",
            "MessageLink",
            "TargetMatched",
            "ScopeMatched",
            "SourcePath",
        ],
    )
    write_csv(case.exports_dir / "key_artifact_paths.csv", key_artifact_rows, ["label", "path", "href", "exists", "note"])

    completeness_rows = _completeness_rows(case)
    write_csv(case.exports_dir / "completeness_matrix.csv", completeness_rows, ["label", "path", "exists", "status", "rowCount", "baselineSource"])

    summary = {
        "generatedAt": now_iso(),
        "folderInventoryRows": len(folder_rows),
        "screenshotValidationRows": len(screenshot_rows),
        "screenshotRefreshCandidates": len([row for row in screenshot_rows if str(row.get("NeedsRefresh", "")).lower() == "true"]),
        "desktopCookieRows": len(desktop_cookie_rows),
        "auditLogRows": len(audit_rows),
        "recoveredTraceRows": len(recovered_trace_rows),
        "completenessPresent": len([row for row in completeness_rows if row.get("status") == "present"]),
        "completenessMissing": len([row for row in completeness_rows if row.get("status") == "missing"]),
    }
    _supplement_markdown(case, summary)
    write_json(case.info_dir / "supplement_summary.json", summary)
    return summary


def _collect_report_references(report_root: Path, snapshot_path: Path) -> list[dict]:
    if not snapshot_path.exists():
        return []
    rows: list[dict] = []
    seen: set[tuple[str, str]] = set()

    def add_row(kind: str, ref: str) -> None:
        ref = str(ref or "").strip()
        if not ref or ref.startswith(("http://", "https://", "data:", "mailto:", "#")):
            return
        normalized = ref.replace("\\", "/")
        key = (kind, normalized)
        if key in seen:
            return
        seen.add(key)
        target = Path(normalized).resolve() if Path(normalized).is_absolute() else (report_root / normalized).resolve()
        rows.append(
            {
                "kind": kind,
                "reference": normalized,
                "resolvedPath": str(target),
                "exists": target.exists(),
            }
        )

    try:
        payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except Exception:
        payload = {}
    for item in payload.get("resources", []) if isinstance(payload, dict) else []:
        add_row("resource", str(item.get("path", "") or item.get("href", "") or ""))
    for item in payload.get("screenshots", []) if isinstance(payload, dict) else []:
        add_row("screenshot", str(item.get("path", "") or item.get("href", "") or ""))
    for item in payload.get("attachments", []) if isinstance(payload, dict) else []:
        add_row("attachment", str(item.get("sourcePath", "") or item.get("resourcePath", "") or ""))

    return rows


def validate_report_bundle(case: CaseContext) -> dict:
    report_root = case.report_dir
    snapshot_path = case_snapshot_path(case)
    if not report_root.exists():
        return {
            "generatedAt": now_iso(),
            "counts": {"references": 0, "valid": 0, "invalid": 0},
            "rows": [],
        }

    rows = _collect_report_references(report_root, snapshot_path)
    valid = len([row for row in rows if row.get("exists")])
    invalid_rows = [row for row in rows if not row.get("exists")]
    payload = {
        "generatedAt": now_iso(),
        "counts": {"references": len(rows), "valid": valid, "invalid": len(invalid_rows)},
        "rows": rows,
    }
    write_json(report_root / "validation_summary.json", payload)

    lines = [
        "# Report Validation Summary",
        "",
        f"- Generated: {payload['generatedAt']}",
        f"- Total references: {payload['counts']['references']}",
        f"- Valid references: {payload['counts']['valid']}",
        f"- Invalid references: {payload['counts']['invalid']}",
        "",
    ]
    if invalid_rows:
        lines.extend(["## Invalid references", ""])
        for row in invalid_rows:
            lines.append(f"- [{row.get('kind')}] {row.get('reference')} -> {row.get('resolvedPath')}")
    else:
        lines.extend(["## Result", "", "- All discovered local report references are valid."])
    (report_root / "validation_summary.md").write_text("\n".join(lines), encoding="utf-8")
    return payload
