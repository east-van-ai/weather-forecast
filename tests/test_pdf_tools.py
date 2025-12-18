# tests/test_pdf_tools.py
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.chart.processors.pdf_tools import pdf_to_png


def test_pdf_to_png(tmp_path):
    # fake paths
    pdf_path = tmp_path / "test.pdf"
    png_path = tmp_path / "out.png"

    # create fake PDF file
    pdf_path.write_bytes(b"%PDF fake content")

    # mock convert_from_path to avoid real PDF processing
    mock_image = MagicMock()
    mock_image.save = MagicMock()

    with patch(
        "src.chart.processors.pdf_tools.convert_from_path", return_value=[mock_image]
    ) as mock_convert:
        output = pdf_to_png(pdf_path, png_path)

    # Assertions
    mock_convert.assert_called_once_with(pdf_path)
    mock_image.save.assert_called_once_with(png_path)
    assert output == png_path
