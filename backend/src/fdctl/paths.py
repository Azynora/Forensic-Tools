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
    local_appdata = str(os.environ.get("LOCALAPPDATA", "") or "").strip()
    if local_appdata:
        settings = Path(local_appdata) / "FORENSICS_DISCORD" / "settings.json"
        try:
            import json
            data = json.loads(settings.read_text(encoding="utf-8"))
            workspace = str(data.get("workspace", "") or "").strip()
            if workspace:
                return Path(workspace).expanduser().resolve()
        except Exception:
            pass
    if getattr(sys, "frozen", False):
        documents = Path.home() / "Documents" / "FORENSICS_DISCORD"
        return documents
    return project_root() / "workspace"


def runtime_root() -> Path:
    return workspace_root() / "runtime"


def cases_root() -> Path:
    return workspace_root() / "cases"


def workspace_file() -> Path:
    return project_root() / "forensics-discord.code-workspace"
