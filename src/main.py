# Weather Forecast + Salesforce
#
# License:
#   MIT License
#
# Enjoy coding! 🛸
# ==========================================
import logging
from src.cli.app import parse_args
from src.orchestration.pipeline import WeatherPipeline

logger = logging.getLogger(__name__)


def main():
    args = parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )

    logger.info(
        "Execution started (run=%s, force=%s, dryrun=%s)",
        args.run,
        args.force,
        args.dryrun,
    )

    if not args.run:
        logger.error("Missing --run flag; aborting execution")
        raise SystemExit("Error: Missing --run. This flag is required.")

    if args.dryrun:
        logger.info("--dryrun enabled (logic not yet implemented)")

    pipeline = WeatherPipeline(force=args.force)

    try:
        result = pipeline.run()
    except Exception:
        logger.exception("Pipeline execution failed with an unexpected error")
        raise

    if result:
        logger.info("Pipeline executed successfully")
    else:
        logger.info("Pipeline skipped execution based on conditions")


if __name__ == "__main__":
    main()
