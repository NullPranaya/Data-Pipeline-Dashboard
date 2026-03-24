# Weather Data Pipeline Dashboard

A real-time weather data pipeline with an anomaly detection engine and a live web dashboard. It automatically fetches hourly weather data for 5 cities, stores it in PostgreSQL, flags statistical anomalies, and displays everything on an interactive dashboard.

---

## What It Does

- **Fetches** hourly weather data (temperature, humidity, wind speed) for 5 cities from the [Open-Meteo API](https://open-meteo.com/) — free, no API key required.
- **Stores** the data in a PostgreSQL database using an upsert so re-runs never create duplicates.
- **Detects anomalies** using a rolling z-score (|z| >= 2.5 over a 48-hour window) and logs them to the database.
- **Alerts** via Slack (optional) whenever an anomaly is detected.
- **Serves** a dark-themed Flask dashboard with Plotly charts that auto-refreshes every 60 seconds.

**Cities tracked:** New York City, Los Angeles, Chicago, London, Tokyo

---

## Project Structure

```
.
├── run.py           # Entry point — starts the scheduler + Flask server together
├── pipeline.py      # ETL logic: extract → transform → load
├── anomaly.py       # Z-score anomaly detection
├── alerts.py        # Slack alert sender
├── app.py           # Flask web server + REST API endpoints
├── config.py        # Database connection settings (edit this)
├── schema.sql       # SQL to create the database tables
├── requirements.txt # Python dependencies
└── templates/
    └── index.html   # Dashboard UI (Plotly + vanilla JS)
```

---

## Setup

### 1. Prerequisites

- Python 3.11+
- PostgreSQL running locally (default port 5432)

### 2. Create the database

```bash
psql -U postgres -c "CREATE DATABASE pipeline_db;"
psql -U postgres -d pipeline_db -f schema.sql
```

### 3. Configure database credentials

Edit `config.py` to match your PostgreSQL setup:

```python
DB = {
    "host": "localhost",
    "port": 5432,
    "dbname": "pipeline_db",
    "user": "postgres",
    "password": "your_password_here",
}
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. (Optional) Enable Slack alerts

Set the `SLACK_WEBHOOK_URL` environment variable to your Slack incoming webhook URL:

```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
```

If this variable is not set, anomalies are only printed to the console.

---

## Running

```bash
python run.py
```

This does two things at once:
1. Runs the pipeline immediately, then re-runs it every hour in the background.
2. Starts the Flask web server on `http://localhost:5050`.

Open `http://localhost:5050` in your browser to see the dashboard.

To stop, press `Ctrl+C`.

---

## Running the Pipeline Manually (without the server)

```bash
python pipeline.py
```

---

## Dashboard Features

| Section | Description |
|---|---|
| City cards | Latest temperature, humidity, and wind speed for each city. Click a card to drill into that city. |
| 24h trend chart | Multi-line chart showing temperature over the last 24 hours across all cities. |
| City detail chart | Temperature, humidity, and wind speed history for the selected city. |
| Anomaly log | Table of the 50 most recent anomalies with z-scores and timestamps. |

The dashboard auto-refreshes every 60 seconds.

---

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /api/current` | Latest reading per city |
| `GET /api/history/<city>` | Last 24h of hourly readings for one city |
| `GET /api/trends` | Last 24h data for all cities (used by the multi-line chart) |
| `GET /api/anomalies` | 50 most recent anomalies |

---

## Database Schema

**`weather_readings`** — one row per city per hour (upserted on conflict):

| Column | Type | Description |
|---|---|---|
| location | VARCHAR | City name |
| reading_time | TIMESTAMPTZ | Hour the reading is for |
| temperature_c | FLOAT | Temperature in Celsius |
| humidity_pct | FLOAT | Relative humidity % |
| wind_speed_kmh | FLOAT | Wind speed in km/h |

**`anomalies`** — one row per detected anomaly:

| Column | Type | Description |
|---|---|---|
| city | VARCHAR | City where anomaly was detected |
| metric | VARCHAR | Which metric (temperature, humidity, wind) |
| value | FLOAT | The anomalous value |
| z_score | FLOAT | How many std deviations from the mean |
| reading_time | TIMESTAMPTZ | When the reading occurred |
| detected_at | TIMESTAMPTZ | When the anomaly was logged |

---

## Tech Stack

- **Python** — pipeline, anomaly detection, scheduling
- **PostgreSQL** — data storage
- **Flask** — web server and REST API
- **Plotly.js** — interactive charts
- **NumPy** — z-score calculations
- **Open-Meteo API** — free weather data source (no key needed)
