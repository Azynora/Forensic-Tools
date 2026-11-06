from __future__ import annotations

from pathlib import Path

from fdctl.models import CaseContext

CASE_SNAPSHOT_NAME = "case_snapshot.json"


def case_snapshot_path(case: CaseContext) -> Path:
    return case.report_dir / CASE_SNAPSHOT_NAME

