from contextlib import closing, contextmanager

from PIL import Image, ImageOps, UnidentifiedImageError
from pillow_heif import register_heif_opener

MAX_PIXELS = 40_000_000


def configure_codecs():
    register_heif_opener(thumbnails=False, depth_images=False, aux_images=False)


class InvalidImage(ValueError):
    pass


class UnsupportedImage(InvalidImage):
    pass


class ImageTooLarge(InvalidImage):
    pass


def check_pixels(image):
    if image.width * image.height > MAX_PIXELS:
        raise ImageTooLarge("Image exceeds 40,000,000 pixels.")


@contextmanager
def decode_image(source):
    try:
        with closing(Image.open(source)) as image:
            if image.format not in {"JPEG", "PNG", "WEBP", "HEIF"}:
                raise UnsupportedImage("Choose a JPEG, PNG, WebP or HEIC image.")
            check_pixels(image)
            if image.format != "HEIF" and getattr(image, "is_animated", False):
                raise InvalidImage("Animated images are not supported.")
            image.load()
            check_pixels(image)
            ImageOps.exif_transpose(image, in_place=True)
            yield image
    except Image.DecompressionBombError:
        raise ImageTooLarge("Image exceeds 40,000,000 pixels.") from None
    except UnidentifiedImageError, OSError, SyntaxError:
        raise InvalidImage("Image is empty or corrupted.") from None
