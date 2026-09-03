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
    based on local file state and idempotency guards, and a `dry_run`
    mode that decides how far a run goes.

    force (bool):
        When True, forces the pipeline to run regardless of local file
        existence or cache conditions. Salesforce records are created
        or updated while idempotency guards still prevent duplicates.

        When False, the pipeline respects local file state and skip
        conditions to avoid unnecessary processing.

    dry_run (bool):
        When True, the run stops after the forecast and never reaches
        Salesforce, so the JWT handshake does not happen either. The
        download, the render, and the model all run as usual: a dry run
        is a full run that stops before the writes, not a run that skips
        itself.

    config (dict)
        Contains Salesforce Credentials
        - client_id
        - username
        - audience
        - private_key

    Intended for controlled re-runs, recovery scenarios, and MVP testing.
    Use with caution.
    """

    def __init__(self, force: bool = False, dry_run: bool = False, config: dict = {}):
        """Initialize the pipeline execution mode."""
        self.force = force
        self.dry_run = dry_run
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

        if self.dry_run:
            logger.info(
                "Dry run: would upsert Weather_Report__c PDF_Hash__c=%s "
                "with preview %s",
                chart["hash"],
                images["small"],
            )
            logger.info("Dry run forecast: %s", forecast)
            logger.info("Pipeline run completed successfully (dry run)")
            return True

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

        The PDF hash is the only condition. `force` is not consulted here: the
        caller decides whether to ask at all, which keeps this answering one
        question rather than two.

        Args:
            chart (dict): Output from _download_chart()

        Returns:
            bool: True if processing should continue
        """
        if not chart.get("updated", False):
            return False

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
        Describe the chart with the local vision model.

        The full-size render is used on purpose. The 300px thumbnail carries
        too little of the chart to survive the model's crop splitting.

        Args:
            images (dict): Prepared images from _prepare_images()
        Returns:
            str: The model's description of the chart
        """
        wv = WeatherVision()
        return wv.generate_forecast(images["regular"], "What is this?")

    def _publish_salesforce(
        self, chart: dict, images: dict, forecast: str
    ) -> ReportUpsertResult:
        """
        Publish the forecast and images to Salesforce.

        Args:
            images (dict): Prepared images from _prepare_images()
            forecast (str): Chart description from _generate_forecast()
        Returns:
            str: Salesforce record ID
        """
        sf = SFWeatherClient(self.config)
        report = sf.upsert_report(chart["hash"], forecast)

        sf.ensure_preview_image(report.record_id, images["small"])

        return report
