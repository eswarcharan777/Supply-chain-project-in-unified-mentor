"""End-to-end render tests for the Streamlit dashboard."""

from __future__ import annotations

import os
from pathlib import Path
import unittest

from streamlit.testing.v1 import AppTest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TMP_DIR = PROJECT_ROOT / ".tmp-streamlit-test"


class DashboardRenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        TMP_DIR.mkdir(exist_ok=True)
        os.environ["TEMP"] = str(TMP_DIR)
        os.environ["TMP"] = str(TMP_DIR)
        os.environ["STREAMLIT_TEST_MODE"] = "1"

    def test_default_dashboard_renders_all_core_controls(self) -> None:
        app = AppTest.from_file(str(PROJECT_ROOT / "app.py"))
        app.run(timeout=120)
        self.assertFalse(app.exception)
        self.assertGreaterEqual(len(app.metric), 5)
        self.assertGreaterEqual(len(app.multiselect), 5)
        self.assertEqual(len(app.download_button), 0)
        self.assertGreaterEqual(len(app.info), 1)
        self.assertGreaterEqual(len(app.warning), 1)
        self.assertIn("180,519", app.metric[0].value)

    def test_shipping_filter_and_clear_all_return_expected_counts(self) -> None:
        app = AppTest.from_file(str(PROJECT_ROOT / "app.py"))
        app.run(timeout=120)
        app.multiselect[0].set_value(["First Class"]).run(timeout=120)
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[0].value, "27,814")
        self.assertEqual(app.metric[2].value, "100.00%")
        app.button[1].click().run(timeout=120)
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[0].value, "180,519")

    def test_exact_narrow_filter_case_from_manual_validation(self) -> None:
        app = AppTest.from_file(str(PROJECT_ROOT / "app.py"))
        app.run(timeout=120)
        values = [
            ["First Class"],
            ["Africa"],
            ["North Africa"],
            ["Algeria"],
            ["Consumer"],
        ]
        for widget, value in zip(app.multiselect, values, strict=True):
            widget.set_value(value)
        app.run(timeout=120)
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[0].value, "30")
        self.assertEqual(app.metric[2].value, "100.00%")


if __name__ == "__main__":
    unittest.main()
