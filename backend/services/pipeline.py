import cv2
import uuid
import os
import numpy as np
from PIL import Image

from models.stable_diffusion import sd_stylize
from models.background import remove_background
from models.face import segment_human_face, detect_subject_type, crop_animal_head
from services.border import apply_border_style
from services.filters import apply_filters
from models.face import YOLO_MODEL

cv2.setUseOptimized(True)


# -----------------------------------
# SAFE SAVE (FIXED)
# -----------------------------------
def safe_save(path, img):

    if img is None:
        return False

    img = np.asarray(img)

    if len(img.shape) == 2:
        img = cv2.cvtColor(
            img,
            cv2.COLOR_GRAY2BGRA
        )

    elif len(img.shape) == 3:

        if img.shape[2] == 3:
            img = cv2.cvtColor(
                img,
                cv2.COLOR_BGR2BGRA
            )

        elif img.shape[2] != 4:
            raise ValueError(
                f"Unsupported channel count: {img.shape[2]}"
            )

    img = np.ascontiguousarray(
        img.astype(np.uint8)
    )

    return cv2.imwrite(path, img)


# -----------------------------------
# IMAGE LOADER
# -----------------------------------
def load_image(path):
    return np.array(Image.open(path).convert("RGB"))


def ensure_rgba(img):
    if img is None:
        return None

    if len(img.shape) == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)

    elif img.shape[2] == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)

    return img


# -----------------------------------
# STYLE APPLY (FIXED)
# -----------------------------------
def apply_style(img, style):
    if not style:
        return img

    return sd_stylize(img, style)
    
# -----------------------------------
# FINAL PROCESSING (FIXED)
# -----------------------------------
def finalize_steps(
    rgba,
    style=None,
    brightness=100,
    contrast=100,
    saturate=100,
    blur=0,
    rotate=0,
    border_size=0,
    border_color=(0, 255, 255)
):

    rgba = ensure_rgba(rgba)

    if rgba is None:
        return None

    # ---------------------------------
    # KEEP RGB for Stable Diffusion
    # ---------------------------------
    rgb = cv2.cvtColor(rgba, cv2.COLOR_RGBA2RGB)

    alpha = rgba[:, :, 3]

    # ---------------------------------
    # AI STYLING (RGB input)
    # ---------------------------------
    if style:
        rgb = apply_style(rgb, style)

    # ---------------------------------
    # Convert to BGR for OpenCV filters
    # ---------------------------------
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

    bgr = apply_filters(
        bgr,
        brightness=brightness,
        contrast=contrast,
        saturate=saturate,
        blur=blur
    )

    # ---------------------------------
    # Merge alpha
    # ---------------------------------
    h, w = bgr.shape[:2]

    alpha = cv2.resize(
        alpha,
        (w, h),
        interpolation=cv2.INTER_NEAREST
    )

    final = cv2.merge((
        bgr[:, :, 0],
        bgr[:, :, 1],
        bgr[:, :, 2],
        alpha
    ))

    # ---------------------------------
    # Rotation
    # ---------------------------------
    if rotate != 0:

        M = cv2.getRotationMatrix2D(
            (w // 2, h // 2),
            rotate,
            1.0
        )

        final = cv2.warpAffine(
            final,
            M,
            (w, h),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(0, 0, 0, 0)
        )
    print("Before border:", final.shape)
    print("Alpha pixels:", np.count_nonzero(final[:, :, 3]))

    # ---------------------------------
    # Border
    # ---------------------------------
    if border_size > 0:

        final = apply_border_style(
            final,
            style="simple",
            thickness=border_size,
            color=border_color
        )

    return final


# -----------------------------------
# MAIN PIPELINE
# -----------------------------------
def process_image(
    file_path,
    mode="full",
    style=None,
    brightness=100,
    contrast=100,
    rotate=0,
    saturate=100,
    blur=0,
    border_size=8,
    border_color=(0, 255, 255)
):

    os.makedirs("outputs", exist_ok=True)

    img = load_image(file_path)
    if img is None:
        raise ValueError("Invalid image")

    results = []

    # ================= FACE MODE =================
    if mode == "face":

        subject_type, box = detect_subject_type(img)

        if subject_type == "human":

            detections = YOLO_MODEL(img)[0]

            for b in detections.boxes:

                if int(b.cls[0]) != 0:
                    continue

                x1, y1, x2, y2 = map(int, b.xyxy[0])
                h, w = img.shape[:2]

                x1 = max(0, x1)
                y1 = max(0, y1)

                x2 = min(w, x2)
                y2 = min(h, y2)

                if x2 <= x1 or y2 <= y1:
                    continue

                face = img[y1:y2, x1:x2]
                rgba = segment_human_face(face)

                processed = finalize_steps(
                    rgba, style, brightness, contrast,
                    saturate, blur, rotate,
                    border_size, border_color
                )

                filename = f"human_{uuid.uuid4()}.png"
                path = f"outputs/{filename}"
                safe_save(path, processed)

                results.append({"face_url": f"/outputs/{filename}"})

        elif subject_type == "animal":

            animal = crop_animal_head(img, box)
            rgba = remove_background(animal)

            processed = finalize_steps(
                rgba, style, brightness, contrast,
                saturate, blur, rotate,
                border_size, border_color
            )

            filename = f"animal_{uuid.uuid4()}.png"
            path = f"outputs/{filename}"
            safe_save(path, processed)

            results.append({"face_url": f"/outputs/{filename}"})

        else:

            rgba = remove_background(img)

            processed = finalize_steps(
                rgba, style, brightness, contrast,
                saturate, blur, rotate,
                border_size, border_color
            )

            filename = f"object_{uuid.uuid4()}.png"
            path = f"outputs/{filename}"
            safe_save(path, processed)

            results.append({"face_url": f"/outputs/{filename}"})

        return {"mode": "face", "faces": results}

    # ================= FULL MODE =================
    rgba = remove_background(img)

    processed = finalize_steps(
        rgba, style, brightness, contrast,
        saturate, blur, rotate,
        border_size, border_color
    )

    filename = f"full_{uuid.uuid4()}.png"
    path = f"outputs/{filename}"
    safe_save(path, processed)

    return {
        "mode": "full",
        "url": f"/outputs/{filename}"
    }