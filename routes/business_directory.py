# backend/routes/business_directory.py

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

# Example in-memory database (replace with a real database later)
businesses = [
    {
        "company_name": "John's Plumbing",
        "company_type": "Home Services",
        "description": "Expert plumbing repair and installation.",
        "location": "Portland, OR",
        "contact_email": "contact@johnsplumbing.com",
        "website": "https://johnsplumbing.com"
    },
    {
        "company_name": "Bright Electric",
        "company_type": "Electrical",
        "description": "Licensed electricians for residential and commercial work.",
        "location": "Beaverton, OR",
        "contact_email": "support@brightelectric.com",
        "website": "https://brightelectric.com"
    }
]

@router.get("/directory")
async def get_directory():
    """
    Returns businesses grouped by category.
    Format: { "companies_by_category": { "CategoryName": [businesses...] } }
    """
    grouped = {}
    for biz in businesses:
        cat = biz.get("company_type", "General")
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append(biz)

    return JSONResponse({"companies_by_category": grouped})
