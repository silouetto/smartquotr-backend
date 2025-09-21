# backend/routes/business_directory.py

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from collections import defaultdict
from pathlib import Path
import json

# ✅ Import your local predefined businesses
from routes.data.local_businesses import LOCAL_BUSINESSES

router = APIRouter()

# ✅ Path to saved JSON submissions
DATA_FILE = Path("data/business_directory.json")
DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
if not DATA_FILE.exists():
    DATA_FILE.write_text("[]", encoding="utf-8")


@router.get("/directory")
async def get_directory():
    """
    Returns businesses grouped by category.
    Combines local static businesses + submitted businesses.
    """
    try:
        # Load saved businesses from file
        submitted = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"⚠️ Could not read business_directory.json: {e}")
        submitted = []

    # Merge local + saved
    all_companies = LOCAL_BUSINESSES + submitted

    # Group by category
    grouped = defaultdict(list)
    for biz in all_companies:
        cat = biz.get("company_type") or biz.get("category") or "General"
        grouped[cat].append(biz)

    # Sort by timestamp (newest first if timestamp exists)
    for cat in grouped:
        grouped[cat] = sorted(grouped[cat], key=lambda x: x.get("timestamp", 0), reverse=True)

    return JSONResponse({"companies_by_category": grouped})

