from __future__ import annotations
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from fdctl.adapters import get_adapters
from fdctl.console import StageProgress, print_section, print_status
from fdctl.models import CaseContext
from fdctl.services.autopsy_service import build_autopsy_bundle
from fdctl.services.supplement_service import normalize_audit_log_exports, run_supplemental_checks
from fdctl.utils import iter_files, query_sqlite_rows, read_csv, read_json, write_csv, write_json


PRINTABLE_PATTERN = re.compile(rb"[\x09\x0A\x0D\x20-\x7E]{40,}")
MESSAGE_PATTERN = re.compile(r'"id":"(?P<message_id>\d{15,20})".{0,1200}?"channel_id":"(?P<channel_id>\d{15,20})".{0,1200}?"content":"(?P<content>(?:\\.|[^"\\])*)"', re.DOTALL)
AUTHOR_ID_PATTERN = re.compile(r'"author":\{.{0,500}?"id":"(?P<author_id>\d{15,20})"', re.DOTALL)
AUTHOR_USERNAME_PATTERN = re.compile(r'"author":\{.{0,500}?"username":"(?P<username>(?:\\.|[^"\\])*)"', re.DOTALL)
AUTHOR_GLOBAL_NAME_PATTERN = re.compile(r'"author":\{.{0,700}?"global_name":"(?P<global_name>(?:\\.|[^"\\])*)"', re.DOTALL)
ATTACHMENT_PATTERN = re.compile(r'"filename":"(?P<filename>(?:\\.|[^"\\])*)"')
TIMESTAMP_PATTERN = re.compile(r'"timestamp":"(?P<timestamp>[^"]+)"')
EDITED_TIMESTAMP_PATTERN = re.compile(r'"edited_timestamp":"(?P<edited_timestamp>[^"]+)"')
GUILD_ID_PATTERN = re.compile(r'"guild_id":"(?P<guild_id>\d{15,20})"')
CHANNEL_LINK_PATTERN = re.compile(r"https?://(?:canary\.|ptb\.)?discord\.com/channels/(?P<guild_id>\d{15,20})(?!\d)/(?P<channel_id>\d{15,20})(?!\d)(?:/(?P<message_id>\d{15,20})(?!\d))?", re.IGNORECASE)
DM_CHANNEL_LINK_PATTERN = re.compile(r"https?://(?:canary\.|ptb\.)?discord\.com/channels/@me(?:/\d{15,20}(?!\d))?", re.IGNORECASE)
DELETE_HINT_PATTERN = re.compile(r"(message_snapshots|deleted?|remove[sd]?|recall(?:ed)?|purge|tombstone)", re.IGNORECASE)
URL_PATTERN = re.compile(r"https://(?:discord\.(?:com|gg)|zalo\.me)/\S+", re.IGNORECASE)

def _query_sqlite(db_path: Path, query: str) -> list[dict]:
    return query_sqlite_rows(db_path, query)

def _decode_match(value: str) -> str:
    return bytes(value, "utf-8").decode("unicode_escape", errors="ignore").replace("\x00", "").strip()

def _clean_url(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    duplicate_marker = text[8:].find("https://")
    if duplicate_marker >= 0:
        text = text[: duplicate_marker + 8]
    text = text.rstrip(")]}>.,;:'\"^")
    dm_match = DM_CHANNEL_LINK_PATTERN.search(text)
    if dm_match:
        return dm_match.group(0)
    match = CHANNEL_LINK_PATTERN.search(text)
    if match:
        guild_id = match.group("guild_id")
        channel_id = match.group("channel_id")
        message_id = match.group("message_id") or ""
        canonical = f"https://discord.com/channels/{guild_id}/{channel_id}"
        if message_id:
            canonical += f"/{message_id}"
        return canonical
    return text

def _pick_first(snippet: str, pattern: re.Pattern[str], group: str) -> str:
    match = pattern.search(snippet)
    if not match:
        return ""
    return _decode_match(match.group(group))

def _discord_scope(case: CaseContext) -> dict:
    case_meta = read_json(case.root / "case.json")
    scope = case_meta.get("scope", {}) if isinstance(case_meta, dict) else {}
    channel_url = str(scope.get("channelUrl", "") or "")
    target_user = str(scope.get("targetUser", "") or "")

    guild_id = ""
    channel_id = ""
    message_id = ""
    match = CHANNEL_LINK_PATTERN.search(channel_url)
    if match:
        guild_id = match.group("guild_id") or guild_id
        channel_id = match.group("channel_id") or channel_id
        message_id = match.group("message_id") or message_id

    return {
        "channelUrl": channel_url,
        "targetUser": target_user,
        "guildId": guild_id,
        "channelId": channel_id,
        "messageId": message_id,
    }

def _message_observations(case: CaseContext, app_id: str) -> dict[str, list[dict]]:
    message_map: dict[str, list[dict]] = {}
    id_prefix = app_id
    for root in [case.acquired_dir, case.browser_dir]:
        if not root.exists():
            continue
        for file_path in iter_files(root):
            if file_path.suffix.lower() not in {".log", ".json", ".txt", ".ldb", ".sqlite", ".localstorage", ""}:
                continue
            try:
                data = file_path.read_bytes()
            except OSError:
                continue
            text = "\n".join(match.decode("utf-8", errors="ignore") for match in PRINTABLE_PATTERN.findall(data))
            for match in MESSAGE_PATTERN.finditer(text):
                snippet = text[max(0, match.start() - 800) : match.end() + 800]
                attachments = "; ".join(_decode_match(item) for item in ATTACHMENT_PATTERN.findall(snippet))
                username = _pick_first(snippet, AUTHOR_USERNAME_PATTERN, "username")
                global_name = _pick_first(snippet, AUTHOR_GLOBAL_NAME_PATTERN, "global_name")
                observation = {
                    "messageId": match.group("message_id"),
                    "channelId": match.group("channel_id"),
                    "guildId": _pick_first(snippet, GUILD_ID_PATTERN, "guild_id"),
                    "authorId": _pick_first(snippet, AUTHOR_ID_PATTERN, "author_id"),
                    "authorUsername": username or global_name or f"{id_prefix}_unknown",
                    "authorDisplayName": global_name or username or f"{id_prefix}_unknown",
                    "content": _decode_match(match.group("content")),
                    "attachmentNames": attachments,
                    "timestamp": _pick_first(snippet, TIMESTAMP_PATTERN, "timestamp"),
                    "editedTimestamp": _pick_first(snippet, EDITED_TIMESTAMP_PATTERN, "edited_timestamp"),
                    "deletionHints": "; ".join(sorted({hint.lower() for hint in DELETE_HINT_PATTERN.findall(snippet)})),
                    "sourcePath": str(file_path),
                }
                message_map.setdefault(observation["messageId"], []).append(observation)
    return message_map

def _normalize_iso_to_local(value: str) -> str:
    if not value:
        return ""
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value).astimezone().isoformat()
    except ValueError:
        return value

def _normalize_epoch_to_local(value: str | float | int) -> str:
    if value in {"", None}:
        return ""
    try:
        return datetime.fromtimestamp(float(value)).astimezone().isoformat()
    except (TypeError, ValueError, OSError):
        return str(value)

def _target_matches(target_user: str, author_id: str, author_username: str, author_display_name: str) -> bool:
    normalized = target_user.strip().lstrip("@").lower()
    if not normalized:
        return False
    for candidate in [author_id, author_username, author_display_name]:
        if str(candidate or "").strip().lower() == normalized:
            return True
    return normalized in str(author_username or "").lower() or normalized in str(author_display_name or "").lower()

def _message_link(guild_id: str, channel_id: str, message_id: str) -> str:
    if guild_id and channel_id and message_id:
        return f"https://discord.com/channels/{guild_id}/{channel_id}/{message_id}"
    return ""

def _sort_time_key(value: str) -> tuple[int, str]:
    return (0 if value else 1, value or "")

def _consolidate_messages(observations: dict[str, list[dict]], scope: dict) -> tuple[list[dict], list[dict]]:
    rows: list[dict] = []
    deleted_candidates: list[dict] = []
    scope_channel_id = str(scope.get("channelId", "") or "")
    target_user = str(scope.get("targetUser", "") or "")

    for message_id, entries in observations.items():
        channel_id = next((row["channelId"] for row in entries if row.get("channelId")), "")
        guild_id = next((row["guildId"] for row in entries if row.get("guildId")), "") or str(scope.get("guildId", "") or "")
        author_id = next((row["authorId"] for row in entries if row.get("authorId")), "")
        author_username = next((row["authorUsername"] for row in entries if row.get("authorUsername")), "discord_unknown")
        author_display_name = next((row["authorDisplayName"] for row in entries if row.get("authorDisplayName")), author_username)
        timestamps = sorted({_normalize_iso_to_local(str(row.get("timestamp", ""))) for row in entries if row.get("timestamp")})
        edited_timestamps = sorted({_normalize_iso_to_local(str(row.get("editedTimestamp", ""))) for row in entries if row.get("editedTimestamp")})
        distinct_contents = sorted({str(row.get("content", "") or "") for row in entries if str(row.get("content", "") or "")})
        primary_content = max(distinct_contents, key=len, default="")
        attachment_names = sorted(
            {
                name.strip()
                for row in entries
                for name in str(row.get("attachmentNames", "")).split(";")
                if name.strip()
            }
        )
        deletion_hints = sorted(
            {
                hint.strip()
                for row in entries
                for hint in str(row.get("deletionHints", "")).split(";")
                if hint.strip()
            }
        )
        source_paths = sorted({str(row.get("sourcePath", "")) for row in entries if row.get("sourcePath")})
        first_seen = timestamps[0] if timestamps else ""
        last_seen = edited_timestamps[-1] if edited_timestamps else (timestamps[-1] if timestamps else "")
        target_matched = _target_matches(target_user, author_id, author_username, author_display_name)
        scope_matched = not scope_channel_id or channel_id == scope_channel_id
        source_path = source_paths[0] if source_paths else ""
        row = {
            "messageId": message_id,
            "guildId": guild_id,
            "channelId": channel_id,
            "authorId": author_id,
            "authorUsername": author_username,
            "authorDisplayName": author_display_name,
            "content": primary_content,
            "timestamp": first_seen,
            "editedTimestamp": edited_timestamps[-1] if edited_timestamps else "",
            "firstSeen": first_seen,
            "lastSeen": last_seen,
            "attachmentNames": "; ".join(attachment_names),
            "contentVersionCount": len(distinct_contents),
            "sourceHitCount": len(entries),
            "scopeMatched": "yes" if scope_matched else "no",
            "targetMatched": "yes" if target_matched else "no",
            "messageLink": _message_link(guild_id, channel_id, message_id),
            "sourcePath": source_path,
        }
        # Determine message type (text | link | image | attachment)
        try:
            if attachment_names:
                image_exts = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".heic", ".heif", ".tiff")
                lowered = [n.lower() for n in attachment_names]
                if any(name.endswith(image_exts) for name in lowered):
                    message_type = "image"
                elif any(name.startswith("http") or "://" in name for name in lowered):
                    message_type = "link"
                else:
                    message_type = "attachment"
            else:
                if primary_content and re.search(r"https?://", primary_content):
                    message_type = "link"
                else:
                    message_type = "text"
        except Exception:
            message_type = "text"
        row["messageType"] = message_type
        rows.append(row)

        delete_reasons: list[str] = []
        if len(distinct_contents) > 1:
            delete_reasons.append("multiple_content_versions_recovered")
        if deletion_hints:
            delete_reasons.append("deletion_keywords_found")
        if not primary_content and attachment_names:
            delete_reasons.append("empty_content_with_attachment_metadata")

        if delete_reasons:
            deleted_candidates.append(
                {
                    "messageId": message_id,
                    "channelId": channel_id,
                    "authorUsername": author_username,
                    "reason": "; ".join(delete_reasons),
                    "confidence": min(0.95, 0.45 + 0.15 * len(delete_reasons)),
                    "contentPreview": primary_content[:280],
                    "messageLink": _message_link(guild_id, channel_id, message_id),
                    "sourcePath": source_path,
                }
            )

    rows.sort(key=lambda item: _sort_time_key(str(item.get("timestamp", ""))))
    filtered_rows = [row for row in rows if str(row.get("scopeMatched", "")) == "yes"]
    return filtered_rows or rows, deleted_candidates

def _extract_string_hits(case: CaseContext, pattern: str) -> list[dict]:
    hits: list[dict] = []
    compiled = re.compile(pattern, re.IGNORECASE)
    for root in [case.acquired_dir, case.browser_dir]:
        if not root.exists():
            continue
        for file_path in iter_files(root):
            if file_path.suffix.lower() not in {".log", ".json", ".txt", ".ldb", ".sqlite", ".html", ".js", ""}:
                continue
            try:
                data = file_path.read_bytes()
            except OSError:
                continue
            text = "\n".join(match.decode("utf-8", errors="ignore") for match in PRINTABLE_PATTERN.findall(data))
            for found in compiled.findall(text):
                cleaned = _clean_url(found)
                if cleaned:
                    hits.append({"path": str(file_path), "match": cleaned})
    return hits

def _normalize_attachments(messages: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for message in messages:
        names = [item.strip() for item in str(message.get("attachmentNames", "")).split(";") if item.strip()]
        for index, name in enumerate(names, start=1):
            lower = name.lower()
            image_exts = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".heic", ".heif", ".tiff")
            if lower.endswith(image_exts):
                attachment_type = "image"
            elif lower.startswith("http") or "://" in lower:
                attachment_type = "link"
            else:
                attachment_type = "file"
            rows.append(
                {
                    "messageId": message.get("messageId", ""),
                    "authorUsername": message.get("authorDisplayName") or message.get("authorUsername", ""),
                    "channelId": message.get("channelId", ""),
                    "attachmentIndex": index,
                    "attachmentName": name,
                    "attachmentType": attachment_type,
                    "sourcePath": message.get("sourcePath", ""),
                }
            )
    return rows

def _top_authors(messages: list[dict]) -> list[dict]:
    counter = Counter(row.get("authorDisplayName", "unknown") or "unknown" for row in messages)
    return [
        {"authorDisplayName": username, "messageCount": count}
        for username, count in counter.most_common()
    ]

def _url_scope_rows(hits: list[dict]) -> list[dict]:
    counter = Counter(hit["match"] for hit in hits)
    rows: list[dict] = []
    for url, count in counter.most_common():
        parsed = urlparse(url)
        rows.append(
            {
                "url": url,
                "host": parsed.netloc,
                "path": parsed.path,
                "count": count,
            }
        )
    return rows

def _scoped_browser_history(rows: list[dict], scope: dict) -> list[dict]:
    channel_url = str(scope.get("channelUrl", "") or "")
    server_url = str(scope.get("serverUrl", "") or "")
    channel_id = str(scope.get("channelId", "") or "")
    if not any([channel_url, server_url, channel_id]):
        return rows

    filtered: list[dict] = []
    for row in rows:
        url = str(row.get("url", "") or "")
        if channel_url and channel_url in url:
            filtered.append(row)
            continue
        if server_url and server_url in url:
            filtered.append(row)
            continue
        if channel_id and channel_id in url:
            filtered.append(row)
    return filtered

def _target_user_rows(messages: list[dict], target_user: str) -> list[dict]:
    if not target_user:
        return []
    return [row for row in messages if str(row.get("targetMatched", "")) == "yes"]

def _target_user_summary(target_rows: list[dict], scope: dict) -> dict:
    if not target_rows:
        return {
            "targetUser": str(scope.get("targetUser", "") or ""),
            "matched": False,
            "messageCount": 0,
            "channels": [],
            "firstSeen": "",
            "lastSeen": "",
            "remoteUserIpStatus": "not_available_from_local_discord_artifacts",
        }

    channels = sorted({str(row.get("channelId", "") or "") for row in target_rows if row.get("channelId")})
    timestamps = sorted({str(row.get("timestamp", "") or "") for row in target_rows if row.get("timestamp")})
    return {
        "targetUser": str(scope.get("targetUser", "") or ""),
        "matched": True,
        "messageCount": len(target_rows),
        "channels": channels,
        "firstSeen": timestamps[0] if timestamps else "",
        "lastSeen": timestamps[-1] if timestamps else "",
        "remoteUserIpStatus": "not_available_from_local_discord_artifacts",
    }

def _fulltext_lines(title: str, rows: list[dict]) -> str:
    if not rows:
        return f"{title}\nNo recovered rows.\n"
    blocks: list[str] = [title, ""]
    for row in rows:
        blocks.extend(
            [
                f"Time: {row.get('timestamp') or row.get('firstSeen') or ''}",
                f"Author: {row.get('authorDisplayName') or row.get('authorUsername') or ''} ({row.get('authorId') or ''})",
                f"Channel: {row.get('channelId') or ''}",
                f"Message ID: {row.get('messageId') or ''}",
                f"Link: {row.get('messageLink') or ''}",
                "Content:",
                str(row.get("content", "") or ""),
                "",
            ]
        )
    return "\n".join(blocks).strip() + "\n"


def _merge_audit_context_into_deleted_candidates(
    deleted_candidates: list[dict], recovered: list[dict], audit_rows: list[dict]
) -> list[dict]:
    if not audit_rows:
        return deleted_candidates

    recovered_index = {str(row.get("messageId", "") or ""): row for row in recovered}
    enhanced: list[dict] = []
    seen_message_ids: set[str] = set()

    for candidate in deleted_candidates:
        message_id = str(candidate.get("messageId", "") or "")
        recovered_row = recovered_index.get(message_id, {})
        matched_audit = next(
            (
                row
                for row in audit_rows
                if str(row.get("ChannelId", "") or "") == str(candidate.get("channelId", "") or "")
                and str(row.get("TargetUsername", "") or "").lower() == str(candidate.get("authorUsername", "") or "").lower()
            ),
            None,
        )
        if matched_audit:
            candidate["reason"] = "; ".join(
                filter(
                    None,
                    [
                        str(candidate.get("reason", "") or ""),
                        "matched_real_audit_log",
                    ],
                )
            )
            try:
                candidate["confidence"] = min(0.99, float(candidate.get("confidence", 0) or 0) + 0.25)
            except Exception:
                candidate["confidence"] = 0.85
            candidate["auditEntryId"] = matched_audit.get("AuditEntryId", "")
            candidate["auditActionType"] = matched_audit.get("ActionType", "")
            candidate["auditCreatedAt"] = matched_audit.get("CreatedAtLocal", "")
        enhanced.append(candidate)
        seen_message_ids.add(message_id)

    audit_by_channel: dict[str, list[dict]] = {}
    for row in audit_rows:
        audit_by_channel.setdefault(str(row.get("ChannelId", "") or ""), []).append(row)

    for message in recovered:
        message_id = str(message.get("messageId", "") or "")
        if message_id in seen_message_ids:
            continue
        channel_id = str(message.get("channelId", "") or "")
        matches = audit_by_channel.get(channel_id, [])
        if not matches:
            continue
        author_username = str(message.get("authorUsername", "") or "")
        for audit in matches:
            if str(audit.get("TargetUsername", "") or "").lower() != author_username.lower():
                continue
            enhanced.append(
                {
                    "messageId": message_id,
                    "channelId": channel_id,
                    "authorUsername": author_username,
                    "reason": "matched_real_audit_log",
                    "confidence": 0.8,
                    "contentPreview": str(message.get("content", "") or "")[:280],
                    "messageLink": message.get("messageLink", ""),
                    "sourcePath": message.get("sourcePath", ""),
                    "auditEntryId": audit.get("AuditEntryId", ""),
                    "auditActionType": audit.get("ActionType", ""),
                    "auditCreatedAt": audit.get("CreatedAtLocal", ""),
                }
            )
            break

    return enhanced

def _timeline_rows(
    case: CaseContext,
    messages: list[dict],
    browser_history: list[dict],
    process_inventory: list[dict],
    tcp_connections: list[dict],
    scope: dict,
) -> list[dict]:
    rows: list[dict] = []
    for message in messages:
        timestamp = str(message.get("timestamp", "") or "")
        rows.append(
            {
                "timeLocal": timestamp,
                "eventType": "message_recovered",
                "actor": message.get("authorDisplayName") or message.get("authorUsername") or "",
                "channelId": message.get("channelId", ""),
                "messageId": message.get("messageId", ""),
                "detail": str(message.get("content", "") or "")[:220],
                "source": "recovered_messages.csv",
                "path": message.get("sourcePath", ""),
            }
        )
        if message.get("editedTimestamp"):
            rows.append(
                {
                    "timeLocal": message.get("editedTimestamp", ""),
                    "eventType": "message_edit_seen",
                    "actor": message.get("authorDisplayName") or message.get("authorUsername") or "",
                    "channelId": message.get("channelId", ""),
                    "messageId": message.get("messageId", ""),
                    "detail": f"Edited message {message.get('messageId', '')}",
                    "source": "recovered_messages.csv",
                    "path": message.get("sourcePath", ""),
                }
            )

    scoped_history = _scoped_browser_history(browser_history, scope)
    for row in scoped_history:
        rows.append(
            {
                "timeLocal": row.get("visitTimeLocal", ""),
                "eventType": "browser_visit",
                "actor": "",
                "channelId": "",
                "messageId": "",
                "detail": f"{row.get('title', '')} | {row.get('url', '')}",
                "source": "browser_history",
                "path": row.get("url", ""),
            }
        )

    for proc in process_inventory:
        rows.append(
            {
                "timeLocal": _normalize_epoch_to_local(proc.get("createTime", "")),
                "eventType": "process_start",
                "actor": proc.get("username", ""),
                "channelId": "",
                "messageId": "",
                "detail": f"{proc.get('name', '')} pid={proc.get('pid', '')}",
                "source": "process_inventory.csv",
                "path": proc.get("executablePath", ""),
            }
        )

    collection_summary = read_json(case.info_dir / "collection_summary.json") if (case.info_dir / "collection_summary.json").exists() else {}
    collected_at = _normalize_iso_to_local(str(collection_summary.get("collectedAt", "") or ""))
    for conn in tcp_connections:
        rows.append(
            {
                "timeLocal": collected_at,
                "eventType": "tcp_snapshot",
                "actor": "",
                "channelId": "",
                "messageId": "",
                "detail": f"{conn.get('localAddress', '')} -> {conn.get('remoteAddress', '')} [{conn.get('status', '')}]",
                "source": "tcp_connections.csv",
                "path": conn.get("remoteAddress", ""),
            }
        )

    rows.sort(key=lambda item: _sort_time_key(str(item.get("timeLocal", ""))))
    return rows

def _scope_link_rows(scope: dict, browser_scope: list[dict], messages: list[dict]) -> list[dict]:
    rows: list[dict] = []

    def add(kind: str, url: str, note: str = "") -> None:
        if url:
            rows.append({"kind": kind, "url": url, "note": note})

    add("selected_server", str(scope.get("serverUrl", "") or ""), "Server link supplied by operator")
    add("selected_channel", str(scope.get("channelUrl", "") or ""), "Channel link supplied by operator")
    for item in browser_scope:
        url = str(item.get("url", "") or "")
        if CHANNEL_LINK_PATTERN.fullmatch(url) or DM_CHANNEL_LINK_PATTERN.fullmatch(url):
            add("browser_discovered", url, f"count={item.get('count', '')}")
    for item in messages:
        add("message_link", str(item.get("messageLink", "") or ""), str(item.get("authorDisplayName", "") or item.get("authorUsername", "")))

    deduped: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        key = (row["kind"], row["url"])
        if row["url"] and key not in seen:
            seen.add(key)
            deduped.append(row)
    return deduped

def analyze_discord(case: CaseContext) -> dict:
    print_section("Discord Analysis", f"Case {case.case_id} | Root {case.root}")
    progress = StageProgress(6)
    print_status("step", "Loading operator scope and browser evidence...")
    scope = _discord_scope(case)
    chrome_history = _query_sqlite(
        case.browser_dir / "Chrome" / "History",
        """
        SELECT
          datetime(last_visit_time/1000000-11644473600,'unixepoch','localtime') AS visitTimeLocal,
          url,
          title,
          visit_count AS visitCount,
          typed_count AS typedCount
        FROM urls
        WHERE url LIKE '%discord%'
        ORDER BY last_visit_time DESC
        LIMIT 500
        """,
    )
    chrome_cookies = _query_sqlite(
        case.browser_dir / "Chrome" / "Cookies",
        """
        SELECT host_key AS hostKey, name, path, is_secure AS isSecure, is_httponly AS isHttpOnly,
               has_expires AS hasExpires, expires_utc AS expiresUtc, last_access_utc AS lastAccessUtc
        FROM cookies
        WHERE host_key LIKE '%discord%'
        ORDER BY last_access_utc DESC
        """,
    )
    progress.advance("Chrome artifacts extracted", f"History rows: {len(chrome_history)} | Cookie rows: {len(chrome_cookies)}")

    print_status("step", f"Extracting raw message observations from {case.acquired_dir.name} and {case.browser_dir.name}...")
    observations = _message_observations(case, "discord")
    print_status("info", "Consolidating and deduplicating recovered message threads...", f"Observed threads: {len(observations)}")
    recovered, deleted_candidates = _consolidate_messages(observations, scope)
    progress.advance("Recovered messages consolidated", f"Messages: {len(recovered)} | Deleted candidates: {len(deleted_candidates)}")
    print_status("step", "Extracting Discord URL hits from cached strings...")
    browser_hits = _extract_string_hits(case, URL_PATTERN.pattern)
    scope_rows = _url_scope_rows([hit for hit in browser_hits if "discord" in hit["match"].lower()])
    top_authors = _top_authors(recovered)
    attachment_rows = _normalize_attachments(recovered)
    process_inventory = read_csv(case.live_dir / "process_inventory.csv")
    tcp_connections = read_csv(case.live_dir / "tcp_connections.csv")
    
    print_status("step", "Processing target user matches and timeline correlation...")
    target_rows = _target_user_rows(recovered, str(scope.get("targetUser", "") or ""))
    target_summary = _target_user_summary(target_rows, scope)
    timeline_rows = _timeline_rows(case, recovered, chrome_history, process_inventory, tcp_connections, scope)
    normalized_target = str(scope.get("targetUser", "") or "").strip().lstrip("@").lower()
    target_timeline_rows = [row for row in timeline_rows if normalized_target and normalized_target in str(row.get("actor", "")).lower()]
    scope_links = _scope_link_rows(scope, scope_rows, recovered)
    scoped_history_rows = _scoped_browser_history(chrome_history, scope)
    audit_log_rows = normalize_audit_log_exports(case)
    deleted_candidates = _merge_audit_context_into_deleted_candidates(deleted_candidates, recovered, audit_log_rows)
    progress.advance("Timeline and target-user views prepared", f"Timeline rows: {len(timeline_rows)} | Target rows: {len(target_rows)}")

    print_status("step", "Exporting analysis results to CSV, JSON, and text bundles...")
    write_json(
        case.exports_dir / "scope_summary.json",
        {
            **scope,
            "scopedHistoryRows": len(scoped_history_rows),
            "scopedMessageRows": len(recovered),
            "targetMatchedRows": len(target_rows),
        },
    )
    write_json(case.exports_dir / "target_user_summary.json", target_summary)
    write_csv(case.exports_dir / "chrome_discord_history.csv", chrome_history, ["visitTimeLocal", "url", "title", "visitCount", "typedCount"])
    write_csv(case.exports_dir / "chrome_discord_cookies_metadata.csv", chrome_cookies, ["hostKey", "name", "path", "isSecure", "isHttpOnly", "hasExpires", "expiresUtc", "lastAccessUtc"])
    write_csv(case.exports_dir / "recovered_messages.csv", recovered, ["messageId", "guildId", "channelId", "authorId", "authorUsername", "authorDisplayName", "content", "timestamp", "editedTimestamp", "firstSeen", "lastSeen", "attachmentNames", "contentVersionCount", "sourceHitCount", "scopeMatched", "targetMatched", "messageLink", "messageType", "sourcePath"])
    write_csv(case.exports_dir / "browser_scope_summary.csv", scope_rows, ["url", "host", "path", "count"])
    write_csv(case.exports_dir / "string_hits.csv", browser_hits, ["path", "match"])
    write_csv(case.exports_dir / "top_authors.csv", top_authors, ["authorDisplayName", "messageCount"])
    write_csv(case.exports_dir / "messages_with_attachments.csv", attachment_rows, ["messageId", "authorUsername", "channelId", "attachmentIndex", "attachmentName", "attachmentType", "sourcePath"])
    write_csv(case.exports_dir / "timeline.csv", timeline_rows, ["timeLocal", "eventType", "actor", "channelId", "messageId", "detail", "source", "path", "messageType"])
    write_csv(case.exports_dir / "target_user_messages.csv", target_rows, ["messageId", "guildId", "channelId", "authorId", "authorUsername", "authorDisplayName", "content", "timestamp", "editedTimestamp", "firstSeen", "lastSeen", "attachmentNames", "contentVersionCount", "sourceHitCount", "scopeMatched", "targetMatched", "messageLink", "messageType", "sourcePath"])
    write_csv(case.exports_dir / "target_user_timeline.csv", target_timeline_rows, ["timeLocal", "eventType", "actor", "channelId", "messageId", "detail", "source", "path", "messageType"])
    write_csv(case.exports_dir / "scope_links.csv", scope_links, ["kind", "url", "note"])
    write_csv(case.exports_dir / "deleted_message_candidate.csv", deleted_candidates, ["messageId", "channelId", "authorUsername", "reason", "confidence", "contentPreview", "messageLink", "sourcePath", "auditEntryId", "auditActionType", "auditCreatedAt"])
    (case.exports_dir / "target_user_fulltext.txt").write_text(_fulltext_lines("Recovered target user messages", target_rows), encoding="utf-8")
    (case.exports_dir / "deleted_message_candidate_fulltext.txt").write_text(_fulltext_lines("Recovered deleted-message candidates", deleted_candidates), encoding="utf-8")
    progress.advance("Exports written", f"CSV/JSON outputs: {len(list(case.exports_dir.glob('*')))} files")

    progress.advance("Analysis summary assembled", f"Top authors: {len(top_authors)} | Attachments: {len(attachment_rows)} | Scope links: {len(scope_links)}")
    progress.finish("Discord analysis complete", f"Ready to build report for case {case.case_id}")
    print_status("ok", "Discord analysis complete.", f"Recovered messages: {len(recovered)} | Browser hits: {len(browser_hits)}")
    
    # Print analysis summary table
    print("\n" + "="*90)
    print("  PHAN TICH HOAN TAT - HUONG DAN KHOI TAO TRANG WEB BAO CAO")
    print("="*90)
    print(f"\n>>> THU MUC CASE: {case.root}\n")
    
    print("[*] DU LIEU BROWSER (Browser Artifacts)")
    print(f"    - Chrome History:      {len(chrome_history):6} ban ghi | {case.browser_dir}/Chrome/History")
    print(f"    - Chrome Cookies:      {len(chrome_cookies):6} ban ghi | {case.browser_dir}/Chrome/Cookies")
    print("")
    
    print("[*] DU LIEU DISCORD (Discord Messages)")
    print(f"    - Tin nhan khoi phuc:       {len(recovered):8} | 07_Exports/recovered_messages.csv")
    print(f"    - Timeline su kien:        {len(timeline_rows):8} | 07_Exports/timeline.csv")
    print(f"    - Top tac gia:             {len(top_authors):8} | 07_Exports/top_authors.csv")
    print(f"    - Vat lieu dinh kem:       {len(attachment_rows):8} | 07_Exports/messages_with_attachments.csv")
    print("")
    
    if target_rows:
        print("[*] DU LIEU MUC TIEU (Target User)")
        print(f"    - Tin tu muc tieu:        {len(target_rows):8} | 07_Exports/target_user_messages.csv")
        print(f"    - Timeline muc tieu:      {len(target_timeline_rows):8} | 07_Exports/target_user_timeline.csv")
        print("")
    
    print("[*] LIEN KET VA URL (Scope Links)")
    print(f"    - URL duoc kham pha:       {len(scope_links):8} | 07_Exports/scope_links.csv")
    print(f"    - Ung vien xoa tin:        {len(deleted_candidates):8} | 07_Exports/deleted_message_candidate.csv")
    print("")
    
    print("[*] TEPS METADATA")
    print(f"    - scope_summary.json              | {case.exports_dir}/scope_summary.json")
    print(f"    - analysis_summary.json           | {case.exports_dir}/analysis_summary.json")
    print(f"    - collection_summary.json         | {case.info_dir}/collection_summary.json")
    
    print("\n" + "="*90)
    print("  NEXT STEPS: BUILD AND REVIEW THE TERMINAL REPORT BUNDLE")
    print("="*90)
    print("\nGuidance:")
    print("\n[1] BUILD THE REPORT BUNDLE")
    print(f"    > fdctl report build --case {case.case_id}")
    print("\n[2] OPEN A TERMINAL SUMMARY OF THE REPORT")
    print(f"    > fdctl report open --case {case.case_id}")
    print("\n[3] REVIEW THE CANONICAL REPORT FILES")
    print(f"    - Report index:   {case.report_dir}/Muc_luc_bao_cao.md")
    print(f"    - Handover note:  {case.report_dir}/Bien_ban_ban_giao.md")
    print(f"    - Case snapshot:  {case.report_dir}/case_snapshot.json")
    print("\n[4] REVIEW EXPORTED EVIDENCE")
    print(f"    - Exports:        {case.exports_dir}")
    print(f"    - Autopsy bundle: {case.autopsy_dir}")
    print("\n[5] SAVE OR SHARE THE CASE")
    print(f"    > fdctl case save --case {case.case_id}")
    print(f"    Share Markdown/JSON/CSV from: {case.report_dir}")
    print("\n" + "="*90 + "\n")
    return {
        "scope": scope,
        "chromeHistoryRows": len(chrome_history),
        "chromeCookieRows": len(chrome_cookies),
        "recoveredMessageRows": len(recovered),
        "timelineRows": len(timeline_rows),
        "targetUserRows": len(target_rows),
        "scopeLinkRows": len(scope_links),
        "deletedCandidateRows": len(deleted_candidates),
        "browserScopeRows": len(scope_rows),
        "attachmentRows": len(attachment_rows),
        "topAuthorRows": len(top_authors),
        "notes": [
            "Target user IP cannot be asserted from local Discord client artifacts unless direct network evidence explicitly references that user.",
            "Deleted message recovery is best-effort and based on locally recovered content plus deletion-related indicators.",
        ],
    }

def analyze_zalo(case: CaseContext) -> dict:
    summary = {
        "appId": "zalo",
        "displayName": "Zalo",
        "supportLevel": "planned",
        "caseId": case.case_id,
        "status": "reserved_for_future_implementation",
    }
    write_json(case.exports_dir / "analysis_summary.json", summary)
    return summary


def analyze_telegram(case: CaseContext) -> dict:
    import hashlib
    import re
    from datetime import datetime

    print_section("Telegram Forensic Analyzer", f"Case {case.case_id} | Artifacts root {case.acquired_dir}")
    progress = StageProgress(5)

    acquired_root = case.acquired_dir
    telegram_tdata = acquired_root / "TelegramTdata"
    
    has_key_datas = False
    has_settingss = False
    key_datas_size = 0
    tdata_files: list[dict] = []
    
    PHONE_PATTERN = re.compile(r"(?:\+?84|0)[3|5|7|8|9][0-9]{8}\b|\+?[1-9][0-9]{9,14}\b")
    USERNAME_PATTERN = re.compile(r"@[a-zA-Z0-9_]{5,32}\b")
    LINK_PATTERN = re.compile(r"https?://(?:t\.me|telegram\.me)/\S+", re.IGNORECASE)
    
    carved_phones: set[str] = set()
    carved_usernames: set[str] = set()
    carved_links: set[str] = set()
    session_dirs: list[str] = []

    if telegram_tdata.exists():
        for file_path in iter_files(telegram_tdata):
            try:
                rel = str(file_path.relative_to(telegram_tdata))
                sz = file_path.stat().st_size
                tdata_files.append({"file": rel, "size": sz})
                if file_path.name == "key_datas":
                    has_key_datas = True
                    key_datas_size = sz
                elif file_path.name == "settingss":
                    has_settingss = True

                parts = file_path.parts
                for p_item in parts:
                    if len(p_item) == 16 and all(c in "0123456789ABCDEFabcdef" for c in p_item):
                        session_dirs.append(p_item)

                # Chi quet text tren cac tep tin cau hinh thuc su, bo qua toan bo emoji atlas, shader cache va du lieu ma hoa AES
                ignore_dirs = {"emoji", "grshadercache", "shadercache", "dawngraphitecache", "smartscreen", "user_data"}
                is_ignored = any(d in [part.lower() for part in file_path.parts] for d in ignore_dirs)
                is_text_target = file_path.suffix.lower() in {".json", ".txt", ".ini", ".log"} or file_path.name in {"shortcuts-custom.json", "settingss"}
                
                if not is_ignored and is_text_target and sz < 5 * 1024 * 1024:
                    raw_data = file_path.read_bytes()
                    decoded_text = raw_data.decode("utf-8", errors="ignore")
                    for match in PHONE_PATTERN.finditer(decoded_text):
                        carved_phones.add(match.group(0))
                    for match in USERNAME_PATTERN.finditer(decoded_text):
                        carved_usernames.add(match.group(0))
                    for match in LINK_PATTERN.finditer(decoded_text):
                        carved_links.add(match.group(0))
            except Exception:
                continue

    progress.advance("Session files inspected", f"Files: {len(tdata_files)} | KeyDatas: {has_key_datas}")

    MAGIC_MAP = [
        (b"\xFF\xD8\xFF", "image/jpeg", ".jpg"),
        (b"\x89PNG\r\n\x1a\n", "image/png", ".png"),
        (b"GIF87a", "image/gif", ".gif"),
        (b"GIF89a", "image/gif", ".gif"),
        (b"OggS", "audio/ogg", ".ogg"),
        (b"%PDF-", "application/pdf", ".pdf"),
        (b"PK\x03\x04", "application/zip", ".zip"),
    ]

    media_items: list[dict] = []
    tdata_dirs = [p for p in acquired_root.glob("TelegramTdata*") if p.is_dir()]
    if not tdata_dirs and telegram_tdata.exists():
        tdata_dirs = [telegram_tdata]

    cache_roots: list[Path] = []
    for td_dir in tdata_dirs:
        u_data = td_dir / "user_data"
        if u_data.exists():
            for sub in ("cache", "media_cache", "wvbots"):
                sub_p = u_data / sub
                if sub_p.exists():
                    cache_roots.append(sub_p)
        direct_cache = td_dir / "cache"
        if direct_cache.exists():
            cache_roots.append(direct_cache)

    for cache_root in cache_roots:
        for file_path in iter_files(cache_root):
            try:
                raw = file_path.read_bytes()
                sz = len(raw)
                detected_mime = "application/octet-stream"
                ext = ".bin"
                for magic, mime, def_ext in MAGIC_MAP:
                    if raw.startswith(magic):
                        detected_mime = mime
                        ext = def_ext
                        break
                if len(raw) > 8 and raw[4:8] == b"ftyp":
                    detected_mime = "video/mp4"
                    ext = ".mp4"
                elif len(raw) > 12 and raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
                    detected_mime = "image/webp"
                    ext = ".webp"

                sha = hashlib.sha256(raw).hexdigest()
                media_items.append({
                    "fileName": file_path.name,
                    "fileSize": sz,
                    "mimeType": detected_mime,
                    "suggestedExt": ext,
                    "sha256": sha,
                    "modifiedTime": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                    "sourcePath": str(file_path),
                })
            except Exception:
                continue

    progress.advance("Media cache carved", f"Recovered media items: {len(media_items)}")

    browser_rows: list[dict] = []
    chrome_history_db = case.browser_dir / "Chrome" / "History"
    if chrome_history_db.exists():
        try:
            query = "SELECT url, title, visit_count, last_visit_time FROM urls WHERE url LIKE '%telegram%' OR url LIKE '%t.me%'"
            browser_rows = query_sqlite_rows(chrome_history_db, query)
            # Trich xuat thuc the that 100% tu lich su trinh duyet
            for b_row in browser_rows:
                u_str = b_row.get("url", "")
                if "@" in u_str:
                    for token in u_str.split("/"):
                        if token.startswith("@"):
                            clean_u = token.split("?")[0].split("#")[0].strip()
                            if len(clean_u) > 1:
                                carved_usernames.add(clean_u)
                if "t.me/" in u_str:
                    carved_links.add(u_str)
                    target_val = u_str.split("t.me/")[-1].split("?")[0].split("#")[0].strip()
                    if target_val.isdigit() and len(target_val) >= 9:
                        carved_phones.add(target_val)
                    elif target_val.startswith("@") or (target_val and not target_val.startswith("+")):
                        carved_usernames.add("@" + target_val.lstrip("@"))
        except Exception:
            pass

    progress.advance("Browser correlation parsed", f"Web visits: {len(browser_rows)}")

    entities_rows: list[dict] = []
    for u in sorted(carved_usernames):
        entities_rows.append({"type": "username", "value": u, "confidence": "0.90"})
    for p in sorted(carved_phones):
        entities_rows.append({"type": "phone_number", "value": p, "confidence": "0.85"})
    for l in sorted(carved_links):
        entities_rows.append({"type": "telegram_link", "value": l, "confidence": "0.95"})
    write_csv(case.exports_dir / "telegram_carved_entities.csv", entities_rows, ["type", "value", "confidence"])

    # Xuat rieng 2 tep danh ba ro rang de giam dinh vien tra cuu tuc thi
    username_rows = [{"username": u, "confidence": "0.90"} for u in sorted(carved_usernames)]
    write_csv(case.exports_dir / "telegram_usernames.csv", username_rows, ["username", "confidence"])

    phone_rows = [{"phoneNumber": p, "confidence": "0.85"} for p in sorted(carved_phones)]
    write_csv(case.exports_dir / "telegram_phone_numbers.csv", phone_rows, ["phoneNumber", "confidence"])

    write_csv(
        case.exports_dir / "telegram_media_cache.csv",
        media_items,
        ["fileName", "fileSize", "mimeType", "suggestedExt", "sha256", "modifiedTime", "sourcePath"],
    )

    if browser_rows:
        write_csv(case.exports_dir / "telegram_browser_history.csv", browser_rows, ["url", "title", "visit_count", "last_visit_time"])

    summary_data = {
        "appId": "telegram",
        "caseId": case.case_id,
        "hasKeyDatas": has_key_datas,
        "keyDatasSizeBytes": key_datas_size,
        "hasSettings": has_settingss,
        "activeSessionsCount": len(set(session_dirs)),
        "mediaCacheCount": len(media_items),
        "carvedUsernamesCount": len(carved_usernames),
        "carvedPhoneNumbersCount": len(carved_phones),
        "carvedLinksCount": len(carved_links),
        "browserTelegramVisits": len(browser_rows),
        "analyzedAt": datetime.now().isoformat(),
    }
    write_json(case.exports_dir / "telegram_account_summary.json", summary_data)

    # Ghi chu trung thuc: Telegram Desktop ma hoa AES-IGE cuc bo. 
    # Khong duoc phep bien tep cache rong thanh tin nhan gia.
    message_rows: list[dict] = []
    write_csv(case.exports_dir / "messages.csv", message_rows, ["messageId", "channelId", "guildId", "authorUsername", "content", "timestamp", "attachmentNames", "sourcePath"])
    write_csv(case.exports_dir / "timeline.csv", message_rows, ["messageId", "channelId", "guildId", "authorUsername", "content", "timestamp", "attachmentNames", "sourcePath"])

    progress.advance("Outputs exported to 07_Exports", f"Entities: {len(entities_rows)} | Media: {len(media_items)}")
    progress.finish("Telegram analysis complete", str(case.exports_dir))

    print("")
    print("[*] THỐNG KÊ GIÁM ĐỊNH TELEGRAM DESKTOP")
    print(f"    - Tệp phiên tdata phát hiện:  {len(tdata_files):8} tệp (files)")
    print(f"    - KeyDatas mã hóa (tệp muối):  {'TÌM THẤY (Found)' if has_key_datas else 'KHÔNG TÌM THẤY'}")
    print(f"    - Tệp Media khôi phục (Cache):{len(media_items):8} | 07_Exports/telegram_media_cache.csv")
    print(f"    - Usernames (@) bóc tách:    {len(carved_usernames):8} | 07_Exports/telegram_usernames.csv")
    print(f"    - Số điện thoại phát hiện:   {len(carved_phones):8} | 07_Exports/telegram_phone_numbers.csv")
    print(f"    - Đường dẫn t.me thu thập:   {len(carved_links):8} | 07_Exports/telegram_carved_entities.csv")
    print(f"    - Lịch sử duyệt Telegram Web: {len(browser_rows):8} | 07_Exports/telegram_browser_history.csv")
    print("")

    return {
        "appId": "telegram",
        "caseId": case.case_id,
        "tdataFilesCount": len(tdata_files),
        "mediaCacheCount": len(media_items),
        "recoveredMessageRows": len(message_rows),
        "timelineRows": len(message_rows),
        "carvedUsernamesCount": len(carved_usernames),
        "carvedPhoneNumbersCount": len(carved_phones),
        "carvedLinksCount": len(carved_links),
        "hasKeyDatas": has_key_datas,
    }


def analyze_case(case: CaseContext) -> dict:
    from fdctl.services.license_service import require_bundle_access
    require_bundle_access("analysis")
    adapters = get_adapters()
    adapter = adapters[case.app_id]
    defaults = adapter.build_analysis_defaults(case) # type: ignore
    if case.app_id == "discord":
        results = analyze_discord(case)
    elif case.app_id == "telegram":
        results = analyze_telegram(case)
    elif case.app_id == "zalo":
        results = analyze_zalo(case)
        return results
    else:
        results = {}

    summary = {**defaults, **results}
    supplemental = run_supplemental_checks(case)
    summary["supplemental"] = supplemental
    write_json(case.exports_dir / "analysis_summary.json", summary)
    build_autopsy_bundle(case)
    return summary
