from __future__ import annotations
import csv
import ctypes
import getpass
import json
try:
    import msvcrt
except ImportError:
    msvcrt = None  # type: ignore[assignment]
import os
import sqlite3
import stat
import shutil
import socket
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable
import psutil


GENERIC_READ = 0x80000000
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
FILE_SHARE_DELETE = 0x00000004
OPEN_EXISTING = 3
FILE_ATTRIBUTE_NORMAL = 0x00000080
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

def now_iso() -> str:
    return datetime.now(UTC).astimezone().isoformat()

def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def to_extended_path(path: Path | str) -> str:
    path_str = str(path)
    if sys.platform == 'win32' and not path_str.startswith('\\\\?\\') and os.path.isabs(path_str):
        return '\\\\?\\' + os.path.abspath(path_str)
    return path_str

def ensure_dir(path: Path) -> Path:
    if sys.platform == 'win32':
        os.makedirs(to_extended_path(path), exist_ok=True)
    else:
        path.mkdir(parents=True, exist_ok=True)
    return path

def write_json(path: Path, data: object) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})

def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))

def is_admin() -> bool:
    if sys.platform == "win32":
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return False
    try:
        return os.geteuid() == 0
    except AttributeError:
        return False

def _elevation_command(arguments: list[str] | None = None) -> tuple[str, str]:
    arg_list = arguments if arguments is not None else sys.argv[1:]
    if getattr(sys, "frozen", False):
        return sys.executable, subprocess.list2cmdline(arg_list)
    command = ["-m", "fdctl", *arg_list]
    return sys.executable, subprocess.list2cmdline(command)

def rerun_as_admin(arguments: list[str] | None = None) -> None:
    if sys.platform != "win32":
        arg_list = arguments if arguments is not None else sys.argv[1:]
        cmd = ["sudo", sys.executable]
        if not getattr(sys, "frozen", False):
            cmd.extend(["-m", "fdctl"])
        cmd.extend(arg_list)
        ret = subprocess.call(cmd)
        raise SystemExit(ret)
    executable, params = _elevation_command(arguments)
    result = ctypes.windll.shell32.ShellExecuteW(None, "runas", executable, params, str(Path.cwd()), 1)
    if result <= 32:
        raise RuntimeError("User declined elevation or Windows failed to relaunch the command.")
    raise SystemExit(0)

def launch_executable(path: Path, as_admin: bool = False) -> None:
    if sys.platform == "win32":
        if as_admin:
            result = ctypes.windll.shell32.ShellExecuteW(None, "runas", str(path), None, str(path.parent), 1)
            if result <= 32:
                raise RuntimeError(f"Windows failed to launch {path} as administrator.")
            return
        os.startfile(str(path))
        return
    cmd: list[str] = []
    if as_admin:
        cmd = ["sudo", str(path)]
    elif shutil.which("xdg-open"):
        cmd = ["xdg-open", str(path)]
    else:
        cmd = [str(path)]
    subprocess.Popen(cmd)

def open_path(path: Path) -> None:
    if sys.platform == "win32":
        os.startfile(str(path))
    else:
        cmd = ["xdg-open", str(path)] if shutil.which("xdg-open") else ["open", str(path)]
        subprocess.Popen(cmd)

def run_command(command: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        check=check,
        text=True,
        capture_output=True,
    )

def _open_windows_shared_reader(path: Path):
    if sys.platform != "win32" or msvcrt is None:
        return path.open("rb")
    handle = ctypes.windll.kernel32.CreateFileW(
        to_extended_path(path),
        GENERIC_READ,
        FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
        None,
        OPEN_EXISTING,
        FILE_ATTRIBUTE_NORMAL,
        None,
    )
    if handle == INVALID_HANDLE_VALUE:
        raise OSError(ctypes.get_last_error(), f"CreateFileW failed for {path}")
    fd = msvcrt.open_osfhandle(handle, os.O_RDONLY)
    return os.fdopen(fd, "rb")

def copy_file_preserve(source: Path, destination: Path) -> None:
    ensure_dir(destination.parent)
    src_ext = to_extended_path(source.resolve()) if sys.platform == 'win32' else str(source)
    dst_ext = to_extended_path(destination.resolve()) if sys.platform == 'win32' else str(destination)
    try:
        shutil.copy2(src_ext, dst_ext)
    except OSError:
        with _open_windows_shared_reader(source) as reader, open(dst_ext, 'wb') as writer:
            shutil.copyfileobj(reader, writer)
        try:
            shutil.copystat(src_ext, dst_ext)
        except OSError:
            pass

def _sqlite_uri(path: Path, immutable: bool = False) -> str:
    uri = f"file:{path.as_posix()}?mode=ro"
    if immutable:
        uri += "&immutable=1"
    return uri

def _execute_sqlite_query(db_path: Path, query: str, immutable: bool = False) -> list[dict]:
    connection = sqlite3.connect(_sqlite_uri(db_path, immutable=immutable), uri=True)
    connection.row_factory = sqlite3.Row
    try:
        return [dict(row) for row in connection.execute(query)]
    finally:
        connection.close()

def query_sqlite_rows(db_path: Path, query: str) -> list[dict]:
    if not db_path.exists():
        return []
    try:
        return _execute_sqlite_query(db_path, query)
    except (sqlite3.DatabaseError, OSError):
        pass

    try:
        with tempfile.TemporaryDirectory(prefix="fdctl-sqlite-") as temp_dir:
            temp_root = Path(temp_dir)
            shadow_db = temp_root / db_path.name
            copy_file_preserve(db_path, shadow_db)
            for suffix in ("-wal", "-shm", "-journal"):
                sidecar = Path(str(db_path) + suffix)
                if sidecar.exists():
                    copy_file_preserve(sidecar, temp_root / sidecar.name)
            return _execute_sqlite_query(shadow_db, query, immutable=True)
    except (sqlite3.DatabaseError, OSError):
        return []

def _rmtree_onerror(function, path: str, excinfo) -> None:
    os.chmod(path, stat.S_IWRITE)
    function(path)

def remove_tree(path: Path) -> None:
    if path.exists():
        target = to_extended_path(path) if sys.platform == "win32" else path
        shutil.rmtree(target, onerror=_rmtree_onerror)

def iter_files(root: Path) -> Iterable[Path]:
    if root.is_file():
        yield root
        return
    for path in root.rglob("*"):
        if path.is_file():
            yield path

def relative_to(path: Path, base: Path) -> str:
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)

def collect_local_ipv4_addresses() -> list[dict]:
    rows: list[dict] = []
    for interface_name, addresses in psutil.net_if_addrs().items():
        for address in addresses:
            if getattr(address, "family", None) == socket.AF_INET and address.address and not address.address.startswith("127."):
                rows.append(
                    {
                        "interface": interface_name,
                        "ipAddress": address.address,
                        "netmask": address.netmask or "",
                        "broadcast": address.broadcast or "",
                    }
                )
    return rows

def current_user_context() -> dict:
    return {
        "username": getpass.getuser(),
        "hostname": socket.gethostname(),
        "fqdn": socket.getfqdn(),
        "localIpv4": collect_local_ipv4_addresses(),
    }
