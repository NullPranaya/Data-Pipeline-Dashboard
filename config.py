import os


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


DB = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": _env_int("DB_PORT", 5432),
    "dbname": os.getenv("DB_NAME", "pipeline_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}

APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = _env_int("APP_PORT", 5050)
DASHBOARD_REFRESH_SECONDS = _env_int("DASHBOARD_REFRESH_SECONDS", 60)
PIPELINE_INTERVAL_HOURS = _env_int("PIPELINE_INTERVAL_HOURS", 1)
