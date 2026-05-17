from utils.image_utils import preprocess, postprocess
from PIL import Image
import torch

def predict(model, image_path):
    image = Image.open(image_path).convert("RGB")
    inp = preprocess(image)

    with torch.no_grad():
        out = model(inp)

    result = postprocess(out[0], image)
    return result