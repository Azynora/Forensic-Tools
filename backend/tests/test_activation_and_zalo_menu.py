from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fdctl.models import AppDetection
from fdctl.services import license_service
import fdctl.cli as cli


class _Progress:
    def __init__(self, *_args: object) -> None: pass
    def advance(self, *_args: object) -> None: pass
    def finish(self, *_args: object) -> None: pass


class _Adapter:
    def __init__(self, app_id: str) -> None:
        self.app_id = app_id
    def detect(self) -> AppDetection:
        return AppDetection(self.app_id, self.app_id.title(), False, "full" if self.app_id == "discord" else "planned")
    def requires_admin_for_collection(self) -> bool:
        return False


class ZaloSelectionTests(unittest.TestCase):
    def _run_menu(self, selected_app: str | None, choices: list[str]) -> tuple[list[tuple], list[str]]:
        notices: list[tuple] = []
        prompts: list[str] = []
        choice_iter = iter(choices)
        def choose(prompt: str) -> str:
            prompts.append(prompt)
            return next(choice_iter)
        args = SimpleNamespace(app=selected_app, channel_url=None, target_user=None, skip_open_discord=True)
        with (
            patch.object(cli, "setup_terminal"), patch.object(cli, "clear_screen"),
            patch.object(cli, "_styled_banner"), patch.object(cli, "print_copyright_notice"),
            patch.object(cli, "verify_bundle_integrity", return_value={"ok": True}),
            patch.object(cli, "_ensure_interactive_bundle_access", return_value={"features": ["collection"]}),
            patch.object(cli, "get_adapters", return_value={"discord": _Adapter("discord"), "zalo": _Adapter("zalo")}),
            patch.object(cli, "_numlock_enabled", return_value=None), patch.object(cli, "StageProgress", _Progress),
            patch.object(cli, "print_status", side_effect=lambda *values: notices.append(values)),
            patch.object(cli, "_prompt_selection", side_effect=choose),
            patch.object(cli, "is_admin", return_value=True),
            patch.object(cli, "create_case", side_effect=RuntimeError("controlled stop before collection")),
            patch("builtins.input", side_effect=["", ""]),
            redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()),
        ):
            cli.interactive_menu(args)
        return notices, prompts

    def test_zalo_choice_returns_to_discord_selection(self) -> None:
        notices, prompts = self._run_menu(None, ["2", "1"])
        self.assertEqual(len(prompts), 2)
        self.assertTrue(any("under development" in str(row) for row in notices))

    def test_preselected_zalo_returns_to_selection(self) -> None:
        notices, prompts = self._run_menu("zalo", ["1"])
        self.assertEqual(len(prompts), 1)
        self.assertTrue(any("under development" in str(row) for row in notices))


class LicenseEntitlementTests(unittest.TestCase):
    def test_trial_cannot_collect_real_evidence(self) -> None:
        with patch.object(license_service, "current_license_status", return_value={
            "active": True, "enforced": True, "features": ["demo"], "licenseType": "trial_7d_email",
        }):
            with self.assertRaises(PermissionError):
                license_service.require_active_license("collection")

    def test_paid_entitlement_can_collect(self) -> None:
        with patch.object(license_service, "current_license_status", return_value={
            "active": True, "enforced": True,
            "features": ["cli", "report", "collection", "analysis", "autopsy"],
        }):
            self.assertTrue(license_service.require_active_license("collection")["active"])

    def test_local_trial_last_seven_days_and_only_unlocks_demo(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with (
                patch.object(license_service, "activation_path", return_value=root / "active_license.json"),
                patch.object(license_service, "trial_registry_path", return_value=root / "trial_registry.json"),
                patch.object(license_service, "license_request_path", return_value=root / "request.txt"),
                patch.object(license_service, "remember_email_usage"),
            ):
                status = license_service.current_license_status(
                    selected_email="trial.user@gmail.com", force_enforced=True,
                )
        self.assertTrue(status["active"])
        self.assertEqual(status["daysValid"], 7)
        self.assertEqual(status["features"], ["demo"])


if __name__ == "__main__":
    unittest.main()
