from cv2.typing import MatLike
from .saturation import saturation
from .contrast import contrast
from .warmth import warmth
from .vignette import vignette

def polaroid(
    img: MatLike
) -> MatLike:
    """
    Apply polaroid filter to given image

    :param img: BGR image
    :type img: MatLike
    :return:
    :rtype: MatLike
    """

    SATURATION = 18
    WARMTH = 12
    CONTRAST = 10
    VIGNETTE = 25

    img = saturation(img=img, intensity=SATURATION)
    img = warmth(img=img, intensity=WARMTH)
    img = contrast(img=img, intensity=CONTRAST)
    img = vignette(img=img, intensity=VIGNETTE)

    return img
