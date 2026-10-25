import re
import unicodedata
from collections import defaultdict
from collections.abc import Iterator
from typing import Any

from ...datareader.models import OCELLog

_BATCH_SIZE = 1000

_OBJECT_LABELS: dict[str, str] = {
    "customers": "Customer",
    "orders": "Order",
    "items": "Item",
    "products": "Product",
    "packages": "Package",
    "employees": "Employee",
}

_O2O_RELATIONSHIPS: dict[tuple[str, str, str], str] = {
    ("customers", "places", "orders"): "PLACES",
    ("customers", "primarySalesRep", "employees"): "PRIMARY_SALES_REP_OF",
    ("customers", "secondarySalesRep", "employees"): "SECONDARY_SALES_REP_OF",
    ("orders", "comprises", "items"): "INCLUDES",
    ("items", "is a", "products"): "IS_A",
    ("packages", "contains", "items"): "CONTAINS",
    ("packages", "packed by", "employees"): "PACKED_BY",
    ("packages", "forwarded by", "employees"): "FORWARDED_BY",
    ("packages", "shipped by", "employees"): "SHIPPED_BY",
}

_REVERSED_O2O = {
    ("customers", "primarySalesRep", "employees"),
    ("customers", "secondarySalesRep", "employees"),
}

_VERSIONED_ATTRS: set[tuple[str, str]] = {("products", "price")}

_PROP_NAME_REGEX = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")


class CypherGenerator:
    def __init__(
        self,
        batch_size: int = _BATCH_SIZE,
        object_labels: dict[str, str] = _OBJECT_LABELS,
        o2o_relationships: dict[tuple[str, str, str], str] = _O2O_RELATIONSHIPS,
        versioned_attrs: set[tuple[str, str]] = _VERSIONED_ATTRS,
        reversed_o2o: set[tuple[str, str, str]] = _REVERSED_O2O,
    ):
        self._batch_size = batch_size
        self._object_labels = object_labels
        self._o2o_relationships = o2o_relationships
        self._versioned_attrs = versioned_attrs
        self._reversed_o2o = reversed_o2o

    def generate_cypher(self, log: OCELLog) -> Iterator[str]:
        yield "CREATE CONSTRAINT object_id IF NOT EXISTS FOR (o:Object) REQUIRE o.id IS UNIQUE;"
        yield "CREATE CONSTRAINT event_id IF NOT EXISTS FOR (e:Event) REQUIRE e.id IS UNIQUE;"
        yield "CREATE CONSTRAINT productprice_key IF NOT EXISTS FOR (v:ProductPrice) REQUIRE v.key IS UNIQUE;"

        nodes: dict[str, list[dict]] = defaultdict(list)
        prices: list[dict] = []

        for obj in log.objects.values():
            label = self._object_labels[obj.type]
            props: dict[str, Any] = {}

            for attr in obj.attributes:
                ts = attr.time.isoformat()

                if (obj.type, attr.name) in self._versioned_attrs:
                    prices.append(
                        {
                            "object_id": obj.id,
                            "key": f"{obj.id}|{ts}",
                            "value": attr.value,
                            "timestamp": ts,
                        }
                    )
                elif attr.name in props:
                    raise ValueError(
                        f"object {obj.id!r}, attribute {attr.name!r}: several values for a non-versioned attribute"
                    )
                else:
                    props[attr.name] = attr.value

            nodes[label].append({"id": obj.id, "props": props})

        if len({p["key"] for p in prices}) != len(prices):
            raise ValueError("two prices for the same product at the same time")

        for label, rows in nodes.items():
            yield from self._unwind(
                rows, f"MERGE (o:Object {{id: row.id}})\nSET o:{label}, o += row.props"
            )

        events = []
        for ev in log.events.values():
            if ev.attributes:
                raise ValueError(f"event {ev.id!r}: event attributes are not supported")

            events.append(
                {
                    "id": ev.id,
                    "type": ev.type,
                    "timestamp": ev.time.isoformat(),
                }
            )
        yield from self._unwind(
            events,
            "MERGE (e:Event {id: row.id})\nSET e.type = row.type, e.timestamp = datetime(row.timestamp)",
        )

        # add ProductPrice node and relationship
        yield from self._unwind(
            prices,
            "MATCH (o:Object {id: row.object_id})\n"
            "MERGE (v:ProductPrice {key: row.key})\n"
            "SET v.value = row.value, v.timestamp = datetime(row.timestamp)\n"
            "MERGE (o)-[:HAS_PRICE]->(v)",
        )

        e2o = []
        for rel in log.e2o:
            (
                log.events[rel.source_id],
                log.objects[rel.target_id],
            )
            e2o.append(
                {
                    "event_id": rel.source_id,
                    "object_id": rel.target_id,
                    "qualifier": rel.qualifier,
                }
            )
        yield from self._unwind(
            e2o,
            "MATCH (e:Event {id: row.event_id})\nMATCH (o:Object {id: row.object_id})\n"
            "MERGE (e)-[:INVOLVES {qualifier: row.qualifier}]->(o)",
        )

        o2o: dict[str, list[dict]] = defaultdict(list)
        for rel in log.o2o:
            key = (
                log.objects[rel.source_id].type,
                rel.qualifier,
                log.objects[rel.target_id].type,
            )
            source, target = rel.source_id, rel.target_id

            if key in self._reversed_o2o:
                source, target = target, source

            o2o[self._o2o_relationships[key]].append(
                {"source_id": source, "target_id": target}
            )

        for rel_type, rows in o2o.items():
            yield from self._unwind(
                rows,
                "MATCH (s:Object {id: row.source_id})\nMATCH (t:Object {id: row.target_id})\n"
                f"MERGE (s)-[:{rel_type}]->(t)",
            )

        yield "CREATE INDEX event_type IF NOT EXISTS FOR (e:Event) ON (e.type);"
        yield "CREATE INDEX event_timestamp IF NOT EXISTS FOR (e:Event) ON (e.timestamp);"
        yield "CREATE INDEX productprice_timestamp IF NOT EXISTS FOR (v:ProductPrice) ON (v.timestamp);"
        yield "CALL db.awaitIndexes();"

    def _cypher_literal(self, value: Any) -> str:
        if isinstance(value, str):
            out = []
            for ch in value:
                if ch in '\\"':
                    out.append("\\" + ch)
                elif ch == "\n":
                    out.append("\\n")
                elif unicodedata.category(ch) in ("Cc", "Zl", "Zp"):
                    out.append(f"\\u{ord(ch):04x}")
                else:
                    out.append(ch)
            return '"' + "".join(out) + '"'

        if isinstance(value, dict):
            items = []
            for key, val in value.items():
                if not isinstance(key, str) or not _PROP_NAME_REGEX.match(key):
                    raise ValueError(f"unsafe property name {key!r}")

                items.append(f"{key}: {self._cypher_literal(val)}")

            return "{" + ", ".join(items) + "}"

        return repr(value)

    def _unwind(self, rows: list[dict], body: str) -> Iterator[str]:
        for i in range(0, len(rows), self._batch_size):
            lines = ",\n".join(
                f"  {self._cypher_literal(r)}" for r in rows[i : i + self._batch_size]
            )
            yield f"UNWIND [\n{lines}\n] AS row\n{body};"
