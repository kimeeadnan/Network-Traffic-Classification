import os
from random import shuffle

import cv2
import pandas as pd
from tqdm import tqdm
try:
    import wandb
except ImportError:
    wandb = None

# USTC-TK2016 3_Session2Png.py writes class folders as 0..23 under 4_Png/Train.
# Override with NTC_TRAIN_DIR / NTC_OUTPUT_CSV when using AllLayers PNGs (same folder layout).
TRAIN_DIR = os.environ.get(
    "NTC_TRAIN_DIR",
    "/home/user/intern-kimu/ntc/uc1/USTC-TK2016/4_Png/Train",
)
OUTPUT_CSV = os.environ.get("NTC_OUTPUT_CSV", "dataset_L7_multiclass_bin32.csv")
LAYER_TAG = os.environ.get("NTC_LAYER", "L7")

run = None
if wandb is not None:
    run = wandb.init(
        project="network-traffic-classification",
        job_type="preprocess",
        name=f"{LAYER_TAG.lower()}_histogram_build",
        config={
            "train_dir": TRAIN_DIR,
            "num_bins": 32,
            "mode": "multiclass",
            "layer": LAYER_TAG,
            "output_csv": OUTPUT_CSV,
        },
    )

rows = []
for class_dir in tqdm(sorted(os.listdir(TRAIN_DIR))):
    class_path = os.path.join(TRAIN_DIR, class_dir)
    if not os.path.isdir(class_path):
        continue
    try:
        label = int(class_dir)
    except ValueError:
        continue
    for img_name in os.listdir(class_path):
        img_path = os.path.join(class_path, img_name)
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        hist = cv2.calcHist([img], [0], None, [32], [0, 256]).flatten()
        rows.append(list(hist) + [label])

shuffle(rows)
columns = [f"bin_{i}" for i in range(32)] + ["label"]
df = pd.DataFrame(rows, columns=columns)
print(df.shape)
df.to_csv(OUTPUT_CSV, index=False)
if run is not None:
    run.log({
        "dataset_rows": int(df.shape[0]),
        "dataset_cols": int(df.shape[1]),
        "num_classes": int(df["label"].nunique()),
    })
    run.finish()
