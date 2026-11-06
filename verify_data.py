"""Independently check the sample data with Python; no model or API needed."""
from collections import defaultdict
import csv
import json
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent / "sample_project"


def verify_sales(path: Path) -> dict:
    totals: dict[str, int] = defaultdict(int)
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != ["item", "units"]:
            raise ValueError("This checker expects exactly the item,units schema.")
        rows = list(reader)
    for line, row in enumerate(rows, start=2):
        if None in row or not row["item"] or row["units"] is None:
            raise ValueError(f"Incomplete or extra fields at CSV line {line}.")
        try:
            units = int(row["units"])
        except ValueError:
            raise ValueError(f"Expected whole-number units at CSV line {line}.") from None
        totals[row["item"]] += units
    return {"data_rows": len(rows), "units_by_item": dict(totals),
            "revenue": "Cannot calculate: no price column."}


def verify_order(path: Path) -> dict:
    order = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(order, dict):
        raise ValueError("Expected a JSON object for the order.")
    for key in ("order_id", "status", "total"):
        if key not in order:
            raise ValueError(f"Missing order field: {key}")
    return {"order_id": order["order_id"], "status": order["status"],
            "total": order["total"], "total_is_null": order["total"] is None}


def main():
    findings = {"sales.csv": verify_sales(PROJECT_DIR / "sales.csv"),
                "order.json": verify_order(PROJECT_DIR / "order.json")}
    print(json.dumps(findings, indent=2))


if __name__ == "__main__":
    main()
