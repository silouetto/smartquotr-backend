from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse
from routes.data import save_company, load_companies, send_email_copy
from collections import defaultdict
from routes.data.local_businesses import LOCAL_BUSINESSES
import time

router = APIRouter()

ALLOWED_CATEGORIES = ["Auto Repair", "Construction", "Landscaping", "Painting", "Electrical", "Plumbing", "Other"]

# -------------------------------
# Submit a business
# -------------------------------
@router.post("/company-submission")
async def company_submission(
    company_name: str = Body(...),
    contact_email: str = Body(...),
    company_type: str = Body(...),
    description: str = Body(...),
    website: str = Body(None)
):
    # Deduplicate
    if any(
        c["company_name"].lower() == company_name.lower() and
        c["contact_email"].lower() == contact_email.lower()
        for c in TEMP_USER_COMPANIES
    ):
        return JSONResponse({"success": False, "message": "Duplicate submission skipped."})

    # Build the company dict
    submission = {
        "company_name": company_name,
        "contact_email": contact_email,
        "company_type": company_type,
        "description": description,
        "website": website,
        "timestamp": int(time.time())
    }

    # 1️⃣ Save to JSON & memory
    save_company(submission)

    # 2️⃣ Send email copy
    send_email_copy(company_name, contact_email, company_type, description, website)

    return JSONResponse({"success": True, "message": "Submission saved and emailed!"})

# -------------------------------
# Get directory (local + submissions)
# -------------------------------
@router.get("/directory")
async def get_directory():
    # Ensure latest TEMP_USER_COMPANIES is loaded
    load_companies()  # optional: refresh from JSON if needed

    all_companies = LOCAL_BUSINESSES 

    grouped = defaultdict(list)
    for c in all_companies:
        cat = c.get("company_type", "General")
        if cat not in ALLOWED_CATEGORIES:
            cat = "General"
        grouped[cat].append(c)

    # Sort each category by timestamp (newest first)
    for cat in grouped:
        grouped[cat] = sorted(grouped[cat], key=lambda c: c.get("timestamp", 0), reverse=True)

    return {"companies_by_category": grouped}
