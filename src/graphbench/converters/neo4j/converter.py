from pathlib import Path

from ...datareader.reader import DataReader
from .cypher_generator import CypherGenerator
from .cypher_writer import CypherWriter

ROOT = Path(__file__).resolve().parents[4]
DATASET_PATH = ROOT / "data" / "order-management.json"
OUTPUT_PATH = ROOT / "output" / "neo4j" / "order-management.cypher"


def main() -> None:
    log = DataReader().read(DATASET_PATH)

    count = CypherWriter().write_cypher(
        CypherGenerator().generate_cypher(log), OUTPUT_PATH
    )

    print(f"Wrote {count} statements to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
