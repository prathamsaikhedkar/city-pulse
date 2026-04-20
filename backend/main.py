from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
import os, json, pickle, requests
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

load_dotenv()

# ── Database ───────────────────────────────────────────────────────────────────
# Uses the Neon cloud connection string from .env (WEB_POSTGRES_LINK).
# Falls back to a local Postgres URL for local dev if the env var is absent.
DATABASE_URL = os.getenv(
    "WEB_POSTGRES_LINK",
    f"postgresql+psycopg2://postgres:{os.getenv('POSTGRES_PW')}@127.0.0.1:5432/AQI_Data"
)
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# ── ML Model ───────────────────────────────────────────────────────────────────
_dir = os.path.dirname(__file__)
with open(os.path.join(_dir, 'model.pkl'), 'rb') as f:
    model = pickle.load(f)

# ── Locations ──────────────────────────────────────────────────────────────────
with open(os.path.join(_dir, 'gwl_data.json'), 'r') as f:
    LOCATIONS = json.load(f)

# ── OWM API keys (rotated to stay within free-tier rate limits) ────────────────
API_KEYS = [k for k in [os.getenv(f"AQI_API_KEY_{i}") for i in range(1, 5)] if k]

OWM_URL   = "https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={key}"
METEO_URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude={lat}&longitude={lon}"
    "&hourly=temperature_2m,relative_humidity_2m"
    "&forecast_days=1&timezone=GMT"
)

# ── AQI breakpoints (Indian standard) ─────────────────────────────────────────
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

def _sub_index(conc, bps):
    for bp in bps:
        if bp['c_low'] <= conc <= bp['c_high']:
            return ((bp['i_high'] - bp['i_low']) / (bp['c_high'] - bp['c_low'])) * (conc - bp['c_low']) + bp['i_low']
    return 500

def get_aqi(pm25, pm10):
    return max(_sub_index(pm25, PM25_BP), _sub_index(pm10, PM10_BP))


# ═══════════════════════════════════════════════════════════════════════════════
# INGESTION JOB
# ═══════════════════════════════════════════════════════════════════════════════

def _ensure_unique_constraint():
    """Idempotently add UNIQUE(time, location_id) so ON CONFLICT works."""
    with engine.begin() as conn:
        conn.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint WHERE conname = 'uq_time_location'
                ) THEN
                    ALTER TABLE public.air_quality_data
                    ADD CONSTRAINT uq_time_location UNIQUE (time, location_id);
                END IF;
            END $$;
        """))


def fetch_and_store_latest():
    """
    Pull the current air pollution + weather reading for every location and
    upsert it into the database. Uses ON CONFLICT DO NOTHING — safe to call
    any number of times without creating duplicates.
    """
    print(f"[Ingestion] Starting at {datetime.now(tz=timezone.utc).isoformat()}")
    session   = requests.Session()
    key_cycle = 0
    ok_count  = 0

    insert_sql = text("""
        INSERT INTO public.air_quality_data
            (time, location_id, pm2_5, pm10, co, no, no2, o3, so2, temperature, humidity)
        VALUES
            (:time, :location_id, :pm2_5, :pm10, :co, :no, :no2, :o3, :so2, :temperature, :humidity)
        ON CONFLICT (time, location_id) DO NOTHING;
    """)

    for loc in LOCATIONS:
        lat, lon, loc_id = loc['lat'], loc['lng'], loc['id']
        key = API_KEYS[key_cycle % len(API_KEYS)]
        try:
            # 1. Current OWM air pollution reading
            air = session.get(OWM_URL.format(lat=lat, lon=lon, key=key), timeout=10).json()
            entry = air['list'][0]
            comp  = entry['components']
            ts    = datetime.fromtimestamp(entry['dt'], tz=timezone.utc).replace(minute=0, second=0, microsecond=0)

            # 2. Open-Meteo weather (free, no key required)
            wx = session.get(METEO_URL.format(lat=lat, lon=lon), timeout=10).json()
            hourly      = wx.get('hourly', {})
            target_str  = ts.strftime('%Y-%m-%dT%H:00')
            times_list  = hourly.get('time', [])
            try:
                idx  = times_list.index(target_str)
                temp = hourly['temperature_2m'][idx]
                hum  = hourly['relative_humidity_2m'][idx]
            except (ValueError, IndexError):
                temp = hourly['temperature_2m'][-1]
                hum  = hourly['relative_humidity_2m'][-1]

            # 3. Upsert
            with engine.begin() as conn:
                conn.execute(insert_sql, {
                    'time': ts, 'location_id': loc_id,
                    'pm2_5': comp.get('pm2_5', 0), 'pm10': comp.get('pm10', 0),
                    'co':    comp.get('co',    0), 'no':   comp.get('no',   0),
                    'no2':   comp.get('no2',   0), 'o3':   comp.get('o3',   0),
                    'so2':   comp.get('so2',   0),
                    'temperature': temp, 'humidity': hum,
                })
            ok_count  += 1
            key_cycle += 1

        except Exception as exc:
            print(f"[Ingestion] Location {loc_id} failed: {exc}")

    print(f"[Ingestion] Done — {ok_count}/{len(LOCATIONS)} locations updated.")


# ═══════════════════════════════════════════════════════════════════════════════
# LIFESPAN  (replaces deprecated @app.on_event)
# ═══════════════════════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──
    _ensure_unique_constraint()
    fetch_and_store_latest()               # immediate refresh on every boot

    scheduler = BackgroundScheduler()
    scheduler.add_job(fetch_and_store_latest, 'interval', hours=1, id='aqi_refresh')
    scheduler.start()
    print("[Scheduler] Hourly refresh job started.")

    yield  # ← app runs here

    # ── Shutdown ──
    scheduler.shutdown(wait=False)
    print("[Scheduler] Stopped.")


# ═══════════════════════════════════════════════════════════════════════════════
# APP
# ═══════════════════════════════════════════════════════════════════════════════

app = FastAPI(title="CityPulse API", lifespan=lifespan)

# Allow all origins in dev; lock this down to your Vercel URL in production.
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Helper: build prediction features ─────────────────────────────────────────

def _predict_24h(aqi_history, latest_time, const_temp, const_hum, loc_id, as_full=False):
    """
    Autoregressive 24-step XGBoost forecast.
    Returns a list of dicts with 'time' and 'aqi' (or 'predicted_aqi').
    """
    predictions = []
    aqi_hist    = list(aqi_history)

    for step in range(1, 25):
        t            = latest_time + timedelta(hours=step)
        w24          = aqi_hist[-24:]
        w6           = aqi_hist[-6:]

        features = {
            'location_id':          [int(loc_id)],
            'hour':                 [t.hour],
            'day_of_week':          [t.weekday()],
            'month':                [t.month],
            'aqi_rolling_mean_6h':  [np.mean(w6)],
            'aqi_rolling_mean_24h': [np.mean(w24)],
            'aqi_rolling_std_24h':  [np.std(w24, ddof=1)],
            'temperature':          [const_temp],
            'humidity':             [const_hum],
        }
        for lag in range(1, 25):
            features[f'aqi_lag_{lag}'] = [aqi_hist[-lag]]

        pred = float(model.predict(pd.DataFrame(features))[0])
        entry = {'time': t.isoformat(), 'aqi': round(pred, 2)}
        if as_full:
            entry['temperature'] = round(const_temp, 1)
            entry['humidity']    = round(const_hum, 0)
        predictions.append(entry)
        aqi_hist.append(pred)

    return predictions


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/history")
def get_history():
    """Return the last 3 days of air quality data for every location."""
    query = """
    WITH max_time AS (SELECT MAX(time) AS mtime FROM public.air_quality_data)
    SELECT time, location_id, pm2_5, pm10, co, no, no2, o3, so2, temperature, humidity
    FROM public.air_quality_data, max_time
    WHERE time >= max_time.mtime - INTERVAL '3 days'
    ORDER BY location_id, time DESC;
    """
    df = pd.read_sql(query, engine)
    df['aqi'] = df.apply(lambda r: get_aqi(r['pm2_5'], r['pm10']), axis=1)
    df = df[df['aqi'] < 450]

    return {int(loc_id): grp.to_dict('records') for loc_id, grp in df.groupby('location_id')}


@app.get("/api/predict/{location_id}")
def predict_single(location_id: int):
    """Return a 24-hour XGBoost AQI forecast for one location."""
    query = f"""
    SELECT time, pm2_5, pm10, temperature, humidity
    FROM public.air_quality_data
    WHERE location_id = {location_id}
    ORDER BY time DESC LIMIT 24;
    """
    df = pd.read_sql(query, engine)
    if len(df) < 24:
        return {"error": "Not enough data for this location."}

    df = df.sort_values('time').reset_index(drop=True)
    df['aqi'] = df.apply(lambda r: get_aqi(r['pm2_5'], r['pm10']), axis=1)

    preds = _predict_24h(
        df['aqi'].tolist(), df['time'].iloc[-1],
        float(df['temperature'].iloc[-1]), float(df['humidity'].iloc[-1]),
        location_id
    )
    # Keep backward-compat key name for the single-location endpoint
    for p in preds:
        p['predicted_aqi'] = p.pop('aqi')

    return {"location_id": location_id, "predictions": preds}


@app.get("/api/predict_all")
def predict_all():
    """Return a 24-hour forecast for all 15 locations."""
    query = """
    WITH latest AS (
        SELECT time, location_id, pm2_5, pm10, temperature, humidity,
               ROW_NUMBER() OVER(PARTITION BY location_id ORDER BY time DESC) AS rn
        FROM public.air_quality_data
    )
    SELECT time, location_id, pm2_5, pm10, temperature, humidity
    FROM latest WHERE rn <= 24
    ORDER BY location_id, time ASC;
    """
    df = pd.read_sql(query, engine)
    df['aqi'] = df.apply(lambda r: get_aqi(r['pm2_5'], r['pm10']), axis=1)

    results = {}
    for loc_id, grp in df.groupby('location_id'):
        if len(grp) < 24:
            continue
        grp = grp.reset_index(drop=True)
        results[int(loc_id)] = _predict_24h(
            grp['aqi'].tolist(), grp['time'].iloc[-1],
            float(grp['temperature'].iloc[-1]), float(grp['humidity'].iloc[-1]),
            loc_id, as_full=True
        )

    return results


@app.get("/health")
def health():
    """Render health-check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
