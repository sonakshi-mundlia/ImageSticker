import os
import replicate
import numpy as np
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

# load key safely
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN


# ------------------------------------
# STYLE MAP
# ------------------------------------
STYLE_MAP = {
    "pixar": "pixar animated character, 3d animated movie character, expressive eyes, cinematic lighting, colorful, studio quality",
    "disney": "disney animated character, magical animation style, cinematic lighting, soft face",
    "comic": "comic book style, bold outlines, dramatic shadows",
    "3d": "cinematic 3d render, ultra detailed, realistic lighting",
    "anime": "anime character portrait, large eyes, soft shading",
    "cartoon": "modern cartoon character, smooth shading, expressive face",
    "manga": "manga style black and white illustration",
    "chibi": "cute chibi character, small body big head kawaii",
    "watercolor": "watercolor painting, soft brush strokes",
    "oil": "oil painting portrait, classical art style",
    "popart": "pop art style, bold colors",
    "neon": "cyber neon glowing portrait",
    "pixel": "pixel art retro style",
    "cyberpunk": "cyberpunk neon futuristic portrait",
    "sketch": "pencil sketch drawing",
    "pencil": "detailed pencil drawing"
}


# ------------------------------------
# CONVERT IMAGE
# ------------------------------------
def _to_pil(image_input):
    if isinstance(image_input, Image.Image):
        return image_input.convert("RGB")

    if isinstance(image_input, str):
        return Image.open(image_input).convert("RGB")

    if isinstance(image_input, np.ndarray):
        if image_input.shape[-1] == 4:
            image_input = image_input[:, :, :3]
        return Image.fromarray(image_input.astype("uint8")).convert("RGB")

    raise TypeError("Unsupported input type")


# ------------------------------------
# MAIN FUNCTION
# ------------------------------------
def sd_stylize(image_input, style="pixar"):

    image = _to_pil(image_input)

    # IMPORTANT: reduce size (cost + speed)
    image = image.resize((768, 768))

    prompt = STYLE_MAP.get(style, STYLE_MAP["pixar"])

    try:
        output = replicate.run(
            "stability-ai/sdxl:latest",
            input={
                "prompt": prompt,
                "image": image,
                "strength": 0.75,
                "num_inference_steps": 4,
                "guidance_scale": 2
            }
        )

        return {
            "success": True,
            "image_url": output[0]
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }