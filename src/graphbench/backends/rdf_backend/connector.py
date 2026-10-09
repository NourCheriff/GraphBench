from SPARQLWrapper import JSON, SPARQLWrapper

_URI = "http://localhost:7200/repositories/OrderManagement"


def get_sparql_wrapper() -> SPARQLWrapper:
    sparql = SPARQLWrapper(_URI)
    sparql.setReturnFormat(JSON)

    if not _check_connection(sparql):
        raise Exception()

    return sparql


def _check_connection(sparql: SPARQLWrapper) -> bool:
    try:
        sparql.setQuery("ASK {}")
        result = sparql.query().convert()
        return isinstance(result, dict) and "boolean" in result
    except Exception as ex:
        return False
