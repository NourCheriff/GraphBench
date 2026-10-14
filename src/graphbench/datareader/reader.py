import json
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import (
    Attribute,
    AttributeDefinition,
    OCELEvent,
    OCELLog,
    OCELObject,
    Relationship,
    TypeDefinition,
)


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value)


_COERCERS: dict[str, Callable[[Any], Any]] = {
    "string": str,
    "float": float,
    "time": _parse_time,
}


class DataReader:
    def read(self, path: str | Path) -> OCELLog:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)

        return self.parse(data)

    def parse(self, data: dict) -> OCELLog:
        event_types = self._parse_types(data.get("eventTypes", []))
        object_types = self._parse_types(data.get("objectTypes", []))

        object_attr_types = self._declared_types(object_types)
        event_attr_types = self._declared_types(event_types)

        objects: dict[str, OCELObject] = {}
        o2o: list[Relationship] = []
        for raw in data.get("objects", []):
            obj = OCELObject(
                id=raw["id"],
                type=raw["type"],
                attributes=self._parse_attributes(
                    raw.get("attributes", []), object_attr_types.get(raw["type"], {})
                ),
            )

            objects[obj.id] = obj

            for rel in raw.get("relationships", []):
                o2o.append(
                    Relationship(
                        source_id=obj.id,
                        target_id=rel["objectId"],
                        qualifier=rel["qualifier"],
                    )
                )

        events: dict[str, OCELEvent] = {}
        e2o: list[Relationship] = []
        for raw in data.get("events", []):
            event = OCELEvent(
                id=raw["id"],
                type=raw["type"],
                time=_parse_time(raw["time"]),
                attributes=self._parse_attributes(
                    raw.get("attributes", []), event_attr_types.get(raw["type"], {})
                ),
            )

            events[event.id] = event

            for rel in raw.get("relationships", []):
                e2o.append(
                    Relationship(
                        source_id=event.id,
                        target_id=rel["objectId"],
                        qualifier=rel["qualifier"],
                    )
                )

        return OCELLog(
            event_types=event_types,
            object_types=object_types,
            objects=objects,
            events=events,
            o2o=tuple(o2o),
            e2o=tuple(e2o),
        )

    @staticmethod
    def _parse_types(types: list[dict]) -> dict[str, TypeDefinition]:
        return {
            t["name"]: TypeDefinition(
                name=t["name"],
                attributes=tuple(
                    AttributeDefinition(name=attr["name"], type=attr["type"])
                    for attr in t.get("attributes", [])
                ),
            )
            for t in types
        }

    @staticmethod
    def _declared_types(
        types: dict[str, TypeDefinition],
    ) -> dict[str, dict[str, str]]:
        return {
            name: {attr.name: attr.type for attr in t.attributes}
            for name, t in types.items()
        }

    @staticmethod
    def _parse_attributes(
        attrs: list[dict], declared_types: dict[str, str]
    ) -> tuple[Attribute, ...]:
        attributes = []

        for attr in attrs:
            time = _parse_time(attr["time"]) if "time" in attr else None
            type_name = declared_types.get(attr["name"])
            if type_name not in _COERCERS:
                raise ValueError(f"attribute '{attr['name']}' not managed with type not managed: {type_name!r}")
            coerce = _COERCERS.get(declared_types.get(attr["name"]))
            attributes.append(
                Attribute(name=attr["name"], time=time, value=coerce(attr["value"]))
            )

        return tuple(attributes)
