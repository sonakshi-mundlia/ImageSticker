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
# DEVICE MODELS (LAZY LOADING)
# =====================================================
YOLO_MODEL = None
MP_SEGMENTER = None


def get_yolo():
    global YOLO_MODEL

    if YOLO_MODEL is None:
        print("🚀 Loading YOLO model...")

        YOLO_MODEL = YOLO(YOLO_PATH)

        print("🔥 YOLO loaded")

    return YOLO_MODEL


def get_mediapipe():
    global MP_SEGMENTER

    if MP_SEGMENTER is None:
        print("🚀 Loading MediaPipe model...")

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

        MP_SEGMENTER = image_segmenter.create_from_options(options)

        print("🔥 MediaPipe loaded")

    return MP_SEGMENTER


# =====================================================
# COCO CLASS IDS
# =====================================================
PERSON_CLASS = 0

ANIMAL_CLASSES = [
    14, 15, 16, 17, 18, 19, 21, 22, 23
]


# =====================================================
# MASK CLEANUP
# =====================================================
def refine_mask(mask):
    alpha = (mask * 255).astype(np.uint8)

    kernel = np.ones((3, 3), np.uint8)

    alpha = cv2.morphologyEx(alpha, cv2.MORPH_OPEN, kernel)
    alpha = cv2.morphologyEx(alpha, cv2.MORPH_CLOSE, kernel)
    alpha = cv2.GaussianBlur(alpha, (5, 5), 0)

    return alpha


# =====================================================
# HUMAN SEGMENTATION
# =====================================================
def segment_human_face(bgr_image):

    mp_segmenter = get_mediapipe()

    rgb_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)

    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb_image
    )

    result = mp_segmenter.segment(mp_image)

    category_mask = result.category_mask.numpy_view()

    human_mask = np.logical_or(
        category_mask == 1,
        category_mask == 3
    )

    alpha = refine_mask(human_mask)

    b, g, r = cv2.split(bgr_image)

    rgba = cv2.merge([b, g, r, alpha])

    return rgba


# =====================================================
# DETECT SUBJECT TYPE
# =====================================================
def detect_subject_type(bgr_image):

    model = get_yolo()
    results = model(bgr_image)

    boxes = results[0].boxes

    humans = []
    animals = []

    if boxes is None or len(boxes) == 0:
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
def crop_animal_head(image, box):

    x1, y1, x2, y2 = box

    height = y2 - y1

    head_y2 = y1 + int(height * 0.45)

    return image[y1:head_y2, x1:x2]


# =====================================================
# MAIN FUNCTION
# =====================================================
def process_image(image_bytes):

    np_arr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if image is None:
        raise ValueError("Invalid image")

    subject_type, boxes = detect_subject_type(image)

    print(f"Detected: {subject_type}, count: {len(boxes)}")

    faces = []

    if subject_type == "human":

        for box in boxes:
            x1, y1, x2, y2 = box

            face_crop = image[y1:y2, x1:x2]

            # ⚠️ keep only ONE processing (avoid double heavy load)
            rgba = remove_background(face_crop)

            faces.append(rgba)

    elif subject_type == "animal":

        for box in boxes:
            animal = crop_animal_head(image, box)
            rgba = remove_background(animal)
            faces.append(rgba)

    else:
        rgba = remove_background(image)
        faces.append(rgba)

    return faces