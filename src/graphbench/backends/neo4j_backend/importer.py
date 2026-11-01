from collections.abc import Iterable
from pathlib import Path

from tqdm import tqdm

from .connector import Neo4jClient

DATABASE = "order-management"

REPO_ROOT = Path(__file__).resolve().parents[4]
CYPHER_FILE_PATH = REPO_ROOT / "output" / "neo4j" / "order-management.cypher"

STATEMENT_SEP = ";\n"


def read_statements(path: Path) -> list[str]:
    statements = path.read_text(encoding="utf-8").split(STATEMENT_SEP)
    return [statement for statement in statements if statement.strip()]


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


def load(client: Neo4jClient, statements: Iterable[str]) -> None:
    for statement in statements:
        client.driver.execute_query(statement.strip(), database_=DATABASE)


def load_database(
    client: Neo4jClient, path: Path = CYPHER_FILE_PATH, progress: bool = False
) -> None:
    statements: Iterable[str] = read_statements(path)
    if progress:
        statements = tqdm(statements, desc="Importing", unit="stmt")
    load(client, statements)


def main():
    with Neo4jClient() as client:
        wipe_database(client)
        load_database(client, CYPHER_FILE_PATH, progress=True)


if __name__ == "__main__":
    main()
