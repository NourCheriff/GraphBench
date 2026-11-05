from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass
from string import Template

from ..backends.neo4j_backend.connector import Neo4jClient
from ..backends.rdf_backend.connector import GraphDBClient
from ..converters.ocel_to_rdf import DATA
from ..settings import NEO4J_DATABASE

logger = logging.getLogger(__name__)


EXPLICIT = "http://www.ontotext.com/explicit"
INFERRED = "http://www.ontotext.com/implicit"

RDF_TRIPLE_KINDS = Template("""
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
SELECT ?kind (COUNT(*) AS ?count)
FROM <$graph>
WHERE {
  ?s ?p ?o .
  BIND(
    IF(!(isIRI(?s) && STRSTARTS(STR(?s), "$data")), "schema",
    IF(?p = rdf:type, "type",
    IF(isLiteral(?o), "literal",
    IF(isIRI(?o) && STRSTARTS(STR(?o), "$data"), "edge", "other")))) AS ?kind)
}
GROUP BY ?kind
""")

RDF_NODE_KINDS = Template("""
SELECT ?kind (COUNT(DISTINCT ?n) AS ?count)
FROM <$graph>
WHERE {
  { ?n ?p ?o } UNION { ?s ?p ?n }
  FILTER(isIRI(?n) && STRSTARTS(STR(?n), "$data"))
  BIND(STRBEFORE(STRAFTER(STR(?n), "$data"), "/") AS ?kind)
}
GROUP BY ?kind
""")

RDF_EDGES = Template("""
SELECT ?s ?o
FROM <$graph>
WHERE {
  ?s ?p ?o .
  FILTER(isIRI(?s) && isIRI(?o)
         && STRSTARTS(STR(?s), "$data") && STRSTARTS(STR(?o), "$data"))
}
""")


LPG_NODE_KINDS = """
MATCH (n)
RETURN CASE
         WHEN n:Event THEN 'event'
         WHEN n:ProductPrice THEN 'attribute'
         WHEN n:Object THEN 'object'
         ELSE 'other'
       END AS kind,
       count(n) AS count
"""

LPG_EDGES = """
MATCH (s)-->(o)
RETURN elementId(s) AS s, elementId(o) AS o,
       s:Event AS from_event, o:ProductPrice AS to_attribute
"""


@dataclass(kw_only=True)
class GraphMetric:
    backend: str
    metric: str
    value: float


def edge_kind(from_event: bool, to_attribute: bool) -> str:
    """Same rule on both models: event -> object, object -> price, object -> object."""
    if from_event:
        return "e2o"
    if to_attribute:
        return "attribute"
    return "o2o"


def edge_metrics(nodes: int, edges: list[tuple[str, str, str]]) -> dict[str, float]:
    """Edges by kind, their sum, and degree metrics; `edges` = (source, target, kind)."""
    kinds = Counter(kind for _, _, kind in edges)
    out_degree = Counter(s for s, _, _ in edges)
    in_degree = Counter(o for _, o, _ in edges)
    return {
        "edges_e2o": kinds["e2o"],
        "edges_o2o": kinds["o2o"],
        "edges_attribute": kinds["attribute"],
        "edges": len(edges),
        "density": len(edges) / (nodes * (nodes - 1)) if nodes > 1 else 0.0,
        "avg_degree": len(edges) / nodes if nodes else 0.0,
        "max_out_degree": max(out_degree.values(), default=0),
        "max_in_degree": max(in_degree.values(), default=0),
    }


def _sparql(client: GraphDBClient, template: Template, graph: str) -> list[dict]:
    result = client.query(template.substitute(graph=graph, data=DATA))
    return [
        {k: cell["value"] for k, cell in binding.items()}
        for binding in result["results"]["bindings"]
    ]


def graphdb_metrics(client: GraphDBClient) -> dict[str, float]:
    metrics: dict[str, float] = {}

    for kind in ("event", "object", "attribute"):
        metrics[f"nodes_{kind}"] = 0
    for row in _sparql(client, RDF_NODE_KINDS, EXPLICIT):
        metrics[f"nodes_{row['kind']}"] = int(row["count"])
    nodes = sum(metrics.values())
    metrics["nodes"] = nodes

    for graph, suffix in ((EXPLICIT, "explicit"), (INFERRED, "inferred")):
        counts = {k: 0 for k in ("edge", "literal", "type", "schema", "other")}
        for row in _sparql(client, RDF_TRIPLE_KINDS, graph):
            counts[row["kind"]] = int(row["count"])
        metrics[f"triples_{suffix}"] = sum(counts.values())
        metrics[f"resource_edges_{suffix}"] = counts["edge"]
        metrics[f"literal_triples_{suffix}"] = counts["literal"]
        metrics[f"type_triples_{suffix}"] = counts["type"]
        metrics[f"schema_triples_{suffix}"] = counts["schema"]
        metrics[f"other_triples_{suffix}"] = counts["other"]
    metrics["resource_edges"] = (
        metrics["resource_edges_explicit"] + metrics["resource_edges_inferred"]
    )

    def kind(iri: str) -> str:
        return iri.removeprefix(DATA).split("/")[0]  # event, object, attribute

    edges = [
        (s, o, edge_kind(kind(s) == "event", kind(o) == "attribute"))
        for s, o in (
            (row["s"], row["o"]) for row in _sparql(client, RDF_EDGES, EXPLICIT)
        )
    ]
    metrics.update(edge_metrics(nodes, edges))
    return metrics


def neo4j_metrics(
    client: Neo4jClient, database: str = NEO4J_DATABASE
) -> dict[str, float]:
    def run(query: str) -> list[dict]:
        records, _, _ = client.driver.execute_query(query, database_=database)
        return [record.data() for record in records]

    metrics: dict[str, float] = {}
    for kind in ("event", "object", "attribute"):
        metrics[f"nodes_{kind}"] = 0
    for row in run(LPG_NODE_KINDS):
        metrics[f"nodes_{row['kind']}"] = row["count"]
    nodes = sum(metrics.values())
    metrics["nodes"] = nodes

    edges = [
        (row["s"], row["o"], edge_kind(row["from_event"], row["to_attribute"]))
        for row in run(LPG_EDGES)
    ]
    metrics.update(edge_metrics(nodes, edges))
    return metrics


def compute_sna() -> list[GraphMetric]:
    with Neo4jClient() as neo4j_client, GraphDBClient() as graphdb_client:
        results = {
            "neo4j": neo4j_metrics(neo4j_client),
            "graphdb": graphdb_metrics(graphdb_client),
        }

    rows = []
    for backend, metrics in results.items():
        for metric, value in metrics.items():
            logger.info("%s %s: %s", backend, metric, value)
            rows.append(GraphMetric(backend=backend, metric=metric, value=value))
    return rows


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    compute_sna()


if __name__ == "__main__":
    main()
