import cv2
import numpy as np


# -----------------------------
# GLOBAL IMAGE FILTER ENGINE
# -----------------------------
def apply_filters(
    img,
    brightness=100,
    contrast=100,
    saturate=100,
    blur=0
):

    img = img.astype(np.float32)

    # BRIGHTNESS + CONTRAST
    img = img * (contrast / 100.0)
    img = img + (brightness - 100)

    img = np.clip(img, 0, 255)

    img = img.astype(np.uint8)

    # BLUR
    if blur > 0:
        k = blur if blur % 2 == 1 else blur + 1
        img = cv2.GaussianBlur(img, (int(k), int(k)), 0)

    # SATURATION
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)

    hsv[:, :, 1] *= (saturate / 100.0)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255)

    img = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    return img