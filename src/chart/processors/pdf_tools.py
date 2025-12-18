from pathlib import Path
from pdf2image import convert_from_path


def pdf_to_png(pdf_path: Path, output_path: Path):
    """Convert the first page of a PDF to a PNG image."""
    pages = convert_from_path(pdf_path)
    pages[0].save(output_path)
    return output_path
