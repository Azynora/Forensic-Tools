from __future__ import annotations
from pathlib import Path
from fdctl.models import AppDetection, ArtifactTarget, CaseContext

class BaseAdapter:
    app_id = "base"
    display_name = "Base Adapter"
    support_level = "planned"
    process_names: tuple[str, ...] = ()

    def detect(self) -> AppDetection:
        raise NotImplementedError

    def get_artifact_targets(self, case: CaseContext) -> list[ArtifactTarget]:
        raise NotImplementedError

    def get_collection_scope(self) -> list[str]:
        return []

    def requires_admin_for_collection(self) -> bool:
        return False

    def find_launch_executable(self) -> Path | None:
        return None

    def build_analysis_defaults(self, case: CaseContext) -> dict:
        return {
            "appId": self.app_id,
            "displayName": self.display_name,
            "supportLevel": self.support_level,
            "caseId": case.case_id,
        }

    @staticmethod
    def home() -> Path:
        return Path.home()
