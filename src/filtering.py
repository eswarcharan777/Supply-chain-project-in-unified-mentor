"""Efficient cascading filter helpers for the logistics dashboard."""

from __future__ import annotations

import pandas as pd


def option_values(data: pd.DataFrame, column: str) -> list[str]:
    """Return sorted, non-empty values that are valid for one filter."""
    return sorted(data[column].dropna().astype(str).unique().tolist())


def apply_selection(data: pd.DataFrame, column: str, selected: list[str]) -> pd.DataFrame:
    """Apply a multi-select filter only when the user has selected values."""
    if not selected:
        return data
    return data.loc[data[column].astype(str).isin(selected)]


def valid_selection(selected: list[str], options: list[str]) -> list[str]:
    """Keep only selections that remain possible after an upstream change."""
    allowed = set(options)
    return [value for value in selected if value in allowed]
