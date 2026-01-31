import cv2
import numpy as np
from cv2.typing import MatLike


def noise(
    img: MatLike,
    x_noise: int,
    y_noise: int,
    intensity: int
) -> MatLike:

    # Normalize intensity
    intensity_norm = intensity / 100.0

    # Invert noise on axis
    sigma_x = 101 - x_noise
    sigma_y = 101 - y_noise

    # Normalize image
    img_norm = img.astype(np.float32) / 255.0

    h, w = img.shape[:2]

    # Handle 0 values
    if x_noise == 0 and y_noise == 0:
        return img
    if intensity == 0:
        return img

    # Noise map
    noise = cv2.GaussianBlur(
        np.random.rand(h, w).astype(np.float32),
        (0, 0),
        sigmaX=sigma_x,
        sigmaY=sigma_y
    )

    # Normalize noise to [-1, 1]
    noise = (noise - 0.5) * 2.0

    # Noise map
    gamma_map = 1 + noise * intensity_norm * 2
    gamma_map = np.clip(gamma_map, 0.2, 3.0)

    # Apply
    out_norm = np.power(img_norm, gamma_map[..., None])
    out_norm = np.clip(out_norm, 0.0, 1.0)

    out = (out_norm * 255.0).astype(np.uint8)

    return out