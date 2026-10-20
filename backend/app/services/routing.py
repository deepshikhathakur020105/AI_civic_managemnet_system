"""Rule-based department routing with a human fallback."""

CATEGORY_TO_DEPARTMENT = {
    "pothole": "Road Infrastructure",
    "road_damage": "Road Infrastructure",
    "garbage": "Sanitation",
    "overflowing_drain": "Sanitation",
    "water_leakage": "Public Utilities / Water",
    "broken_streetlight": "Electricity / Street Lighting",
    "fallen_tree": "Horticulture / Parks",
}
FALLBACK = "Manual Review"
MIN_CONFIDENCE = 0.5


def route(category: str, confidence: float) -> str:
    if confidence < MIN_CONFIDENCE:
        return FALLBACK
    return CATEGORY_TO_DEPARTMENT.get(category, FALLBACK)
