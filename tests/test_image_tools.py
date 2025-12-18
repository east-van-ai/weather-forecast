# tests/test_image_tools.py
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.chart.processors.image_tools import resize_png


def test_resize_png(tmp_path):
    src = tmp_path / "in.png"
    dst = tmp_path / "out.png"

    # create fake PNG
    src.write_bytes(b"fake png")

    # mock PIL Image.open
    mock_img = MagicMock()
    mock_img.size = (600, 400)  # width, height
    mock_img.resize = MagicMock(return_value=mock_img)
    mock_img.save = MagicMock()

    with patch(
        "src.chart.processors.image_tools.Image.open", return_value=mock_img
    ) as mock_open, patch("src.chart.processors.image_tools.Image.LANCZOS", 99):
        output = resize_png(src, dst, width=300)

    # Assertions
    mock_open.assert_called_once_with(src)
    mock_img.resize.assert_called_once_with((300, 200), 99)
    mock_img.save.assert_called_once_with(dst, optimize=True)
    assert output == dst
