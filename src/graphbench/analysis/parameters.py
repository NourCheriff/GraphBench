from __future__ import annotations

import json
import logging
from collections import Counter
from pathlib import Path

from ..datareader.models import OCELLog
from ..datareader.reader import DataReader
from ..query import QueryName
from ..settings import DATASET_PATH, QUERY_PARAMETER_COUNT, QUERY_PARAMETERS_PATH

logger = logging.getLogger(__name__)


def order_events(log: OCELLog) -> dict[str, int]:
    degree = Counter(
        rel.target_id for rel in log.e2o if log.objects[rel.target_id].type == "orders"
    )
    return dict(degree)


def event_objects(log: OCELLog) -> dict[str, int]:
    objects: dict[str, set[str]] = {event_id: set() for event_id in log.events}
    for rel in log.e2o:
        objects[rel.source_id].add(rel.target_id)
    return {event_id: len(ids) for event_id, ids in objects.items()}


def customer_rows(log: OCELLog) -> dict[str, int]:
    items = Counter(rel.source_id for rel in log.o2o if rel.qualifier == "comprises")
    degree = Counter()
    for rel in log.o2o:
        if rel.qualifier == "places":
            degree[rel.source_id] += items[rel.target_id]
    return dict(degree)


DEGREES = {
    QueryName.Q01_ORDER_EVENT_SEQUENCE: order_events,
    QueryName.Q02_EVENT_OBJECTS: event_objects,
    QueryName.Q03_CUSTOMER_ORDERS: customer_rows,
}


def spread(degrees: dict[str, int], count: int) -> list[tuple[str, int]]:
    low, high = min(degrees.values()), max(degrees.values())
    candidates = sorted(degrees)
    chosen: list[tuple[str, int]] = []

    for i in range(count):
        target = low + (high - low) * i / (count - 1)
        best = min(candidates, key=lambda id_: abs(degrees[id_] - target))
        candidates.remove(best)
        chosen.append((best, degrees[best]))

    return chosen


def select_parameters(
    log: OCELLog, count: int = QUERY_PARAMETER_COUNT
) -> dict[str, list[dict[str, object]]]:
    return {
        name.value: [{"id": id_, "degree": d} for id_, d in spread(degree(log), count)]
        for name, degree in DEGREES.items()
    }


def load_parameters(path: Path = QUERY_PARAMETERS_PATH) -> dict[QueryName, list[str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {QueryName(name): [p["id"] for p in params] for name, params in data.items()}


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    parameters = select_parameters(DataReader().read(DATASET_PATH))
    QUERY_PARAMETERS_PATH.write_text(
        json.dumps(parameters, indent=2) + "\n", encoding="utf-8"
    )

    for name, params in parameters.items():
        logger.info("%s: %s", name, [p["degree"] for p in params])
    logger.info("Saved %s", QUERY_PARAMETERS_PATH)


if __name__ == "__main__":
    main()
