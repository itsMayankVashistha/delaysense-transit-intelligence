---
title: "TfL Delay Intelligence System: Architecture & Implementation Guide"
author: "Killian, Peter, Mayank"
date: "2026-03-01"
keywords: "TfL, delay prediction, machine learning, time series, real-time system"
---

# TfL Delay Intelligence System: Architecture & Implementation Guide

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Overview](#system-overview)
3. [Architecture Flow](#architecture-flow)
4. [Technical Implementation](#technical-implementation)
5. [Data Dictionary](#data-dictionary)
6. [Machine Learning Approach](#machine-learning-approach)
7. [Implementation Roadmap](#implementation-roadmap)

---

## Executive Summary

The **TfL Delay Intelligence System** is a real-time machine learning platform that predicts unusual train delays on London's Victoria and Jubilee lines. By continuously monitoring TfL API data and applying feature-based time-aware ML using rolling-window statistics and seasonal baselines, the system provides actionable delay probability predictions to improve passenger experience and operational efficiency.

> **Key Innovation**: Event-level time-aware classification that learns from historical patterns to predict abnormal delays in real-time.

### Business Value

- **Proactive Passenger Communication**: Alert passengers before delays become critical
- **Operational Optimization**: Enable preemptive resource allocation during high-risk periods
- **Data-Driven Insights**: Transform raw transit data into actionable intelligence

---

## System Overview

### Core Concept

The system operates on a simple yet powerful principle:

> **Predict whether a train arrival is unusually late compared to normal behavior patterns.**

### Three-Layer Architecture

| Layer | Purpose | Technology |
|-------|---------|------------|
| **Data Collection** | Continuous TfL API monitoring | SQLite, REST APIs |
| **Feature Engineering** | Transform raw data into ML features | Python, Pandas |
| **Prediction Engine** | Real-time delay probability scoring | Scikit-learn, Time-series ML |

### Unit of Observation (Critical Understanding)

> Each dataset row represents one **arrival prediction snapshot record** observed at poll time (`observed_at`). It is not necessarily a unique train trip. Multiple predictions for the same vehicle/arrival may appear across time as TfL updates estimates.

This matters for interpreting `roll_count_10m` (which can be large due to repeated polling).

### Key Differentiators

- **Real-time Processing**: 30-second data collection intervals
- **Historical Context**: Baseline comparison using seasonal patterns
- **Time-aware Features**: Rolling windows and temporal dependencies
- **Production-ready**: Scalable architecture with proper data management

---

## Architecture Flow

### 1) Offline Pipeline Flowchart (Data → Features → Dataset → Model)

```
                ┌──────────────────────────────────────────┐
                │ TfL StopPoint Arrivals API               │
                │ (Victoria + Jubilee, every 30 seconds)   │
                └──────────────────────────────────────────┘
                                  │
                                  ▼
                ┌──────────────────────────────────────────┐
                │ Collector (Python)                        │
                │ - polls API                               │
                │ - parses fields                           │
                │ - writes rows                             │
                └──────────────────────────────────────────┘
                                  │
                                  ▼
                ┌──────────────────────────────────────────┐
                │ SQLite: data/raw/tfl_arrivals.sqlite       │
                │ Table: raw_arrivals                        │
                │ (observed_at, stop_id, line_id, ... raw_json)│
                └──────────────────────────────────────────┘
                                  │
                                  ▼
                ┌──────────────────────────────────────────┐
                │ Safe snapshot backup (Python)              │
                │ sqlite3.Connection.backup() + retries       │
                │ -> data/raw/tfl_arrivals_backup_safe.sqlite │
                └──────────────────────────────────────────┘
                                  │
                                  ▼
                ┌──────────────────────────────────────────┐
                │ Dataset Builder (Python)                   │
                │ Reads ONLY snapshot DB                     │
                │ 1) DEV slice by observed_at cutoff         │
                │ 2) Parse types / clean                      │
                │ 3) Rolling features (10min) per             │
                │    (stop_id, line_id, direction)            │
                │ 4) Baseline median per                      │
                │    (stop_id, line_id, direction, hour, weekday)│
                │ 5) deviation = tts - baseline               │
                │ 6) label late = deviation > 300s            │
                └──────────────────────────────────────────┘
                          │                     │
                          │                     │
                          ▼                     ▼
     ┌──────────────────────────────┐   ┌──────────────────────────────┐
     │ Parquet ML dataset            │   │ Parquet baseline lookup table │
     │ data/processed/dataset_*.parquet │ │ data/processed/baseline_table_*.parquet │
     └──────────────────────────────┘   └──────────────────────────────┘
                          │
                          ▼
                ┌──────────────────────────────────────────┐
                │ Model Training (time-aware split)         │
                │ - train on past, test on future           │
                │ - metrics: PR-AUC, ROC-AUC, calibration   │
                │ - save model artifact                      │
                └──────────────────────────────────────────┘
                                  │
                                  ▼
                ┌──────────────────────────────────────────┐
                │ Saved model file (joblib)                  │
                └──────────────────────────────────────────┘
```

### 2) Online Inference Flowchart (Live API → Features → Model → Output)

```
           ┌────────────────────────────────────────┐
           │ User opens Streamlit / calls API endpoint│
           └────────────────────────────────────────┘
                          │
                          ▼
           ┌────────────────────────────────────────┐
           │ On-demand live TfL API call              │
           │ (same StopPoint Arrivals endpoint)       │
           └────────────────────────────────────────┘
                          │
                          ▼
           ┌────────────────────────────────────────┐
           │ Build "snapshot" rows                   │
           │ Extract fields: stop_id, line_id, ...   │
           │ time_to_station, observed_at            │
           └────────────────────────────────────────┘
                          │
          ┌───────────────┴─────────────────┐
          │                                 │
          ▼                                 ▼
┌──────────────────────────┐    ┌──────────────────────────┐
│ Rolling feature cache      │    │ Baseline lookup table     │
│ (in-memory, last 10 min)   │    │ baseline_table_*.parquet  │
│ keyed by (stop,line,dir)   │    │ key: (stop,line,dir,hour,weekday) │
└──────────────────────────┘    └──────────────────────────┘
          │                                 │
          └───────────────┬─────────────────┘
                          ▼
           ┌────────────────────────────────────────┐
           │ Assemble model feature vector X_t        │
           │ (time_to_station + rolling + time + cats│
           │ + optional baseline/deviation)           │
           └────────────────────────────────────────┘
                          │
                          ▼
           ┌────────────────────────────────────────┐
           │ Load trained model (joblib)              │
           │ Predict p(late=1 | X_t)                  │
           └────────────────────────────────────────┘
                          │
                          ▼
           ┌────────────────────────────────────────┐
           │ Output                                 │
           │ - probability of abnormal delay         │
           │ - (optional) explanation layer later    │
           └────────────────────────────────────────┘
```

### AI Intelligence Layers (Current & Future)

**Layer 1 (Current)**: ML classifier that outputs probability of "late"

**Layer 2 (Soon)**: Threshold tuning + calibration ("risk levels" low/med/high)

**Layer 3 (Later)**: Explainability (feature contributions, SHAP)

**Layer 4 (Optional)**: "Reason" text using retrieved historical patterns (RAG-ish)

### Operational Workflow

#### Phase 1: Data Collection
- **Frequency**: Every 30 seconds
- **Source**: TfL StopPoint Arrivals API
- **Coverage**: Victoria + Jubilee lines
- **Storage**: Raw SQLite database with backup snapshots

#### Phase 2: Feature Engineering
- **Current State**: Real-time arrival predictions
- **Short-term Memory**: 10-minute rolling statistics
- **Historical Context**: Baseline medians by station/time/day
- **Output**: Structured feature vectors for ML

#### Phase 3: Model Training
- **Approach**: Time-aware supervised classification
- **Target**: Binary delay labels (>5 minutes vs normal)
- **Validation**: Chronological train/test split
- **Output**: Serialized model artifact

#### Phase 4: Real-time Inference
- **Input**: Live TfL API call
- **Processing**: Feature generation + baseline lookup
- **Output**: Delay probability score (0.0 - 1.0)

---

## Technical Implementation

### Data Collection Strategy

**API Integration**
```python
# Pseudo-code for data collection
def collect_arrivals():
    response = tfl_api.get_arrivals(['victoria', 'jubilee'])
    for arrival in response:
        store_raw_data(arrival, timestamp=now())
    schedule_next_collection(delay=30)
```

### SQLite Operational Safety

Critical engineering constraints and solutions:

- **Live DB Protection**: Collector writes to live DB (WAL mode recommended)
- **Safe Snapshots**: Use `sqlite3.Connection.backup()` to create read-only snapshots
- **Dataset Builder**: Always reads from snapshot DB, never from live DB
- **Corruption Prevention**: Never copy live DB file manually - prevents locks/corruption
- **Concurrency**: Collector configured with proper timeout and WAL mode for safe concurrent access

> **Key Learning**: SQLite corruption occurred from copying while live. This architecture prevents lock errors and ensures data integrity.

**Data Storage Schema**
- **Raw Storage**: Complete API responses with timestamps
- **Backup Strategy**: Automated snapshots using Connection.backup() with retries
- **Query Optimization**: Indexed by station, line, and timestamp

### Feature Engineering Pipeline

#### Time-based Features
- `hour`: Hour of day (0-23) for circadian patterns
- `weekday`: Day of week (0-6) for weekly seasonality
- `is_weekend`: Binary flag for weekend behavior

#### Rolling Statistics (10-minute windows)
- `roll_mean_tts_10m`: Average arrival time in recent window
- `roll_max_tts_10m`: Maximum delay observed recently
- `roll_count_10m`: Activity level indicator
- `roll_std_tts_10m`: Variability measure

#### Baseline Comparison
- `baseline_median_tts`: Historical normal for (station, line, direction, hour, weekday)
- `deviation_from_baseline`: Current vs. expected performance

### Inference-Time Feature Generation Strategy

**Rolling Features Cache:**
- Maintain in-memory cache keyed by (stop_id, line_id, direction)
- Store last 10 minutes of `time_to_station` observations
- Compute rolling statistics (mean, max, count) from cache
- Cache updated with each new API call

**Baseline Lookup:**
- Query stored `baseline_table_dev.parquet` for median values
- Handle missing buckets using fallback hierarchy
- No real-time computation of baselines required

### Machine Learning Formulation

**Mathematical Framework**

Let:
- `Y_t` = delay label at time t
- `X_t` = feature vector at time t

**Feature Vector Structure:**
```
X_t = {
    time_to_station_t,
    roll_mean_{t-10:t},
    roll_max_{t-10:t},
    roll_count_{t-10:t},
    baseline(station, line, direction, hour, weekday),
    hour, weekday, station_id, ...
}
```

**Target Definition:**
```
Y_t = 1 if (deviation_from_baseline > 300 seconds) else 0
```

**Model Objective:**
```
P(Y_t = 1 | X_t) = Probability of abnormal delay given current system state
```

This represents **event-level time-aware classification**, not traditional forecasting.

---

## Data Dictionary

### Raw Identifiers

| Field | Type | Description |
|-------|------|-------------|
| `observed_at` | Timestamp | UTC timestamp when API was polled |
| `stop_id` | String | Unique TfL station identifier |
| `stop_name` | String | Human-readable station name |
| `line_id` | String | Tube line identifier (victoria, jubilee) |
| `direction` | String | Train direction (inbound, outbound, unknown) |
| `platform_name` | String | Platform identifier within station |
| `destination_name` | String | Final destination of train |

### Engineered Features

#### Core Signal
| Field | Type | Description |
|-------|------|-------------|
| `time_to_station` | Integer | Seconds until train reaches station (from TfL prediction) |

#### Temporal Context
| Field | Type | Description |
|-------|------|-------------|
| `hour` | Integer | Hour of day (0–23) |
| `weekday` | Integer | Day of week (0=Monday, 6=Sunday) |
| `is_weekend` | Boolean | 1 if Saturday/Sunday, else 0 |

#### Rolling Statistics (10-minute window per stop/line/direction)
| Field | Type | Description |
|-------|------|-------------|
| `roll_mean_tts_10m` | Float | Mean time_to_station in last 10 minutes |
| `roll_max_tts_10m` | Integer | Maximum time_to_station in last 10 minutes |
| `roll_count_10m` | Integer | Number of observations in last 10 minutes |
| `roll_std_tts_10m` | Float | Standard deviation of time_to_station (optional) |

#### Baseline Comparison
| Field | Type | Description |
|-------|------|-------------|
| `baseline_median_tts` | Float | Median time_to_station for (stop_id, line_id, direction, hour, weekday) |
| `deviation_from_baseline` | Float | time_to_station - baseline_median_tts |

> **Interpretation**: Positive deviation = slower than usual, Negative = faster than usual

#### Baseline Artifacts & Leakage Prevention

**Two Key Artifacts:**
- `dataset_dev.parquet` = training rows with features + labels
- `baseline_table_dev.parquet` = lookup table used in both training and inference

**Missing Baseline Fallback Strategy (Planned improvement):**
When a baseline bucket is missing (especially in DEV windows):
1. Fallback to (stop, line, direction, hour) - dropping weekday
2. Fallback to (stop, line, direction) - dropping time specificity  
3. Fallback to global median per line

**Leakage-Safe Evaluation:**
- Baseline medians computed from **training window only**
- Applied to validation/test data without recomputation
- Prevents subtle data leakage in offline evaluation

#### Target Variable
| Field | Type | Description |
|-------|------|-------------|
| `late` | Boolean | 1 if deviation_from_baseline > 300 seconds, 0 otherwise |

### Data Volume & Scaling Constraints

**Growth Patterns:**
- **~7 GB/day** raw data growth rate
- **~22 GB** accumulated after ~3 days of collection
- Justifies development using DEV windows: 6h → 12h → 24h → 48h → full 7 days

**Engineering Implications:**
- Parquet format used for efficient columnar ML processing
- Incremental build strategy required for larger datasets
- Backup and snapshot procedures critical for data management

### Data Quality Notes

⚠️ **Critical Considerations**:
- Dataset requires **chronological splitting** for time-series validation
- Rolling features introduce **short-term memory** dependencies
- `deviation_from_baseline` is directly related to target label - use carefully to avoid data leakage
- Baseline median removes **structural time-of-day effects**

---

## Machine Learning Approach

### Model Learning Scenarios

#### Scenario 1: With Baseline Deviation
If `deviation_from_baseline` is included as a feature:
- Model learns threshold logic: `late = 1(deviation > 300)`
- Strong baseline performance but limited learning depth
- Risk of overfitting to the engineered feature

#### Scenario 2: Without Baseline Deviation
Model must discover patterns from raw signals:
- **Rolling Statistics**: When mean increases or max spikes
- **Station Patterns**: Location-specific behavior differences  
- **Temporal Patterns**: Hour and weekday risk variations
- **Interaction Effects**: Complex multi-feature relationships

> **Recommendation**: Start with Scenario 1 for baseline, then explore Scenario 2 for deeper insights.

### Time Series Methodology

**Core Time Series Concepts Applied:**

1. **Temporal Ordering**: Chronological data sorting by `observed_at`
2. **Rolling Windows**: Short-term memory via 10-minute statistics
3. **Seasonal Baselines**: Hour + weekday conditioning
4. **Time-aware Validation**: Training on past, testing on future

**What We're NOT Doing (Not now):**
- ❌ ARIMA modeling
- ❌ LSTM neural networks  
- ❌ Prophet forecasting

**What We ARE Doing:**
- ✅ **Feature-based supervised time-series modeling**
- ✅ Industry-standard approach for real-time classification
- ✅ Scalable and interpretable methodology

### Model Validation Strategy

```
Training Data:    [Days 1-5] (chronological)
                           │
Validation Data:          [Day 6]
                            │
Test Data:                [Day 7]
```

**Key Principles:**
- **Chronological Split**: 7-day rolling window with time-aware validation
- **Baseline Integrity**: Baseline medians computed on training data only, applied to validation/test
- **No Data Leakage**: Future information never used for past predictions
- **Short Training Horizon**: ~7 days of data (not months/years) - affects baseline stability and generalization

**Note**: Why we chose classification instead of regression: "We model delay as a binary classification problem (late vs not late) rather than predicting exact delay seconds because classification is more robust, easier to evaluate in limited data horizons (~7 days), and more directly actionable for risk-based decision systems."

---

## Implementation Roadmap

### Week 0-1: Dataset & Baseline Foundation
- [ ] **Data Collection & Safety**
  - Complete TfL API integration with SQLite operational safety
  - Implement Connection.backup() snapshot system
  - Dataset builder reading from snapshots

- [ ] **Feature Engineering & EDA**
  - Rolling statistics computation and validation
  - Baseline median calculation with fallback strategies
  - Exploratory data analysis on DEV windows

- [ ] **Baseline Model**
  - Time-aware chronological split implementation
  - Initial logistic regression model training
  - Evaluation metrics setup (ROC-AUC, PR-AUC, calibration)

### Week 1-2: Model Improvement & Evaluation
- [ ] **Advanced Modeling**
  - Gradient boosting and ensemble methods
  - Feature importance analysis and selection
  - Model calibration and threshold tuning

- [ ] **Robust Evaluation**
  - Cross-validation on multiple time windows
  - Performance analysis across stations and time periods
  - Baseline fallback strategy testing

### Week 2-3: Inference System & Demo
- [ ] **Real-time Inference Endpoint**
  - In-memory cache implementation for rolling features
  - Baseline lookup system integration
  - API endpoint with <200ms response time target (to be validated during integration testing)

- [ ] **Streamlit Demo Application**
  - Interactive delay probability visualization
  - Station-specific risk monitoring dashboard
  - Historical performance analytics

### Week 3-4: Polish & Final Presentation (Target: April 7)
- [ ] **System Documentation & Testing**
  - End-to-end system validation
  - Performance benchmarking and optimization
  - Comprehensive documentation completion

- [ ] **Capstone Presentation Preparation**
  - Demo scenario preparation and testing
  - Results analysis and business impact assessment
  - Final presentation materials and rehearsal

---

## Success Metrics & Measurement Plan

### Technical Performance Metrics (Initial)
**Offline Evaluation:**
- **ROC-AUC**: Area under receiver operating characteristic curve
- **PR-AUC**: Precision-recall area under curve (critical for imbalanced data)
- **Brier Score**: Calibration quality measurement
- **Confusion Matrix**: At chosen probability threshold

**Online Performance:**
- **Inference Latency**: p50/p95 response times (target <200ms)
- **Cache Hit Rate**: Rolling feature cache effectiveness
- **Error Rate**: Missing baseline bucket frequency
- **Data Freshness**: 30-second collection interval maintenance

### Business Impact Measurement
**Descriptive Analytics:**
- **High-Risk Detection**: Number of stations/time periods flagged as high-risk
- **Coverage**: Monitoring across 100% of Victoria + Jubilee line stations
- **Pattern Discovery**: Identification of systematic delay patterns

### Target KPIs (After Initial Iteration)
- **Prediction Performance**: ROC-AUC >0.75, PR-AUC >0.60
- **System Reliability**: >99% uptime during demo periods
- **Scalability**: Architecture ready for additional tube lines

> **Note**: Initial targets are conservative given 7-day training horizon and uncertain class balance. Performance expectations will be refined based on actual data characteristics and baseline model results.

---

## AI & Intelligence Layer (Future Expansion)

### Current Implementation
**Layer 1 — Predictive Model:**
- Logistic Regression / Gradient Boosting for delay probability
- Feature-based time-aware classification

**Layer 2 — Risk Scoring:**
- Threshold tuning based on PR-AUC optimization
- Calibrated probability outputs for decision-making

### Future Extensions
**Layer 3 — Explanation Layer:**
- SHAP-based feature contribution explanations
- Interpretable delay factor identification

**Layer 4 — RAG-style Reasoning (Optional):**
- Integration with external transit disruption data
- Contextual delay explanation generation

---

> **Next Steps**: Begin Week 0-1 implementation with focus on SQLite operational safety and dataset builder foundation. The revised architecture addresses real engineering constraints and provides a solid foundation for the April 7 capstone presentation.

