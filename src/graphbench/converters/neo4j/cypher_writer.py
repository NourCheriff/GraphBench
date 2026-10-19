from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

STATEMENT_SEPARATOR = "\n\n"


class CypherWriter:
    def write_cypher(self, statements: Iterable[str], path: Path) -> int:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".tmp")
        count = 0

        try:
            with open(tmp, "w", encoding="utf-8", newline="\n") as file:
                for statement in statements:
                    if not statement.endswith(";"):
                        raise ValueError(
                            f"statement does not end with ';': {statement[:80]!r}"
                        )

                    file.write(statement)
                    file.write(STATEMENT_SEPARATOR)
                    count += 1

            tmp.replace(path)
        except BaseException:
            tmp.unlink(missing_ok=True)
            raise

        return count
