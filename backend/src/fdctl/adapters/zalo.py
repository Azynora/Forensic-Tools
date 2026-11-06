from __future__ import annotations
from pathlib import Path
from fdctl.adapters.base import BaseAdapter
from fdctl.models import AppDetection, ArtifactTarget, CaseContext

class ZaloAdapter(BaseAdapter):
    app_id = "zalo"
    display_name = "Zalo"
    support_level = "planned"
    process_names = ("zalo.exe", "zalopc.exe")

    def detect(self) -> AppDetection:
        home = Path.home()
        candidates = [
            home / "AppData" / "Local" / "Programs" / "Zalo",
            home / "AppData" / "Roaming" / "Zalo",
            home / "AppData" / "Local" / "ZaloPC",
        ]
        detected = any(path.exists() for path in candidates)
        notes = [
            "Zalo is kept as a secondary future option.",
            "The current build does not expose or persist Zalo application paths in reports.",
            "Deep Zalo collection and analysis will be added in a later implementation pass.",
        ]
        return AppDetection(
            app_id=self.app_id,
            display_name=self.display_name,
            detected=detected,
            support_level=self.support_level,
            install_paths=[],
            notes=notes,
        )

    def get_artifact_targets(self, case: CaseContext) -> list[ArtifactTarget]:
        return []

    def get_collection_scope(self) -> list[str]:
        return [
            "Zalo is reserved for future implementation in the current build.",
            "No Zalo artifact paths are collected or shown yet.",
        ]
