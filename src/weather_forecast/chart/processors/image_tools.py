from pathlib import Path
from PIL import Image


def resize_png(src_path: Path, dst_path: Path, width: int = 300):
    """Resize a PNG image to the specified width while maintaining aspect ratio."""
    img = Image.open(src_path)
    w, h = img.size
    ratio = width / float(w)
    new_size = (width, int(h * ratio))
    img = img.resize(new_size, Image.LANCZOS)
    img.save(dst_path, optimize=True)
    return dst_path
