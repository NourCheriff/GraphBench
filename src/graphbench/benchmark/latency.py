from __future__ import annotations

import gc
import logging
import random

from ..analysis.parameters import load_parameters
from ..backends.base import QueryBackend
from ..backends.neo4j_backend.connector import Neo4jClient
from ..backends.neo4j_backend.query_backend import Neo4jQueryBackend
from ..backends.rdf_backend.connector import GraphDBClient
from ..backends.rdf_backend.query_backend import RDFBackend
from ..query import PARAMETERS, Query, QueryName
from ..settings import NEO4J_DATABASE, QUERY_RUNS, QUERY_SEED, QUERY_WARMUP_RUNS
from .metrics import QueryTiming, repeat

logger = logging.getLogger(__name__)


def _cases(backend: QueryBackend, name: QueryName, ids: list[str]) -> list[Query]:
    text = backend.load_query(name)

    if name not in PARAMETERS:
        return [Query(name, text)]

    if not ids:
        raise ValueError(f"no IDs for {name} in the parameters file")

    return [Query(name, text, {PARAMETERS[name]: id_}) for id_ in ids]


def _run(
    backend: QueryBackend,
    name: QueryName,
    ids: list[str],
    timing: QueryTiming,
    timed: bool,
) -> None:
    if timing.error is not None:
        return

    try:
        rows = 0
        for query in _cases(backend, name, ids):
            if timed:
                timing.times_ms += repeat(
                    lambda q=query: backend.execute(q), 1, setup=gc.collect
                )
            else:
                rows += len(backend.execute(query))
        if not timed:
            timing.rows = rows
    except Exception as exc:
        timing.error = f"{type(exc).__name__}: {exc}"
        logger.error("%s %s failed: %s", backend.name, timing.query, timing.error)


def run_latency(
    warmup: int = QUERY_WARMUP_RUNS, runs: int = QUERY_RUNS, seed: int = QUERY_SEED
) -> list[QueryTiming]:
    rng = random.Random(seed)
    parameters = load_parameters()

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
                    ids = parameters.get(name, [])
                    _run(backend, name, ids, timings[backend.name, name], False)

        for i in range(runs):
            logger.info("query measured pass %d/%d", i + 1, runs)
            names = list(QueryName)
            rng.shuffle(names)
            order = backends if i % 2 == 0 else backends[::-1]
            for name in names:
                for backend in order:
                    ids = parameters.get(name, [])
                    _run(backend, name, ids, timings[backend.name, name], True)

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
