from pathlib import Path

from ...query import Query
from ...rdf_utils import decode
from ..base import QueryBackend, Row
from .connector import GraphDBClient

_QUERIES_DIR = Path(__file__).resolve().parents[4] / "queries" / "sparql"


class RDFBackend(QueryBackend):
    name = "graphdb"
    extension = "sparql"

    def __init__(self, client: GraphDBClient, queries_dir: Path = _QUERIES_DIR):
        super().__init__(queries_dir)
        self._client = client

    @staticmethod
    def _to_rows(result: dict) -> list[Row]:
        variables = result["head"].get("vars", [])
        rows = []

        for binding in result["results"]["bindings"]:
            row: Row = dict.fromkeys(variables)
            for variable, cell in binding.items():
                value = cell["value"]
                row[variable] = decode(value) if cell["type"] == "uri" else value
            rows.append(row)

        return rows

    def execute(self, query: Query) -> list[dict]:
        return self._to_rows(self._client.query(query.text))
