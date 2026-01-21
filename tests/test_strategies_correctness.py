import math
from datetime import datetime, timezone, timedelta

import pytest

from models import MarketDataPoint
from strategies import (
    NaiveMovingAverageStrategy,
    OptimizedCumulativeAverageStrategy,
    WindowedMovingAverageStrategy,
)


def make_ticks(prices, symbol="XYZ"):
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    ticks = []
    for i, p in enumerate(prices):
        ticks.append(MarketDataPoint(timestamp=base + timedelta(seconds=i), symbol=symbol, price=float(p)))
    return ticks


def signals_only(strategy, ticks):
    out = []
    strategy.reset()
    for t in ticks:
        out.extend(strategy.generate_signals(t))
    return out


def test_optimized_matches_naive_for_cumulative_average_signals():
    prices = [10, 12, 11, 13, 13, 12, 14, 9, 10, 10]
    ticks = make_ticks(prices)

    naive = NaiveMovingAverageStrategy()
    opt = OptimizedCumulativeAverageStrategy()

    s1 = signals_only(naive, ticks)
    s2 = signals_only(opt, ticks)

    assert [x.action for x in s1] == [x.action for x in s2]
    # references should be very close floating-point-wise
    for a, b in zip(s1, s2):
        assert math.isclose(a.reference, b.reference, rel_tol=1e-12, abs_tol=1e-12)


def test_windowed_matches_manual_window_average():
    prices = [1, 2, 3, 4, 5]
    ticks = make_ticks(prices)
    k = 3
    strat = WindowedMovingAverageStrategy(window_size=k)

    sigs = signals_only(strat, ticks)

    window = []
    for i, sig in enumerate(sigs):
        window.append(prices[i])
        if len(window) > k:
            window.pop(0)
        expected_avg = sum(window) / len(window)
        assert math.isclose(sig.reference, expected_avg, rel_tol=1e-12, abs_tol=1e-12)
