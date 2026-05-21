# =======================================================================
# weather-forecast -- JMA weather chart to Salesforce, no cloud required.
# East Van AI -- AI for the rest of us!
# https://github.com/east-van-ai
# ========================================================================
import torch
import pytest
from PIL import Image
from unittest.mock import MagicMock, patch

from src.weather_forecast.forecast.generator import WeatherVision


@pytest.fixture
def fake_image(tmp_path):
    """
    Create a temporary PNG image for testing.
    """
    img_path = tmp_path / "test.png"
    img = Image.new("RGB", (64, 64), color="blue")
    img.save(img_path)
    return img_path


@patch("src.weather_forecast.forecast.generator.AutoProcessor")
@patch("src.weather_forecast.forecast.generator.AutoModelForImageTextToText")
# @patch("src.weather_forecast.forecast.generator.Qwen2VLForConditionalGeneration")
def test_weather_vision_init_cpu(
    mock_model_cls,
    mock_processor_cls,
):
    """
    Ensure WeatherVision initializes on CPU when MPS is unavailable.
    """
    with patch("torch.backends.mps.is_available", return_value=False):
        processor = MagicMock()
        model = MagicMock()

        mock_processor_cls.from_pretrained.return_value = processor
        mock_model_cls.from_pretrained.return_value = model

        wv = WeatherVision()

        assert wv.device.type == "cpu"
        mock_processor_cls.from_pretrained.assert_called_once()
        mock_model_cls.from_pretrained.assert_called_once()
        model.to.assert_called_once_with(wv.device)
        model.eval.assert_called_once()


@patch("src.weather_forecast.forecast.generator.AutoProcessor")
@patch("src.weather_forecast.forecast.generator.AutoModelForImageTextToText")
# @patch("src.weather_forecast.forecast.generator.Qwen2VLForConditionalGeneration")
def test_generate_forecast(
    mock_model_cls,
    mock_processor_cls,
    fake_image,
):
    """
    Test forecast generation flow with mocked model + processor.
    """
    processor = MagicMock()
    processor.apply_chat_template.return_value = "fake chat text"
    processor.return_value = {
        "input_ids": torch.tensor([[1, 2, 3]]),
        "pixel_values": torch.randn(1, 3, 224, 224),
    }
    processor.decode.return_value = "Sunny with scattered clouds."

    fake_output = torch.tensor([[1, 2, 3, 4, 5]])
    model = MagicMock()
    model.generate.return_value = fake_output

    mock_processor_cls.from_pretrained.return_value = processor
    mock_model_cls.from_pretrained.return_value = model

    with patch("torch.backends.mps.is_available", return_value=False):
        wv = WeatherVision()
        text = wv.generate_forecast(
            file_path=str(fake_image),
            prompt="Describe the weather.",
            max_tokens=50,
        )

    model.generate.assert_called_once()
    processor.decode.assert_called_once()
    assert text == "Sunny with scattered clouds."
