import builtins
import pytest
from unittest.mock import patch, MagicMock

from src.salesforce.weather import SFWeatherClient


FAKE_PRIVATE_KEY = b"-----BEGIN PRIVATE KEY-----\nFAKEKEY\n-----END PRIVATE KEY-----"
FAKE_ACCESS_TOKEN = "XYZ123456789"
FAKE_INSTANCE_URL = "https://example.salesforce.com"


@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("SF_CLIENT_ID", "TEST_CLIENT_ID")
    monkeypatch.setenv("SF_USERNAME", "test@example.com")
    monkeypatch.setenv("SF_AUDIENCE", "https://login.salesforce.com")
    monkeypatch.setenv("SF_PRIVATE_KEY_PATH", "/fake/key.pem")


def setup_auth_patches():
    """Return un-started patches so each test activates them cleanly."""
    open_patch = patch.object(
        builtins, "open", return_value=MagicMock(read=lambda: FAKE_PRIVATE_KEY)
    )

    jwt_patch = patch("src.salesforce.base.jwt.encode", return_value="FAKE_JWT")

    post_patch = patch("src.salesforce.base.requests.post")
    sf_patch = patch("src.salesforce.base.Salesforce")

    return open_patch, jwt_patch, post_patch, sf_patch


def test_find_or_create_records_1(mock_env):
    """Case 1: First query returns nothing (record missing)"""
    open_p, jwt_p, post_p, sf_p = setup_auth_patches()

    with open_p, jwt_p, post_p as post_mock, sf_p as sf_mock:
        post_mock.return_value.json.return_value = {
            "access_token": FAKE_ACCESS_TOKEN,
            "instance_url": FAKE_INSTANCE_URL,
        }
        post_mock.return_value.raise_for_status = lambda: None

        sf_mock.return_value = MagicMock()

        client = SFWeatherClient()

        with patch.object(client, "query") as mock_query, patch.object(
            client, "create"
        ) as mock_create:

            pdf_hash = "abc123"

            mock_query.side_effect = [
                [],  # first query: no record
                [
                    {"Id": "001", "PDF_Hash__c": pdf_hash}
                ],  # second query: record created
            ]

            results = client.find_or_create_report(pdf_hash)

            # verify creation happened
            mock_create.assert_called_once_with(
                "Weather_Report__c",
                {"Name": "DEV Weather Report", "PDF_Hash__c": pdf_hash},
            )

            assert results == [{"Id": "001", "PDF_Hash__c": pdf_hash}]


def test_find_or_create_records_2(mock_env):
    """Case 2: Record already exists"""
    open_p, jwt_p, post_p, sf_p = setup_auth_patches()

    with open_p, jwt_p, post_p as post_mock, sf_p as sf_mock:
        post_mock.return_value.json.return_value = {
            "access_token": FAKE_ACCESS_TOKEN,
            "instance_url": FAKE_INSTANCE_URL,
        }
        post_mock.return_value.raise_for_status = lambda: None

        sf_mock.return_value = MagicMock()

        client = SFWeatherClient()

        with patch.object(client, "query") as mock_query, patch.object(
            client, "create"
        ) as mock_create:

            pdf_hash = "abc123"

            mock_query.return_value = [{"Id": "existing", "PDF_Hash__c": pdf_hash}]

            results = client.find_or_create_report(pdf_hash)

            # No creation this time
            mock_create.assert_not_called()
            assert results == [{"Id": "existing", "PDF_Hash__c": pdf_hash}]
