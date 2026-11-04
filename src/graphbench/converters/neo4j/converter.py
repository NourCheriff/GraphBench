from pathlib import Path
from typing import Literal

from ...datareader.models import OCELLog
from ...datareader.reader import DataReader
from ...settings import DATASET_PATH, LPG_CYPHER_PATH, LPG_JSONL_PATH
from .cypher_generator import CypherGenerator
from .cypher_writer import CypherWriter
from .jsonl_writer import JsonlWriter

type OutputFormat = Literal["jsonl", "cypher"]

OUTPUT_PATHS: dict[OutputFormat, Path] = {
    "jsonl": LPG_JSONL_PATH,
    "cypher": LPG_CYPHER_PATH,
}


def convert(log: OCELLog, fmt: OutputFormat = "jsonl", path: Path | None = None) -> int:
    path = path or OUTPUT_PATHS[fmt]
    operations = CypherGenerator().generate_cypher(log)

    match fmt:
        case "jsonl":
            return JsonlWriter().write_jsonl(operations, path)
        case "cypher":
            return CypherWriter().write_cypher(operations, path)


def main() -> None:
    log = DataReader().read(DATASET_PATH)

    for fmt in ("jsonl", "cypher"):
        count = convert(log, fmt)
        print(f"Wrote {count} operations to {OUTPUT_PATHS[fmt]}")


if __name__ == "__main__":
    main()
