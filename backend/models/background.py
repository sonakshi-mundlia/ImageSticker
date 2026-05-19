import torch
import cv2
import numpy as np

from PIL import Image
from torchvision import transforms
from models.u2net import U2NET


# ---------------------------------
# DEVICE
# ---------------------------------
device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)


# ---------------------------------
# LAZY MODEL (IMPORTANT FIX)
# ---------------------------------
net = None


def get_model():
    global net

    if net is None:
        print("🚀 Loading U2NET model (first request only)...")

        model = U2NET(3, 1)

        model.load_state_dict(
            torch.load(
                "models/weights/u2net.pth",
                map_location=device
            )
        )

        model.to(device)
        model.eval()

        net = model

        print("🔥 U2NET loaded successfully")

    return net


# ---------------------------------
# MASK REFINEMENT
# ---------------------------------
def refine_mask(mask_np):

    mask = (mask_np * 255).astype(np.uint8)

    kernel = np.ones((3, 3), np.uint8)

    mask = cv2.morphologyEx(
        mask, cv2.MORPH_CLOSE, kernel, iterations=1
    )

    mask = cv2.morphologyEx(
        mask, cv2.MORPH_OPEN, kernel, iterations=1
    )

    mask = cv2.GaussianBlur(mask, (5, 5), 0)

    return mask


# ---------------------------------
# MAIN FUNCTION
# ---------------------------------
def remove_background(image_input):

    # -----------------------------
    # INPUT HANDLING
    # -----------------------------
    if isinstance(image_input, str):
        img = Image.open(image_input).convert("RGB")

    elif isinstance(image_input, np.ndarray):
        img = Image.fromarray(image_input).convert("RGB")

    elif isinstance(image_input, Image.Image):
        img = image_input.convert("RGB")

    else:
        raise ValueError("Unsupported image input")

    original_size = img.size

    # -----------------------------
    # PREPROCESS
    # -----------------------------
    transform = transforms.Compose([
        transforms.Resize((320, 320)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])

    input_tensor = transform(img).unsqueeze(0).to(device)

    # -----------------------------
    # LOAD MODEL (LAZY)
    # -----------------------------
    model = get_model()

    # -----------------------------
    # INFERENCE
    # -----------------------------
    with torch.no_grad():
        d1, d2, d3, d4, d5, d6, d7 = model(input_tensor)

        pred = (d1 + d2 + d3 + d4 + d5 + d6 + d7) / 7.0
        pred = pred[:, 0, :, :]

        pred = (pred - pred.min()) / (pred.max() - pred.min() + 1e-8)

    # -----------------------------
    # TO NUMPY
    # -----------------------------
    mask_np = pred.squeeze().cpu().numpy()

    # -----------------------------
    # REFINE MASK
    # -----------------------------
    mask = refine_mask(mask_np)

    # -----------------------------
    # RESIZE BACK
    # -----------------------------
    mask = cv2.resize(
        mask,
        original_size,
        interpolation=cv2.INTER_CUBIC
    )

    # -----------------------------
    # FINAL SMOOTHING
    # -----------------------------
    mask = cv2.GaussianBlur(mask, (3, 3), 0)

    # -----------------------------
    # BUILD RGBA
    # -----------------------------
    rgba = np.array(img.convert("RGBA"))
    rgba[:, :, 3] = mask

    return rgba