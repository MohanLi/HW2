import csv
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path


def generate_market_data_csv(
    out_path: str = "market_data.csv",
    symbol: str = "SIM",
    n: int = 100_000,
    start_price: float = 100.0,
    start_time: datetime | None = None,
    step_seconds: int = 1,
    drift: float = 0.0,
    volatility: float = 0.2,
    seed: int = 42,
) -> Path:
    """
    Generates synthetic market data using a simple random-walk model.

    price[t+1] = max(0.01, price[t] + drift + noise)
    noise ~ Normal(0, volatility)

    Produces timestamps in ISO 8601 with timezone, e.g. 2026-01-01T00:00:00+00:00
    """
    rng = random.Random(seed)
    if start_time is None:
        start_time = datetime(2026, 1, 1, tzinfo=timezone.utc)

    out = Path(out_path)

    current_price = float(start_price)
    current_time = start_time

    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "symbol", "price"])

        for _ in range(n):
            writer.writerow([current_time.isoformat(), symbol, f"{current_price:.6f}"])

            # Box-Muller for ~Normal(0, 1) without numpy
            u1 = max(rng.random(), 1e-12)
            u2 = rng.random()
            z0 = ( (-2.0 * __import__("math").log(u1)) ** 0.5 ) * __import__("math").cos(2.0 * __import__("math").pi * u2)

            noise = z0 * volatility
            current_price = max(0.01, current_price + drift + noise)

            current_time = current_time + timedelta(seconds=step_seconds)

    return out


if __name__ == "__main__":
    path = generate_market_data_csv(
        out_path="market_data.csv",
        symbol="SIM",
        n=100_000,          # matches your benchmark max size
        start_price=100.0,
        step_seconds=1,
        drift=0.0005,       # small upward drift
        volatility=0.2,     # noise size
        seed=42,
    )
    print(f"Wrote {path.resolve()}")
