# Notebook Results Report: 60s vs 180s Target Comparison

## Notebook

- Source notebook: `models/models_target_comparison_60s_vs_180s.ipynb`
- Dataset: `data/processed/dataset_192H_60.parquet`

## Objective

The notebook compared two target definitions for late-train classification:

- `late`: deviation from baseline greater than 60 seconds
- `late_3min`: deviation from baseline greater than 180 seconds

The evaluation goal was not to force the models into generic precision, recall, and F1 target bands. Instead, the notebook compared both targets in a more business-aware way using:

- class balance
- ranking metrics
- baseline lift
- passenger-oriented operating thresholds
- alert burden measures

## Class Balance

Observed positive rates:

- `late`: `0.4447`
- `late_3min`: `0.3566`

Interpretation:

- the 60-second target is close to balanced
- the 180-second target is still workable and not severely imbalanced
- class imbalance is no longer the main performance bottleneck

## Warnings Seen During Execution

### LogisticRegression convergence warning

`LogisticRegression` did not converge within `max_iter=2000`.

Interpretation:

- this affects the logistic baseline quality somewhat
- it does not invalidate the notebook
- it is not the main driver of the conclusions because the tree models are the main candidates

### LightGBM feature-name warning

LightGBM emitted a warning about feature names during prediction.

Interpretation:

- this is a common sklearn and LightGBM interoperability warning
- it is not evidence that the model results are unusable

## Results For 60-Second Target

Best ranking metrics:

- LightGBM:
  - `avg_precision = 0.4854`
  - `roc_auc = 0.5477`
  - `logloss = 0.6849`
- DummyPrior:
  - `avg_precision = 0.4465`
  - `roc_auc = 0.5000`

Interpretation:

- the model has some signal above the dummy baseline
- but the lift is modest
- ROC-AUC around `0.55` is still weak
- the model does not separate late vs not-late strongly

Passenger-oriented best threshold:

- LightGBM at threshold `0.65`
  - precision `0.6846`
  - recall `0.0027`
  - F1 `0.0054`
  - false alerts per hour `87.6360`
  - false alerts per station-hour `2.1031`

Interpretation:

- precision looks acceptable
- recall is effectively zero
- the model only catches a tiny fraction of truly late trains
- this is not a usable passenger-facing alert model

## Results For 180-Second Target

Best ranking metrics:

- LightGBM:
  - `avg_precision = 0.4186`
  - `roc_auc = 0.5826`
  - `logloss = 0.6663`
- DummyPrior:
  - `avg_precision = 0.3602`
  - `roc_auc = 0.5000`

Interpretation:

- the 180-second target is cleaner than the 60-second target
- the lift over dummy is stronger
- ranking quality is better than for the 60-second target
- this suggests the 180-second label is less noisy and more learnable

Passenger-oriented best threshold:

- LightGBM at threshold `0.70`
  - precision `0.7258`
  - recall `0.0010`
  - F1 `0.0021`
  - false alerts per hour `22.2089`
  - false alerts per station-hour `0.5330`

Interpretation:

- this is cleaner than the 60-second case
- false-alert burden is substantially lower
- but recall is still effectively zero
- so this is still not good enough for deployment

## Comparison Between Targets

### What improved with `late_3min`

Compared with `late`, the `late_3min` target showed:

- better ROC-AUC
- stronger lift over the dummy baseline
- higher top precision in the passenger-oriented setup
- lower false alerts per hour
- lower false alerts per station-hour

### What did not improve enough

Even with `late_3min`:

- recall at passenger-friendly precision remained near zero
- F1 at the chosen passenger threshold remained near zero
- no model achieved a strong practical balance between precision and recall

## Main Conclusion

The notebook was successful as an evaluation tool, because it exposed the true trade-off.

It showed that:

1. The old problem of very high recall and low precision is not the full story.
2. Once we enforce a more realistic precision floor for passenger-facing use, recall collapses.
3. The `late_3min` target is better than the `late` target under the current feature and model setup.
4. However, the current models are still not strong enough for a real passenger-facing alert product.

So the conclusion is:

- `late_3min` is the better main candidate target so far
- but the modeling pipeline still needs feature improvements before it can be considered strong

## Runtime Note

Cell 4 took about `77 minutes`.

This is believable for this setup because the notebook:

- used a dataset with about `24.6 million` rows
- ran two full target evaluations
- trained seven models for each target
- applied large one-hot preprocessing
- computed threshold tables for each model

This is slow but not abnormal.

## Recommended Next Step

The next notebook iteration should:

- keep `late_3min` as the main target
- drop `AlwaysLate` and `AlwaysNotLate` from routine runs
- keep routine comparisons focused on:
  - `DummyPrior`
  - `LogisticRegression`
  - `XGBoost`
  - `LightGBM`
- run one model per cell for easier runtime tracking
- test feature improvements and then re-check whether recall can improve without giving up too much precision

## Note On `time_to_station`

`time_to_station` is not direct target leakage by itself.

The target is defined from:

- `deviation_from_baseline = time_to_station - baseline_median_tts`

So:

- `deviation_from_baseline` is direct leakage and should stay excluded
- `time_to_station` is not identical to the target and is available at inference time

However, it is a very strong proxy feature, so it should be added only as a deliberate experiment and judged carefully.

That means:

- it is valid to test
- but we should evaluate whether it makes the model more useful in a product sense, not just numerically stronger
