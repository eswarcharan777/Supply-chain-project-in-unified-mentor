"""Clearly labeled route-planning simulation using available customer coordinates."""

from __future__ import annotations

import math

import pandas as pd


def _distance_km(a_lat: float, a_lon: float, b_lat: float, b_lon: float) -> float:
    radius = 6371.0
    lat_delta = math.radians(b_lat - a_lat)
    lon_delta = math.radians(b_lon - a_lon)
    value = math.sin(lat_delta / 2) ** 2 + math.cos(math.radians(a_lat)) * math.cos(math.radians(b_lat)) * math.sin(lon_delta / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(value))


def simulated_route_plan(data: pd.DataFrame, origin_lat: float, origin_lon: float, stops: int) -> pd.DataFrame:
    """Build a nearest-neighbour visit order for high-volume customer locations.

    This is a planning simulation only. The dataset has customer coordinates but
    no warehouse, road, traffic, carrier, or cost information.
    """
    columns = ["Order Country", "Latitude", "Longitude", "delivery_delay_gap"]
    # Order City is useful context for a stop, but it is not part of the
    # dashboard's column set. Fall back gracefully when it is absent instead of
    # raising a KeyError.
    has_city = "Order City" in data.columns
    if has_city:
        columns.insert(1, "Order City")
    frame = data[columns].copy()
    frame["Latitude"] = pd.to_numeric(frame["Latitude"], errors="coerce")
    frame["Longitude"] = pd.to_numeric(frame["Longitude"], errors="coerce")
    frame = frame.dropna(subset=["Latitude", "Longitude"])
    group_keys = ["Order Country", "Latitude", "Longitude"]
    if has_city:
        group_keys.insert(1, "Order City")
    locations = (
        frame.groupby(group_keys, as_index=False)
        .agg(shipments=("delivery_delay_gap", "size"), average_delay_days=("delivery_delay_gap", "mean"))
        .sort_values("shipments", ascending=False)
        .head(max(1, stops))
        .copy()
    )
    remaining = locations.to_dict("records")
    plan: list[dict[str, object]] = []
    current_lat, current_lon = origin_lat, origin_lon
    total_distance = 0.0
    while remaining:
        next_stop = min(remaining, key=lambda row: _distance_km(current_lat, current_lon, float(row["Latitude"]), float(row["Longitude"])))
        leg_distance = _distance_km(current_lat, current_lon, float(next_stop["Latitude"]), float(next_stop["Longitude"]))
        total_distance += leg_distance
        plan.append({
            "stop": len(plan) + 1,
            "country": next_stop["Order Country"],
            "city": next_stop.get("Order City", ""),
            "shipments": int(next_stop["shipments"]),
            "average_delay_days": round(float(next_stop["average_delay_days"]), 2),
            "leg_distance_km": round(leg_distance, 1),
            "cumulative_distance_km": round(total_distance, 1),
        })
        current_lat, current_lon = float(next_stop["Latitude"]), float(next_stop["Longitude"])
        remaining.remove(next_stop)
    return pd.DataFrame(plan)
