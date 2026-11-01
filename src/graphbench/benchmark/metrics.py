from __future__ import annotations

import statistics
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Literal

type Stage = Literal["read", "convert", "load"]
type Target = Literal["ocel", "rdf", "lpg", "graphdb", "neo4j"]


@dataclass(kw_only=True)
class Timing:
    times_ms: list[float] = field(default_factory=list)
    error: str | None = None

    def labels(self) -> dict[str, object]:
        """Identifying columns for CSV output, overridden by subclasses."""
        raise NotImplementedError

    def stats(self) -> dict[str, float]:
        t = self.times_ms
        if not t:
            return {}
        return {
            "min_ms": min(t),
            "max_ms": max(t),
            "median_ms": statistics.median(t),
            "mean_ms": statistics.mean(t),
            "stdev_ms": statistics.stdev(t) if len(t) > 1 else 0.0,
        }


@dataclass(kw_only=True)
class QueryTiming(Timing):
    backend: str
    query: str
    rows: int | None = None

    def labels(self) -> dict[str, object]:
        return {"backend": self.backend, "query": self.query, "rows": self.rows}


@dataclass(kw_only=True)
class StageTiming(Timing):
    stage: Stage
    target: Target

    def labels(self) -> dict[str, object]:
        return {"stage": self.stage, "target": self.target}


def repeat(
    action: Callable[[], object],
    runs: int,
    setup: Callable[[], object] | None = None,
) -> list[float]:
    """Repeat the `action` `runs` times, `setup` will run before each `action` and is not timed"""
    times = []
    for _ in range(runs):
        if setup is not None:
            setup()
        start = time.perf_counter()
        action()
        times.append((time.perf_counter() - start) * 1000)
    return times
