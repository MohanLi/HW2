# HW2 – Runtime & Space Complexity in Financial Signal Processing

This project analyzes the runtime and space complexity of moving average–based trading strategies using Python.

It compares:
- A naive full-history moving average
- An optimized cumulative moving average
- A fixed-size windowed moving average

The goal is to demonstrate how algorithmic design choices affect performance at scale.

---

## Project Structure

```text
hw2/
├── data_loader.py
├── models.py
├── strategies.py
├── profiler.py
├── reporting.py
├── main.py
├── market_data.csv
├── runtime_plot.png
├── memory_plot.png
├── complexity_report.md
├── tests/
└── profiles/
