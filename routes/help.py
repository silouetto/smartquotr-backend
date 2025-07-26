from fastapi import APIRouter, Request

router = APIRouter()

# Helpbot
@router.post("/helpbot")
async def helpbot_handler(request: Request):
    try:
        data = await request.json()
        question = data.get("question", "").strip()

        if not question:
            return {"reply": "⚠️ Please ask a valid question."}

        # 🧠 You can use OpenAI or local logic here
        response = f"I’m just a demo bot. You asked: {question}"
        
        return {"reply": response}

    except Exception as e:
        print("❌ Helpbot error:", e)
        return {"reply": "⚠️ Sorry, something went wrong."}
