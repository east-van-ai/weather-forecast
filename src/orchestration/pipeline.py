import logging
from pathlib import Path
from src.chart.downloader import WeatherPDFDownloader
from src.chart.processors.image_tools import resize_png
from src.chart.processors.pdf_tools import pdf_to_png
from src.forecast.generator import WeatherVision
from src.salesforce.weather import ReportUpsertResult, SFWeatherClient

WEATHER_PDF_URL = "https://www.data.jma.go.jp/yoho/data/wxchart/quick/ASAS_COLOR.pdf"
DATA_DIR = "./data"
WEATHER_PNG = "weather.png"
WEATHER_SMALL_PNG = "weather_small.png"

logger = logging.getLogger(__name__)


class WeatherPipeline:
    """
    Orchestrates the weather forecast workflow.

    The pipeline supports a `force` mode that controls skip behavior
    based on local file state and idempotency guards.

    force (bool):
        When True, forces the pipeline to run regardless of local file
        existence or cache conditions. Salesforce records are created
        or updated while idempotency guards still prevent duplicates.

        When False, the pipeline respects local file state and skip
        conditions to avoid unnecessary processing.

    Intended for controlled re-runs, recovery scenarios, and MVP testing.
    Use with caution.
    """

    def __init__(self, force: bool = False):
        """Initialize the pipeline execution mode."""
        self.force = force

    def run(self) -> bool:
        """
        Run the weather forecast pipeline.

        Returns:
            bool: True if the pipeline ran successfully, False otherwise.
        """
        logger.info("Pipeline run started")

        chart = self._download_chart()

        if not self.force and not self._should_process(chart):
            logger.info("Pipeline execution skipped (should_process=False)")
            return False

        logger.info("Preparing images")
        images = self._prepare_images(chart)

        logger.info("Generating forecast via AI")
        forecast = self._generate_forecast(images)

        logger.info("Publishing results to Salesforce")
        record = self._publish_salesforce(chart, images, forecast)

        logger.info(
            "Salesforce publish completed: record_id=%s created=%s",
            record.record_id,
            record.created,
        )

        logger.info("Pipeline run completed successfully")
        return True

    def _download_chart(self) -> dict:
        """
        Download the weather chart and return its status.

        Returns:
            dict: A dictionary containing 'updated' (bool), 'hash' (str), and 'path' (Path).
        """
        downloader = WeatherPDFDownloader(Path(DATA_DIR), WEATHER_PDF_URL)

        updated, pdf_hash, pdf_path = downloader.refresh_pdf()

        return {
            "updated": updated,
            "hash": pdf_hash,
            "path": pdf_path,
        }

    def _should_process(self, chart: dict) -> bool:
        """
        Decide whether the pipeline should continue processing.

        Args:
            chart (dict): Output from _download_chart()

        Returns:
            bool: True if processing should continue
        """
        if not chart.get("updated", False):
            return False

        # future:
        # if self.force:
        #     return True
        # if self.dryrun:
        #     return False
        # if not within_schedule_window():
        #     return False

        return True

    def _prepare_images(self, chart: dict) -> dict:
        """
        Prepare PNG images from the downloaded PDF for further processing.

        Args:
            chart (dict): Output from _download_chart()
        Returns:
            dict: Paths to prepared images
        """
        # Convert to PNG for AI and Salesforce
        regular_png_path = pdf_to_png(chart["path"], Path(DATA_DIR) / WEATHER_PNG)

        # Create resized 300px PNG for Salesforce (lightweight)
        small_png_path = resize_png(
            regular_png_path, Path(DATA_DIR) / WEATHER_SMALL_PNG, width=300
        )

        images = {
            "regular": regular_png_path,
            "small": small_png_path,
        }
        return images

    def _generate_forecast(self, images):
        """
        Generate AI-based weather forecast from the images.

        Args:
            images (dict): Prepared images from _prepare_images()
        Returns:
            dict: Generated forecast with 'title' and 'content'
        """
        wv = WeatherVision()
        ai_forecast = wv.generate_forecast(
            images["regular"], "Title and description\n<image>"
        )

        lines = ai_forecast.split("\n", 1)  # Split into at most 2 parts
        title = lines[0]
        content = lines[1] if len(lines) > 1 else ""

        forecast = {
            "title": title,
            "content": content,
        }
        return forecast

    def _publish_salesforce(
        self, chart: dict, images: dict, forecast: dict
    ) -> ReportUpsertResult:
        """
        Publish the forecast and images to Salesforce.

        Args:
            images (dict): Prepared images from _prepare_images()
            forecast (dict): Generated forecast from _generate_forecast()
        Returns:
            str: Salesforce record ID
        """
        sf = SFWeatherClient()
        report = sf.upsert_report(chart["hash"], forecast["content"])

        sf.ensure_preview_image(report.record_id, images["small"])

        return report
