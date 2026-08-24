# ⚙️ CityPulse Backend Service

The CityPulse backend is an asynchronous, high-performance REST API built with **FastAPI** that powers air quality monitoring, automated data ingestion, and autoregressive machine learning predictions for the CityPulse platform.

---

## 📌 Architecture & Components

```
backend/
├── main.py              # FastAPI application, route handlers, scheduler & ML inference
├── model2.pkl           # Trained XGBoost model serialized with pickle (US EPA scale)
├── model.pkl            # Legacy trained model (NAQI scale)
├── gwl_data.json        # Sensor coordinates metadata for 15 locations in Gwalior
├── requirements.txt     # Python dependencies
└── README.md            # Backend documentation (this file)
```

---

## 🚀 Key Responsibilities

1. **Scheduled Data Ingestion**:
   - Uses `apscheduler.schedulers.background.BackgroundScheduler` configured with `CronTrigger(minute=5)`.
   - Fires at `:05` past every UTC hour to query:
     - **OpenWeatherMap Air Pollution API**: Pollutant levels ($\text{PM}_{2.5}, \text{PM}_{10}, \text{CO}, \text{NO}, \text{NO}_2, \text{O}_3, \text{SO}_2$).
     - **Open-Meteo API**: Synchronized hourly temperature and relative humidity.
   - Rotates across API keys (`AQI_API_KEY_1..4`) to ensure uninterrupted polling without rate limit violations.
   - Performs idempotent upsert queries into PostgreSQL with `ON CONFLICT (time, location_id) DO NOTHING`.

2. **Real-time Air Quality Conversion**:
   - Converts pollutant concentrations ($\mu\text{g/m}^3$) into US EPA standard Air Quality Index values via piecewise linear interpolation breakpoints (`get_aqi_display`).

3. **Autoregressive 24-Hour Forecasting**:
   - Gathers the latest 24 continuous hourly records for each sensor.
   - Computes dynamic features (lags 1–24, 6-hour rolling mean, 24-hour rolling mean, 24-hour rolling standard deviation, calendar harmonics, ambient temperature, humidity).
   - Iteratively feeds step $t+1$ output back into the feature matrix to forecast $t+1 \dots t+24$.

---

## 🛠️ Endpoints Specification

### 1. `GET /health`
- **Response**: `{"status": "ok"}`
- **Purpose**: Liveness probe for monitoring and load balancers.

### 2. `GET /api/history`
- **Response**: Map of `location_id` $\to$ List of hourly readings for the last 72 hours.
- **SQL Query**:
  ```sql
  WITH max_time AS (SELECT MAX(time) AS mtime FROM public.air_quality_data)
  SELECT time, location_id, pm2_5, pm10, co, no, no2, o3, so2, temperature, humidity
  FROM public.air_quality_data, max_time
  WHERE time >= max_time.mtime - INTERVAL '3 days'
  ORDER BY location_id, time DESC;
  ```
- **Post-processing**: Filters out sensor spikes / invalid anomalies (`aqi < 450`).

### 3. `GET /api/predict/{location_id}`
- **Path Parameter**: `location_id` (integer)
- **Response**:
  ```json
  {
    "location_id": 1,
    "predictions": [
      {
        "time": "2026-08-24T07:00:00+00:00",
        "predicted_aqi": 104.52
      }
    ]
  }
  ```

### 4. `GET /api/predict_all`
- **Response**: Map of `location_id` $\to$ List of 24 future hours with predicted `aqi`, `temperature`, and `humidity`.

---

## 📦 Setup & Execution

### 1. Virtual Environment & Dependencies
```bash
# From the project root
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1

pip install -r backend/requirements.txt
```

### 2. Running Locally
```bash
# Inside backend directory
uvicorn main:app --reload --port 8000
```
Interactive documentation will be available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## ⚙️ Environment Variables

The backend loads configuration from the root `.env` file via `python-dotenv`:

| Variable | Description | Default |
|:---|:---|:---|
| `WEB_POSTGRES_LINK` | Full PostgreSQL connection URI | `postgresql+psycopg2://postgres:{POSTGRES_PW}@127.0.0.1:5432/AQI_Data` |
| `POSTGRES_PW` | Password for local PostgreSQL instance | *None* |
| `AQI_API_KEY_1..4` | OpenWeatherMap API Keys for rotation | *None* |
| `ALLOWED_ORIGINS` | Comma-separated CORS whitelist | `*` |
