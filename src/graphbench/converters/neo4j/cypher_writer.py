from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .cypher_generator import Operation
from .utils import write_atomic

STATEMENT_SEPARATOR = "\n\n"

_PROP_NAME_REGEX = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")


class CypherWriter:
    def write_cypher(self, operations: Iterable[Operation], path: Path) -> int:
        return write_atomic(
            path, (self._render(op) + ";" + STATEMENT_SEPARATOR for op in operations)
        )

    def _render(self, op: Operation) -> str:
        if op.rows is None:
            return op.query

        lines = ",\n".join(f"  {self._cypher_literal(r)}" for r in op.rows)
        return op.query.replace("$rows", f"[\n{lines}\n]", 1)

    def _cypher_literal(self, value: Any) -> str:
        if isinstance(value, str):
            out = []
            for ch in value:
                if ch in '\\"':
                    out.append("\\" + ch)
                elif ch == "\n":
                    out.append("\\n")
                elif unicodedata.category(ch) in ("Cc", "Zl", "Zp"):
                    out.append(f"\\u{ord(ch):04x}")
                else:
                    out.append(ch)
            return '"' + "".join(out) + '"'

        if isinstance(value, dict):
            items = []
            for key, val in value.items():
                if not isinstance(key, str) or not _PROP_NAME_REGEX.match(key):
                    raise ValueError(f"unsafe property name {key!r}")

                items.append(f"{key}: {self._cypher_literal(val)}")

            return "{" + ", ".join(items) + "}"

        return repr(value)
