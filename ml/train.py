"""Fine-tune a pretrained YOLO classification model on the merged dataset.

    pip install -r requirements.txt
    python train.py --data data/civic --epochs 30
Copies the best weights to ../backend/models/best.pt (picked up by the API).
"""
import argparse
import shutil
from pathlib import Path

from ultralytics import YOLO


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/civic")
    ap.add_argument("--model", default="yolo11n-cls.pt")
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--imgsz", type=int, default=224)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--device", default=None, help="0 for first GPU, 'cpu' otherwise")
    a = ap.parse_args()

    model = YOLO(a.model)
    res = model.train(data=a.data, epochs=a.epochs, imgsz=a.imgsz, batch=a.batch,
                      device=a.device, project="runs", name="civic-cls", exist_ok=True)
    best = Path(res.save_dir) / "weights" / "best.pt"
    dest = Path(__file__).resolve().parent.parent / "backend" / "models" / "best.pt"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(best, dest)
    print(f"Saved model to {dest}")


if __name__ == "__main__":
    main()
