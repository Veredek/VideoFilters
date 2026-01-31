import numpy as np
import cv2
from cv2.typing import MatLike


def banding_luminance(
    img: MatLike,
    levels: int = 8
) -> MatLike:
    """
    Increases banding focusing on luminance (HSV V channel).
    """
    step = 256 // levels

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    v = hsv[..., 2]

    v = (v // step) * step
    hsv[..., 2] = v.astype(np.uint8)

    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
