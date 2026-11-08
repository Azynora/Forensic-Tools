from __future__ import annotations
from pathlib import Path

from fdctl.models import CaseContext
from fdctl.services.report_layout import case_snapshot_path
from fdctl.utils import read_csv, read_json


EXPORT_FILES = [
    "recovered_messages.csv",
    "recovered_message_trace.csv",
    "messages_with_attachments.csv",
    "top_authors.csv",
    "timeline.csv",
    "target_user_messages.csv",
    "target_user_timeline.csv",
    "direct_messages.csv",
    "group_messages.csv",
    "cache_inventory.csv",
    "discord_desktop_cookies_metadata.csv",
    "chrome_discord_history.csv",
    "chrome_discord_cookies_metadata.csv",
    "browser_scope_summary.csv",
    "scope_links.csv",
    "string_hits.csv",
    "deleted_message_candidate.csv",
    "audit_log_delete_normalized.csv",
    "audit_log_import_manifest.csv",
    "key_artifact_paths.csv",
    "completeness_matrix.csv",
    "scope_summary.json",
    "target_user_summary.json",
    "target_user_fulltext.txt",
    "deleted_message_candidate_fulltext.txt",
    "zalo_file_inventory.csv",
    "telegram_carved_entities.csv",
    "telegram_media_cache.csv",
    "telegram_browser_history.csv",
    "telegram_account_summary.json",
]


def _load_csv(case: CaseContext, filename: str) -> list[dict]:
    return read_csv(case.exports_dir / filename)


def _normalize_case_meta(case: CaseContext, case_meta: dict) -> dict:
    return {
        **case_meta,
        "case_id": case_meta.get("caseId", case.case_id),
        "app_id": case_meta.get("appId", case.app_id),
        "created_at": case_meta.get("createdAt", ""),
        "saved_at": case_meta.get("savedAt", ""),
    }


def _frontend_recovered(rows: list[dict]) -> list[dict]:
    normalized: list[dict] = []
    for row in rows:
        normalized.append(
            {
                **row,
                "author_username": row.get("authorDisplayName", "") or row.get("authorUsername", ""),
                "author_id": row.get("authorId", ""),
                "channel_name": row.get("channelId", ""),
                "channel_url": row.get("messageLink", ""),
                "attachment_names": row.get("attachmentNames", ""),
                "attachment_count": len([n for n in str(row.get("attachmentNames", "")).split(";") if n.strip()]),
                "message_type": row.get("messageType", ""),
            }
        )
    return normalized


def _frontend_attachments(rows: list[dict], recovered_rows: list[dict]) -> list[dict]:
    message_index = {str(row.get("messageId", "")): row for row in recovered_rows}
    normalized: list[dict] = []
    for row in rows:
        recovered = message_index.get(str(row.get("messageId", "")), {})
        normalized.append(
            {
                **row,
                "filename": row.get("attachmentName", ""),
                "file_size": "",
                "author_username": row.get("authorUsername", "") or recovered.get("authorDisplayName", "") or recovered.get("authorUsername", ""),
                "author_id": recovered.get("authorId", ""),
                "timestamp": recovered.get("timestamp", ""),
                "channel_name": row.get("channelId", "") or recovered.get("channelId", ""),
                "sourcePath": row.get("sourcePath", ""),
                "attachment_type": row.get("attachmentType", ""),
            }
        )
    return normalized


def _frontend_top_authors(rows: list[dict]) -> list[dict]:
    return [
        {
            **row,
            "author_username": row.get("authorDisplayName", ""),
            "author_id": "",
            "message_count": row.get("messageCount", 0),
        }
        for row in rows
    ]


def _frontend_timeline(rows: list[dict]) -> list[dict]:
    return [
        {
            **row,
            "timestamp": row.get("timeLocal", ""),
            "author_username": row.get("actor", ""),
            "content": row.get("detail", ""),
            "channel_name": row.get("channelId", ""),
        }
        for row in rows
    ]


def _frontend_browser_history(rows: list[dict]) -> list[dict]:
    return [
        {
            **row,
            "last_visit_time": row.get("visitTimeLocal", ""),
            "visit_count": row.get("visitCount", 0),
        }
        for row in rows
    ]


def _frontend_browser_cookies(rows: list[dict]) -> list[dict]:
    return [
        {
            **row,
            "domain": row.get("hostKey", row.get("host_key", "")),
            "value": row.get("value", ""),
            "expires_utc": row.get("expiresUtc", row.get("expires_utc", row.get("expiry", ""))),
        }
        for row in rows
    ]


def _screenshots(case: CaseContext) -> list[dict]:
    rows: list[dict] = []
    for item in sorted(case.images_dir.glob("*")):
        if item.is_file() and item.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
            rows.append(
                {
                    "name": item.name,
                    "path": str(item),
                    "href": item.resolve().as_uri(),
                }
            )
    return rows


def _resources(case: CaseContext) -> list[dict]:
    resources: list[dict] = []
    candidate_paths = [
        case.root / "case.json",
        case.autopsy_dir / "README_Autopsy_Bundle.md",
        case.autopsy_dir / "autopsy_bundle_manifest.json",
        case.autopsy_dir / "autopsy_bundle_inventory.csv",
        case.autopsy_dir / "case_source_inventory.csv",
        case.info_dir / "collection_summary.json",
        case.info_dir / "collection_result.json",
        case.info_dir / "folder_inventory.csv",
        case.info_dir / "screenshot_validation.csv",
        case.info_dir / "supplement_summary.json",
        case.info_dir / "user_context.json",
        case.live_dir / "network_identity.json",
        case.live_dir / "local_ipv4_addresses.csv",
        case.live_dir / "remote_ip_addresses.csv",
        case.exports_dir / "analysis_summary.json",
        case.report_dir / "Muc_luc_bao_cao.md",
        case.report_dir / "Bien_ban_ban_giao.md",
        case.report_dir / "Bo_sung_kiem_tra_case.md",
        case_snapshot_path(case),
        case.report_dir / "validation_summary.md",
        case.report_dir / "validation_summary.json",
        case.autopsy_dir / "06_Data_Sources" / "data_sources_manifest.json",
    ]
    for filename in EXPORT_FILES:
        candidate_paths.append(case.exports_dir / filename)
    audit_import_dir = case.exports_dir / "audit_logs"
    if audit_import_dir.exists():
        for path in sorted(audit_import_dir.glob("*.json")):
            candidate_paths.append(path)
    for path in candidate_paths:
        if path.exists():
            resources.append(
                {
                    "label": path.name,
                    "path": str(path),
                    "href": path.resolve().as_uri(),
                }
            )
    # Include any attachment source files discovered during analysis
    attachments_csv = case.exports_dir / "messages_with_attachments.csv"
    seen: set[str] = {r.get("path") for r in resources if r.get("path")} # type: ignore
    if attachments_csv.exists():
        for att in read_csv(attachments_csv):
            src = str(att.get("sourcePath", "") or "")
            if not src:
                continue
            try:
                p = Path(src)
            except Exception:
                p = None
            if p and p.exists():
                if str(p) in seen:
                    continue
                seen.add(str(p))
                resources.append(
                    {
                        "label": p.name,
                        "path": str(p),
                        "href": p.resolve().as_uri(),
                    }
                )
    return resources


def build_case_schema(case: CaseContext) -> dict:
    case_meta = _normalize_case_meta(case, read_json(case.root / "case.json"))
    collection_summary = read_json(case.info_dir / "collection_summary.json") if (case.info_dir / "collection_summary.json").exists() else {}
    collection_result = read_json(case.info_dir / "collection_result.json") if (case.info_dir / "collection_result.json").exists() else {}
    analysis_summary = read_json(case.exports_dir / "analysis_summary.json") if (case.exports_dir / "analysis_summary.json").exists() else {}
    user_context = read_json(case.info_dir / "user_context.json") if (case.info_dir / "user_context.json").exists() else {}
    network_identity = read_json(case.live_dir / "network_identity.json") if (case.live_dir / "network_identity.json").exists() else {}
    scope_summary = read_json(case.exports_dir / "scope_summary.json") if (case.exports_dir / "scope_summary.json").exists() else {}
    target_user_summary = read_json(case.exports_dir / "target_user_summary.json") if (case.exports_dir / "target_user_summary.json").exists() else {}

    recovered = _load_csv(case, "recovered_messages.csv")
    attachments = _load_csv(case, "messages_with_attachments.csv")
    top_authors = _load_csv(case, "top_authors.csv")
    timeline = _load_csv(case, "timeline.csv")
    target_user_messages = _load_csv(case, "target_user_messages.csv")
    target_user_timeline = _load_csv(case, "target_user_timeline.csv")
    direct_messages = _load_csv(case, "direct_messages.csv")
    group_messages = _load_csv(case, "group_messages.csv")
    cache_inventory = _load_csv(case, "cache_inventory.csv")
    chrome_history = _load_csv(case, "chrome_discord_history.csv")
    chrome_cookies = _load_csv(case, "chrome_discord_cookies_metadata.csv")
    desktop_cookies = _load_csv(case, "discord_desktop_cookies_metadata.csv")
    browser_scope = _load_csv(case, "browser_scope_summary.csv")
    scope_links = _load_csv(case, "scope_links.csv")
    string_hits = _load_csv(case, "string_hits.csv")
    deleted_candidates = _load_csv(case, "deleted_message_candidate.csv")
    recovered_trace = _load_csv(case, "recovered_message_trace.csv")
    key_artifact_paths = _load_csv(case, "key_artifact_paths.csv")
    completeness_matrix = _load_csv(case, "completeness_matrix.csv")
    audit_log = _load_csv(case, "audit_log_delete_normalized.csv")
    process_inventory = read_csv(case.live_dir / "process_inventory.csv")
    tcp_connections = read_csv(case.live_dir / "tcp_connections.csv")
    artifact_manifest = read_csv(case.info_dir / "artifact_manifest.csv")
    copy_errors = read_csv(case.info_dir / "copy_errors.csv")
    folder_inventory = read_csv(case.info_dir / "folder_inventory.csv")
    screenshot_validation = read_csv(case.info_dir / "screenshot_validation.csv")
    supplement_summary = read_json(case.info_dir / "supplement_summary.json") if (case.info_dir / "supplement_summary.json").exists() else {}
    report_validation = read_json(case.report_dir / "validation_summary.json") if (case.report_dir / "validation_summary.json").exists() else {}
    screenshots = _screenshots(case)

    detection = collection_summary.get("detection", {}) if isinstance(collection_summary, dict) else {}
    app_paths = detection.get("installPaths", []) if isinstance(detection, dict) else []

    return {
        "case": case_meta,
        "summary": {
            "artifactCount": len(artifact_manifest),
            "copyErrorCount": len(copy_errors),
            "processCount": len(process_inventory),
            "tcpCount": len(tcp_connections),
            "recoveredMessages": len(recovered),
            "timelineRows": len(timeline),
            "targetUserRows": len(target_user_messages),
            "directMessages": len(direct_messages),
            "groupMessages": len(group_messages),
            "attachments": len(attachments),
            "cacheArtifacts": len(cache_inventory),
            "topAuthors": len(top_authors),
            "chromeHistoryRows": len(chrome_history),
            "chromeCookieRows": len(chrome_cookies),
            "desktopCookieRows": len(desktop_cookies),
            "browserScopeRows": len(browser_scope),
            "scopeLinks": len(scope_links),
            "deletedCandidates": len(deleted_candidates),
            "completenessPresent": supplement_summary.get("completenessPresent", 0) if isinstance(supplement_summary, dict) else 0,
            "completenessMissing": supplement_summary.get("completenessMissing", 0) if isinstance(supplement_summary, dict) else 0,
        },
        "collection": collection_summary,
        "collectionResult": collection_result,
        "analysis": analysis_summary,
        "scope": scope_summary,
        "system": {
            "userContext": user_context,
            "networkIdentity": network_identity,
            "targetUserSummary": target_user_summary,
        },
        "links": {
            "caseRoot": str(case.root),
            "liveRoot": str(case.live_dir),
            "acquiredRoot": str(case.acquired_dir),
            "browserRoot": str(case.browser_dir),
            "autopsyRoot": str(case.autopsy_dir),
            "exportsRoot": str(case.exports_dir),
            "reportRoot": str(case.report_dir),
            "applicationPaths": app_paths,
        },
        "messages": {
            "recovered": recovered,
            "timeline": timeline,
            "targetUserMessages": target_user_messages,
            "targetUserTimeline": target_user_timeline,
            "attachments": attachments,
            "recoveredTrace": recovered_trace,
            "topAuthors": top_authors,
            "deletedCandidates": deleted_candidates,
            "auditLog": audit_log,
            "scopeLinks": scope_links,
        },
        "recovered": _frontend_recovered(recovered),
        "attachments": _frontend_attachments(attachments, recovered),
        "topAuthors": _frontend_top_authors(top_authors),
        "timeline": _frontend_timeline(timeline),
        "targetUserMessages": _frontend_recovered(target_user_messages),
        "browser": {
            "chromeHistory": _frontend_browser_history(chrome_history),
            "chromeCookies": _frontend_browser_cookies(chrome_cookies),
            "desktopCookies": _frontend_browser_cookies(desktop_cookies),
            "scope": browser_scope,
            "stringHits": string_hits,
        },
        "live": {
            "processInventory": process_inventory,
            "tcpConnections": tcp_connections,
        },
        "artifacts": {
            "manifest": artifact_manifest,
            "copyErrors": copy_errors,
            "cacheInventory": cache_inventory,
        },
        "screenshots": screenshots,
        "resources": _resources(case),
        "dataSources": read_json(case.autopsy_dir / "06_Data_Sources" / "data_sources_manifest.json") if (case.autopsy_dir / "06_Data_Sources" / "data_sources_manifest.json").exists() else {},
        "inspection": {
            "folderInventory": folder_inventory,
            "screenshotValidation": screenshot_validation,
            "completenessMatrix": completeness_matrix,
            "keyArtifactPaths": key_artifact_paths,
            "reportValidation": report_validation,
            "supplementSummary": supplement_summary,
        },
    }
