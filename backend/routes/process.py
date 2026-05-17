from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import shutil
import uuid
import os

from services.pipeline import process_image

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# -----------------------------
# HEX → RGB CONVERTER
# -----------------------------
def normalize_color(color: str):
    """
    Accepts:
    - "#ffffff"
    - "255,255,255"
    Returns RGB tuple
    """

    if not color:
        return (255, 255, 255)

    color = color.strip()

    # HEX COLOR
    if color.startswith("#"):
        color = color.lstrip("#")

        if len(color) != 6:
            raise HTTPException(status_code=400, detail="Invalid hex color")

        return tuple(int(color[i:i+2], 16) for i in (0, 2, 4))

    # RGB COLOR
    try:
        return tuple(map(int, color.split(",")))
    except:
        raise HTTPException(status_code=400, detail="Invalid color format")


# -----------------------------
# FILE VALIDATION
# -----------------------------
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "pdf"}
MAX_SIZE_MB = 10


def validate_file(file: UploadFile):
    filename = file.filename.lower()

    # extension check
    if "." not in filename:
        raise HTTPException(status_code=400, detail="Invalid file")

    ext = filename.split(".")[-1]

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Only {ALLOWED_EXTENSIONS} allowed"
        )


@router.post("/")
def process(
    file: UploadFile = File(...),
    mode: str = Form("full"),
    style: str = Form(None),

    brightness: float = Form(100),
    contrast: float = Form(100),
    rotate: float = Form(0),
    saturate: float = Form(100),
    blur: int = Form(0),

    border_size: int = Form(8),
    border_color: str = Form("0,255,255"),
):

    # ---------------- VALIDATE FILE ----------------
    validate_file(file)

    # size check (10MB)
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)

    if size > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    # ---------------- SAVE FILE ----------------
    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}.jpg")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    border_size = max(1, min(border_size, 80))

    # ---------------- COLOR NORMALIZATION ----------------
    outer = normalize_color(border_color)
    print("DEBUG COLOR:", outer)

    outer = (outer[2], outer[1], outer[0])

    # ---------------- PIPELINE ----------------
    result = process_image(
    file_path,
    mode=mode,
    style=style,
    brightness=brightness,
    contrast=contrast,
    rotate=rotate,
    saturate=saturate,
    blur=blur,
    border_size=border_size,
    border_color=outer
)

    if isinstance(result, dict):
        return {
        "url": result.get("url"),
        "faces": result.get("faces", [])
        }

    return {
    "url": result,
    "faces": []
    }