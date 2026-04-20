import psycopg2
import os
from dotenv import load_dotenv

def check_database():
    load_dotenv()
    password = os.getenv("POSTGRES_PW")

    try:
        connection = psycopg2.connect(
            user="postgres",
            password=password,
            host='127.0.0.1',
            port='5432',
            database='AQI_Data'
        )
        cursor = connection.cursor()

        print("--- Database Diagnostics: AQI_Data ---\n")

        # 1. Check locations table
        cursor.execute("SELECT COUNT(*) FROM public.locations;")
        loc_count = cursor.fetchone()[0]
        print(f"Total Locations stored: {loc_count}")

        if loc_count > 0:
            cursor.execute("SELECT id, name, latitude, longitude FROM public.locations LIMIT 3;")
            locations = cursor.fetchall()
            print("Sample Locations:")
            for loc in locations:
                print(f"  - ID: {loc[0]} | Name: {loc[1]} | Lat: {loc[2]}, Lng: {loc[3]}")
        print("\n")

        # 2. Check air_quality_data table
        cursor.execute("SELECT COUNT(*) FROM public.air_quality_data;")
        aqi_count = cursor.fetchone()[0]
        print(f"Total Air Quality Records stored: {aqi_count}")

        if aqi_count > 0:
            cursor.execute("SELECT MIN(time), MAX(time) FROM public.air_quality_data;")
            time_range = cursor.fetchone()
            print(f"Data Time Range: {time_range[0]} to {time_range[1]}")

            print("\nSample AQI Records (Last 5 inserted):")
            cursor.execute('''
                SELECT time, location_id, pm2_5, pm10, temperature, humidity 
                FROM public.air_quality_data 
                ORDER BY time DESC 
                LIMIT 5;
            ''')
            records = cursor.fetchall()
            print(f"{'Time':<25} | {'Loc ID':<6} | {'PM2.5':<6} | {'PM10':<6} | {'Temp':<6} | {'Humidity':<8}")
            print("-" * 75)
            for r in records:
                print(f"{str(r[0]):<25} | {r[1]:<6} | {r[2]:<6.2f} | {r[3]:<6.2f} | {r[4]:<6.2f} | {r[5]:<8.2f}")
        
    except psycopg2.Error as e:
        print(f"Database error occurred: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'connection' in locals() and connection:
            cursor.close()
            connection.close()
            print("\nConnection closed.")

if __name__ == "__main__":
    check_database()
