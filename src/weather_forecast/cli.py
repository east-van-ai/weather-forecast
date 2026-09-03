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
# vision-language model (SmolVLM2 500M) on Apple Silicon, and upserts
# the description + preview image into a Salesforce org.
#
# Usage:
#
#    weather-forecast run --dry-run [--force]
#    weather-forecast run --commit [--force]
#
# Commands:
#
#    run                 download the chart, describe it, and upsert it
#                        to Salesforce. A PDF unchanged since the last
#                        run is skipped.
#
# Options:
#
#    --dry-run           describe the chart and stop before Salesforce
#    --commit            post the description and the preview image
#    --force             run even when the PDF is unchanged
#
# run takes one of --dry-run or --commit, and neither is a default.
# Nothing is written unless --commit is passed. Run the command with
# nothing else after it for its own documentation:
#
#    weather-forecast run
#
# Flags follow the command word, and their order among themselves is
# free. Spell them in full: an abbreviation like `--com` is rejected, so
# it can never stand in for `--commit`.
#
# weather-forecast reads no piped input.
#
# Environment:
#
#    SF_USERNAME, SF_CLIENT_ID, SF_AUDIENCE, SF_SERVER_KEY  (all required)
#
# Exit codes:
#
#    0:     success, a run skipped because the PDF is unchanged, and
#           documentation
#    1:     weather-forecast's own error, a stray word after a command,
#           a run with no mode flag, a missing environment variable, or
#           a pipeline failure
#    2:     an unknown command, an unknown flag, or a bad value
#
# License: MIT
# ==============================================
"""

import sys

from weather_forecast import cli_run
from weather_forecast.args import (
    EXIT_ARGPARSE,
    EXIT_ERROR,
    EXIT_OK,
    USAGE,
    build_parser,
    version_line,
)

__all__ = ["EXIT_ARGPARSE", "EXIT_ERROR", "EXIT_OK", "main"]


def show_version(args) -> int:
    """Print the program name and the installed version."""
    print(version_line())
    return EXIT_OK


# Callables rather than modules: `run` has a surface module of its own,
# `version` is one print and lives here beside the table.
COMMANDS = {
    "run": cli_run.run,
    "version": show_version,
}

# What a lone command word answers with. `version` is absent on purpose: it
# has no mode and takes no argument, so the word alone is a complete line.
DOCS = {
    "run": cli_run.__doc__,
}


def leading_paths(tokens):
    """Return the tokens ahead of the first flag.

    The documented grammar puts every positional before every flag, so the
    slot is read off the front of the command line. What argparse resolved
    from anywhere else is discarded, since how much it tolerates depends on
    the interpreter. See DESIGN.md, "Positions are decided, not inferred".
    """
    paths = []
    for token in tokens:
        if token.startswith("-"):
            break
        paths.append(token)
    return paths


def usage_error(message) -> int:
    """Report a command line weather-forecast could not read, with its usage.

    Grammar errors only. A readiness failure, a missing environment variable,
    prints no usage line: the command line was read fine, and usage beside it
    would answer a question nobody asked.
    """
    print(f"weather-forecast: {message}", file=sys.stderr)
    print(f"Usage: {USAGE}", file=sys.stderr)
    return EXIT_ERROR


def main():
    """Parse arguments, enforce the CLI grammar, and dispatch to a command.

    A bare invocation is a question and gets the banner, and a lone command
    word gets that command's own documentation. Both exit 0. The test is the
    token count, never a missing argument: once any other token is present the
    user asked for something specific, and answering with documentation would
    hide the mistake.

    Neither command takes an argument, so any bare word after the command word
    is a stray and gets an error, exit 1, as does a run with neither mode flag.
    Argparse keeps the vocabulary it owns: an unknown command, an unknown flag,
    or a bad value, exiting 2.
    """
    tokens = sys.argv[1:]

    if not tokens:
        print(__doc__.strip())
        return EXIT_OK

    # A command word and nothing else at all.
    if len(tokens) == 1 and tokens[0] in DOCS:
        print(DOCS[tokens[0]].strip())
        return EXIT_OK

    parser = build_parser()
    args, extras = parser.parse_known_args(tokens)

    if any(extra.startswith("-") for extra in extras):
        parser.parse_args(tokens)  # argparse names the flag better, exit 2

    # The slot ahead of the first flag, plus argparse's leftovers.
    strays = leading_paths(tokens[1:]) or [
        extra for extra in extras if not extra.startswith("-")
    ]
    if strays:
        return usage_error(f"{args.command} takes no argument: {strays[0]!r}")

    # Here rather than on the parser, so a missing mode is exit 1, not 2.
    if args.command == "run" and not (args.dry_run or args.commit):
        return usage_error("run takes one of --dry-run or --commit")

    return COMMANDS[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
