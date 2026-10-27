from __future__ import annotations

import re
from pathlib import Path

from ...query import Query, QueryName
from ...rdf_utils import decode
from .connector import GraphDBClient

REPO_ROOT = Path(__file__).resolve().parents[4]
QUERIES_DIR = REPO_ROOT / "queries" / "sparql"


def load_query(name: QueryName) -> Query:
    path = QUERIES_DIR / f"{name}.rq"
    if not path.exists():
        raise FileNotFoundError(f"SPARQL query {name!r} not found: {path}")
    return Query(name, path.read_text(encoding="utf-8"))


def to_rows(result: dict) -> list[dict[str, str]]:
    return [
        {
            variable: decode(cell["value"]) if cell["type"] == "uri" else cell["value"]
            for variable, cell in binding.items()
        }
        for binding in result["results"]["bindings"]
    ]


class RdfBackend:
    name = "graphdb"

    def __init__(self, client: GraphDBClient | None = None):
        self._client = client or GraphDBClient()

    def __enter__(self) -> RdfBackend:
        if hasattr(self._client, "connect"):
            self._client.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if hasattr(self._client, "close"):
            self._client.close()

    def load_query(self, name: QueryName) -> Query:
        return load_query(name)

    def execute(self, query: Query) -> list[dict[str, str]]:
        return to_rows(self._client.query(query.text))