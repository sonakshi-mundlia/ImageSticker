import torch
from PIL import Image
import numpy as np
import threading
import random
from diffusers import StableDiffusionXLImg2ImgPipeline


# ------------------------------------
# GLOBAL STATE
# ------------------------------------
pipe = None
pipe_loading = False

device = "cuda" if torch.cuda.is_available() else "cpu"


# ------------------------------------
# BACKGROUND LOADER
# ------------------------------------
def _load_pipe_background():
    global pipe, pipe_loading

    if pipe is not None or pipe_loading:
        return

    pipe_loading = True
    print("🚀 SDXL loading in background...")

    model = StableDiffusionXLImg2ImgPipeline.from_pretrained(
        "stabilityai/sdxl-turbo",
        torch_dtype=torch.float16 if device == "cuda" else torch.float32
    ).to(device)

    # Memory optimization
    model.enable_attention_slicing()

    if device == "cuda":
        model.enable_vae_slicing()

    pipe = model
    pipe_loading = False

    print("🔥 SDXL model loaded successfully")


# ------------------------------------
# SAFE PUBLIC LOADER
# ------------------------------------
def load_pipe():
    global pipe

    if pipe is not None:
        return pipe

    threading.Thread(
        target=_load_pipe_background,
        daemon=True
    ).start()

    return None


# ------------------------------------
# BETTER STYLE PROMPTS
# ------------------------------------
STYLE_MAP = {
    "pixar": "masterpiece, best quality, pixar animated character, 3d animated movie character, expressive eyes, soft rounded facial features, charming smile, smooth skin shading, cinematic lighting, colorful, detailed hair, studio render, octane render",
    "disney": "masterpiece, best quality, disney animated movie character, magical animation style, expressive eyes, soft facial proportions, beautiful skin shading, charming smile, cinematic lighting, detailed hair, professional studio render",
    "comic": "masterpiece, best quality, comic book character, bold ink outlines, dramatic shadows, high contrast, dynamic character portrait, highly detailed illustration",
    "3d": "masterpiece, best quality, cinematic 3d character render, ultra detailed, realistic skin shading, octane render, global illumination, professional lighting",
    "anime": "masterpiece, best quality, anime character portrait, large detailed eyes, soft face, beautiful anime shading, cinematic lighting, high detail artwork",
    "cartoon": "masterpiece, best quality, modern cartoon character, expressive eyes, rounded facial features, colorful, smooth shading, animation studio quality",
    "manga": "masterpiece, best quality, manga character portrait, black and white ink drawing, expressive face, detailed shading, dramatic composition",
    "chibi": "masterpiece, best quality, cute chibi character, oversized head, tiny body, kawaii face, sparkling eyes, colorful illustration",
    "watercolor": "masterpiece, best quality, watercolor portrait painting, soft brush strokes, paper texture, artistic colors, elegant portrait",
    "oil": "masterpiece, best quality, oil painting portrait, rich brush textures, classical painting style, museum quality, dramatic lighting",
    "popart": "masterpiece, best quality, pop art portrait, bold colors, graphic design, comic inspired, high contrast, modern artwork",
    "neon": "masterpiece, best quality, futuristic neon portrait, glowing lights, cyber aesthetic, colorful reflections, cinematic sci-fi lighting",
    "pixel": "masterpiece, best quality, pixel art character, retro 8-bit game style, sprite artwork, colorful pixel design",
    "cyberpunk": "masterpiece, best quality, cyberpunk character portrait, neon city lights, futuristic atmosphere, sci-fi cinematic lighting, ultra detailed",
    "sketch": "masterpiece, best quality, hand drawn sketch portrait, pencil lines, artistic shading, paper texture, expressive drawing",
    "pencil": "masterpiece, best quality, realistic pencil portrait, fine line work, detailed shading, artistic paper texture"
}


# ------------------------------------
# NEGATIVE PROMPT
# ------------------------------------
NEGATIVE_PROMPT = """
photorealistic,
realistic skin,
human photo,
ugly face,
deformed face,
asymmetrical face,
duplicate face,
extra eyes,
extra nose,
extra mouth,
blurry,
low quality,
bad anatomy,
watermark,
text,
noise
"""


# ------------------------------------
# UNIVERSAL IMAGE CONVERTER
# ------------------------------------
def _to_pil(image_input):

    if isinstance(image_input, Image.Image):
        return image_input.convert("RGB")

    if isinstance(image_input, str):
        return Image.open(image_input).convert("RGB")

    if isinstance(image_input, np.ndarray):

        if image_input.shape[-1] == 4:
            image_input = image_input[:, :, :3]

        return Image.fromarray(
            image_input.astype("uint8")
        ).convert("RGB")

    raise TypeError(
        f"Unsupported image type: {type(image_input)}"
    )


# ------------------------------------
# MAIN STYLIZER
# ------------------------------------
def sd_stylize(image_input, style="pixar"):
    global pipe

    load_pipe()

    if pipe is None:
        raise Exception("Model still loading...")

    prompt = STYLE_MAP.get(style, STYLE_MAP["pixar"])

    # Image preprocess
    image = _to_pil(image_input)

    # High quality input
    image = image.resize(
        (1024, 1024),
        Image.LANCZOS
    )

    # Different output every time
    seed = random.randint(1, 999999)

    with torch.inference_mode():

        generator = torch.Generator(
            device=device
        ).manual_seed(seed)

        result = pipe(
            prompt=prompt,
            negative_prompt=NEGATIVE_PROMPT,
            image=image,

            # Main tuning
            strength=0.82,
            num_inference_steps=6,
            guidance_scale=2.0,

            generator=generator
        ).images[0]

    return np.array(result)
