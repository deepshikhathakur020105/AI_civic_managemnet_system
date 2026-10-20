"""Evaluate a trained model on the held-out test split.

    python evaluate.py --data data/civic --weights ../backend/models/best.pt
Writes reports/metrics.json and reports/confusion_matrix.csv (for the project report).
"""
import argparse
import csv
import json
from pathlib import Path

from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from ultralytics import YOLO

IMG_EXT = {".jpg", ".jpeg", ".png"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/civic")
    ap.add_argument("--weights", default="../backend/models/best.pt")
    ap.add_argument("--out", default="reports")
    a = ap.parse_args()

    model = YOLO(a.weights)
    test = Path(a.data) / "test"
    labels = sorted(p.name for p in test.iterdir() if p.is_dir())
    y_true, y_pred = [], []
    for cls in labels:
        files = [p for p in (test / cls).iterdir() if p.suffix.lower() in IMG_EXT]
        for f in files:
            r = model(str(f), verbose=False)[0]
            y_true.append(cls)
            y_pred.append(r.names[r.probs.top1])

    out = Path(a.out)
    out.mkdir(exist_ok=True)
    report = classification_report(y_true, y_pred, labels=labels, output_dict=True, zero_division=0)
    report["accuracy"] = accuracy_score(y_true, y_pred)
    (out / "metrics.json").write_text(json.dumps(report, indent=2))
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    with open(out / "confusion_matrix.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["true\\pred"] + labels)
        for lab, row in zip(labels, cm):
            w.writerow([lab] + list(row))
    print(classification_report(y_true, y_pred, labels=labels, zero_division=0))


if __name__ == "__main__":
    main()
