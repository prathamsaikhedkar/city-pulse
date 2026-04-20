# CityPulse - A modern city dashboard app

CityPulse is a web application that provides a comprehensive overview of a city's key metrics. It allows users to monitor various aspects of the city's health and well-being, such as air quality, Sound quality, traffic conditions, public transport availability, and more. It also allows for future (24 hours) forecasting of above metrics using time series analysis and machine learning models. The app features a modern, intuitive interface with interactive visualizations and real-time data updates.

## Important: while the features listed above are what we are aiming for, we will start with a minimal viable product (MVP) that includes only Air Quality Dashboard and AQI prediction for various areas (about 10-15) of a single city (Gwalior). Only the MVP of Air Quality dashboard and AQI prediction will be built using the tech stack listed below. 

## Features

- **Real-time Data**: Fetches data from various APIs to provide up-to-date information.
- **Interactive Dashboard**: A visually appealing dashboard with charts and graphs to display city metrics for entire city as well as region-wise.
- **24 hours AQI Prediction**: Predicts AQI for various areas of a city using time series analysis and machine learning models.
- **Geographic HeatMap visualisation**: Visualizes the predicted AQI for various areas of a city using a heatmap on a map, and also for current AQI.
- **Responsive Design**: The app works seamlessly on different devices, including desktops, tablets, and mobile phones.
- **Modular Architecture**: Built with a modular approach, making it easy to add new features and metrics.
- **API Integration**: Integrates with multiple APIs to gather data on air quality.
- **Design palette**: The app uses different color palettes depending on which metric is being displayed (for example, it could be a warm color palette for AQI, a cool color palette for sound quality, etc.). The color palette should be chosen such that it is easy on the eyes and does not cause any discomfort to the user. 

## Tech Stack

- **Frontend**: React, React Router, Material-UI, Chart.js for Charts, leaflet.js for maps
- **Backend**: Python FastAPI with an ML model for AQI prediction
- **Database**: PostgreSQL
- **APIs**: OpenWeatherMap API.


## API Integrations

CityPulse integrates with the following APIs to gather data:

- **OpenWeatherMap API**: For air quality and weather data.



## instructions for the agent

### ML Model Information:

The ML model is trained using the `train.ipynb` script and the trained model is saved as `model.pkl`. The model should ideally be trained on historical AQI data for Gwalior. Prefer general models like XGBoost over Time series specific models if possible.

### Database Information:

The PostgreSQL database is installed on my local machine at `C:\Program Files\PostgreSQL\18`.

### Key Areas of Gwalior to be included in the App

No.,Area Name,Description,Latitude,Longitude
1,Gwalior Fort,The historic heart and highest point of the city.,26.2300° N,78.1691° E
2,Lashkar,The traditional central business district and palace area.,26.2031° N,78.1610° E
3,Gole Ka Mandir,A major transit hub connecting to the northern outskirts.,26.2465° N,78.2045° E
4,Hazira,An industrial and densely populated residential zone.,26.2392° N,78.1795° E
5,Morar,"Formerly a separate cantonment, now a bustling eastern wing.",26.2238° N,78.2255° E
6,City Centre,The modern administrative and upscale commercial hub.,26.2120° N,78.1944° E
7,Thatipur,A prominent residential government colony area.,26.2163° N,78.2098° E
8,Phool Bagh,"A central cultural area housing parks, museums, and shrines.",26.2195° N,78.1744° E
9,Dabra (Outskirts),The southern gateway and industrial satellite region.,25.8900° N,78.3300° E
10,DD Nagar,A planned residential township towards the northeast.,26.2580° N,78.2180° E
11,Sada (New Gwalior),The counter-magnet city area being developed to the west.,26.1950° N,78.0800° E
12,Kampoo,A historic southern area known for hospitals and sports.,26.1965° N,78.1565° E
13,Birla Nagar,An industrial belt centered around the railway station.,26.2485° N,78.1885° E
14,Tansen Nagar,A residential area named after the legendary musician.,26.2355° N,78.1905° E
15,Hurawali,A fast-developing residential zone on the eastern edge.,26.2040° N,78.2320° E

### Project building Tasks:

Perform these tasks one by one separately only when I ask you to do so.

1. First of all, build the FRONTEND ONLY with MOCK DATA, as well as WITHOUT the Predicted AQI feature. 
Use the cdn versions of Chart js and leaflet js.

DO NOT build any backend or databases at this step.
There are a few Database related files in the workspace, but I want to build the database myself. So don't interfere with it. Also since there is no data yet, do not build the model.
Just for your knowledge, the schema for the database tables will look like this:

(i)
CREATE TABLE IF NOT EXISTS public.locations
(
    id integer NOT NULL DEFAULT nextval('locations_id_seq'::regclass),
    name character varying(255)[] COLLATE pg_catalog."default" NOT NULL,
    latitude numeric(9,6) NOT NULL,
    longitude numeric(9,6) NOT NULL,
    CONSTRAINT locations_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.locations
    OWNER to postgres;

(ii)
CREATE TABLE IF NOT EXISTS public.air_quality_data
(
    id integer NOT NULL DEFAULT nextval('"air_quality-data_id_seq"'::regclass),
    "time" timestamp with time zone,
    location_id integer,
    co real,
    no real,
    no2 real,
    o3 real,
    so2 real,
    pm2_5 real,
    pm10 real,
    temperature real,
    humidity real,
    CONSTRAINT "air_quality-data_pkey" PRIMARY KEY (id),
    CONSTRAINT location_id FOREIGN KEY (location_id)
        REFERENCES public.locations (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.air_quality_data
    OWNER to postgres;
-- Index: idx_location_time

-- DROP INDEX IF EXISTS public.idx_location_time;

CREATE INDEX IF NOT EXISTS idx_location_time
    ON public.air_quality_data USING btree
    (location_id ASC NULLS LAST, "time" DESC NULLS FIRST)
    WITH (fillfactor=100, deduplicate_items=True)
    TABLESPACE pg_default;

2. Check the database using the credentials from .env. If at this point, the database is not built yet, then I will ask you to build it separately and give necessary details at that time. 

3. Make a Jupyter notebook and create the ML Model using the database

4. Create the backend FastAPI for serving Air quality details and Model predictions. And add the AQI prediction feature to the frontend, and link the frontend to the backend.


### Other instructions:

Make sure to always make the code as structured, easy to follow and as little complex as possible, as I will be reviewing the code and changing it in the future manually. So, ensure proper readability.