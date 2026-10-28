"""Data preparation functions for the APL Logistics dashboard."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


ACTUAL_DAYS = "Days for shipping (real)"
SCHEDULED_DAYS = "Days for shipment (scheduled)"
RISK_COLUMN = "Late_delivery_risk"


def clean_column_names(frame: pd.DataFrame) -> pd.DataFrame:
    """Trim whitespace from source column names without renaming business fields."""
    cleaned = frame.copy()
    cleaned.columns = [str(column).strip() for column in cleaned.columns]
    return cleaned


def normalize_text_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Trim text values and normalize the fields used by dashboard filters."""
    cleaned = frame.copy()
    text_columns = [
        "Delivery Status",
        "Shipping Mode",
        "Order Region",
        "Order Country",
        "Market",
        "Customer Segment",
    ]
    for column in text_columns:
        if column in cleaned.columns:
            cleaned[column] = cleaned[column].astype("string").str.strip()
    return cleaned


def classify_delivery(delay_gap: float | int | None) -> str:
    """Return a business-readable delivery classification from the delay gap."""
    if pd.isna(delay_gap):
        return "Unknown"
    if delay_gap < 0:
        return "Early"
    if delay_gap == 0:
        return "On Time"
    return "Delayed"


def prepare_logistics_data(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """Validate, deduplicate, and enrich raw APL Logistics records.

    Rows without valid non-negative actual and scheduled shipping durations are
    excluded because they cannot support the central delivery-performance KPIs.
    """
    data = normalize_text_columns(clean_column_names(raw))
    source_rows = len(data)
    duplicate_rows = int(data.duplicated().sum())
    data = data.drop_duplicates().copy()

    for column in (ACTUAL_DAYS, SCHEDULED_DAYS, RISK_COLUMN):
        if column not in data.columns:
            raise ValueError(f"Required column is missing: {column}")
        data[column] = pd.to_numeric(data[column], errors="coerce")

    valid_duration = (
        data[ACTUAL_DAYS].notna()
        & data[SCHEDULED_DAYS].notna()
        & data[ACTUAL_DAYS].ge(0)
        & data[SCHEDULED_DAYS].ge(0)
    )
    invalid_duration_rows = int((~valid_duration).sum())
    data = data.loc[valid_duration].copy()

    data["delivery_delay_gap"] = data[ACTUAL_DAYS] - data[SCHEDULED_DAYS]
    data["delivery_category"] = data["delivery_delay_gap"].map(classify_delivery)
    data["is_delayed"] = data["delivery_category"].eq("Delayed")
    data["is_on_time_or_early"] = data["delivery_category"].isin(["On Time", "Early"])

    # Retain only known binary values; other source values remain missing for audit.
    data[RISK_COLUMN] = data[RISK_COLUMN].where(data[RISK_COLUMN].isin([0, 1]))
    audit = {
        "source_rows": source_rows,
        "duplicate_rows_removed": duplicate_rows,
        "invalid_duration_rows_removed": invalid_duration_rows,
        "analysis_rows": len(data),
    }
    return data, audit


def slugify(value: object) -> str:
    """Create stable text labels for future grouping or URL-safe exports."""
    return re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")


def load_and_prepare_csv(source_path: str | Path) -> tuple[pd.DataFrame, dict[str, int]]:
    """Read an APL CSV file and return analytics-ready data plus audit metrics."""
    try:
        raw = pd.read_csv(source_path, low_memory=False, encoding="utf-8")
    except UnicodeDecodeError:
        # The supplied source export contains Windows-1252 characters.
        raw = pd.read_csv(source_path, low_memory=False, encoding="cp1252")
    return prepare_logistics_data(raw)
