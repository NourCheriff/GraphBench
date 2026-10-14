from pathlib import Path

from ...datareader.reader import DataReader
from .connector import Neo4jClient

DATABASE = ""
DATASET_PATH = (
    Path(__file__).resolve().parent / "../../../../data/order-management.json"
).resolve()


def main():
    data = DataReader().read(DATASET_PATH)
    with Neo4jClient() as client:
        print("Neo4j - Connection established")


if __name__ == "__main__":
    main()
