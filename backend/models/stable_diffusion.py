import torch
from PIL import Image
import numpy as np
import random
from diffusers import StableDiffusionXLImg2ImgPipeline


# ------------------------------------
# GLOBAL STATE
# ------------------------------------
pipe = None

device = "cuda" if torch.cuda.is_available() else "cpu"


# ------------------------------------
# LAZY LOADER (SAFE)
# ------------------------------------
def get_pipe():
    global pipe

    if pipe is not None:
        return pipe

    print("🚀 Loading SDXL model (first request only)...")

    model = StableDiffusionXLImg2ImgPipeline.from_pretrained(
        "stabilityai/sdxl-turbo",
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        variant="fp16" if device == "cuda" else None
    ).to(device)

    # memory optimizations
    model.enable_attention_slicing()

    if device == "cuda":
        model.enable_vae_slicing()

    pipe = model

    print("🔥 SDXL loaded successfully")

    return pipe


# ------------------------------------
# STYLE MAP
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
# IMAGE CONVERTER
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

    raise TypeError(f"Unsupported type: {type(image_input)}")


# ------------------------------------
# MAIN FUNCTION
# ------------------------------------
def sd_stylize(image_input, style="pixar"):

    pipe = get_pipe()

    prompt = STYLE_MAP.get(style, STYLE_MAP["pixar"])

    image = _to_pil(image_input)

    # IMPORTANT: reduce memory load (1024 is too heavy for Render)
    image = image.resize((768, 768), Image.LANCZOS)

    seed = random.randint(1, 999999)

    with torch.inference_mode():

        generator = torch.Generator(device=device).manual_seed(seed)

        result = pipe(
            prompt=prompt,
            negative_prompt=NEGATIVE_PROMPT,
            image=image,
            strength=0.75,
            num_inference_steps=4,   # reduced for stability
            guidance_scale=2.0,
            generator=generator
        ).images[0]

    return np.array(result)
