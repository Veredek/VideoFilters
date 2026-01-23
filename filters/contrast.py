import numpy as np
from cv2.typing import MatLike


def contrast(img: MatLike, intensity: int) -> MatLike:
    """
    Adjusts image contrast.

    intensity (int):
        -100 → very low contrast
           0 → original
        +100 → very high contrast
    """

    # Normalize to [-1.0, +1.0]
    norm = intensity / 100.0

    # Contrast factor
    factor = 1.0 + norm

    # Convert to float
    img_f = img.astype(np.float32)

    # Pivot (mid-gray)
    pivot = 128.0

    # Apply contrast
    result = (img_f - pivot) * factor + pivot

    # Clamp and convert back
    return np.clip(result, 0, 255).astype(np.uint8)
