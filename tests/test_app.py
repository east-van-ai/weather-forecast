# =======================================================================
# weather-forecast -- JMA weather chart to Salesforce, no cloud required.
# East Van AI -- AI for the rest of us!
# https://github.com/east-van-ai
# ========================================================================
from weather_forecast.cli.app import parse_args


def test_cli_run_flag():
    """Test that the --run flag is parsed correctly."""
    args = parse_args(["--run"])
    assert args.run is True
