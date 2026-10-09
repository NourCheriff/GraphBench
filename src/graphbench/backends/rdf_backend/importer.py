from .connector import GraphDBClient


def main():
    with GraphDBClient() as graphdb:
        result = graphdb.query("ASK {}")
        print(result)


if __name__ == "__main__":
    main()
