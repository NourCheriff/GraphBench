from __future__ import annotations

import time
from pathlib import Path

import requests

from .connector import GraphDBClient

REPO_ROOT = Path(__file__).resolve().parents[4]
SCHEMA_PATH = REPO_ROOT / "docs" / "schemas" / "rdf" / "variants" / "v2.ttl"
DATA_PATH = REPO_ROOT / "output" / "rdf" / "order-management.ttl"
CONFIG_PATH = REPO_ROOT / "config" / "rdf" / "order-management-config.ttl"

SERVER_URL = "http://localhost:7200"
REPOSITORY_ID = "OrderManagement"
REPOSITORY_URL = f"{SERVER_URL}/repositories/{REPOSITORY_ID}"


def _check(response: requests.Response) -> requests.Response:
    if not response.ok:
        raise RuntimeError(
            f"GraphDB returned {response.status_code} for "
            f"{response.request.method} {response.url}:\n{response.text}"
        )
    return response


def repository_exists(repository_id: str = REPOSITORY_ID) -> bool:
    repositories = _check(requests.get(f"{SERVER_URL}/rest/repositories")).json()
    return any(repo["id"] == repository_id for repo in repositories)


def create_repository(config_path: Path = CONFIG_PATH) -> None:
    with config_path.open("rb") as config:
        _check(
            requests.post(f"{SERVER_URL}/rest/repositories", files={"config": config})
        )


def ensure_repository(config_path: Path = CONFIG_PATH) -> None:
    if not repository_exists():
        create_repository(config_path)


def clear_repository() -> None:
    _check(requests.delete(f"{REPOSITORY_URL}/statements"))


def upload_file(path: Path) -> float:
    start = time.perf_counter()
    _check(
        requests.post(
            f"{REPOSITORY_URL}/statements",
            data=path.read_bytes(),
            headers={"Content-Type": "text/turtle"},
        )
    )
    return time.perf_counter() - start


def get_size(graphdb: GraphDBClient) -> int:
    result = graphdb.query("SELECT (COUNT(*) AS ?n) WHERE { ?s ?p ?o }")
    return int(result["results"]["bindings"][0]["n"]["value"])


def load_repository(
    schema_path: Path = SCHEMA_PATH, data_path: Path = DATA_PATH
) -> None:
    upload_file(schema_path)
    upload_file(data_path)


def main() -> None:
    ensure_repository()

    with GraphDBClient(REPOSITORY_URL) as graphdb:
        clear_repository()

        schema_time = upload_file(SCHEMA_PATH)
        data_time = upload_file(DATA_PATH)
        size = get_size(graphdb)

    print(f"schema loaded in {schema_time:.1f}s ({SCHEMA_PATH.name})")
    print(f"data loaded in   {data_time:.1f}s ({DATA_PATH.name})")
    print(f"statements in repository: {size:,}")


if __name__ == "__main__":
    main()
