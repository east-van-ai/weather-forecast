import pytest
from pathlib import Path
from src.downloader import WeatherPDFDownloader
from unittest.mock import patch, MagicMock


class DummyDL(WeatherPDFDownloader):
    """Extending a class and override methods for testing."""

    def __init__(self, data_dir, contents):
        super().__init__(data_dir, weather_pdf_url="dummy")
        self.fake_contents = contents
        self.calls = 0

    def _download(self):
        """Simulate downloading by writing predefined content."""
        self.calls += 1
        with self.current_pdf_path.open("wb") as f:
            f.write(self.fake_contents[self.calls - 1])


def test_case_A(tmp_path):
    """Case A: neither exists"""
    # tmp_path is a pytest fixture providing a temporary directory
    dl = DummyDL(tmp_path, [b"PDF-A"])

    changed, pdf_hash = dl.update()

    assert changed is True
    assert dl._exists(dl.current_pdf_path)
    assert not dl._exists(dl.last_pdf_path)


def test_case_B(tmp_path):
    """Case B: only current exists"""
    # tmp_path is a pytest fixture providing a temporary directory
    current_pdf_path = tmp_path / WeatherPDFDownloader.CURRENT_PDF
    current_pdf_path.write_bytes(b"OLD")

    dl = DummyDL(tmp_path, [b"NEW"])
    changed, pdf_hash = dl.update()

    # After rename: last.pdf=OLD, current.pdf=NEW
    assert (tmp_path / WeatherPDFDownloader.LAST_PDF).read_bytes() == b"OLD"
    assert (tmp_path / WeatherPDFDownloader.CURRENT_PDF).read_bytes() == b"NEW"
    assert changed is True


def test_case_C_no_change(tmp_path):
    """Case C: only last exists. New download is the same as last."""
    last = tmp_path / WeatherPDFDownloader.LAST_PDF
    last.write_bytes(b"SAME")

    dl = DummyDL(tmp_path, [b"SAME"])
    changed, pdf_hash = dl.update()

    assert changed is False
    assert (tmp_path / WeatherPDFDownloader.LAST_PDF).read_bytes() == b"SAME"
    assert not (tmp_path / WeatherPDFDownloader.CURRENT_PDF).exists()


def test_case_C_change(tmp_path):
    """Case C: only last exists. New download is different from last."""
    last = tmp_path / WeatherPDFDownloader.LAST_PDF
    last.write_bytes(b"OLD")

    dl = DummyDL(tmp_path, [b"NEW"])
    changed, pdf_hash = dl.update()

    assert changed is True
    assert (tmp_path / WeatherPDFDownloader.LAST_PDF).read_bytes() == b"OLD"
    assert (tmp_path / WeatherPDFDownloader.CURRENT_PDF).read_bytes() == b"NEW"


def test_case_D_no_change(tmp_path):
    """Case D: both exists. New download is the same as current."""
    last = tmp_path / WeatherPDFDownloader.LAST_PDF
    last.write_bytes(b"LAST")
    current = tmp_path / WeatherPDFDownloader.CURRENT_PDF
    current.write_bytes(b"CURRENT")

    dl = DummyDL(tmp_path, [b"CURRENT"])
    changed, pdf_hash = dl.update()

    assert changed is False
    assert (tmp_path / WeatherPDFDownloader.LAST_PDF).read_bytes() == b"CURRENT"
    assert not (tmp_path / WeatherPDFDownloader.CURRENT_PDF).exists()


def test_case_D_change(tmp_path):
    """Case D: both exists. New download is different from current."""
    last = tmp_path / WeatherPDFDownloader.LAST_PDF
    last.write_bytes(b"LAST")
    current = tmp_path / WeatherPDFDownloader.CURRENT_PDF
    current.write_bytes(b"CURRENT")

    dl = DummyDL(tmp_path, [b"NEWER"])
    changed, pdf_hash = dl.update()

    assert changed is True
    assert (tmp_path / WeatherPDFDownloader.LAST_PDF).read_bytes() == b"CURRENT"
    assert (tmp_path / WeatherPDFDownloader.CURRENT_PDF).read_bytes() == b"NEWER"


def test_create_png(tmp_path):
    # Arrange: create a downloader with temp directory
    dl = WeatherPDFDownloader(tmp_path, weather_pdf_url="dummy.url")

    # Create fake current.pdf so the path exists
    dl.current_pdf_path.write_bytes(b"%PDF-1.4 fake")

    # Mock: fake page with .save() method
    fake_page = MagicMock()
    fake_pages = [fake_page]

    with patch(
        "src.downloader.convert_from_path", return_value=fake_pages
    ) as conv_mock:
        # Act
        dl.create_png()

    # Assert convert_from_path was called correctly
    conv_mock.assert_called_once_with(dl.current_pdf_path)

    # Assert .save() called on first page
    expected_png_path = tmp_path / dl.WEATHER_PNG
    fake_page.save.assert_called_once_with(expected_png_path)
