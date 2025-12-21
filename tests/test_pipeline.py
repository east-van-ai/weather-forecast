from pathlib import Path
from unittest.mock import MagicMock
from src.orchestration.pipeline import WeatherPipeline


def test_run_happy_path(mocker):
    pipeline = WeatherPipeline()

    # Arrange
    fake_chart = MagicMock()
    fake_images = MagicMock()
    fake_forecast = MagicMock()

    mock_download = mocker.patch.object(
        pipeline, "_download_chart", return_value=fake_chart
    )
    mock_should = mocker.patch.object(pipeline, "_should_process", return_value=True)

    mock_prepare = mocker.patch.object(
        pipeline, "_prepare_images", return_value=fake_images
    )
    mock_generate = mocker.patch.object(
        pipeline, "_generate_forecast", return_value=fake_forecast
    )
    mock_publish = mocker.patch.object(pipeline, "_publish_salesforce")

    # Act
    pipeline.run()

    # Assert
    mock_download.assert_called_once_with()
    mock_should.assert_called_once_with(fake_chart)
    mock_prepare.assert_called_once_with(fake_chart)
    mock_generate.assert_called_once_with(fake_images)
    mock_publish.assert_called_once_with(fake_chart, fake_images, fake_forecast)


def test_run_skips_when_should_process_is_false(mocker):
    pipeline = WeatherPipeline()

    # Arrange
    fake_chart = MagicMock()

    mock_download = mocker.patch.object(
        pipeline, "_download_chart", return_value=fake_chart
    )
    mock_should = mocker.patch.object(pipeline, "_should_process", return_value=False)

    mock_prepare = mocker.patch.object(pipeline, "_prepare_images")
    mock_generate = mocker.patch.object(pipeline, "_generate_forecast")
    mock_publish = mocker.patch.object(pipeline, "_publish_salesforce")

    # Act
    pipeline.run()

    # Assert
    mock_download.assert_called_once_with()
    mock_should.assert_called_once_with(fake_chart)
    mock_prepare.assert_not_called()
    mock_generate.assert_not_called()
    mock_publish.assert_not_called()


def test_download_chart(monkeypatch):
    pipeline = WeatherPipeline()

    # Arrange
    def fake_refresh(self):
        return True, "hash123", "/tmp/test.pdf"

    monkeypatch.setattr(
        "src.chart.downloader.WeatherPDFDownloader.refresh_pdf",
        fake_refresh,
    )

    # Act
    result = pipeline._download_chart()

    # Assert
    assert result["updated"] is True
    assert result["hash"] == "hash123"
    assert result["path"] == "/tmp/test.pdf"


def test_should_process():
    pipeline = WeatherPipeline()

    # Case 1: updated is True
    chart1 = {"updated": True}
    assert pipeline._should_process(chart1) is True

    # Case 2: updated is False
    chart2 = {"updated": False}
    assert pipeline._should_process(chart2) is False


def test_prepare_images(mocker):
    pipeline = WeatherPipeline()

    # Arrange
    mock_pdf_to_png = mocker.patch(
        "src.orchestration.pipeline.pdf_to_png",
        return_value=Path("/fake/weather.png"),
    )
    mock_resize_png = mocker.patch(
        "src.orchestration.pipeline.resize_png",
        return_value=Path("/fake/weather_small.png"),
    )

    fake_chart = {"path": Path("/fake/test.pdf")}

    # Act
    result = pipeline._prepare_images(fake_chart)

    mock_pdf_to_png.assert_called_once_with(
        fake_chart["path"], Path("./data") / "weather.png"
    )
    mock_resize_png.assert_called_once_with(
        Path("/fake/weather.png"), Path("./data") / "weather_small.png", width=300
    )

    # Assert
    assert result["regular"] == Path("/fake/weather.png")
    assert result["small"] == Path("/fake/weather_small.png")


def test_generate_forecast(mocker):
    pipeline = WeatherPipeline()

    # Arrange
    fake_images = {
        "regular": Path("/fake/weather.png"),
        "small": Path("/fake/weather_small.png"),
    }

    fake_forecast = "Today's weather forecast:\nSunny with scattered clouds"
    expected = {
        "title": "Today's weather forecast:",
        "content": "Sunny with scattered clouds",
    }

    mock_weather_vision = mocker.patch(
        "src.orchestration.pipeline.WeatherVision", autospec=True
    )
    mock_weather_vision.return_value.generate_forecast.return_value = fake_forecast

    # Act
    result = pipeline._generate_forecast(fake_images)

    # Assert
    assert result == expected
    mock_weather_vision.return_value.generate_forecast.assert_called_once()


def test_publish_salesforce(mocker):
    pipeline = WeatherPipeline()

    # Arrange
    fake_sf = mocker.patch(
        "src.orchestration.pipeline.SFWeatherClient",
        autospec=True,
    ).return_value

    fake_report = MagicMock()
    fake_report.record_id = "REPORT123"
    fake_sf.upsert_report.return_value = fake_report

    chart = {"hash": "abc123"}
    images = {"small": Path("/fake/small.png")}
    forecast = {"content": "Sunny"}

    # Act
    result = pipeline._publish_salesforce(chart, images, forecast)

    # Assert
    fake_sf.upsert_report.assert_called_once_with("abc123", "Sunny")
    fake_sf.ensure_preview_image.assert_called_once_with(
        "REPORT123",
        images["small"],
    )
    assert result is fake_report
