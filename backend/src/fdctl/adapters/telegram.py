from __future__ import annotations

import os
import shutil
import string
from pathlib import Path
from fdctl.adapters.base import BaseAdapter
from fdctl.models import AppDetection, ArtifactTarget, CaseContext


class TelegramAdapter(BaseAdapter):
    app_id = "telegram"
    display_name = "Telegram Desktop"
    support_level = "full"
    process_names = ("telegram.exe", "telegram")

    def find_launch_executable(self) -> Path | None:
        """Find the Telegram Desktop executable from running processes, portable dirs, or standard installs."""
        # 1. From running process (fast & 100% accurate if user has Telegram open)
        try:
            import psutil
            for p in psutil.process_iter(["name", "exe"]):
                p_name = (p.info["name"] or "").lower()
                if p_name in {"telegram.exe", "telegram"}:
                    exe_str = p.info.get("exe")
                    if exe_str and Path(exe_str).exists():
                        return Path(exe_str)
        except Exception:
            pass

        # 2. Candidate paths in user profile and program files
        home = Path.home()
        candidates: list[Path] = [
            home / "AppData" / "Roaming" / "Telegram Desktop" / "Telegram.exe",
            home / "AppData" / "Local" / "Programs" / "Telegram Desktop" / "Telegram.exe",
            home / "Downloads" / "Telegram Desktop" / "Telegram.exe",
            home / "AppData" / "Local" / "Microsoft" / "WindowsApps" / "Telegram.exe",
        ]

        # 3. Check common logical drives for portable or custom installations
        for letter in ("C", "D", "E", "F", "G"):
            drive_path = Path(f"{letter}:\\")
            if drive_path.exists():
                candidates.extend([
                    drive_path / "Telegram Desktop" / "Telegram.exe",
                    drive_path / "Telegram" / "Telegram.exe",
                    drive_path / "Program Files" / "Telegram Desktop" / "Telegram.exe",
                    drive_path / "Program Files (x86)" / "Telegram Desktop" / "Telegram.exe",
                ])

        for candidate in candidates:
            if candidate.exists():
                return candidate

        # 4. PATH lookup
        which_path = shutil.which("Telegram.exe") or shutil.which("Telegram")
        if which_path and Path(which_path).exists():
            return Path(which_path)

        return None

    def find_tdata_roots(self) -> list[Path]:
        """Find all valid tdata directory locations (portable, AppData, custom drive installs)."""
        found: list[Path] = []
        seen: set[str] = set()

        def _add_if_valid(p: Path) -> None:
            norm = str(p.resolve() if p.exists() else p).lower()
            if p.exists() and norm not in seen:
                # Must be a dir and ideally contain key_datas or session maps
                if p.is_dir():
                    found.append(p)
                    seen.add(norm)

        # 1. From executable parent directory (Telegram Portable puts tdata right next to Telegram.exe)
        exe = self.find_launch_executable()
        if exe:
            _add_if_valid(exe.parent / "tdata")

        # 2. Standard user profile paths
        home = Path.home()
        _add_if_valid(home / "AppData" / "Roaming" / "Telegram Desktop" / "tdata")
        _add_if_valid(home / "AppData" / "Local" / "Telegram Desktop" / "tdata")
        _add_if_valid(home / "Downloads" / "Telegram Desktop" / "tdata")

        # 3. Drive roots
        for letter in ("C", "D", "E", "F", "G"):
            drive_path = Path(f"{letter}:\\")
            if drive_path.exists():
                _add_if_valid(drive_path / "Telegram Desktop" / "tdata")
                _add_if_valid(drive_path / "Telegram" / "tdata")

        return found

    def detect(self) -> AppDetection:
        tdata_roots = self.find_tdata_roots()
        exe = self.find_launch_executable()

        install_paths: list[str] = []
        if exe:
            install_paths.append(str(exe.parent))
        for root in tdata_roots:
            p_str = str(root)
            if p_str not in install_paths:
                install_paths.append(p_str)

        detected = bool(tdata_roots) or exe is not None
        notes = [
            "Collects Telegram Desktop tdata session keys, maps, user_data media cache, and settings.",
            "Captures active Telegram.exe memory triage and TCP socket connections to Telegram Data Centers.",
            "Best-effort carving for phone numbers, @usernames, t.me links, and cached voice/media files.",
        ]
        return AppDetection(
            app_id=self.app_id,
            display_name=self.display_name,
            detected=detected,
            support_level=self.support_level,
            install_paths=install_paths,
            notes=notes,
        )

    def get_artifact_targets(self, case: CaseContext) -> list[ArtifactTarget]:
        home = Path.home()
        tdata_roots = self.find_tdata_roots()
        chrome_default = home / "AppData" / "Local" / "Google" / "Chrome" / "User Data" / "Default"

        targets: list[ArtifactTarget] = []

        for idx, tdata_root in enumerate(tdata_roots):
            dest_prefix = case.acquired_dir / "TelegramTdata" if idx == 0 else case.acquired_dir / f"TelegramTdata_{idx}"
            # 1. Core tdata root files (key_datas, settingss, usertag, maps...)
            for item in tdata_root.glob("*"):
                if item.is_file():
                    targets.append(
                        ArtifactTarget(
                            source=item,
                            destination=dest_prefix / item.name,
                            category="telegram",
                        )
                    )
                elif item.is_dir() and item.name.lower() not in {"user_data", "dumps", "temp"}:
                    # Session hex directories (e.g. D87FB344239AC...)
                    targets.append(
                        ArtifactTarget(
                            source=item,
                            destination=dest_prefix / item.name,
                            category="telegram",
                        )
                    )

            # 2. Media cache & user data (images, voice notes, stickers, cached documents)
            user_data_dir = tdata_root / "user_data"
            if user_data_dir.exists():
                for sub in ("cache", "media_cache", "wvbots"):
                    sub_dir = user_data_dir / sub
                    if sub_dir.exists():
                        targets.append(
                            ArtifactTarget(
                                source=sub_dir,
                                destination=dest_prefix / "user_data" / sub,
                                category="telegram_cache",
                            )
                        )

        # 3. Downloads folder if exists
        downloads_td = home / "Downloads" / "Telegram Desktop"
        if downloads_td.exists():
            targets.append(
                ArtifactTarget(
                    source=downloads_td,
                    destination=case.acquired_dir / "TelegramDownloads",
                    category="telegram_downloads",
                    optional=True,
                )
            )

        # 4. Chrome default profile history and cookies for web.telegram.org correlation
        if chrome_default.exists():
            for relative in [
                "History",
                "History-journal",
                "History-wal",
                "Cookies",
                "Cookies-journal",
                "Cookies-wal",
            ]:
                source_file = chrome_default / relative
                if source_file.exists():
                    targets.append(
                        ArtifactTarget(
                            source=source_file,
                            destination=case.browser_dir / "Chrome" / relative,
                            category="browser",
                            optional=True,
                        )
                    )

        return targets

    def get_collection_scope(self) -> list[str]:
        return [
            "Telegram Desktop session artifacts from %APPDATA%\\Telegram Desktop\\tdata and portable directories",
            "Telegram media cache and downloaded files",
            "Chrome default profile history and cookies related to web.telegram.org",
            "Live process and TCP snapshots for Telegram.exe processes",
        ]

    def requires_admin_for_collection(self) -> bool:
        return True
