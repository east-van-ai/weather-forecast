import argparse


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
