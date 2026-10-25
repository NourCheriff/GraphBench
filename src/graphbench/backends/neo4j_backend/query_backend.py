from pathlib import Path

from neo4j import RoutingControl

from ...query import Query, QueryName
from ..base import QueryBackend
from .connector import Neo4jClient

_QUERIES_DIR = Path(__file__).resolve().parents[4] / "queries" / "cypher"


class Neo4jQueryBackend(QueryBackend):
    name = "neo4j"

    def __init__(
        self, client: Neo4jClient, database: str, queries_dir: Path = _QUERIES_DIR
    ):
        self._client = client
        self._database = database
        self._dir = queries_dir

    def _path(self, name: QueryName) -> Path:
        """Each QueryName entry has it's cypher file named as <name>.cypher"""
        return self._dir / f"{name}.cypher"

    def list_queries(self) -> list[Query]:
        return [Query(name, self.load_query(name)) for name in QueryName]

    def load_query(self, name: QueryName) -> str:
        path = self._path(name)

        if not path.is_file():
            raise FileNotFoundError(f"missing query file: {path}")

        return path.read_text(encoding="utf-8").strip()

    def execute(self, query: Query) -> list[dict]:
        records, _, _ = self._client.driver.execute_query(
            query.text, database_=self._database, routing_=RoutingControl.READ
        )

        return [record.data() for record in records]
