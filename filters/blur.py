import cv2
from cv2.typing import MatLike

def blur(frame: MatLike,
         blur_intensity: int = 1) -> MatLike:

    # ksize: kernel size (size of influence)
    # ksize needs to be odd

    ksize = (2 * blur_intensity) + 1

    return cv2.GaussianBlur(frame, (ksize, ksize), 0)