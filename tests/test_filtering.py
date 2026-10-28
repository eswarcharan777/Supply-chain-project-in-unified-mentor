"""Tests for cascading dashboard filter behavior."""

from __future__ import annotations

import unittest

import pandas as pd

from src.filtering import apply_selection, option_values, valid_selection


class CascadingFilterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = pd.DataFrame(
            {
                "Market": ["Africa", "Africa", "Europe", "Europe"],
                "Order Region": ["East Africa", "North Africa", "Western Europe", "Eastern Europe"],
                "Order Country English": ["Kenya", "Algeria", "France", "Poland"],
                "Customer Segment": ["Consumer", "Corporate", "Consumer", "Home Office"],
            }
        )

    def test_market_restricts_regions_and_country(self) -> None:
        africa = apply_selection(self.data, "Market", ["Africa"])
        self.assertEqual(option_values(africa, "Order Region"), ["East Africa", "North Africa"])
        east_africa = apply_selection(africa, "Order Region", ["East Africa"])
        self.assertEqual(option_values(east_africa, "Order Country English"), ["Kenya"])

    def test_invalid_downstream_selection_is_removed(self) -> None:
        self.assertEqual(valid_selection(["France", "Kenya"], ["Kenya", "Algeria"]), ["Kenya"])


if __name__ == "__main__":
    unittest.main()
