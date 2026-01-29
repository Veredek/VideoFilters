import numpy as np
from cv2.typing import MatLike

def gamma_linear(img: MatLike, gamma: int) -> MatLike:
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

    out = np.power(img_norm, gamma_exp)

    return (out * 255).astype(np.uint8)
