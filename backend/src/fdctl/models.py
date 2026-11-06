from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path

WORK_DIR_NAMES = [
    "01_Case_Info",
    "02_Live_Response",
    "03_Acquired_Files",
    "04_Browser_Artifacts",
    "05_Autopsy_Case",
    "06_Screenshots",
    "07_Exports",
    "08_Report",
]

@dataclass(slots=True)
class ArtifactTarget:
    source: Path
    destination: Path
    category: str
    optional: bool = True

@dataclass(slots=True)
class AppDetection:
    app_id: str
    display_name: str
    detected: bool
    support_level: str
    install_paths: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

@dataclass(slots=True)
class CaseContext:
    case_id: str
    app_id: str
    root: Path
    saved: bool = False

    @property
    def info_dir(self) -> Path:
        return self.root / "01_Case_Info"

    @property
    def live_dir(self) -> Path:
        return self.root / "02_Live_Response"

    @property
    def acquired_dir(self) -> Path:
        return self.root / "03_Acquired_Files"

    @property
    def browser_dir(self) -> Path:
        return self.root / "04_Browser_Artifacts"

    @property
    def autopsy_dir(self) -> Path:
        return self.root / "05_Autopsy_Case"

    @property
    def images_dir(self) -> Path:
        return self.root / "06_Screenshots"

    @property
    def exports_dir(self) -> Path:
        return self.root / "07_Exports"

    @property
    def report_dir(self) -> Path:
        return self.root / "08_Report"
