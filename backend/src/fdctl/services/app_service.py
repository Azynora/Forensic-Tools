from __future__ import annotations
from fdctl.adapters import get_adapters
from fdctl.utils import launch_executable

def open_application(app_id: str, as_admin: bool = False) -> dict:
    adapters = get_adapters()
    adapter = adapters[app_id]
    executable = adapter.find_launch_executable() # type: ignore
    if executable is None:
        raise FileNotFoundError(f"No launch executable found for app '{app_id}'.")
    launch_executable(executable, as_admin=as_admin)
    return {
        "appId": app_id,
        "executablePath": str(executable),
        "launchedAsAdmin": as_admin,
    }
