from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from urllib.parse import quote

from rdflib import OWL, RDF, Graph, Namespace

from graphbench.rdf_utils import (
    iri,
    lookup,
    time_literal,
    value_literal,
)

from ..datareader.models import Attribute, OCELLog
from ..datareader.reader import DataReader

REPO_ROOT = Path(__file__).resolve().parents[3]
DATASET_PATH = REPO_ROOT / "data" / "order-management.json"
SCHEMA_PATH = REPO_ROOT / "docs" / "schemas" / "rdf" / "variants" / "v2.ttl"
OUTPUT_PATH = REPO_ROOT / "output" / "rdf" / "order-management.ttl"
MATERIALIZE_INVERSES = True

OCEL = Namespace("https://graphbench.org/ocel#")
OM = Namespace("https://graphbench.org/order-management#")
DATA = "https://graphbench.org/order-management/data/"
EVENT = Namespace(DATA + "event/")
OBJ = Namespace(DATA + "object/")
ATTRIBUTE_VALUE = Namespace(DATA + "attribute/")

EVENT_CLASS = {
    "place order": OM.PlaceOrder,
    "confirm order": OM.ConfirmOrder,
    "payment reminder": OM.PaymentReminder,
    "pay order": OM.PayOrder,
    "item out of stock": OM.ItemOutOfStock,
    "reorder item": OM.ReorderItem,
    "pick item": OM.PickItem,
    "create package": OM.CreatePackage,
    "send package": OM.SendPackage,
    "failed delivery": OM.FailedDelivery,
    "package delivered": OM.PackageDelivered,
}

OBJECT_CLASS = {
    "orders": OM.Order,
    "items": OM.Item,
    "packages": OM.Package,
    "customers": OM.Customer,
    "products": OM.Product,
    "employees": OM.Employee,
}

E2O_PROPERTY = {
    "customer": OM.customer,
    "sales person": OM.salesPerson,
    "item": OM.item,
    "order": OM.order,
    "product": OM.product,
    "packer": OM.packer,
    "creates": OM.creates,
    "shipper": OM.shipper,
    "shipped package": OM.shippedPackage,
    "employee": OM.employee,
    "forwarder": OM.forwarder,
}

O2O_PROPERTY = {
    "places": (OM.places, False),
    "comprises": (OM.comprises, False),
    "is a": (OM.isA, False),
    "contains": (OM.contains, False),
    "packed by": (OM.packedBy, False),
    "forwarded by": (OM.forwardedBy, False),
    "shipped by": (OM.shippedBy, False),
    "primarySalesRep": (OM.primarySalesRepOf, True),
    "secondarySalesRep": (OM.secondarySalesRepOf, True),
}

INVERSE_PROPERTY = {
    OM.comprises: OM.belongsToOrder,
    OM.contains: OM.packedInto,
}

STATIC_ATTRIBUTE = {
    ("orders", "price"): OM.price,
    ("items", "price"): OM.price,
    ("items", "weight"): OM.weight,
    ("packages", "weight"): OM.weight,
    ("products", "weight"): OM.weight,
    ("employees", "role"): OM.role,
}

DYNAMIC_ATTRIBUTE = {
    ("products", "price"): OM.hasPrice,
}


def build_graph(log: OCELLog, materialize_inverses: bool = False) -> Graph:
    g = Graph()
    for prefix, ns in (
        ("ocel", OCEL),
        ("om", OM),
        ("ev", EVENT),
        ("obj", OBJ),
        ("av", ATTRIBUTE_VALUE),
    ):
        g.bind(prefix, ns)

    _add_objects(g, log)
    _add_events(g, log)
    _add_e2o(g, log)
    _add_o2o(g, log, materialize_inverses)
    return g


def _add_objects(g: Graph, log: OCELLog) -> None:
    for obj in log.objects.values():
        subject = iri(OBJ, obj.id)
        g.add((subject, RDF.type, lookup(OBJECT_CLASS, obj.type)))

        history: dict[str, list[Attribute]] = defaultdict(list)
        for attr in obj.attributes:
            history[attr.name].append(attr)

        for name, values in history.items():
            key = (obj.type, name)
            values.sort(key=lambda a: a.time)

            if key in DYNAMIC_ATTRIBUTE:
                prop = DYNAMIC_ATTRIBUTE[key]
                for index, attr in enumerate(values):
                    node = ATTRIBUTE_VALUE[f"{quote(obj.id, safe='')}/{name}/{index}"]
                    g.add((subject, prop, node))
                    g.add((node, RDF.type, OCEL.AttributeValue))
                    g.add((node, OCEL.value, value_literal(attr.value)))
                    g.add((node, OCEL.time, time_literal(attr.time)))

            elif key in STATIC_ATTRIBUTE:
                if len(values) > 1:
                    raise ValueError(
                        f"{obj.id}: the attribute {name!r} has {len(values)} values "
                        f"but is mapped as static"
                    )
                g.add((subject, STATIC_ATTRIBUTE[key], value_literal(values[0].value)))

            else:
                raise ValueError(f"attribute {key!r} not mapped in the converter")


def _add_events(g: Graph, log: OCELLog) -> None:
    for event in log.events.values():
        subject = iri(EVENT, event.id)
        g.add((subject, RDF.type, lookup(EVENT_CLASS, event.type)))
        g.add((subject, OCEL.time, time_literal(event.time)))


def _add_e2o(g: Graph, log: OCELLog) -> None:
    for rel in log.e2o:
        prop = lookup(E2O_PROPERTY, rel.qualifier)
        g.add((iri(EVENT, rel.source_id), prop, iri(OBJ, rel.target_id)))


def _add_o2o(g: Graph, log: OCELLog, materialize_inverses: bool) -> None:
    for rel in log.o2o:
        prop, inverted = lookup(O2O_PROPERTY, rel.qualifier)
        source = iri(OBJ, rel.source_id)
        target = iri(OBJ, rel.target_id)
        if inverted:
            source, target = target, source
        g.add((source, prop, target))
        if materialize_inverses and prop in INVERSE_PROPERTY:
            g.add((target, INVERSE_PROPERTY[prop], source))


def validate_graph(data: Graph, schema: Graph) -> None:
    declared = (
        set(schema.subjects(RDF.type, OWL.Class))
        | set(schema.subjects(RDF.type, OWL.ObjectProperty))
        | set(schema.subjects(RDF.type, OWL.DatatypeProperty))
    )
    problems = [
        f"property not declared: {p}"
        for p in set(data.predicates()) - {RDF.type}
        if p not in declared
    ]
    problems += [
        f"class not declared: {c}"
        for c in set(data.objects(None, RDF.type))
        if c not in declared
    ]
    if problems:
        raise ValueError(
            "the graph is not consistent with the ontology:\n  "
            + "\n  ".join(sorted(problems))
        )


def save_graph(graph: Graph, path: Path, fmt: str = "turtle") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(destination=path, format=fmt, encoding="utf-8")


def convert(
    log: OCELLog, path: Path = OUTPUT_PATH, schema: Graph | None = None
) -> None:
    graph = build_graph(log, MATERIALIZE_INVERSES)
    if schema is not None:
        validate_graph(graph, schema)
    save_graph(graph, path, "turtle")


def main() -> None:
    ocel_log = DataReader().read(DATASET_PATH)
    convert(ocel_log, OUTPUT_PATH, schema=Graph().parse(SCHEMA_PATH))


if __name__ == "__main__":
    main()
