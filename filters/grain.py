import cv2
import numpy as np
from cv2.typing import MatLike


def grain(
    img: MatLike,
    intensity: int,
    grain_size: int
) -> MatLike:
    if intensity <= 0:
        return img

    img_f = img.astype(np.float32)
    h, w = img.shape[:2]

    # Monochrome film grain
    noise = np.random.randn(h, w).astype(np.float32)

    sigma = max(0.1, grain_size / 2.0)
    noise = cv2.GaussianBlur(noise, (0, 0), sigmaX=sigma, sigmaY=sigma)

    gain = (intensity / 100.0) * 255.0
    out = img_f + noise[..., None] * gain

    out = np.clip(out, 0.0, 255.0).astype(np.uint8)
    return out
