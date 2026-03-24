# Exploratory Data Analysis (EDA) — Key Findings

## TfL Delay Intelligence System


# 1. Dataset Overview

The dataset was collected from the **Transport for London (TfL) StopPoint Arrivals API** by polling the API every **30 seconds**.

Each record represents a **real-time arrival prediction event**, describing the predicted time for a train to reach a specific station at a particular moment.

Unlike typical datasets that contain completed trips or historical records, this dataset represents a **continuous operational telemetry stream of the transit network**.

### Dataset Size

The final dataset contains:

* **24,043,191 rows**
* **~8 days (192 hours) of data**
* **multiple stations across Victoria and Jubilee lines**
* **engineered temporal and rolling statistical features**

Each row includes:

* timestamp (`observed_at`)
* station identifier
* line and direction
* predicted arrival time (`time_to_station`)
* rolling delay statistics
* contextual time variables
* anomaly label (`late`)

---

# 2. Problem Definition

The goal of the system is **not to forecast exact arrival times**, but to detect **abnormal delay patterns in real time**.

The target variable is defined as:

```
late = 1 if predicted arrival time exceeds historical baseline by ≥ 5 minutes
late = 0 otherwise
```

This transforms the problem into a **time-aware anomaly classification task**, similar to:

* fraud detection
* system anomaly monitoring
* operational alerting systems

---

# 3. Data Collection Integrity

### Event Volume Over Time

The first analysis examined the **event volume collected over time**.

Key observations:

* Event counts follow a clear **daily operational rhythm**.
* Activity increases during daytime transit hours.
* Activity drops during late-night hours.

This confirms that the ingestion pipeline successfully captured **real-world transit activity patterns**.

### Collector Downtime

Several temporary drops in event volume were observed due to interruptions such as system restarts.

Detected gaps:

| Gap Duration | Likely Cause           |
| ------------ | ---------------------- |
| ~420 minutes | system restart         |
| ~220 minutes | collector interruption |
| ~60 minutes  | short interruption     |
| ~10 minutes  | minor gap              |

Total downtime detected:

```
~900 minutes (~7.8% of the collection window)
```

These gaps represent **periods when no events were collected**, not corrupted data.

Because the dataset is event-based:

* missing periods simply contain no rows
* existing rows remain valid

Therefore **no row-level data cleaning was required**.

---

# 4. Target Variable Distribution

The target distribution is:

```
late = 0 → 72.4%
late = 1 → 27.6%
```

Interpretation:

* The dataset is **moderately imbalanced**, but not severely.
* Always predicting "not late" would yield ~72% accuracy.
* Therefore accuracy is not an appropriate evaluation metric.

For this problem, **Precision-Recall AUC** is more appropriate.

---

# 5. Temporal Behavior of Delays

## Late Rate by Hour

The probability of lateness varies across the day.

Observed range:

```
~24% to ~30%
```

Interpretation:

* Time of day influences delay probability.
* However, the effect is moderate.
* Hour-of-day acts as **contextual information**, not the dominant signal.

---

## Late Rate by Day

The daily lateness probability remained extremely stable:

```
~0.270 – 0.279
```

Interpretation:

* The anomaly definition is stable across time.
* There is no significant drift in the dataset.
* This stability is beneficial for training supervised models.

---

# 6. Station-Level Behavior

Transit networks often exhibit **location-specific delay behavior**, so station-level analysis was performed.

### Event Count by Station

The most represented stations contributed approximately:

| Station             | Share of Dataset |
| ------------------- | ---------------- |
| Stratford           | ~4.7%            |
| Green Park          | ~4.6%            |
| Brixton             | ~4.0%            |
| Walthamstow Central | ~3.9%            |
| Stanmore            | ~3.8%            |

Interpretation:

* No station dominates the dataset.
* Sampling across stations is well balanced.
* The model will not become biased toward a small subset of locations.

---

### Late Rate by Station

Significant variation in lateness probability exists across stations.

Stations with higher delay probability include:

* Baker Street
* Bond Street
* St. John’s Wood
* Stratford
* Finchley Road

Stations with lower delay probability include:

* Euston
* Oxford Circus
* King's Cross
* Warren Street

Interpretation:

Station context is an important predictive signal.

This suggests that some locations consistently behave as **congestion points or operational bottlenecks**.

---

# 7. Prediction Volatility by Station

To measure prediction stability, the standard deviation of `time_to_station` was computed for each station.

The most volatile stations exhibit prediction variability around:

```
~500 seconds standard deviation
```

Interpretation:

* Some stations have significantly more volatile predictions.
* This may reflect complex operational dynamics such as:

  * line junctions
  * merging routes
  * passenger congestion

Prediction volatility itself may act as a useful signal for anomaly detection.

---

# 8. Feature Distribution Analysis

## Time to Station

The distribution of `time_to_station` is right-skewed.

This is expected because trains can appear in the API when they are:

* very close to a station
* moderately distant
* far away along the route

The distribution shows no abnormal spikes or corrupted values.

---

## Rolling Mean Delay

The rolling delay feature (`roll_mean_tts_10m`) is concentrated around:

```
~800–900 seconds
```

Interpretation:

This feature captures the **local delay environment around a station**, summarizing recent arrival predictions.

It is likely to be a strong predictive feature for delay anomalies.

---

# 9. Feature Signal Strength

To evaluate predictive signal, the distribution of `roll_mean_tts_10m` was compared for:

```
late = 0
late = 1
```

The resulting density plots show clear separation.

Observations:

* Higher rolling delay levels correspond to higher late probability.
* Normal events occur at lower rolling delay levels.

Interpretation:

Rolling delay features contain **strong predictive information**.

This validates the anomaly detection concept of the project.

---

# 10. Feature Correlation and Leakage Detection

The correlation matrix revealed several expected relationships.

### Rolling Feature Correlations

Rolling delay statistics are strongly correlated with each other.

This is expected because they summarize similar recent delay dynamics.

Tree-based models can handle this correlation effectively.

---

### Target Leakage Detection

The feature:

```
deviation_from_baseline
```

was highly correlated with the target variable.

This is because the label was defined as:

```
deviation_from_baseline = time_to_station − baseline_median_tts
late = 1 if deviation_from_baseline ≥ threshold
```

Including this feature would allow the model to reconstruct the label directly.

Therefore it was removed from the modeling dataset to prevent **target leakage**.

---

# 11. Data Quality Validation

The dataset passed several integrity checks:

* timestamps are monotonic
* duplicate rows = 0
* balanced station sampling
* stable class distribution
* meaningful feature distributions
* target leakage removed

One engineered feature (`roll_std_tts_10m`) contained only missing values and can be excluded from modeling.

---

# 12. Key Insights from EDA

The exploratory analysis reveals several important characteristics of the dataset:

1. Transit delay probability is relatively stable across days.
2. Event volume follows strong daily operational patterns.
3. Station context plays a significant role in delay behavior.
4. Rolling delay statistics capture meaningful local dynamics.
5. No single station dominates the dataset.
6. The dataset contains strong predictive signal for anomaly detection.

---

# 13. Conclusion

The EDA confirms that the dataset is:

* large-scale and realistic
* structurally consistent
* balanced across stations
* temporally stable
* rich in predictive signal

After removing the leakage feature (`deviation_from_baseline`), the dataset is suitable for **training machine learning models for real-time transit delay anomaly detection**.

The next stage of the project will focus on:

* time-aware train/test splitting
* baseline model training
* model evaluation using PR-AUC
* building a real-time inference system.

---

