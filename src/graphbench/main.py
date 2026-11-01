import logging

from .benchmark.pipeline import run_conversion, run_loading
from .benchmark.reporting import create_run_dir, save_timings

CONVERSION_RUNS = 5
LOADING_RUNS = 1

logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )
    run_dir = create_run_dir()
    logger.info("Run folder: %s", run_dir)

    # order matter since loading will use the output of conversion
    pipeline = run_conversion(runs=CONVERSION_RUNS) + run_loading(runs=LOADING_RUNS)
    save_timings(pipeline, run_dir, "pipeline")

    logger.info("Results saved to %s", run_dir)


if __name__ == "__main__":
    main()
