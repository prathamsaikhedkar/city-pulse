from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import os, json, pickle, requests
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

load_dotenv()

# ── Database ───────────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv(
    "WEB_POSTGRES_LINK",
    f"postgresql+psycopg2://postgres:{os.getenv('POSTGRES_PW')}@127.0.0.1:5432/AQI_Data"
)
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# ── ML Model ───────────────────────────────────────────────────────────────────
_dir = os.path.dirname(__file__)
with open(os.path.join(_dir, 'model2.pkl'), 'rb') as f:
    model = pickle.load(f)

# ── Locations ──────────────────────────────────────────────────────────────────
with open(os.path.join(_dir, 'gwl_data.json'), 'r') as f:
    LOCATIONS = json.load(f)

# ── API keys ───────────────────────────────────────────────────────────────────
API_KEYS = [k for k in [os.getenv(f"AQI_API_KEY_{i}") for i in range(1, 5)] if k]

OWM_URL   = "https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={key}"
METEO_URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude={lat}&longitude={lon}"
    "&hourly=temperature_2m,relative_humidity_2m"
    "&forecast_days=1&timezone=GMT"
)


# ═══════════════════════════════════════════════════════════════════════════════
# AQI CALCULATION  — two separate functions with different standards
# ═══════════════════════════════════════════════════════════════════════════════
#
# WHY TWO FUNCTIONS:
#   • get_aqi_display()  — US EPA breakpoints.
#     All major AQI comparison sites (AQI.in, AQICN, IQAir) use this standard.
#     Used only for the /api/history endpoint so the dashboard matches real-world readings.
#
#   • get_aqi_model()  — Indian NAQI (CPCB) breakpoints.
#     The XGBoost model was trained on Indian NAQI values.
#     Used as input features inside the autoregressive prediction loop so the model
#     receives values from the same distribution it was trained on.
# ───────────────────────────────────────────────────────────────────────────────

# US EPA breakpoints — used for display
_EPA_PM25 = [
    {'c_lo': 0.0,   'c_hi': 12.0,  'i_lo': 0,   'i_hi': 50},
    {'c_lo': 12.1,  'c_hi': 35.4,  'i_lo': 51,  'i_hi': 100},
    {'c_lo': 35.5,  'c_hi': 55.4,  'i_lo': 101, 'i_hi': 150},
    {'c_lo': 55.5,  'c_hi': 150.4, 'i_lo': 151, 'i_hi': 200},
    {'c_lo': 150.5, 'c_hi': 250.4, 'i_lo': 201, 'i_hi': 300},
    {'c_lo': 250.5, 'c_hi': 350.4, 'i_lo': 301, 'i_hi': 400},
    {'c_lo': 350.5, 'c_hi': 500.4, 'i_lo': 401, 'i_hi': 500},
]
_EPA_PM10 = [
    {'c_lo': 0,   'c_hi': 54,  'i_lo': 0,   'i_hi': 50},
    {'c_lo': 55,  'c_hi': 154, 'i_lo': 51,  'i_hi': 100},
    {'c_lo': 155, 'c_hi': 254, 'i_lo': 101, 'i_hi': 150},
    {'c_lo': 255, 'c_hi': 354, 'i_lo': 151, 'i_hi': 200},
    {'c_lo': 355, 'c_hi': 424, 'i_lo': 201, 'i_hi': 300},
    {'c_lo': 425, 'c_hi': 504, 'i_lo': 301, 'i_hi': 400},
    {'c_lo': 505, 'c_hi': 604, 'i_lo': 401, 'i_hi': 500},
]

# Indian NAQI (CPCB) breakpoints — used for model predictions
_NAQI_PM25 = [
    {'c_lo': 0,   'c_hi': 30,    'i_lo': 0,   'i_hi': 50},
    {'c_lo': 30,  'c_hi': 60,    'i_lo': 51,  'i_hi': 100},
    {'c_lo': 60,  'c_hi': 90,    'i_lo': 101, 'i_hi': 200},
    {'c_lo': 90,  'c_hi': 120,   'i_lo': 201, 'i_hi': 300},
    {'c_lo': 120, 'c_hi': 250,   'i_lo': 301, 'i_hi': 400},
    {'c_lo': 250, 'c_hi': 10000, 'i_lo': 401, 'i_hi': 500},
]
_NAQI_PM10 = [
    {'c_lo': 0,   'c_hi': 50,    'i_lo': 0,   'i_hi': 50},
    {'c_lo': 50,  'c_hi': 100,   'i_lo': 51,  'i_hi': 100},
    {'c_lo': 100, 'c_hi': 250,   'i_lo': 101, 'i_hi': 200},
    {'c_lo': 250, 'c_hi': 350,   'i_lo': 201, 'i_hi': 300},
    {'c_lo': 350, 'c_hi': 430,   'i_lo': 301, 'i_hi': 400},
    {'c_lo': 430, 'c_hi': 10000, 'i_lo': 401, 'i_hi': 500},
]


def _sub_index(conc, bps):
    for bp in bps:
        if bp['c_lo'] <= conc <= bp['c_hi']:
            return ((bp['i_hi'] - bp['i_lo']) / (bp['c_hi'] - bp['c_lo'])) * (conc - bp['c_lo']) + bp['i_lo']
    return 500


def get_aqi_display(pm25, pm10):
    """US EPA AQI — matches what comparison websites show."""
    return max(_sub_index(pm25, _EPA_PM25), _sub_index(pm10, _EPA_PM10))


def get_aqi_model(pm25, pm10):
    """Indian NAQI — matches the scale the XGBoost model was trained on."""
    return max(_sub_index(pm25, _NAQI_PM25), _sub_index(pm10, _NAQI_PM10))


# ═══════════════════════════════════════════════════════════════════════════════
# INGESTION JOB
# ═══════════════════════════════════════════════════════════════════════════════

def _ensure_unique_constraint():
    """Idempotently add UNIQUE(time, location_id) for upsert safety."""
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
    Fetch the current air quality + weather reading for every location from OWM
    and Open-Meteo, then upsert into the DB.

    ON CONFLICT DO NOTHING ensures re-runs are safe without creating duplicates.
    The scheduler calls this at :05 past every UTC hour via CronTrigger.
    """
    now_utc = datetime.now(tz=timezone.utc)
    print(f"[Ingestion] Starting at {now_utc.isoformat()}")

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
            # 1. OWM current air pollution
            air   = session.get(OWM_URL.format(lat=lat, lon=lon, key=key), timeout=10).json()
            entry = air['list'][0]
            comp  = entry['components']
            # Round down to the hour for a clean, consistent primary key
            ts = datetime.fromtimestamp(entry['dt'], tz=timezone.utc).replace(
                minute=0, second=0, microsecond=0
            )

            # 2. Open-Meteo weather (free, no API key needed)
            wx      = session.get(METEO_URL.format(lat=lat, lon=lon), timeout=10).json()
            hourly  = wx.get('hourly', {})
            t_str   = ts.strftime('%Y-%m-%dT%H:00')
            t_list  = hourly.get('time', [])
            try:
                idx  = t_list.index(t_str)
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
                    'co':    comp.get('co',    0), 'no':  comp.get('no',   0),
                    'no2':   comp.get('no2',   0), 'o3':  comp.get('o3',   0),
                    'so2':   comp.get('so2',   0),
                    'temperature': temp, 'humidity': hum,
                })
            ok_count  += 1
            key_cycle += 1

        except Exception as exc:
            print(f"[Ingestion] Location {loc_id} failed: {exc}")

    print(f"[Ingestion] Done — {ok_count}/{len(LOCATIONS)} locations updated.")


# ═══════════════════════════════════════════════════════════════════════════════
# LIFESPAN
# ═══════════════════════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ─────────────────────────────────────────────────────────────
    _ensure_unique_constraint()
    fetch_and_store_latest()   # always refresh on boot so data is never stale

    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        fetch_and_store_latest,
        # CronTrigger fires at :05 past every hour regardless of server restart time.
        # This prevents the drift/gap problem caused by interval-based scheduling.
        trigger=CronTrigger(minute=5),
        id='aqi_refresh',
        replace_existing=True,
        misfire_grace_time=300,   # if the :05 tick is missed by up to 5 min, still run
        coalesce=True,            # if multiple ticks were missed, run once not many times
    )
    scheduler.start()
    print("[Scheduler] CronTrigger active — runs at :05 past every UTC hour.")

    yield  # ← app serves requests here

    # ── Shutdown ─────────────────────────────────────────────────────────────
    scheduler.shutdown(wait=False)
    print("[Scheduler] Stopped.")


# ═══════════════════════════════════════════════════════════════════════════════
# APP
# ═══════════════════════════════════════════════════════════════════════════════

app = FastAPI(title="CityPulse API", lifespan=lifespan)

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Shared prediction helper ───────────────────────────────────────────────────

def _predict_24h(aqi_history, latest_time, const_temp, const_hum, loc_id, as_full=False):
    """
    Autoregressive 24-step XGBoost forecast.
    Uses get_aqi_model() (Indian NAQI) for input features — the scale the
    model was trained on. Returns raw model-scale predictions.
    """
    predictions = []
    hist = list(aqi_history)

    for step in range(1, 25):
        t = latest_time + timedelta(hours=step)
        w24, w6 = hist[-24:], hist[-6:]

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
            features[f'aqi_lag_{lag}'] = [hist[-lag]]

        pred = float(model.predict(pd.DataFrame(features))[0])
        entry = {'time': t.isoformat(), 'aqi': round(pred, 2)}
        if as_full:
            entry['temperature'] = round(const_temp, 1)
            entry['humidity']    = round(const_hum, 0)
        predictions.append(entry)
        hist.append(pred)

    return predictions


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/history")
def get_history():
    """
    Returns the last 3 days of readings with US EPA AQI so the dashboard
    matches values shown on comparison websites.
    """
    query = """
    WITH max_time AS (SELECT MAX(time) AS mtime FROM public.air_quality_data)
    SELECT time, location_id, pm2_5, pm10, co, no, no2, o3, so2, temperature, humidity
    FROM public.air_quality_data, max_time
    WHERE time >= max_time.mtime - INTERVAL '3 days'
    ORDER BY location_id, time DESC;
    """
    df = pd.read_sql(query, engine)
    # US EPA AQI for display
    df['aqi'] = df.apply(lambda r: get_aqi_display(r['pm2_5'], r['pm10']), axis=1)
    df = df[df['aqi'] < 450]

    return {int(loc_id): grp.to_dict('records') for loc_id, grp in df.groupby('location_id')}


@app.get("/api/predict/{location_id}")
def predict_single(location_id: int):
    """24-hour XGBoost forecast for one location."""
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
    # Model features now use US EPA (new model2.pkl was retrained on this)
    df['aqi'] = df.apply(lambda r: get_aqi_display(r['pm2_5'], r['pm10']), axis=1)

    preds = _predict_24h(
        df['aqi'].tolist(), df['time'].iloc[-1],
        float(df['temperature'].iloc[-1]), float(df['humidity'].iloc[-1]),
        location_id
    )
    for p in preds:
        p['predicted_aqi'] = p.pop('aqi')

    return {"location_id": location_id, "predictions": preds}


@app.get("/api/predict_all")
def predict_all():
    """24-hour forecast for all 15 locations."""
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
    # Model features now use US EPA (new model2.pkl was retrained on this)
    df['aqi'] = df.apply(lambda r: get_aqi_display(r['pm2_5'], r['pm10']), axis=1)

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
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
