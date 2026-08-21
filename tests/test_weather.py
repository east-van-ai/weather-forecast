# =======================================================================
# weather-forecast -- JMA weather chart to Salesforce, no cloud required.
# East Van AI -- AI for the rest of us!
# https://github.com/east-van-ai
# ========================================================================
from unittest.mock import patch, MagicMock

from weather_forecast.salesforce.weather import ReportUpsertResult, SFWeatherClient

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


def test_upsert_report_created():
    """Upsert creates a new Weather_Report__c when PDF hash is new."""
    jwt_p, post_p, sf_p = setup_auth_patches()

    with jwt_p, post_p as post_mock, sf_p as sf_mock:
        make_post_mock(post_mock)
        sf_mock.return_value = MagicMock()

        client = SFWeatherClient(config=FAKE_CONFIG)

        with patch.object(client, "upsert") as mock_upsert:
            mock_upsert.return_value = {
                "record_id": "001NEW",
                "created": True,
            }

            result = client.upsert_report(
                pdf_hash="abc123",
                forecast_text="Rainy",
            )

            mock_upsert.assert_called_once_with(
                "Weather_Report__c",
                external_id_field="PDF_Hash__c",
                external_id_value="abc123",
                fields={
                    "Name": "DEV Weather Report",
                    "Forecast__c": "Rainy",
                },
            )

            assert result == ReportUpsertResult(
                record_id="001NEW",
                created=True,
            )


def test_upsert_report_updated():
    """Upsert updates an existing Weather_Report__c when PDF hash exists."""
    jwt_p, post_p, sf_p = setup_auth_patches()

    with jwt_p, post_p as post_mock, sf_p as sf_mock:
        make_post_mock(post_mock)
        sf_mock.return_value = MagicMock()

        client = SFWeatherClient(config=FAKE_CONFIG)

        with patch.object(client, "upsert") as mock_upsert:
            mock_upsert.return_value = {
                "record_id": "001EXISTING",
                "created": False,
            }

            result = client.upsert_report(
                pdf_hash="abc123",
                forecast_text="Sunny",
            )

            mock_upsert.assert_called_once()

            assert result == ReportUpsertResult(
                record_id="001EXISTING",
                created=False,
            )


def test_ensure_preview_image_skips_if_already_exists(tmp_path):
    """If a preview image with the same Title already exists, do nothing."""
    jwt_p, post_p, sf_p = setup_auth_patches()

    img = tmp_path / "small.png"
    img.write_bytes(b"fake-image")

    with jwt_p, post_p as post_mock, sf_p as sf_mock:
        make_post_mock(post_mock)
        fake_sf = MagicMock()
        sf_mock.return_value = fake_sf

        client = SFWeatherClient(config=FAKE_CONFIG)

        # query is called twice:
        # 1) ContentDocumentLink
        # 2) ContentVersion
        client.query = MagicMock(
            side_effect=[
                [{"ContentDocumentId": "CD1"}],
                [{"Title": "small"}],
            ]
        )

        result = client.ensure_preview_image(
            record_id="REC123",
            file_path=str(img),
        )

        assert result is None
        fake_sf.ContentVersion.create.assert_not_called()


def test_ensure_preview_image_uploads_if_missing(tmp_path):
    """Uploads preview image when no matching ContentVersion exists."""
    img = tmp_path / "small.png"
    img.write_bytes(b"fake-image")

    fake_sf = MagicMock()
    fake_sf.ContentVersion.create.return_value = {"id": "CV_NEW"}

    with patch.object(SFWeatherClient, "__init__", lambda self: None):
        client = SFWeatherClient()
        client.sf = fake_sf

        client.query = MagicMock(
            side_effect=[
                [{"ContentDocumentId": "CD1"}],
                [],  # no ContentVersion
            ]
        )

        result = client.ensure_preview_image(
            record_id="REC123",
            file_path=str(img),
        )

        assert result == "CV_NEW"
        fake_sf.ContentVersion.create.assert_called_once()
