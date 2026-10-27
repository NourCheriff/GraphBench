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


def main():
    statements = read_statements(CYPHER_FILE_PATH)

    with Neo4jClient() as client:
        wipe_database(client)

        for statement in tqdm(statements, desc="Importing", unit="stmt"):
            client.driver.execute_query(statement.strip(), database_=DATABASE)


if __name__ == "__main__":
    main()
