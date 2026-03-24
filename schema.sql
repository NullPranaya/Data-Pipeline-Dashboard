CREATE TABLE IF NOT EXISTS weather_readings (
    id              SERIAL PRIMARY KEY,
    location        VARCHAR(100)  NOT NULL,
    latitude        FLOAT         NOT NULL,
    longitude       FLOAT         NOT NULL,
    reading_time    TIMESTAMPTZ   NOT NULL,
    temperature_c   FLOAT,
    humidity_pct    FLOAT,
    wind_speed_kmh  FLOAT,
    fetched_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    UNIQUE (location, reading_time)
);

CREATE TABLE IF NOT EXISTS anomalies (
    id          SERIAL PRIMARY KEY,
    city        VARCHAR(100)  NOT NULL,
    metric      VARCHAR(50)   NOT NULL,
    value       FLOAT         NOT NULL,
    z_score     FLOAT         NOT NULL,
    reading_time TIMESTAMPTZ  NOT NULL,
    detected_at TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);