from __future__ import annotations

from pathlib import Path

from fdctl.models import CaseContext
from fdctl.utils import (
    copy_file_preserve,
    ensure_dir,
    iter_files,
    now_iso,
    read_json,
    relative_to,
    remove_tree,
    write_csv,
    write_json,
)


TEXTUAL_EVIDENCE_SUFFIXES = {
    ".csv",
    ".db",
    ".json",
    ".ldb",
    ".localstorage",
    ".log",
    ".sqlite",
    ".sqlite3",
    ".txt",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".bmp",
    ".heic",
    ".heif",
    ".tiff",
}

RELEVANT_ACQUIRED_TOKENS = {
    "cache",
    "code cache",
    "indexeddb",
    "leveldb",
    "local storage",
    "logs",
    "service worker",
    "session storage",
    "tdata",
    "telegram",
    "user_data",
}


def _copied_entry(case: CaseContext, source: Path, destination: Path, section: str) -> dict:
    stats = destination.stat()
    return {
        "section": section,
        "sourcePath": str(source),
        "bundlePath": relative_to(destination, case.autopsy_dir),
        "sizeBytes": stats.st_size,
        "modifiedTime": stats.st_mtime,
    }


def _copy_file_group(case: CaseContext, label: str, source_paths: list[Path], destination_root: Path) -> list[dict]:
    copied: list[dict] = []
    for source in source_paths:
        if not source.exists() or not source.is_file():
            continue
        destination = destination_root / source.name
        copy_file_preserve(source, destination)
        copied.append(_copied_entry(case, source, destination, label))
    return copied


def _copy_tree(case: CaseContext, label: str, source_root: Path, destination_root: Path) -> list[dict]:
    copied: list[dict] = []
    if not source_root.exists():
        return copied
    for source in iter_files(source_root):
        destination = destination_root / source.relative_to(source_root)
        copy_file_preserve(source, destination)
        copied.append(_copied_entry(case, source, destination, label))
    return copied


def _is_relevant_acquired(path: Path) -> bool:
    suffix = path.suffix.lower()
    if suffix in TEXTUAL_EVIDENCE_SUFFIXES:
        return True
    lowered = str(path).lower().replace("/", "\\")
    if "\\discordroaming\\network\\cookies" in lowered:
        return True
    return any(token in lowered for token in RELEVANT_ACQUIRED_TOKENS)


def _inventory_rows(root: Path, section: str, case_root: Path) -> list[dict]:
    rows: list[dict] = []
    if not root.exists():
        return rows
    for path in iter_files(root):
        stats = path.stat()
        rows.append(
            {
                "section": section,
                "path": relative_to(path, case_root),
                "sizeBytes": stats.st_size,
                "modifiedTime": stats.st_mtime,
            }
        )
    rows.sort(key=lambda item: str(item.get("path", "")))
    return rows


def _read_scope(case: CaseContext) -> dict:
    case_file = case.root / "case.json"
    if case_file.exists():
        case_data = read_json(case_file)
        scope = case_data.get("scope", {}) if isinstance(case_data, dict) else {}
        if isinstance(scope, dict):
            return scope
    return {}


def _read_analysis_summary(case: CaseContext) -> dict:
    path = case.exports_dir / "analysis_summary.json"
    if path.exists():
        return read_json(path)
    return {}


def _read_collection_summary(case: CaseContext) -> dict:
    path = case.info_dir / "collection_summary.json"
    if path.exists():
        return read_json(path)
    return {}


def build_autopsy_bundle(case: CaseContext) -> dict:
    bundle_root = case.autopsy_dir
    remove_tree(bundle_root)
    ensure_dir(bundle_root)

    metadata_root = ensure_dir(bundle_root / "01_Metadata")
    live_root = ensure_dir(bundle_root / "02_Live_Response")
    exports_root = ensure_dir(bundle_root / "03_Exports")
    browser_root = ensure_dir(bundle_root / "04_Browser_Artifacts")
    acquired_root = ensure_dir(bundle_root / "05_Relevant_Acquired_Files")

    copied_rows: list[dict] = []

    metadata_files = [
        case.root / "case.json",
        case.info_dir / "collection_summary.json",
        case.info_dir / "collection_result.json",
        case.info_dir / "user_context.json",
        case.info_dir / "artifact_manifest.csv",
        case.info_dir / "copy_errors.csv",
        case.live_dir / "network_identity.json",
        case.live_dir / "local_ipv4_addresses.csv",
        case.live_dir / "remote_ip_addresses.csv",
        case.exports_dir / "analysis_summary.json",
        case.exports_dir / "scope_summary.json",
        case.exports_dir / "target_user_summary.json",
        case.report_dir / "Muc_luc_bao_cao.md",
        case.report_dir / "Bien_ban_ban_giao.md",
    ]
    copied_rows.extend(_copy_file_group(case, "metadata", metadata_files, metadata_root))
    copied_rows.extend(_copy_tree(case, "live_response", case.live_dir, live_root))
    copied_rows.extend(_copy_tree(case, "exports", case.exports_dir, exports_root))
    copied_rows.extend(_copy_tree(case, "browser_artifacts", case.browser_dir, browser_root))

    for source in iter_files(case.acquired_dir):
        if not _is_relevant_acquired(source):
            continue
        destination = acquired_root / source.relative_to(case.acquired_dir)
        copy_file_preserve(source, destination)
        copied_rows.append(_copied_entry(case, source, destination, "relevant_acquired"))

    copied_rows.sort(key=lambda item: (str(item.get("section", "")), str(item.get("bundlePath", ""))))
    write_csv(
        bundle_root / "autopsy_bundle_inventory.csv",
        copied_rows,
        ["section", "sourcePath", "bundlePath", "sizeBytes", "modifiedTime"],
    )

    source_inventory = (
        _inventory_rows(case.live_dir, "live_response", case.root)
        + _inventory_rows(case.acquired_dir, "acquired_files", case.root)
        + _inventory_rows(case.browser_dir, "browser_artifacts", case.root)
        + _inventory_rows(case.exports_dir, "exports", case.root)
        + _inventory_rows(case.images_dir, "screenshots", case.root)
    )
    write_csv(
        bundle_root / "case_source_inventory.csv",
        source_inventory,
        ["section", "path", "sizeBytes", "modifiedTime"],
    )
    # Build a Data Sources manifest grouping browser DBs, LevelDB, logs and timeline evidence
    data_sources_root = ensure_dir(bundle_root / "06_Data_Sources")
    browser_dbs: list[dict] = []
    discord_desktop_sqlite: list[dict] = []
    leveldb_items: list[dict] = []
    log_files: list[dict] = []
    timeline_files: list[dict] = []
    audit_log_exports: list[dict] = []

    for entry in copied_rows:
        src = str(entry.get("sourcePath", "") or "")
        bundle_path = str(entry.get("bundlePath", "") or "")
        if not src:
            continue
        low = src.lower()
        name = Path(src).name
        item = {
            "label": name,
            "sourcePath": src,
            "bundlePath": bundle_path,
            "sizeBytes": entry.get("sizeBytes", 0),
            "modifiedTime": entry.get("modifiedTime", 0),
        }

        # Timeline evidence (exports)
        if "timeline.csv" in low or name.lower() == "timeline.csv":
            timeline_files.append(item)
            continue

        if "\\07_exports\\audit_logs\\" in low or "/07_exports/audit_logs/" in low:
            audit_log_exports.append(item)
            continue

        # LevelDB artifacts
        if "leveldb" in low or name.lower().endswith(".ldb"):
            leveldb_items.append(item)
            continue

        if ("\\discordroaming\\network\\" in low or "/discordroaming/network/" in low) and name.lower().startswith("cookies"):
            discord_desktop_sqlite.append(item)
            continue

        # Browser DBs: Chrome History/Cookies and Firefox places/cookies
        if ("/chrome/" in low or "\\chrome\\" in low or "/firefox/" in low or "\\firefox\\" in low) and (
            name.lower() in ("history", "cookies") or name.lower().endswith("places.sqlite") or name.lower().endswith("cookies.sqlite")
        ):
            browser_dbs.append(item)
            continue

        # Logs
        if name.lower().endswith(".log") or "/log/" in low or "\\log\\" in low or "logs" in low:
            log_files.append(item)

    data_sources = {
        "caseId": case.case_id,
        "generatedAt": now_iso(),
        "dataSources": {
            "browserDatabases": browser_dbs,
            "discordDesktopCookiesDb": discord_desktop_sqlite,
            "leveldb": leveldb_items,
            "logs": log_files,
            "timeline": timeline_files,
            "auditLogExports": audit_log_exports,
        },
        "counts": {
            "browserDatabases": len(browser_dbs),
            "discordDesktopCookiesDb": len(discord_desktop_sqlite),
            "leveldb": len(leveldb_items),
            "logs": len(log_files),
            "timeline": len(timeline_files),
            "auditLogExports": len(audit_log_exports),
        },
    }
    write_json(data_sources_root / "data_sources_manifest.json", data_sources)

    collection_summary = _read_collection_summary(case)
    analysis_summary = _read_analysis_summary(case)
    scope = _read_scope(case)
    manifest = {
        "caseId": case.case_id,
        "appId": case.app_id,
        "generatedAt": now_iso(),
        "bundleRoot": str(bundle_root),
        "bundleType": "autopsy_ready_bundle",
        "note": "This folder is an Autopsy-ready evidence package generated by fdctl, not a native Autopsy project database.",
        "scope": scope,
        "counts": {
            "copiedRows": len(copied_rows),
            "sourceInventoryRows": len(source_inventory),
            "artifactCount": collection_summary.get("artifactCount", 0),
            "copyErrorCount": collection_summary.get("copyErrorCount", 0),
            "recoveredMessages": analysis_summary.get("recoveredMessageRows", 0),
            "timelineRows": analysis_summary.get("timelineRows", 0),
            "dataSources": data_sources.get("counts", {}),
        },
        "sources": {
            "caseRoot": str(case.root),
            "liveRoot": str(case.live_dir),
            "acquiredRoot": str(case.acquired_dir),
            "browserRoot": str(case.browser_dir),
            "exportsRoot": str(case.exports_dir),
            "reportRoot": str(case.report_dir),
        },
        "dataSourcesManifest": str(data_sources_root / "data_sources_manifest.json"),
    }
    write_json(bundle_root / "autopsy_bundle_manifest.json", manifest)

    readme = [
        "# Autopsy-Ready Bundle",
        "",
        f"- Case ID: {case.case_id}",
        f"- App ID: {case.app_id}",
        f"- Generated: {manifest['generatedAt']}",
        "",
        "## Muc dich",
        "",
        "- Thu muc nay duoc fdctl tao de gom cac du lieu phuc vu import/doi chieu trong Autopsy.",
        "- Day khong phai la native project database cua Autopsy.",
        "",
        "## Noi dung chinh",
        "",
        "- 01_Metadata: metadata va tom tat dieu tra",
        "- 02_Live_Response: process, TCP, network identity",
        "- 03_Exports: CSV/JSON/TXT phan tich",
        "- 04_Browser_Artifacts: browser databases da sao chep",
        "- 05_Relevant_Acquired_Files: cac file acquired co lien quan cao den noi dung dieu tra",
        "- autopsy_bundle_manifest.json: thong tin tong hop bundle",
        "- autopsy_bundle_inventory.csv: danh sach file duoc dua vao bundle",
        "- case_source_inventory.csv: inventory day du cua du lieu goc trong case",
        "",
        "## Scope",
        "",
        f"- Channel URL: {scope.get('channelUrl', '')}",
        f"- Target User: {scope.get('targetUser', '')}",
        "",
        "## Nguon goc du lieu",
        "",
        f"- Case root: {case.root}",
        f"- Acquired files root: {case.acquired_dir}",
        f"- Browser artifacts root: {case.browser_dir}",
        f"- Exports root: {case.exports_dir}",
    ]
    (bundle_root / "README_Autopsy_Bundle.md").write_text("\n".join(readme), encoding="utf-8")
    return manifest
