from __future__ import annotations
from pathlib import Path
from .connector import GraphDBClient

import time
import urllib.error
import urllib.request

REPO_ROOT = Path(__file__).resolve().parents[4]
SCHEMA_PATH = REPO_ROOT / "docs" / "schemas" / "rdf" / "variants" / "v2.ttl"
DATA_PATH = REPO_ROOT / "output" / "rdf" / "order-management.ttl"

REPOSITORY_URL = "http://localhost:7200/repositories/OrderManagement"

def _request(method: str, url: str, body: bytes | None = None) -> bytes:
    headers = {
        "Content-Type": "text/turtle"
    } 

    request = urllib.request.Request(
        url, 
        data=body, 
        method=method, 
        headers=headers
    )

    try:
        with urllib.request.urlopen(request) as response:
            return response.read()
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GraphDB returned {error.code} for {method} {url}:\n{detail}") from None


def clear_repository() -> None:
    _request("DELETE", f"{REPOSITORY_URL}/statements")


def upload_file(path: Path) -> float:
    start = time.perf_counter()
    _request("POST", f"{REPOSITORY_URL}/statements", path.read_bytes())
    return time.perf_counter() - start


def get_size(graphdb: GraphDBClient) -> int:
    result = graphdb.query("SELECT (COUNT(*) AS ?n) WHERE { ?s ?p ?o }")
    return int(result["results"]["bindings"][0]["n"]["value"])


def main() -> None:
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