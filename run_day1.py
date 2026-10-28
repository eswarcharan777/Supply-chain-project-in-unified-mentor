"""Run the Day 1 data foundation pipeline for APL Logistics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.data_processing import load_and_prepare_csv
from src.metrics import calculate_kpis, data_quality_profile, performance_by


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare APL Logistics data for dashboard analysis.")
    parser.add_argument("--source", required=True, help="Path to the raw APL Logistics CSV file")
    parser.add_argument("--output-dir", default="data/processed", help="Directory for generated Day 1 outputs")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    data, audit = load_and_prepare_csv(args.source)
    kpis = calculate_kpis(data)

    data.to_csv(output_dir / "cleaned_logistics.csv", index=False)
    performance_by(data, "Shipping Mode").to_csv(output_dir / "shipping_mode_performance.csv", index=False)
    performance_by(data, "Order Region").to_csv(output_dir / "regional_performance.csv", index=False)
    performance_by(data, "Customer Segment").to_csv(output_dir / "customer_segment_performance.csv", index=False)
    data_quality_profile(data).to_csv(output_dir / "data_quality_profile.csv", index=False)

    with (output_dir / "day1_summary.json").open("w", encoding="utf-8") as file:
        json.dump({"data_audit": audit, "kpis": kpis}, file, indent=2)

    print(json.dumps({"data_audit": audit, "kpis": kpis}, indent=2))


if __name__ == "__main__":
    main()
