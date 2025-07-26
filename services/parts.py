# services/parts.py

import difflib

# 🧠 Expanded database with categories + pricing + body parts
PART_DATABASE = {
    # 🛠️ Mechanical Parts
    "brake caliper": {"estimate": 75, "min": 60, "max": 90, "category": "Brakes"},
    "brake pads": {"estimate": 50, "min": 40, "max": 70, "category": "Brakes"},
    "rotors": {"estimate": 80, "min": 60, "max": 100, "category": "Brakes"},
    "air filter": {"estimate": 20, "min": 15, "max": 30, "category": "Engine"},
    "oil filter": {"estimate": 15, "min": 10, "max": 20, "category": "Engine"},
    "spark plug": {"estimate": 10, "min": 5, "max": 15, "category": "Ignition"},
    "battery": {"estimate": 120, "min": 100, "max": 150, "category": "Electrical"},
    "alternator": {"estimate": 150, "min": 130, "max": 200, "category": "Electrical"},
    "starter motor": {"estimate": 160, "min": 130, "max": 210, "category": "Electrical"},
    "headlight": {"estimate": 60, "min": 40, "max": 80, "category": "Lighting"},
    "taillight": {"estimate": 50, "min": 30, "max": 70, "category": "Lighting"},
    "radiator": {"estimate": 120, "min": 100, "max": 160, "category": "Cooling"},
    "water pump": {"estimate": 140, "min": 110, "max": 180, "category": "Cooling"},
    "fuel pump": {"estimate": 180, "min": 150, "max": 220, "category": "Fuel System"},
    "cv joint": {"estimate": 110, "min": 90, "max": 150, "category": "Suspension"},
    "tie rod": {"estimate": 70, "min": 50, "max": 90, "category": "Steering"},
    "oxygen sensor": {"estimate": 90, "min": 75, "max": 120, "category": "Emissions"},
    "serpentine belt": {"estimate": 35, "min": 25, "max": 50, "category": "Belts"},
    "muffler": {"estimate": 150, "min": 130, "max": 200, "category": "Exhaust"},
    "catalytic converter": {"estimate": 350, "min": 300, "max": 500, "category": "Emissions"},
    "timing belt": {"estimate": 250, "min": 200, "max": 350, "category": "Engine"},
    "control arm": {"estimate": 130, "min": 110, "max": 180, "category": "Suspension"},
    "struts": {"estimate": 200, "min": 180, "max": 260, "category": "Suspension"},

    # 🚗 Car Body / Exterior
    "front bumper": {"estimate": 250, "min": 180, "max": 400, "category": "Body"},
    "rear bumper": {"estimate": 280, "min": 200, "max": 450, "category": "Body"},
    "fender": {"estimate": 150, "min": 120, "max": 220, "category": "Body"},
    "hood": {"estimate": 350, "min": 300, "max": 500, "category": "Body"},
    "trunk lid": {"estimate": 320, "min": 250, "max": 450, "category": "Body"},
    "grille": {"estimate": 130, "min": 90, "max": 180, "category": "Body"},
    "driver door": {"estimate": 450, "min": 350, "max": 600, "category": "Body"},
    "passenger door": {"estimate": 450, "min": 350, "max": 600, "category": "Body"},
    "side mirror": {"estimate": 90, "min": 70, "max": 150, "category": "Body"},
    "windshield": {"estimate": 300, "min": 250, "max": 450, "category": "Glass"},
    "rear window": {"estimate": 280, "min": 220, "max": 400, "category": "Glass"},
    "tailgate": {"estimate": 500, "min": 400, "max": 650, "category": "Body"},
}

def get_closest_part(query):
    matches = difflib.get_close_matches(query.lower(), PART_DATABASE.keys(), n=1, cutoff=0.6)
    return matches[0] if matches else None

def get_estimate(part_name: str):
    part_name_lower = part_name.lower()
    exact = PART_DATABASE.get(part_name_lower)

    if exact:
        return {
            "matched_name": part_name_lower,
            "estimate": exact["estimate"],
            "min": exact.get("min"),
            "max": exact.get("max"),
            "category": exact.get("category")
        }

    closest = get_closest_part(part_name)
    if closest:
        data = PART_DATABASE[closest]
        return {
            "matched_name": closest,
            "estimate": data["estimate"],
            "min": data.get("min"),
            "max": data.get("max"),
            "category": data.get("category")
        }

    return {
        "matched_name": None,
        "estimate": "Unknown",
        "min": None,
        "max": None,
        "category": None
    }
