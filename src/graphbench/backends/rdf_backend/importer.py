from .connector import SPARQLWrapper, get_sparql_wrapper


def main():
    sparql = get_sparql_wrapper()
    print("GraphDB - Connection established")


if __name__ == "__main__":
    main()
