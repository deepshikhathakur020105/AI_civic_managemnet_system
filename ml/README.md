# ML pipeline (Tier 1: image classification)

Why classification first: public datasets for these civic issues are a mix of folder-per-class
images and YOLO box annotations. Reducing everything to one label per image lets you merge them
and train one model. Bounding-box detection (needed for size-based severity) is Tier 2.

## 1. Get the data (run on your laptop or Google Colab; the build workspace cannot reach Kaggle)
Kaggle: create an API token (Account -> Create New Token), save as `~/.kaggle/kaggle.json`, then

    kaggle datasets download -d <owner>/<dataset-slug> -p data/raw/pothole --unzip

Search kaggle.com for each class and pick datasets that have a clear licence. Candidates found
outside Kaggle (check each licence before use):
- Pothole: [Roboflow pothole](https://public.roboflow.com/object-detection/pothole), [Mendeley water-filled/dry potholes](https://data.mendeley.com/datasets/tp95cdvgm8/1)
- Garbage: [TACO (YOLO format)](https://gts.ai/dataset-download/taco-dataset-yolo-format/), [Mendeley trash detection](https://data.mendeley.com/datasets/z732f9pwxt)
- Water leakage: [Roboflow pipe leakage](https://universe.roboflow.com/work-upary/pipe-leakage-gvr3a), [Mendeley water leakage](https://data.mendeley.com/datasets/xz2nykszbs)
- Broken streetlight: no ready dataset found. Photograph your own (campus, Dehradun streets) and add
  intact-lamp images to `other`. Aim for 200+ per class.

Also collect 100+ of your OWN photos per class as a separate test set: public data will not
match real citizen photos, and your evaluation should say so.

## 2. Merge and split

    cp datasets.example.yaml datasets.yaml     # edit paths/classes
    python prepare_dataset.py --config datasets.yaml --out data/civic

Exact-duplicate images are removed before splitting so the same photo cannot land in train and test.

## 3. Train and evaluate

    pip install -r requirements.txt
    python train.py --data data/civic --epochs 30
    python evaluate.py --data data/civic

`train.py` writes the weights to `backend/models/best.pt`; the API loads them automatically.
`evaluate.py` writes per-class precision/recall/F1 and a confusion matrix to `ml/reports/`.
Report these numbers only after you have run them.
