"""
# ==============================================
# East Van AI -- AI for the rest of us!
# https://github.com/east-van-ai
# contact: east-van-ai@proton.me
# ==============================================
#
# ~~~ ~~~ ~~~ ~~~ weather-forecast ~~~ ~~~ ~~~ ~~~
#
# JMA weather chart to Salesforce, no cloud required.
# Downloads the JMA surface analysis PDF, runs it through a local
# vision-language model (LLaVA Interleave Qwen 0.5B) on Apple Silicon,
# and upserts the forecast + preview image into a Salesforce org.
#
# Usage:
#   weather-forecast --run
#   weather-forecast --run --force
#   weather-forecast --run --dryrun
#
# --run     Required to execute; guards against accidental runs.
# --force   Bypass the PDF-unchanged skip (mutually exclusive with --dryrun).
# --dryrun  Simulate without posting to Salesforce (not yet implemented).
#
# Environment:
#   SF_USERNAME, SF_CLIENT_ID, SF_AUDIENCE, SF_SERVER_KEY  (required)
#   WF_VISION_MODEL  (optional HF model id override)
#
# Exit codes:
#   0  success, run skipped (PDF unchanged), or bare invocation (banner shown)
#   1  missing --run, missing env vars, or pipeline error
#
# License: MIT
# ==============================================
"""

import argparse
import logging
import os
import sys
from weather_forecast.orchestration.pipeline import WeatherPipeline

logger = logging.getLogger(__name__)


def parse_args(argv=None):
    """
    Parse command-line arguments and return an argparse.Namespace.

    Parameters:
        argv (list[str] or None):
            When None, argparse reads from the real command line (sys.argv).
            Tests can pass a custom list (e.g., ["--run"]) to avoid executing
            the full program or triggering side effects.

    Returns:
        argparse.Namespace: Parsed command-line options.
    """
    parser = argparse.ArgumentParser(description="Weather Forecast + Salesforce")

    parser.add_argument(
        "--run",
        action="store_true",
        help="Required to execute; prevents accidental execution.",
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="Force execution without checking fingerprints; useful for demos.",
    )
    group.add_argument(
        "--dryrun",
        action="store_true",
        default=False,
        help="Simulate the run without posting to Salesforce.",
    )

    return parser.parse_args(argv)


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


def main():
    """
    Entry point for the `weather-forecast` command.

    Parses arguments, validates the environment, runs the pipeline, and
    exits 0 on success or skip, 1 on any error. Invoked bare, it prints
    the banner and exits 0 without touching anything.
    """
    # bare invocation on a TTY: print the banner, touch nothing
    if len(sys.argv) == 1:
        print(__doc__)
        sys.exit(0)

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
