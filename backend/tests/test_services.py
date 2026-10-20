from app.services.duplicates import haversine_m, is_duplicate
from app.services.priority import compute_priority
from app.services.routing import route


def test_routing_rules_and_fallback():
    assert route("pothole", 0.9) == "Road Infrastructure"
    assert route("garbage", 0.9) == "Sanitation"
    assert route("pothole", 0.2) == "Manual Review"
    assert route("unknown_thing", 0.9) == "Manual Review"


def test_priority_levels_and_report_cap():
    high = compute_priority("fallen_tree", 1.0, 1.0, 5, 14)
    low = compute_priority("garbage", 0.1, 0.0, 1, 0)
    assert high["level"] == "P1" and low["level"] == "P4"
    # reports beyond the cap must not change the score
    a = compute_priority("pothole", 0.5, 0.0, 5, 3)["score"]
    b = compute_priority("pothole", 0.5, 0.0, 500, 3)["score"]
    assert a == b


def test_haversine_known_distance():
    # ~111.2 km per degree of latitude
    assert abs(haversine_m(0, 0, 1, 0) - 111195) < 200


def test_duplicate_rules():
    base = {"category": "pothole", "lat": 30.3165, "lon": 78.0322}
    near = {"category": "pothole", "lat": 30.31655, "lon": 78.03225}
    far = {"category": "pothole", "lat": 30.3265, "lon": 78.0322}
    other = {"category": "garbage", "lat": 30.3165, "lon": 78.0322}
    assert is_duplicate(base, near)
    assert not is_duplicate(base, far)
    assert not is_duplicate(base, other)
    # same place, dissimilar embeddings -> not a duplicate
    a = {**base, "embedding": [1, 0]}
    b = {**near, "embedding": [0, 1]}
    assert not is_duplicate(a, b)
