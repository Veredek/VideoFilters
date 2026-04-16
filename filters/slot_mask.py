import numpy as np
from cv2.typing import MatLike


def slot_mask(
    img: MatLike,
    intensity: int = 35,
    slot_width: int = 6,
    slot_height: int = 12,
    gap: int = 2
) -> MatLike:
    """
    Applies a CRT-style slot mask pattern with vertically aligned slots.

    intensity:
        0   -> no mask
        100 -> strongest mask

    slot_width:
        Width, in pixels, of each RGB slot group.

    slot_height:
        Height, in pixels, of the lit phosphor block before a dark gap.

    gap:
        Size, in pixels, of the dark separator between slot blocks.

    The mask alternates the vertical phase between neighboring columns so the
    slots form two interleaved heights across the horizontal axis.
    """

    if intensity <= 0:
        return img

    h, w = img.shape[:2]

    slot_width = max(3, int(slot_width))
    slot_height = max(1, int(slot_height))
    gap = max(0, int(gap))

    img_f = img.astype(np.float32)

    # Base brightness reduction for masked regions.
    strength = np.clip(intensity / 100.0, 0.0, 1.0)
    dark_level = 1.0 - (0.55 * strength)

    mask = np.ones((h, w, 3), dtype=np.float32)

    x = np.arange(w)
    y = np.arange(h)

    column_idx = x // slot_width
    group_idx = column_idx % 3
    pitch = max(1, slot_height + gap)
    slot_idx = column_idx // 3
    column_phase = (slot_idx % 2) * (pitch // 2)
    row_phase = (y[:, None] - column_phase[None, :]) % pitch
    lit_area = row_phase < slot_height

    # Darken everything first, then light the active phosphor color more strongly.
    mask *= dark_level

    color_boost = dark_level + (1.0 - dark_level) * 0.95

    for channel in range(3):
        active_cols = group_idx == channel
        active_area = lit_area & active_cols[None, :]
        mask[:, :, channel][active_area] = color_boost

    # Slightly dim non-active channels even inside lit rows to reinforce separation.
    cross_talk = 1.0 - (0.18 * strength)
    for channel in range(3):
        active_cols = group_idx == channel
        active_area = lit_area & active_cols[None, :]
        for other_channel in range(3):
            if other_channel == channel:
                continue
            mask[:, :, other_channel][active_area] *= cross_talk

    out = img_f * mask
    return np.clip(out, 0, 255).astype(np.uint8)
