import numpy as np
from cv2.typing import MatLike


def posterize(
    img: MatLike,
    levels: int = 4
) -> MatLike:
    """
    Applies a posterization effect.

    Reduces the number of tonal levels per channel.

    Parameters:
        img (MatLike): Input image (BGR).
        levels (int): Number of color levels per channel (min=2, max=256).

    Returns:
        MatLike: Posterized image.
    """

    # Convert to float
    img_f = img.astype(np.float32)

    # Quantization
    step = 256 // levels
    poster = (img_f // step) * step + step // 2

    # Clipping and convert back
    out = np.clip(poster, 0, 255).astype(np.uint8)

    return out
