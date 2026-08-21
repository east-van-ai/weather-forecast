# =======================================================================
# weather-forecast -- JMA weather chart to Salesforce, no cloud required.
# East Van AI -- AI for the rest of us!
# https://github.com/east-van-ai
# ========================================================================
import logging
import sys
from pathlib import Path
from weather_forecast.chart.downloader import WeatherPDFDownloader
from weather_forecast.chart.processors.image_tools import resize_png
from weather_forecast.chart.processors.pdf_tools import pdf_to_png
from weather_forecast.forecast.generator import WeatherVision
from weather_forecast.salesforce.weather import ReportUpsertResult, SFWeatherClient

WEATHER_PDF_URL = "https://www.data.jma.go.jp/yoho/data/wxchart/quick/ASAS_COLOR.pdf"
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

    config (dict)
        Contains Salesforce Credentials
        - client_id
        - username
        - audience
        - private_key

    Intended for controlled re-runs, recovery scenarios, and MVP testing.
    Use with caution.
    """

    def __init__(self, force: bool = False, config: dict = {}):
        """Initialize the pipeline execution mode."""
        self.force = force
        self.config = config

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

    def _get_data_dir(self, app_name="weather-forecast"):
        """Determine data directory based on installation method."""
        if ".local/pipx" in str(sys.prefix):
            # Running under pipx
            data_dir = Path.home() / ".cache" / app_name / "data"
        else:
            # Running normally
            data_dir = Path("./data")

        # Create if it doesn't exist
        data_dir.mkdir(parents=True, exist_ok=True)

        return data_dir

    def _download_chart(self) -> dict:
        """
        Download the weather chart and return its status.

        Returns:
            dict: A dictionary containing 'updated' (bool), 'hash' (str), and 'path' (Path).
        """
        data_dir = self._get_data_dir()

        downloader = WeatherPDFDownloader(Path(data_dir), WEATHER_PDF_URL)

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
        data_dir = self._get_data_dir()

        # Convert to PNG for AI and Salesforce
        regular_png_path = pdf_to_png(chart["path"], Path(data_dir) / WEATHER_PNG)

        # Create resized 300px PNG for Salesforce (lightweight)
        small_png_path = resize_png(
            regular_png_path, Path(data_dir) / WEATHER_SMALL_PNG, width=300
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
        sf = SFWeatherClient(self.config)
        report = sf.upsert_report(chart["hash"], forecast["content"])

        sf.ensure_preview_image(report.record_id, images["small"])

        return report
