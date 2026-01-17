from cv2.typing import MatLike

def scanlines(frame: MatLike,
              intensity: int = 50,
              spacing: int = 2) -> MatLike:
    intensity = intensity / 100

    frame = frame.copy()
    frame[::spacing, :, :] = (frame[::spacing, :, :] * (1 - intensity)).astype("uint8")
    return frame