import cv2
import numpy as np
from cv2.typing import MatLike


def saturation(img: MatLike, intensity: int) -> MatLike:
    """
    Adjusts the color saturation.

    intensity (int):
        -100 → gray
           0 → original
        +100 → strong colors
    """

    # Normalize to [-1.0, +1.0]
    norm = intensity / 100.0

    # Saturation Factor
    sat_factor = 1.0 + norm

    # Convert to float to avoid overflow
    img_f = img.astype(np.float32)

    # Perceptual Luminance (BGR)
    gray = (
        0.114 * img_f[:, :, 0] +
        0.587 * img_f[:, :, 1] +
        0.299 * img_f[:, :, 2]
    )

    # Expand to broadcast
    gray = gray[:, :, np.newaxis]

    # Apply
    result = gray + (img_f - gray) * sat_factor

    # Clamp and convert back
    return np.clip(result, 0, 255).astype(np.uint8)
