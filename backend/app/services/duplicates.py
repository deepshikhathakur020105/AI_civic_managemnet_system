"""Duplicate detection: geo-radius candidates, then optional embedding rank."""
import math

DEFAULT_RADIUS_M = 50.0
SIMILARITY_THRESHOLD = 0.85  # tune on labelled pairs


def haversine_m(lat1, lon1, lat2, lon2) -> float:
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = p2 - p1
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def cosine(a, b) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def is_duplicate(new: dict, existing: dict,
                 radius_m: float = DEFAULT_RADIUS_M,
                 threshold: float = SIMILARITY_THRESHOLD) -> bool:
    """new/existing: {category, lat, lon, embedding (optional)}."""
    if new["category"] != existing["category"]:
        return False
    if haversine_m(new["lat"], new["lon"], existing["lat"], existing["lon"]) > radius_m:
        return False
    if new.get("embedding") is not None and existing.get("embedding") is not None:
        return cosine(new["embedding"], existing["embedding"]) >= threshold
    return True  # Tier 1: location + category only
