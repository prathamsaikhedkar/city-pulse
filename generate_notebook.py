import json

notebook = {
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# CityPulse AQI Prediction Model\n",
    "\n",
    "This notebook covers the end-to-end Machine Learning pipeline to train an XGBoost model predicting Air Quality Index (AQI) across 15 locations in Gwalior.\n"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "import pandas as pd\n",
    "import numpy as np\n",
    "import psycopg2\n",
    "import os\n",
    "from sqlalchemy import create_engine\n",
    "from dotenv import load_dotenv\n",
    "import matplotlib.pyplot as plt\n",
    "import seaborn as sns\n",
    "\n",
    "from xgboost import XGBRegressor\n",
    "from sklearn.metrics import mean_squared_error, mean_absolute_error\n",
    "import pickle\n",
    "\n",
    "%matplotlib inline\n",
    "sns.set_theme(style=\"whitegrid\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "load_dotenv()\n",
    "password = os.getenv(\"POSTGRES_PW\")\n",
    "engine = create_engine(f'postgresql+psycopg2://postgres:{password}@127.0.0.1:5432/AQI_Data')\n",
    "query = \"\"\"\n",
    "SELECT time, location_id, pm2_5, pm10, co, no, no2, o3, so2, temperature, humidity\n",
    "FROM public.air_quality_data\n",
    "ORDER BY location_id, time ASC;\n",
    "\"\"\"\n",
    "df = pd.read_sql(query, engine)\n",
    "df['time'] = pd.to_datetime(df['time'], utc=True).dt.tz_convert(None)\n",
    "df.head()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "def calculate_sub_index(conc, breakpoints):\n",
    "    for bp in breakpoints:\n",
    "        if bp['c_low'] <= conc <= bp['c_high']:\n",
    "            return ((bp['i_high'] - bp['i_low']) / (bp['c_high'] - bp['c_low'])) * (conc - bp['c_low']) + bp['i_low']\n",
    "    return 500\n",
    "\n",
    "pm25_bp = [\n",
    "    {'c_low': 0, 'c_high': 30, 'i_low': 0, 'i_high': 50},\n",
    "    {'c_low': 30, 'c_high': 60, 'i_low': 51, 'i_high': 100},\n",
    "    {'c_low': 60, 'c_high': 90, 'i_low': 101, 'i_high': 200},\n",
    "    {'c_low': 90, 'c_high': 120, 'i_low': 201, 'i_high': 300},\n",
    "    {'c_low': 120, 'c_high': 250, 'i_low': 301, 'i_high': 400},\n",
    "    {'c_low': 250, 'c_high': 10000, 'i_low': 401, 'i_high': 500}\n",
    "]\n",
    "\n",
    "pm10_bp = [\n",
    "    {'c_low': 0, 'c_high': 50, 'i_low': 0, 'i_high': 50},\n",
    "    {'c_low': 50, 'c_high': 100, 'i_low': 51, 'i_high': 100},\n",
    "    {'c_low': 100, 'c_high': 250, 'i_low': 101, 'i_high': 200},\n",
    "    {'c_low': 250, 'c_high': 350, 'i_low': 201, 'i_high': 300},\n",
    "    {'c_low': 350, 'c_high': 430, 'i_low': 301, 'i_high': 400},\n",
    "    {'c_low': 430, 'c_high': 10000, 'i_low': 401, 'i_high': 500}\n",
    "]\n",
    "\n",
    "df['pm25_subi'] = df['pm2_5'].apply(lambda x: calculate_sub_index(x, pm25_bp))\n",
    "df['pm10_subi'] = df['pm10'].apply(lambda x: calculate_sub_index(x, pm10_bp))\n",
    "df['aqi'] = df[['pm25_subi', 'pm10_subi']].max(axis=1)\n",
    "\n",
    "df = df[df['aqi'] < 450]\n",
    "df['aqi'].describe()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "plt.figure(figsize=(10, 5))\n",
    "sns.histplot(df['aqi'], bins=50, kde=True, color='purple')\n",
    "plt.title('Distribution of AQI across Gwalior')\n",
    "plt.show()\n",
    "\n",
    "loc_1 = df[df['location_id'] == 1].sort_values('time')\n",
    "plt.figure(figsize=(14, 4))\n",
    "plt.plot(loc_1['time'][-720:], loc_1['aqi'][-720:])\n",
    "plt.title('AQI Trend over the last month for Location ID 1')\n",
    "plt.show()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "df.sort_values(by=['location_id', 'time'], inplace=True)\n",
    "df['hour'] = df['time'].dt.hour\n",
    "df['day_of_week'] = df['time'].dt.dayofweek\n",
    "df['month'] = df['time'].dt.month\n",
    "\n",
    "for lag in range(1, 25):\n",
    "    df[f'aqi_lag_{lag}'] = df.groupby('location_id')['aqi'].shift(lag)\n",
    "\n",
    "df['aqi_rolling_mean_6h'] = df.groupby('location_id')['aqi_lag_1'].transform(lambda x: x.rolling(window=6).mean())\n",
    "df['aqi_rolling_mean_24h'] = df.groupby('location_id')['aqi_lag_1'].transform(lambda x: x.rolling(window=24).mean())\n",
    "df['aqi_rolling_std_24h'] = df.groupby('location_id')['aqi_lag_1'].transform(lambda x: x.rolling(window=24).std())\n",
    "df.dropna(inplace=True)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "cutoff_date = df['time'].max() - pd.DateOffset(months=2)\n",
    "train_df = df[df['time'] < cutoff_date]\n",
    "test_df = df[df['time'] >= cutoff_date]\n",
    "\n",
    "features = [\n",
    "    'location_id', 'hour', 'day_of_week', 'month',\n",
    "    'aqi_rolling_mean_6h', 'aqi_rolling_mean_24h', 'aqi_rolling_std_24h', \n",
    "    'temperature', 'humidity'\n",
    "] + [f'aqi_lag_{i}' for i in range(1, 25)]\n",
    "\n",
    "X_train = train_df[features]\n",
    "y_train = train_df['aqi']\n",
    "X_test = test_df[features]\n",
    "y_test = test_df['aqi']\n",
    "\n",
    "model = XGBRegressor(n_estimators=300, learning_rate=0.05, max_depth=6, random_state=42, n_jobs=-1)\n",
    "model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=50)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "predictions = model.predict(X_test)\n",
    "rmse = np.sqrt(mean_squared_error(y_test, predictions))\n",
    "mae = mean_absolute_error(y_test, predictions)\n",
    "print(f\"Test RMSE: {rmse:.2f}\")\n",
    "print(f\"Test MAE:  {mae:.2f}\")\n",
    "\n",
    "with open('model.pkl', 'wb') as f:\n",
    "    pickle.dump(model, f)\n"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {"name": "ipython", "version": 3},
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.9.7"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}

with open('train.ipynb', 'w') as f:
    json.dump(notebook, f, indent=1)
