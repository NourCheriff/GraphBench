from pathlib import Path

from neo4j import RoutingControl

from ...query import Query
from ...settings import CYPHER_QUERIES_DIR
from ..base import QueryBackend, Row
from .connector import Neo4jClient


class Neo4jQueryBackend(QueryBackend):
    name = "neo4j"
    extension = "cypher"

    def __init__(
        self, client: Neo4jClient, database: str, queries_dir: Path = CYPHER_QUERIES_DIR
    ):
        super().__init__(queries_dir)
        self._client = client
        self._database = database

    def execute(self, query: Query) -> list[Row]:
        records, _, _ = self._client.driver.execute_query(
            query.text,
            parameters_=query.params,
            database_=self._database,
            routing_=RoutingControl.READ,
        )

        return [record.data() for record in records]
