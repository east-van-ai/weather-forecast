# =======================================================================
# weather-forecast -- JMA weather chart to Salesforce, no cloud required.
# East Van AI -- AI for the rest of us!
# https://github.com/east-van-ai
# ========================================================================
import pytest
from unittest.mock import patch, MagicMock

from weather_forecast.salesforce.base import SalesforceBaseClient

FAKE_PRIVATE_KEY = b"-----BEGIN PRIVATE KEY-----\nFAKEKEY\n-----END PRIVATE KEY-----"
FAKE_ACCESS_TOKEN = "XYZ123456789"
FAKE_INSTANCE_URL = "https://example.salesforce.com"

FAKE_CONFIG = {
    "client_id": "TEST_CLIENT_ID",
    "username": "test@example.com",
    "audience": "https://login.salesforce.com",
    "private_key": FAKE_PRIVATE_KEY,
}


def setup_auth_patches():
    """Return un-started patches so each test activates them cleanly."""
    jwt_patch = patch(
        "weather_forecast.salesforce.base.jwt.encode", return_value="FAKE_JWT"
    )

    post_patch = patch("weather_forecast.salesforce.base.requests.post")
    sf_patch = patch("weather_forecast.salesforce.base.Salesforce")

    return jwt_patch, post_patch, sf_patch


def make_post_mock(post_mock):
    """Configure a post mock with standard fake token response."""
    post_mock.return_value.json.return_value = {
        "access_token": FAKE_ACCESS_TOKEN,
        "instance_url": FAKE_INSTANCE_URL,
    }
    post_mock.return_value.raise_for_status = lambda: None


# -------------------------------
# Test: authentication
# -------------------------------
def test_salesforce_auth():
    jwt_p, post_p, sf_p = setup_auth_patches()

    with jwt_p, post_p as post_mock, sf_p as sf_mock:
        make_post_mock(post_mock)

        client = SalesforceBaseClient(config=FAKE_CONFIG)

        sf_mock.assert_called_once_with(
            session_id=FAKE_ACCESS_TOKEN,
            instance_url=FAKE_INSTANCE_URL,
        )
        assert client.sf is sf_mock.return_value


# -------------------------------
# Test: query
# -------------------------------
def test_salesforce_query():
    jwt_p, post_p, sf_p = setup_auth_patches()

    fake_sf = MagicMock()
    fake_sf.query.return_value = {"records": [{"Id": "001"}]}

    with jwt_p, post_p as post_mock, sf_p as sf_mock:
        make_post_mock(post_mock)
        sf_mock.return_value = fake_sf

        client = SalesforceBaseClient(config=FAKE_CONFIG)
        result = client.query("SELECT Id FROM Account")

        assert result == [{"Id": "001"}]
        fake_sf.query.assert_called_once()


# -------------------------------
# Test: create / update / get
# -------------------------------
class FakeSF:
    """Simple substitute for Salesforce() that returns same object for any sObject."""

    def __init__(self, obj):
        self._obj = obj

    def __getattr__(self, name):
        return self._obj


def test_salesforce_base_client_crud():
    jwt_p, post_p, sf_p = setup_auth_patches()

    fake_obj = MagicMock()
    fake_obj.create.return_value = {"id": "NEW_ID"}
    fake_obj.update.return_value = True
    fake_obj.get.return_value = {"Id": "REC_ID"}

    fake_sf = FakeSF(fake_obj)

    with jwt_p, post_p as post_mock, sf_p as sf_mock:
        make_post_mock(post_mock)
        sf_mock.return_value = fake_sf

        client = SalesforceBaseClient(config=FAKE_CONFIG)

        assert client.create("Weather_Report__c", {"PDF_Hash__c": "aaa"}) == {
            "id": "NEW_ID"
        }
        fake_obj.create.assert_called_once()

        assert (
            client.update("Weather_Report__c", "REC_ID", {"Forecast__c": "Rain"})
            is True
        )
        fake_obj.update.assert_called_once()

        assert client.get("Weather_Report__c", "REC_ID") == {"Id": "REC_ID"}
        fake_obj.get.assert_called_once()


def test_salesforce_base_client_upsert():
    jwt_p, post_p, sf_p = setup_auth_patches()

    fake_obj = MagicMock()
    fake_obj.upsert.return_value = "201"  # created

    fake_sf = FakeSF(fake_obj)

    with jwt_p, post_p as post_mock, sf_p as sf_mock:
        make_post_mock(post_mock)
        sf_mock.return_value = fake_sf

        client = SalesforceBaseClient(config=FAKE_CONFIG)

        client.query = MagicMock(return_value=[{"Id": "UPSERT_ID"}])

        result = client.upsert(
            object_name="Weather_Report__c",
            external_id_field="PDF_Hash__c",
            external_id_value="aaa",
            fields={"Name": "DEV Weather Report"},
        )

        fake_obj.upsert.assert_called_once_with(
            "PDF_Hash__c/aaa",
            {"Name": "DEV Weather Report"},
        )

        assert result == {
            "created": True,
            "record_id": "UPSERT_ID",
        }
