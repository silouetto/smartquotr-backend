from fastapi import APIRouter, Request, Body
from fastapi.responses import JSONResponse
from routes.data import save_company
import time

router = APIRouter()

@router.post("/company-submission")
async def company_submission(
    company_name: str = Body(...),
    contact_email: str = Body(...),
    company_type: str = Body(...),
    description: str = Body(...),
    website: str = Body(None)
):
    # Build the company dict
    submission = {
        "company_name": company_name,
        "contact_email": contact_email,
        "company_type": company_type,
        "description": description,
        "website": website,
        "timestamp": int(time.time())
    }

    # 1️⃣ Save to JSON
    save_company(submission)

    # 2️⃣ Send email copy
    # Make sure your send_email_copy function is imported and works
    send_email_copy(company_name, contact_email, company_type, description, website)

    return JSONResponse({"success": True, "message": "Submission saved and emailed!"})
