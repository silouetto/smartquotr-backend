# backend/routes/business_signup.py

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
import smtplib, json, os, time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

router = APIRouter()

# ✅ Email Config
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_USER = os.getenv("EMAIL_USER", "your_email@gmail.com")
EMAIL_PASS = os.getenv("EMAIL_PASS", "your_password")
SUPPORT_EMAIL = "support@SmartQuotr.com"

# ✅ Local JSON Storage
DATA_FILE = Path("data/business_directory.json")
DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
if not DATA_FILE.exists():
    DATA_FILE.write_text("[]", encoding="utf-8")  # initialize with empty list


@router.post("/api/company-submission")
async def submit_company(request: Request):
    try:
        data = await request.json()
        data["timestamp"] = int(time.time())  # add server timestamp

        # --- 1) Save to local JSON file ---
        try:
            current = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            current.append(data)
            DATA_FILE.write_text(json.dumps(current, indent=2), encoding="utf-8")
            print(f"✅ Saved new business to {DATA_FILE}")
        except Exception as file_err:
            print(f"⚠️ Could not write to JSON file: {file_err}")

        # --- 2) Send email notification ---
        try:
            msg = MIMEMultipart()
            msg["From"] = EMAIL_USER
            msg["To"] = SUPPORT_EMAIL
            msg["Subject"] = f"New Business Submission: {data.get('company_name', 'No Name')}"

            body = (
                f"📌 New Business Submission\n\n"
                f"Business Name: {data.get('company_name')}\n"
                f"Category: {data.get('company_type')}\n"
                f"Description: {data.get('description')}\n"
                f"Location: {data.get('location')}\n"
                f"Contact Email: {data.get('contact_email')}\n"
                f"Website: {data.get('website') or 'N/A'}\n"
            )

            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(EMAIL_USER, EMAIL_PASS)
                server.sendmail(EMAIL_USER, SUPPORT_EMAIL, msg.as_string())
            print("📧 Email sent successfully.")
        except Exception as email_err:
            print(f"⚠️ Failed to send email: {email_err}")

        return JSONResponse({"success": True, "message": "Business submitted."})

    except Exception as e:
        print("❌ Error processing business submission:", e)
        raise HTTPException(status_code=500, detail="Failed to process business submission.")
