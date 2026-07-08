# =======================================================================
# weather-forecast -- JMA weather chart to Salesforce, no cloud required.
# East Van AI -- AI for the rest of us!
# https://github.com/east-van-ai
# ========================================================================
import logging
import os
import sys
from weather_forecast.cli.app import parse_args
from weather_forecast.orchestration.pipeline import WeatherPipeline

logger = logging.getLogger(__name__)


def load_env_values() -> dict:
    env_vars = {
        "client_id": "SF_CLIENT_ID",
        "username": "SF_USERNAME",
        "audience": "SF_AUDIENCE",
        "private_key": "SF_SERVER_KEY",
    }

    config = {k: os.getenv(v) for k, v in env_vars.items()}
    missing = [env_vars[k] for k, v in config.items() if not v]

    return config, missing


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
        sys.exit(1)

    if args.dryrun:
        logger.info("--dryrun enabled (logic not yet implemented)")

    config, missing = load_env_values()
    if missing:
        logger.error(f"Missing required env vars: {missing}")
        sys.exit(1)

    pipeline = WeatherPipeline(force=args.force, config=config)

    try:
        result = pipeline.run()
    except Exception:
        logger.error("Pipeline execution failed with an unexpected error")
        sys.exit(1)

    if result:
        logger.info("Pipeline executed successfully")
    else:
        logger.info("Pipeline skipped execution based on conditions")

    sys.exit(0)


if __name__ == "__main__":
    main()
