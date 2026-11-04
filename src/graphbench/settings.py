from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


DATASET_PATH = REPO_ROOT / "data" / "order-management.json"
RDF_SCHEMA_PATH = REPO_ROOT / "docs" / "schemas" / "rdf" / "variants" / "v2.ttl"
GRAPHDB_CONFIG_PATH = REPO_ROOT / "config" / "rdf" / "order-management-config.ttl"
SPARQL_QUERIES_DIR = REPO_ROOT / "queries" / "sparql"
CYPHER_QUERIES_DIR = REPO_ROOT / "queries" / "cypher"


RDF_OUTPUT_PATH = REPO_ROOT / "output" / "rdf" / "order-management.ttl"
LPG_JSONL_PATH = REPO_ROOT / "output" / "neo4j" / "order-management.jsonl"
LPG_CYPHER_PATH = REPO_ROOT / "output" / "neo4j" / "order-management.cypher"
RESULTS_DIR = REPO_ROOT / "output" / "benchmark"
PLOTS_DIR_NAME = "plots"  # subfolder of each run folder


MATERIALIZE_INVERSES = True
NEO4J_BATCH_SIZE = 1000


GRAPHDB_URL = "http://localhost:7200"
GRAPHDB_REPOSITORY = "OrderManagement"
GRAPHDB_REPOSITORY_URL = f"{GRAPHDB_URL}/repositories/{GRAPHDB_REPOSITORY}"


NEO4J_URI = "neo4j://localhost:7687"
NEO4J_AUTH = ("neo4j", "neo4j-pwd")
NEO4J_DATABASE = "order-management"


GRAPHDB_CONTAINER = "graphdb"
NEO4J_CONTAINER = "neo4j"
GRAPHDB_JVM_MAIN_CLASS = "GraphDBWorkbench"
NEO4J_JVM_MAIN_CLASS = "Neo4jCommunity"
GRAPHDB_STORE_DIR = f"/opt/graphdb/home/data/repositories/{GRAPHDB_REPOSITORY}"
NEO4J_STORE_DIR = f"/data/databases/{NEO4J_DATABASE}"
NEO4J_TRANSACTION_LOGS_DIR = f"/data/transactions/{NEO4J_DATABASE}"
NEO4J_STOP_TIMEOUT = 120


CONVERSION_RUNS = 10
LOADING_RUNS = 5
QUERY_WARMUP_RUNS = 5
QUERY_RUNS = 50
QUERY_SEED = 42
