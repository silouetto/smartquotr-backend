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
router = APIRouter()

# Updated ✅ DIAGNOSTIC ROUTE: isolate crash issues
@router.post("/analyze-test")
async def analyze_test(file: UploadFile = File(...)):
    import traceback

    try:
        print(f"📂 Starting analyze-test for: {file.filename}")
        contents = await file.read()
        print(f"📏 File size: {len(contents) / 1024:.2f} KB")

        # Try PIL just to confirm decode
        from PIL import Image
        import io
        image = Image.open(io.BytesIO(contents))
        image.verify()
        print("✅ Image verified successfully")

        mem_used = psutil.Process().memory_info().rss / 1024**2
        return {
            "filename": file.filename,
            "file_size_kb": round(len(contents) / 1024, 2),
            "memory_used_mb": round(mem_used, 2),
            "status": "✅ Upload and decode successful"
        }

    except Exception as e:
        print("❌ Exception during /analyze-test:")
        traceback.print_exc()

        return JSONResponse(
            {"error": f"❌ Failed to handle upload: {str(e)}"},
            status_code=500
        )    

# added options post cos workaround
@router.api_route("/analyze", methods=["POST", "OPTIONS"])
async def analyze_image(
    request: Request,
    file: UploadFile = File(None),
    intent: str = Form(None),
    description: str = Form(default=""),
    project_type: str = Form(None),
    steps: str = Form(default="off"),
    include_sketch: str = Form(default="off"),
    include_coupons: str = Form(default="off")
):
    if request.method == "OPTIONS":
        return JSONResponse(content={"message": "Preflight OK"}, status_code=200)
   
    start = time.time()
    print("📩 /analyze route HIT")

    # ✅ Added this validation block below
    if not file:
        return JSONResponse({"error": "❌ No file received."}, status_code=400)

    print("📸 Uploaded file:", file.filename)

    try:
        contents = await file.read()
        from PIL import Image
        import io
        img_bytes = io.BytesIO(contents) # NEW
        image = Image.open(io.BytesIO(contents))
        image.load() #new from verify
        file.file.seek(0)
    except Exception as e:
        print("❌ Image decode failed:", str(e))
        return JSONResponse({
            "error": "Server error: ❌ Failed to read image. It may be corrupted or unsupported format."
        }, status_code=500)
    
    # Rewind bytes and open again (verify() closes it)
    img_bytes.seek(0)
    image = Image.open(img_bytes)

    # ✅ Resize to reduce memory usage
    image.thumbnail((1024, 1024))  # Resize in-place, keeps aspect ratio

    # Optional: if you pass image onward (e.g. to `caption_image`)
    # convert to file-like again if needed
    image_io = io.BytesIO()
    image.save(image_io, format='JPEG')
    image_io.seek(0)
    
    try:
        print("📸 Starting captioning...")
        image_path, caption = await caption_image(file)
        print("📸 Captioning complete:", caption)

        print("🤖 Starting part detection...")
        ai_part_info = detect_part(image_path)
        print("🤖 Part detected:", ai_part_info)
        print("⏱️ Detect part took", time.time() - start, "seconds")

        ai_price_estimate = get_estimate(ai_part_info["name"])
        
        ai_tutorials = []
        try:
            if ai_part_info.get("name") and ai_part_info["name"] != "Unknown Component":
                ai_tutorials = get_youtube_tutorials(ai_part_info["name"])
        except Exception as e:
            print("⚠️ YouTube fetch failed:", str(e))
        

        gpt4 = is_gpt4_unlocked(request)

        # Only include flags if using GPT-4
        sketch_flag = False # took out include_sketch and coupons
        coupon_flag = False
        
        # Get advice from GPT
        # ----------------------------- Analyze Core (Inside /analyze) -----------------------------
        # 🧠 Advice from GPT
        advice = generate_advice(intent, description, project_type, caption, include_steps=False, include_sketch=sketch_flag, include_coupons=coupon_flag, use_gpt4=gpt4)
        print("🧠 GPT advice:\n", advice)

        if not advice or not isinstance(advice, str):
            raise Exception("❌ No advice returned from GPT")

        # 🧱 Structure advice
        structured = format_advice_structured(advice)
        
        # ✅ Extract coupon section if enabled
        if coupon_flag:
            coupon_lines = []
            for section, lines in structured.items():
                if "coupon" in section.lower() or "promo" in section.lower():
                    coupon_lines.extend(line.strip("-• ") for line in lines if line.strip())
    
            if coupon_lines:
                # Rename the section to something user-friendly and deduplicated
                structured["Exclusive Coupons"] = list(dict.fromkeys(coupon_lines))


        structured = copy.deepcopy(structured)

        if not structured:
            raise Exception("❌ Failed to parse structured advice from GPT")

                # 🧹 Define vague or non-product-like words to exclude
        vague_words = {
            "tools", "materials", "equipment", "stuff", "things", "total", "estimated",
            "time", "cost", "optional", "titles", "youtube", "labor", "days", "hours"
        }

        def normalize_kw(kw):
            return re.sub(r'[^a-z0-9]', '', kw.lower())

        def looks_like_product_kw(kw):
            if not kw:
                return False
            kw_clean = normalize_kw(kw)
            if len(kw_clean) < 4:
                return False
            if kw_clean in vague_words:
                return False
            if any(char.isdigit() for char in kw[:3]):
                return False
            if "$" in kw or " per " in kw.lower():
                return False
            if re.search(r"\$\d+", kw):
                return False
            if " for " in kw.lower() and "$" in kw:
                return False
            noise = ["total", "estimated", "hour", "day", "cost", "range", "time", "paint", "soil mix", "stain"]
            if any(n in kw.lower() for n in noise):
                return False
            return True

        # ✅ Extract structured keywords from only tools/materials
        structured_keywords = set()

        for section, lines in structured.items():
            if "tools" in section.lower() or "materials" in section.lower():
                for line in lines:
                    # 🧹 Remove checkbox/bullet/parentheses
                    kw = re.sub(r'^\[\s*\]\s*[-•*]?\s*', '', line).strip()
                    kw = re.sub(r'\s*\(.*?\)', '', kw)
                    kw = kw.strip(" -:")  # Trim edge punctuation

                    # 🧼 Normalize and check
                    kw_cleaned = kw.title()
                    if looks_like_product_kw(kw_cleaned):
                        structured_keywords.add(kw_cleaned)
                    else:
                        print("🚫 Filtered non-product:", kw)


        # 🔁 Merge advice with extracted tool/materials to create better scraping context
        search_blob = advice + "\n" + "\n".join(structured_keywords)


        # ✅ Ensure "Helpful Product Links" section exists
        if "Helpful Product Links" not in structured:
            structured["Helpful Product Links"] = []

        clean_keywords = set()
        for raw in structured_keywords:
            cleaned = re.sub(r'^\[\s*\]\s*', '', raw).strip()
            cleaned = re.sub(r'\s*\(.*?\)', '', cleaned).strip(" -:")
            clean_keywords.add(cleaned.title())



        # 🔗 Scrape product links using full search blob
        links = scrape_all_links(search_blob, project_type, clean_keywords)
        
        # ✅ Inject clean keywords directly into the structured section
        structured["Helpful Product Links"] = [f"🔗 {kw}" for kw in sorted(set(clean_keywords))]

        print("🧾 Cleaned keywords for product search:", clean_keywords)

        # ✅ Fuzzy match helpers
        def is_fuzzy_match(a: str, b: str) -> bool:
            return (
                a in b or
                b in a or
                difflib.SequenceMatcher(None, a, b).ratio() > 0.5
            )
        # COMMENTED OUT EXTRA STORE LINKS
        store_keys = [
            "amazon_links",
            "walmart_links",
            "harborfreight_links",
            "autozone_links",
            # "homedepot_links",
            # "temu_links",
            # "bestbuy_links",
            # "oreilly_links",
            # "napa_links"
            # "carparts_links",
        ]

        store_matches = {key: [] for key in store_keys}
        seen = set()  # For deduplication

        try:
            for kw in structured_keywords:
                kw_text = normalize_kw(kw)

                for store_key in store_keys:
                    for link in links.get(store_key, []):
                        if not isinstance(link, dict):
                            continue

                        label = normalize_kw(link.get("name", ""))
                        url = link.get("url")

                        if not url or not label:
                            continue

                        if (kw_text, label, url) in seen:
                            continue

                        if is_fuzzy_match(kw_text, label):
                            store_matches[store_key].append({
                                "name": kw,
                                "url": url
                            })
                            seen.add((kw_text, label, url))
                            break
        except Exception as match_err:
            print("🚨 Matching failed:", match_err)

        # ✅ Append unique matches to each store tab
        for store_key in store_keys:
            existing_urls = set(normalize_kw(link.get("url", "")) for link in links[store_key])
            for match in store_matches[store_key]:
                if normalize_kw(match["url"]) not in existing_urls:
                    links[store_key].append(match)
                    existing_urls.add(normalize_kw(match["url"]))


       
        if not structured.get("Tools Needed") and not structured.get("Materials"):
            return JSONResponse(content={"error": "Could not extract valid tools or materials."}, status_code=400)

        # Build final list once, safely
        helpful_links_final = []
        seen_links = set()
        for kw in sorted(set(clean_keywords)):
            kw_clean = re.sub(r'\s*\(.*?\)', '', kw).strip(" -:")
            if kw_clean.lower() not in seen_links:
                helpful_links_final.append(f"🔗 {kw_clean.title()}")
                seen_links.add(kw_clean.lower())

        structured["Helpful Product Links"] = helpful_links_final




        # 🧱 Build HTML + PDF
        # ✅ Generate UUID-based filename
        pdf_id = f"{uuid.uuid4().hex}.pdf"

        # ✅ Use persistent local directory for storage
        output_dir = os.path.join(os.getcwd(), "generated_pdfs")
        os.makedirs(output_dir, exist_ok=True)

        # ✅ Full path for PDF file
        pdf_path = os.path.join(output_dir, pdf_id)

        # ✅ Create the actual PDF file
        create_pdf(pdf_path, caption, intent, description, project_type, structured)
        print("✅ PDF created at:", pdf_path)
        print("🗂️ Exists?", os.path.exists(pdf_path))

        # ✅ Generate HTML version
        html_blocks = build_html_blocks(structured, ai_tutorials=ai_tutorials)


        # ✅ Map keys to match frontend camelCase IDs   COMMENTED OUT EXTRA LINKS
        snake_to_camel = {
            "amazon_links": "amazonLinks",
            # "homedepot_links": "homedepotLinks",
            "walmart_links": "walmartLinks",
            # "temu_links": "temuLinks",
            # "bestbuy_links": "bestbuyLinks",
            "harborfreight_links": "harborfreightLinks",
            "autozone_links": "autozoneLinks",
            # "oreilly_links": "oreillyLinks",
            # "napa_links": "napaLinks",
            # "carparts_links": "carpartsLinks",

        }

        camel_case_links = {
            snake_to_camel[k]: links.get(k, []) + store_matches.get(k, [])
            for k in store_keys if k in snake_to_camel
        }

        print("⏱️ Analyze total time:", time.time() - start, "seconds")

        print("✅ Completed /analyze successfully")

        # ✅ Return payload
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
        traceback.print_exc()  # 🔍 shows full crash stack trace in terminal
        return JSONResponse(content={"error": f"Server error: {str(e)}"}, status_code=500)


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

#added new directory and signup page
import json

DATA_DIR = os.path.join(os.getcwd(), "data")
os.makedirs(DATA_DIR, exist_ok=True)
COMPANY_FILE = os.path.join(DATA_DIR, "companies.json")

def load_companies():
    if not os.path.exists(COMPANY_FILE):
        return []
    try:
        with open(COMPANY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("⚠️ Corrupted companies.json, resetting.")
        return []

def save_companies(companies):
    with open(COMPANY_FILE, "w", encoding="utf-8") as f:
        json.dump(companies, f, indent=2)

@router.post("/company-submission")
async def company_submission(
    company_name: str = Body(...),
    contact_email: str = Body(...),
    company_type: str = Body(...),
    description: str = Body(...),
    website: str = Body(None)  # new optional field
):
    companies = load_companies()

    # Deduplication: avoid duplicates by name+email
    already_exists = any(
        c["company_name"].lower() == company_name.lower() and 
        c["contact_email"].lower() == contact_email.lower()
        for c in companies
    )

    if not already_exists:
        companies.append({
            "company_name": company_name,
            "contact_email": contact_email,
            "company_type": company_type,
            "description": description,
            "website": website,
            "timestamp": int(time.time())  # store as UNIX timestamp
        })
        save_companies(companies)
        print(f"✅ Added new company: {company_name}")
    else:
        print(f"⚠️ Duplicate skipped: {company_name} ({contact_email})")

    send_email_copy(company_name, contact_email, company_type, description)

    return {
        "success": True,
        "message": "Submission received, stored, and emailed to support@SmartQuotr.com"
    }

@router.get("/directory")
async def get_directory():
    companies = load_companies()
    # Sort newest first
    companies_sorted = sorted(companies, key=lambda c: c.get("timestamp", 0), reverse=True)
    return {"companies": companies_sorted}


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

