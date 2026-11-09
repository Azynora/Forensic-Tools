from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path
from typing import Callable

from fdctl import __release__
from fdctl.paths import project_root, workspace_root

GITHUB_REPO = "Azynora/Forensic-Tools"
LATEST_RELEASE_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


def _parse_version(v_str: str) -> tuple[int, ...]:
    """Parse version string like 'v1.4.2' or '1.4.2' into comparable integer tuple (1, 4, 2)."""
    cleaned = re.sub(r"^[^\d]*", "", str(v_str or "").strip())
    parts = []
    for p in cleaned.split("."):
        digits = "".join(c for c in p if c.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def check_github_update(repo: str = GITHUB_REPO, timeout: int = 6) -> dict:
    """
    Check GitHub Releases for newer version of Forensics Suite.
    Returns:
        dict with keys:
          - has_update (bool)
          - current_version (str)
          - latest_version (str)
          - release_name (str)
          - release_notes (str)
          - published_at (str)
          - setup_url (str | None)
          - portable_url (str | None)
          - checksum_url (str | None)
          - setup_size (int)
          - portable_size (int)
          - offline (bool)
          - error (str | None)
    """
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": f"ForensicsSuite-Updater/{__release__} (Windows x64)",
            "Accept": "application/vnd.github.v3+json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as err:
        return {
            "has_update": False,
            "current_version": __release__,
            "latest_version": __release__,
            "offline": True,
            "error": f"Không thể kết nối máy chủ GitHub (Chế độ Offline): {err.reason}",
        }
    except Exception as exc:
        return {
            "has_update": False,
            "current_version": __release__,
            "latest_version": __release__,
            "offline": True,
            "error": f"Lỗi kiểm tra cập nhật: {exc}",
        }

    tag_name = str(data.get("tag_name", "")).strip()
    latest_v = _parse_version(tag_name)
    current_v = _parse_version(__release__)

    has_update = latest_v > current_v

    setup_url = None
    portable_url = None
    checksum_url = None
    setup_size = 0
    portable_size = 0

    for asset in data.get("assets", []):
        name = str(asset.get("name", "")).lower()
        d_url = asset.get("browser_download_url")
        size = int(asset.get("size", 0))

        if name.endswith("_setup.exe") or (name.endswith(".exe") and "setup" in name):
            setup_url = d_url
            setup_size = size
        elif name.endswith("_portable.zip") or (name.endswith(".zip") and "portable" in name):
            portable_url = d_url
            portable_size = size
        elif "sha256" in name or name.endswith(".txt"):
            checksum_url = d_url

    return {
        "has_update": has_update,
        "current_version": __release__,
        "latest_version": tag_name.lstrip("v"),
        "raw_tag": tag_name,
        "release_name": data.get("name", tag_name),
        "release_notes": data.get("body", ""),
        "published_at": data.get("published_at", ""),
        "setup_url": setup_url,
        "portable_url": portable_url,
        "checksum_url": checksum_url,
        "setup_size": setup_size,
        "portable_size": portable_size,
        "offline": False,
        "error": None,
    }


def download_file(
    url: str,
    target_path: Path,
    progress_callback: Callable[[int, int], None] | None = None,
    chunk_size: int = 65536,
) -> Path:
    """Download a file with streaming chunks and optional progress callback."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": f"ForensicsSuite-Updater/{__release__}"},
    )
    with urllib.request.urlopen(req) as resp:
        total_size = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "wb") as f:
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if progress_callback:
                    progress_callback(downloaded, total_size)
    return target_path


def apply_installer_update(installer_path: Path, silent: bool = False) -> None:
    """
    Launch the downloaded Setup.exe installer to perform in-place upgrade.
    Preserves all %LOCALAPPDATA% licenses and workspace cases.
    """
    args = [str(installer_path)]
    if silent:
        # Inno Setup silent flags
        args.extend(["/SILENT", "/CLOSEAPPLICATIONS", "/RESTARTAPPLICATIONS"])
    subprocess.Popen(args, close_fds=True)
    # The caller application should exit so installer can overwrite running binaries
