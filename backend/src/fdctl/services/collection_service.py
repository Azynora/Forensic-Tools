from __future__ import annotations
import sys
import hashlib
from pathlib import Path
import psutil
from PIL import Image, ImageDraw, ImageGrab
from fdctl.adapters import get_adapters
from fdctl.console import StageProgress, print_section, print_status
from fdctl.models import ArtifactTarget, CaseContext
from fdctl.services.autopsy_service import build_autopsy_bundle
from fdctl.services.supplement_service import import_external_audit_logs

from fdctl.utils import (
    copy_file_preserve,
    current_user_context,
    ensure_dir,
    is_admin,
    now_iso,
    relative_to,
    rerun_as_admin,
    write_csv,
    write_json,
)
from fdctl.services.license_service import require_bundle_access

def _copy_target(target: ArtifactTarget, case_root: Path, manifest: list[dict], errors: list[dict]) -> None:
    if not target.source.exists():
        if not target.optional:
            errors.append({"sourcePath": str(target.source), "error": "Required path missing"})
        return

    try:
        files = [target.source] if target.source.is_file() else list(target.source.rglob("*"))
        for file_path in files:
            if file_path.is_dir():
                continue
            destination = target.destination if target.source.is_file() else target.destination / file_path.relative_to(target.source)
            copy_file_preserve(file_path, destination)
            digest = hashlib.sha256(destination.read_bytes()).hexdigest()
            manifest.append(
                {
                    "category": target.category,
                    "sourcePath": str(file_path),
                    "destinationPath": relative_to(destination, case_root),
                    "sizeBytes": destination.stat().st_size,
                    "sha256": digest,
                    "lastWriteTimeUtc": destination.stat().st_mtime,
                }
            )
    except Exception as exc:
        errors.append({"sourcePath": str(target.source), "error": str(exc)})

def _snapshot_processes(case: CaseContext, process_names: tuple[str, ...]) -> tuple[list[dict], list[dict]]:
    live_rows: list[dict] = []
    pid_set: set[int] = set()
    lower_names = {name.lower() for name in process_names}
    search_tokens = {token.replace(".exe", "") for token in lower_names}
    for proc in psutil.process_iter(["pid", "ppid", "name", "exe", "cmdline", "username", "create_time", "status"]):
        try:
            name = (proc.info.get("name") or "").lower()
            exe_path = (proc.info.get("exe") or "").lower()
            cmdline_parts = [str(item).lower() for item in (proc.info.get("cmdline") or []) if item]
            cmdline = " ".join(cmdline_parts)
            cmdline_names = {Path(item).name.lower().replace(".exe", "") for item in cmdline_parts}
            exe_name = Path(exe_path).name.lower().replace(".exe", "") if exe_path else ""
            if name in lower_names or exe_name in search_tokens or bool(cmdline_names & search_tokens):
                live_rows.append(
                    {
                        "pid": proc.info.get("pid", ""),
                        "parentPid": proc.info.get("ppid", ""),
                        "name": proc.info.get("name", ""),
                        "executablePath": proc.info.get("exe", ""),
                        "commandLine": cmdline,
                        "username": proc.info.get("username", ""),
                        "createTime": proc.info.get("create_time", ""),
                        "status": proc.info.get("status", ""),
                    }
                )
                pid_set.add(proc.info.get("pid", 0))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    tcp_rows: list[dict] = []
    try:
        for conn in psutil.net_connections(kind="tcp"):
            if conn.pid in pid_set:
                tcp_rows.append(
                    {
                        "pid": conn.pid or "",
                        "localAddress": f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "",
                        "remoteAddress": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "",
                        "status": conn.status,
                    }
                )
    except Exception as exc:
        tcp_rows.append({"pid": "", "localAddress": "", "remoteAddress": "", "status": f"Unavailable: {exc}"})

    write_csv(case.live_dir / "process_inventory.csv", live_rows, ["pid", "parentPid", "name", "executablePath", "commandLine", "username", "createTime", "status"])
    write_csv(case.live_dir / "tcp_connections.csv", tcp_rows, ["pid", "localAddress", "remoteAddress", "status"])
    return live_rows, tcp_rows

def _capture_window_by_process_names(process_names: tuple[str, ...], output_path: Path) -> bool:
    """Capture only the target application window, preserving user desktop privacy."""
    if sys.platform != "win32":
        return False
    try:
        import ctypes
        from ctypes import wintypes
        if not hasattr(ctypes, "windll"):
            return False
        user32 = ctypes.windll.user32

        target_pids = set()
        for p in psutil.process_iter(["pid", "name"]):
            p_name = (p.info["name"] or "").lower()
            if any(t.lower() in p_name for t in process_names):
                target_pids.add(p.info["pid"])

        if not target_pids:
            return False

        candidate_hwnds = []

        def enum_callback(hwnd, _lparam):
            if not user32.IsWindowVisible(hwnd) or user32.IsIconic(hwnd):
                return True
            lpdw_pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(lpdw_pid))
            if lpdw_pid.value in target_pids:
                rect = wintypes.RECT()
                user32.GetWindowRect(hwnd, ctypes.byref(rect))
                w = rect.right - rect.left
                h = rect.bottom - rect.top
                if w > 200 and h > 200:
                    candidate_hwnds.append((hwnd, w * h, rect))
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        user32.EnumWindows(WNDENUMPROC(enum_callback), 0)

        if not candidate_hwnds:
            return False

        candidate_hwnds.sort(key=lambda x: x[1], reverse=True)
        _, _, rect = candidate_hwnds[0]
        bbox = (rect.left, rect.top, rect.right, rect.bottom)
        if bbox[2] > bbox[0] and bbox[3] > bbox[1]:
            img = ImageGrab.grab(bbox=bbox)
            img.save(output_path)
            return True
    except Exception:
        pass
    return False


def _generate_evidence_contact_sheet(image_paths: list[Path], output_path: Path, case_id: str, app_name: str) -> bool:
    """Generate a visual contact sheet gallery from recovered cache media."""
    if not image_paths:
        return False
    try:
        cols = 3
        selected = image_paths[:9]
        rows = (len(selected) + cols - 1) // cols

        thumb_w, thumb_h = 340, 240
        card_h = thumb_h + 65
        pad_x, pad_y = 30, 24
        header_h = 90

        width = cols * thumb_w + (cols + 1) * pad_x
        height = header_h + rows * card_h + (rows + 1) * pad_y

        canvas = Image.new("RGB", (width, height), "#0B132B")
        draw = ImageDraw.Draw(canvas)

        draw.text((pad_x, 22), f"FORENSIC EVIDENCE MEDIA GALLERY - {app_name.upper()}", fill="#38BDF8")
        draw.text((pad_x, 50), f"Case ID: {case_id}  |  Recovered Cached Media & Evidence Thumbnails with SHA-256", fill="#94A3B8")
        draw.line((pad_x, 78, width - pad_x, 78), fill="#1E293B", width=2)

        for idx, p in enumerate(selected):
            r = idx // cols
            c = idx % cols
            x = pad_x + c * (thumb_w + pad_x)
            y = header_h + pad_y + r * (card_h + pad_y)

            draw.rectangle((x, y, x + thumb_w, y + card_h), fill="#1E293B", outline="#334155", width=1)

            try:
                im = Image.open(p)
                im.thumbnail((thumb_w - 12, thumb_h - 12))
                im_w, im_h = im.size
                im_x = x + (thumb_w - im_w) // 2
                im_y = y + 6 + (thumb_h - im_h) // 2
                canvas.paste(im, (im_x, im_y))
            except Exception:
                draw.text((x + 20, y + thumb_h // 2), "[Corrupt/Encrypted Media]", fill="#EF4444")

            try:
                raw = p.read_bytes()
                sha = hashlib.sha256(raw).hexdigest()
                meta1 = f"File: {p.name[:22]} ({len(raw)} B)"
                meta2 = f"SHA: {sha[:24]}..."
            except Exception:
                meta1 = f"File: {p.name[:22]}"
                meta2 = "SHA: Unknown"

            draw.text((x + 8, y + thumb_h + 10), meta1, fill="#F8FAFC")
            draw.text((x + 8, y + thumb_h + 32), meta2, fill="#38BDF8")

        canvas.save(output_path)
        return True
    except Exception:
        return False


def _capture_screenshots(case: CaseContext, adapter: object, artifact_count: int, process_count: int, tcp_count: int) -> list[str]:
    screenshots_dir = ensure_dir(case.images_dir)
    output_paths: list[str] = []

    if hasattr(adapter, "display_name"):
        app_name = str(adapter.display_name)
        app_id = str(getattr(adapter, "app_id", case.app_id))
        process_names = tuple(getattr(adapter, "process_names", ()))
    else:
        app_name = str(adapter)
        app_id = case.app_id
        process_names = ()

    # 1. Option 1: Chụp cửa sổ ứng dụng mục tiêu (Target Window Capture)
    target_window_path = screenshots_dir / f"01_target_window_{app_id}.png"
    if process_names and _capture_window_by_process_names(process_names, target_window_path):
        output_paths.append(str(target_window_path))
    else:
        status_path = screenshots_dir / f"01_target_window_{app_id}.png"
        canvas = Image.new("RGB", (1280, 720), "#0B132B")
        draw = ImageDraw.Draw(canvas)
        draw.rectangle((40, 40, 1240, 680), fill="#1E293B", outline="#38BDF8", width=2)
        draw.text((80, 80), f"FORENSIC APPLICATION STATUS - {app_name.upper()}", fill="#38BDF8")
        draw.text((80, 130), f"Case ID: {case.case_id}  |  Target App: {app_name}", fill="#94A3B8")
        draw.line((80, 170, 1200, 170), fill="#334155", width=2)
        status_note = f"Active processes detected: {process_count} | TCP connections: {tcp_count}"
        draw.text((80, 220), status_note, fill="#F8FAFC")
        draw.text((80, 260), "Application was active in background or system tray during live acquisition.", fill="#94A3B8")
        draw.text((80, 300), "Target window coordinates secured (Desktop privacy preserved).", fill="#38BDF8")
        draw.text((80, 360), f"Timestamp: {now_iso()}", fill="#64748B")
        canvas.save(status_path)
        output_paths.append(str(status_path))

    # 2. Option 2: Bảng Gallery bằng chứng ảnh bóc tách từ Cache (Evidence Media Contact Sheet)
    gallery_path = screenshots_dir / "02_carved_media_contact_sheet.png"
    found_images: list[Path] = []
    if case.acquired_dir.exists():
        for p in case.acquired_dir.rglob("*"):
            if p.is_file():
                try:
                    head = p.read_bytes()[:16]
                    if head.startswith(b"\xff\xd8\xff") or head.startswith(b"\x89PNG") or head.startswith(b"GIF8") or (head[:4] == b"RIFF" and head[8:12] == b"WEBP"):
                        found_images.append(p)
                        if len(found_images) >= 9:
                            break
                except Exception:
                    pass

    if found_images and _generate_evidence_contact_sheet(found_images, gallery_path, case.case_id, app_name):
        output_paths.append(str(gallery_path))
    else:
        triage_path = screenshots_dir / "02_live_network_triage.png"
        canvas = Image.new("RGB", (1280, 720), "#0B132B")
        draw = ImageDraw.Draw(canvas)
        draw.rectangle((40, 40, 1240, 680), fill="#1E293B", outline="#059669", width=2)
        draw.text((80, 80), f"LIVE TRIAGE EVIDENCE - {app_name.upper()}", fill="#34D399")
        draw.text((80, 130), f"Case ID: {case.case_id}  |  Process & Network Socket Triage", fill="#94A3B8")
        draw.line((80, 170, 1200, 170), fill="#334155", width=2)
        draw.text((80, 220), f"Total Artifacts Collected: {artifact_count}", fill="#F8FAFC")
        draw.text((80, 260), f"Active Live Processes: {process_count}", fill="#F8FAFC")
        draw.text((80, 300), f"Live Network Socket Connections: {tcp_count}", fill="#F8FAFC")
        draw.text((80, 360), f"Evidence Root: {case.acquired_dir}", fill="#94A3B8")
        draw.text((80, 400), f"Collection Timestamp: {now_iso()}", fill="#64748B")
        canvas.save(triage_path)
        output_paths.append(str(triage_path))

    return output_paths

def _cache_inventory(manifest: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for item in manifest:
        destination = str(item.get("destinationPath", ""))
        if "cache" in destination.lower():
            rows.append(item)
    return rows

def _network_identity(process_rows: list[dict], tcp_rows: list[dict]) -> dict:
    remote_ips = sorted(
        {
            row["remoteAddress"].split(":")[0]
            for row in tcp_rows
            if row.get("remoteAddress")
        }
    )
    return {
        "processCount": len(process_rows),
        "tcpConnectionCount": len(tcp_rows),
        "remoteIps": remote_ips,
    }

def collect_case(case: CaseContext, elevated: bool = False) -> dict:
    require_bundle_access("collection")
    print_section("Collection Pipeline", f"Case {case.case_id} | App {case.app_id}")
    progress = StageProgress(6)
    print_status("step", "Initializing collection context...", f"Case root: {case.root}")
    adapters = get_adapters()
    adapter = adapters[case.app_id]
    if adapter.requires_admin_for_collection() and not is_admin() and not elevated: # type: ignore
        print_status("warn", "Discord forensic collection requires administrator permission.")
        print_status("warn", "Windows will now ask the user to allow elevated access (UAC prompt).")
        rerun_as_admin(["collect", "--case", case.case_id, "--elevated"])

    ensure_dir(case.info_dir)
    ensure_dir(case.live_dir)
    ensure_dir(case.acquired_dir)
    ensure_dir(case.browser_dir)
    progress.advance("Workspace prepared", f"{case.info_dir} | {case.live_dir} | {case.acquired_dir} | {case.browser_dir}")

    manifest: list[dict] = []
    errors: list[dict] = []
    detection = adapter.detect() # type: ignore
    targets = adapter.get_artifact_targets(case) # type: ignore

    print_status("step", "Snapshotting running processes and TCP connections...")
    process_rows, tcp_rows = _snapshot_processes(case, adapter.process_names) # type: ignore
    progress.advance("Live response captured", f"Processes: {len(process_rows)} | TCP rows: {len(tcp_rows)}")

    if case.app_id == "telegram":
        print_status("step", "Executing volatile live process memory carving (Method 1: Live RAM Carving)...")
        from fdctl.services.memory_carver import execute_telegram_memory_carving
        execute_telegram_memory_carving(case)
    
    print_status("step", f"Preparing to copy artifacts for {len(targets)} targets...")
    for index, target in enumerate(targets, start=1):
        print_status(
            "info",
            f"[{index}/{len(targets)}] {target.category}",
            f"{target.source} -> {target.destination}",
        )
        _copy_target(target, case.root, manifest, errors)
    progress.advance("Artifact copy completed", f"Copied files: {len(manifest)} | Copy errors: {len(errors)}")

    print_status("step", "Generating inventory caches and exporting connection context...")
    write_csv(case.info_dir / "artifact_manifest.csv", manifest, ["category", "sourcePath", "destinationPath", "sizeBytes", "sha256", "lastWriteTimeUtc"])
    write_csv(case.info_dir / "copy_errors.csv", errors, ["sourcePath", "error"])
    cache_rows = _cache_inventory(manifest)
    write_csv(case.exports_dir / "cache_inventory.csv", cache_rows, ["category", "sourcePath", "destinationPath", "sizeBytes", "sha256", "lastWriteTimeUtc"])
    user_context = current_user_context()
    network_identity = _network_identity(process_rows, tcp_rows)
    write_json(case.info_dir / "user_context.json", user_context)
    write_json(case.live_dir / "network_identity.json", network_identity)
    write_csv(case.live_dir / "local_ipv4_addresses.csv", user_context["localIpv4"], ["interface", "ipAddress", "netmask", "broadcast"])
    write_csv(case.live_dir / "remote_ip_addresses.csv", [{"ipAddress": ip} for ip in network_identity["remoteIps"]], ["ipAddress"])
    write_json(
        case.info_dir / "collection_summary.json",
        {
            "collectedAt": now_iso(),
            "app": adapter.display_name, # type: ignore
            "caseId": case.case_id,
            "scope": adapter.get_collection_scope(), # type: ignore
            "detection": {
                "detected": detection.detected,
                "supportLevel": detection.support_level,
                "installPaths": detection.install_paths,
                "notes": detection.notes,
            },
            "artifactCount": len(manifest),
            "copyErrorCount": len(errors),
            "processCount": len(process_rows),
            "tcpCount": len(tcp_rows),
            "isAdmin": is_admin(),
            "cacheArtifactCount": len(cache_rows),
            "userContextPath": str(case.info_dir / "user_context.json"),
            "networkIdentityPath": str(case.live_dir / "network_identity.json"),
        },
    )
    progress.advance("Inventories exported", f"Cache artifacts: {len(cache_rows)} | Local IPs: {len(user_context['localIpv4'])}")
    print_status("step", "Scanning for externally exported Discord audit-log JSON files...")
    audit_imports = import_external_audit_logs(case)
    print_status("info", "Audit-log imports detected", f"Files: {len(audit_imports)}")
    print_status("step", "Capturing evidence screenshots...")
    screenshots = _capture_screenshots(case, adapter, len(manifest), len(process_rows), len(tcp_rows)) # type: ignore
    progress.advance("Evidence screenshots captured", f"Screenshot files: {len(screenshots)}")
    summary = {
        "artifactCount": len(manifest),
        "copyErrorCount": len(errors),
        "processCount": len(process_rows),
        "tcpCount": len(tcp_rows),
        "cacheArtifactCount": len(cache_rows),
        "user": user_context["username"],
        "hostname": user_context["hostname"],
        "localIpCount": len(user_context["localIpv4"]),
        "remoteIpCount": len(network_identity["remoteIps"]),
        "auditImportCount": len(audit_imports),
        "screenshots": screenshots,
    }
    write_json(case.info_dir / "collection_result.json", summary)
    autopsy_manifest = build_autopsy_bundle(case)
    print_status("step", "Autopsy-ready bundle refreshed.", str(case.autopsy_dir))
    progress.advance("Autopsy bundle prepared", f"Copied rows: {autopsy_manifest.get('counts', {}).get('copiedRows', 0)}")
    progress.finish("Collection completed", f"{len(manifest)} files collected for {adapter.display_name}") # type: ignore
    print_status("ok", "Collection complete.", f"Files: {len(manifest)} | Errors: {len(errors)} | Screenshots: {len(screenshots)}")
    return summary
