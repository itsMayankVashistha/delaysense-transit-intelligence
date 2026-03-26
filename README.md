# 🚇 TfL Delay Intelligence  
## Real-Time Tube Delay Early Warning System

A forecasting-based machine learning system for monitoring London Underground arrival predictions and identifying short-term delay risk in real time.

This capstone project uses live Transport for London (TfL) arrival data, builds a historical dataset from repeated API snapshots, engineers time-aware features, trains forecasting-style ML models, and serves predictions through a FastAPI backend and Streamlit dashboard.

---

## 📌 Project Summary

This project focuses on **London Underground arrival prediction monitoring** for the **Victoria** and **Jubilee** lines.

Instead of predicting whether a train is currently delayed using present-state features, the system uses a **forecasting-style early warning setup**:

> At time **t**, predict whether the arrival context will be delayed at time **t + H**

For example:

- at **23:05**, predict whether the train context will be late at **23:10**

This makes the project an **early warning system**, not a naive current-state classifier.

The system now supports:

- live TfL arrival fetching
- baseline-aware feature generation
- rolling-window live feature updates
- trained ML model integration via `.joblib`
- FastAPI prediction endpoints
- Streamlit monitoring dashboard
- optional intelligence / historical-context layer

---

## 🎯 Current Scope

### Transport mode
- London Underground (Tube)

### Lines
- Victoria
- Jubilee

### Core capabilities
- collect live TfL arrival prediction snapshots
- store raw data in SQLite
- build a processed historical dataset in Parquet
- engineer spatiotemporal and rolling features
- generate future forecasting targets
- train time-aware ML models
- serve predictions through FastAPI
- visualize monitored arrivals in Streamlit
- support both sample demo mode and live TfL mode

---

## 🧠 Problem Framing

### What one row represents

A row in the dataset is **not** a train, trip, or event.

Each row is:

> **one API snapshot of one arrival prediction at poll time**

So the dataset contains:

- repeated rows for the same vehicle over time
- repeated prediction sequences
- many snapshots for the same arrival context

This distinction is critical to understanding both the dataset and the modeling approach.

---

## ❌ Old Approach We Moved Away From

An earlier formulation tried to predict whether an arrival was currently late at the same timestamp.

That approach was weak because present-state features were too closely linked to the label. In particular:

- `deviation_from_baseline` is directly tied to `time_to_station`
- rolling features can leak present-state information
- the model can end up reconstructing the current rule rather than forecasting future delay risk

This is **not** the final framing of the project.

---

## ✅ Current Approach: Forecasting / Early Warning (Path B)

The project now uses a **future-horizon forecasting setup**.

At time **t**, the system predicts whether the same arrival context will be delayed at time **t + H**.

Example target horizons include:

- `future_late_3min_120s`
- `future_late_3min_300s`
- `future_late_3min_1800s`

The current preferred deployment horizon is:

- **300 seconds (5 minutes)**

This framing makes the system useful as an operational early warning product rather than a present-state detector.

---

## 🧱 Data Pipeline Overview

### 1. Live ingestion
- TfL Arrivals API polled approximately every 30 seconds
- raw prediction snapshots stored in SQLite

### 2. Dataset construction
- raw snapshots converted into a processed Parquet dataset
- contextual and rolling features engineered
- future labels generated for forecasting horizons

### 3. Model training
- time-aware train / validation / test split
- multiple models trained and evaluated
- artifact packaging for deployment

### 4. Inference & monitoring
- FastAPI backend loads trained joblib artifacts
- Streamlit dashboard displays monitored arrivals
- optional intelligence layer provides extra context

---

## 🏗 Current Architecture

### Backend
- **FastAPI**
- prediction endpoints
- live monitoring endpoint
- artifact-aware model loading
- optional intelligence layer

### Frontend
- **Streamlit dashboard**
- monitoring overview
- selected-arrival inspection
- delay likelihood charts
- sample demo mode + live TfL mode

### ML / inference services
- baseline lookup service
- rolling cache
- feature pipeline
- inference service
- model artifact loader
- optional intelligence layer

---

## 📂 Project Structure

```text
capstone_project/
│
├── app/
│   ├── api/
│   │   └── main.py
│   ├── config/
│   │   └── settings.py
│   ├── models/
│   │   └── *.joblib
│   ├── services/
│   │   ├── artifact_loader.py
│   │   ├── baseline_service.py
│   │   ├── feature_pipeline.py
│   │   ├── inference_service.py
│   │   ├── mock_model.py
│   │   ├── rolling_cache.py
│   │   ├── tfl_api_service.py
│   │   └── intelligence_layer.py   # optional
│   ├── ui/
│   │   └── assets/
│   └── bootstrap.py
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── data.parquet
│
├── scripts/
│   ├── fetch_stations.py
│   ├── collect_arrivals.py
│   ├── backup_sqlite.py
│   ├── check_db.py
│   └── build_dataset.py
│
├── modeling/
│   ├── train.py
│   ├── predict.py
│   ├── feature_engineering.py
│   ├── config.py
│   └── validate_model_artifact.py
│
├── notebooks/
├── requirements.txt
├── README.md
└── .env
````

---

## 📊 Dataset and Feature Logic

### Example raw / engineered columns

* `observed_at`
* `stop_id`
* `stop_name`
* `line_id`
* `vehicle_id`
* `direction`
* `platform_name`
* `destination_name`
* `hour`
* `weekday`
* `is_weekend`
* `time_to_station`
* `roll_mean_tts_10m`
* `roll_max_tts_10m`
* `roll_count_10m`
* `baseline_median_tts`
* `deviation_from_baseline`
* `late`
* `late_3min`

### Current deployed feature contract

The current inference layer expects the following model feature set:

* `hour`
* `weekday`
* `is_weekend`
* `time_to_station`
* `roll_mean_tts_10m`
* `roll_max_tts_10m`
* `roll_count_10m`
* `baseline_median_tts`
* `deviation_from_baseline`

---

## 🔀 Run Segmentation and Future Labels

Because API snapshots are continuous over time, separate prediction runs are identified using grouped contexts such as:

* `vehicle_id`
* `stop_id`
* `direction`
* `destination_name`

A new run is created when the time gap exceeds 300 seconds.

Future labels are then created by matching each row to a future row within the same run using a time-shifted lookup approach.

This allows targets such as:

* “will this arrival context be late 5 minutes from now?”

---

## ⏱ Time-Aware Validation

The project does **not** use random train/test splitting.

Instead, it uses a **chronological split**:

* train: earliest 70%
* validation: next 15%
* test: final 15%

This is essential for realistic evaluation in time-dependent data.

---

## 🤖 Models Used

Models explored include:

* Logistic Regression
* Random Forest
* LightGBM
* XGBoost artifacts received for deployment comparison

The current deployment setup supports loading packaged model artifacts with metadata and feature contract information.

The currently integrated real-model path uses a **LightGBM-based 300-second horizon artifact**.

---

## 🧾 Model Artifact Handoff

The deployment layer supports model artifacts that include:

* `.joblib` model package
* metadata
* feature list / feature contract
* horizon information
* threshold information
* positive class index
* input type (DataFrame vs array)
* validation compatibility checks

A validation script is used before deployment integration:

```bash
python .\modeling\validate_model_artifact.py .\app\models\lightgbm_v2_h300_balanced.joblib
```

---

## 🌐 API Endpoints

Current backend endpoints include:

### Health check

```http
GET /health
```

### Single sample prediction

```http
GET /sample
```

### Predict one arrival row

```http
POST /predict
```

### Live TfL monitoring

```http
GET /monitor/live
POST /monitor/live
```

The live monitoring route fetches real TfL arrivals, normalizes them into the project schema, and returns model predictions for monitored stations.

---

## 🖥 Streamlit Dashboard

The dashboard supports:

* monitoring overview table
* risk-based arrival inspection
* delay likelihood visualization
* current vs usual arrival comparison
* advanced technical details
* **Sample demo mode**
* **Live TfL mode**

This makes the project usable both as:

* a stable presentation demo
* a real live-data monitoring prototype

---

## ⚙️ Setup Instructions

## Clone the repository

```bash
git clone <your-repo-url>
cd capstone_project
```

---

## `macOS / Linux`

Install the virtual environment and the required packages by following commands:

```bash
pyenv local 3.11.3
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## `WindowsOS`

Install the virtual environment and the required packages by following commands.

### For `PowerShell` CLI

```powershell
pyenv local 3.11.3
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### For `Git-bash` CLI

```bash
pyenv local 3.11.3
python -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🔑 Environment Variables

Create a `.env` file in the project root as needed.

Typical variables may include:

```env
TFL_APP_ID=your_app_id
TFL_APP_KEY=your_app_key
DB_PATH=data/raw/tfl_arrivals.sqlite
POLL_SECONDS=30
```

Do **not** commit `.env` to version control.

---

## 📡 Data Collection

### Fetch selected stations

```bash
python scripts/fetch_stations.py
```

### Start live arrival collection

```bash
python scripts/collect_arrivals.py
```

This stores raw arrival snapshots in SQLite.

---

## 🛠 Build the Processed Dataset

```bash
python scripts/build_dataset.py
```

This step converts raw snapshot data into a processed modeling dataset with engineered features and forecasting targets.

---

## 🧪 Run the API

```bash
python -m uvicorn app.api.main:app --reload
```

Then open:

* `http://127.0.0.1:8000/health`
* `http://127.0.0.1:8000/sample`
* `http://127.0.0.1:8000/monitor/live`

---

## 📊 Run the Streamlit Dashboard

```bash
streamlit run app/ui/streamlit_app.py
```

---

## 🚀 Project Highlights

This project demonstrates:

* real-time API data ingestion
* time-aware ML feature engineering
* forecasting-style label design
* realistic chronological evaluation
* model artifact validation and handoff
* backend deployment with FastAPI
* frontend monitoring with Streamlit
* live data + fallback demo mode
* end-to-end productization of an ML system

---

## ⚠️ Notes

* raw SQLite data is large and should not be committed
* `.env` should remain ignored
* live TfL API availability can vary
* rolling live features improve as the in-memory cache receives more arrivals
* sample mode should be kept for presentation safety

---

## 👥 Authors

* Mayank Vashistha
* Peter Furtado
* Killian Schmiers

