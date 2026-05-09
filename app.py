from flask import Flask, jsonify, render_template
import psycopg2
import psycopg2.extras

import config

app = Flask(__name__)


def get_conn():
    return psycopg2.connect(**config.DB)


@app.route("/")
def index():
    return render_template(
        "index.html",
        refresh_seconds=config.DASHBOARD_REFRESH_SECONDS,
    )


@app.route("/health")
def health():
    """Lightweight health check for the app and database connection."""
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        return jsonify({"status": "ok", "database": "connected"}), 200
    except psycopg2.Error as exc:
        return jsonify({"status": "degraded", "database": "unavailable", "error": str(exc)}), 503
    finally:
        if conn is not None:
            conn.close()


@app.route("/api/current")
def api_current():
    """Latest reading per city."""
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT DISTINCT ON (location)
                    location, temperature_c, humidity_pct, wind_speed_kmh, reading_time
                FROM weather_readings
                ORDER BY location, reading_time DESC
                """
            )
            rows = cur.fetchall()
    finally:
        conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/history/<city>")
def api_history(city):
    """Last 24 h of hourly readings for one city."""
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT reading_time, temperature_c, humidity_pct, wind_speed_kmh
                FROM weather_readings
                WHERE location = %s
                  AND reading_time >= NOW() - INTERVAL '24 hours'
                ORDER BY reading_time
                """,
                (city,),
            )
            rows = cur.fetchall()
    finally:
        conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/trends")
def api_trends():
    """Last 24 h temperature for all cities — for the multi-line chart."""
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT location, reading_time, temperature_c, humidity_pct, wind_speed_kmh
                FROM weather_readings
                WHERE reading_time >= NOW() - INTERVAL '24 hours'
                ORDER BY location, reading_time
                """
            )
            rows = cur.fetchall()
    finally:
        conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/anomalies")
def api_anomalies():
    """50 most recent anomalies."""
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT city, metric, value, z_score, reading_time, detected_at
                FROM anomalies
                ORDER BY detected_at DESC
                LIMIT 50
                """
            )
            rows = cur.fetchall()
    finally:
        conn.close()
    return jsonify([dict(r) for r in rows])


if __name__ == "__main__":
    app.run(host=config.APP_HOST, port=config.APP_PORT, debug=True)
