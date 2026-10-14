from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class AttributeDefinition:
    name: str
    type: str


@dataclass(frozen=True)
class TypeDefinition:
    name: str
    attributes: tuple[AttributeDefinition, ...] = ()


@dataclass(frozen=True)
class Attribute:
    name: str
    value: Any
    time: datetime | None = None


@dataclass(frozen=True)
class OCELEvent:
    id: str
    type: str
    time: datetime
    attributes: tuple[Attribute, ...] = ()


@dataclass(frozen=True)
class OCELObject:
    id: str
    type: str
    attributes: tuple[Attribute, ...] = ()


@dataclass(frozen=True)
class Relationship:
    source_id: str
    target_id: str
    qualifier: str


@dataclass(frozen=True)
class OCELLog:
    event_types: dict[str, TypeDefinition]
    object_types: dict[str, TypeDefinition]
    objects: dict[str, OCELObject]
    events: dict[str, OCELEvent]
    e2o: tuple[Relationship, ...]
    o2o: tuple[Relationship, ...]
