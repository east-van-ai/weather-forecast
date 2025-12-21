from pathlib import Path
import hashlib
import urllib.request  # or requests
from pdf2image import convert_from_path
from PIL import Image
import os


class WeatherPDFDownloader:
    CURRENT_PDF = "current.pdf"
    LAST_PDF = "last.pdf"

    def __init__(self, data_path: Path, weather_pdf_url: str):
        self.data_path = data_path
        self.weather_pdf_url = weather_pdf_url
        self.current_pdf_path = self.data_path / WeatherPDFDownloader.CURRENT_PDF
        self.last_pdf_path = self.data_path / WeatherPDFDownloader.LAST_PDF

    # Core: manage renames + download + compare
    def refresh_pdf(self):
        current_exists = self._exists(self.current_pdf_path)
        last_exists = self._exists(self.last_pdf_path)

        # Case A: neither exists
        if not last_exists and not current_exists:
            self._download()
            current_hash = WeatherPDFDownloader.hash_pdf(self.current_pdf_path)
            return True, current_hash, self.current_pdf_path  # new file

        # Case B: only current exists
        if not last_exists and current_exists:
            self._rename(self.current_pdf_path, self.last_pdf_path)
            self._download()
            return self._compare_and_cleanup()

        # Case C: only last exists
        if last_exists and not current_exists:
            self._download()
            return self._compare_and_cleanup()

        # Case D: both exist
        self._delete(self.last_pdf_path)
        self._rename(self.current_pdf_path, self.last_pdf_path)
        self._download()
        return self._compare_and_cleanup()

    # ------------------
    # Utility Methods
    # ------------------

    def _exists(self, path: Path) -> bool:
        """Check if the file exists."""
        return path.exists()

    def _delete(self, path: Path) -> None:
        """Delete the file if it exists."""
        if path.exists():
            path.unlink()  # remove the file

    def _download(self) -> None:
        """Download the current PDF from the URL."""
        data = urllib.request.urlopen(self.weather_pdf_url).read()
        with self.current_pdf_path.open("wb") as f:
            f.write(data)

    def _rename(self, src: Path, dst: Path) -> None:
        """Rename (move) a file from src to dst."""
        if src.exists():
            src.rename(dst)

    def _compare_and_cleanup(self) -> bool:
        """Compare current and last PDFs, clean up if unchanged."""
        last_hash = WeatherPDFDownloader.hash_pdf(self.last_pdf_path)
        current_hash = WeatherPDFDownloader.hash_pdf(self.current_pdf_path)

        if last_hash == current_hash:
            self._delete(self.current_pdf_path)
            return False, last_hash, self.last_pdf_path  # no change

        return True, current_hash, self.current_pdf_path  # changed

    @classmethod
    def hash_pdf(cls, path: Path) -> str:
        """Compute SHA256 hash of the PDF file."""
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
