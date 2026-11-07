from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from fdctl.adapters.base import BaseAdapter
from fdctl.models import AppDetection, ArtifactTarget, CaseContext


class DiscordAdapter(BaseAdapter):
    app_id = "discord"
    display_name = "Discord"
    support_level = "full"
    process_names = ("discord.exe", "discordsystemhelper.exe", "discord", "Discord")

    def _candidate_config_roots(self) -> list[Path]:
        home = Path.home()
        candidates: list[Path] = []
        if sys.platform == "win32":
            candidates.append(home / "AppData" / "Roaming" / "discord")
        else:
            candidates.extend(
                [
                    home / ".config" / "discord",
                    home / ".var" / "app" / "com.discordapp.Discord" / "config" / "discord",
                    home / "snap" / "discord" / "current" / ".config" / "discord",
                ]
            )
        return candidates

    def _candidate_local_roots(self) -> list[Path]:
        home = Path.home()
        candidates: list[Path] = []
        if sys.platform == "win32":
            candidates.append(home / "AppData" / "Local" / "Discord")
        return candidates

    def _candidate_browser_profiles(self) -> list[Path]:
        home = Path.home()
        candidates: list[Path] = []
        if sys.platform == "win32":
            candidates.extend(
                [
                    home / "AppData" / "Local" / "Google" / "Chrome" / "User Data" / "Default",
                    home / "AppData" / "Local" / "BraveSoftware" / "Brave-Browser" / "User Data" / "Default",
                    home / "AppData" / "Local" / "Microsoft" / "Edge" / "User Data" / "Default",
                ]
            )
        else:
            candidates.extend(
                [
                    home / ".config" / "google-chrome" / "Default",
                    home / ".config" / "chromium" / "Default",
                    home / ".config" / "BraveSoftware" / "Brave-Browser" / "Default",
                    home / ".var" / "app" / "com.google.Chrome" / "config" / "google-chrome" / "Default",
                ]
            )
        return candidates

    def detect(self) -> AppDetection:
        config_roots = [p for p in self._candidate_config_roots() if p.exists()]
        local_roots = [p for p in self._candidate_local_roots() if p.exists()]
        install_paths = [str(p) for p in (config_roots + local_roots)]
        notes = [
            "Collects Discord desktop artifacts, browser history, cookies metadata, live triage, and best-effort message recovery.",
            "Analysis does not use legacy case data and only reads files collected into the current case.",
        ]
        return AppDetection(
            app_id=self.app_id,
            display_name=self.display_name,
            detected=bool(install_paths),
            support_level=self.support_level,
            install_paths=install_paths,
            notes=notes,
        )

    def get_artifact_targets(self, case: CaseContext) -> list[ArtifactTarget]:
        targets: list[ArtifactTarget] = []

        config_roots = [p for p in self._candidate_config_roots() if p.exists()]
        primary_root = config_roots[0] if config_roots else (
            Path.home() / "AppData" / "Roaming" / "discord" if sys.platform == "win32" else Path.home() / ".config" / "discord"
        )

        relative_items = [
            Path("Cache") / "Cache_Data",
            Path("Code Cache"),
            Path("GPUCache"),
            Path("Local Storage") / "leveldb",
            Path("Session Storage"),
            Path("logs"),
            Path("Network"),
            Path("Service Worker"),
            Path("blob_storage"),
            Path("settings.json"),
            Path("Local State"),
            Path("Preferences"),
        ]

        for rel in relative_items:
            source = primary_root / rel
            destination = case.acquired_dir / "DiscordRoaming" / rel
            targets.append(ArtifactTarget(source=source, destination=destination, category="discord"))

        for local_root in self._candidate_local_roots():
            if local_root.exists():
                targets.append(
                    ArtifactTarget(
                        source=local_root,
                        destination=case.acquired_dir / "DiscordLocal",
                        category="discord",
                    )
                )

        browser_profiles = [p for p in self._candidate_browser_profiles() if p.exists()]
        chrome_default = browser_profiles[0] if browser_profiles else None
        if chrome_default and chrome_default.exists():
            for name in [
                "History",
                "History-journal",
                "History-wal",
                "History-shm",
                "Cookies",
                "Cookies-journal",
                "Cookies-wal",
                "Cookies-shm",
                "Login Data",
                "Login Data-journal",
                "Login Data-wal",
                "Login Data-shm",
            ]:
                source = chrome_default / name
                targets.append(
                    ArtifactTarget(
                        source=source,
                        destination=case.browser_dir / "Chrome" / name,
                        category="browser",
                        optional=True,
                    )
                )

        return targets

    def get_collection_scope(self) -> list[str]:
        if sys.platform == "win32":
            storage_label = "%APPDATA% and %LOCALAPPDATA%"
        else:
            storage_label = "~/.config/discord or Flatpak/Snap containers"
        return [
            f"Discord desktop artifacts from {storage_label}",
            "Browser default profile history and cookies",
            "Discord cache, code cache, GPU cache, and browser-linked cache artifacts",
            "Live process and TCP snapshots for Discord processes",
        ]

    def requires_admin_for_collection(self) -> bool:
        return sys.platform == "win32"

    def find_launch_executable(self) -> Path | None:
        if sys.platform == "win32":
            local_root = Path.home() / "AppData" / "Local" / "Discord"
            version_dirs = sorted(local_root.glob("app-*"), reverse=True)
            for version_dir in version_dirs:
                candidate = version_dir / "Discord.exe"
                if candidate.exists():
                    return candidate
            fallback = local_root / "Update.exe"
            return fallback if fallback.exists() else None

        for name in ("discord", "Discord"):
            which = shutil.which(name)
            if which and Path(which).exists():
                return Path(which)
        for linux_path in [
            Path("/usr/bin/discord"),
            Path("/usr/share/discord/Discord"),
            Path.home() / ".local" / "share" / "flatpak" / "exports" / "bin" / "com.discordapp.Discord",
            Path("/var/lib/flatpak/exports/bin/com.discordapp.Discord"),
            Path("/snap/bin/discord"),
        ]:
            if linux_path.exists():
                return linux_path
        return None
