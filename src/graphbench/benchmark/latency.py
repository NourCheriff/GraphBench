from __future__ import annotations

import gc
import logging

from ..backends.base import QueryBackend
from ..backends.neo4j_backend.connector import Neo4jClient
from ..backends.neo4j_backend.query_backend import Neo4jQueryBackend
from ..backends.rdf_backend.connector import GraphDBClient
from ..backends.rdf_backend.query_backend import RDFBackend
from ..query import Query, QueryName
from ..settings import NEO4J_DATABASE, QUERY_RUNS, QUERY_WARMUP_RUNS
from .metrics import QueryTiming, repeat

logger = logging.getLogger(__name__)


def measure_query(
    backend: QueryBackend, name: QueryName, warmup: int, runs: int
) -> QueryTiming:
    """`warmup` discarded runs, then `runs` timed runs of the same query."""
    timing = QueryTiming(backend=backend.name, query=name.value)
    try:
        query = Query(name, backend.load_query(name))

        for _ in range(warmup):
            # row count: a check that both backends return the same result size
            timing.rows = len(backend.execute(query))

        timing.times_ms = repeat(lambda: backend.execute(query), runs, setup=gc.collect)
    except Exception as exc:
        timing.error = f"{type(exc).__name__}: {exc}"
        logger.error("%s %s failed: %s", backend.name, name, timing.error)
    else:
        logger.info(
            "%s %s: %s rows, median %.1f ms",
            backend.name,
            name,
            timing.rows,
            timing.stats()["median_ms"],
        )
    return timing


def run_latency(
    warmup: int = QUERY_WARMUP_RUNS, runs: int = QUERY_RUNS
) -> list[QueryTiming]:
    """Every query on both backends."""
    with Neo4jClient() as neo4j_client, GraphDBClient() as graphdb_client:
        backends: list[QueryBackend] = [
            Neo4jQueryBackend(client=neo4j_client, database=NEO4J_DATABASE),
            RDFBackend(client=graphdb_client),
        ]
        return [
            measure_query(backend, name, warmup, runs)
            for backend in backends
            for name in QueryName
        ]
