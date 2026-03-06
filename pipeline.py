import requests
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timezone

import config

API_URL = "https://api.open-meteo.com/v1/forecast"
LOCATION = "New York City"
LATITUDE = 40.7128
LONGITUDE = -74.0060


# --- EXTRACT ---

def extract():
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m",
        "timezone": "America/New_York",
        "forecast_days": 1,
    }
    response = requests.get(API_URL, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    print(f"[extract] Fetched {len(data['hourly']['time'])} hourly records.")
    return data


# --- TRANSFORM ---

def transform(raw: dict) -> list[dict]:
    hourly = raw["hourly"]
    records = []

    for time_str, temp, humidity, wind in zip(
        hourly["time"],
        hourly["temperature_2m"],
        hourly["relative_humidity_2m"],
        hourly["wind_speed_10m"],
    ):
        records.append({
            "location": LOCATION,
            "latitude": raw["latitude"],
            "longitude": raw["longitude"],
            "reading_time": time_str,
            "temperature_c": temp,
            "humidity_pct": humidity,
            "wind_speed_kmh": wind,
            "fetched_at": datetime.now(timezone.utc),
        })

    print(f"[transform] Transformed {len(records)} records.")
    return records


# --- LOAD ---

def load(records: list[dict]):
    conn = psycopg2.connect(**config.DB)
    try:
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
        print(f"[load] Inserted/updated {len(records)} records.")
    finally:
        conn.close()


# --- PIPELINE ---

def run():
    print(f"\n[pipeline] Starting run at {datetime.now(timezone.utc).isoformat()}")
    raw = extract()
    records = transform(raw)
    load(records)
    print("[pipeline] Done.")


if __name__ == "__main__":
    run()