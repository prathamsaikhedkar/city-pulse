import psycopg2
import psycopg2
from dotenv import load_dotenv
import os
import requests
from datetime import datetime, timezone, timedelta
import json
import time
with open('gwl_data.json', 'r') as f:
    gwalior_locations = json.load(f)


load_dotenv()

api_keys = []
for i in range(1, 5):
    api_keys.append(os.getenv(f"AQI_API_KEY_{i}"))


password = os.getenv("POSTGRES_PW")

try:
    connection = psycopg2.connect(
        user = "postgres",
        password= password,
        host='127.0.0.1',
        port='5432',
        database='AQI_Data'
    )

    cursor = connection.cursor()

    epoch = 1776520800
    curr_epoch = 1776669181

    # dt_utc = datetime.fromtimestamp(epoch, tz=timezone.utc)
    # dt = dt_utc.strftime('%Y-%m-%d')
    # print(dt)
    

    weather_url = 'https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={start_date}&end_date={end_date}&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m&timezone=GMT'

    # response = requests.get(weather_url.format(lat=26.2183, lon=78.1944, start_date=dt, end_date=dt))
    # response = response.json()
    # vals = response['hourly']
    # print(len(vals['temperature_2m']))
    # print(len(vals['relative_humidity_2m']))
    # print(len(vals['wind_speed_10m']))
    # print(vals['time'])


    aqi_url = 'https://api.openweathermap.org/data/2.5/air_pollution/history?lat={lat}&lon={lon}&start={start}&end={end}&appid={key}'

    # response = requests.get(aqi_url.format(lat=26.2183, lon=78.1944, start=epoch, end=epoch+86399, key=api_keys[0]))
    # data = response.json()['list']
    # print(len(data))
    # for d in data:
    #     print(d['dt'])

    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry

    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))

    key_index = 0
    key = api_keys[key_index]

    while epoch+864000 < curr_epoch:
        dt_utc = datetime.fromtimestamp(epoch, tz=timezone.utc)
        dt = dt_utc.strftime('%Y-%m-%d')

        for location in gwalior_locations:
            

            response1 = session.get(aqi_url.format(lat=location['lat'], lon=location['lng'], start=epoch, end=epoch+863999, key=key), timeout=10)
            response1 = response1.json()

            response2 = session.get(weather_url.format(lat=location['lat'], lon=location['lng'], start_date=dt, end_date=(dt_utc+timedelta(days=9)).strftime('%Y-%m-%d')), timeout=10)
            response2 = response2.json()

            air_data = response1['list']
            weather_data = response2['hourly']

            for i in range(240):
                if i >= len(air_data) or i >= len(weather_data['temperature_2m']) or i >= len(weather_data['relative_humidity_2m']):
                    break
                components = air_data[i]['components']
                temp = weather_data['temperature_2m'][i]
                humidity = weather_data['relative_humidity_2m'][i]
                timestamp = air_data[i]['dt']
                dt_timestamp = datetime.fromtimestamp(timestamp, tz=timezone.utc)

                cursor.execute('''
                INSERT INTO public.air_quality_data(
                time, location_id, pm2_5, pm10, co, no, no2, o3, so2, temperature, humidity)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                ''', (dt_timestamp, location['id'], components['pm2_5'], components['pm10'], components['co'], components['no'], components['no2'], components['o3'], components['so2'], temp, humidity))

                connection.commit()

            print(f"Inserted data for location {location['id']} for date {dt} to {(dt_utc+timedelta(days=9)).strftime('%Y-%m-%d')}")

        print('sleeping I guess bruh')
        time.sleep(7) 
        print('slept for 7 seconds woohoo') 
        key_index = (key_index + 1) % len(api_keys)
        key = api_keys[key_index]
        epoch += 864000

    # last few days
    else:
        dt_utc = datetime.fromtimestamp(epoch, tz=timezone.utc)
        dt = dt_utc.strftime('%Y-%m-%d')

        for location in gwalior_locations:
            

            response1 = session.get(aqi_url.format(lat=location['lat'], lon=location['lng'], start=epoch, end=curr_epoch, key=key), timeout=10)
            response1 = response1.json()

            response2 = session.get(weather_url.format(lat=location['lat'], lon=location['lng'], start_date=dt, end_date=datetime.now(tz=timezone.utc).strftime('%Y-%m-%d')), timeout=10)
            response2 = response2.json()

            air_data = response1['list']
            weather_data = response2['hourly']

            for i in range(len(air_data)):
                if i >= len(weather_data['temperature_2m']) or i >= len(weather_data['relative_humidity_2m']):
                    break
                components = air_data[i]['components']
                temp = weather_data['temperature_2m'][i]
                humidity = weather_data['relative_humidity_2m'][i]
                timestamp = air_data[i]['dt']
                dt_timestamp = datetime.fromtimestamp(timestamp, tz=timezone.utc)

                cursor.execute('''
                INSERT INTO public.air_quality_data(
                time, location_id, pm2_5, pm10, co, no, no2, o3, so2, temperature, humidity)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                ''', (dt_timestamp, location['id'], components['pm2_5'], components['pm10'], components['co'], components['no'], components['no2'], components['o3'], components['so2'], temp, humidity))

                connection.commit()

            print(f"Inserted data for location {location['id']} for date {dt} to {datetime.now(tz=timezone.utc).strftime('%Y-%m-%d')}")

    print("finally finished yeahhhhhh!!!!!")





    # connection.commit()

    
    

    # for location in gwalior_locations:
    #     cursor.execute('''
    #     INSERT INTO public.locations(
    #     latitude, longitude, name)
    #     VALUES (%s, %s, %s);
    #     ''', (location['lat'], location['lng'], location['name']))

    
except Exception as e:
    print("Error:", e)

finally:
    if connection:
        cursor.close()
        connection.close()
        print("Database connection closed.")