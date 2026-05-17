from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routes.auth import router as auth_router
from routes.process import router as process_router
from routes.outputs import router as outputs_router

import os
import threading

# import your SDXL loader
from models.stable_diffusion import load_pipe  # 👈 IMPORTANT

app = FastAPI(
    title="AI Image Processing API",
    description="Background removal + Face detection + Style transfer API",
    version="1.0.0"
)

# ------------------------------------
# CORS
# ------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------
# OUTPUT DIR
# ------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

os.makedirs(OUTPUT_DIR, exist_ok=True)

app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")

print("OUTPUT DIR:", OUTPUT_DIR)


# ------------------------------------
# BACKGROUND SDXL LOADER
# ------------------------------------
def load_models_background():
    print("🚀 Starting background model loading...")
    load_pipe()  # this triggers SDXL load
    print("🔥 All models loaded in background")


# ------------------------------------
# STARTUP EVENT (NON-BLOCKING)
# ------------------------------------
@app.on_event("startup")
def startup_event():
    thread = threading.Thread(target=load_models_background, daemon=True)
    thread.start()


# ------------------------------------
# ROUTES
# ------------------------------------
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(process_router, prefix="/api/process", tags=["Image Processing"])
app.include_router(outputs_router, prefix="/api/outputs", tags=["Outputs"])


# ------------------------------------
# HEALTH CHECK
# ------------------------------------
@app.get("/")
def home():
    return {"status": "running", "message": "AI Image API is live 🚀"}

@app.get("/health")
def health():
    return {"status": "ok"}