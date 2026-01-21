"""
data_loader.py

Reads market_data.csv using the built-in csv module.

Space complexity note:
- We parse the CSV into a Python list of MarketDataPoint.
- If there are N rows, storing the entire dataset in memory is O(N) space.
  Each MarketDataPoint stores:
    - datetime object (constant-sized reference)
    - symbol string reference (the string itself costs extra; worst-case O(len(symbol)))
    - float
  The list itself also stores N references.

If you wanted to reduce space, you could stream ticks (generator) instead of collecting them.
This assignment explicitly requests collecting them in a list.
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple, Optional

from models import MarketDataPoint


def _parse_timestamp(value: str) -> datetime:
    """
    Parses timestamp robustly:
    - ISO 8601 (recommended): 2026-01-20T13:30:00 or with timezone
    - If ends with 'Z', treat as UTC.
    """
    s = value.strip()
    if s.endswith("Z"):
        # datetime.fromisoformat doesn't accept trailing 'Z' directly in older versions.
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    # If naive, assume UTC to keep consistent.
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def load_market_data(csv_path: str | Path) -> List[MarketDataPoint]:
    """
    Load all ticks from CSV into a list.

    Time: O(N) for N rows.
    Space: O(N) for storing the list of ticks.
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path.resolve()}")

    points: List[MarketDataPoint] = []
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"timestamp", "symbol", "price"}
        if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
            raise ValueError(f"CSV must have columns {sorted(required)}; got {reader.fieldnames}")

        for row in reader:
            ts = _parse_timestamp(row["timestamp"])
            symbol = row["symbol"].strip()
            price = float(row["price"])
            points.append(MarketDataPoint(timestamp=ts, symbol=symbol, price=price))

    return points


def estimate_dataset_space_complexity(n_rows: int) -> str:
    """
    Returns a short explanation of theoretical space complexity.

    We keep it theoretical (Big-O) rather than pretending we can know exact bytes
    across Python implementations.
    """
    return (
        f"Storing {n_rows:,} ticks in a Python list is O(N) space.\n"
        "- List holds N references (O(N)).\n"
        "- Each MarketDataPoint holds constant-number of fields (O(1) per tick),\n"
        "  plus symbol string storage (bounded by symbol length).\n"
        "Overall: O(N) total space."
    )
