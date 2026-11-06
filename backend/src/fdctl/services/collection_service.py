from __future__ import annotations
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

def _capture_screenshots(case: CaseContext, app_name: str, artifact_count: int, process_count: int, tcp_count: int) -> list[str]:
    screenshots_dir = ensure_dir(case.images_dir)
    output_paths: list[str] = []

    desktop_path = screenshots_dir / "01_desktop_snapshot.png"
    try:
        image = ImageGrab.grab(all_screens=True)
        image.save(desktop_path)
        output_paths.append(str(desktop_path))
    except Exception:
        pass

    summary_path = screenshots_dir / "02_collection_summary.png"
    canvas = Image.new("RGB", (1600, 900), "#f4efe6")
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((60, 60, 1540, 840), radius=28, fill="#fffdf8", outline="#c6d3ce", width=3)
    draw.text((120, 110), f"FORENSICS_DISCORD - {app_name}", fill="#0f1720")
    draw.text((120, 180), f"Case ID: {case.case_id}", fill="#334155")
    draw.text((120, 240), f"Collected at: {now_iso()}", fill="#334155")
    draw.text((120, 330), f"Artifacts copied: {artifact_count}", fill="#0f766e")
    draw.text((120, 390), f"Processes found: {process_count}", fill="#0f766e")
    draw.text((120, 450), f"TCP connections found: {tcp_count}", fill="#0f766e")
    draw.text((120, 540), f"Live data: {case.live_dir}", fill="#475569")
    draw.text((120, 600), f"Acquired files: {case.acquired_dir}", fill="#475569")
    draw.text((120, 660), f"Browser artifacts: {case.browser_dir}", fill="#475569")
    draw.text((120, 720), f"Exports: {case.exports_dir}", fill="#475569")
    canvas.save(summary_path)
    output_paths.append(str(summary_path))

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
    screenshots = _capture_screenshots(case, adapter.display_name, len(manifest), len(process_rows), len(tcp_rows)) # type: ignore
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
