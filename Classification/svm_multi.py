import os

import numpy as np
from sklearn import preprocessing, model_selection, metrics
import pandas as pd
from sklearn.svm import SVC 
try:
    import wandb
except ImportError:
    wandb = None

DATASET_CSV = os.environ.get("NTC_DATASET_CSV", "dataset_L7_multiclass_bin32.csv")
LAYER_TAG = os.environ.get("NTC_LAYER", "L7")
WANDB_RUN_NAME = os.environ.get(
    "NTC_WANDB_TRAIN_NAME",
    f"svm_multiclass_{LAYER_TAG.lower()}_bin32",
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
            "C": 1,
            "test_size": 0.2,
        },
    )

df = pd.read_csv(DATASET_CSV)
df.replace('?',-99999, inplace=True)
#df.drop(['random'], 1, inplace=True)

X = np.array(df.drop(columns=['label']))
y = np.array(df['label'])

X_train, X_test, y_train, y_test = model_selection.train_test_split(X, y, test_size=0.2)

min_max_scaler = preprocessing.MinMaxScaler()
X_train_minmax = min_max_scaler.fit_transform(X_train)
X_test_minmax = min_max_scaler.transform(X_test)

svm_model_linear = SVC(kernel = 'linear',C=1).fit(X_train_minmax, y_train) 
svm_predictions = svm_model_linear.predict(X_test_minmax)

print(f'MULTI-CLASS CLASSIFICATION ({LAYER_TAG}) BIN SIZE 32')
print('')
  
# model accuracy for X_test   
accuracy = svm_model_linear.score(X_test_minmax, y_test)
print("Accuracy =", accuracy)
print('')

report = metrics.classification_report(y_test,svm_model_linear.predict(X_test_minmax))
print("Report")
print(report)
print()
if run is not None:
    run.log({
        "accuracy": float(accuracy),
        "num_train_samples": int(X_train.shape[0]),
        "num_test_samples": int(X_test.shape[0]),
        "num_features": int(X_train.shape[1]),
        "num_classes": int(len(np.unique(y))),
        "total_support_vectors": int(np.sum(svm_model_linear.n_support_)),
    })
    run.summary["classification_report"] = report
# creating a confusion matrix 
#cm = confusion_matrix(y_test, svm_predictions)
#print("confusion matrix")
#print(cm)
print('')
su_vec = svm_model_linear.support_vectors_
print('support vectors')
print(su_vec)
print('')
su_vec_n = svm_model_linear.n_support_
print('Number of support vectors for each class')
print(su_vec_n)
print('')
print('total Number of support vectors')
print(sum(su_vec_n))
print('')
weights = svm_model_linear.coef_
print('The weights associated for each feature')
print(weights)
if run is not None:
    run.finish()

