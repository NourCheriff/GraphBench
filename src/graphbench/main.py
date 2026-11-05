import logging

from .analysis.sna import compute_sna
from .benchmark.latency import run_latency
from .benchmark.pipeline import run_conversion, run_loading
from .benchmark.plots import plot_run
from .benchmark.reporting import create_run_dir, save_rows, save_timings
from .benchmark.storage import measure_storage
from .settings import CONVERSION_RUNS, LOADING_RUNS, QUERY_RUNS, QUERY_WARMUP_RUNS

logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )
    # the driver logs every failed attempt while Neo4j restarts; errors still raise
    logging.getLogger("neo4j").setLevel(logging.CRITICAL)
    run_dir = create_run_dir()
    logger.info("Run folder: %s", run_dir)

    # order matter since loading will use the output of conversion
    pipeline = run_conversion(runs=CONVERSION_RUNS) + run_loading(runs=LOADING_RUNS)
    save_timings(pipeline, run_dir, "pipeline")

    # measured once, right after loading
    save_rows(measure_storage(), run_dir, "storage")

    save_rows(compute_sna(), run_dir, "sna")

    latency = run_latency(warmup=QUERY_WARMUP_RUNS, runs=QUERY_RUNS)
    save_timings(latency, run_dir, "query_latency")

    plot_run(run_dir)

    logger.info("Results saved to %s", run_dir)


if __name__ == "__main__":
    main()
