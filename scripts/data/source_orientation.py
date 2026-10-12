"""Apply reviewed page direction in RAM, after EXIF; never guess from OCR text."""
import hashlib
from pathlib import Path

from PIL import Image, ImageOps


def reviewed_rotation(item):
    review = item.get('reviewed_orientation')
    if review is None:
        return 0
    if (not isinstance(review, dict) or review.get('status') != 'verified'
            or review.get('sha256') != item.get('sha256')
            or not isinstance(review.get('reviewer'), str) or not review['reviewer'].strip()
            or type(review.get('clockwise_degrees')) is not int
            or review['clockwise_degrees'] not in (0, 90, 180, 270)):
        raise ValueError('Orientation requires a source-bound, explicit visual review')
    return review['clockwise_degrees']


def orient_image(image, item):
    image = ImageOps.exif_transpose(image).convert('RGB')
    rotation = reviewed_rotation(item)
    if rotation:
        operation = {90: Image.Transpose.ROTATE_270, 180: Image.Transpose.ROTATE_180,
                     270: Image.Transpose.ROTATE_90}[rotation]
        image = image.transpose(operation)
    return image


def validate_orientation_geometry(item, region):
    """Equal dimensions do not identify a coordinate frame (e.g. 90 vs 270)."""
    rotation = reviewed_rotation(item)
    if region.get('reviewed_orientation') != item.get('reviewed_orientation'):
        raise ValueError('Page geometry belongs to a different orientation review')
    if rotation:
        expected = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        if region.get('orientation_code_sha256') != expected:
            raise ValueError('Orientation preprocessing changed; regenerate page geometry')
