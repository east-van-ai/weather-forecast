import builtins
import pytest
from unittest.mock import patch, MagicMock

from src.salesforce.weather import ReportUpsertResult, SFWeatherClient


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


def test_upsert_report_created(mock_env):
    """Upsert creates a new Weather_Report__c when PDF hash is new"""
    open_p, jwt_p, post_p, sf_p = setup_auth_patches()

    with open_p, jwt_p, post_p as post_mock, sf_p as sf_mock:
        post_mock.return_value.json.return_value = {
            "access_token": FAKE_ACCESS_TOKEN,
            "instance_url": FAKE_INSTANCE_URL,
        }
        post_mock.return_value.raise_for_status = lambda: None

        sf_mock.return_value = MagicMock()

        client = SFWeatherClient()

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


def test_upsert_report_updated(mock_env):
    """Upsert updates an existing Weather_Report__c when PDF hash exists"""
    open_p, jwt_p, post_p, sf_p = setup_auth_patches()

    with open_p, jwt_p, post_p as post_mock, sf_p as sf_mock:
        post_mock.return_value.json.return_value = {
            "access_token": FAKE_ACCESS_TOKEN,
            "instance_url": FAKE_INSTANCE_URL,
        }
        post_mock.return_value.raise_for_status = lambda: None

        sf_mock.return_value = MagicMock()

        client = SFWeatherClient()

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


def test_ensure_preview_image_skips_if_already_exists(mock_env, tmp_path):
    """If a preview image with the same Title already exists, do nothing."""
    open_p, jwt_p, post_p, sf_p = setup_auth_patches()

    # fake image file
    img = tmp_path / "small.png"
    img.write_bytes(b"fake-image")

    with open_p, jwt_p, post_p as post_mock, sf_p as sf_mock:
        post_mock.return_value.json.return_value = {
            "access_token": FAKE_ACCESS_TOKEN,
            "instance_url": FAKE_INSTANCE_URL,
        }
        post_mock.return_value.raise_for_status = lambda: None

        fake_sf = MagicMock()
        sf_mock.return_value = fake_sf

        client = SFWeatherClient()

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


def test_ensure_preview_image_uploads_if_missing(mock_env, tmp_path):
    """Uploads preview image when no matching ContentVersion exists."""
    _, jwt_p, post_p, sf_p = setup_auth_patches()

    img = tmp_path / "small.png"
    img.write_bytes(b"fake-image")

    with jwt_p, post_p as post_mock, sf_p as sf_mock:
        post_mock.return_value.json.return_value = {
            "access_token": FAKE_ACCESS_TOKEN,
            "instance_url": FAKE_INSTANCE_URL,
        }
        post_mock.return_value.raise_for_status = lambda: None

        fake_sf = MagicMock()
        fake_sf.ContentVersion.create.return_value = {"id": "CV_NEW"}
        sf_mock.return_value = fake_sf

        # bypass auth init completely
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
