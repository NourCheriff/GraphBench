import logging

from ..backends.neo4j_backend.connector import Neo4jClient
from ..backends.neo4j_backend.query_backend import Neo4jQueryBackend
from ..backends.rdf_backend.connector import GraphDBClient
from ..backends.rdf_backend.query_backend import RDFBackend
from .runner import run_all


def main():
    logging.basicConfig(level=logging.INFO)

    with Neo4jClient() as neo4j_client, GraphDBClient() as graphdb_client:
        backends = [
            Neo4jQueryBackend(client=neo4j_client, database="order-management"),
            RDFBackend(client=graphdb_client),
        ]

        run_all(backends)


if __name__ == "__main__":
    main()
