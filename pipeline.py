import requests
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timezone

import config
from anomaly import detect_and_store_anomalies

API_URL = "https://api.open-meteo.com/v1/forecast"

CITIES = {
    "New York City": {"latitude": 40.7128,  "longitude": -74.0060},
    "Los Angeles":   {"latitude": 34.0522,  "longitude": -118.2437},
    "Chicago":       {"latitude": 41.8781,  "longitude": -87.6298},
    "London":        {"latitude": 51.5074,  "longitude": -0.1278},
    "Tokyo":         {"latitude": 35.6762,  "longitude": 139.6503},
}


# --- EXTRACT ---

def extract(city: str, lat: float, lon: float) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m",
        "timezone": "auto",
        "forecast_days": 1,
    }
    response = requests.get(API_URL, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    data["_city"] = city
    print(f"[extract] {city}: fetched {len(data['hourly']['time'])} hourly records.")
    return data


# --- TRANSFORM ---

def transform(raw: dict) -> list[dict]:
    hourly = raw["hourly"]
    city = raw["_city"]
    records = []

    for time_str, temp, humidity, wind in zip(
        hourly["time"],
        hourly["temperature_2m"],
        hourly["relative_humidity_2m"],
        hourly["wind_speed_10m"],
    ):
        records.append({
            "location":       city,
            "latitude":       raw["latitude"],
            "longitude":      raw["longitude"],
            "reading_time":   time_str,
            "temperature_c":  temp,
            "humidity_pct":   humidity,
            "wind_speed_kmh": wind,
            "fetched_at":     datetime.now(timezone.utc),
        })

    print(f"[transform] {city}: transformed {len(records)} records.")
    return records


# --- LOAD ---

def load(records: list[dict], conn) -> list[dict]:
    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO weather_readings
                (location, latitude, longitude, reading_time,
                 temperature_c, humidity_pct, wind_speed_kmh, fetched_at)
            VALUES %s
            ON CONFLICT (location, reading_time) DO UPDATE SET
                temperature_c  = EXCLUDED.temperature_c,
                humidity_pct   = EXCLUDED.humidity_pct,
                wind_speed_kmh = EXCLUDED.wind_speed_kmh,
                fetched_at     = EXCLUDED.fetched_at
            """,
            [
                (
                    r["location"], r["latitude"], r["longitude"],
                    r["reading_time"], r["temperature_c"],
                    r["humidity_pct"], r["wind_speed_kmh"], r["fetched_at"],
                )
                for r in records
            ],
        )
    conn.commit()
    print(f"[load] {records[0]['location']}: inserted/updated {len(records)} records.")
    return records


# --- PIPELINE ---

def run():
    print(f"\n[pipeline] Starting run at {datetime.now(timezone.utc).isoformat()}")
    conn = psycopg2.connect(**config.DB)
    try:
        for city, coords in CITIES.items():
            try:
                raw = extract(city, coords["latitude"], coords["longitude"])
                records = transform(raw)
                load(records, conn)
                detect_and_store_anomalies(city, records, conn)
            except Exception as e:
                print(f"[pipeline] ERROR for {city}: {e}")
    finally:
        conn.close()
    print("[pipeline] Done.\n")


if __name__ == "__main__":
    run()