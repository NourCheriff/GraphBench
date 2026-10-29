from pathlib import Path

from neo4j import RoutingControl

from ...query import Query
from ..base import QueryBackend, Row
from .connector import Neo4jClient

_QUERIES_DIR = Path(__file__).resolve().parents[4] / "queries" / "cypher"


class Neo4jQueryBackend(QueryBackend):
    name = "neo4j"
    extension = "cypher"

    def __init__(
        self, client: Neo4jClient, database: str, queries_dir: Path = _QUERIES_DIR
    ):
        super().__init__(queries_dir)
        self._client = client
        self._database = database

    def execute(self, query: Query) -> list[Row]:
        records, _, _ = self._client.driver.execute_query(
            query.text, database_=self._database, routing_=RoutingControl.READ
        )

        return [record.data() for record in records]
