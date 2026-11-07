from __future__ import annotations

import os
import sys
from pathlib import Path


def _optional_env_path(name: str) -> Path | None:
    value = str(os.environ.get(name, "") or "").strip()
    if not value:
        return None
    return Path(value).expanduser().resolve()


def _bundle_root() -> Path:
    executable_dir = Path(sys.executable).resolve().parent
    if executable_dir.name.lower() == "fdctl_runtime":
        return executable_dir.parent
    return executable_dir


def project_root() -> Path:
    if getattr(sys, "frozen", False):
        return _bundle_root()
    return Path(__file__).resolve().parents[3]


def workspace_root() -> Path:
    configured_root = _optional_env_path("FDCTL_DATA_ROOT")
    if configured_root:
        return configured_root
    settings_candidates: list[Path] = []
    local_appdata = str(os.environ.get("LOCALAPPDATA", "") or "").strip()
    if local_appdata:
        settings_candidates.append(Path(local_appdata) / "FORENSIC_SUITE" / "settings.json")
        settings_candidates.append(Path(local_appdata) / "FORENSICS_DISCORD" / "settings.json")
    xdg_config = str(os.environ.get("XDG_CONFIG_HOME", "") or "").strip()
    if xdg_config:
        settings_candidates.append(Path(xdg_config) / "FORENSIC_SUITE" / "settings.json")
        settings_candidates.append(Path(xdg_config) / "FORENSICS_DISCORD" / "settings.json")
    else:
        settings_candidates.append(Path.home() / ".config" / "FORENSIC_SUITE" / "settings.json")
        settings_candidates.append(Path.home() / ".config" / "FORENSICS_DISCORD" / "settings.json")

    for settings in settings_candidates:
        if settings.is_file():
            try:
                import json
                data = json.loads(settings.read_text(encoding="utf-8"))
                workspace = str(data.get("workspace", "") or "").strip()
                if workspace:
                    return Path(workspace).expanduser().resolve()
            except Exception:
                pass
    if getattr(sys, "frozen", False):
        if sys.platform == "win32":
            documents = Path.home() / "Documents" / "Forensics Suite"
        else:
            xdg_data = str(os.environ.get("XDG_DATA_HOME", "") or "").strip()
            if xdg_data:
                documents = Path(xdg_data) / "ForensicsSuite"
            else:
                documents = Path.home() / ".local" / "share" / "ForensicsSuite"
        return documents
    return project_root() / "workspace"


def runtime_root() -> Path:
    return workspace_root() / "runtime"


def cases_root() -> Path:
    return workspace_root() / "cases"


def workspace_file() -> Path:
    return project_root() / "forensics-discord.code-workspace"
