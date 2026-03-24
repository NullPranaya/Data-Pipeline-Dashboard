import os
import requests

# Set SLACK_WEBHOOK_URL in your environment to enable Slack alerts.
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")

METRIC_LABELS = {
    "temperature_c":  ("Temperature", "°C"),
    "humidity_pct":   ("Humidity", "%"),
    "wind_speed_kmh": ("Wind Speed", "km/h"),
}


def send_alert(anomaly: dict):
    label, unit = METRIC_LABELS.get(anomaly["metric"], (anomaly["metric"], ""))
    direction = "spike" if anomaly["z_score"] > 0 else "drop"
    msg = (
        f"[ANOMALY] {anomaly['city']} — {label} {direction}: "
        f"{anomaly['value']:.1f}{unit} (z={anomaly['z_score']:+.2f}) "
        f"at {anomaly['reading_time']}"
    )
    print(f"[alert] {msg}")

    if SLACK_WEBHOOK_URL:
        try:
            requests.post(
                SLACK_WEBHOOK_URL,
                json={"text": msg},
                timeout=5,
            )
        except Exception as e:
            print(f"[alert] Slack delivery failed: {e}")
