# Capstone-project

# 🚇 Urban Transit Delay Intelligence System

## 📌 Project Overview

This project builds a **real-time transit delay intelligence system** using open data from the London Transport for London (TfL) API.

The goal is to:

* Collect live Tube arrival predictions
* Construct a historical dataset from real-time data
* Engineer spatiotemporal features
* Train a time-aware machine learning model to predict short-term delay risk
* Extend the system with an AI-based explanation layer (RAG)

Currently, the project is in the **data ingestion phase**, collecting real-time arrival predictions for selected Tube lines.

---

# 🎯 Current Scope (Phase 1 – Data Ingestion)

* Mode: **London Underground (Tube)**
* Lines: **Victoria & Jubilee**
* Polling interval: **Every 30 seconds**
* Storage: **SQLite database**
* Output file: `data/raw/tfl_arrivals.sqlite`

The system continuously collects arrival prediction snapshots for each station on the selected lines.

---

# 🏗 Project Structure

```
capstone-project_KMP/
│
├── scripts/
│   ├── fetch_stations.py
│   ├── collect_arrivals.py
│   ├── check_db.py
│
├── data/
│   ├── raw/
│   │   ├── stations.csv
│   │   ├── tfl_arrivals.sqlite
│   ├── processed/
│
├── notebooks/
├── src/
├── requirements.txt
├── .env (NOT committed)
└── README.md
```

---

# ⚙️ Setup Instructions

## 1️⃣ Clone Repository

```bash
git clone <your-repo-url>
cd capstone_project
```

---

## 2️⃣ Create Virtual Environment

```bash
python -m venv .venv
```

Activate:

**Windows:**

```bash
.\.venv\Scripts\Activate.ps1
```

---

## 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

If `requirements.txt` is missing:

```bash
pip install requests pandas python-dotenv tqdm
pip freeze > requirements.txt
```

---

# 🔑 TfL API Setup

1. Register at:
   [https://api-portal.tfl.gov.uk/](https://api-portal.tfl.gov.uk/)

2. Go to your profile → copy your **Primary Key**

3. Create a `.env` file in the project root:

```env
TFL_APP_KEY=your_primary_key_here
DB_PATH=data/raw/tfl_arrivals.sqlite
POLL_SECONDS=30
```

⚠️ `.env` must NOT be committed to Git.

---

# 🚦 Step 1 – Fetch Stations

This retrieves all stations for the selected lines.

```bash
python scripts/fetch_stations.py
```

This creates:

```
data/raw/stations.csv
```

---

# 📡 Step 2 – Start Real-Time Data Collection

```bash
python scripts/collect_arrivals.py
```

This will:

* Poll all Victoria & Jubilee stations
* Query TfL API every 30 seconds
* Append prediction records into:

```
data/raw/tfl_arrivals.sqlite
```

Stop with:

```
CTRL + C
```

---

# 🗄 Database Schema

Table: `raw_arrivals`

Each row represents one arrival prediction snapshot:

* observed_at
* stop_id
* stop_name
* line_id
* direction
* platform_name
* destination_name
* time_to_station
* expected_arrival
* vehicle_id
* raw_json

---

# 🧠 Upcoming Phases

## Phase 2 – Dataset Construction

* Clean prediction snapshots
* Build event-level dataset
* Engineer time-based and rolling features
* Define “late vs baseline” classification label

## Phase 3 – Machine Learning

* Time-aware train/test split
* Baseline logistic regression
* Gradient boosting classifier
* Precision/Recall & PR-AUC evaluation

## Phase 4 – AI Explanation Layer

* Build historical pattern summaries
* Vector embeddings (RAG)
* LLM-generated grounded explanations
* API endpoints for prediction + explanation

## Phase 5 – Deployment

* FastAPI backend
* Streamlit dashboard
* Real-time interactive demo

---

# 📊 Impact of the project

This system demonstrates:

* Real-time API ingestion
* Time-aware ML validation
* Spatiotemporal feature engineering
* Production-ready architecture
* Retrieval-Augmented AI reasoning
* End-to-end ML + AI deployment

This is not a static project — it is a live operational ML system.

---

# 🔒 Notes

* SQLite file is not committed (large + raw data).
* `.env` file is ignored.
* API limit: 500 requests/min (current usage ~84/min).

---

# 👤 Author
Peter Furtado

Killian Schmiers

Mayank Vashistha

---

