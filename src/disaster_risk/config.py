from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = ROOT / "models"
REPORTS_DIR = ROOT / "reports"
DATASETS_DIR = ROOT / "datasets"
RAW_DIR = DATASETS_DIR / "raw"
SAMPLES_DIR = DATASETS_DIR / "samples"
STORAGE_DIR = ROOT / "storage"  # local SQLite history, git-ignored

SEED = 42

# Flood: FloodProbability >= threshold -> class 1 (flood)
FLOOD_THRESHOLD = 0.5
FLOOD_TARGET = "FloodProbability"

# Earthquake severity from magnitude: Low < 4.0 <= Medium < 6.0 <= High
SEVERITY_LABELS = ["Low", "Medium", "High"]
SEVERITY_EDGES = (4.0, 6.0)
# Rows below this magnitude are sentinel/invalid values (the data contains -10)
MIN_VALID_MAGNITUDE = -5.0
# `significance` is excluded on purpose: it is derived from magnitude (leakage)
EQ_FEATURES = ["longitude", "latitude", "depth"]
# Lowest depth (km) the dashboard form accepts. The data minimum is -10.0; the sample's lowest value is -3.33.
MIN_INPUT_DEPTH = -3.0
