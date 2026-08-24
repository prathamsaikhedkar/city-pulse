# 💻 CityPulse Frontend Application

The CityPulse frontend is a modern, responsive Single Page Application (SPA) built with **React 19**, **Vite**, and **Material-UI (MUI v9)**, featuring interactive geospatial maps and multi-vector environmental visualizations.

---

## 🎨 Technology Highlights

- **Framework**: [React 19](https://react.dev)
- **Bundler & Tooling**: [Vite 8](https://vitejs.dev)
- **Component System & Theme**: [Material-UI (MUI v9)](https://mui.com) with Emotion styled components
- **Navigation**: [React Router v7](https://reactrouter.com)
- **Mapping**: [Leaflet 1.9.4](https://leafletjs.com) with CartoDB Voyager raster tiles
- **Data Visualizations**: [Chart.js](https://www.chartjs.org) with custom gradients and multi-axis configurations

---

## 📂 Component & Directory Structure

```text
frontend/src/
├── assets/
│   └── logo.png                 # CityPulse application logo
├── components/
│   ├── AQIChart.jsx             # Minimalist standalone AQI trend line chart
│   ├── CityMap.jsx              # Interactive Leaflet map with dynamic circle markers & popups
│   ├── DashboardAnalytics.jsx   # 6-chart analytical grid powered by Chart.js
│   ├── Layout.jsx               # Navigation bar, logo header, and route toggle controls
│   ├── LocationSelector.jsx     # Responsive sensor selector (horizontal bar on mobile / vertical drawer on desktop)
│   └── MetricCards.jsx          # Top summary cards (AQI status, PM2.5/PM10, Temp, Humidity)
├── mockData/
│   ├── data.json                # Sensor metadata backup
│   └── gwaliorData.js           # 15 Gwalior sensor coordinate objects & metadata
├── pages/
│   ├── Dashboard.jsx            # Live 72-hour air quality monitoring page
│   └── Forecasts.jsx            # 24-hour predictive AI forecasting page
├── api.js                       # Centralized API service for backend endpoints
├── App.css                      # Global layout & utility styling
├── App.jsx                      # App root component with MUI ThemeProvider & React Router
├── index.css                    # Base CSS variables & resets
├── main.jsx                     # Application bootstrap entry point
└── theme.js                     # MUI theme configuration (typography, shadows, palettes)
```

---

## 🖥️ Views & Pages

### 1. Live Dashboard (`/dashboard`)
- **Metric Summary Cards**: Shows real-time AQI badge with color-coded severity (*Good*, *Moderate*, *Poor*, *Severe*), particulate concentration ($\text{PM}_{2.5} / \text{PM}_{10}$), ambient temperature, and humidity.
- **View Toggle**: Switch seamlessly between **Map** and **Analytics**.
- **Geographic Map View**: Displays all 15 monitoring stations on a CartoDB basemap. Station markers are sized and colored by current AQI, with click-to-view popups.
- **Analytics Grid**:
  1. *AQI Trend* (24-hour historical line chart with gradient fill)
  2. *Pollutant Profile* (Polar area chart of $\text{PM}_{2.5}$, $\text{PM}_{10}$, $\text{NO}_2$, $\text{SO}_2$, $\text{O}_3$, $\text{CO}$)
  3. *Climatological Matrix* (Dual-axis 48-hour Temperature vs. Humidity line chart)
  4. *AQI Distribution* (Doughnut chart of 72-hour air quality categories)
  5. *Trace Gas Stack* (Stacked bar chart of trace gases $\text{NO}_2$, $\text{SO}_2$, $\text{O}_3$)
  6. *Diurnal Pattern* (Hourly average AQI distribution across the day)

### 2. AI Forecast View (`/forecasts`)
- **Visual Theme**: Indigo-violet color scheme with glowing gradient banner.
- **Forecast Heatmap**: Visualizes the predicted AQI for the very next projection hour across all 15 stations.
- **24-Hour Projection Chart**: Smooth spline line chart projecting hourly AQI progression over the next 24 hours.

---

## 🛠️ Development & Build Commands

### Prerequisites
- Node.js `18.0.0+`
- npm `9.0.0+`

### Installation
```bash
cd frontend
npm install
```

### Run Local Development Server
```bash
npm run dev
```
Accessible at `http://localhost:5173`.

### Build for Production
```bash
npm run build
```
Creates an optimized static bundle in `dist/`.

### Preview Production Build
```bash
npm run preview
```

### Run Linter
```bash
npm run lint
```

---

## ⚙️ Environment Configuration

Set the backend API connection in `frontend/.env.local`:

```ini
# Backend API Base URL
VITE_API_URL=http://localhost:8000
```
