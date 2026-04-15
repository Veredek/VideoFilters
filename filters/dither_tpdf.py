import numpy as np
from cv2.typing import MatLike


def dither_tpdf(
    img: MatLike,
    levels: int,
    dither_strength: int,
    intensity: int
) -> MatLike:
    """
    Applies tonal quantization with TPDF dithering.

    The image is first perturbed with triangular-distribution noise and then
    quantized to a reduced number of tonal levels. The filtered result is
    finally blended with the original image according to ``intensity``.

    Parameters:
        img (MatLike): Input image.
        levels (int): Number of quantization levels per channel (min=2).
        dither_strength (int): Strength of the TPDF noise, from 0 to 100.
        intensity (int): Blend amount of the filtered result, from 0 to 100.

    Returns:
        MatLike: Quantized image with TPDF dithering applied.
    """
    if levels < 2:
        return img
    if intensity <= 0:
        return img

    img_f = img.astype(np.float32)
    step = 255.0 / (levels - 1)
    blend = np.clip(intensity / 100.0, 0.0, 1.0)

    noise_shape = img.shape if img.ndim == 2 else (*img.shape[:2], 1)
    # TPDF noise in range [-1, 1]. Reusing one noise field across channels
    # avoids adding unnecessary color speckle to RGB/BGR images.
    noise = (
        np.random.rand(*noise_shape) + np.random.rand(*noise_shape) - 1.0
    ).astype(np.float32)
    noise *= step * 0.5 * np.clip(dither_strength / 100.0, 0.0, 1.0)

    dithered = img_f + noise
    quantized = np.round(dithered / step) * step
    out = img_f + (quantized - img_f) * blend

    return np.clip(out, 0, 255).astype(np.uint8)
