"""Merge several raw datasets into one image-classification dataset.

Output layout (what Ultralytics `classify` expects):
    OUT/train/<class>/*.jpg   OUT/val/<class>/*.jpg   OUT/test/<class>/*.jpg

Source types (see datasets.example.yaml):
  folders : <path>/<folder>/*.jpg, folder name -> unified class via `map`
  yolo    : YOLO detection dataset (images/ + labels/). Each image gets ONE label:
            the mapped class with the largest total box area. Images whose boxes
            map to nothing are skipped.

Usage:  python prepare_dataset.py --config datasets.yaml --out data/civic
"""
import argparse
import hashlib
import json
import random
import shutil
from collections import Counter, defaultdict
from pathlib import Path

import yaml

IMG_EXT = {".jpg", ".jpeg", ".png"}
MIN_RECOMMENDED = 200


def iter_folders(src):
    for folder, cls in src["map"].items():
        root = Path(src["path"]) / folder
        if not root.is_dir():
            print(f"  WARNING: {root} not found")
            continue
        for p in sorted(root.rglob("*")):
            if p.suffix.lower() in IMG_EXT:
                yield p, cls


def find_image(label_path: Path):
    parts = list(label_path.parts)
    if "labels" not in parts:
        return None
    idx = len(parts) - 1 - parts[::-1].index("labels")  # last 'labels' component
    parts[idx] = "images"
    base = Path(*parts).with_suffix("")
    for ext in IMG_EXT | {e.upper() for e in IMG_EXT}:
        cand = base.with_suffix(ext)
        if cand.exists():
            return cand
    return None


def iter_yolo(src):
    names = src["names"]
    mapping = src["map"]
    for lbl in sorted(Path(src["path"]).rglob("*.txt")):
        img = find_image(lbl)
        if img is None:
            continue
        area = defaultdict(float)
        for line in lbl.read_text().splitlines():
            f = line.split()
            if len(f) < 5:
                continue
            try:
                cid, w, h = int(float(f[0])), float(f[3]), float(f[4])
            except ValueError:
                continue
            if 0 <= cid < len(names) and names[cid] in mapping:
                area[mapping[names[cid]]] += w * h
        if area:
            yield img, max(area, key=area.get)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--split", type=float, nargs=3, default=[0.8, 0.1, 0.1])
    ap.add_argument("--max-per-class", type=int, default=0, help="cap images per class (0 = no cap)")
    a = ap.parse_args()

    cfg = yaml.safe_load(open(a.config))
    classes = cfg["classes"]
    rng = random.Random(a.seed)
    seen, per_class = set(), defaultdict(list)

    for src in cfg["sources"]:
        it = iter_folders(src) if src["type"] == "folders" else iter_yolo(src)
        n = dup = 0
        for path, cls in it:
            if cls not in classes:
                raise SystemExit(f"Class '{cls}' (source {src['name']}) is not in `classes`")
            digest = hashlib.md5(path.read_bytes()).hexdigest()
            if digest in seen:
                dup += 1
                continue
            seen.add(digest)
            per_class[cls].append((path, f"{src['name']}_{digest[:10]}{path.suffix.lower()}"))
            n += 1
        print(f"{src['name']}: {n} images ({dup} exact duplicates skipped)")

    out = Path(a.out)
    if out.exists():
        shutil.rmtree(out)
    counts = {s: Counter() for s in ("train", "val", "test")}
    tr, va, _ = a.split
    for cls in classes:
        items = per_class.get(cls, [])
        rng.shuffle(items)
        if a.max_per_class:
            items = items[: a.max_per_class]
        n_tr, n_va = int(len(items) * tr), int(len(items) * va)
        parts = {"train": items[:n_tr], "val": items[n_tr:n_tr + n_va], "test": items[n_tr + n_va:]}
        for split, subset in parts.items():
            if not subset:
                continue  # no empty class folders: they break training
            d = out / split / cls
            d.mkdir(parents=True, exist_ok=True)
            for path, name in subset:
                shutil.copy2(path, d / name)
            counts[split][cls] = len(subset)

    summary = {s: dict(c) for s, c in counts.items()}
    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    for cls in classes:
        total = sum(counts[s][cls] for s in counts)
        if total == 0:
            print(f"WARNING: no images for class '{cls}'")
        elif total < MIN_RECOMMENDED:
            print(f"WARNING: only {total} images for '{cls}' (aim for {MIN_RECOMMENDED}+)")


if __name__ == "__main__":
    main()
