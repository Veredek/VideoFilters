import cv2
import numpy as np
from cv2.typing import MatLike


def ca_linear(
    img: MatLike,
    shift_r: int = 5,
    shift_g: int = 0,
    shift_b: int = -5
) -> MatLike:
    """
    Applies a chromatic aberration effect by shifting color channels independently.

    Parameters:
        img (MatLike): Input image in BGR format.
        shift_r (int): Horizontal shift for the red channel.
        shift_g (int): Horizontal shift for the green channel.
        shift_b (int): Horizontal shift for the blue channel.

    Returns:
        MatLike: Image with chromatic aberration applied.
    """

    h, w = img.shape[:2]

    # Split BGR channels
    b, g, r = cv2.split(img)

    def shift_channel(channel: MatLike, shift: int) -> MatLike:
        """
        Move pixels of the channel by given shift value

        :param channel:
        :type channel: MatLike
        :param shift:
        :type shift: int
        :return:
        :rtype: MatLike
        """

        M = np.float32([[1, 0, shift], # shift here makes horizontal shift
                        [0, 1, 0]]) # instead, shift here makes vertical shift
        return cv2.warpAffine(channel, M, (w, h))

    b_shifted = shift_channel(b, shift_b)
    g_shifted = shift_channel(g, shift_g)
    r_shifted = shift_channel(r, shift_r)

    return cv2.merge((b_shifted, g_shifted, r_shifted))