from pathlib import Path

from ...datareader.reader import DataReader
from .connector import GraphDBClient

DATASET_PATH = (
    Path(__file__).resolve().parent / "../../../../data/order-management.json"
).resolve()


def main():
    data = DataReader().read(DATASET_PATH)

    with GraphDBClient() as graphdb:
        result = graphdb.query("ASK {}")
        print(result)


if __name__ == "__main__":
    main()
