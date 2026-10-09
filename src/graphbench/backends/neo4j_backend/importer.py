from .connector import Neo4jClient

DATABASE = ""


def main():
    with Neo4jClient() as client:
        print("Neo4j - Connection established")


if __name__ == "__main__":
    main()
