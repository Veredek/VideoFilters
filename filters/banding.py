import numpy as np
from cv2.typing import MatLike


def banding(
    img: MatLike,
    levels: int = 8
) -> MatLike:

    step = 256 // levels

    out = (img // step) * step
    return out.astype(np.uint8)
