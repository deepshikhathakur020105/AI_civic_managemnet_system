"""Image classifier wrapper.

Tier 1 stub: returns a fixed low-confidence result so the pipeline routes to
manual review until a trained model is dropped in at MODEL_PATH.
Replace `predict` with Ultralytics YOLO (or MobileNetV2) inference.
"""
import os

CLASSES = ["pothole", "garbage", "water_leakage", "broken_streetlight",
           "overflowing_drain", "fallen_tree"]
MODEL_PATH = os.getenv("MODEL_PATH", "models/best.pt")
_model = None


def _load():
    global _model
    if _model is None and os.path.exists(MODEL_PATH):
        from ultralytics import YOLO  # imported lazily; heavy dependency
        _model = YOLO(MODEL_PATH)
    return _model


def predict(image_path: str) -> tuple[str, float, float]:
    """Return (category, confidence, severity 0..1)."""
    model = _load()
    if model is None:
        return "pothole", 0.0, 0.5
    res = model(image_path, verbose=False)[0]
    if len(res.boxes) == 0:
        return "pothole", 0.0, 0.0
    best = max(res.boxes, key=lambda b: float(b.conf))
    h, w = res.orig_shape
    x1, y1, x2, y2 = best.xyxy[0].tolist()
    severity = min(((x2 - x1) * (y2 - y1)) / (w * h) * 4, 1.0)  # box-area proxy
    return res.names[int(best.cls)], float(best.conf), severity
