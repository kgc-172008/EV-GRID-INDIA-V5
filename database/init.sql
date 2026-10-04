CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS vehicle_registrations (
    id BIGSERIAL PRIMARY KEY,
    state TEXT NOT NULL,
    district TEXT NOT NULL,
    year INTEGER NOT NULL,
    ev_count DOUBLE PRECISION NOT NULL,
    population DOUBLE PRECISION NOT NULL,
    road_score DOUBLE PRECISION DEFAULT 50,
    activity_score DOUBLE PRECISION DEFAULT 50,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    source TEXT DEFAULT 'DEMO/SYNTHETIC',
    retrieved_on DATE
);

CREATE TABLE IF NOT EXISTS chargers (
    id BIGSERIAL PRIMARY KEY,
    charger_id TEXT UNIQUE NOT NULL,
    state TEXT NOT NULL,
    district TEXT NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    operator TEXT DEFAULT 'DEMO',
    status TEXT DEFAULT 'UNKNOWN',
    total_connectors INTEGER DEFAULT 1,
    available_connectors INTEGER DEFAULT 0,
    charging_connectors INTEGER DEFAULT 0,
    reserved_connectors INTEGER DEFAULT 0,
    faulted_connectors INTEGER DEFAULT 0,
    source TEXT DEFAULT 'DEMO/SYNTHETIC',
    retrieved_on DATE
);

CREATE INDEX IF NOT EXISTS idx_vehicle_geo
ON vehicle_registrations USING GIST (
    ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
);

CREATE INDEX IF NOT EXISTS idx_charger_geo
ON chargers USING GIST (
    ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
);
