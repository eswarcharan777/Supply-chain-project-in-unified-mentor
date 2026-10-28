"""Local FastAPI service for APL Logistics live-data integration."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query

from src.database import database_status, initialize_database


DATABASE_PATH = Path("data/live/apl_logistics.db")
CSV_PATH = Path("data/processed/cleaned_logistics.csv")
app = FastAPI(title="APL Logistics API", version="1.0.0")


def _connection() -> sqlite3.Connection:
    if not DATABASE_PATH.exists():
        if not CSV_PATH.exists():
            raise HTTPException(status_code=503, detail="Prepared logistics data is unavailable.")
        initialize_database(DATABASE_PATH, CSV_PATH)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


@app.get("/health")
def health() -> dict[str, int | bool]:
    if not DATABASE_PATH.exists() and CSV_PATH.exists():
        initialize_database(DATABASE_PATH, CSV_PATH)
    return database_status(DATABASE_PATH)


@app.get("/shipments")
def shipments(limit: int = Query(default=100, ge=1, le=1000), shipping_mode: str | None = None) -> list[dict[str, object]]:
    # Do not expose customer name, street address, or other personally identifying columns.
    query = """SELECT [Shipping Mode], [Market], [Order Region], [Order Country],
        [Customer Segment], [Category Name], [Days for shipment (scheduled)],
        delivery_delay_gap, delivery_category, is_delayed FROM shipments"""
    values: list[object] = []
    if shipping_mode:
        query += " WHERE [Shipping Mode] = ?"
        values.append(shipping_mode)
    query += " LIMIT ?"
    values.append(limit)
    with _connection() as connection:
        return [dict(row) for row in connection.execute(query, values).fetchall()]


@app.get("/summary")
def summary() -> dict[str, float | int]:
    with _connection() as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS shipments, AVG(is_delayed) * 100 AS delayed_rate, AVG(delivery_delay_gap) AS average_delay_days FROM shipments"
        ).fetchone()
    return {"shipments": int(row["shipments"]), "delayed_rate": round(float(row["delayed_rate"]), 2), "average_delay_days": round(float(row["average_delay_days"]), 2)}
