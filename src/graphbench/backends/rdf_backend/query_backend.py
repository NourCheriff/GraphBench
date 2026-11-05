import re
from pathlib import Path

from ...converters.ocel_to_rdf import EVENT, OBJ
from ...query import Query
from ...rdf_utils import decode, iri
from ...settings import SPARQL_QUERIES_DIR
from ..base import QueryBackend, Row
from .connector import GraphDBClient

PARAMETER_NAMESPACE = {"order": OBJ, "event": EVENT, "customer": OBJ}


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
        return self._to_rows(self._client.query(self._fill(query)))

    @staticmethod
    def _fill(query: Query) -> str:
        text = query.text
        for name, id_ in query.params.items():
            value = iri(PARAMETER_NAMESPACE[name], id_).n3()
            text = re.sub(rf"\${name}\b", lambda _: value, text)
        return text
