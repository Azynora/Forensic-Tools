from __future__ import annotations

from fdctl.adapters import get_adapters
from fdctl.utils import launch_executable


def open_application(app_id: str, as_admin: bool = False) -> dict:
    adapters = get_adapters()
    adapter = adapters[app_id]

    # Check if the application is already running
    try:
        import psutil
        for p in psutil.process_iter(["name", "exe"]):
            p_name = (p.info["name"] or "").lower()
            if any(target in p_name for target in adapter.process_names):
                return {
                    "appId": app_id,
                    "executablePath": str(p.info.get("exe") or "Active Process"),
                    "alreadyRunning": True,
                    "launchedAsAdmin": False,
                    "status": "already_active",
                }
    except Exception:
        pass

    executable = adapter.find_launch_executable()  # type: ignore
    if executable is None:
        raise FileNotFoundError(f"No launch executable found for app '{app_id}'.")
    launch_executable(executable, as_admin=as_admin)
    return {
        "appId": app_id,
        "executablePath": str(executable),
        "alreadyRunning": False,
        "launchedAsAdmin": as_admin,
        "status": "launched",
    }
