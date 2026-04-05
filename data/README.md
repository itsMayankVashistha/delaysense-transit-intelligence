# Data

This repository includes a small sample dataset for demonstration and local testing.

## Included
- `sample_data.parquet` — lightweight sample extracted from the full processed dataset

## Not included
The full processed dataset is not stored in GitHub because of repository size constraints.

## Reproducing the dataset
The full dataset can be recreated using the project scripts:
- `scripts/collect_arrivals.py`
- `scripts/build_dataset.py`

These scripts collect live TfL arrival snapshots, store them in SQLite, and convert them into modeling-ready parquet datasets with rolling features and forecasting targets.