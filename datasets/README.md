# Datasets

Three public Kaggle datasets are used. All three are published under **CC0 1.0 (Public Domain Dedication)**; the licence
shown on each Kaggle page was checked on 2026-10-25. The raw files are not committed. Download them into `datasets/raw/`
with the file names below.

| Raw file | Kaggle source | Licence | Used for |
|---|---|---|---|
| `flood1.csv` | https://www.kaggle.com/datasets/naiyakhalid/flood-prediction-dataset (file `flood.csv` on Kaggle, renamed) | CC0 1.0 | Flood model, flood clustering |
| `Eartquakes-1990-2023.csv` | https://www.kaggle.com/datasets/alessandrolobello/the-ultimate-earthquake-dataset-from-1990-2023 | CC0 1.0 | Earthquake severity model, earthquake clustering |
| `flood_risk_dataset_india.csv` | https://www.kaggle.com/datasets/s3programmer/flood-risk-in-india | CC0 1.0 | Baseline comparison in a notebook only; not used by any saved model or by the dashboard |

The file name `Eartquakes-1990-2023.csv` keeps the spelling of the Kaggle download.

## Integrity check

Each local copy was compared with a fresh Kaggle download; the SHA-256 hashes were identical:

```
9cf6a2339d7c7524620f99497801c278e3c1ed0aca8d0fde22a683508fa10e8d  flood1.csv
a8ec444d0cb669da108ad66304e2ee7ddff5bbd8d2e65baef8354efd5dd0ef39  Eartquakes-1990-2023.csv
ea0924a7a36ab7c1d153fac6675c6cf72cd3d3d4373e1a0ad388676a01e3f88a  flood_risk_dataset_india.csv
```

Check yours with `sha256sum <file>` (Linux, macOS) or `certutil -hashfile <file> SHA256` (Windows).

## Contents

**`flood1.csv`**: 50,000 rows, 21 columns. 20 integer ratings (MonsoonIntensity, TopographyDrainage, RiverManagement,
Deforestation, Urbanization, ClimateChange, DamsQuality, Siltation, AgriculturalPractices, Encroachments,
IneffectiveDisasterPreparedness, DrainageSystems, CoastalVulnerability, Landslides, Watersheds,
DeterioratingInfrastructure, PopulationScore, WetlandLoss, InadequatePlanning, PoliticalFactors) and the target
`FloodProbability`. The model label is `FloodProbability >= 0.5` (flood class 51.03% of rows). The real-world unit of the ratings is
not defined in the source. This is a tabular benchmark, not field measurements.

**`Eartquakes-1990-2023.csv`**: 3,445,751 rows of earthquake catalogue records, 1990 to 2023. Columns used: `longitude`,
`latitude`, `depth`, `magnitudo`. Rows with an invalid magnitude (the file uses -10; the rule drops values at or below -5; 647 rows) are dropped, leaving 3,445,104.
Severity is derived from magnitude: Low below 4.0, Medium 4.0 to below 6.0, High 6.0 or higher (3,062,035 / 378,128 / 4,941 events).
`magnitudo` and `significance` are not model inputs because they would leak the label.

**`flood_risk_dataset_india.csv`**: 10,000 rows, 14 columns (latitude, longitude, rainfall, temperature, humidity, river discharge,
water level, elevation, land cover, soil type, population density, infrastructure, historical floods, `Flood Occurred`).
A Random Forest baseline reached 50.25% test accuracy against a 50.55% majority-class baseline (see
`notebooks/Disaster_Prediction_ML_Pipeline.ipynb`), so no usable signal was found in it. No saved model or dashboard page uses it.
It has not been checked against national boundaries.

## Generated files (`datasets/samples/`, committed)

`python datasets/make_samples.py` builds small sample files; the dashboard reads only `samples_info.json` (the depth range):

- `usgs_events_sample.csv`: equal random sample per severity class
- `india_flood_points.csv`: latitude, longitude and label of every row of the India file
- `samples_info.json`: row counts, sampling description and depth range

## Citation

The authors of each dataset are credited on its Kaggle page (links above). CC0 does not require attribution; it is given here anyway.
The code in this repository is MIT licensed (see `LICENSE`); the datasets keep their own CC0 licence.
