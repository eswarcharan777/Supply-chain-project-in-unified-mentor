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

    def test_default_dashboard_waits_for_a_filter_selection(self) -> None:
        app = AppTest.from_file(str(PROJECT_ROOT / "app.py"))
        app.run(timeout=120)
        self.assertFalse(app.exception)
        self.assertEqual(len(app.metric), 0)
        self.assertGreaterEqual(len(app.multiselect), 5)
        self.assertEqual(len(app.download_button), 0)
        self.assertIn("Select at least one filter", app.info[0].value)

    def test_shipping_filter_and_clear_all_return_to_filter_prompt(self) -> None:
        app = AppTest.from_file(str(PROJECT_ROOT / "app.py"))
        app.run(timeout=120)
        app.multiselect[0].set_value(["First Class"]).run(timeout=120)
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[0].value, "27,814")
        self.assertEqual(app.metric[2].value, "100.00%")
        # Target the control by label: button indexes shift as panels are
        # rendered, so a positional click can hit an unrelated button.
        clear_button = next(button for button in app.button if button.label == "Clear all filters")
        clear_button.click().run(timeout=120)
        self.assertFalse(app.exception)
        self.assertEqual(len(app.metric), 0)
        self.assertIn("Select at least one filter", app.info[0].value)

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

    def test_route_simulator_generates_a_plan_without_errors(self) -> None:
        # The route simulator reads the dashboard's loaded columns, which do not
        # include Order City. This guards against a KeyError that silently
        # broke the feature while the screenshot evidence still showed a
        # rendered panel.
        app = AppTest.from_file(str(PROJECT_ROOT / "app.py"))
        app.run(timeout=120)
        app.multiselect[0].set_value(["First Class"]).run(timeout=120)
        simulate = next(button for button in app.button if button.label == "Generate simulated visit plan")
        simulate.click().run(timeout=120)
        self.assertFalse(app.exception)
        self.assertTrue(any(metric.value.endswith("km") for metric in app.metric))


if __name__ == "__main__":
    unittest.main()
