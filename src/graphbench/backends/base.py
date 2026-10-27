from typing import Protocol

from ..query import Query, QueryName


class QueryBackend(Protocol):
    @property
    def name(self) -> str: ...

    def list_queries(self) -> list[Query]: ...

    def load_query(self, name: QueryName) -> str: ...

    def execute(self, query: Query) -> list[dict]: ...
