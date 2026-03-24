
# ML Integration Contract — TfL Delay Intelligence System

This document defines the required outputs from the ML modeling phase so that the
Inference / API / Dashboard / AI layer can be implemented without mismatch.

The goal is to ensure that the trained model can be used in the live inference system.

---

## 1. Model Artifact

Please provide the final trained model as a serialized file.

Accepted formats:

- `.joblib`
- `.pkl`

Example:

```

model_final.joblib

```

The model must already be trained and ready for inference.

No retraining should be required in the inference system.

---

## 2. Feature List Used for Training

Provide the exact list of features used to train the model.

The order must match the training order.

Example:

```

[
"time_to_station",
"roll_mean_tts_10m",
"roll_max_tts_10m",
"roll_count_10m",
"baseline_median_tts",
"hour",
"weekday",
"is_weekend",
"stop_id",
"line_id",
"direction",
"platform_name",
"destination_name",
...
]

```

Important:

- Feature order must not change
- Feature names must match exactly

The inference layer will generate these features live.

---

## 3. Columns Removed During EDA

Dataset originally had 18 columns.

After EDA the following columns were removed:

- deviation_from_baseline
- roll_std_tts_10m

Final model is expected to use:

```

16 columns

```

Please confirm the final feature set.

---

## 4. Preprocessing Used During Training

Please specify preprocessing steps used before training.

Examples:

- StandardScaler
- MinMaxScaler
- OneHotEncoder
- LabelEncoder
- ColumnTransformer
- Pipeline

Important questions:

- Was scaling used?
- Were categorical features encoded?
- Was a sklearn Pipeline used?

The inference system must reproduce the same preprocessing.

---

## 5. Model Output Type

Please specify how predictions should be obtained.

Options:

```

model.predict()
model.predict_proba()

```

The inference layer requires probability output.

Preferred:

```

predict_proba()

```

We need probability to compute risk levels.

---

## 6. Classification Threshold

Please provide the threshold used to classify late vs not late.

Example:

```

threshold = 0.5

```

or

```

threshold = 0.6

```

This will be used in the Risk Interpretation Layer.

---

## 7. Model Type

Please specify final selected model:

- Logistic Regression
- Random Forest
- Gradient Boosting
- XGBoost
- Other

This is needed for explanation compatibility.

---

## 8. SHAP Compatibility

Please confirm if the model supports SHAP.

Supported:

- XGBoost
- RandomForest
- GradientBoosting
- LogisticRegression

Needed for Explanation Layer.

---

## 9. Feature Importance

Please provide feature importance if available.

Examples:

- model.feature_importances_
- SHAP summary
- coefficient table

This will be used in explanation UI.

---

## 10. Calibration (Optional)

If probability calibration was used, please provide:

- calibration method
- calibrated model

Example:

- Platt scaling
- Isotonic regression

Needed for correct risk interpretation.

---

## 11. Dataset Version Used for Training

Please confirm:

- dataset file name
- dataset version
- baseline table version

This must match the inference pipeline.

---

## 12. Expected Inference Input Format

Please confirm the model expects input as:

```

pandas DataFrame
numpy array
sklearn pipeline input

```

Inference layer will build features accordingly.

---

## 13. Expected Output Format

Expected output should allow:

```

probability of late

```

Example:

```

0.82

```

This will be converted into:

- low risk
- medium risk
- high risk

---

## 14. Contact

Inference / API / AI layer depends on this contract.

Any change in features or preprocessing must be communicated.
