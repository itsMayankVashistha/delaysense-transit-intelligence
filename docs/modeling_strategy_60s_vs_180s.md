# TfL Delay Modeling Strategy: 60s vs 180s Targets

## Purpose

This document captures the current state of the TfL late-train modeling work, what the existing notebook has achieved so far, why parts of the previous evaluation logic were misleading, and how we should evaluate the next version of the models in a way that matches the product we are trying to build.

The current working assumption in this document is:

- `late` means the train is more than 60 seconds worse than its baseline
- we also want to test a second target, `late_3min`, defined as more than 180 seconds worse than baseline

We are not using the older 5-minute definition here.

## Current Data and Label Setup

The processed dataset is:

- `data/processed/dataset_192H_60.parquet`

This dataset currently contains:

- the existing target column `late` based on the 60-second rule
- `deviation_from_baseline`, which allows us to derive a second target for 180 seconds

Observed class balance from the dataset:

- `late` at 60 seconds: about `44.47%` positive
- `late_3min` at 180 seconds: about `35.66%` positive

This means:

- the 60-second target is much less imbalanced than the old 5-minute version
- the 180-second target is still workable and may be less noisy

## What The Existing v5 Notebook Does

The existing notebook:

- loads the processed dataset
- uses a time-aware split with the final fold as holdout
- trains `XGBoost`, `LightGBM`, and `CatBoost`
- compares against a `DummyClassifier` and `LogisticRegression`
- searches for a threshold using fixed metric bands
- adds some backtesting and stability checks

The current v5 feature set is:

- categorical:
  - `stop_id`
  - `stop_name`
  - `line_id`
  - `direction`
  - `platform_name`
  - `destination_name`
- numeric:
  - `hour`
  - `weekday`
  - `is_weekend`
  - `roll_mean_tts_10m`
  - `roll_max_tts_10m`
  - `roll_count_10m`
  - `baseline_median_tts`

Columns not used as model features in v5:

- `observed_at`
  - used for chronological ordering, not as a raw feature
- `late`
  - the target
- `deviation_from_baseline`
  - should not be used as a feature because it directly defines the target
- `roll_std_tts_10m`
  - left out in the current setup, likely to keep the baseline notebook simpler and cheaper
- `time_to_station`
  - excluded in the current notebook for a cleaner baseline setup, but worth testing later as an explicit experiment

## What We Have Achieved So Far

The current notebook has already established several important things:

1. The 60-second target reduces the old class imbalance materially.
2. Tree models are only slightly better than a dummy prior baseline on the current feature set.
3. The current thresholding logic cannot achieve the originally desired precision and recall bands.
4. The best-F1 operating points are all very high-recall and low-precision.
5. The current models are not yet strong enough for a reliable passenger-facing alert system.

In plain language:

- the model has some signal
- but it does not separate late vs not-late cleanly enough yet
- so it tends to predict "late" too often

## Why The Previous Evaluation Logic Was Misleading

The old logic used fixed metric bands:

- precision between `0.5` and `0.7`
- recall between `0.7` and `0.9`
- F1 between `0.6` and `0.8`

Then it searched for thresholds that fit those bands.

This is misleading for two reasons.

### 1. The bands are not universal truth

Those values are not "standard good model" numbers for every problem. A good threshold depends on the cost of:

- false positives
- false negatives
- user trust
- operational burden

### 2. Best F1 can still mean a poor product outcome

With the current 60-second target, the positive class is common enough that a model can get:

- very high recall
- only slightly above-base-rate precision
- an F1 score that looks acceptable on paper

while still producing too many false alerts to be useful in practice.

That is what happened in the current notebook.

## What We Should Optimize For Instead

The goal is not:

- "find a threshold that satisfies internet metric bands"

The goal is:

- determine whether the model creates useful, trustworthy alerts for the product

That means our evaluation should answer:

1. Is the model meaningfully better than simple baselines?
2. Does it rank truly late cases above normal cases well enough?
3. At realistic thresholds, how many false alerts does it create?
4. Would users trust those alerts?

## Recommended Evaluation Framework

### 1. Compare against simple baselines

Every target should be compared against:

- `DummyPrior`
- `AlwaysLate`
- `AlwaysNotLate`
- `LogisticRegression`
- the tree models

Why:

- if the model is only slightly better than "always late", then the product value is still weak

### 2. Use threshold-free ranking metrics

Primary ranking metrics:

- `PR-AUC` or average precision
- `ROC-AUC`

Why:

- these tell us whether the model has useful ranking power before threshold choice
- they are a cleaner way to assess whether the signal exists at all

How to interpret them in this project:

- `ROC-AUC` near `0.50` means nearly random ranking
- `PR-AUC` should be judged against the positive rate
- if `PR-AUC` is only slightly above the class prevalence, the model has limited value

### 3. Evaluate confusion-matrix outcomes at business-relevant thresholds

For each model and target, we should inspect thresholds through:

- precision
- recall
- F1
- true positives
- false positives
- false negatives
- specificity
- alert rate

Why:

- this shows the real trade-off between catching delays and generating false alarms

### 4. Translate results into operational burden

We should estimate:

- expected alerts per hour
- expected false alerts per hour
- expected alerts per station-hour
- expected false alerts per station-hour

Why:

- a model may look fine numerically while still producing an unusable stream of alerts

### 5. Use product-oriented thresholds

Thresholds should be chosen by business mode.

For a passenger-facing alert product:

- precision matters most
- too many false positives destroy trust

For an internal monitoring product:

- recall can matter more
- more false positives may be acceptable

## Recommended Bands For This Project

These are not universal. They are project-specific starting bands.

### Passenger-facing recommendation

- precision: `0.60+`
- recall: `0.35` to `0.70`
- F1: secondary
- alert rate: should remain believable and manageable

Reason:

- if more than 40% of alerts are wrong, users are likely to stop trusting the system

### Internal monitoring recommendation

- precision: `0.50+`
- recall: `0.60+`

Reason:

- internal users can often tolerate more noise if the system helps them catch more true delay events

## How To Think About 60 Seconds vs 180 Seconds

### 60-second target

Pros:

- more sensitive
- earlier warning
- more positive examples

Cons:

- likely noisier
- may reflect normal fluctuation rather than meaningful disruption
- may make precision harder to achieve

### 180-second target

Pros:

- likely cleaner signal
- probably more meaningful to passengers
- may allow higher precision

Cons:

- fewer positives
- later detection
- may miss smaller but still relevant disruptions

### Practical interpretation

If the 60-second target gives:

- low precision
- weak PR-AUC lift
- very high alert burden

while the 180-second target gives:

- stronger precision
- clearer lift over baselines
- more usable alert volume

then the 180-second target is likely the better product choice even if it is less "balanced" as a label.

## What The Next Notebook Should Do

The next notebook should:

1. load `dataset_192H_60.parquet`
2. create `late_3min = 1(deviation_from_baseline > 180)`
3. run the same modeling workflow separately for:
   - `late`
   - `late_3min`
4. compare both targets using:
   - class balance
   - baseline metrics
   - model ranking metrics
   - threshold tables
   - confusion-matrix summaries
   - alert burden metrics
5. recommend which target is more product-appropriate

## What We Should Avoid In The Next Version

We should not:

- auto-generate "feasible metric bands" from weak model performance
- claim readiness because the model meets self-adjusted targets
- rely on F1 alone
- present generic online metric ranges as deployment truth

## What We Need Next To Get A Better Version

If the new notebook still shows weak separation, likely next steps are:

- compare 60-second vs 180-second labels directly
- test whether `time_to_station` should be added as a controlled feature experiment
- improve feature engineering around recent trend and station context
- inspect label noise, especially for the 60-second target
- tune models only after confirming the target definition is sensible

## Working Recommendation

Build the next notebook around both targets and use it to answer one core question:

- is the 60-second target useful enough for a real alert product, or is the 180-second target the better business definition of "late"?

That comparison should drive the next modeling decision, not generic metric bands.
