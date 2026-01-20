import cv2
import numpy as np
from cv2.typing import MatLike


def ca_radial(
    img: MatLike,
    strength_r: int = 2,
    strength_g: int = 0,
    strength_b: int = -2
) -> MatLike:
    """
    Applies a radial chromatic aberration effect.

    Each color channel is displaced radially from the image center
    with a different strength, simulating real lens chromatic aberration.

    Parameters:
        img (MatLike): Input image in BGR format.
        strength_r (float): Radial strength for the red channel.
        strength_g (float): Radial strength for the green channel.
        strength_b (float): Radial strength for the blue channel.

    Returns:
        MatLike: Image with radial chromatic aberration applied.
    """

    strength_r = strength_r / 100.0
    strength_g = strength_g / 100.0
    strength_b = strength_b / 100.0

    h, w = img.shape[:2]
    cx, cy = w * 0.5, h * 0.5

    # Create normalized coordinate grid
    x, y = np.meshgrid(np.arange(w), np.arange(h))
    x = x.astype(np.float32)
    y = y.astype(np.float32)

    dx = x - cx
    dy = y - cy

    # Normalized radial distance (0 at center, ~1 at corners)
    max_radius = np.sqrt(cx * cx + cy * cy)
    radius = np.sqrt(dx * dx + dy * dy) / max_radius

    # Split channels
    b, g, r = cv2.split(img)

    def remap_channel(channel: MatLike, strength: float) -> MatLike:
        """
        Applies radial displacement to a single channel using remap.
        """

        factor = 1.0 + strength * radius

        map_x:np.float64 = cx + dx * factor
        map_y:np.float64 = cy + dy * factor

        return cv2.remap(
            channel,
            map_x.astype(np.float32),
            map_y.astype(np.float32),
            interpolation=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=0
        )

    b_shifted = remap_channel(b, strength_b)
    g_shifted = remap_channel(g, strength_g)
    r_shifted = remap_channel(r, strength_r)

    return cv2.merge((b_shifted, g_shifted, r_shifted))
