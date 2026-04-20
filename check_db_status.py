from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()
pw = os.getenv('POSTGRES_PW')
engine = create_engine(f'postgresql+psycopg2://postgres:{pw}@127.0.0.1:5432/AQI_Data')

with engine.connect() as conn:
    r = conn.execute(text('SELECT MAX(time), MIN(time), COUNT(*) FROM public.air_quality_data'))
    row = r.fetchone()
    print(f'Latest row : {row[0]}')
    print(f'Earliest row: {row[1]}')
    print(f'Total rows  : {row[2]}')

    r2 = conn.execute(text("SELECT conname FROM pg_constraint WHERE conname = 'uq_time_location'"))
    exists = r2.fetchone()
    print(f'Unique constraint: {"EXISTS" if exists else "MISSING - will be created on next startup"}')

    r3 = conn.execute(text('SELECT time, location_id FROM public.air_quality_data ORDER BY time DESC LIMIT 5'))
    print('Last 5 rows:')
    for x in r3:
        print(f'  location={x[1]}  time={x[0]}')
