from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from PIL import Image, ImageOps

MAX_SIDE = 2000
WEBP_QUALITY = 82


def to_webp(uploaded_file) -> ContentFile:
    """
    Returns a web-sized WebP copy of an uploaded photo.

    Phone/camera originals are 8-10 MB; this rotates them by their EXIF
    orientation, shrinks the longer side to MAX_SIDE (never upscales) and
    re-encodes as WebP. EXIF (including GPS) is dropped, the colour profile is kept.
    """
    uploaded_file.seek(0)
    with Image.open(uploaded_file) as img:
        # JPEG only: decode at a reduced scale right away, so a 48 MP photo
        # doesn't need ~150 MB of RAM just to be shrunk afterwards.
        img.draft("RGB", (MAX_SIDE, MAX_SIDE))
        # A CMYK profile would be wrong once the pixels are converted to RGB.
        icc_profile = img.info.get("icc_profile") if img.mode != "CMYK" else None

        img = ImageOps.exif_transpose(img)
        img = img.convert("RGBA" if img.has_transparency_data else "RGB")
        img.thumbnail((MAX_SIDE, MAX_SIDE), Image.Resampling.LANCZOS)

        buffer = BytesIO()
        img.save(buffer, format="WEBP", quality=WEBP_QUALITY, icc_profile=icc_profile)

    return ContentFile(buffer.getvalue(), name=f"{Path(uploaded_file.name).stem}.webp")