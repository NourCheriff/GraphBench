from __future__ import annotations

import csv
import logging
import math
import statistics
import sys
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import NullFormatter

from ..settings import PLOTS_DIR_NAME, RESULTS_DIR

logger = logging.getLogger(__name__)

BACKENDS = ["neo4j", "graphdb"]
LABELS = {"neo4j": "Neo4j", "graphdb": "GraphDB"}
COLORS = {"neo4j": "#2a78d6", "graphdb": "#eb6834"}
TEXT = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
GRID = "#e5e4e0"

SYSTEM = {"rdf": "graphdb", "lpg": "neo4j", "graphdb": "graphdb", "neo4j": "neo4j"}

MIB = 1024**2


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _grouped_bars(
    ax,
    groups: list[str],
    values: dict[str, list[float]],
    errors: dict[str, list] | None = None,
    label: Callable[[float], str] | None = None,
    horizontal: bool = False,
) -> None:
    width = 0.34
    positions = range(len(groups))

    for i, backend in enumerate(BACKENDS):
        offset = (i - 0.5) * (width + 0.03)
        at = [p + offset for p in positions]
        common = {
            "color": COLORS[backend],
            "label": LABELS[backend],
            "zorder": 2,
            "error_kw": {"ecolor": TEXT_SECONDARY, "elinewidth": 1, "capsize": 2.5},
        }
        err = errors[backend] if errors else None
        if horizontal:
            bars = ax.barh(at, values[backend], height=width, xerr=err, **common)
        else:
            bars = ax.bar(at, values[backend], width=width, yerr=err, **common)

        if label is None:
            continue
        for j, (bar, value) in enumerate(zip(bars, values[backend])):
            if math.isnan(value):
                continue

            tip = value + (err[j] if err is not None else 0)
            ax.annotate(
                label(value),
                (bar.get_x() + bar.get_width() / 2, tip),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8,
                color=TEXT,
            )

    if horizontal:
        ax.set_yticks(list(positions), groups)
        ax.invert_yaxis()
    else:
        ax.set_xticks(list(positions), groups)


def _style(ax, title: str, subtitle: str, value_axis: str) -> None:
    ax.set_title(title, loc="left", fontsize=12, color=TEXT, pad=22)
    ax.text(0, 1.02, subtitle, transform=ax.transAxes, fontsize=9, color=TEXT_SECONDARY)
    ax.grid(axis="x" if value_axis == "x" else "y", color=GRID, linewidth=1, zorder=0)

    for side in ("top", "right"):
        ax.spines[side].set_visible(False)

    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)

    ax.tick_params(colors=TEXT_SECONDARY, labelsize=9)
    ax.legend(frameon=False, fontsize=9, labelcolor=TEXT)


def _save(fig, path: Path) -> Path:
    fig.tight_layout()
    fig.savefig(path, dpi=200)

    plt.close(fig)

    logger.info("Saved %s", path)
    return path


def plot_pipeline(run_dir: Path, out_dir: Path) -> Path:
    rows = _read_csv(run_dir / "pipeline_summary.csv")
    stages = {"convert": "Conversion", "load": "Loading"}

    values = {b: [math.nan] * len(stages) for b in BACKENDS}
    errors = {b: [0.0] * len(stages) for b in BACKENDS}
    runs: dict[str, str] = {}

    for row in rows:
        if row["error"] or not row["mean_ms"]:
            continue

        if row["stage"] == "read":
            continue

        i = list(stages).index(row["stage"])
        backend = SYSTEM[row["target"]]
        values[backend][i] = float(row["mean_ms"]) / 1000
        errors[backend][i] = float(row["stdev_ms"]) / 1000
        runs[row["stage"]] = row["runs"]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    _grouped_bars(
        ax, list(stages.values()), values, errors, label=lambda v: f"{v:.2f} s"
    )

    ax.set_ylabel("Time (s)", color=TEXT_SECONDARY)
    _style(
        ax,
        "Conversion and loading time",
        f"Mean ± std. dev. · conversion: {runs.get('convert', '?')} runs, "
        f"loading: {runs.get('load', '?')} runs",
        value_axis="y",
    )

    return _save(fig, out_dir / "pipeline.png")


def plot_storage(run_dir: Path, out_dir: Path) -> Path:
    rows = _read_csv(run_dir / "storage.csv")

    components = {
        "heap": "Heap",
        "store": "Store on disk",
        "transaction_logs": "Transaction logs\n(Neo4j only)",
    }

    values = {b: [math.nan] * len(components) for b in BACKENDS}
    for row in rows:
        i = list(components).index(row["component"])
        values[row["backend"]][i] = int(row["bytes"]) / MIB

    fig, ax = plt.subplots(figsize=(7, 4.5))
    _grouped_bars(ax, list(components.values()), values, label=lambda v: f"{v:.1f}")
    ax.set_ylabel("Size (MiB)", color=TEXT_SECONDARY)
    _style(
        ax,
        "Memory and disk usage",
        "",
        value_axis="y",
    )

    return _save(fig, out_dir / "storage.png")


def plot_query_latency(run_dir: Path, out_dir: Path) -> Path:
    times: dict[tuple[str, str], list[float]] = defaultdict(list)

    for row in _read_csv(run_dir / "query_latency_runs.csv"):
        times[row["backend"], row["query"]].append(float(row["time_ms"]))

    queries = sorted({query for _, query in times})
    groups = [f"Q{q[:2]} {q[3:].replace('_', ' ')}" for q in queries]

    values = {b: [] for b in BACKENDS}
    errors = {b: [[], []] for b in BACKENDS}  # [below median, above median]
    runs = set()
    for backend in BACKENDS:
        for query in queries:
            t = times.get((backend, query), [])
            if len(t) < 2:
                values[backend].append(math.nan)
                errors[backend][0].append(0)
                errors[backend][1].append(0)
                continue
            q1, median, q3 = statistics.quantiles(t, n=4)
            values[backend].append(median)
            errors[backend][0].append(median - q1)
            errors[backend][1].append(q3 - median)
            runs.add(len(t))

    fig, ax = plt.subplots(figsize=(8, 7))
    _grouped_bars(ax, groups, values, errors, horizontal=True)
    ax.set_xscale("log")

    ticks = (1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000)
    low, high = ax.get_xlim()
    ax.set_xticks(
        [t for t in ticks if low <= t <= high],
        [str(t) for t in ticks if low <= t <= high],
    )
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xlabel("Latency (ms, log scale)", color=TEXT_SECONDARY)
    _style(
        ax,
        "Query latency",
        f"{'/'.join(map(str, sorted(runs)))} measured runs per query",
        value_axis="x",
    )

    return _save(fig, out_dir / "query_latency.png")


def plot_run(run_dir: Path) -> list[Path]:
    out_dir = run_dir / PLOTS_DIR_NAME
    out_dir.mkdir(exist_ok=True)

    plots = [
        ("pipeline_summary.csv", plot_pipeline),
        ("storage.csv", plot_storage),
        ("query_latency_runs.csv", plot_query_latency),
    ]
    return [plot(run_dir, out_dir) for name, plot in plots if (run_dir / name).exists()]


def latest_run(base: Path = RESULTS_DIR) -> Path:
    runs = sorted(d for d in base.iterdir() if d.is_dir() and any(d.glob("*.csv")))
    if not runs:
        raise FileNotFoundError(f"no benchmark runs in {base}")
    return runs[-1]


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    run_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else latest_run()
    plot_run(run_dir)


if __name__ == "__main__":
    main()
