"""KPI and grouping helpers for the supply-chain dashboard."""

from __future__ import annotations

import pandas as pd


def calculate_kpis(data: pd.DataFrame) -> dict[str, float | int]:
    """Calculate the project KPIs from prepared logistics data."""
    total_shipments = len(data)
    if total_shipments == 0:
        return {
            "total_shipments": 0,
            "on_time_delivery_rate": 0.0,
            "late_delivery_rate": 0.0,
            "average_delivery_delay_days": 0.0,
            "late_delivery_risk_ratio": 0.0,
        }

    risk = pd.to_numeric(data["Late_delivery_risk"], errors="coerce")
    return {
        "total_shipments": total_shipments,
        "on_time_delivery_rate": round(data["is_on_time_or_early"].mean() * 100, 2),
        "late_delivery_rate": round(data["is_delayed"].mean() * 100, 2),
        "average_delivery_delay_days": round(data["delivery_delay_gap"].mean(), 2),
        "late_delivery_risk_ratio": round(risk.mean() * 100, 2),
    }


def performance_by(data: pd.DataFrame, column: str) -> pd.DataFrame:
    """Summarize operational delivery performance by a selected dimension."""
    required = [column, "delivery_delay_gap", "is_delayed", "is_on_time_or_early"]
    grouped = data.dropna(subset=[column]).groupby(column, dropna=False)
    summary = grouped.agg(
        shipments=("delivery_delay_gap", "size"),
        average_delay_days=("delivery_delay_gap", "mean"),
        delayed_delivery_rate=("is_delayed", "mean"),
        on_time_delivery_rate=("is_on_time_or_early", "mean"),
    ).reset_index()
    summary["average_delay_days"] = summary["average_delay_days"].round(2)
    summary["delayed_delivery_rate"] = (summary["delayed_delivery_rate"] * 100).round(2)
    summary["on_time_delivery_rate"] = (summary["on_time_delivery_rate"] * 100).round(2)
    return summary.sort_values("shipments", ascending=False).reset_index(drop=True)


def data_quality_profile(data: pd.DataFrame) -> pd.DataFrame:
    """Profile fields that power the dashboard filters and KPI calculations."""
    dashboard_fields = [
        "Days for shipping (real)",
        "Days for shipment (scheduled)",
        "Late_delivery_risk",
        "Delivery Status",
        "Shipping Mode",
        "Order Region",
        "Order Country",
        "Market",
        "Customer Segment",
        "delivery_delay_gap",
        "delivery_category",
    ]
    rows = []
    for column in dashboard_fields:
        if column in data.columns:
            rows.append(
                {
                    "column": column,
                    "missing_values": int(data[column].isna().sum()),
                    "distinct_values": int(data[column].nunique(dropna=True)),
                }
            )
    return pd.DataFrame(rows)
