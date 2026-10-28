"""SQLite persistence helpers for the local live-data API demonstration."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


def initialize_database(database_path: str | Path, csv_path: str | Path) -> int:
    """Create or refresh the local SQLite shipment table from prepared data."""
    database_path = Path(database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    data = pd.read_csv(csv_path)
    with sqlite3.connect(database_path) as connection:
        data.to_sql("shipments", connection, if_exists="replace", index=False)
        connection.execute("CREATE INDEX IF NOT EXISTS idx_shipments_region ON shipments ([Order Region])")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_shipments_mode ON shipments ([Shipping Mode])")
    return len(data)


def database_status(database_path: str | Path) -> dict[str, int | bool]:
    path = Path(database_path)
    if not path.exists():
        return {"ready": False, "rows": 0}
    with sqlite3.connect(path) as connection:
        rows = int(connection.execute("SELECT COUNT(*) FROM shipments").fetchone()[0])
    return {"ready": True, "rows": rows}
