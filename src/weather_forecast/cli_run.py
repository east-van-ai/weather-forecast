"""
# ~~~ ~~~ ~~~ ~~~ weather-forecast run ~~~ ~~~ ~~~ ~~~
#
# Download the latest JMA surface analysis PDF, render page 1, describe it
# with a local vision model, and upsert the description plus a preview image
# into Salesforce. A PDF whose hash matches the last run is skipped, so a
# repeat run costs a download and nothing else.
#
# Usage:
#
#    weather-forecast run [--force | --dryrun]
#
# Options:
#
#    --force             run even when the PDF is unchanged
#    --dryrun            simulate without posting to Salesforce
#                        (not yet implemented)
#
# Environment:
#
#    SF_USERNAME, SF_CLIENT_ID, SF_AUDIENCE, SF_SERVER_KEY  (all required)
"""

import logging
import os

from weather_forecast.args import EXIT_ERROR, EXIT_OK
from weather_forecast.orchestration.pipeline import WeatherPipeline

logger = logging.getLogger(__name__)


def load_env_values() -> tuple[dict, list]:
    """
    Read the Salesforce JWT settings from the environment.

    Returns a (config, missing) tuple: config maps internal keys to the
    values of the SF_* environment variables, and missing lists the names
    of any variables that are unset or empty.
    """
    env_vars = {
        "client_id": "SF_CLIENT_ID",
        "username": "SF_USERNAME",
        "audience": "SF_AUDIENCE",
        "private_key": "SF_SERVER_KEY",
    }

    config = {k: os.getenv(v) for k, v in env_vars.items()}
    missing = [env_vars[k] for k, v in config.items() if not v]

    return config, missing


def run(args) -> int:
    """
    Validate the environment and run the pipeline.

    Logging is configured here rather than in main(), so `version` answers
    with one line and no log preamble above it. A missing environment
    variable is a readiness failure: it reports and exits 1 with no usage
    line, since the command line itself was fine.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )

    logger.info("Execution started (force=%s, dryrun=%s)", args.force, args.dryrun)

    if args.dryrun:
        logger.info("--dryrun enabled (logic not yet implemented)")

    config, missing = load_env_values()
    if missing:
        logger.error(f"Missing required env vars: {missing}")
        return EXIT_ERROR

    pipeline = WeatherPipeline(force=args.force, config=config)

    try:
        result = pipeline.run()
    except Exception:
        logger.error("Pipeline execution failed with an unexpected error")
        return EXIT_ERROR

    if result:
        logger.info("Pipeline executed successfully")
    else:
        logger.info("Pipeline skipped execution based on conditions")

    return EXIT_OK
