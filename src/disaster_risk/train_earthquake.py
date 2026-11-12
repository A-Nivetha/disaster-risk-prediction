"""Train the earthquake severity classifier (Low/Medium/High from magnitude, without magnitude or significance as inputs).
Usage: python -m disaster_risk.train_earthquake --data data/raw/Eartquakes-1990-2023.csv"""
import argparse

import numpy as np
import xgboost
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_sample_weight
from xgboost import XGBClassifier

from . import config as C
from . import metrics
from .data import load_earthquakes

PARAMS = dict(
    n_estimators=200, max_depth=8, learning_rate=0.1, subsample=0.8,
    colsample_bytree=1.0, objective="multi:softprob", eval_metric="mlogloss",
    tree_method="hist", n_jobs=-1, random_state=C.SEED,
)


def _fit_eval(X_tr, X_te, y_tr, y_te, balanced):
    weights = compute_sample_weight("balanced", y_tr) if balanced else None
    model = XGBClassifier(**PARAMS).fit(X_tr, y_tr, sample_weight=weights)
    pred = model.predict(X_te)
    result = {
        "sample_weighting": "balanced" if balanced else "none",
        "test_accuracy": round(float(accuracy_score(y_te, pred)), 4),
        "test_macro_f1": round(float(f1_score(y_te, pred, average="macro")), 4),
        "confusion_matrix": confusion_matrix(y_te, pred).tolist(),
        "report": classification_report(y_te, pred, target_names=C.SEVERITY_LABELS, output_dict=True),
    }
    return model, result


def main(data_path, variant="none"):
    X, y, info = load_earthquakes(data_path)
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, random_state=C.SEED, stratify=y)
    model, result = _fit_eval(X_tr, X_te, y_tr, y_te, balanced=(variant == "balanced"))

    if variant == "balanced":
        # Documentation only: records the precision/recall trade-off, saves no model.
        current = metrics.load()["earthquake_severity"]
        current["alternative_balanced_weights"] = result
        metrics.update("earthquake_severity", current)
        print(result["test_accuracy"], result["test_macro_f1"])
        return

    # The unweighted model is the one saved (higher macro-F1).
    baseline_acc = float((y_te == int(np.bincount(y_te).argmax())).mean())
    C.MODELS_DIR.mkdir(exist_ok=True)
    model.save_model(C.MODELS_DIR / "earthquake_severity_xgb.json")
    metrics.update("earthquake_severity", {
        "task": "3-class severity from magnitude (Low <4.0, Medium 4.0-6.0, High >=6.0)",
        "features": C.EQ_FEATURES, "excluded": ["magnitudo", "significance"],
        "labels": C.SEVERITY_LABELS, "seed": C.SEED, "test_size": 0.2,
        "xgboost_version": xgboost.__version__,
        **info,
        "class_counts": {C.SEVERITY_LABELS[i]: int((y == i).sum()) for i in range(3)},
        "majority_class_baseline_accuracy": round(baseline_acc, 4),
        "saved_model": result,
        "params": {k: v for k, v in PARAMS.items() if k != "n_jobs"},
    })
    print(info, "baseline", baseline_acc, result["test_accuracy"], result["test_macro_f1"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(C.RAW_DIR / "Eartquakes-1990-2023.csv"))
    ap.add_argument("--variant", choices=["none", "balanced"], default="none")
    a = ap.parse_args()
    main(a.data, a.variant)
