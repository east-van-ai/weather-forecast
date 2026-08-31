"""Argument parsing for weather-forecast's CLI grammar."""

import argparse
from importlib import metadata

# Argparse hardcodes 2 in `ArgumentParser.error()`, which calls `sys.exit`
# itself, so EXIT_ARGPARSE is never returned, only asserted against. See
# DESIGN.md, "Exit codes", for what the three cover.
EXIT_OK = 0
EXIT_ERROR = 1
EXIT_ARGPARSE = 2

PROG = "weather-forecast"

USAGE = "weather-forecast run [--force | --dryrun] | weather-forecast version"


def installed_version() -> str:
    """
    Return the version of the installed weather-forecast distribution.

    A tree that has never been built carries no metadata to read, so the
    lookup is guarded: the parser is built on every invocation past a bare
    word, and an unguarded miss would take down every command, not just this
    one.
    """
    try:
        return metadata.version("weather-forecast")
    except metadata.PackageNotFoundError:
        return "unknown (not installed)"


def version_line() -> str:
    """
    Return the program name and the installed version on one line.

    Both `version` and `--version` answer with this, so the two spellings
    cannot drift apart.
    """
    return f"{PROG} {installed_version()}"


def build_parser() -> argparse.ArgumentParser:
    """
    Construct the argument parser for the whole command surface.

    `--version` is defined on the top-level parser and nowhere else, so
    asking a command for the version is an unknown flag, exit 2. Abbreviation
    is off everywhere: `--dry` must never stand in for `--dryrun`, and
    add_parser() inherits nothing, so each subparser repeats the keyword.
    """
    parser = argparse.ArgumentParser(
        prog=PROG,
        description="JMA weather chart to Salesforce, no cloud required.",
        allow_abbrev=False,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=version_line(),
        help="Print the installed version and exit.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    run_help = "Download the chart, describe it, and upsert it to Salesforce."
    run_parser = subparsers.add_parser(
        "run", help=run_help, description=run_help, allow_abbrev=False
    )
    group = run_parser.add_mutually_exclusive_group()
    group.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="Run even when the PDF is unchanged; useful for demos.",
    )
    group.add_argument(
        "--dryrun",
        action="store_true",
        default=False,
        help="Simulate the run without posting to Salesforce.",
    )

    version_help = "Print the installed version and exit."
    subparsers.add_parser(
        "version", help=version_help, description=version_help, allow_abbrev=False
    )

    return parser
