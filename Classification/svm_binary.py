import os

import numpy as np
from sklearn import preprocessing, model_selection, metrics, svm
import pandas as pd

try:
    import wandb
except ImportError:
    wandb = None

DATASET_CSV = os.environ.get("NTC_DATASET_CSV", "dataset_L7_binary_bin32.csv")
LAYER_TAG = os.environ.get("NTC_LAYER", "L7")
WANDB_RUN_NAME = os.environ.get(
    "NTC_WANDB_TRAIN_NAME",
    f"svm_binary_{LAYER_TAG.lower()}_bin32",
)

run = None
if wandb is not None:
    run = wandb.init(
        project="network-traffic-classification",
        job_type="train",
        name=WANDB_RUN_NAME,
        config={
            "dataset": DATASET_CSV,
            "layer": LAYER_TAG,
            "model": "SVC",
            "kernel": "linear",
            "test_size": 0.1,
        },
    )

df = pd.read_csv(DATASET_CSV)
df.replace("?", -99999, inplace=True)

X = np.array(df.drop(columns=["label"]))
y = np.array(df["label"])

X_train, X_test, y_train, y_test = model_selection.train_test_split(
    X, y, test_size=0.1, random_state=42, stratify=y,
)

min_max_scaler = preprocessing.MinMaxScaler()
X_train = min_max_scaler.fit_transform(X_train)
X_test = min_max_scaler.transform(X_test)

clf = svm.SVC(kernel="linear")
clf.fit(X_train, y_train)

print(f"BINARY CLASSIFICATION ({LAYER_TAG})")
print("")

accuracy = clf.score(X_test, y_test)
print("Accuracy =", accuracy)
print("")

report = metrics.classification_report(y_test, clf.predict(X_test))
print("Report")
print(report)
print()

if run is not None:
    run.log({
        "accuracy": float(accuracy),
        "num_train_samples": int(X_train.shape[0]),
        "num_test_samples": int(X_test.shape[0]),
        "num_features": int(X_train.shape[1]),
        "total_support_vectors": int(np.sum(clf.n_support_)),
    })
    run.summary["classification_report"] = report

print("support vectors")
print(clf.support_vectors_)
print("")
print("Number of support vectors for each class")
print(clf.n_support_)
print("")
print("total Number of support vectors")
print(int(np.sum(clf.n_support_)))
print("")
print("The weights associated for each feature")
print(clf.coef_)

if run is not None:
    run.finish()
