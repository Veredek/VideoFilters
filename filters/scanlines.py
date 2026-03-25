from cv2.typing import MatLike


def scanlines(img: MatLike,
              intensity: int = 50,
              width: int = 1,
              spacing: int = 2) -> MatLike:

    img = img.copy()
    intensity = intensity / 100

    # Apply darkened lines with a given width and spacing.
    height = img.shape[0]
    for y in range(0, height, spacing):
        y_end = min(y + width, height)
        img[y:y_end, :, :] = (img[y:y_end, :, :] * (1 - intensity)).astype("uint8")

    return img