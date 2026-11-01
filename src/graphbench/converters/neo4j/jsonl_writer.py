from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

from .cypher_generator import Operation
from .utils import write_atomic


class JsonlWriter:
    def write_jsonl(self, operations: Iterable[Operation], path: Path) -> int:
        return write_atomic(
            path,
            (
                json.dumps({"query": op.query, "rows": op.rows}, ensure_ascii=False)
                + "\n"
                for op in operations
            ),
        )
