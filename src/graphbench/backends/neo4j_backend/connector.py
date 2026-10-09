from neo4j import Driver, GraphDatabase

_URI = "neo4j://localhost:7687"
_AUTH = ("neo4j", "neo4j-pwd")


def get_driver() -> Driver:
    driver = GraphDatabase.driver(
        _URI,
        auth=_AUTH,
    )

    try:
        driver.verify_connectivity()
        return driver
    except Exception:
        driver.close()
        raise ConnectionError(f"Cannot connect to Neo4j instance on uri:{_URI}")
