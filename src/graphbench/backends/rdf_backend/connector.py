from SPARQLWrapper import JSON, SPARQLWrapper

from ...settings import GRAPHDB_REPOSITORY_URL


class GraphDBClient:
    def __init__(self, uri: str = GRAPHDB_REPOSITORY_URL):
        self._uri = uri
        self._client: SPARQLWrapper | None = None

    def connect(self) -> None:
        if self._client is not None:
            return

        client = SPARQLWrapper(self._uri)
        client.setReturnFormat(JSON)

        client.setQuery("ASK {}")
        result = client.query().convert()

        if not isinstance(result, dict) or "boolean" not in result:
            raise ConnectionError(f"Unexpected response from GraphDB at {self._uri}")

        self._client = client

    @property
    def client(self) -> SPARQLWrapper:
        if self._client is None:
            raise RuntimeError("GraphDB client is not connected. Call connect() first.")
        return self._client

    def query(self, query: str):
        self.client.setQuery(query)
        return self.client.query().convert()

    def close(self) -> None:
        self._client = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
