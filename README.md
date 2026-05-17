# StickSpark ✨

StickSpark is an AI-powered sticker generation platform that transforms normal images into high-quality custom stickers using computer vision and generative AI.

Users upload an image, and the system automatically detects the subject, removes the background, applies artistic styling, and generates a sticker-ready transparent image.

---

# What StickSpark Does

StickSpark can process:

- Human faces
- Animals
- Objects

The system automatically detects the subject type and applies the best AI pipeline to generate a clean sticker output.

Output:
- Transparent PNG sticker
- Stylized cartoon/art output
- High-quality cutout

---

# System Architecture

```text
User Upload
    │
    ▼
Frontend Interface
    │
    ▼
FastAPI Backend
    │
    ▼
Subject Detection
(YOLOv8)
    │
    ▼
Subject Routing
 ┌───────────────┬───────────────┬───────────────┐
 ▼               ▼               ▼
Human         Animal         Object
 │               │               │
 ▼               ▼               ▼
MediaPipe      U2Net         U2Net
Segmentation   Cutout        Cutout
 │               │               │
 └───────────────┴───────────────┘
                │
                ▼
Stable Diffusion
                │
                ▼
Sticker Output
```

---

# How It Works

## 1. Image Upload

User uploads an image.

Supported formats:
- JPG
- PNG
- JPEG

---

## 2. Subject Detection

YOLOv8 detects whether the image contains:

- Human
- Animal
- Object

Then routes it to the correct processing pipeline.

---

## 3. Segmentation

### Human Processing

MediaPipe extracts:

- Face
- Hair
- Facial regions

For better sticker quality.

### Animal/Object Processing

U2Net removes background while preserving:

- Fur
- Edges
- Fine object details

---

## 4. Style Generation

Stable Diffusion applies artistic styles like:

- Pixar
- Disney
- Anime
- Cartoon
- Comic
- Sketch
- Watercolor

---

## 5. Final Output

System generates:

- Transparent PNG sticker
- High-resolution image
- Download-ready output

---

# Technologies Used

## Frontend
- HTML
- CSS
- JavaScript
- Tailwind CSS

## Backend
- Python
- FastAPI

## Database
- MongoDB

## AI Models

### YOLOv8
Used for:
- Human detection
- Animal detection
- Object detection

### MediaPipe
Used for:
- Face segmentation
- Hair segmentation

### U2Net
Used for:
- Background removal
- Edge refinement

### Stable Diffusion XL
Used for:
- Artistic style transfer
- Cartoon generation

---

# Features

- Automatic subject detection
- Background removal
- AI styling
- Transparent sticker generation
- Multi-subject support
- Fast processing pipeline

---

# Future Enhancements

Planned improvements:

- WhatsApp sticker export
- Custom sticker borders
- Text overlays
- Mobile application
- Batch processing

---
