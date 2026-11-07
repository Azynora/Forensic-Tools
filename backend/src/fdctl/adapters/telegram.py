from __future__ import annotations
import os
from pathlib import Path
from fdctl.adapters.base import BaseAdapter
from fdctl.models import AppDetection, ArtifactTarget, CaseContext

class TelegramAdapter(BaseAdapter):
    app_id = "telegram"
    display_name = "Telegram Desktop"
    support_level = "full"
    process_names = ("telegram.exe",)

    def detect(self) -> AppDetection:
        home = Path.home()
        roaming_tdata = home / "AppData" / "Roaming" / "Telegram Desktop" / "tdata"
        local_install = home / "AppData" / "Local" / "Programs" / "Telegram Desktop"
        roaming_install = home / "AppData" / "Roaming" / "Telegram Desktop"
        downloads_td = home / "Downloads" / "Telegram Desktop"

        install_paths = [
            str(p) for p in (roaming_install, local_install, downloads_td) if p.exists()
        ]
        detected = roaming_tdata.exists() or bool(install_paths)
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
        tdata_root = home / "AppData" / "Roaming" / "Telegram Desktop" / "tdata"
        chrome_default = home / "AppData" / "Local" / "Google" / "Chrome" / "User Data" / "Default"

        targets: list[ArtifactTarget] = []

        if tdata_root.exists():
            # 1. Core tdata root files (key_datas, settingss, usertag, maps...)
            for item in tdata_root.glob("*"):
                if item.is_file():
                    targets.append(
                        ArtifactTarget(
                            source=item,
                            destination=case.acquired_dir / "TelegramTdata" / item.name,
                            category="telegram",
                        )
                    )
                elif item.is_dir() and item.name.lower() not in {"user_data", "dumps", "temp"}:
                    # Session hex directories (e.g. D87FB344239AC...)
                    targets.append(
                        ArtifactTarget(
                            source=item,
                            destination=case.acquired_dir / "TelegramTdata" / item.name,
                            category="telegram",
                        )
                    )

            # 2. Media cache (images, voice notes, stickers, cached documents)
            cache_dir = tdata_root / "user_data" / "cache"
            if cache_dir.exists():
                targets.append(
                    ArtifactTarget(
                        source=cache_dir,
                        destination=case.acquired_dir / "TelegramTdata" / "user_data" / "cache",
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
            "Telegram Desktop session artifacts from %APPDATA%\\Telegram Desktop\\tdata",
            "Telegram media cache and downloaded files",
            "Chrome default profile history and cookies related to web.telegram.org",
            "Live process and TCP snapshots for Telegram.exe processes",
        ]

    def requires_admin_for_collection(self) -> bool:
        return True

    def find_launch_executable(self) -> Path | None:
        home = Path.home()
        candidates = [
            home / "AppData" / "Roaming" / "Telegram Desktop" / "Telegram.exe",
            home / "AppData" / "Local" / "Programs" / "Telegram Desktop" / "Telegram.exe",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None
