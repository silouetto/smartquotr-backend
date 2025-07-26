# services/vision.py

from services.parts import get_estimate, PART_DATABASE
from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
from fastapi import UploadFile
import easyocr
import shutil
import uuid
import os
import torch
import cv2
import traceback

# 🔁 Load models once
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
caption_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
reader = easyocr.Reader(['en'])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def caption_image(file: UploadFile):
    filename = f"temp_{uuid.uuid4().hex}.jpg"
    filepath = os.path.join(UPLOAD_DIR, filename)

    # 💾 Save uploaded file to disk
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # ✅ Ensure OpenCV can read it (guard against corrupted files)
    img = cv2.imread(filepath)
    if img is None:
        raise Exception("❌ Failed to read image. It may be corrupted or unsupported format.")

    # 🔍 Resize as preprocessing (optional, ensures consistency)
    resized = cv2.resize(img, (224, 224))

    # 🧠 BLIP captioning
    image = Image.open(filepath).convert("RGB")
    inputs = processor(images=image, return_tensors="pt")
    out = caption_model.generate(**inputs)
    caption = processor.decode(out[0], skip_special_tokens=True)

    image.load()  # ✅ Load fully to avoid lazy errors
    del image     # ✅ Free memory manually
    torch.cuda.empty_cache()  # ✅ Clears unused memory (safe on CPU too)

    return filepath, caption


def detect_part(image_path: str):
    import difflib
    import threading
    from services.parts import PART_DATABASE  # use updated monster DB

    try:
        print("📷 Reading text from:", image_path)

        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file does not exist: {image_path}")

        result = []

        def run_ocr():
            nonlocal result
            try:
                result = reader.readtext(image_path)
            except Exception as e:
                print("❌ OCR inner exception:", e)

        thread = threading.Thread(target=run_ocr)
        thread.start()
        thread.join(timeout=10)

        if thread.is_alive():
            print("❌ OCR timed out after 10s, killing attempt.")
            return {"name": "Unknown Component", "confidence": 0.0, "serial": None}

        text_hits = [res[1].lower() for res in result]

        for line in text_hits:
            match = difflib.get_close_matches(line, PART_DATABASE.keys(), n=1, cutoff=0.6)
            if match:
                part_name = match[0]
                price_info = get_estimate(part_name)
                print("🧠 Matched Part:", part_name)
                return {
                    "name": part_name,
                    "confidence": 0.8,
                    "serial": None,
                    "estimate": price_info.get("estimate", "Unknown"),
                    "category": price_info.get("category", "Unknown")
                }

        print("🔍 No match found in OCR text hits:", text_hits)
        return {"name": "Unknown Component", "confidence": 0.4, "serial": None}

    except Exception as e:
        print("❌ detect_part crashed:", str(e))
        traceback.print_exc()
        return {"name": "Unknown Component", "confidence": 0.0, "serial": None}

