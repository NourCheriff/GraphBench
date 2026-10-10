from typing import Self

from neo4j import Driver, GraphDatabase

_URI = "neo4j://localhost:7687"
_AUTH = ("neo4j", "neo4j-pwd")


class Neo4jClient:
    def __init__(self, uri: str = _URI, auth: tuple[str, str] = _AUTH):
        self._uri = uri
        self._auth = auth
        self._driver: Driver | None = None

    def connect(self) -> None:
        if self._driver is not None:
            return

        driver = GraphDatabase.driver(
            self._uri,
            auth=self._auth,
        )

        try:
            driver.verify_connectivity()
            self._driver = driver
        except Exception as ex:
            driver.close()
            raise ConnectionError(
                f"Cannot connect to Neo4j instance on uri:{_URI}"
            ) from ex

    @property
    def driver(self) -> Driver:
        if self._driver is None:
            raise RuntimeError("Neo4j client is not connected. Call connect() first.")
        return self._driver

    def close(self) -> None:
        if self._driver is None:
            return

        self._driver.close()
        self._driver = None

    # __enter__ and __exit__ allows to use `with` keyword
    def __enter__(self) -> Self:
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()
