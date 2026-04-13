# Modeling

The DelaySense models were trained and validated interactively during development.
The full training workflow is documented in the project notebooks:

- `notebooks/01_eda_and_baseline_modeling.ipynb` — EDA, baseline modeling, feature analysis
- `notebooks/02_horizon_target_comparison.ipynb` — horizon tuning and model comparison

## Deployed artifact

The production model used by the inference layer is:

`app/models/lightgbm_v2_h300_balanced.joblib`

Model selection, validation, and threshold analysis are documented in the notebooks above.