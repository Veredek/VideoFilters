import numpy as np
from cv2.typing import MatLike


def bit_depth(
    img: MatLike,
    bits: int = 4
) -> MatLike:
    """
    Reduces bit depth.

    Parameters:
        img  : uint8
        bits : bits per channel (1-8)

    Returns:
        Image with given bit size
    """

    # Levels
    levels = 2 ** bits

    # Normalize [0,1]
    img_norm = img.astype(np.float32) / 255.0

    # Quantization
    img_quant: MatLike = np.floor(img_norm * levels) / levels

    # Remap [0,255]
    img_out: MatLike = (img_quant * 255.0).astype(np.uint8)

    return img_out