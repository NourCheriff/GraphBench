from __future__ import annotations

import logging
import re
import subprocess
import time

from ..backends.neo4j_backend.connector import Neo4jClient
from ..settings import (
    GRAPHDB_CONTAINER,
    GRAPHDB_JVM_MAIN_CLASS,
    GRAPHDB_STORE_DIR,
    NEO4J_CONTAINER,
    NEO4J_JVM_MAIN_CLASS,
    NEO4J_STOP_TIMEOUT,
    NEO4J_STORE_DIR,
    NEO4J_TRANSACTION_LOGS_DIR,
)
from .metrics import StorageMeasurement

logger = logging.getLogger(__name__)


JVMS = {
    "graphdb": (GRAPHDB_CONTAINER, GRAPHDB_JVM_MAIN_CLASS),
    "neo4j": (NEO4J_CONTAINER, NEO4J_JVM_MAIN_CLASS),
}

DISK_PATHS = [
    ("graphdb", "store", GRAPHDB_CONTAINER, GRAPHDB_STORE_DIR),
    ("neo4j", "store", NEO4J_CONTAINER, NEO4J_STORE_DIR),
    ("neo4j", "transaction_logs", NEO4J_CONTAINER, NEO4J_TRANSACTION_LOGS_DIR),
]


def _docker(*args: str) -> str:
    result = subprocess.run(
        ["docker", *args], capture_output=True, text=True, check=True
    )
    return result.stdout


def heap_used(container: str, main_class: str) -> int:
    """NOTE: The result is in bytes"""
    _docker("exec", container, "jcmd", main_class, "GC.run")
    info = _docker("exec", container, "jcmd", main_class, "GC.heap_info")
    return int(re.search(r"used (\d+)K", info).group(1)) * 1024


def disk_usage(container: str, path: str) -> int:
    """Size in bytes of `path` inside `container`."""
    return int(_docker("exec", container, "du", "-sb", path).split()[0])


def restart_neo4j() -> None:
    """Required to execute a checkpoint on Neo4j Community Edition"""
    _docker("restart", "--time", str(NEO4J_STOP_TIMEOUT), NEO4J_CONTAINER)

    for _ in range(60):
        try:
            with Neo4jClient():
                return
        except ConnectionError:
            time.sleep(1)
    raise TimeoutError("Neo4j did not come back after restart")


def measure_storage() -> list[StorageMeasurement]:
    """Live heap and disk size of each database, measured once after loading."""
    rows = [
        StorageMeasurement(
            backend=backend, component="heap", bytes=heap_used(container, main_class)
        )
        for backend, (container, main_class) in JVMS.items()
    ]

    restart_neo4j()

    rows += [
        StorageMeasurement(
            backend=backend, component=component, bytes=disk_usage(container, path)
        )
        for backend, component, container, path in DISK_PATHS
    ]

    for row in rows:
        logger.info("%s %s: %.1f MiB", row.backend, row.component, row.bytes / 1024**2)
    return rows
