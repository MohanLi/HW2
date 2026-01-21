import time
import tracemalloc
from datetime import datetime, timezone, timedelta

import pytest

from models import MarketDataPoint
from strategies import OptimizedCumulativeAverageStrategy


def make_ticks(n, symbol="XYZ"):
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    ticks = []
    # deterministic, non-random prices (fast + reproducible)
    for i in range(n):
        price = float((i % 100) + 1)  # 1..100 repeating
        ticks.append(MarketDataPoint(timestamp=base + timedelta(seconds=i), symbol=symbol, price=price))
    return ticks


@pytest.mark.performance
def test_optimized_under_1s_and_100mb_for_100k_ticks():
    """
    Requirement: optimized strategy <1s runtime and <100MB memory for 100k ticks.

    Notes:
    - Runtime depends on machine speed; this test assumes a typical modern dev/CI environment.
    - Memory uses tracemalloc (Python allocation peak). This is a conservative, stable measure.
    """
    ticks = make_ticks(100_000)
    strat = OptimizedCumulativeAverageStrategy()

    # Memory
    tracemalloc.start()
    t0 = time.perf_counter()
    strat.reset()
    for tick in ticks:
        strat.generate_signals(tick)
    t1 = time.perf_counter()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    elapsed = t1 - t0
    peak_mb = peak / (1024 * 1024)

    assert elapsed < 1.0, f"Elapsed {elapsed:.3f}s >= 1.0s"
    assert peak_mb < 100.0, f"Peak {peak_mb:.2f}MB >= 100MB"
