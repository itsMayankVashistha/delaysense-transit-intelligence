# Repository Tree Map

This map reflects the repository as it exists now.

Excluded on purpose:

- `.git/`
- `.venv/`
- `__pycache__/`

## Repository Tree

```text
delaysense-transit-intelligence/
|-- .env
|-- .gitignore
|-- LICENSE
|-- Makefile
|-- README.md
|-- __init__.py
|-- environment.yml
|-- requirements.txt
|-- requirements_dev.txt
|
|-- .github/
|   `-- workflows/
|       |-- add_issue_todo.yml
|       |-- add_issue_to_done.yml
|       |-- add_pr_in_progress.yml
|       `-- add_pr_to_done.yml
|
|-- app/
|   |-- bootstrap.py
|   |-- test_run.py
|   |
|   |-- api/
|   |   |-- main.py
|   |   `-- routes.py
|   |
|   |-- artifacts/
|   |   |-- baseline_table.parquet
|   |   `-- model.joblib
|   |
|   |-- config/
|   |   `-- settings.py
|   |
|   |-- models/
|   |   |-- lightgbm_v2_h300_balanced.joblib
|   |   |-- lightgbm_v2_h300_conservative.joblib
|   |   |-- lightgbm_v2_h300_sensitive.joblib
|   |   |-- xgboost_h300_balanced.joblib
|   |   |-- xgboost_h300_conservative.joblib
|   |   `-- xgboost_h300_sensitive.joblib
|   |
|   |-- services/
|   |   |-- artifact_loader.py
|   |   |-- baseline_service.py
|   |   |-- explanation_utils.py
|   |   |-- feature_pipeline.py
|   |   |-- inference_service.py
|   |   |-- intelligence_layer.py
|   |   |-- live_monitor_manager.py
|   |   |-- mock_model.py
|   |   |-- retrieval_utils.py
|   |   |-- rolling_cache.py
|   |   `-- tfl_api_service.py
|   |
|   `-- ui/
|       |-- streamlit_app.py
|       `-- assets/
|           |-- banner.png
|           `-- banner1.png
|
|-- data/
|   |-- .gitkeep
|   |-- README.md
|   |-- data.parquet
|   |-- sample_data.parquet
|   `-- processed/
|       |-- baseline_table_192H_60.parquet
|       |-- baseline_table_192H_60_forecast.parquet
|       |-- dataset_192H_60.parquet
|       |-- dataset_192H_60_forecast.7z
|       |-- dataset_192H_60_forecast.parquet
|       `-- dataset_60.7z
|
|-- docs/
|   |-- eda_report.md
|   |-- file_dependency_map.md
|   |-- Ml_contract_DelaySense.md
|   |-- project_overview.md
|   |-- release_v1.0.0.md
|   |-- repository_architecture.md
|   `-- repository_tree_map.md
|
|-- images/
|   |-- architecture_overview.png
|   |-- dashboard.png
|   `-- workflow.png
|
|-- modeling/
|   |-- config.py
|   |-- feature_engineering.py
|   |-- predict.py
|   |-- train.py
|   `-- validate_model_artifact.py
|
|-- models/
|   `-- (legacy or auxiliary modeling artifacts not used by the active runtime path)
|
|-- notebooks/
|   |-- 01_eda_and_baseline_modeling.ipynb
|   `-- 02_horizon_target_comparison.ipynb
|
`-- scripts/
    |-- backup_sqlite.py
    |-- build_dataset.py
    |-- check_db.py
    |-- collect_arrivals.py
    `-- fetch_stations.py
```

## Directory Intent

- `app/`: deployed product code for FastAPI, Streamlit, runtime services, and packaged runtime artifacts.
- `data/`: local datasets, sample data, and processed outputs used for baselines and optional historical intelligence.
- `docs/`: current documentation for architecture, repository structure, project overview, contracts, and release notes.
- `images/`: images used by the README and documentation.
- `modeling/`: model development and validation area; only part of it is aligned with the active runtime.
- `models/`: older or auxiliary model artifacts outside the active deployment path.
- `notebooks/`: exploratory analysis and modeling notebooks.
- `scripts/`: ingestion and dataset-building utilities for the TfL forecasting workflow.

## Important Notes

- `app/api/routes.py` exists but is not the primary API implementation; the active endpoints live in `app/api/main.py`.
- `app/artifacts/model.joblib` exists but is currently a placeholder and is not the configured runtime model path.
- The active deployed model path in `app/config/settings.py` points to `app/models/lightgbm_v2_h300_balanced.joblib`.
- `data/sample_data.parquet` is intentionally included as a lightweight shareable dataset for GitHub and quick inspection.
- The top-level `models/` directory should be treated as historical or auxiliary unless explicitly re-integrated into the runtime app.
