"""
profiler.py

Benchmark strategies using:
- timeit (wall-clock timing)
- cProfile (function-level profiling)
- memory_profiler (peak RSS-like sampling) if available; otherwise tracemalloc fallback

Bench sizes: 1k, 10k, 100k ticks.

We aim for production-quality, repeatable benchmarks:
- Ensure strategy.reset() between runs
- Use the same input slices for all strategies
"""

from __future__ import annotations

import io
import os
import timeit
import cProfile
import pstats
import tracemalloc
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Tuple

from models import MarketDataPoint, Strategy

try:
    # external dependency; install via: pip install memory-profiler
    from memory_profiler import memory_usage  # type: ignore
    _HAS_MEMORY_PROFILER = True
except Exception:
    memory_usage = None
    _HAS_MEMORY_PROFILER = False


@dataclass(frozen=True)
class BenchmarkResult:
    strategy_name: str
    n_ticks: int
    time_seconds: float
    peak_memory_mb: float


def run_strategy(strategy: Strategy, ticks: List[MarketDataPoint]) -> int:
    """
    Run strategy over ticks, return total signals emitted (for sanity).
    """
    strategy.reset()
    total = 0
    for t in ticks:
        total += len(strategy.generate_signals(t))
    return total


def time_run(strategy: Strategy, ticks: List[MarketDataPoint], repeats: int = 3) -> float:
    """
    Use timeit for timing.

    We time the whole run_strategy call.
    """
    def _call() -> None:
        run_strategy(strategy, ticks)

    # timeit repeats; take best to reduce noise from background load
    timings = timeit.repeat(_call, number=1, repeat=repeats)
    return min(timings)


def peak_memory_run_mb(strategy: Strategy, ticks: List[MarketDataPoint]) -> float:
    """
    Peak memory in MB.

    Preferred: memory_profiler.memory_usage(..., max_usage=True)
    Fallback: tracemalloc peak tracked Python allocations (not full RSS, but stable for tests).
    """
    if _HAS_MEMORY_PROFILER and memory_usage is not None:
        # max_usage=True returns a single float (MiB) for peak usage during the function
        def _call() -> None:
            run_strategy(strategy, ticks)

        peak_mib = memory_usage((_call, tuple(), {}), max_usage=True, retval=False, interval=0.01)
        return float(peak_mib)

    # Fallback: tracemalloc
    tracemalloc.start()
    run_strategy(strategy, ticks)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    peak_mb = peak / (1024 * 1024)
    return float(peak_mb)


def cprofile_run(strategy: Strategy, ticks: List[MarketDataPoint], out_dir: str | Path, label: str) -> Tuple[Path, Path]:
    """
    Generate cProfile output for one run (typically on largest N).
    Produces:
      - .prof binary
      - .txt human-readable stats (sorted by cumulative time)
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    prof_path = out / f"{strategy.name}_{label}.prof"
    txt_path = out / f"{strategy.name}_{label}.txt"

    pr = cProfile.Profile()
    pr.enable()
    run_strategy(strategy, ticks)
    pr.disable()
    pr.dump_stats(str(prof_path))

    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
    ps.print_stats(40)
    txt_path.write_text(s.getvalue(), encoding="utf-8")

    return prof_path, txt_path


def benchmark_strategies(
    strategies: List[Strategy],
    ticks: List[MarketDataPoint],
    sizes: List[int] = [1_000, 10_000, 100_000],
    repeats: int = 3,
    cprofile_on_size: int = 100_000,
    cprofile_dir: str | Path = "profiles",
) -> List[BenchmarkResult]:
    """
    Run benchmarks for each strategy at each size.

    Returns a flat list of BenchmarkResult records.
    """
    results: List[BenchmarkResult] = []

    for n in sizes:
        subset = ticks[:n]
        if len(subset) < n:
            raise ValueError(f"Not enough ticks: requested {n}, have {len(ticks)}")

        for strat in strategies:
            t = time_run(strat, subset, repeats=repeats)
            m = peak_memory_run_mb(strat, subset)
            results.append(BenchmarkResult(strat.name, n, t, m))

            if n == cprofile_on_size:
                cprofile_run(strat, subset, out_dir=cprofile_dir, label=f"{n}")

    return results
