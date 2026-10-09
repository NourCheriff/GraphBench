from .connector import Driver, get_driver


def main():
    with get_driver() as driver:
        print("Neo4j - Connection established")


if __name__ == "__main__":
    main()
