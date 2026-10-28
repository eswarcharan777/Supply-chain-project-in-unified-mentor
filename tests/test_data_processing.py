"""Unit tests for logistics cleaning and KPI calculations."""

from __future__ import annotations

import unittest

import pandas as pd

from src.data_processing import classify_delivery, prepare_logistics_data
from src.metrics import calculate_kpis, data_quality_profile, performance_by


def sample_records() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Days for shipping (real)": [2, 3, 1, -1, 2],
            "Days for shipment (scheduled)": [2, 2, 3, 2, 2],
            "Late_delivery_risk": [0, 1, 0, 1, 0],
            "Delivery Status": ["Shipping on time ", "Late delivery", "Advance shipping", "Late delivery", "Shipping on time "],
            "Shipping Mode": ["Standard Class", "First Class", "Same Day", "First Class", "Standard Class"],
            "Order Region": ["Region A", "Region A", "Region B", "Region A", "Region A"],
            "Order Country": ["Country A", "Country A", "Country B", "Country A", "Country A"],
            "Market": ["Market A", "Market A", "Market B", "Market A", "Market A"],
            "Customer Segment": ["Consumer", "Corporate", "Consumer", "Corporate", "Consumer"],
        }
    )


class DeliveryClassificationTests(unittest.TestCase):
    def test_classifies_early_on_time_delayed_and_missing(self) -> None:
        self.assertEqual(classify_delivery(-1), "Early")
        self.assertEqual(classify_delivery(0), "On Time")
        self.assertEqual(classify_delivery(1), "Delayed")
        self.assertEqual(classify_delivery(None), "Unknown")

    def test_prepare_data_removes_duplicate_and_invalid_duration_records(self) -> None:
        data, audit = prepare_logistics_data(sample_records())
        self.assertEqual(audit["source_rows"], 5)
        self.assertEqual(audit["duplicate_rows_removed"], 1)
        self.assertEqual(audit["invalid_duration_rows_removed"], 1)
        self.assertEqual(audit["analysis_rows"], 3)
        self.assertListEqual(data["delivery_category"].tolist(), ["On Time", "Delayed", "Early"])
        self.assertTrue(data["Delivery Status"].eq(data["Delivery Status"].str.strip()).all())

    def test_missing_required_field_fails_with_clear_message(self) -> None:
        raw = sample_records().drop(columns=["Late_delivery_risk"])
        with self.assertRaisesRegex(ValueError, "Late_delivery_risk"):
            prepare_logistics_data(raw)


class MetricsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data, _ = prepare_logistics_data(sample_records())

    def test_kpis_match_expected_delivery_categories(self) -> None:
        kpis = calculate_kpis(self.data)
        self.assertEqual(kpis["total_shipments"], 3)
        self.assertEqual(kpis["on_time_delivery_rate"], 66.67)
        self.assertEqual(kpis["late_delivery_rate"], 33.33)
        self.assertEqual(kpis["average_delivery_delay_days"], -0.33)
        self.assertEqual(kpis["late_delivery_risk_ratio"], 33.33)

    def test_empty_kpis_are_safe(self) -> None:
        empty = self.data.iloc[0:0]
        kpis = calculate_kpis(empty)
        self.assertEqual(kpis["total_shipments"], 0)
        self.assertEqual(kpis["late_delivery_rate"], 0.0)

    def test_grouped_performance_and_quality_profile(self) -> None:
        grouped = performance_by(self.data, "Shipping Mode")
        first_class = grouped.loc[grouped["Shipping Mode"] == "First Class"].iloc[0]
        self.assertEqual(first_class["shipments"], 1)
        self.assertEqual(first_class["delayed_delivery_rate"], 100.0)
        profile = data_quality_profile(self.data)
        self.assertEqual(profile.loc[profile["column"] == "delivery_delay_gap", "missing_values"].iloc[0], 0)


if __name__ == "__main__":
    unittest.main()
