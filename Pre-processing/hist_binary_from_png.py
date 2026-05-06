"""
Build a binary (benign=1, malware=0) histogram dataset from USTC 4_Png/Train.

Folder indices 0..N under 4_Png/Train must match enumerate(os.listdir(TrimedSession/Train))
from USTC-TK2016/3_Session2Png.py — use the same TrimedSession tree you used when generating PNGs.
"""
import os
from random import shuffle

import cv2
import pandas as pd
from tqdm import tqdm

try:
    import wandb
except ImportError:
    wandb = None

USTC_ROOT = os.environ.get(
    "NTC_USTC_ROOT",
    "/home/user/intern-kimu/ntc/uc1/USTC-TK2016",
)
TRAIN_DIR = os.environ.get(
    "NTC_TRAIN_DIR",
    os.path.join(USTC_ROOT, "4_Png", "Train"),
)
# Same relative path 3_Session2Png.py uses for Train
TRIMED_TRAIN = os.environ.get(
    "NTC_TRIMED_TRAIN",
    os.path.join(USTC_ROOT, "3_ProcessedSession", "TrimedSession", "Train"),
)
OUTPUT_CSV = os.environ.get("NTC_OUTPUT_CSV", "dataset_L7_binary_bin32.csv")
LAYER_TAG = os.environ.get("NTC_LAYER", "L7")

BENIGN_MARKERS = (
    "BitTorrent", "Facetime", "FTP", "Gmail", "MySQL", "Outlook", "Skype",
    "SMB", "Weibo", "WorldOfWarcraft",
)
MALWARE_MARKERS = (
    "Cridex", "Geodo", "Htbot", "Miuref", "Neris", "Nsis-ay", "Shifu",
    "Tinba", "Virut", "Zeus",
)


def binary_label_from_trimed_folder(name: str):
    for m in BENIGN_MARKERS:
        if m in name:
            return 1
    for m in MALWARE_MARKERS:
        if m in name:
            return 0
    return None


def build_index_to_label():
    """Match 3_Session2Png.py: for i, d in enumerate(os.listdir(TrimedSession/Train))."""
    if not os.path.isdir(TRIMED_TRAIN):
        raise FileNotFoundError(f"Trimed train dir not found: {TRIMED_TRAIN}")
    mapping = {}
    for i, d in enumerate(os.listdir(TRIMED_TRAIN)):
        path = os.path.join(TRIMED_TRAIN, d)
        if not os.path.isdir(path):
            raise ValueError(f"Non-directory entry in TrimedSession/Train: {d!r} (index {i})")
        y = binary_label_from_trimed_folder(d)
        if y is None:
            raise ValueError(f"Could not classify Trimed folder name: {d!r}")
        mapping[str(i)] = y
    return mapping


run = None
if wandb is not None:
    run = wandb.init(
        project="network-traffic-classification",
        job_type="preprocess",
        name=f"{LAYER_TAG.lower()}_binary_histogram",
        config={
            "train_dir": TRAIN_DIR,
            "trimed_train": TRIMED_TRAIN,
            "num_bins": 32,
            "mode": "binary",
            "layer": LAYER_TAG,
            "output_csv": OUTPUT_CSV,
        },
    )

idx_to_y = build_index_to_label()
rows = []
for class_dir in tqdm(sorted(os.listdir(TRAIN_DIR), key=lambda x: int(x) if x.isdigit() else x)):
    class_path = os.path.join(TRAIN_DIR, class_dir)
    if not os.path.isdir(class_path):
        continue
    if class_dir not in idx_to_y:
        continue
    y = idx_to_y[class_dir]
    for img_name in os.listdir(class_path):
        img_path = os.path.join(class_path, img_name)
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        hist = cv2.calcHist([img], [0], None, [32], [0, 256]).flatten()
        rows.append(list(hist) + [y])

shuffle(rows)
columns = [f"bin_{i}" for i in range(32)] + ["label"]
df = pd.DataFrame(rows, columns=columns)
print(df.shape)
print("label counts:\n", df["label"].value_counts().sort_index())
df.to_csv(OUTPUT_CSV, index=False)

if run is not None:
    run.log({
        "dataset_rows": int(df.shape[0]),
        "dataset_cols": int(df.shape[1]),
        "num_benign_rows": int((df["label"] == 1).sum()),
        "num_malware_rows": int((df["label"] == 0).sum()),
    })
    run.finish()
