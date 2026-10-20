"""Explainable priority scoring (P1 highest .. P4 lowest).

score = sum(weight * factor), every factor normalised to 0..1.
Report count is capped so heavily-reported areas cannot dominate
(reporting-bias mitigation). Weights are a starting point: tune and
justify them during evaluation.
"""

WEIGHTS = {
    "severity": 0.35,
    "safety": 0.25,
    "location": 0.15,
    "reports": 0.10,
    "age": 0.15,
}
REPORT_CAP = 5      # reports beyond this add nothing
AGE_CAP_DAYS = 14

SAFETY_RISK = {
    "pothole": 0.8,
    "road_damage": 0.7,
    "broken_streetlight": 0.6,
    "water_leakage": 0.5,
    "overflowing_drain": 0.6,
    "fallen_tree": 0.9,
    "garbage": 0.3,
}


def compute_priority(category: str, severity: float, location_sensitivity: float,
                     report_count: int, days_pending: float) -> dict:
    factors = {
        "severity": min(max(severity, 0.0), 1.0),
        "safety": SAFETY_RISK.get(category, 0.4),
        "location": min(max(location_sensitivity, 0.0), 1.0),
        "reports": min(report_count, REPORT_CAP) / REPORT_CAP,
        "age": min(max(days_pending, 0.0), AGE_CAP_DAYS) / AGE_CAP_DAYS,
    }
    score = sum(WEIGHTS[k] * v for k, v in factors.items())
    if score >= 0.65:
        level = "P1"
    elif score >= 0.5:
        level = "P2"
    elif score >= 0.35:
        level = "P3"
    else:
        level = "P4"
    return {"score": round(score, 3), "level": level, "factors": factors}
