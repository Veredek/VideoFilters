import numpy as np
from cv2.typing import MatLike

def gamma(img: MatLike, gamma: int) -> MatLike:
    """
    Adjusts gamma equally in all pixels.

    Default: 100.
    Min: 0.
    Max: 100.
    """

    # Exponent
    gamma_exp = gamma / 100

    # Normalize
    img_norm = img.astype(np.float32) / 255.0

    # Apply
    out_norm = np.power(img_norm, gamma_exp)
    out_norm = np.clip(out_norm, 0.0, 1.0)

    out = (out_norm * 255).astype(np.uint8)

    return out
