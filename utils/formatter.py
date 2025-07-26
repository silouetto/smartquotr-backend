# utils/formatter.py


import re
import requests

def normalize_item(text):
    return re.sub(r'^\[\s*\]', '', text).strip().lower()

def format_advice_structured(raw: str):
    import re

    lines = raw.splitlines()
    section = None
    blocks = {}

    # Known section identifiers
    section_headers = ["tools", "materials", "cost", "time", "youtube", "labor", "helpful product links"]

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # ✅ Detect section headers more reliably
        if any(x in line.lower() for x in section_headers):
            section_clean = re.sub(r"^\s*#+\s*|\*\*|\[.*?\]", "", line, flags=re.IGNORECASE).strip(":- ").title()
            section = section_clean
            blocks[section] = []
            continue

        # ✅ Normalize entries to "[ ] Item Name"
        if not line.startswith("[ ]"):
            line = re.sub(r"^[-•*]\s*", "", line)  # strip dashes, bullets
            line = f"[ ] {line.strip()}"

        if section:
            blocks[section].append(line)

    print("🧱 Structured output with", len(blocks), "sections:", list(blocks.keys()))
    return blocks



    
def build_html_blocks(structured, ai_tutorials=None):
    import re
    import requests

    html_blocks = ""
    rendered_sections = set()
    vague_labels = {
        "tools", "materials", "equipment", "stuff", "things", "cost", "time", "labor",
        "optional", "youtube", "titles", "days", "hours"
    }

    # 🔎 Build lookup for real tutorial links
    tutorial_lookup = {
        t['title'].strip().lower(): t['url'] for t in ai_tutorials or []
    }

    for section, items in structured.items():
        section_key = section.strip().lower()
        if "labor" in section_key or section_key in rendered_sections:
            continue
        rendered_sections.add(section_key)

        # ✅ Sketch block
        if "sketch" in section_key or "diagram" in section_key:
            html_blocks += f"<h3>{section}</h3><pre>{''.join(items)}</pre>"
            continue

        # ✅ Coupon block
        if "coupon" in section_key or "promo" in section_key:
            html_blocks += f"<h3>{section}</h3><ul>"
            for item in items:
                html_blocks += f"<li>🧾 {item}</li>"
            html_blocks += "</ul>"
            continue

        if "contractor" in section_key or "company" in section_key:
            html_blocks += f"<h3>{section}</h3><ul>"
            for item in unique_items:
                html_blocks += f"<li>🏢 {item}</li>"
            html_blocks += "</ul>"
            continue

        # ✅ Better deduplication using normalized content
        unique_items = []
        seen_items = set()

        for item in items:
            norm = normalize_item(item)
            if norm not in seen_items:
                unique_items.append(item)
                seen_items.add(norm)

        # ✅ TOOLS / MATERIALS (skip links)
        if "tools" in section_key or "materials" in section_key:
            html_blocks += f"<h3>{section}</h3><ul>"
            for item in unique_items:
                clean = re.sub(r'\[\s*\]', '', item).strip(" -:")
                html_blocks += f"<li>- {clean}</li>"
            html_blocks += "</ul>"
            continue

        # ✅ Render ESTIMATED TIME / COST with plain text only (no links/icons)
        if "time" in section_key or "cost" in section_key:
            html_blocks += f"<h3>{section}</h3><ul>"
            for item in unique_items:
                clean = re.sub(r'\[\s*\]', '', item).strip(" -:")
                html_blocks += f"<li>{clean}</li>"
            html_blocks += "</ul>"
            continue

        # 🎯 Other sections (with links and detection)
        html_blocks += f"<h3>{section}</h3><ul>"
        for item in unique_items:
            original = item.strip()
            handled = False

            # 🔗 Format: [ ] - Label: [url]
            m = re.match(r'\[\s*\]\s*[-–]?\s*(.+?):\s*\[(https?://[^\]]+)\]', original, re.IGNORECASE)
            if m:
                label, url = m.groups()
                if label.strip().lower() in vague_labels:
                    continue
                item = f'<a href="{url}" target="_blank" rel="noopener noreferrer">🔗 {label.strip()}</a>'
                handled = True

            # 🎥 YouTube tutorial title (exact + fuzzy match to ai_tutorials)
            if not handled:
                m = re.match(r'\[\s*\]\s*(?:-?\s*)"?(.+?)"?$', original)
                if m:
                    title = m.group(1).strip()
                    url = tutorial_lookup.get(title.lower())

                    if not url:
                        # fallback search
                        url = f"https://www.youtube.com/results?search_query={requests.utils.quote(title)}"

                        item = f'<a href="{url}" target="_blank" rel="noopener noreferrer">▶️ {title}</a>'
                        handled = True


            # 🛠️ Fallback Markdown [text](url)
            if not handled:
                def plain_link(m):
                    url = m.group(2)
                    label = m.group(1)
                    if "amazon.com" in url and "tag=" not in url:
                        sep = "&" if "?" in url else "?"
                        url += f"{sep}tag=smartquotr-20"
                    return f'<a href="{url}" target="_blank" rel="noopener noreferrer">🔗 {label}</a>'
                item = re.sub(r'\[(.*?)\]\((https?://[^\s]+)\)', plain_link, original)

            html_blocks += f"<li>{item}</li>"

        html_blocks += "</ul>"

    return html_blocks




