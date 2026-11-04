from pathlib import Path

from ...query import Query
from ...rdf_utils import decode
from ...settings import SPARQL_QUERIES_DIR
from ..base import QueryBackend, Row
from .connector import GraphDBClient


class RDFBackend(QueryBackend):
    name = "graphdb"
    extension = "rq"

    def __init__(self, client: GraphDBClient, queries_dir: Path = SPARQL_QUERIES_DIR):
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
