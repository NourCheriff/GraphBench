from __future__ import annotations

import gc
import logging
from collections.abc import Callable
from pathlib import Path

from ..backends.neo4j_backend import importer as neo4j_importer
from ..backends.neo4j_backend.connector import Neo4jClient
from ..backends.rdf_backend import importer as graphdb_importer
from ..converters import ocel_to_rdf
from ..converters.neo4j import converter as lpg_converter
from ..converters.ocel_to_rdf import DATASET_PATH
from ..datareader.reader import DataReader
from .metrics import Stage, StageTiming, Target, repeat

logger = logging.getLogger(__name__)


def _measure(
    stage: Stage,
    target: Target,
    action: Callable[[], object],
    runs: int,
    reset: Callable[[], object] | None = None,
) -> StageTiming:
    """Time `action` `runs` times; `reset` and `gc.collect` run untimed before each run."""

    run = 0

    def setup() -> None:
        nonlocal run
        run += 1
        if reset is not None:
            reset()
        gc.collect()
        logger.info("%s %s: run %d/%d", stage, target, run, runs)

    timing = StageTiming(stage=stage, target=target)
    try:
        timing.times_ms = repeat(action, runs, setup=setup)
    except Exception as exc:
        timing.error = f"{type(exc).__name__}: {exc}"
        logger.error("%s %s failed: %s", stage, target, timing.error)
    else:
        logger.info("%s %s: median %.0f ms", stage, target, timing.stats()["median_ms"])
    return timing


def run_conversion(runs: int = 5, dataset: Path = DATASET_PATH) -> list[StageTiming]:
    reader = DataReader()
    log = reader.read(dataset)

    return [
        _measure("read", "ocel", lambda: reader.read(dataset), runs),
        _measure("convert", "rdf", lambda: ocel_to_rdf.convert(log), runs),
        _measure("convert", "lpg", lambda: lpg_converter.convert(log, "jsonl"), runs),
    ]


def run_loading(runs: int = 1) -> list[StageTiming]:
    graphdb_importer.ensure_repository()

    with Neo4jClient() as client:
        return [
            _measure(
                "load",
                "graphdb",
                graphdb_importer.load_repository,
                runs,
                reset=graphdb_importer.clear_repository,
            ),
            _measure(
                "load",
                "neo4j",
                lambda: neo4j_importer.load_database(client),
                runs,
                reset=lambda: neo4j_importer.wipe_database(client),
            ),
        ]
