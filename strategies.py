"""
strategies.py

Implements multiple moving-average-based trading strategies and clearly documents Big-O.

Signal rule (kept intentionally simple for clarity):
- Compute a moving average reference for the tick
- If price > avg: BUY
- If price < avg: SELL
- Else: HOLD

This yields deterministic behavior for unit tests and benchmarking.
"""

from __future__ import annotations

from collections import deque
from typing import Deque, List, Optional

from models import MarketDataPoint, Signal, Strategy


def _action(price: float, avg: float) -> str:
    if price > avg:
        return "BUY"
    if price < avg:
        return "SELL"
    return "HOLD"


class NaiveMovingAverageStrategy(Strategy):
    """
    Naive (full-history) average.

    For each tick, recompute the average from scratch over *all* historical prices.

    Let n be number of ticks seen so far:
    - Time per tick: O(n)   (sum over history each tick)
    - Total time over N ticks: O(N^2)
    - Space: O(n) (store full history prices)
    """

    def __init__(self) -> None:
        self._prices: List[float] = []
        self._last_symbol: Optional[str] = None

    def reset(self) -> None:
        self._prices.clear()
        self._last_symbol = None

    def generate_signals(self, tick: MarketDataPoint) -> List[Signal]:
        self._prices.append(tick.price)

        # O(n) time: sum over all prices so far
        avg = sum(self._prices) / len(self._prices)

        return [
            Signal(
                timestamp=tick.timestamp,
                symbol=tick.symbol,
                action=_action(tick.price, avg),
                price=tick.price,
                reference=avg,
            )
        ]


class OptimizedCumulativeAverageStrategy(Strategy):
    """
    Optimized refactor of the naive *full-history* average strategy.

    Instead of summing the full history every tick, maintain a running sum and count.

    Let n be number of ticks seen so far:
    - Time per tick: O(1)   (update running sum)
    - Total time over N ticks: O(N)
    - Space: O(1)           (no need to keep history for the average)
      (We only store sum and count.)

    This specifically addresses Requirement #5: refactor naive to reduce both time and space.
    """

    def __init__(self) -> None:
        self._sum: float = 0.0
        self._count: int = 0

    def reset(self) -> None:
        self._sum = 0.0
        self._count = 0

    def generate_signals(self, tick: MarketDataPoint) -> List[Signal]:
        self._sum += tick.price
        self._count += 1
        avg = self._sum / self._count

        return [
            Signal(
                timestamp=tick.timestamp,
                symbol=tick.symbol,
                action=_action(tick.price, avg),
                price=tick.price,
                reference=avg,
            )
        ]


class WindowedMovingAverageStrategy(Strategy):
    """
    Fixed-size sliding window average (last k ticks).

    Maintain:
    - a deque of up to k recent prices
    - a running sum of those prices

    Let k be window size:
    - Time per tick: O(1) amortized
      (append/pop in deque and constant arithmetic)
    - Space: O(k)
    """

    def __init__(self, window_size: int = 50) -> None:
        if window_size <= 0:
            raise ValueError("window_size must be positive")
        self.window_size = window_size
        self._window: Deque[float] = deque()
        self._sum: float = 0.0

    def reset(self) -> None:
        self._window.clear()
        self._sum = 0.0

    def generate_signals(self, tick: MarketDataPoint) -> List[Signal]:
        # O(1): push new
        self._window.append(tick.price)
        self._sum += tick.price

        # O(1): evict old if needed
        if len(self._window) > self.window_size:
            old = self._window.popleft()
            self._sum -= old

        # O(1): compute avg
        avg = self._sum / len(self._window)

        return [
            Signal(
                timestamp=tick.timestamp,
                symbol=tick.symbol,
                action=_action(tick.price, avg),
                price=tick.price,
                reference=avg,
            )
        ]
