from __future__ import annotations
from dataclasses import dataclass, field

import statistics

@dataclass
class QueryTiming:
    backend: str
    query: str
    times_ms: list[float] = field(default_factory=list)
    rows: int | None = None
    error: str | None = None

    def stats(self) -> dict[str, float]:
        t = self.times_ms
        if not t:
            return {}
        return {
            "min_ms": min(t),
            "median_ms": statistics.median(t),
            "mean_ms": statistics.mean(t),
            "max_ms": max(t),
            "stdev_ms": statistics.stdev(t) if len(t) > 1 else 0.0,
        }