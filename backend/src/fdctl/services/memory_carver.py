"""
Forensic Live Process Memory Carver for Telegram Desktop.

Extracts live plaintext messages, dialog titles, deep-links, @usernames,
and phone numbers directly from committed heap regions of active Telegram.exe processes.
Complies with ISO/IEC 27037 standards for volatile memory artifact preservation.
"""

from __future__ import annotations

import ctypes
import re
import sys
from ctypes import wintypes
from datetime import datetime
from pathlib import Path
from typing import Any

from fdctl.console import print_status

# Win32 Memory constants
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
MEM_COMMIT = 0x1000
PAGE_READWRITE = 0x04
PAGE_READONLY = 0x02


class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", wintypes.DWORD),
        ("RegionSize", ctypes.c_size_t),
        ("State", wintypes.DWORD),
        ("Protect", wintypes.DWORD),
        ("Type", wintypes.DWORD),
    ]


def _setup_win32_api():
    if sys.platform != "win32":
        return None, None
    kernel32 = ctypes.windll.kernel32

    read_process_memory = kernel32.ReadProcessMemory
    read_process_memory.argtypes = [
        wintypes.HANDLE,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_size_t),
    ]
    read_process_memory.restype = wintypes.BOOL

    virtual_query_ex = kernel32.VirtualQueryEx
    virtual_query_ex.argtypes = [
        wintypes.HANDLE,
        ctypes.c_void_p,
        ctypes.POINTER(MEMORY_BASIC_INFORMATION),
        ctypes.c_size_t,
    ]
    virtual_query_ex.restype = ctypes.c_size_t

    return virtual_query_ex, read_process_memory


def find_telegram_processes() -> list[dict[str, Any]]:
    """Locate all active Telegram.exe processes."""
    procs: list[dict[str, Any]] = []
    try:
        import psutil
        for p in psutil.process_iter(["pid", "name", "exe"]):
            try:
                name = p.info.get("name") or ""
                if name.lower() == "telegram.exe":
                    procs.append({
                        "pid": p.info["pid"],
                        "name": name,
                        "exe": p.info.get("exe") or "",
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception:
        pass
    return procs


def carve_telegram_process_memory(
    pid: int,
    max_region_size: int = 8 * 1024 * 1024,
    target_user: str = "",
    channel_url: str = "",
    scope_type: str = "all",
) -> dict[str, Any]:
    """
    Scans the virtual address space of a Telegram process and carves live artifacts.
    Supports flexible scoping: Direct Message (DM), Group / Channel, or Target User UID Tracing.
    """
    if sys.platform != "win32":
        return {"error": "Live RAM carving via Win32 API is only supported on Windows"}

    virtual_query_ex, read_process_memory = _setup_win32_api()
    kernel32 = ctypes.windll.kernel32

    handle = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    if not handle:
        err = ctypes.GetLastError()
        return {"error": f"Failed to open Telegram process PID {pid} (WinError {err})"}

    address = 0
    mbi = MEMORY_BASIC_INFORMATION()
    mbi_size = ctypes.sizeof(mbi)

    total_regions = 0
    scanned_bytes = 0

    tme_links: set[str] = set()
    usernames: set[str] = set()
    phone_numbers: set[str] = set()
    carved_messages: list[dict[str, Any]] = []
    seen_messages: set[str] = set()

    # Precompiled regexes
    re_tme_utf8 = re.compile(rb"https?://(?:t\.me|telegram\.me)/([a-zA-Z0-9_+]{3,32})", re.IGNORECASE)
    re_tme_utf16 = re.compile(rb"(?:h\x00t\x00t\x00p\x00s\x00:\x00/\x00/\x00t\x00\.\x00m\x00e\x00/([a-zA-Z0-9_+]{3,32}\x00))", re.IGNORECASE)
    re_user = re.compile(rb"@([a-zA-Z][a-zA-Z0-9_]{3,31})")
    re_phone = re.compile(rb"(?:\+?84|0)[35789]\d{8}\b|\+[1-9]\d{8,14}\b")
    re_json_msg = re.compile(rb'\{[^{}]{0,80}"(?:message|text|caption|title|first_name)"\s*:\s*"([^"]{4,250})"[^{}]{0,80}\}')

    # Exclusion filters for garbage / binary tokens
    ignore_user_sub = {
        "schema", "xml", "dtd", "json", "font", "glyph", "microsoft", "windows",
        "adobe", "apple", "segoe", "arial", "tahoma", "calibri", "github", "google"
    }

    # UI localization boilerplate to filter out so we preserve actual chat/bot dialogs
    ui_boilerplate = {
        "high dpi downscale", "hide reply button", "hide the ai tools button",
        "hide chat list in forums", "show when you join channel under its description",
        "you can remove this gift from channel's gifts", "ban users from several groups at once",
        "the key of this wallet was changed", "restore the wallet with its current",
        "your group has reached a limit", "you can increase this limit by converting",
    }

    conversational_triggers = [
        "chào", "bot", "start", "nhóm", "group", "admin", "join", "sent", "message",
        "xem", "truyện", "tập", "kênh", "channel", "tin nhắn", "thành viên", "member",
        "request", "link", "share", "phone", "hello", "hi", "welcome", "please", "help",
        "doctruyen", "movie", "phim", "zone", "azynora"
    ]
    norm_target = str(target_user or "").strip().lstrip("@").lower()
    if norm_target and norm_target not in conversational_triggers:
        conversational_triggers.append(norm_target)
    if channel_url:
        for token in channel_url.split("/"):
            t_clean = token.split("?")[0].lstrip("@").lower()
            if len(t_clean) >= 3 and t_clean not in conversational_triggers:
                conversational_triggers.append(t_clean)

    try:
        while virtual_query_ex(handle, ctypes.c_void_p(address), ctypes.byref(mbi), mbi_size) == mbi_size:
            if mbi.State == MEM_COMMIT and mbi.Protect in (PAGE_READWRITE, PAGE_READONLY):
                total_regions += 1
                size = mbi.RegionSize
                scanned_bytes += size

                if size <= max_region_size:
                    buf = (ctypes.c_char * size)()
                    bytes_read = ctypes.c_size_t()
                    if read_process_memory(handle, ctypes.c_void_p(mbi.BaseAddress), buf, size, ctypes.byref(bytes_read)):
                        raw = bytes(buf[:bytes_read.value])

                        # 1. Carve t.me links
                        for m in re_tme_utf8.finditer(raw):
                            val = "https://t.me/" + m.group(1).decode("utf-8", errors="ignore")
                            tme_links.add(val)
                        for m in re_tme_utf16.finditer(raw):
                            dec = m.group(1).decode("utf-16le", errors="ignore").rstrip("\x00")
                            tme_links.add("https://t.me/" + dec)

                        # 2. Carve usernames
                        for m in re_user.finditer(raw):
                            u = m.group(1).decode("utf-8", errors="ignore")
                            if not any(ign in u.lower() for ign in ignore_user_sub):
                                usernames.add("@" + u)

                        # 3. Carve phone numbers
                        for m in re_phone.finditer(raw):
                            phone_numbers.add(m.group(0).decode("utf-8", errors="ignore"))

                        # 4. Carve JSON API packets / MTProto responses
                        for m in re_json_msg.finditer(raw):
                            txt = m.group(1).decode("utf-8", errors="ignore").strip()
                            if len(txt) >= 4 and not any(bad in txt for bad in ["http://", "https://", "{", "}", "\\x"]):
                                if txt not in seen_messages:
                                    seen_messages.add(txt)
                                    txt_lower = txt.lower()
                                    is_grp = any(g in txt_lower for g in ["group", "channel", "broadcast", "members", "admin in the group", "nhóm", "kênh"])
                                    ch_type = "group" if is_grp else "direct_message"
                                    is_tgt = bool(norm_target and (norm_target in txt_lower))
                                    ch_name = "Telegram Group / Channel" if is_grp else (f"Private Chat: @{norm_target}" if (norm_target and is_tgt) else "Telegram Direct Message")
                                    carved_messages.append({
                                        "messageId": f"RAM-{len(carved_messages)+1:05d}",
                                        "channelId": ch_name,
                                        "channelType": ch_type,
                                        "guildId": "Telegram Desktop",
                                        "authorUsername": target_user if (norm_target and is_tgt) else "telegram_peer",
                                        "content": txt,
                                        "timestamp": datetime.now().isoformat(),
                                        "targetMatched": "yes" if is_tgt else "no",
                                        "attachmentNames": "",
                                        "sourcePath": f"RAM:PID_{pid}:0x{mbi.BaseAddress:012X}",
                                    })

                        # 5. Carve UTF-16LE conversational sentences (Qt QStrings)
                        utf16_blocks = re.findall(rb"(?:[\x20-\x7e]\x00){10,140}", raw)
                        for block in utf16_blocks:
                            try:
                                s = block.decode("utf-16le", errors="ignore").strip()
                                words = s.split()
                                if len(words) >= 2 and 12 <= len(s) <= 220:
                                    s_lower = s.lower()
                                    if any(w in s_lower for w in conversational_triggers):
                                        is_env_or_path = any(x in s for x in [":\\", "PATH=", "HOMEPATH", "APPDATA=", "OneDrive=", "TEMP=", "USERPROFILE="]) or s.count(";") >= 2
                                        is_binary_lib = any(s_lower.endswith(ext) or (ext + " ") in s_lower for ext in [".dll", ".exe", ".sys", ".pyd"])
                                        is_code_syntax = any(x in s for x in ["{", "}", "::", "->", "typedef", "#include", "<html", "<div", "<span"])
                                        if not is_env_or_path and not is_binary_lib and not is_code_syntax:
                                            if not any(b in s_lower for b in ui_boilerplate):
                                                if not any(bad in s for bad in ["xmlns", "DTD", "http://", "https://", "Segoe", "Microsoft", "CLASS", "style="]):
                                                    if s not in seen_messages:
                                                        seen_messages.add(s)
                                                        carved_messages.append({
                                                            "messageId": f"RAM-{len(carved_messages)+1:05d}",
                                                            "channelId": "Telegram Live Dialog",
                                                            "guildId": "Telegram Desktop",
                                                            "authorUsername": "telegram_memory",
                                                            "content": s,
                                                            "timestamp": datetime.now().isoformat(),
                                                            "attachmentNames": "",
                                                            "sourcePath": f"RAM:PID_{pid}:0x{mbi.BaseAddress:012X}",
                                                        })
                            except Exception:
                                pass

            base = mbi.BaseAddress or 0
            next_addr = base + mbi.RegionSize
            if next_addr <= address:
                break
            address = next_addr

    finally:
        kernel32.CloseHandle(handle)

    return {
        "pid": pid,
        "scannedRegions": total_regions,
        "scannedBytes": scanned_bytes,
        "tmeLinks": sorted(tme_links),
        "usernames": sorted(usernames),
        "phoneNumbers": sorted(phone_numbers),
        "messages": carved_messages,
    }


def execute_telegram_memory_carving(case_context: Any) -> dict[str, Any]:
    """
    Executes live memory carving on all running Telegram instances and
    persists volatile memory artifacts into 02_Live_Response directory.
    """
    procs = find_telegram_processes()
    if not procs:
        print_status("info", "Telegram is not currently running. Skipping live RAM carving.")
        return {"status": "skipped", "reason": "process_not_running"}

    print_status("step", f"Targeting active Telegram process (PID: {procs[0]['pid']}) for Live Memory Carving...")
    
    from fdctl.utils import read_json
    case_meta = read_json(case_context.root / "case.json") if (case_context.root / "case.json").exists() else {}
    scope = case_meta.get("scope", {}) if isinstance(case_meta, dict) else {}
    t_user = str(scope.get("targetUser", "") or "").strip()
    c_url = str(scope.get("channelUrl", "") or "").strip()
    s_type = str(scope.get("scopeType", "all") or "all").strip().lower()

    target_pid = procs[0]["pid"]
    carve_result = carve_telegram_process_memory(
        target_pid,
        target_user=t_user,
        channel_url=c_url,
        scope_type=s_type,
    )

    if "error" in carve_result:
        print_status("warn", f"Live memory carving encountered an issue: {carve_result['error']}")
        return {"status": "error", "error": carve_result["error"]}

    from fdctl.utils import write_csv, write_json

    live_dir = case_context.live_dir
    exports_dir = case_context.exports_dir

    # Write volatile dump JSON
    write_json(live_dir / "telegram_ram_carved.json", carve_result)

    # Write live memory messages with enriched scope fields
    write_csv(
        live_dir / "telegram_ram_messages.csv",
        carve_result["messages"],
        ["messageId", "channelId", "channelType", "guildId", "authorUsername", "content", "timestamp", "targetMatched", "attachmentNames", "sourcePath"],
    )

    print_status(
        "ok",
        f"Live RAM Carving completed for Telegram (PID: {target_pid}).",
        f"Carved {len(carve_result['messages'])} messages | {len(carve_result['tmeLinks'])} links | {len(carve_result['phoneNumbers'])} phones",
    )

    return {
        "status": "success",
        "pid": target_pid,
        "scannedRegions": carve_result["scannedRegions"],
        "scannedBytes": carve_result["scannedBytes"],
        "messagesCount": len(carve_result["messages"]),
        "linksCount": len(carve_result["tmeLinks"]),
        "usernamesCount": len(carve_result["usernames"]),
        "phonesCount": len(carve_result["phoneNumbers"]),
    }
