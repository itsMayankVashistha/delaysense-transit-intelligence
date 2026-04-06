# DelaySense v1.0.0 - Capstone Final Product Release

## Version

`v1.0.0`

## Release Summary

DelaySense is a real-time transit intelligence system that predicts whether a currently visible London Underground arrival is likely to become delayed in the next few minutes.

Instead of only showing the current countdown, the system adds forecasting, baseline comparison, and live contextual monitoring so operators and viewers can identify which arrivals are most likely to turn problematic next.

## What the system does

- ingests live London Underground arrival data from the TfL Arrivals API
- computes contextual features from current state, rolling short-term behavior, and historical baselines
- predicts short-horizon delay risk using trained machine learning model artifacts
- serves predictions and monitoring state through a FastAPI backend
- presents results through a Streamlit dashboard designed for both demo storytelling and live monitoring

## Key features

- real-time delay-risk scoring for monitored arrivals
- forecasting-based prediction instead of simple current-state display
- rolling live context with warm-up aware monitoring behavior
- baseline comparison against expected arrival time patterns
- configurable alert sensitivity modes: Conservative, Balanced, Sensitive
- optional historical intelligence layer for narrative context and similar-case retrieval
- packaged model artifact loading with metadata-aware inference support
- API-first design with a separate dashboard client

## Included demo and live modes

### Showcase demo mode

- uses curated scenarios embedded in the Streamlit app
- highlights high, medium, and low risk cases for presentations and product walkthroughs
- supports product storytelling without relying on live API availability

### Live TfL mode

- polls the TfL Arrivals API for selected monitored stations
- scores live arrivals through the backend monitor manager
- exposes current live status, warm-up state, and prioritized results

## Main stack

- Python
- FastAPI
- Streamlit
- pandas
- scikit-learn compatible model artifacts loaded via joblib
- LightGBM and XGBoost runtime model variants
- SQLite for raw arrival collection
- Parquet for processed datasets and baseline tables
- TfL Arrivals API as the external live data source

## Known limitations

- live rolling features require warm-up time before the monitor reaches stable context
- the monitored live scope is limited to selected stations and lines configured in the runtime app
- the historical intelligence layer depends on local availability of `data/data.parquet`
- parts of the `modeling/` directory still reflect an older workflow and are not yet the single source of truth for deployment
- publishing the actual GitHub release must still be done from GitHub or a machine with GitHub CLI access and repository authentication

## Suggested GitHub Release Title

`DelaySense v1.0.0 - Capstone Final Product Release`
