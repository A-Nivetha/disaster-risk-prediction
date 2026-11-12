import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ui

ui.setup("Model reliability", "Test results for both models from reports/metrics.json, and their limits.")
import streamlit as st

m = ui.load_metrics()
fl, eq = m["flood"], m["earthquake_severity"]
sm, bal = eq["saved_model"], eq.get("alternative_balanced_weights")
rf, rs = fl["report"], sm["report"]

st.header("Flood class model")
ui.kpi_row([
    ("Test accuracy", f"{fl['test_accuracy']:.2%}", f"{int(rf['macro avg']['support']):,} held-out rows", "teal"),
    ("5-fold cross-validation", f"{fl['cv5_accuracy_mean']:.2%}", f"standard deviation {fl['cv5_accuracy_std']:.2%}", "teal"),
    ("Flood-class recall", f"{rf['1']['recall']:.2%}", f"precision {rf['1']['precision']:.2%}", "blue"),
    ("Flood class share", f"{fl['class_share_flood']:.2%}", "of all rows in the dataset", "blue"),
])
st.caption(f"{fl['dataset_rows']:,} rows, {fl['n_features']} integer ratings, {int(fl['test_size'] * 100)}% stratified test split, "
           f"seed {fl['seed']}, XGBoost {fl['xgboost_version']}.")

st.header("Earthquake severity model")
ui.kpi_row([
    ("Test accuracy", f"{sm['test_accuracy']:.2%}", f"baseline (always Low): {eq['majority_class_baseline_accuracy']:.2%}", "teal"),
    ("Macro F1", f"{sm['test_macro_f1']:.4f}", "mean of the three class F1 scores", "teal"),
    ("High-class recall", f"{rs['High']['recall']:.4f}", f"{sm['confusion_matrix'][2][2]} of {sum(sm['confusion_matrix'][2])} High test events", "red"),
    ("High-class precision", f"{rs['High']['precision']:.4f}", "share of High predictions that were High", "amber"),
])
st.caption(f"Inputs: {', '.join(eq['features'])}. Excluded: {', '.join(eq['excluded'])} (the label comes from magnitude, "
           f"so these would leak it). {eq['rows_used']:,} events used; {eq['rows_dropped_invalid_magnitude']:,} dropped for an invalid magnitude.")

st.header("Limits")
alt = (f" Balanced class weights raise High recall to {bal['report']['High']['recall']:.4f} and lower High precision "
       f"to {bal['report']['High']['precision']:.4f}.") if bal else ""
st.markdown(f"""
- **High class is barely detectable.** The saved model finds {rs['High']['recall']:.4f} of High events.{alt}
- **Not a forecast.** The earthquake model maps location and depth to the magnitude band in past records. It does not say when or where the next event occurs.
- **Optimistic test split.** Events close in space and time (aftershocks) sit in both training and test sets, so scores on a new region or period are likely lower. This was not measured.
- **Flood data is a tabular benchmark.** The label is FloodProbability cut at 0.5; accuracy is agreement with that label, not with observed floods.
""")
