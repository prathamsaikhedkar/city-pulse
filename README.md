# 🌆 CityPulse — Intelligent Urban Air Quality & Forecasting Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.136.0-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19.2.4-61DAFB.svg?style=flat&logo=react)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-8.0.4-646CFF.svg?style=flat&logo=vite)](https://vitejs.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%2F18-336791.svg?style=flat&logo=postgresql)](https://www.postgresql.org)
[![XGBoost](https://img.shields.io/badge/XGBoost-3.2.0-FF6600.svg?style=flat)](https://xgboost.readthedocs.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**CityPulse** is a modern, full-stack urban environmental dashboard that monitors real-time air quality metrics, tracks atmospheric pollutants, and delivers **24-hour predictive forecasts** using machine learning (XGBoost) across 15 key geographical zones in **Gwalior, Madhya Pradesh, India**.

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [System Architecture & Data Flow](#-system-architecture--data-flow)
- [Monitored Geographic Locations](#-monitored-geographic-locations)
- [Machine Learning Pipeline & AQI Computation](#-machine-learning-pipeline--aqi-computation)
- [Tech Stack](#-tech-stack)
- [Project Directory Structure](#-project-directory-structure)
- [API Reference](#-api-reference)
- [Environment Configuration](#-environment-configuration)
- [Getting Started & Local Setup](#-getting-started--local-setup)
  - [1. Prerequisites](#1-prerequisites)
  - [2. Database Setup](#2-database-setup)
  - [3. Backend Setup](#3-backend-setup)
  - [4. Frontend Setup](#4-frontend-setup)
- [Model Training & Retraining](#-model-training--retraining)
- [Production Deployment](#-production-deployment)
- [License](#-license)

---

## 🌟 Overview

Urban air quality is highly dynamic, influenced by vehicular traffic, industrial activity, geographical topography, and meteorological fluctuations. CityPulse bridges raw sensor streams with predictive analytics, providing city planners, citizens, and researchers with actionable environmental insights.

The platform continuously digests pollutant concentrations ($\text{PM}_{2.5}$, $\text{PM}_{10}$, $\text{NO}_2$, $\text{SO}_2$, $\text{CO}$, $\text{O}_3$, $\text{NO}$) alongside meteorological variables (temperature and relative humidity), stores standardized time-series records in PostgreSQL, computes sub-index air quality standards, and serves live interactive geospatial heatmaps, multi-chart analytical breakdowns, and autoregressive 24-hour predictions.

---

## ✨ Key Features

- **Automated Hourly Ingestion**: Scheduled background cron ingestion (`APScheduler`) querying OpenWeatherMap Air Pollution API and Open-Meteo Historical/Forecast Weather APIs at `:05` past every UTC hour.
- **24-Hour Autoregressive AQI Forecasting**: Time-series inference powered by XGBoost with 24 lag steps, multi-window rolling aggregates (6h & 24h means, 24h standard deviations), and meteorological features.
- **Geographic Sensor Heatmap**: Leaflet.js interactive map with color-coded circular markers displaying AQI severities, temperature, humidity, and location metadata.
- **Multi-Vector Analytics Suite**:
  - 📈 **AQI Trend**: 24-hour historical smoothed timeline.
  - 🎯 **Pollutant Profile**: Polar area snapshot breakdown ($\text{PM}_{2.5}$, $\text{PM}_{10}$, $\text{NO}_2$, $\text{SO}_2$, $\text{O}_3$, $\text{CO}$).
  - 🌡️ **Climatological Matrix**: Dual-axis 48-hour temperature vs. humidity synchronization.
  - 🍩 **AQI Distribution**: 72-hour air quality tier categorizations (*Good*, *Moderate*, *Poor*, *Severe*).
  - 📊 **Trace Gas Stack**: 24-hour stacked bar representation of harmful trace gases.
  - ⏰ **Diurnal Pattern**: 24-hour cyclical hourly mean AQI distribution.
- **Responsive Layout**: Designed with Material-UI v9, featuring sticky navigation, adaptive sensor selectors (horizontal scrolling for mobile, sticky vertical sidebar for desktop), and distinct color palettes.

---

## 🏗️ System Architecture & Data Flow

```
                                  [ EXTERNAL SOURCES ]
                                            │
                  ┌─────────────────────────┴─────────────────────────┐
                  ▼                                                   ▼
       OpenWeatherMap API                                    Open-Meteo API
(PM2.5, PM10, CO, NO, NO2, O3, SO2)                       (Temperature, Humidity)
                  │                                                   │
                  └─────────────────────────┬─────────────────────────┘
                                            │ (HTTP / JSON)
                                            ▼
                           ┌─────────────────────────────────┐
                           │   FASTAPI APPLICATION SERVER    │
                           │                                 │
                           │  • Background Scheduler (:05)   │
                           │  • US EPA AQI Linear Evaluator  │
                           │  • Autoregressive Forecaster    │
                           └────────────────┬────────────────┘
                                            │
                     ┌──────────────────────┴──────────────────────┐
                     ▼                                             ▼
          ┌─────────────────────┐                       ┌─────────────────────┐
          │  POSTGRESQL DB      │                       │  XGBOOST MODEL      │
          │  (Neon Cloud/Local) │                       │  (model2.pkl)       │
          │                     │                       │                     │
          │  • locations        │                       │  • 24 Lags + Stats  │
          │  • air_quality_data │                       │  • Recursive 24-hr  │
          └──────────┬──────────┘                       └──────────┬──────────┘
                     │                                             │
                     └──────────────────────┬──────────────────────┘
                                            │ (REST Endpoints / JSON)
                                            ▼
                           ┌─────────────────────────────────┐
                           │      REACT 19 + VITE FRONTEND   │
                           │                                 │
                           │  • /dashboard (Live Analytics)  │
                           │  • /forecasts (AI Projections)  │
                           │  • Leaflet.js Map + Chart.js    │
                           └─────────────────────────────────┘
```

### Data Pipeline Sequence
1. **Cron Trigger**: At `:05` past each UTC hour, `apscheduler` initiates `fetch_and_store_latest()`.
2. **External Querying**: Iterates across 15 coordinates in Gwalior, rotating across API keys to prevent rate limit bottlenecks.
3. **Data Unification**: Hourly pollution timestamps are synced with concurrent Open-Meteo ambient temperature and relative humidity.
4. **Idempotent Upsert**: Records are committed to PostgreSQL using `ON CONFLICT (time, location_id) DO NOTHING`.
5. **Client Serving**:
   - `/api/history` queries the last 72 hours, computes AQI per row, and returns structured sensor histories.
   - `/api/predict_all` gathers the latest 24 hourly data points per sensor, initializes the autoregressive rolling feature loop, and predicts the next 24 hours.

---

## 📍 Monitored Geographic Locations

The initial MVP covers 15 strategic zones across Gwalior:

| ID | Location Name | Description | Latitude | Longitude |
|:---|:---|:---|:---:|:---:|
| **1** | Gwalior Fort | Historic heart and highest elevation point | 26.2300° N | 78.1691° E |
| **2** | Lashkar | Traditional central business & commercial district | 26.2031° N | 78.1610° E |
| **3** | Gole Ka Mandir | Major transit interchange connecting north outskirts | 26.2465° N | 78.2045° E |
| **4** | Hazira | Industrial sector and dense residential area | 26.2392° N | 78.1795° E |
| **5** | Morar | Bustling eastern wing and former cantonment | 26.2238° N | 78.2255° E |
| **6** | City Centre | Modern administrative and corporate hub | 26.2120° N | 78.1944° E |
| **7** | Thatipur | Prominent residential government sector | 26.2163° N | 78.2098° E |
| **8** | Phool Bagh | Central cultural hub with public parks and shrines | 26.2195° N | 78.1744° E |
| **9** | Dabra | Southern gateway and satellite industrial suburb | 25.8900° N | 78.3300° E |
| **10** | DD Nagar | Planned residential township in the northeast | 26.2580° N | 78.2180° E |
| **11** | Sada (New Gwalior) | Counter-magnet urban development zone to the west | 26.1950° N | 78.0800° E |
| **12** | Kampoo | Historic southern belt housing major hospitals | 26.1965° N | 78.1565° E |
| **13** | Birla Nagar | Railway-centered heavy industrial corridor | 26.2485° N | 78.1885° E |
| **14** | Tansen Nagar | Residential township named after the musician | 26.2355° N | 78.1905° E |
| **15** | Hurawali | Fast-growing eastern residential expansion | 26.2040° N | 78.2320° E |

---

## 🧮 Machine Learning Pipeline & AQI Computation

### 1. AQI Calculation Standard (US EPA)
The Air Quality Index is derived using linear interpolation across concentration breakpoint intervals for $\text{PM}_{2.5}$ and $\text{PM}_{10}$:

$$I = \frac{I_{\text{high}} - I_{\text{low}}}{C_{\text{high}} - C_{\text{low}}} \times (C - C_{\text{low}}) + I_{\text{low}}$$

$$\text{AQI} = \max\left(I_{\text{PM}_{2.5}}, I_{\text{PM}_{10}}\right)$$

#### Breakpoints Table:
| AQI Range | Category | Color Hex | $\text{PM}_{2.5}$ ($\mu\text{g/m}^3$) | $\text{PM}_{10}$ ($\mu\text{g/m}^3$) |
|:---:|:---:|:---:|:---:|:---:|
| **0 – 50** | Good | `#22c55e` | 0.0 – 12.0 | 0 – 54 |
| **51 – 100** | Moderate | `#f59e0b` | 12.1 – 35.4 | 55 – 154 |
| **101 – 150** | Unhealthy for Sensitive | `#ef4444` | 35.5 – 55.4 | 155 – 254 |
| **151 – 200** | Poor / Unhealthy | `#ef4444` | 55.5 – 150.4 | 255 – 354 |
| **201 – 300** | Very Poor | `#a855f7` | 150.5 – 250.4 | 355 – 424 |
| **301 – 500** | Severe / Hazardous | `#a855f7` | 250.5 – 500.4 | 425 – 604 |

### 2. Feature Engineering & Autoregression
The XGBoost regressor (`model2.pkl`) is evaluated on 33 engineered features:
- **Spatial & Temporal**: `location_id`, `hour` (0–23), `day_of_week` (0–6), `month` (1–12).
- **Lag Series**: 24 discrete hourly backward values (`aqi_lag_1` to `aqi_lag_24`).
- **Rolling Window Dynamics**:
  - `aqi_rolling_mean_6h`: 6-hour moving average of AQI.
  - `aqi_rolling_mean_24h`: 24-hour moving average of AQI.
  - `aqi_rolling_std_24h`: 24-hour moving standard deviation (capturing volatility).
- **Ambient Meteorology**: `temperature` (°C), `humidity` (%).

### 3. Autoregressive Inference Loop
To project 24 hours forward:
1. The model takes the last 24 observed hourly AQI records for a sensor.
2. For step $t=1$, the model predicts $\widehat{\text{AQI}}_{t+1}$.
3. $\widehat{\text{AQI}}_{t+1}$ is appended to the lag window, the rolling metrics are recalculated, and the loop advances to predict $t=2 \dots 24$.

---

## 💻 Tech Stack

### Frontend
- **Framework**: React 19 (`react`, `react-dom`)
- **Build Tool**: Vite 8 (Hot Module Replacement, ES modules)
- **Routing**: React Router v7 (`react-router-dom`)
- **UI Components & Styling**: Material UI v9 (`@mui/material`, `@mui/icons-material`, `@emotion/react`, `@emotion/styled`)
- **Geospatial & Charts**: Leaflet 1.9.4 with CartoDB Voyager tiles, Chart.js

### Backend
- **Framework**: Python 3.10+ FastAPI 0.136
- **Server**: Uvicorn (ASGI)
- **Task Scheduling**: APScheduler (Background cron)
- **ORM & Database Drivers**: SQLAlchemy 2.0, Psycopg2-binary
- **Data & ML**: Pandas 3.0, NumPy 2.4, XGBoost 3.2, Scikit-Learn 1.8

### Database & Infrastructure
- **Database**: PostgreSQL 16+ (Local or Serverless via Neon.tech)
- **External APIs**: OpenWeatherMap Air Pollution API, Open-Meteo Weather API

---

## 📁 Project Directory Structure

```text
CityPulseApp/
├── backend/
│   ├── gwl_data.json            # 15 Gwalior sensor coordinate metadata
│   ├── main.py                  # FastAPI app, routes, scheduler & inference
│   ├── model.pkl                # Trained model (NAQI scale)
│   ├── model2.pkl               # Production trained model (US EPA scale)
│   ├── requirements.txt         # Python backend dependencies
│   └── README.md                # Dedicated backend documentation
│
├── frontend/
│   ├── public/                  # Public assets
│   ├── src/
│   │   ├── assets/              # Logos and brand assets
│   │   ├── components/
│   │   │   ├── AQIChart.jsx           # Reusable AQI line chart
│   │   │   ├── CityMap.jsx            # Leaflet map with colored circle markers
│   │   │   ├── DashboardAnalytics.jsx # 6-chart analytical grid (Chart.js)
│   │   │   ├── Layout.jsx             # Navigation bar and header wrapper
│   │   │   ├── LocationSelector.jsx   # Responsive sensor selector radio list
│   │   │   └── MetricCards.jsx        # Metric summary cards
│   │   ├── mockData/
│   │   │   ├── data.json              # Sensor coordinates backup
│   │   │   └── gwaliorData.js         # Sensor coordinates & metadata module
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx          # Live Monitoring view
│   │   │   └── Forecasts.jsx          # 24-hr AI Forecasting view
│   │   ├── api.js               # Frontend API client (fetch wrapper)
│   │   ├── App.css              # Global custom CSS
│   │   ├── App.jsx              # Routing & root component
│   │   ├── index.css            # CSS reset & baseline styling
│   │   ├── main.jsx             # React entry point
│   │   └── theme.js             # MUI custom palette and component overrides
│   ├── .env.local               # Frontend environment variables
│   ├── eslint.config.js         # ESLint configuration
│   ├── index.html               # HTML entry file (loads Leaflet & Chart.js CDN)
│   ├── package.json             # Frontend dependencies & npm scripts
│   ├── vite.config.js           # Vite build configuration
│   └── README.md                # Dedicated frontend documentation
│
├── .env                         # Root environment variables
├── .gitignore                   # Git ignore specifications
├── Application_Flow.txt         # Architectural overview & notes
├── check_db.py                  # Database diagnostics & summary script
├── check_db_status.py           # Quick connection & row counter script
├── database_init.py             # Historical ingestion & backfill script
├── generate_notebook.py         # Helper script generating train.ipynb
├── train.ipynb                  # Jupyter Notebook for EDA & model training
├── train2.py                    # Standalone model training script (EPA scale)
└── README.md                    # Master documentation (this file)
```

---

## 🔌 API Reference

### Base URL: `http://localhost:8000`

### 1. Health Check
- **`GET /health`**
  - **Description**: Returns the operational status of the FastAPI backend.
  - **Response**:
    ```json
    { "status": "ok" }
    ```

---

### 2. Historical Air Quality Readings
- **`GET /api/history`**
  - **Description**: Fetches the past 3 days (72 hours) of hourly pollutant readings for all 15 locations, calculates the US EPA AQI for each record, and filters out erroneous outliers (`aqi < 450`).
  - **Response**: `Object` mapping `location_id` to array of records:
    ```json
    {
      "1": [
        {
          "time": "2026-08-24T06:00:00+00:00",
          "location_id": 1,
          "pm2_5": 38.4,
          "pm10": 85.2,
          "co": 420.5,
          "no": 0.15,
          "no2": 14.8,
          "o3": 62.1,
          "so2": 8.3,
          "temperature": 29.4,
          "humidity": 68.0,
          "aqi": 108.3
        }
      ]
    }
    ```

---

### 3. Single Location 24-Hour Forecast
- **`GET /api/predict/{location_id}`**
  - **Description**: Computes 24-hour forward autoregressive AQI predictions for a specified location.
  - **Path Parameter**: `location_id` (integer, `1` to `15`)
  - **Response**:
    ```json
    {
      "location_id": 1,
      "predictions": [
        {
          "time": "2026-08-24T07:00:00+00:00",
          "predicted_aqi": 104.52
        },
        {
          "time": "2026-08-24T08:00:00+00:00",
          "predicted_aqi": 98.20
        }
      ]
    }
    ```

---

### 4. City-Wide 24-Hour Forecast
- **`GET /api/predict_all`**
  - **Description**: Generates 24-hour forward predictions across all 15 monitoring zones, including constant temperature and humidity projections.
  - **Response**: `Object` mapping `location_id` to prediction arrays:
    ```json
    {
      "1": [
        {
          "time": "2026-08-24T07:00:00+00:00",
          "aqi": 104.52,
          "temperature": 29.4,
          "humidity": 68.0
        }
      ]
    }
    ```

---

## ⚙️ Environment Configuration

### Backend `.env` (Project Root)
Create a `.env` file in the project root directory:

```ini
# PostgreSQL Database Connection
POSTGRES_PW=your_postgres_password
# Optional: Neon Serverless Postgres URI (Overrides local connection)
WEB_POSTGRES_LINK=postgresql+psycopg2://user:password@ep-sample-pooler.neon.tech/AQI_Data?sslmode=require

# OpenWeatherMap API Keys (Rotated during ingestion)
AQI_API_KEY_1=your_owm_api_key_1
AQI_API_KEY_2=your_owm_api_key_2
AQI_API_KEY_3=your_owm_api_key_3
AQI_API_KEY_4=your_owm_api_key_4

# CORS Allowed Origins (Comma-separated)
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

### Frontend `.env.local` (`frontend/.env.local`)
Create a `.env.local` file in the `frontend` directory:

```ini
# Backend API Base URL
VITE_API_URL=http://localhost:8000
```

---

## 🚀 Getting Started & Local Setup

### 1. Prerequisites
- **Node.js**: `v18.0.0` or later
- **Python**: `3.10` or later
- **PostgreSQL**: `15+` or a free cloud instance on [Neon.tech](https://neon.tech)

---

### 2. Database Setup

1. Open PostgreSQL CLI or pgAdmin and create the database:
   ```sql
   CREATE DATABASE "AQI_Data";
   ```

2. Run the table creation scripts:
   ```sql
   CREATE TABLE IF NOT EXISTS public.locations (
       id SERIAL PRIMARY KEY,
       name VARCHAR(255) NOT NULL,
       latitude NUMERIC(9,6) NOT NULL,
       longitude NUMERIC(9,6) NOT NULL
   );

   CREATE TABLE IF NOT EXISTS public.air_quality_data (
       id SERIAL PRIMARY KEY,
       time TIMESTAMP WITH TIME ZONE NOT NULL,
       location_id INTEGER REFERENCES public.locations(id),
       co REAL,
       no REAL,
       no2 REAL,
       o3 REAL,
       so2 REAL,
       pm2_5 REAL,
       pm10 REAL,
       temperature REAL,
       humidity REAL,
       CONSTRAINT uq_time_location UNIQUE (time, location_id)
   );

   CREATE INDEX IF NOT EXISTS idx_location_time 
   ON public.air_quality_data (location_id ASC, time DESC);
   ```

3. (Optional) Run historical backfill:
   ```bash
   python database_init.py
   ```

4. Verify database health:
   ```bash
   python check_db.py
   ```

---

### 3. Backend Setup

1. Create and activate a Python virtual environment:
   ```bash
   # Windows (PowerShell)
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install backend dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. Start the FastAPI development server:
   ```bash
   # From root or inside backend folder
   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```
   *The Swagger UI documentation is available at `http://localhost:8000/docs`.*

---

### 4. Frontend Setup

1. Navigate to the `frontend/` directory:
   ```bash
   cd frontend
   ```

2. Install Node.js packages:
   ```bash
   npm install
   ```

3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   *The frontend dashboard will be accessible at `http://localhost:5173`.*

---

## 🧠 Model Training & Retraining

If you have collected new historical data and wish to retrain the XGBoost prediction model:

1. Ensure the PostgreSQL database contains at least 2–3 months of continuous hourly records.
2. Run the training script:
   ```bash
   python train2.py
   ```
   *This loads the historical records, calculates lag features ($1\dots24$), rolling statistics ($6\text{h}, 24\text{h}$ mean, $24\text{h}$ std), trains the `XGBRegressor`, prints test RMSE/MAE, and exports the serialized model directly to `backend/model2.pkl`.*

Alternatively, open `train.ipynb` in Jupyter Notebook or VS Code to perform interactive Exploratory Data Analysis (EDA) and hyperparameter tuning.

---

## 🌐 Production Deployment

### Frontend (Vercel / Netlify / Cloudflare Pages)
1. Build the production static bundle:
   ```bash
   cd frontend
   npm run build
   ```
2. Deploy the generated `dist/` directory.
3. Configure `VITE_API_URL` to point to your live backend domain.

### Backend (Render / Railway / AWS / Docker)
1. Ensure `ALLOWED_ORIGINS` in your environment includes your production frontend URL.
2. Run using `uvicorn`:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port $PORT --workers 2
   ```

---

## 📜 License

This project is open source and available under the [MIT License](LICENSE).
