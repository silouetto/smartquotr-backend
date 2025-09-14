# routes/analyze.py
from fastapi import APIRouter, UploadFile, File, Form, Request, Body
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse, Response
import uuid
import os
import traceback
import re
import difflib
import time
import copy
import psutil
import tempfile
import json        # ← make sure this is at the top
import shutil

from services.vision import caption_image, detect_part
from services.parts import get_estimate
from services.pdf_generator import create_pdf
from services.scraping import scrape_all_links
from services.ai_engine import generate_advice, generate_steps
from services.tutorials import get_youtube_tutorials
from utils.formatter import format_advice_structured, build_html_blocks
from utils.gpt_unlock import is_gpt4_unlocked, TEMP_UNLOCKS
from services.scraping import (
    scrape_amazon_links,
    scrape_walmart_links,
    scrape_harborfreight_links,
    scrape_autozone_links,
    wrap_named_links
)
from PIL import Image
import asyncio

router = APIRouter()

vague_words = {
    "tools", "materials", "equipment", "stuff", "things", "total", "estimated",
    "time", "cost", "optional", "titles", "youtube", "labor", "days", "hours"
}

noise_words = ["total", "estimated", "hour", "day", "cost", "range", "time", "paint", "soil mix", "stain"]

def normalize_kw(kw: str) -> str:
    return re.sub(r'[^a-z0-9]', '', kw.lower())

def looks_like_product_kw(kw: str) -> bool:
    if not kw: return False
    kw_clean = normalize_kw(kw)
    if len(kw_clean) < 4 or kw_clean in vague_words:
        return False
    if any(char.isdigit() for char in kw[:3]): return False
    if "$" in kw or " per " in kw.lower(): return False
    if re.search(r"\$\d+", kw): return False
    if " for " in kw.lower() and "$" in kw: return False
    if any(n in kw.lower() for n in noise_words): return False
    return True

def extract_keywords(structured: dict) -> set:
    keywords = set()
    for section, lines in structured.items():
        if "tools" in section.lower() or "materials" in section.lower():
            for line in lines:
                kw = re.sub(r'^\[\s*\]\s*[-•*]?\s*', '', line).strip()
                kw = re.sub(r'\s*\(.*?\)', '', kw).strip(" -:")
                kw_cleaned = kw.title()
                if looks_like_product_kw(kw_cleaned):
                    keywords.add(kw_cleaned)
    return keywords

def merge_unique_links(keywords: set, links: dict, store_matches: dict, store_keys: list):
    seen = set()
    for kw in keywords:
        kw_text = normalize_kw(kw)
        for store_key in store_keys:
            for link in links.get(store_key, []):
                if not isinstance(link, dict): continue
                label = normalize_kw(link.get("name", ""))
                url = link.get("url")
                if not url or not label or (kw_text, label, url) in seen: continue
                if kw_text in label or label in kw_text or difflib.SequenceMatcher(None, kw_text, label).ratio() > 0.5:
                    store_matches[store_key].append({"name": kw, "url": url})
                    seen.add((kw_text, label, url))
                    break
    return store_matches

@router.post("/analyze")
async def analyze_image(
    request: Request,
    file: UploadFile = File(...),
    intent: str = Form(...),
    description: str = Form(default=""),
    project_type: str = Form(...),
    steps: str = Form(default="off"),
    include_sketch: str = Form(default="off"),
    include_coupons: str = Form(default="off")
):
    start = time.time()
    try:
        print("\n" + "="*40)
        print("📩 /analyze HIT")
        if not file:
            return JSONResponse({"error": "❌ No file received."}, status_code=400)

        # -------------------------------
        # 📸 Image processing
        # -------------------------------
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        image.load()
        image.thumbnail((1024, 1024))
        file.file.seek(0)
        print(f"✅ Image loaded ({file.filename})")

        # -------------------------------
        # 🔗 Async tasks: caption, part detection, price, YouTube
        # -------------------------------
        async def caption_task(): 
            try: return await caption_image(file)
            except Exception as e: 
                print("❌ Caption failed:", e)
                return None, "❌ Caption failed"

        async def part_task(img_path): 
            try: return detect_part(img_path) if img_path else {"name": "Unknown Component"}
            except: traceback.print_exc(); return {"name": "Unknown Component"}

        async def price_task(part_info): 
            try: return get_estimate(part_info.get("name", "Unknown Component"))
            except: traceback.print_exc(); return None

        async def youtube_task(part_info): 
            try:
                if part_info.get("name") != "Unknown Component":
                    return get_youtube_tutorials(part_info["name"])
                return []
            except: traceback.print_exc(); return []

        image_path, caption = await caption_task()
        ai_part_info, ai_price_estimate, ai_tutorials = await asyncio.gather(
            part_task(image_path),
            price_task(ai_part_info := {"name": "Unknown Component"}),  # dummy initially
            youtube_task(ai_part_info)
        )

        # -------------------------------
        # 🧠 GPT advice
        # -------------------------------
        gpt4 = is_gpt4_unlocked(request)
        sketch_flag = False
        coupon_flag = False
        advice = generate_advice(
            intent, description, project_type, caption,
            include_steps=False, include_sketch=sketch_flag,
            include_coupons=coupon_flag, use_gpt4=gpt4
        )
        structured = format_advice_structured(advice)
        if not structured:
            raise Exception("❌ Failed to parse GPT advice")

        # -------------------------------
        # 🛠️ Keywords & Product Links
        # -------------------------------
        structured_keywords = extract_keywords(structured)
        search_blob = advice + "\n" + "\n".join(structured_keywords)
        links = scrape_all_links(search_blob, project_type, structured_keywords)
        store_keys = ["amazon_links", "walmart_links", "harborfreight_links", "autozone_links", "tonkinautoparts_links"]
        store_matches = {k: [] for k in store_keys}
        store_matches = merge_unique_links(structured_keywords, links, store_matches, store_keys)

        # Final "Helpful Product Links"
        structured["Helpful Product Links"] = [f"🔗 {kw.title()}" for kw in sorted(structured_keywords)]

        # -------------------------------
        # 🧾 PDF + HTML
        # -------------------------------
        pdf_id = f"{uuid.uuid4().hex}.pdf"
        output_dir = os.path.join(os.getcwd(), "generated_pdfs")
        os.makedirs(output_dir, exist_ok=True)
        pdf_path = os.path.join(output_dir, pdf_id)
        create_pdf(pdf_path, caption, intent, description, project_type, structured)
        html_blocks = build_html_blocks(structured, ai_tutorials=ai_tutorials)

        # -------------------------------
        # 🔗 Camel-case store links
        # -------------------------------
        snake_to_camel = {
            "amazon_links": "amazonLinks",
            "walmart_links": "walmartLinks",
            "harborfreight_links": "harborfreightLinks",
            "autozone_links": "autozoneLinks",
            "tonkinautoparts_links": "tonkinautopartsLinks",
        }
        camel_case_links = {snake_to_camel[k]: links.get(k, []) + store_matches.get(k, []) for k in store_keys if k in snake_to_camel}

        print("⏱️ /analyze total time:", round(time.time()-start,2),"s")
        return {
            "caption": caption,
            "category": project_type,
            "intent": intent,
            "user_description": description,
            "advice": html_blocks,
            "pdf_id": pdf_id,
            "ai_part_info": ai_part_info,
            "ai_price_estimate": ai_price_estimate,
            "ai_tutorials": ai_tutorials,
            "keywords": list(structured_keywords),
            **camel_case_links,
            "coupons": [item for sec, items in structured.items() if "coupon" in sec.lower() for item in items]
        }

    except Exception as e:
        traceback.print_exc()
        return JSONResponse({"error": f"Server error: {str(e)}"}, status_code=500)


@router.post("/steps")
async def get_step_by_step(data: dict):
    try:
        return {
            "steps": generate_steps(
                intent=data["intent"],
                description=data["description"],
                project_type=data["project_type"],
                caption=data["caption"]
            )
        }
    except Exception as e:
        return {"steps": f"❌ Failed to generate steps: {str(e)}"}


# updated pdf path
@router.get("/pdf/{pdf_id}")
async def get_pdf(pdf_id: str):
    path = os.path.join(os.getcwd(), "generated_pdfs", pdf_id)
    print("📤 PDF download request:", path)

    if os.path.exists(path):
        return FileResponse(path, media_type="application/pdf", filename="SmartQuotr_Estimate.pdf")
    return {"error": "PDF not found"}


# -------------------------------
# Helper functions
# -------------------------------

def send_email_copy(company_name, email, company_type, description, website=None):
    # Implement your existing email function here
    print(f"📧 Sending submission email for {company_name} to support@smartquotr.com")
    # You could also include `website` in the email
    return True



# took out methods GET and HEAD
@router.get("/", response_class=HTMLResponse)
async def serve_form():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return f.read()

@router.post("/gpt4-unlock")
async def unlock_gpt4(request: Request):
    ip = request.client.host

    # ⏳ Cooldown: only once per minute
    if ip in TEMP_UNLOCKS and time.time() - TEMP_UNLOCKS[ip] < 60:
        return {"message": "⏳ Please wait before unlocking again."}

    TEMP_UNLOCKS[ip] = time.time()
    return {"message": "✅ GPT-4 unlocked for 10 minutes"}

