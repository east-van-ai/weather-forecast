# =======================================================================
# weather-forecast -- JMA weather chart to Salesforce, no cloud required.
# East Van AI -- AI for the rest of us!
# https://github.com/east-van-ai
# ========================================================================
import pytest
from weather_forecast.main import load_env_values


@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("SF_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("SF_USERNAME", "test@example.com")
    monkeypatch.setenv("SF_AUDIENCE", "https://login.salesforce.com")
    monkeypatch.setenv(
        "SF_SERVER_KEY",
        "-----BEGIN RSA PRIVATE KEY-----\nfakekey\n-----END RSA PRIVATE KEY-----",
    )


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
