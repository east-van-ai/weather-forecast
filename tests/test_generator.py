# =======================================================================
# weather-forecast -- JMA weather chart to Salesforce, no cloud required.
# East Van AI -- AI for the rest of us!
# https://github.com/east-van-ai
# ========================================================================
import torch
import pytest
from PIL import Image
from unittest.mock import MagicMock, patch

from weather_forecast.forecast.generator import WeatherVision


@pytest.fixture
def fake_image(tmp_path):
    """
    Create a temporary PNG image for testing.
    """
    img_path = tmp_path / "test.png"
    img = Image.new("RGB", (64, 64), color="blue")
    img.save(img_path)
    return img_path


@patch("weather_forecast.forecast.generator.AutoProcessor")
@patch("weather_forecast.forecast.generator.AutoModelForImageTextToText")
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


@patch("weather_forecast.forecast.generator.AutoProcessor")
@patch("weather_forecast.forecast.generator.AutoModelForImageTextToText")
def test_generate_forecast(
    mock_model_cls,
    mock_processor_cls,
    fake_image,
):
    """
    Test forecast generation flow with mocked model + processor.
    """
    processor = MagicMock()
    # The prompt is three tokens long, so decoding starts at index 3.
    processor.apply_chat_template.return_value = {
        "input_ids": torch.tensor([[1, 2, 3]]),
        "pixel_values": torch.randn(1, 3, 224, 224),
    }
    processor.decode.return_value = "  A weather chart.  "

    fake_output = torch.tensor([[1, 2, 3, 4, 5]])
    model = MagicMock()
    model.generate.return_value = fake_output

    mock_processor_cls.from_pretrained.return_value = processor
    mock_model_cls.from_pretrained.return_value = model

    with patch("torch.backends.mps.is_available", return_value=False):
        wv = WeatherVision()
        # A Path is passed on purpose: the pipeline deals in Path, and the
        # chat template rejects anything but a string.
        text = wv.generate_forecast(
            file_path=fake_image,
            prompt="What is this?",
            max_tokens=50,
        )

    model.generate.assert_called_once()
    processor.decode.assert_called_once()

    # Only the generated tail is decoded, and the answer is stripped.
    decoded = processor.decode.call_args.args[0]
    assert torch.equal(decoded, torch.tensor([4, 5]))
    assert text == "A weather chart."

    # The image and the prompt reach the processor through the template.
    messages = processor.apply_chat_template.call_args.args[0]
    content = messages[0]["content"]
    assert content[0] == {"type": "image", "path": str(fake_image)}
    assert isinstance(content[0]["path"], str)
    assert content[1] == {"type": "text", "text": "What is this?"}


@patch("weather_forecast.forecast.generator.AutoProcessor")
@patch("weather_forecast.forecast.generator.AutoModelForImageTextToText")
def test_model_name_resolution_order(mock_model_cls, mock_processor_cls):
    """
    Explicit arg wins over the default.
    """
    mock_processor_cls.from_pretrained.return_value = MagicMock()
    mock_model_cls.from_pretrained.return_value = MagicMock()

    with patch("torch.backends.mps.is_available", return_value=False):
        assert WeatherVision().model_name == WeatherVision.DEFAULT_MODEL_NAME
        assert (
            WeatherVision("some-org/some-vision-model").model_name
            == "some-org/some-vision-model"
        )
