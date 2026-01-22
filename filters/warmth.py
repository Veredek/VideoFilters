import cv2
import numpy as np
from cv2.typing import MatLike


def warmth(img: MatLike, intensity: int) -> MatLike:
    """
    Adjusts the color temperature (warmth) of an image.

    intensity (int):
        -100 → very cold
           0 → original
        +100 → very warm
    """

    # Safety clamp
    intensity = max(-100, min(100, intensity))

    # Normalize to [-1.0, +1.0]
    norm = intensity / 100.0

    # Convert to float to avoid overflow
    img_f = img.astype(np.float32)

    # Warmth strength (empirical, perceptually stable)
    shift = 40.0 * norm

    # Apply
    img_f[:, :, 2] += shift   # Red channel
    img_f[:, :, 0] -= shift   # Blue channel
    # Green channel intentionally unchanged

    # Clamp and convert back
    return np.clip(img_f, 0, 255).astype(np.uint8)