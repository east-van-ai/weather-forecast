# =======================================================================
# weather-forecast -- JMA weather chart to Salesforce, no cloud required.
# East Van AI -- AI for the rest of us!
# https://github.com/east-van-ai
# ========================================================================
from importlib import metadata

import pytest

from weather_forecast.args import build_parser, installed_version, version_line
from weather_forecast.cli_run import load_env_values


@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("SF_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("SF_USERNAME", "test@example.com")
    monkeypatch.setenv("SF_AUDIENCE", "https://login.salesforce.com")
    monkeypatch.setenv(
        "SF_SERVER_KEY",
        "-----BEGIN RSA PRIVATE KEY-----\nfakekey\n-----END RSA PRIVATE KEY-----",
    )


def test_run_command_defaults():
    """Test that `run` alone parses with both mode flags off."""
    args = build_parser().parse_args(["run"])
    assert args.command == "run"
    assert args.force is False
    assert args.dryrun is False


def test_run_command_force():
    """Test that --force is parsed onto the run command."""
    args = build_parser().parse_args(["run", "--force"])
    assert args.force is True
    assert args.dryrun is False


def test_run_command_dryrun():
    """Test that --dryrun is parsed onto the run command."""
    args = build_parser().parse_args(["run", "--dryrun"])
    assert args.dryrun is True
    assert args.force is False


def test_version_line_names_the_program():
    """Test that the version line carries the program name and the number."""
    assert version_line() == f"weather-forecast {installed_version()}"


def test_installed_version_without_metadata(monkeypatch):
    """Test that a missing distribution reports rather than raises."""

    def raise_not_found(name):
        raise metadata.PackageNotFoundError(name)

    monkeypatch.setattr(metadata, "version", raise_not_found)
    assert installed_version() == "unknown (not installed)"


def test_load_env_values_all_present(mock_env):
    result, missing = load_env_values()
    assert result["client_id"] == "test-client-id"
    assert result["username"] == "test@example.com"
    assert result["audience"] == "https://login.salesforce.com"
    assert result["private_key"].startswith("-----BEGIN")


def test_load_env_values_missing_client_id(monkeypatch):
    monkeypatch.delenv("SF_CLIENT_ID", raising=False)
    result, missing = load_env_values()
    assert result["client_id"] is None


def test_load_env_values_missing_all(monkeypatch):
    for key in ["SF_CLIENT_ID", "SF_USERNAME", "SF_AUDIENCE", "SF_SERVER_KEY"]:
        monkeypatch.delenv(key, raising=False)
    result, missing = load_env_values()
    assert all(v is None for v in result.values())
