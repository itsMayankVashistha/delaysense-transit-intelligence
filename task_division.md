#  Current Project Stage

Our project has already completed:

✔ Real-time TfL API ingestion
✔ SQLite storage
✔ Safe backup pipeline
✔ Dataset builder pipeline
✔ Feature engineering (rolling windows + baseline)
✔ Processed dataset creation
✔ Initial EDA started

Current stage:

```text
EDA → Modeling → AI Layer → Deployment → Demo
```

![Project workflow](images/workflow.png "workflow")

---

#  Recommended Task Division (3 People)

## Person 1 — ML / Modeling Lead

Responsible for **building the best model**.

### Tasks

**Modeling**

* Logistic Regression
* Random Forest
* Gradient Boosting
* XGBoost

**Evaluation**

* PR-AUC
* ROC-AUC
* Precision / Recall
* Confusion matrix

**Feature analysis**

* feature importance
* station-level performance

**Model selection**

* choose final model
* export trained model

### Deliverables

* trained model
* evaluation notebook
* model comparison
* final model artifact

---

## Person 2 — Visualization & Insights Lead

Responsible for **EDA and data storytelling**.

### Tasks

**EDA expansion**

* station delay patterns
* line comparisons
* hourly delay patterns
* rolling window behavior

**Insight extraction**

* identify high-risk stations
* identify peak delay periods
* identify anomaly patterns

**Visualization**

* charts for presentation
* station delay plots
* temporal delay trends

### Deliverables

* full EDA notebook
* presentation plots
* insight report

---

## Person 3 — AI Layer + Deployment Lead

Here we will build the **intelligence interface and final product layer**.

### Your responsibilities

**AI layer**

* Define risk levels (low/medium/high)
* Model explanation layer
* SHAP feature explanations
* “Why is this station risky?” explanation system

**Deployment**

* Model loading
* Real-time inference pipeline
* FastAPI service (optional but strong)
* Streamlit dashboard

**System integration**

* connect model → inference → UI

### Deliverables

* real-time risk scoring system
* explanation layer
* dashboard demo
* final product


---

# Collaboration Responsibilities

All three should share:

* architecture decisions
* Git workflow
* demo preparation
* final presentation

---


#  Final Project Architecture

Your system should look like this:

```
TfL API
   ↓
Collector Script
   ↓
SQLite Database
   ↓
Dataset Builder
   ↓
Feature Engineered Dataset
   ↓
ML Models
   ↓
Risk Scoring Layer
   ↓
AI Explanation Layer
   ↓
Dashboard / API
```


