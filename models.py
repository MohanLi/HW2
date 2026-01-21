"""
models.py

Core immutable data structures and interfaces.

Key idea:
- MarketDataPoint is immutable (frozen dataclass) so ticks are safe to share and reason about.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from abc import ABC, abstractmethod
from typing import List, Optional


@dataclass(frozen=True, slots=True)
class MarketDataPoint:
    """
    Immutable market tick.

    Space per tick is O(1), but storing N ticks in a Python list is O(N) total space.
    """
    timestamp: datetime
    symbol: str
    price: float


@dataclass(frozen=True, slots=True)
class Signal:
    """
    A simple trading signal emitted per tick.
    """
    timestamp: datetime
    symbol: str
    action: str  # "BUY" | "SELL" | "HOLD"
    price: float
    reference: float  # e.g., moving average used


class Strategy(ABC):
    """
    Strategy interface.

    generate_signals is called once per tick (streaming style).
    Implementations should be careful about time/space complexity.
    """

    @abstractmethod
    def generate_signals(self, tick: MarketDataPoint) -> List[Signal]:
        raise NotImplementedError

    def reset(self) -> None:
        """
        Reset internal state between runs (benchmarks/tests).
        """
        return

    @property
    def name(self) -> str:
        return self.__class__.__name__
