"""Tests for the route-planning simulation helper."""

from __future__ import annotations

import unittest

import pandas as pd

from src.routing import simulated_route_plan


def sample_route_data(include_city: bool) -> pd.DataFrame:
    records = {
        "Order Country": ["España", "España", "France", "France"],
        "Latitude": [40.4168, 40.4168, 48.8566, 48.8566],
        "Longitude": [-3.7038, -3.7038, 2.3522, 2.3522],
        "delivery_delay_gap": [2, 3, -1, 1],
    }
    if include_city:
        records["Order City"] = ["Madrid", "Madrid", "Paris", "Paris"]
    return pd.DataFrame(records)


class RouteSimulationTests(unittest.TestCase):
    def test_plan_is_built_when_order_city_column_is_present(self) -> None:
        plan = simulated_route_plan(sample_route_data(include_city=True), 0.0, 0.0, 3)
        self.assertEqual(len(plan), 2)
        self.assertEqual(plan.iloc[0]["country"], "España")
        self.assertEqual(plan.iloc[0]["city"], "Madrid")
        self.assertGreater(plan.iloc[-1]["cumulative_distance_km"], 0)

    def test_plan_is_built_when_order_city_column_is_absent(self) -> None:
        # The dashboard's column set does not include Order City, so the
        # simulator must not raise a KeyError when that column is missing.
        plan = simulated_route_plan(sample_route_data(include_city=False), 0.0, 0.0, 3)
        self.assertEqual(len(plan), 2)
        self.assertEqual(plan.iloc[0]["country"], "España")
        self.assertEqual(plan.iloc[0]["city"], "")
        self.assertGreater(plan.iloc[-1]["cumulative_distance_km"], 0)

    def test_visits_are_ordered_nearest_neighbour(self) -> None:
        plan = simulated_route_plan(sample_route_data(include_city=True), 48.8566, 2.3522, 3)
        # Starting in Paris, the first stop must be Paris itself.
        self.assertEqual(plan.iloc[0]["country"], "France")

    def test_rows_without_coordinates_are_ignored(self) -> None:
        data = sample_route_data(include_city=False)
        # Drop every Madrid coordinate; only Paris should remain as a stop.
        data.loc[data["Order Country"] == "España", ["Latitude", "Longitude"]] = None
        plan = simulated_route_plan(data, 0.0, 0.0, 3)
        self.assertEqual(len(plan), 1)
        self.assertEqual(plan.iloc[0]["country"], "France")


if __name__ == "__main__":
    unittest.main()
