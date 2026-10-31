from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from .metrics import Timing

REPO_ROOT = Path(__file__).resolve().parents[3]
RESULTS_DIR = REPO_ROOT / "output" / "benchmark"
STAT_COLUMNS = ["min_ms", "median_ms", "mean_ms", "max_ms", "stdev_ms"]


def create_run_dir(base: Path = RESULTS_DIR) -> Path:
    run_dir = base / datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def save_timings(results: list[Timing], run_dir: Path, name: str) -> tuple[Path, Path]:
    if not results:
        raise ValueError(f"no results to save for {name!r}")

    labels = list(results[0].labels().keys())
    summary_path = run_dir / f"{name}_summary.csv"
    runs_path = run_dir / f"{name}_runs.csv"

    with summary_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[*labels, "runs", *STAT_COLUMNS, "error"])
        writer.writeheader()
        for r in results:
            row = {
                **r.labels(),
                "runs": len(r.times_ms),
                "error": r.error or "",
            }
            row.update({k: round(v, 3) for k, v in r.stats().items()})
            writer.writerow(row)

    with runs_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[*labels, "run", "time_ms"])
        writer.writeheader()

        for r in results:
            for run, t in enumerate(r.times_ms, start=1):
                writer.writerow({**r.labels(), "run": run, "time_ms": round(t, 3)})

    return summary_path, runs_path
