from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, ClassVar

from ..query import Query, QueryName

Row = dict[str, Any]


class QueryBackend(ABC):
    name: ClassVar[str]
    extension: ClassVar[str]

    def __init__(self, queries_dir: Path):
        self._dir = queries_dir

    def _path(self, name: QueryName) -> Path:
        """Each QueryName has its query file named <name>.<extension>."""
        return self._dir / f"{name}.{self.extension}"

    def list_queries(self) -> list[Query]:
        return [Query(name, self.load_query(name)) for name in QueryName]

    def load_query(self, name: QueryName) -> str:
        path = self._path(name)

        if not path.is_file():
            raise FileNotFoundError(f"missing query file: {path}")

        return path.read_text(encoding="utf-8").strip()

    @abstractmethod
    def execute(self, query: Query) -> list[Row]: ...
