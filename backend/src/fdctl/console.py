from __future__ import annotations

import ctypes
import sys
import textwrap
from shutil import get_terminal_size

from fdctl import __release__


_COLOR_ENABLED = False

_FG = {
    "muted": "37",
    "red": "91",
    "green": "32",
    "yellow": "33",
    "blue": "34",
    "magenta": "35",
    "cyan": "36",
    "white": "97",
}

COPYRIGHT_OWNER = "Truong Trieu Vy"
COPYRIGHT_EMAIL = "trieuvy9198@gmail.com"


def setup_terminal(title: str = "Forensics Suite Investigator") -> None:
    global _COLOR_ENABLED
    _configure_console_io()
    _COLOR_ENABLED = _enable_ansi()
    _set_title(title)


def _configure_console_io() -> None:
    if sys.platform == "win32":
        try:
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleOutputCP(65001)
            kernel32.SetConsoleCP(65001)
        except Exception:
            pass
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def _enable_ansi() -> bool:
    if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
        return False
    if sys.platform != "win32":
        return True
    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)) == 0:
            return False
        if kernel32.SetConsoleMode(handle, mode.value | 0x0004) == 0:
            return False
        return True
    except Exception:
        return False


def _set_title(title: str) -> None:
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.kernel32.SetConsoleTitleW(title)
    except Exception:
        return


def colorize(text: str, fg: str = "white", bold: bool = False, dim: bool = False) -> str:
    if not _COLOR_ENABLED:
        return text
    codes = []
    if bold:
        codes.append("1")
    if dim:
        codes.append("2")
    codes.append(_FG.get(fg, _FG["white"]))
    return f"\033[{';'.join(codes)}m{text}\033[0m"


def terminal_width(default: int = 108) -> int:
    return max(80, min(get_terminal_size((default, 30)).columns, 132))


def _wrap_text(value: str, width: int, indent: str = "") -> list[str]:
    text = str(value or "")
    if not text:
        return [""]

    wrapped_lines: list[str] = []
    for raw_line in text.splitlines() or [""]:
        line = raw_line.rstrip()
        if not line:
            wrapped_lines.append("")
            continue
        wrapped_lines.extend(
            textwrap.wrap(
                line,
                width=max(20, width),
                break_long_words=False,
                break_on_hyphens=False,
                subsequent_indent=indent,
            )
            or [""]
        )
    return wrapped_lines


def clear_screen() -> None:
    if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
        return
    print("\033[2J\033[H" if _COLOR_ENABLED else "\n" * 2, end="")


def print_banner(title: str, subtitle: str) -> None:
    width = terminal_width()
    line = "=" * width
    print(colorize(line, "cyan"))
    print(colorize(title.center(width), "green", bold=True))
    print(colorize(subtitle.center(width), "muted"))
    version_line = f"Release {__release__}"
    print(colorize(version_line.center(width), "white", bold=True))
    copyright_line = f"Copyright (c) {COPYRIGHT_OWNER} | {COPYRIGHT_EMAIL} | All rights reserved."
    print(colorize(copyright_line.center(width), "yellow"))
    print(colorize(line, "cyan"))


def print_copyright_notice() -> None:
    print_status("info", f"Copyright (c) {COPYRIGHT_OWNER}", f"{COPYRIGHT_EMAIL} | All rights reserved.")


def print_section(title: str, detail: str = "") -> None:
    print("")
    print(colorize(f"[ {title} ]", "cyan", bold=True))
    if detail:
        for line in _wrap_text(detail, terminal_width() - 2):
            print(colorize(line, "muted"))


def print_status(kind: str, message: str, detail: str = "") -> None:
    palette = {
        "info": ("[INFO]", "blue"),
        "ok": ("[ OK ]", "green"),
        "warn": ("[WARN]", "yellow"),
        "error": ("[FAIL]", "red"),
        "step": ("[STEP]", "cyan"),
    }
    prefix, fg = palette.get(kind, ("[INFO]", "white"))
    message_width = terminal_width() - len(prefix) - 3
    wrapped_message = _wrap_text(message, message_width)
    print(f"{colorize(prefix, fg, bold=True)} {colorize(wrapped_message[0], 'white', bold=(kind in {'ok', 'step'}))}")
    for line in wrapped_message[1:]:
        print(f"       {colorize(line, 'white')}")
    if detail:
        for line in _wrap_text(detail, terminal_width() - 8):
            print(f"       {colorize(line, 'muted')}")


def print_kv(key: str, value: str) -> None:
    label = f"{key}:"
    label_text = colorize(label, "green", bold=True)
    label_width = len(label) + 1
    wrapped_value = _wrap_text(value, terminal_width() - label_width - 1)
    print(f"{label_text} {colorize(wrapped_value[0], 'white')}")
    for line in wrapped_value[1:]:
        print(f"{' ' * label_width} {colorize(line, 'white')}")


def progress_bar(percent: int, width: int = 28) -> str:
    safe_percent = max(0, min(100, percent))
    filled = int(width * safe_percent / 100)
    return "[" + ("=" * filled) + ("." * (width - filled)) + "]"


def print_progress(percent: int, title: str, detail: str = "") -> None:
    bar = progress_bar(percent)
    line = f"{bar} {percent:>3}% {title}"
    print(colorize(line, "magenta", bold=True))
    if detail:
        print(f"       {colorize(detail, 'muted')}")


class StageProgress:
    def __init__(self, total_steps: int, start_percent: int = 0, end_percent: int = 100) -> None:
        self.total_steps = max(1, total_steps)
        self.start_percent = start_percent
        self.end_percent = end_percent
        self.current = 0

    def advance(self, title: str, detail: str = "") -> int:
        self.current = min(self.current + 1, self.total_steps)
        span = self.end_percent - self.start_percent
        percent = self.start_percent + int(span * self.current / self.total_steps)
        print_progress(percent, title, detail)
        return percent

    def finish(self, title: str, detail: str = "") -> None:
        self.current = self.total_steps
        print_progress(self.end_percent, title, detail)
