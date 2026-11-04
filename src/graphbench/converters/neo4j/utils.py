from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path


def write_atomic(path: Path, chunks: Iterable[str]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    count = 0

    try:
        with open(tmp, "w", encoding="utf-8", newline="\n") as file:
            for chunk in chunks:
                file.write(chunk)
                count += 1

        tmp.replace(path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise

    return count
