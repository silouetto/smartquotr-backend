# services/vision.py

from services.parts import get_estimate, PART_DATABASE
from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
from fastapi import UploadFile
import shutil
import uuid
import os
import cv2
import torch
import gc
import traceback
import psutil
import easyocr  # ✅ Moved to top
import difflib
import threading

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 🔁 Lazy-loaded global model variables
caption_processor = None
caption_model = None
reader = None  # Singleton OCR instance

def log_memory(label=""):
    proc = psutil.Process()
    used = proc.memory_info().rss / 1024**2
    print(f"🐏 {label} Memory used: {used:.2f} MB")

async def caption_image(file: UploadFile):
    global caption_processor, caption_model

    filename = f"temp_{uuid.uuid4().hex}.jpg"
    filepath = os.path.join(UPLOAD_DIR, filename)

    # 💾 Save file
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # ✅ Verify image is readable
    img = cv2.imread(filepath)
    if img is None:
        raise Exception("❌ Failed to read image. It may be corrupted or unsupported format.")

    # 🔍 Optional resize
    resized = cv2.resize(img, (224, 224))

    # 🧠 Load BLIP captioning model once
    if caption_processor is None or caption_model is None:
        print("📦 Loading BLIP captioning model...")
        caption_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        caption_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        log_memory("After BLIP load")

    image = Image.open(filepath).convert("RGB")
    image.load()
    inputs = caption_processor(images=image, return_tensors="pt")
    out = caption_model.generate(**inputs, max_new_tokens=250)
    caption = caption_processor.decode(out[0], skip_special_tokens=True)

    del image, inputs, out
    gc.collect()
    torch.cuda.empty_cache()
    log_memory("After captioning")

    return filepath, caption


def load_easyocr():
    global reader
    if reader is None:
        print("📦 Loading EasyOCR reader (singleton)...")
        reader = easyocr.Reader(['en'], gpu=False)
        log_memory("After EasyOCR load")


def detect_part(image_path: str):
    try:
        print("📷 Reading text from:", image_path)
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file does not exist: {image_path}")

        # ✅ Shrink image before OCR (optional)
        img = cv2.imread(image_path)
        if img is not None:
            resized = cv2.resize(img, (640, 480))
            cv2.imwrite(image_path, resized)

        # ✅ Load OCR reader once
        load_easyocr()

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
            print("❌ OCR timed out after 10s.")
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

