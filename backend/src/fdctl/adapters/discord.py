from __future__ import annotations
from pathlib import Path
from fdctl.adapters.base import BaseAdapter
from fdctl.models import AppDetection, ArtifactTarget, CaseContext

class DiscordAdapter(BaseAdapter):
    app_id = "discord"
    display_name = "Discord"
    support_level = "full"
    process_names = ("discord.exe", "discordsystemhelper.exe")

    def detect(self) -> AppDetection:
        roaming_root = Path.home() / "AppData" / "Roaming" / "discord"
        local_root = Path.home() / "AppData" / "Local" / "Discord"
        install_paths = [str(path) for path in (roaming_root, local_root) if path.exists()]
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
        home = Path.home()
        roaming_root = home / "AppData" / "Roaming" / "discord"
        local_root = home / "AppData" / "Local" / "Discord"
        chrome_default = home / "AppData" / "Local" / "Google" / "Chrome" / "User Data" / "Default"

        targets: list[ArtifactTarget] = []
        for relative in [
            "Cache\\Cache_Data",
            "Code Cache",
            "GPUCache",
            "Local Storage\\leveldb",
            "Session Storage",
            "logs",
            "Network",
            "Service Worker",
            "blob_storage",
            "settings.json",
            "Local State",
            "Preferences",
        ]:
            source = roaming_root / relative
            destination = case.acquired_dir / "DiscordRoaming" / Path(relative)
            targets.append(ArtifactTarget(source=source, destination=destination, category="discord"))

        if local_root.exists():
            targets.append(
                ArtifactTarget(
                    source=local_root,
                    destination=case.acquired_dir / "DiscordLocal",
                    category="discord",
                )
            )

        for relative in [
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
            targets.append(
                ArtifactTarget(
                    source=chrome_default / relative,
                    destination=case.browser_dir / "Chrome" / relative,
                    category="browser",
                )
            )

        return targets

    def get_collection_scope(self) -> list[str]:
        return [
            "Discord desktop artifacts from %APPDATA% and %LOCALAPPDATA%",
            "Chrome default profile history and cookies",
            "Discord cache, code cache, GPU cache, and browser-linked cache artifacts",
            "Live process and TCP snapshots for Discord processes",
        ]

    def requires_admin_for_collection(self) -> bool:
        return True

    def find_launch_executable(self) -> Path | None:
        local_root = Path.home() / "AppData" / "Local" / "Discord"
        version_dirs = sorted(local_root.glob("app-*"), reverse=True)
        for version_dir in version_dirs:
            candidate = version_dir / "Discord.exe"
            if candidate.exists():
                return candidate
        fallback = local_root / "Update.exe"
        return fallback if fallback.exists() else None
