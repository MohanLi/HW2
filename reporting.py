"""
reporting.py

Generates:
- runtime_plot.png
- memory_plot.png
- complexity_report.md

The report includes:
- Tables of runtime/memory metrics
- Complexity annotations (Big-O)
- Plots
- Narrative comparing strategies and optimization impact
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt

from profiler import BenchmarkResult


COMPLEXITY_NOTES: Dict[str, str] = {
    "NaiveMovingAverageStrategy": "Per-tick time O(n), total O(N^2); space O(N) (stores full history).",
    "OptimizedCumulativeAverageStrategy": "Per-tick time O(1), total O(N); space O(1) (running sum + count).",
    "WindowedMovingAverageStrategy": "Per-tick time O(1) amortized, total O(N); space O(k) (deque window).",
}


def _group(results: List[BenchmarkResult]) -> Dict[str, Dict[int, BenchmarkResult]]:
    grouped: Dict[str, Dict[int, BenchmarkResult]] = {}
    for r in results:
        grouped.setdefault(r.strategy_name, {})[r.n_ticks] = r
    return grouped


def plot_runtime(results: List[BenchmarkResult], out_path: str | Path = "runtime_plot.png") -> Path:
    out = Path(out_path)
    grouped = _group(results)

    plt.figure()
    for strat, by_n in grouped.items():
        xs = sorted(by_n.keys())
        ys = [by_n[n].time_seconds for n in xs]
        plt.plot(xs, ys, marker="o", label=strat)
    plt.xlabel("Input size (ticks)")
    plt.ylabel("Runtime (seconds)")
    plt.title("Runtime vs Input Size")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out)
    plt.close()
    return out


def plot_memory(results: List[BenchmarkResult], out_path: str | Path = "memory_plot.png") -> Path:
    out = Path(out_path)
    grouped = _group(results)

    plt.figure()
    for strat, by_n in grouped.items():
        xs = sorted(by_n.keys())
        ys = [by_n[n].peak_memory_mb for n in xs]
        plt.plot(xs, ys, marker="o", label=strat)
    plt.xlabel("Input size (ticks)")
    plt.ylabel("Peak memory (MB)")
    plt.title("Memory vs Input Size")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out)
    plt.close()
    return out


def _markdown_table(results: List[BenchmarkResult]) -> str:
    """
    Table with rows: strategy x size
    """
    rows = sorted(results, key=lambda r: (r.strategy_name, r.n_ticks))
    lines = [
        "| Strategy | Ticks | Runtime (s) | Peak Memory (MB) |",
        "|---|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(f"| {r.strategy_name} | {r.n_ticks:,} | {r.time_seconds:.6f} | {r.peak_memory_mb:.2f} |")
    return "\n".join(lines)


def write_report(
    results: List[BenchmarkResult],
    out_md: str | Path = "complexity_report.md",
    runtime_plot_path: str | Path = "runtime_plot.png",
    memory_plot_path: str | Path = "memory_plot.png",
) -> Path:
    out = Path(out_md)

    runtime_img = Path(runtime_plot_path).name
    memory_img = Path(memory_plot_path).name

    strategy_names = sorted({r.strategy_name for r in results})
    notes = "\n".join([f"- **{name}**: {COMPLEXITY_NOTES.get(name, 'See code comments.')}" for name in strategy_names])

    # Pick a simple narrative based on the largest-N timing.
    largest_n = max(r.n_ticks for r in results)
    largest = [r for r in results if r.n_ticks == largest_n]
    largest_sorted = sorted(largest, key=lambda r: r.time_seconds)
    narrative = []
    narrative.append(f"For **{largest_n:,} ticks**, fastest → slowest (by runtime):")
    for r in largest_sorted:
        narrative.append(f"- {r.strategy_name}: {r.time_seconds:.6f}s, peak {r.peak_memory_mb:.2f}MB")
    narrative.append("")
    narrative.append(
        "The naive strategy recomputes a sum over the entire history every tick (quadratic total work), "
        "so it should scale much worse than the O(N) strategies as N grows."
    )
    narrative.append(
        "The optimized cumulative-average refactor reduces both time and space by tracking only a running sum and count "
        "(no full history list required). The windowed strategy bounds memory to O(k) by keeping only the last k prices."
    )

    md = f"""# Runtime & Space Complexity in Financial Signal Processing

## Overview
This project ingests market ticks from a CSV file and compares multiple moving-average trading strategies using:
- Theoretical Big-O analysis
- Empirical profiling (timeit, cProfile, memory_profiler)
- Scaling plots

## Complexity Annotations (Big-O)
{notes}

## Benchmark Results
{_markdown_table(results)}

## Plots
### Runtime vs Input Size
![Runtime vs Input Size]({runtime_img})

### Memory vs Input Size
![Memory vs Input Size]({memory_img})

## Narrative Comparison
{chr(10).join(narrative)}

## Notes on Measurement
- **Runtime** uses `timeit.repeat(..., number=1)` and reports the best of a few repeats to reduce noise.
- **Peak memory** uses `memory_profiler` when installed; otherwise falls back to `tracemalloc` (Python allocation peak).
- `cProfile` outputs are saved under the `profiles/` directory.
"""
    out.write_text(md, encoding="utf-8")
    return out
