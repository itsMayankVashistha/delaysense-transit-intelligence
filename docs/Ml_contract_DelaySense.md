
# ML Model Handoff Contract
## DelaySense — Model to Inference Integration

This document defines the exact contract required for handing over trained ML models from the modeling team to the inference/deployment layer.

The goal is to ensure that any delivered model artifact can be plugged into the API + Streamlit application without ambiguity, rework, or runtime failure.

---

# 1. Project Context

## Project
**DelaySense / Early Warning System**

## Problem Framing
We are working on **Path B only**.

This means the deployed model must predict **future delay risk**, not current delay status.

### Current target framing
Given features at time **t**, predict whether the arrival context will become delayed at time **t + H**.

### Main deployment horizon
For the current application, the preferred production target is:

- **H = 300 seconds**
- target name example: `future_late_3min_300s`

If another horizon is delivered, it must be explicitly documented.

---

# 2. Required Delivered Files

For each model candidate, the ML team must deliver:

## Mandatory
1. **Model artifact**
   - `.joblib` file

2. **Model metadata file**
   - `.json` file with the same base name as the model

3. **Feature contract file**
   - `.json` or `.txt` listing the exact model input features in the correct order

4. **Validation example file**
   - one small `.csv` or `.json` file with 3–10 example inference rows and expected output probabilities

## Recommended
5. **Evaluation summary**
   - markdown or csv summary of test performance

6. **Training notebook / script reference**
   - path or commit reference used to generate the model

---

# 3. Naming Convention

Use consistent file naming.

## Recommended format
`<model_family>_<target>_<mode>.joblib`

### Examples
- `lightgbm_v2_h300_balanced.joblib`
- `lightgbm_v2_h300_conservative.joblib`
- `xgboost_h300_sensitive.joblib`

For each model artifact, provide matching files:

- `lightgbm_v2_h300_balanced.joblib`
- `lightgbm_v2_h300_balanced.metadata.json`
- `lightgbm_v2_h300_balanced.features.json`

---

# 4. Required Metadata Schema

Each model must include a metadata file with the following fields.

## Example
```json
{
  "model_name": "lightgbm_v2_h300_balanced",
  "model_family": "LightGBM",
  "version": "v2",
  "target_name": "future_late_3min_300s",
  "horizon_seconds": 300,
  "mode_name": "balanced",
  "problem_type": "binary_classification",
  "positive_class_definition": "arrival context is late_3min at t + 300s",
  "train_period_start": "2026-02-24T00:00:00",
  "train_period_end": "2026-03-02T23:59:59",
  "validation_period_start": "2026-03-03T00:00:00",
  "validation_period_end": "2026-03-04T23:59:59",
  "test_period_start": "2026-03-05T00:00:00",
  "test_period_end": "2026-03-06T23:59:59",
  "feature_order": [
    "hour",
    "weekday",
    "is_weekend",
    "time_to_station",
    "roll_mean_tts_10m",
    "roll_max_tts_10m",
    "roll_count_10m",
    "baseline_median_tts",
    "deviation_from_baseline"
  ],
  "input_type": "dataframe",
  "predict_method": "predict_proba",
  "positive_class_index": 1,
  "threshold_used_for_mode": 0.60,
  "metrics": {
    "roc_auc": 0.986,
    "pr_auc": 0.964,
    "f1": 0.758,
    "precision": 0.786,
    "recall": 0.730
  },
  "notes": "Trained on Path B forecasting setup. Compatible with current live feature pipeline."
}
````

---

# 5. Required Feature Contract

The ML team must explicitly confirm the exact model input schema.

## Current expected deployed feature set

```text
hour
weekday
is_weekend
time_to_station
roll_mean_tts_10m
roll_max_tts_10m
roll_count_10m
baseline_median_tts
deviation_from_baseline
```

## Important

The ML team must confirm whether the model expects:

### Option A

A **pandas DataFrame** with these exact column names

or

### Option B

A **numeric array** in this exact order

This must not be left implicit.

---

# 6. Preprocessing Contract

The ML team must explicitly state whether preprocessing is already bundled inside the `.joblib`.

## Required answer

One of the following must be true:

### Case 1 — Full pipeline artifact

The `.joblib` already includes:

* imputation
* scaling if needed
* encoding if needed
* model

In this case, the inference layer sends only the raw feature DataFrame/array in the documented schema.

### Case 2 — Model only

The `.joblib` contains only the final trained estimator.

In this case, the ML team must also deliver:

* preprocessing artifact(s)
* exact preprocessing instructions
* required transformation logic

## Preferred delivery

For deployment simplicity, **Case 1 is strongly preferred**.

---

# 7. Probability Contract

The inference layer uses probability output.

The ML team must confirm:

1. the model supports `predict_proba`
2. class ordering is known
3. positive class index is explicitly documented

## Required explicit statement

Example:

> `predict_proba(X)[:, 1]` corresponds to the probability that `future_late_3min_300s = 1`.

Without this, probability interpretation is unsafe.

---

# 8. Threshold / Mode Contract

The deployment app supports user-facing alert modes:

* Conservative
* Balanced
* Sensitive

These modes may be implemented in one of two ways.

## Preferred approach

The model predicts probability only, and thresholding is handled in the app.

### Example app-side thresholds

* Conservative → 0.80
* Balanced → 0.60
* Sensitive → 0.40

## Alternative approach

Separate model artifacts are trained/tuned for different operational modes.

If this is done, the ML team must explicitly document:

* why separate joblibs are needed
* what differs between them
* whether the probability scale remains comparable

## Important

If multiple joblibs are sent for different modes, metadata must clearly indicate:

* mode name
* threshold used during evaluation
* whether the artifact itself differs structurally or only the recommended threshold differs

---

# 9. Label / Horizon Contract

Every delivered model must explicitly state:

* target label name
* horizon in seconds
* whether it predicts current delay or future delay

## Required

Only **future delay forecasting models** are acceptable for deployment.

### Acceptable example

`future_late_3min_300s`

### Not acceptable

Current-time `late_3min` reconstruction models from Path A

---

# 10. Validation Example Requirement

Each model handoff must include a tiny validation set for deployment testing.

## Required content

3–10 rows with:

* exact input features
* expected probability output
* optional expected label prediction at recommended threshold

## Example format

```csv
hour,weekday,is_weekend,time_to_station,roll_mean_tts_10m,roll_max_tts_10m,roll_count_10m,baseline_median_tts,deviation_from_baseline,expected_proba
8,1,0,660,640,710,6,440,220,0.81
14,2,0,300,310,340,5,320,-20,0.28
18,5,1,720,700,760,8,500,220,0.84
```

This file will be used for smoke testing in the inference layer.

---

# 11. Minimum Acceptance Checklist

A model handoff is considered deployable only if all of the following are true:

* [ ] `.joblib` file delivered
* [ ] metadata file delivered
* [ ] exact feature order delivered
* [ ] preprocessing ownership documented
* [ ] `predict_proba` supported
* [ ] positive class index documented
* [ ] horizon documented
* [ ] target label documented
* [ ] small validation sample delivered
* [ ] test metrics delivered
* [ ] model confirmed to be Path B compatible

---

# 12. Questions the ML Team Must Answer for Every Delivered Model

Please answer these for each model artifact:

1. What is the exact target label?
2. What is the forecast horizon in seconds?
3. Is this model Path B only?
4. What exact features are expected?
5. Does the model expect a DataFrame or numeric array?
6. Is preprocessing bundled inside the `.joblib`?
7. Does `predict_proba(X)[:, 1]` represent the positive class probability?
8. What is the recommended decision threshold?
9. What test metrics correspond to this artifact?
10. Which file should be considered the preferred production candidate?

---

# 13. Preferred Final Delivery Example

For one production-ready model, ideal handoff would be:

* `lightgbm_v2_h300_balanced.joblib`
* `lightgbm_v2_h300_balanced.metadata.json`
* `lightgbm_v2_h300_balanced.features.json`
* `lightgbm_v2_h300_balanced.validation_examples.csv`
* `model_comparison_summary.md`

And the team should state:

> This is the preferred production artifact for the current app.
> Target = `future_late_3min_300s`
> Horizon = 300 seconds
> Input type = pandas DataFrame with exact feature names
> Preprocessing is fully bundled
> Positive class probability = `predict_proba(X)[:, 1]`

---

# 14. Current Deployment Assumption

Unless explicitly revised, the deployment layer currently assumes:

* Path B forecasting
* binary classification
* 300-second horizon
* the following features:

```text
hour
weekday
is_weekend
time_to_station
roll_mean_tts_10m
roll_max_tts_10m
roll_count_10m
baseline_median_tts
deviation_from_baseline
```

If the modeling team changes any of the above, they must communicate it explicitly before handoff.

---

# 15. Final Note

The purpose of this contract is to prevent silent integration failure.

A `.joblib` file alone is **not sufficient** for deployment handoff.

The artifact is only considered usable when the associated metadata, feature schema, preprocessing contract, and validation examples are delivered with it.

