from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import shutil
import uuid
import os

from services.pipeline import process_image

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ---------------------------------
# COLOR NORMALIZER
# ---------------------------------
def normalize_color(color: str):

    if not color:
        return (255, 255, 255)

    color = color.strip()

    if color.startswith("#"):
        color = color.lstrip("#")

        if len(color) != 6:
            raise HTTPException(status_code=400, detail="Invalid hex color")

        return tuple(int(color[i:i+2], 16) for i in (0, 2, 4))

    try:
        return tuple(map(int, color.split(",")))
    except:
        raise HTTPException(status_code=400, detail="Invalid color format")


# ---------------------------------
# FILE VALIDATION
# ---------------------------------
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
MAX_SIZE_MB = 10


def validate_file(file: UploadFile):

    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    filename = file.filename.lower()

    if "." not in filename:
        raise HTTPException(status_code=400, detail="Invalid file")

    ext = filename.split(".")[-1]

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Only {ALLOWED_EXTENSIONS} allowed"
        )


# ---------------------------------
# MAIN API
# ---------------------------------
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

    # ---------------- VALIDATION ----------------
    validate_file(file)

    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)

    if size > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    # ---------------- SAVE FILE (KEEP ORIGINAL EXTENSION) ----------------
    ext = file.filename.split(".")[-1].lower()
    file_id = str(uuid.uuid4())

    file_path = os.path.join(UPLOAD_DIR, f"{file_id}.{ext}")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # ---------------- BORDER ----------------
    border_size = max(1, min(border_size, 80))

    outer = normalize_color(border_color)
    outer = (outer[2], outer[1], outer[0])  # RGB → BGR

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

    # ---------------- RESPONSE ----------------
    if isinstance(result, dict):
        return {
            "url": result.get("url"),
            "faces": result.get("faces", [])
        }

    return {
        "url": result,
        "faces": []
    }