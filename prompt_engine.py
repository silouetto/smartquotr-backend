# prompt_engine.py

class PromptEngine:
    def __init__(self, project_type, intent, description, image_caption, include_steps=False, include_sketch=False, include_coupons=False, use_gpt4=False):
        self.project_type = project_type
        self.intent = intent
        self.description = description
        self.caption = image_caption
        self.include_steps = include_steps
        self.include_sketch = include_sketch
        self.include_coupons = include_coupons
        self.use_gpt4 = use_gpt4

    def build_estimate_prompt(self):
        base = f"""
You are an expert technician and project consultant.
A user submitted a project for help.

Project Type: {self.project_type}
User Intent: {self.intent}
Image Caption: {self.caption}
Description: {self.description}

Please provide a structured breakdown including:
- Tools needed
- Materials
- Estimated time
- Cost ranges
- Optional YouTube tutorial titles

Use simple markdown with dash (-) bullets. ❌ Do not use [ ] checkboxes anywhere.
"""
        if self.include_steps:
            base += "\nAlso include a 'Step-by-step instructions' section formatted with clear numbered steps."

        if self.include_sketch:
            base += (
                "\n📐 If helpful, include a simple visual sketch or ASCII diagram of the project layout. "
                "It can show shapes, parts, outlines, or spatial placement relevant to the user's intent. "
                "Keep the sketch minimal, neat, and clearly readable using monospace formatting like ```text blocks."
            )

        if self.include_coupons:
            base += "\n🧾 Include 2–3 relevant coupon codes or promo keywords users can use online or in-store."

        if self.use_gpt4:
            base += "\n🏢 Please list 2–3 local contractor types (e.g., fencing, pond installers, landscapers) and 2–3 nationwide service providers who could also complete the project if needed."

        return base.strip()

    def build_steps_prompt(self):
        return f"""
You are a DIY instructor.

The user is attempting a {self.project_type}.

They described their intent as: {self.intent}
Image Caption: {self.caption}
Extra Description: {self.description}

Generate clear, numbered steps to complete the project.
""".strip()
