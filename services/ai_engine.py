# services/ai_engine.py
import os
from openai import OpenAI
from prompt_engine import PromptEngine
from dotenv import load_dotenv


load_dotenv()

#replacing openai.api_key monolith with a new variable and then calling client with that variable
TheOneAndOnlyKey = os.getenv("OPENAI_API_KEY")
if not TheOneAndOnlyKey:
    raise ValueError("OPENAI_API_KEY environment variable not set.")

client = OpenAI(api_key=TheOneAndOnlyKey)

# openai.api_key = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_advice(intent, description, project_type, caption, include_steps, use_gpt4=False, include_sketch=False, include_coupons=False):
    try:
        engine = PromptEngine(
            project_type=project_type,
            intent=intent,
            description=description,
            image_caption=caption,
            include_steps=include_steps,
            include_sketch=include_sketch,     
            include_coupons=include_coupons,
            use_gpt4=use_gpt4     
        )

        prompt = engine.build_estimate_prompt()
        print("📤 Sending GPT prompt:\n", prompt)

        model = "gpt-4" if use_gpt4 else "gpt-3.5-turbo"

        response = client.chat.completion.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2500
        )

        result = response.choices[0].message.content.strip()
        print("✅ GPT returned:\n", result)
        return result

    except Exception as e:
        print("❌ GPT failed:", str(e))
        return "❌ Failed to get advice from GPT."


def generate_steps(intent, description, project_type, caption):
    engine = PromptEngine(
        project_type=project_type,
        intent=intent,
        description=description,
        image_caption=caption
    )

    prompt = engine.build_steps_prompt()

    response = client.chat.completion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=2500
    )

    return response.choices[0].message.content.strip()
