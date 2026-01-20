import cv2
import numpy as np
from cv2.typing import MatLike


def warp(
    img: MatLike,
    curvature: int = 20
) -> MatLike:
    """
    Applies CRT-style screen curvature warp.

    Parameters:
        img (MatLike): Input image (BGR).
        curvature (int): Warp intensity (recommended 10-40).

    Returns:
        MatLike: Warped image.
    """

    h, w = img.shape[:2]

    # Normalize curvature
    k = curvature / 1000.0

    # Normalized coordinate grid [-1, 1]
    x = np.linspace(-1.0, 1.0, w, dtype=np.float32)
    y = np.linspace(-1.0, 1.0, h, dtype=np.float32)
    x, y = np.meshgrid(x, y)

    # CRT warp formula
    x_warp = x * (1.0 + k * (y ** 2))
    y_warp = y * (1.0 + k * (x ** 2))

    # Back to pixel coordinates
    map_x:np.float64 = ((x_warp + 1.0) * 0.5) * w
    map_y:np.float64 = ((y_warp + 1.0) * 0.5) * h

    return cv2.remap(
        img,
        map_x.astype(np.float32),
        map_y.astype(np.float32),
        interpolation=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0
    )
