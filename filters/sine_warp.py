import cv2
import numpy as np
from cv2.typing import MatLike


def sine_warp(
    img: MatLike,
    amp_x: int,
    amp_y: int,
    period_x: int,
    period_y: int
) -> MatLike:
    """
    Applies a sine warp effect to the input image by distorting it using sine waves.

    Parameters:
    img (MatLike): The input image to be warped.
    amp_x (int): Amplitude of the sine wave for horizontal warping. If <= 0, no horizontal warping is applied.
    amp_y (int): Amplitude of the sine wave for vertical warping. If <= 0, no vertical warping is applied.
    period_x (int): Period of the sine wave for horizontal warping. Must be at least 1.
    period_y (int): Period of the sine wave for vertical warping. Must be at least 1.

    Returns:
    MatLike: The warped image with the sine distortion applied.
    """
    if amp_x <= 0 and amp_y <= 0:
        return img

    h, w = img.shape[:2]

    px = max(1, period_x)
    py = max(1, period_y)

    x = np.arange(w, dtype=np.float32)
    y = np.arange(h, dtype=np.float32)
    x, y = np.meshgrid(x, y)

    if amp_x > 0:
        x = x + amp_x * np.sin((2.0 * np.pi * y) / py)
    if amp_y > 0:
        y = y + amp_y * np.sin((2.0 * np.pi * x) / px)

    return cv2.remap(
        img,
        x.astype(np.float32),
        y.astype(np.float32),
        interpolation=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REFLECT,
        borderValue=0
    )
