import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from tqdm import tqdm

from .connector import Neo4jClient

DATABASE = "order-management"

REPO_ROOT = Path(__file__).resolve().parents[4]
IMPORT_FILE_PATH = REPO_ROOT / "output" / "neo4j" / "order-management.jsonl"


def read_operations(path: Path) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def wipe_database(client: Neo4jClient) -> None:
    with client.driver.session(database=DATABASE) as session:
        session.run(
            "MATCH (n) CALL (n) { DETACH DELETE n } IN TRANSACTIONS OF 10000 ROWS"
        ).consume()

        constraints = session.run("SHOW CONSTRAINTS YIELD name").value("name")
        for name in constraints:
            session.run(f"DROP CONSTRAINT `{name}` IF EXISTS").consume()

        indexes = session.run(
            "SHOW INDEXES YIELD name, type WHERE type <> 'LOOKUP' RETURN name"
        ).value("name")
        for name in indexes:
            session.run(f"DROP INDEX `{name}` IF EXISTS").consume()


def load(client: Neo4jClient, operations: Iterable[dict[str, Any]]) -> None:
    for op in operations:
        rows = op["rows"]
        client.driver.execute_query(
            op["query"],
            None if rows is None else {"rows": rows},
            database_=DATABASE,
        )


def load_database(
    client: Neo4jClient, path: Path = IMPORT_FILE_PATH, progress: bool = False
) -> None:
    operations: Iterable[dict[str, Any]] = read_operations(path)
    if progress:
        operations = tqdm(operations, desc="Importing", unit="op")
    load(client, operations)


def main():
    with Neo4jClient() as client:
        wipe_database(client)
        load_database(client, IMPORT_FILE_PATH, progress=True)


if __name__ == "__main__":
    main()
