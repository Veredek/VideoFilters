from cv2.typing import MatLike

def original(frame: MatLike) -> MatLike:
    print("Filter: original")
    frame = frame.copy()
    return frame