from src.cli import parse_args


def test_cli_run_flag():
    """Test that the --run flag is parsed correctly."""
    args = parse_args(["--run"])
    assert args.run is True
