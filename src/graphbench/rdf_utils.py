from __future__ import annotations

import re
from datetime import UTC, datetime
from urllib.parse import quote, unquote

from rdflib import XSD, Literal, Namespace, URIRef


def iri(namespace: Namespace, identifier: str) -> URIRef:
    return namespace[quote(identifier, safe="")]


def decode(iri: str) -> str:
    return unquote(re.split(r"[/#]", iri)[-1])


def time_literal(value: datetime) -> Literal:
    if value.tzinfo is None:
        raise ValueError(f"timestamp without timezone: {value}")
    return Literal(value.astimezone(UTC).isoformat(), datatype=XSD.dateTime)


def value_literal(value: object) -> Literal:
    if isinstance(value, float):
        return Literal(value, datatype=XSD.float)
    if isinstance(value, str):
        return Literal(value, datatype=XSD.string)
    raise ValueError(f"attribute value of unhandled type: {value!r}")


def lookup(table: dict, key):
    try:
        return table[key]
    except KeyError:
        raise ValueError(f"key not found in table: {key!r}") from None
