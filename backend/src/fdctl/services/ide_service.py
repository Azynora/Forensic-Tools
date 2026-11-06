from __future__ import annotations
import shutil
import subprocess
from fdctl.paths import project_root, workspace_file

def open_workspace() -> str:
    code = shutil.which("code")
    if not code:
        raise FileNotFoundError("VS Code CLI 'code' not found in PATH.")
    target = workspace_file()
    subprocess.Popen([code, "-n", str(target)], cwd=str(project_root()))
    return str(target)
