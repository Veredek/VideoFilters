import numpy as np
from cv2.typing import MatLike


def vignette(img: MatLike, intensity: int) -> MatLike:
    """
    Applies a vignette effect to the image.

    intensity (int):
        -100 → strong bright vignette
           0 → original
        +100 → strong dark vignette
    """

    # Normalize to [-1.0, +1.0]
    norm = intensity / 100.0

    # Convert to float
    img_f = img.astype(np.float32)

    h, w = img_f.shape[:2]

    # Image center
    cx = w / 2.0
    cy = h / 2.0

    # Coordinate grids
    x = np.arange(w)
    y = np.arange(h)
    X, Y = np.meshgrid(x, y)

    # Radial distance
    dist = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)

    # Max distance
    max_dist = np.sqrt(cx ** 2 + cy ** 2)

    # Normalize distance to [0, 1]
    d = dist / max_dist

    # Smooth falloff curve
    v = d ** 2

    # Vignette strength
    k = 0.6 * norm

    # Vignette factor
    factor = 1.0 - k * v

    # Apply
    result = img_f * factor[:, :, np.newaxis]

    # Clamp and convert back
    return np.clip(result, 0, 255).astype(np.uint8)