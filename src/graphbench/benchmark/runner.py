import logging
import time
from collections.abc import Iterable
from dataclasses import dataclass, field

from ..backends.base import QueryBackend, Row
from ..query import Query, QueryName

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class QueryResult:
    backend: str
    query: QueryName
    rows: list[Row] = field(default_factory=list)
    elapsed: float = 0.0
    error: Exception | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


def run_query(backend: QueryBackend, name: QueryName) -> QueryResult:

    try:
        query = Query(name, backend.load_query(name))
        start = time.perf_counter()
        rows = backend.execute(query)
    except Exception as e:
        elapsed = time.perf_counter() - start
        log.exception("%s / %s failed", backend.name, name)
        return QueryResult(backend.name, name, elapsed=elapsed, error=e)

    elapsed = time.perf_counter() - start
    log.info("%s / %s: %d rows in %.3fs", backend.name, name, len(rows), elapsed)
    return QueryResult(backend.name, name, rows=rows, elapsed=elapsed)


def run_all(
    backends: Iterable[QueryBackend], names: Iterable[QueryName] = QueryName
) -> list[QueryResult]:
    names = list(names)
    return [run_query(backend, name) for backend in backends for name in names]
