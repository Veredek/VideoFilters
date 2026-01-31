import numpy as np
import cv2
from cv2.typing import MatLike


def downscale_resolution(
        img: MatLike,
        scale_percent: int
) -> MatLike:

    if scale_percent == 100:
        return img

    h, w = img.shape[:2]

    new_w = max(1, int(w * scale_percent / 100))
    new_h = max(1, int(h * scale_percent / 100))

    # Downscale
    INTERPOLATION_DOWN = cv2.INTER_AREA
    small = cv2.resize(img, (new_w, new_h), interpolation=INTERPOLATION_DOWN)

    # Upscale back (Pixelize)
    INTERPOLATION_UP = cv2.INTER_NEAREST
    degraded = cv2.resize(small, (w, h), interpolation=INTERPOLATION_UP)

    return degraded