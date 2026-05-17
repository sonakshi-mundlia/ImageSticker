import cv2
import numpy as np


# ==========================================
# SIMPLE BORDER (FIXED)
# ==========================================
def style_simple(rgba, thickness=30, color=(255, 255, 255)):

    print("\n[SIMPLE BORDER]")
    print("Thickness:", thickness)
    print("Color:", color)

    color = tuple(color)

    b, g, r, alpha = cv2.split(rgba)
    h, w = alpha.shape[:2]

    # safe clamp
    thickness = max(1, min(thickness, 80))

    if thickness <= 0:
        thickness = max(30, int(min(h, w) * 0.02))

    kernel_size = thickness * 2 + 1

    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (kernel_size, kernel_size)
    )

    iterations = max(2, thickness // 6)

    print("Kernel:", kernel_size)
    print("Iterations:", iterations)

    dilated = cv2.dilate(alpha, kernel, iterations=iterations)

    border_mask = cv2.subtract(dilated, alpha)

    # strengthen mask
    border_mask = cv2.GaussianBlur(border_mask, (5, 5), 0)
    border_mask = cv2.normalize(border_mask, None, 0, 255, cv2.NORM_MINMAX)

    mask = border_mask > 20

    result = rgba.copy()

    # =========================
    # 1. RESTORE OBJECT FIRST
    # =========================
    object_mask = alpha > 0

    for i in range(3):
        result[:, :, i] = np.where(
            object_mask,
            rgba[:, :, i],
            result[:, :, i]
        )

    # =========================
    # 2. APPLY BORDER ON TOP
    # =========================
    for i in range(3):
        result[:, :, i] = np.where(
            mask,
            color[i],
            result[:, :, i]
        )

    # =========================
    # ALPHA MERGE
    # =========================
    result[:, :, 3] = np.maximum(alpha, border_mask)

    return result


# ==========================================
# SHINY BORDER (FIXED)
# ==========================================
def style_shiny(rgba, thickness=30, color=(255, 255, 255)):

    print("\n[SHINY BORDER]")
    print("Thickness:", thickness)
    print("Color:", color)

    color = tuple(color)

    b, g, r, alpha = cv2.split(rgba)

    thickness = max(1, min(thickness, 80))

    kernel_size = thickness * 2 + 1

    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (kernel_size, kernel_size)
    )

    iterations = max(2, thickness // 6)

    # =========================
    # BORDER GLOW MASK
    # =========================
    dilated = cv2.dilate(alpha, kernel, iterations=iterations)

    border_mask = cv2.subtract(dilated, alpha)

    border_mask = cv2.GaussianBlur(border_mask, (15, 15), 0)

    border_mask = cv2.normalize(
        border_mask,
        None,
        0,
        255,
        cv2.NORM_MINMAX
    )

    mask = border_mask > 20

    result = rgba.copy()

    # =========================
    # STEP 1: KEEP OBJECT FIRST
    # =========================
    object_mask = alpha > 0

    for i in range(3):
        result[:, :, i] = np.where(
            object_mask,
            rgba[:, :, i],
            result[:, :, i]
        )

    # =========================
    # STEP 2: APPLY SHINY BORDER ON TOP
    # =========================
    for i in range(3):
        result[:, :, i] = np.where(
            mask,
            color[i],
            result[:, :, i]
        )

    # =========================
    # STEP 3: ADD LIGHT GLOW (OPTIONAL BUT IMPORTANT)
    # =========================
    glow = np.full(alpha.shape, 255, dtype=np.uint8)

    for i in range(3):
        result[:, :, i] = cv2.addWeighted(
            result[:, :, i],
            1.0,
            glow,
            0.10,   # subtle shine effect
            0
        )

    # =========================
    # ALPHA MERGE
    # =========================
    result[:, :, 3] = np.maximum(alpha, border_mask)

    return result


# ==========================================
# NEON BORDER (FIXED)
# ==========================================
def style_neon(rgba, thickness=30, color=(0, 255, 255)):

    print("\n[NEON BORDER]")
    print("Thickness:", thickness)
    print("Color:", color)

    color = tuple(color)

    b, g, r, alpha = cv2.split(rgba)

    thickness = max(1, min(thickness, 80))

    iterations = max(2, thickness // 6)

    # =========================
    # GLOW GENERATION
    # =========================
    glow = cv2.dilate(
        alpha,
        np.ones((5, 5), np.uint8),
        iterations=iterations
    )

    glow = cv2.GaussianBlur(
        glow,
        (thickness * 2 + 1, thickness * 2 + 1),
        0
    )

    result = rgba.copy()

    # =========================
    # APPLY NEON GLOW FIRST
    # =========================
    mask = glow > 10

    for i in range(3):
        color_layer = np.full(alpha.shape, color[i], dtype=np.uint8)

        result[:, :, i] = np.where(
            mask,
            cv2.addWeighted(
                result[:, :, i],
                0.3,   # darker base for neon pop
                color_layer,
                0.9,   # stronger glow
                0
            ),
            result[:, :, i]
        )

    # =========================
    # KEEP OBJECT ON TOP (SAFE)
    # =========================
    object_mask = alpha > 0

    for i in range(3):
        result[:, :, i] = np.where(
            object_mask,
            rgba[:, :, i],
            result[:, :, i]
        )

    # =========================
    # FINAL ALPHA MERGE
    # =========================
    result[:, :, 3] = np.maximum(alpha, glow)

    return result


# ==========================================
# DOUBLE BORDER (FIXED)
# ==========================================
def style_double(rgba, thickness=30, color=(0, 255, 255)):

    print("\n[DOUBLE BORDER]")
    print("Thickness:", thickness)
    print("Color:", color)

    color = tuple(color)

    # Outer colored border
    outer = style_simple(
        rgba,
        thickness=thickness,
        color=color
    )

    # Inner white highlight (smaller, softer)
    inner = style_simple(
        rgba,
        thickness=max(3, thickness // 4),
        color=(255, 255, 255)
    )

    # Combine properly (IMPORTANT FIX)
    combined = np.where(
        inner[:, :, 3:4] > 0,
        inner,
        outer
    )

    return combined


# ==========================================
# MAIN CONTROLLER
# ==========================================
def apply_border_style(
    rgba,
    style="simple",
    thickness=10,
    color=(255, 255, 255)
):

    thickness = max(1, min(thickness, 80))
    color = tuple(color)

    if style == "simple":
        return style_simple(rgba, thickness, color)

    elif style == "shiny":
        return style_shiny(rgba, thickness, color)

    elif style == "neon":
        return style_neon(rgba, thickness, color)

    elif style == "double":
        return style_double(rgba, thickness, color)

    return rgba