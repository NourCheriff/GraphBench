from __future__ import annotations

import time
from pathlib import Path

import requests

from ...settings import (
    GRAPHDB_CONFIG_PATH,
    GRAPHDB_REPOSITORY,
    GRAPHDB_REPOSITORY_URL,
    GRAPHDB_URL,
    RDF_OUTPUT_PATH,
    RDF_SCHEMA_PATH,
)
from .connector import GraphDBClient


def _check(response: requests.Response) -> requests.Response:
    if not response.ok:
        raise RuntimeError(
            f"GraphDB returned {response.status_code} for "
            f"{response.request.method} {response.url}:\n{response.text}"
        )
    return response


def repository_exists(repository_id: str = GRAPHDB_REPOSITORY) -> bool:
    repositories = _check(requests.get(f"{GRAPHDB_URL}/rest/repositories")).json()
    return any(repo["id"] == repository_id for repo in repositories)


def create_repository(config_path: Path = GRAPHDB_CONFIG_PATH) -> None:
    with config_path.open("rb") as config:
        _check(
            requests.post(f"{GRAPHDB_URL}/rest/repositories", files={"config": config})
        )


def ensure_repository(config_path: Path = GRAPHDB_CONFIG_PATH) -> None:
    if not repository_exists():
        create_repository(config_path)


def clear_repository() -> None:
    _check(requests.delete(f"{GRAPHDB_REPOSITORY_URL}/statements"))


def upload_file(path: Path) -> float:
    start = time.perf_counter()
    _check(
        requests.post(
            f"{GRAPHDB_REPOSITORY_URL}/statements",
            data=path.read_bytes(),
            headers={"Content-Type": "text/turtle"},
        )
    )
    return time.perf_counter() - start


def get_size(graphdb: GraphDBClient) -> int:
    result = graphdb.query("SELECT (COUNT(*) AS ?n) WHERE { ?s ?p ?o }")
    return int(result["results"]["bindings"][0]["n"]["value"])


def load_repository(
    schema_path: Path = RDF_SCHEMA_PATH, data_path: Path = RDF_OUTPUT_PATH
) -> None:
    upload_file(schema_path)
    upload_file(data_path)


def main() -> None:
    ensure_repository()

    with GraphDBClient(GRAPHDB_REPOSITORY_URL) as graphdb:
        clear_repository()

        schema_time = upload_file(RDF_SCHEMA_PATH)
        data_time = upload_file(RDF_OUTPUT_PATH)
        size = get_size(graphdb)

    print(f"schema loaded in {schema_time:.1f}s ({RDF_SCHEMA_PATH.name})")
    print(f"data loaded in   {data_time:.1f}s ({RDF_OUTPUT_PATH.name})")
    print(f"statements in repository: {size:,}")


if __name__ == "__main__":
    main()
