import cv2
import numpy as np
from cv2.typing import MatLike


def bloom(
    img: MatLike,
    intensity: int = 35,
    threshold: int = 180,
    radius: int = 8
) -> MatLike:
    """
    Adds a soft glow around bright areas.

    intensity:
        0   -> no bloom
        100 -> strongest bloom

    threshold:
        0   -> all pixels can glow
        255 -> only the brightest pixels glow

    radius:
        Blur radius used to spread highlights.
    """

    if intensity <= 0:
        return img

    intensity = int(np.clip(intensity, 0, 100))
    threshold = int(np.clip(threshold, 0, 255))
    radius = max(1, int(radius))

    img_f = img.astype(np.float32)

    luminance = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    bright_mask = (luminance >= threshold).astype(np.float32)

    if not np.any(bright_mask):
        return img

    highlights = img_f * bright_mask[:, :, None]

    sigma = radius / 2.0
    glow = cv2.GaussianBlur(highlights, (0, 0), sigmaX=sigma, sigmaY=sigma)

    strength = intensity / 100.0
    out = img_f + glow * (0.85 * strength)

    return np.clip(out, 0, 255).astype(np.uint8)
