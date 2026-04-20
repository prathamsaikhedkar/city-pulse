# Software Requirements Specification (SRS)
## CityPulse: A Modern City Dashboard App

---

## 1. Introduction

### 1.1 Purpose
The purpose of this Software Requirements Specification (SRS) is to provide a comprehensive description of the CityPulse web application. It outlines the intended functionality, external interfaces, performance constraints, and other vital criteria that govern the application. This document serves as the foundational agreement between the developers and stakeholders, specifically covering the MVP scope consisting of an Air Quality Dashboard with 24-hour forecasting.

### 1.2 Document Conventions
This document follows the IEEE 830-1998 standard conventions for SRS documentation. 
*   **Must / Shall**: Indicates a mandatory requirement.
*   **Should / May**: Indicates a desirable, but optional, requirement.
*   **TBD**: To Be Determined. Denotes areas where specific metrics or values are pending stakeholder approval.

### 1.3 Intended Audience and Reading Suggestions
This document is intended for:
*   **Software Developers**: To grasp exactly what needs to be built across frontend, backend, and machine learning components.
*   **Data Scientists**: To realize the requirements for integrating the predictive XGBoost models into the infrastructure.
*   **Project Stakeholders**: To maintain project focus and verify that end goals align with business requirements.

It is suggested to read the document sequentially, starting with the Product Scope and Overall Description, before diving into the specific Functional Interfaces.

### 1.4 Product Scope
CityPulse is a comprehensive urban dashboard application designed to give users real-time and predictive insights into city-wide metrics. The MVP phase specifically targets Air Quality Index (AQI) monitoring and prediction for the city of **Gwalior**.

The product will seamlessly fetch real-time atmospheric data, visualize it using geographic heatmaps and time-series charts across 15 distinct districts of Gwalior, and provide a 24-hour predictive forecast using a trained Machine Learning model. The goal is to inform citizens, urban planners, and environmental stakeholders regarding city health.

### 1.5 References
1. IEEE Std 830-1998, Recommended Practice for Software Requirements Specifications.
2. `CityPulse.md` - Primary Project Instruction Manual.
3. OpenWeatherMap API Documentation: [https://openweathermap.org/api](https://openweathermap.org/api)

---

## 2. Overall Description

### 2.1 Product Perspective
CityPulse is an independent web-based application. Its architecture is divided into a client-server model:
*   **Frontend**: A responsive Single Page Application (SPA) built using React.
*   **Backend**: A Python-based FastAPI web server handling localized routing, ML model inference, and external API polling.
*   **Database**: A PostgreSQL relational database holding historical AQI data mapped to precise geographic coordinates.

### 2.2 Product Functions
*   **Real-time Data Aggregation:** Fetch and store AQI metrics via external APIs.
*   **Interactive Visualization:** Render city-wide metrics on an interactive map.
*   **Sub-Region Filtering:** Segregate mapping and chart data for 15 distinct areas of Gwalior.
*   **Predictive Forecasting:** Serve 24-hour AQI predictions using pre-trained regression models.

### 2.3 User Classes and Characteristics
*   **General Citizens:** Users looking to check current air quality or forecast to plan daily activities. They require an intuitive, fast, and visually clean interface (mobile and desktop).
*   **System Administrators:** [TBD: Describe admin privileges if administration portals are added in the future].

### 2.4 Operating Environment
*   **Client**: Any modern web browser (Google Chrome v90+, Firefox v88+, Safari v14+).
*   **Server**: Host machine capable of running Python 3.9+ and PostgreSQL 18.
*   **Database**: PostgreSQL 18 natively installed on the server operating system.

### 2.5 Design and Implementation Constraints
*   The application must use **Vite + React** for the UI.
*   Charts and maps must utilize **CDN** injections of `Chart.js` and `Leaflet.js` to minimize initial bundle loading.
*   Overall themes must rely dynamically on light-mode Material-UI (MUI) constraints.
*   The system heavily relies on the OpenWeatherMap API; rate limits and uptime dictate real-time data flow.

### 2.6 Assumptions and Dependencies
*   **Assumption**: The selected ML Model (`model.pkl` - XGBoost) provides acceptable accuracy when supplied with historical PostgreSQL data logs.
*   **Dependency**: Continuous, reliable internet connection for both the backend (to poll OpenWeatherMap) and the frontend clients.
*   **Dependency**: Google Maps / OpenStreetMap active tile layers for Leaflet rendering.

---

## 3. External Interface Requirements

### 3.1 User Interfaces
*   **Dashboard Layout:** Clean interface comprising an App Bar, an actionable drawer/sidebar, and a main content pane displaying metrics.
*   **Cartography View:** A central map view must center on Gwalior (Lat: 26.218, Lng: 78.182). Circular indicator markers must shift color on a spectrum (Green to Purple) corresponding immediately to their measured AQI.
*   **Chart View:** Time-series line chart updating contextually upon user cross-interaction with the map.

### 3.2 Hardware Interfaces
No specific hardware interfaces are required aside from standard server allocation (CPU/RAM sizing [TBD: Define Hardware limits based on model memory]).

### 3.3 Software Interfaces
*   **PostgreSQL**: Connected over port `5432` utilizing the `psycopg2` or equivalent Python SQLAlchemy engines.
*   **External APIs**: Requires external outbound network interface connectivity to `api.openweathermap.org` via HTTPS (Port 443).
*   **Frontend-Backend Communication**: RESTful HTTP requests using standard JSON bodies.

### 3.4 Communications Interfaces
*   All communication between the React Frontend and the FastAPI Backend shall transfer encrypted via standard HTTPS standard protocols in production.

---

## 4. System Features

### 4.1 Real-Time Air Quality Fetching
**4.1.1 Description**: The backend server must routinely poll the OpenWeatherMap API to update localized metrics for the 15 designated Gwalior zones.
**4.1.2 Stimulus/Response**: 
*   *Stimulus*: Internal server cron-job or asynchronous schedule.
*   *Response*: Ingests JSON, serializes arrays, and executes `INSERT` algorithms into the `air_quality_data` PostgreSQL table.

### 4.2 Interactive Heatmap Application
**4.1.1 Description**: The frontend utilizes Leaflet maps spanning Gwalior limits.
**4.1.2 Functional Requirements**: 
*   System must map 15 exact coordinate bounds accurately.
*   Markers must scale or style-shift prominently upon selection.

### 4.3 24-Hour ML Forecasting
**4.3.1 Description**: Inference serving of `model.pkl` via the FastAPI endpoint.
**4.3.2 Functional Requirements**: 
*   The backend must accept requests specifying a `location_id`.
*   The backend invokes the XGBoost model by piping in the previous 24-to-48 hour parameters.
*   Output shall return a JSON payload formatted identically to standard historical data, tagged with future timestamps.

---

## 5. Other Nonfunctional Requirements

### 5.1 Performance Requirements
*   **Page Load:** The initial React SPA must render the dashboard skeleton in under [TBD: e.g., 2.0 seconds] on a 4G network.
*   **Inference Latency:** The FastAPI endpoint predicting the AQI shall respond in under [TBD: e.g., 500 milliseconds].
*   **DB Transactions:** Must sustain indexing algorithms efficiently for high-read scenarios against the `idx_location_time` B-tree index.

### 5.2 Security Requirements
*   The application must isolate environment variables such as `.env` API keys (e.g., `AQI_API_KEY_1`, `POSTGRES_PW`). Under no circumstances is the Postgres PW or Weather API key passed directly to the client bundle.
*   [TBD: Standard OAuth2 or JWT implementation if user accounts are added in future iterations].

### 5.3 Software Quality Attributes
*   **Maintainability**: Ensure modular component structure in React (`src/components/`, `src/pages/`) for swift iterative testing.
*   **Extensibility**: The dashboard infrastructure allows for easy inclusion of secondary datasets (Traffic, Sound Quality) in late-stage development cycles post-MVP.

## 6. Glossary
*   **AQI:** Air Quality Index.
*   **MVP:** Minimum Viable Product.
*   **SPA:** Single Page Application.
*   **MUI:** Material-User Interface, a React UI standardization framework.
