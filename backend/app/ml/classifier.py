"""Image classifier wrapper.

Loads an Ultralytics model from MODEL_PATH (train with ml/train.py). Supports:
  - classification models (Tier 1): category from class probabilities
  - detection models (Tier 2): category and a box-area severity proxy
Without a model file it returns a zero-confidence result, so every complaint
is routed to the Manual Review queue instead of being mislabelled.
"""
import os

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
    if getattr(res, "probs", None) is not None:  # classification model
        return res.names[res.probs.top1], float(res.probs.top1conf), 0.5
    if len(res.boxes) == 0:  # detection model, nothing found
        return "pothole", 0.0, 0.0
    best = max(res.boxes, key=lambda b: float(b.conf))
    h, w = res.orig_shape
    x1, y1, x2, y2 = best.xyxy[0].tolist()
    severity = min(((x2 - x1) * (y2 - y1)) / (w * h) * 4, 1.0)
    return res.names[int(best.cls)], float(best.conf), severity
