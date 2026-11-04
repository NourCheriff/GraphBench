from __future__ import annotations

import gc
import logging
import random

from ..backends.base import QueryBackend
from ..backends.neo4j_backend.connector import Neo4jClient
from ..backends.neo4j_backend.query_backend import Neo4jQueryBackend
from ..backends.rdf_backend.connector import GraphDBClient
from ..backends.rdf_backend.query_backend import RDFBackend
from ..query import Query, QueryName
from ..settings import NEO4J_DATABASE, QUERY_RUNS, QUERY_SEED, QUERY_WARMUP_RUNS
from .metrics import QueryTiming, repeat

logger = logging.getLogger(__name__)


def _run(
    backend: QueryBackend, name: QueryName, timing: QueryTiming, timed: bool
) -> None:
    if timing.error is not None:
        return

    try:
        query = Query(name, backend.load_query(name))

        if timed:
            timing.times_ms += repeat(
                lambda: backend.execute(query), 1, setup=gc.collect
            )
        else:
            timing.rows = len(backend.execute(query))
    except Exception as exc:
        timing.error = f"{type(exc).__name__}: {exc}"
        logger.error("%s %s failed: %s", backend.name, timing.query, timing.error)


def run_latency(
    warmup: int = QUERY_WARMUP_RUNS, runs: int = QUERY_RUNS, seed: int = QUERY_SEED
) -> list[QueryTiming]:
    rng = random.Random(seed)

    with Neo4jClient() as neo4j_client, GraphDBClient() as graphdb_client:
        backends: list[QueryBackend] = [
            Neo4jQueryBackend(client=neo4j_client, database=NEO4J_DATABASE),
            RDFBackend(client=graphdb_client),
        ]

        timings = {
            (backend.name, name): QueryTiming(backend=backend.name, query=name.value)
            for backend in backends
            for name in QueryName
        }

        for i in range(warmup):
            logger.info("query warm-up pass %d/%d", i + 1, warmup)
            for name in QueryName:
                for backend in backends:
                    _run(backend, name, timings[backend.name, name], timed=False)

        for i in range(runs):
            logger.info("query measured pass %d/%d", i + 1, runs)
            names = list(QueryName)
            rng.shuffle(names)
            order = backends if i % 2 == 0 else backends[::-1]
            for name in names:
                for backend in order:
                    _run(backend, name, timings[backend.name, name], timed=True)

    for timing in timings.values():
        if timing.error is None:
            logger.info(
                "%s %s: %s rows, median %.1f ms",
                timing.backend,
                timing.query,
                timing.rows,
                timing.stats()["median_ms"],
            )

    return list(timings.values())
