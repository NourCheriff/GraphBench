from SPARQLWrapper import JSON, SPARQLWrapper

_URI = "http://localhost:7200/repositories/OrderManagement"


class GraphDBClient:
    def __init__(self, uri: str = _URI):
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
