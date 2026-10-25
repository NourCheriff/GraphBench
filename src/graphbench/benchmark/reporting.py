from __future__ import annotations
from datetime import datetime
from pathlib import Path
from .metrics import QueryTiming

import csv

REPO_ROOT = Path(__file__).resolve().parents[3]
RESULTS_DIR = REPO_ROOT / "output" / "benchmark"
STAT_COLUMNS = ["min_ms", "median_ms", "mean_ms", "max_ms", "stdev_ms"]

def save_results(results: list[QueryTiming], directory: Path = RESULTS_DIR) -> tuple[Path, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    summary_path = directory / f"benchmark_summary_{stamp}.csv"
    raw_path = directory / f"benchmark_runs_{stamp}.csv"

    with summary_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["backend", "query", "rows", "runs", *STAT_COLUMNS, "error"])
        writer.writeheader()
        for r in results:
            row = {"backend": r.backend, "query": r.query, "rows": r.rows,
                   "runs": len(r.times_ms), "error": r.error or ""}
            row.update({k: round(v, 3) for k, v in r.stats().items()})
            writer.writerow(row)

    with raw_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["backend", "query", "run", "time_ms"])
        for r in results:
            for run, t in enumerate(r.times_ms, start=1):
                writer.writerow([r.backend, r.query, run, round(t, 3)])

    return summary_path, raw_path