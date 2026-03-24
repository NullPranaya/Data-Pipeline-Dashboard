import numpy as np
import psycopg2
from datetime import datetime, timezone

from alerts import send_alert

METRICS = ["temperature_c", "humidity_pct", "wind_speed_kmh"]
Z_THRESHOLD = 2.5
HISTORY_HOURS = 48  # rolling window for baseline


def _fetch_history(city: str, conn) -> dict:
    """Pull last HISTORY_HOURS of readings for this city."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT temperature_c, humidity_pct, wind_speed_kmh
            FROM weather_readings
            WHERE location = %s
              AND reading_time >= NOW() - INTERVAL '%s hours'
            ORDER BY reading_time
            """,
            (city, HISTORY_HOURS),
        )
        rows = cur.fetchall()

    history = {"temperature_c": [], "humidity_pct": [], "wind_speed_kmh": []}
    for temp, hum, wind in rows:
        if temp is not None:
            history["temperature_c"].append(temp)
        if hum is not None:
            history["humidity_pct"].append(hum)
        if wind is not None:
            history["wind_speed_kmh"].append(wind)
    return history


def _z_score(value: float, population: list[float]) -> float | None:
    if len(population) < 5:
        return None
    arr = np.array(population)
    std = arr.std()
    if std == 0:
        return None
    return float((value - arr.mean()) / std)


def detect_and_store_anomalies(city: str, records: list[dict], conn):
    history = _fetch_history(city, conn)
    anomalies_found = []

    for record in records:
        for metric in METRICS:
            value = record.get(metric)
            if value is None:
                continue
            z = _z_score(value, history[metric])
            if z is not None and abs(z) >= Z_THRESHOLD:
                anomaly = {
                    "city":         city,
                    "metric":       metric,
                    "value":        value,
                    "z_score":      z,
                    "reading_time": record["reading_time"],
                }
                anomalies_found.append(anomaly)
                history[metric].append(value)  # update rolling window

    if not anomalies_found:
        return

    with conn.cursor() as cur:
        for a in anomalies_found:
            cur.execute(
                """
                INSERT INTO anomalies (city, metric, value, z_score, reading_time)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (a["city"], a["metric"], a["value"], a["z_score"], a["reading_time"]),
            )
    conn.commit()

    print(f"[anomaly] {city}: {len(anomalies_found)} anomalies detected.")
    for a in anomalies_found:
        send_alert(a)
