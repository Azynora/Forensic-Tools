from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fdctl.services.license_service import (
    validate_supported_email,
    issue_compact_license_token,
    verify_license_token,
    current_license_status,
    find_dropin_license_file,
    get_license_watermark,
    is_wildcard_machine_hash,
    COMPACT_MACHINE_HASH_BYTES,
)


class SustainableLicensingTests(unittest.TestCase):
    def test_corporate_and_gmail_email_validation(self) -> None:
        # Standard corporate & government emails
        self.assertEqual(validate_supported_email("analyst@viettel.com.vn"), "analyst@viettel.com.vn")
        self.assertEqual(validate_supported_email("security@fpt.com"), "security@fpt.com")
        self.assertEqual(validate_supported_email("investigator@bca.gov.vn"), "investigator@bca.gov.vn")

        # Gmail canonicalization (dots removed)
        self.assertEqual(validate_supported_email("john.doe@gmail.com"), "johndoe@gmail.com")

        # Invalid emails
        with self.assertRaises(ValueError):
            validate_supported_email("invalid_email")
        with self.assertRaises(ValueError):
            validate_supported_email("no_domain@")
        with self.assertRaises(ValueError):
            validate_supported_email("@nodomain.com")

    def test_portable_wildcard_license_issuance_and_verification(self) -> None:
        issued = issue_compact_license_token(
            email="soc-lead@viettel.com.vn",
            license_type="issued_365d",
            is_portable=True,
            max_seats=10,
        )
        self.assertEqual(issued["licenseMode"], "portable")
        self.assertEqual(issued["isPortable"], True)
        self.assertEqual(issued["maxSeats"], 10)
        self.assertTrue(is_wildcard_machine_hash(issued["machineHash"]))

        # Verification passes on any machine
        verified = verify_license_token(issued["token"])
        self.assertTrue(verified["active"])
        self.assertEqual(verified["payload"]["licenseMode"], "portable")
        self.assertEqual(verified["payload"]["maxSeats"], 10)

    def test_dropin_license_file_auto_discovery(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            issued = issue_compact_license_token(
                email="forensic@lab.org",
                license_type="issued_30d",
                is_portable=True,
            )
            key_file = temp_root / "license.key"
            key_file.write_text(issued["token"], encoding="utf-8")

            # find_dropin_license_file discovers it
            found = find_dropin_license_file(root=temp_root)
            self.assertEqual(found, key_file)

            # current_license_status recognizes it immediately
            status = current_license_status(root=temp_root, force_enforced=True)
            self.assertTrue(status["active"])
            self.assertEqual(status["source"], "dropin_license")
            self.assertEqual(status["licenseMode"], "portable")
            self.assertEqual(status["licenseLabel"], "Issued Access 30 Days")

    def test_license_watermark_formatting(self) -> None:
        status = {
            "issuedToEmail": "analyst@viettel.com.vn",
            "issuedToName": "Viettel SOC",
            "licenseId": "a1b2c3d4e5f60718",
            "licenseLabel": "Enterprise Edition",
            "licenseMode": "portable",
        }
        wm = get_license_watermark(status)
        self.assertIn("Viettel SOC (analyst@viettel.com.vn)", wm["identity"])
        self.assertIn("#A1B2C3D4", wm["shortId"])
        self.assertEqual(wm["mode"], "PORTABLE")
        self.assertIn("OFFICIAL FORENSIC EXAMINATION REPORT", wm["reportWatermark"])
        self.assertIn("VIETTEL SOC", wm["reportWatermark"])


if __name__ == "__main__":
    unittest.main()
