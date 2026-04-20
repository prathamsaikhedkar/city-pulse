from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
import os
import pickle
import requests
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Database ──────────────────────────────────────────────────────────────────
password = os.getenv("POSTGRES_PW")
DB_URL   = f'postgresql+psycopg2://postgres:{password}@127.0.0.1:5432/AQI_Data'
engine   = create_engine(DB_URL)

# ── ML Model ──────────────────────────────────────────────────────────────────
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'model.pkl')
with open(MODEL_PATH, 'rb') as f:
    model = pickle.load(f)

# ── Locations (from gwl_data.json, kept in sync with DB) ─────────────────────
import json
GWL_PATH = os.path.join(os.path.dirname(__file__), '..', 'gwl_data.json')
with open(GWL_PATH, 'r') as f:
    LOCATIONS = json.load(f)

# ── API config ────────────────────────────────────────────────────────────────
API_KEYS = [os.getenv(f"AQI_API_KEY_{i}") for i in range(1, 5)]
# OWM current air pollution (free, no history lag)
OWM_CURRENT_URL = (
    "https://api.openweathermap.org/data/2.5/air_pollution"
    "?lat={lat}&lon={lon}&appid={key}"
)
# Open-Meteo: last 2 hours of weather (free, no key)
METEO_CURRENT_URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude={lat}&longitude={lon}"
    "&hourly=temperature_2m,relative_humidity_2m"
    "&forecast_days=1&timezone=GMT"
)

# ── AQI breakpoints ───────────────────────────────────────────────────────────
PM25_BP = [
    {'c_low': 0,   'c_high': 30,    'i_low': 0,   'i_high': 50},
    {'c_low': 30,  'c_high': 60,    'i_low': 51,  'i_high': 100},
    {'c_low': 60,  'c_high': 90,    'i_low': 101, 'i_high': 200},
    {'c_low': 90,  'c_high': 120,   'i_low': 201, 'i_high': 300},
    {'c_low': 120, 'c_high': 250,   'i_low': 301, 'i_high': 400},
    {'c_low': 250, 'c_high': 10000, 'i_low': 401, 'i_high': 500},
]
PM10_BP = [
    {'c_low': 0,   'c_high': 50,    'i_low': 0,   'i_high': 50},
    {'c_low': 50,  'c_high': 100,   'i_low': 51,  'i_high': 100},
    {'c_low': 100, 'c_high': 250,   'i_low': 101, 'i_high': 200},
    {'c_low': 250, 'c_high': 350,   'i_low': 201, 'i_high': 300},
    {'c_low': 350, 'c_high': 430,   'i_low': 301, 'i_high': 400},
    {'c_low': 430, 'c_high': 10000, 'i_low': 401, 'i_high': 500},
]

def calculate_sub_index(conc, breakpoints):
    for bp in breakpoints:
        if bp['c_low'] <= conc <= bp['c_high']:
            return ((bp['i_high'] - bp['i_low']) / (bp['c_high'] - bp['c_low'])) * (conc - bp['c_low']) + bp['i_low']
    return 500

def get_aqi(pm25, pm10):
    return max(calculate_sub_index(pm25, PM25_BP), calculate_sub_index(pm10, PM10_BP))


# ═══════════════════════════════════════════════════════════════════════════════
# DATA INGESTION  — runs on startup and every hour thereafter
# ═══════════════════════════════════════════════════════════════════════════════

def fetch_and_store_latest():
    """
    Fetch the latest air quality + weather reading for every location from the
    OpenWeatherMap Current Air Pollution API and Open-Meteo Forecast API,
    then upsert into the database.

    The INSERT uses ON CONFLICT DO NOTHING so re-running never creates
    duplicates — safe to call as often as you like.
    """
    print(f"[Scheduler] Fetching latest data at {datetime.now(tz=timezone.utc).isoformat()}")

    session = requests.Session()
    key_cycle = 0  # rotate through API keys to avoid rate limits

    inserted_count = 0

    for location in LOCATIONS:
        lat, lon = location['lat'], location['lng']
        loc_id   = location['id']
        key      = API_KEYS[key_cycle % len(API_KEYS)]

        try:
            # 1. Current air pollution from OWM (returns a single "list" entry)
            air_resp = session.get(
                OWM_CURRENT_URL.format(lat=lat, lon=lon, key=key),
                timeout=10
            ).json()

            air_entry   = air_resp['list'][0]
            components  = air_entry['components']
            # OWM returns the measurement timestamp as a Unix epoch
            ts          = datetime.fromtimestamp(air_entry['dt'], tz=timezone.utc)
            # Round down to the hour so we get clean hourly rows matching historic data
            ts_hour     = ts.replace(minute=0, second=0, microsecond=0)

            # 2. Current temperature + humidity from Open-Meteo (free, no key)
            weather_resp = session.get(
                METEO_CURRENT_URL.format(lat=lat, lon=lon),
                timeout=10
            ).json()

            hourly = weather_resp.get('hourly', {})
            # Find the index whose time matches our rounded timestamp
            times_str  = hourly.get('time', [])
            target_str = ts_hour.strftime('%Y-%m-%dT%H:00')
            try:
                idx         = times_str.index(target_str)
                temperature = hourly['temperature_2m'][idx]
                humidity    = hourly['relative_humidity_2m'][idx]
            except (ValueError, IndexError):
                # fallback: just take the last available reading
                temperature = hourly['temperature_2m'][-1]
                humidity    = hourly['relative_humidity_2m'][-1]

            # 3. Upsert — a UNIQUE constraint on (time, location_id) prevents duplicates.
            #    We create it once at startup if it doesn't already exist.
            insert_sql = text("""
                INSERT INTO public.air_quality_data
                    (time, location_id, pm2_5, pm10, co, no, no2, o3, so2, temperature, humidity)
                VALUES
                    (:time, :location_id, :pm2_5, :pm10, :co, :no, :no2, :o3, :so2, :temperature, :humidity)
                ON CONFLICT (time, location_id) DO NOTHING;
            """)

            with engine.begin() as conn:
                conn.execute(insert_sql, {
                    'time':        ts_hour,
                    'location_id': loc_id,
                    'pm2_5':       components.get('pm2_5', 0),
                    'pm10':        components.get('pm10',  0),
                    'co':          components.get('co',    0),
                    'no':          components.get('no',    0),
                    'no2':         components.get('no2',   0),
                    'o3':          components.get('o3',    0),
                    'so2':         components.get('so2',   0),
                    'temperature': temperature,
                    'humidity':    humidity,
                })

            inserted_count += 1
            key_cycle += 1

        except Exception as e:
            print(f"[Scheduler] Error for location {loc_id} ({location['name']}): {e}")

    print(f"[Scheduler] Done — {inserted_count}/{len(LOCATIONS)} locations updated.")


def ensure_unique_constraint():
    """
    Add a UNIQUE constraint on (time, location_id) if it doesn't exist yet.
    This is idempotent — running it multiple times is safe.
    """
    with engine.begin() as conn:
        conn.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = 'uq_time_location'
                ) THEN
                    ALTER TABLE public.air_quality_data
                    ADD CONSTRAINT uq_time_location UNIQUE (time, location_id);
                END IF;
            END
            $$;
        """))
    print("[Startup] Unique constraint on (time, location_id) ensured.")


# ═══════════════════════════════════════════════════════════════════════════════
# APP STARTUP — wire up the background scheduler
# ═══════════════════════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup_event():
    # Make sure the DB schema is ready for upserts
    ensure_unique_constraint()

    # Run immediately on boot so data is fresh from the first request
    fetch_and_store_latest()

    # Then schedule it to run every hour
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        fetch_and_store_latest,
        trigger='interval',
        hours=1,
        id='aqi_refresh',
        replace_existing=True,
    )
    scheduler.start()
    print("[Scheduler] Background job scheduled — runs every hour.")


# ═══════════════════════════════════════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/history")
def get_history():
    query = """
    WITH max_time AS (SELECT MAX(time) as mtime FROM public.air_quality_data)
    SELECT time, location_id, pm2_5, pm10, co, no, no2, o3, so2, temperature, humidity
    FROM public.air_quality_data, max_time
    WHERE time >= max_time.mtime - interval '3 days'
    ORDER BY location_id, time DESC;
    """
    df = pd.read_sql(query, engine)
    df['aqi'] = df.apply(lambda row: get_aqi(row['pm2_5'], row['pm10']), axis=1)
    df = df[df['aqi'] < 450]

    data_map = {}
    for loc_id, group in df.groupby('location_id'):
        data_map[int(loc_id)] = group.to_dict('records')
    return data_map


@app.get("/api/predict/{location_id}")
def predict_aqi(location_id: int):
    query = f"""
    SELECT time, pm2_5, pm10, temperature, humidity
    FROM public.air_quality_data
    WHERE location_id = {location_id}
    ORDER BY time DESC
    LIMIT 24;
    """
    df = pd.read_sql(query, engine)
    if len(df) < 24:
        return {"error": "Not enough data"}

    df = df.sort_values('time').reset_index(drop=True)
    df['aqi'] = df.apply(lambda row: get_aqi(row['pm2_5'], row['pm10']), axis=1)

    aqi_history  = df['aqi'].tolist()
    latest_time  = df['time'].iloc[-1]
    const_temp   = float(df['temperature'].iloc[-1])
    const_hum    = float(df['humidity'].iloc[-1])
    predictions  = []

    for step in range(1, 25):
        target_time      = latest_time + timedelta(hours=step)
        window_24        = aqi_history[-24:]
        window_6         = aqi_history[-6:]
        rolling_mean_6h  = np.mean(window_6)
        rolling_mean_24h = np.mean(window_24)
        rolling_std_24h  = np.std(window_24, ddof=1)

        features = {
            'location_id':          [location_id],
            'hour':                 [target_time.hour],
            'day_of_week':          [target_time.weekday()],
            'month':                [target_time.month],
            'aqi_rolling_mean_6h':  [rolling_mean_6h],
            'aqi_rolling_mean_24h': [rolling_mean_24h],
            'aqi_rolling_std_24h':  [rolling_std_24h],
            'temperature':          [const_temp],
            'humidity':             [const_hum],
        }
        for lag in range(1, 25):
            features[f'aqi_lag_{lag}'] = [aqi_history[-lag]]

        pred_aqi = float(model.predict(pd.DataFrame(features))[0])
        predictions.append({'time': target_time.isoformat(), 'predicted_aqi': round(pred_aqi, 2)})
        aqi_history.append(pred_aqi)

    return {"location_id": location_id, "predictions": predictions}


@app.get("/api/predict_all")
def predict_all():
    query = """
    WITH latest_data AS (
        SELECT time, location_id, pm2_5, pm10, temperature, humidity,
               ROW_NUMBER() OVER(PARTITION BY location_id ORDER BY time DESC) AS row_num
        FROM public.air_quality_data
    )
    SELECT time, location_id, pm2_5, pm10, temperature, humidity
    FROM latest_data
    WHERE row_num <= 24
    ORDER BY location_id, time ASC;
    """
    df = pd.read_sql(query, engine)
    df['aqi'] = df.apply(lambda row: get_aqi(row['pm2_5'], row['pm10']), axis=1)

    results_map = {}
    for loc_id, group in df.groupby('location_id'):
        if len(group) < 24:
            continue

        group         = group.reset_index(drop=True)
        aqi_history   = group['aqi'].tolist()
        latest_time   = group['time'].iloc[-1]
        const_temp    = float(group['temperature'].iloc[-1])
        const_hum     = float(group['humidity'].iloc[-1])
        predictions   = []

        for step in range(1, 25):
            target_time      = latest_time + timedelta(hours=step)
            window_24        = aqi_history[-24:]
            window_6         = aqi_history[-6:]
            rolling_mean_6h  = np.mean(window_6)
            rolling_mean_24h = np.mean(window_24)
            rolling_std_24h  = np.std(window_24, ddof=1)

            features = {
                'location_id':          [int(loc_id)],
                'hour':                 [target_time.hour],
                'day_of_week':          [target_time.weekday()],
                'month':                [target_time.month],
                'aqi_rolling_mean_6h':  [rolling_mean_6h],
                'aqi_rolling_mean_24h': [rolling_mean_24h],
                'aqi_rolling_std_24h':  [rolling_std_24h],
                'temperature':          [const_temp],
                'humidity':             [const_hum],
            }
            for lag in range(1, 25):
                features[f'aqi_lag_{lag}'] = [aqi_history[-lag]]

            pred_aqi = float(model.predict(pd.DataFrame(features))[0])
            predictions.append({
                'time':        target_time.isoformat(),
                'aqi':         round(pred_aqi, 2),
                'temperature': round(const_temp, 1),
                'humidity':    round(const_hum, 0),
            })
            aqi_history.append(pred_aqi)

        results_map[int(loc_id)] = predictions

    return results_map


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
