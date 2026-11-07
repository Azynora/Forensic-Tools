from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from fdctl.adapters.telegram import TelegramAdapter
from fdctl.app_catalog import get_app
from fdctl.models import CaseContext
from fdctl.services.app_service import open_application
import fdctl.cli as cli


class TelegramAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = TelegramAdapter()

    def test_app_id_and_support_level(self) -> None:
        self.assertEqual(self.adapter.app_id, "telegram")
        self.assertEqual(self.adapter.display_name, "Telegram Desktop")
        self.assertEqual(self.adapter.support_level, "full")
        self.assertIn("telegram.exe", self.adapter.process_names)

    def test_app_catalog_available(self) -> None:
        app = get_app("telegram")
        self.assertEqual(app["status"], "available")
        self.assertIn("Telegram", app["name"])

    def test_get_artifact_targets(self) -> None:
        case = CaseContext("case_001", "telegram", Path(r"D:\dummy\case_001"))
        targets = self.adapter.get_artifact_targets(case)
        self.assertIsInstance(targets, list)

    def test_resolve_menu_choice_for_telegram(self) -> None:
        detection = self.adapter.detect()
        available = [detection]
        resolved = cli._resolve_menu_choice("telegram", available)
        self.assertEqual(getattr(resolved, "app_id", ""), "telegram")

    def test_find_tdata_roots(self) -> None:
        roots = self.adapter.find_tdata_roots()
        self.assertIsInstance(roots, list)

    def test_open_application_for_telegram(self) -> None:
        res = open_application("telegram", as_admin=False)
        self.assertEqual(res.get("appId"), "telegram")
        self.assertIn(res.get("status"), {"launched", "already_active"})


if __name__ == "__main__":
    unittest.main()
