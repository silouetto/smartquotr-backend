# routes/helpbot.py

from fastapi import APIRouter
import re

router = APIRouter()

@router.post("/helpbot")
async def help_bot_handler(data: dict):
    raw_question = data.get("question", "")
    question = re.sub(r"[^\w\s]", "", raw_question).lower().strip()

    if not question:
        return {
            "reply": (
                "⚠️ I didn't catch that. Try asking:\n"
                "- How does billing work?\n"
                "- What’s the difference between GPT-3.5 and GPT-4?\n"
                "- Where are the coupon codes?"
            )
        }

    FAQ = [
        {
            "keywords": ["billing", "money", "charge", "cost", "pricing", "paid", "donation", "subscription"],
            "reply": (
                "💳 **Billing & Support**\n\n"
                "• GPT-3.5 access is free and runs on our local AI budget.\n"
                "• GPT-4 costs real money per request — even more than GPT-3.5 — so it's ad-supported or unlocked via donation.\n"
                "• Your support covers:\n"
                "   - GPT usage 💬\n"
                "   - Server maintenance ☁️\n"
                "   - Feature development 🚀\n\n"
                "Every dollar helps build a smarter, faster SmartQuotr for everyone. 💡"
            )
        },
        {
            "keywords": ["difference", "gpt3", "gpt4", "compare", "model", "ai version"],
            "reply": (
                "🤖 **GPT-3.5 vs GPT-4**\n\n"
                "- GPT-3.5: Free, fast, great for everyday estimates.\n"
                "- GPT-4: SmartQuotr Pro — adds coupon codes, visual sketches, and real-world pro listings.\n"
                "🔓 GPT-4 unlockable after ad view or support."
            )
        },
        {
            "keywords": ["coupon", "promo", "discount", "save", "deal"],
            "reply": (
                "🧾 **Coupons & Promos (GPT-4 Only)**\n\n"
                "When using GPT-4 with 'Include Coupons' checked, the final PDF will include:\n"
                "- Store coupon codes (text + QR)\n"
                "- Redeemable discounts for Home Depot, Amazon, and more\n"
                "Use them online or in-store!"
            )
        },
        {
            "keywords": ["sketch", "diagram", "drawing", "blueprint", "ascii"],
            "reply": (
                "📐 **Sketch Feature (GPT-4 Only)**\n\n"
                "Sketches are visual diagrams shown under the 'Step-by-Step' tab.\n"
                "Check the 'Include Sketch' box + use GPT-4 to enable it.\n"
                "We aim to give a visual layout or top-down view where possible."
            )
        },
        {
            "keywords": ["ad", "watch", "video", "sponsor", "commercial"],
            "reply": (
                "🎬 **Ads and Sponsorships**\n\n"
                "We show 30-second sponsored ads during the AI analysis phase.\n"
                "This helps us fund GPT-4 usage, PDF generation, and development — so you can use the app with minimal cost. 🙌"
            )
        },
        {
            "keywords": ["how", "use", "help", "work", "working", "steps", "guide"],
            "reply": (
                "🧠 **How SmartQuotr Works**\n\n"
                "1. Upload or take a photo 📷\n"
                "2. Type your intent (e.g. 'build a shelf') 🎯\n"
                "3. Optionally add more description 📝\n"
                "4. Click 'Get Estimate' 🛠️\n"
                "5. View: tools, materials, cost, video tutorials, and step-by-step guide.\n"
                "6. Download your custom PDF!"
            )
        },
        {
            "keywords": ["professional", "service", "company", "hire", "contractor"],
            "reply": (
                "👷 **Hire a Pro (GPT-4 Only)**\n\n"
                "Using GPT-4 will include links to local or well-known contractors or companies that can do the job for you.\n"
                "These show up under your PDF or step-by-step suggestions."
            )
        },
        {
            "keywords": ["pdf", "download", "print", "save", "file", "document"],
            "reply": (
                "📄 **About the PDF**\n\n"
                "Once your project is analyzed, scroll to the bottom and click **Download PDF**.\n"
                "It includes all tools, materials, costs, steps, sketches (if checked), and store coupons (if enabled)."
            )
        },
        {
            "keywords": ["store", "shop", "tab", "product", "links", "not showing"],
            "reply": (
                "🛒 **Store Tabs Not Showing?**\n\n"
                "If you don’t see store tabs, it could be:\n"
                "- Not enough valid product keywords\n"
                "- Missing tools/materials in your input\n"
                "- Try rephrasing your project or uploading a clearer image!"
            )
        },
        {
            "keywords": ["account", "password", "login", "sign in"],
            "reply": (
                "🔐 **Account & Login**\n\n"
                "SmartQuotr does not currently use account logins. All access is anonymous and secure. No passwords required."
            )
        },
        {
            "keywords": ["data", "privacy", "secure", "security", "info", "information"],
            "reply": (
                "🔒 **Data Privacy**\n\n"
                "We do not store, sell, or share your data.\n"
                "Everything is used briefly to generate your project estimate — then cleared securely."
            )
        }
    ]

    for entry in FAQ:
        if any(k in question for k in entry["keywords"]):
            return {"reply": entry["reply"]}

    return {
        "reply": (
            "🤖 I'm here to help with anything related to SmartQuotr!\n"
            "Try asking about:\n"
            "- GPT-3.5 vs GPT-4 differences\n"
            "- Sketches or Coupons\n"
            "- How to use the app\n"
            "- Billing or privacy policies\n"
            "- PDF download help"
        )
    }

