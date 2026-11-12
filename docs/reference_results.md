# Reference results

Values written to `reports/metrics.json` by `python -m disaster_risk.train_flood` and `python -m disaster_risk.train_earthquake` (XGBoost 3.4.1, seed 42, 20% stratified test split). The earthquake model uses longitude, latitude and depth.
After running the two training scripts, the numbers in `reports/metrics.json` must match these. A mismatch means
the data files differ from the ones used for the saved models.

| Item | Value |
|---|---|
| Flood: rows, features | 50,000, 20 |
| Flood: flood class share | 0.5103 |
| Flood: test rows (no flood / flood) | 4,897 / 5,103 |
| Flood: test accuracy | 0.9446 |
| Flood: 5-fold CV accuracy, mean / std | 0.9490 / 0.0016 |
| Earthquake: rows raw / dropped invalid / used | 3,445,751 / 647 / 3,445,104 |
| Earthquake: class counts (Low / Medium / High) | 3,062,035 / 378,128 / 4,941 |
| Earthquake: test rows (Low / Medium / High) | 612,407 / 75,626 / 988 |
| Earthquake: majority-class baseline accuracy | 0.8888 |
| Earthquake: test accuracy | 0.9754 |
| Earthquake: macro F1 | 0.6299 |
| Earthquake: High-class recall | 0.0061 (6 of 988) |
