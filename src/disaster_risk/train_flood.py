"""Train the flood classifier. Usage: python -m disaster_risk.train_flood --data data/raw/flood1.csv"""
import argparse
import json

import xgboost
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from xgboost import XGBClassifier

from . import config as C
from . import metrics
from .data import load_flood

PARAMS = dict(
    n_estimators=500, max_depth=6, learning_rate=0.05, subsample=0.85,
    colsample_bytree=0.85, min_child_weight=5, gamma=0.05, reg_alpha=0.05,
    reg_lambda=1.0, objective="binary:logistic", eval_metric="logloss",
    tree_method="hist", n_jobs=-1, random_state=C.SEED,
)


def main(data_path):
    X, y = load_flood(data_path)
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, random_state=C.SEED, stratify=y)

    model = XGBClassifier(**PARAMS).fit(X_tr, y_tr)
    pred = model.predict(X_te)

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=C.SEED)
    cv_scores = cross_val_score(XGBClassifier(**PARAMS), X, y, cv=cv, scoring="accuracy")

    C.MODELS_DIR.mkdir(exist_ok=True)
    model.save_model(C.MODELS_DIR / "flood_xgb.json")
    (C.MODELS_DIR / "flood_features.json").write_text(json.dumps({
        "features": list(X.columns),
        "ranges": {c: [int(X[c].min()), int(X[c].max())] for c in X.columns},
        "medians": {c: float(X[c].median()) for c in X.columns},
    }, indent=2))

    metrics.update("flood", {
        "task": f"binary: FloodProbability >= {C.FLOOD_THRESHOLD}",
        "dataset_rows": int(len(X)), "n_features": int(X.shape[1]),
        "test_size": 0.2, "seed": C.SEED, "xgboost_version": xgboost.__version__,
        "class_share_flood": round(float(y.mean()), 4),
        "test_accuracy": round(float(accuracy_score(y_te, pred)), 4),
        "cv5_accuracy_mean": round(float(cv_scores.mean()), 4),
        "cv5_accuracy_std": round(float(cv_scores.std()), 4),
        "confusion_matrix": confusion_matrix(y_te, pred).tolist(),
        "report": classification_report(y_te, pred, output_dict=True),
        "params": {k: v for k, v in PARAMS.items() if k != "n_jobs"},
    })
    print("test accuracy", accuracy_score(y_te, pred), "| CV", cv_scores.mean(), cv_scores.std())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(C.RAW_DIR / "flood1.csv"))
    main(ap.parse_args().data)
