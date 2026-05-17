import cv2
import mediapipe as mp
import numpy as np

from ultralytics import YOLO
from models.background import remove_background


# =====================================================
# CONFIG
# =====================================================
YOLO_PATH = "models/weights/yolov8n.pt"
MP_MODEL_PATH = "models/path/selfie_multiclass_256x256.tflite"


# =====================================================
# LOAD MODELS ONCE
# =====================================================
print("Loading models...")


def load_mediapipe():
    base_options = mp.tasks.BaseOptions
    image_segmenter = mp.tasks.vision.ImageSegmenter
    image_segmenter_options = mp.tasks.vision.ImageSegmenterOptions

    options = image_segmenter_options(
        base_options=base_options(
            model_asset_path=MP_MODEL_PATH
        ),
        running_mode=mp.tasks.vision.RunningMode.IMAGE,
        output_category_mask=True
    )

    return image_segmenter.create_from_options(options)


YOLO_MODEL = YOLO(YOLO_PATH)
MP_SEGMENTER = load_mediapipe()

print("Models loaded.")


# =====================================================
# COCO CLASS IDS
# =====================================================
PERSON_CLASS = 0

ANIMAL_CLASSES = [
    14,  # bird
    15,  # cat
    16,  # dog
    17,  # horse
    18,  # sheep
    19,  # cow
    21,  # bear
    22,  # zebra
    23   # giraffe
]


# =====================================================
# MASK CLEANUP
# =====================================================
def refine_mask(mask):
    alpha = (mask * 255).astype(np.uint8)

    kernel = np.ones((3, 3), np.uint8)

    alpha = cv2.morphologyEx(
        alpha,
        cv2.MORPH_OPEN,
        kernel
    )

    alpha = cv2.morphologyEx(
        alpha,
        cv2.MORPH_CLOSE,
        kernel
    )

    alpha = cv2.GaussianBlur(
        alpha,
        (5, 5),
        0
    )

    return alpha


# =====================================================
# HUMAN FACE + HAIR
# =====================================================
def segment_human_face(bgr_image):
    rgb_image = cv2.cvtColor(
        bgr_image,
        cv2.COLOR_BGR2RGB
    )

    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb_image
    )

    result = MP_SEGMENTER.segment(
        mp_image
    )

    category_mask = (
        result.category_mask
        .numpy_view()
    )

    # Hair + face skin
    human_mask = np.logical_or(
        category_mask == 1,
        category_mask == 3
    )

    alpha = refine_mask(
        human_mask
    )

    b, g, r = cv2.split(
        bgr_image
    )

    rgba = cv2.merge([
        b,
        g,
        r,
        alpha
    ])

    return rgba


# =====================================================
# DETECT SUBJECT TYPE
# =====================================================
def detect_subject_type(bgr_image):
    results = YOLO_MODEL(bgr_image)
    boxes = results[0].boxes

    humans = []
    animals = []

    if len(boxes) == 0:
        return "object", []

    for box in boxes:
        cls_id = int(box.cls[0])

        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)

        if cls_id == PERSON_CLASS:
            humans.append((x1, y1, x2, y2))

        elif cls_id in ANIMAL_CLASSES:
            animals.append((x1, y1, x2, y2))

    if len(humans) > 0:
        return "human", humans

    if len(animals) > 0:
        return "animal", animals

    return "object", []


# =====================================================
# ANIMAL HEAD CROP
# =====================================================
def crop_animal_head(
    image,
    box
):
    x1, y1, x2, y2 = box

    height = y2 - y1

    head_y2 = y1 + int(
        height * 0.45
    )

    crop = image[
        y1:head_y2,
        x1:x2
    ]

    return crop


# =====================================================
# MAIN ROUTER
# =====================================================
def process_image(image_bytes):

    np_arr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if image is None:
        raise ValueError("Invalid image")

    subject_type, boxes = detect_subject_type(image)

    print(f"Detected: {subject_type}, count: {len(boxes)}")

    faces = []

    # ================================
    # HUMAN MULTI FACE
    # ================================
    if subject_type == "human":

        for box in boxes:
            x1, y1, x2, y2 = box

            face_crop = image[y1:y2, x1:x2]

            rgba = segment_human_face(face_crop)
            rgba = remove_background(face_crop)

            faces.append(rgba)

    # ================================
    # ANIMAL MULTI
    # ================================
    elif subject_type == "animal":

        for box in boxes:
            animal = crop_animal_head(image, box)
            rgba = remove_background(animal)
            faces.append(rgba)

    # ================================
    # OBJECT SINGLE
    # ================================
    else:

        rgba = remove_background(image)
        faces.append(rgba)

    return faces