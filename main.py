"""
main.py

Orchestrates:
- CSV ingestion
- Benchmarking
- Plotting
- Report generation

Usage:
  python -m venv .venv
  source .venv/bin/activate  (or Windows: .venv\\Scripts\\activate)
  pip install -r requirements.txt  (optional; see README)
  python main.py --csv market_data.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

from data_loader import load_market_data, estimate_dataset_space_complexity
from profiler import benchmark_strategies
from reporting import plot_runtime, plot_memory, write_report
from strategies import (
    NaiveMovingAverageStrategy,
    OptimizedCumulativeAverageStrategy,
    WindowedMovingAverageStrategy,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Financial signal processing: runtime & space complexity comparison.")
    p.add_argument("--csv", type=str, default="market_data.csv", help="Path to market_data.csv")
    p.add_argument("--window", type=int, default=50, help="Window size for WindowedMovingAverageStrategy")
    p.add_argument("--repeats", type=int, default=3, help="timeit repeats")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    ticks = load_market_data(args.csv)

    print(f"Loaded {len(ticks):,} ticks from {args.csv}")
    print()
    print("Space complexity analysis:")
    print(estimate_dataset_space_complexity(len(ticks)))
    print()

    strategies = [
        NaiveMovingAverageStrategy(),
        OptimizedCumulativeAverageStrategy(),
        WindowedMovingAverageStrategy(window_size=args.window),
    ]

    results = benchmark_strategies(
        strategies=strategies,
        ticks=ticks,
        sizes=[1_000, 10_000, 100_000],
        repeats=args.repeats,
        cprofile_on_size=100_000,
        cprofile_dir="profiles",
    )

    runtime_png = plot_runtime(results, out_path="runtime_plot.png")
    memory_png = plot_memory(results, out_path="memory_plot.png")
    report_md = write_report(
        results,
        out_md="complexity_report.md",
        runtime_plot_path=runtime_png,
        memory_plot_path=memory_png,
    )

    print("Generated artifacts:")
    print(f"- {runtime_png}")
    print(f"- {memory_png}")
    print(f"- {report_md}")
    print(f"- profiles/ (cProfile outputs)")


if __name__ == "__main__":
    main()
