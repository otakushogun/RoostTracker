CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS radar_scans (
    id BIGSERIAL PRIMARY KEY,
    station VARCHAR(4) NOT NULL,
    scan_time TIMESTAMPTZ NOT NULL,
    source_key TEXT NOT NULL,
    bio_gate_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (station, scan_time)
);

CREATE TABLE IF NOT EXISTS bio_gates (
    id BIGSERIAL PRIMARY KEY,
    scan_id BIGINT NOT NULL REFERENCES radar_scans(id) ON DELETE CASCADE,
    reflectivity DOUBLE PRECISION NOT NULL,
    zdr DOUBLE PRECISION NOT NULL,
    rhohv DOUBLE PRECISION NOT NULL,
    geom geometry(Polygon, 4326) NOT NULL
);

CREATE INDEX IF NOT EXISTS bio_gates_geom_gix ON bio_gates USING GIST (geom);
CREATE INDEX IF NOT EXISTS bio_gates_scan_id_idx ON bio_gates (scan_id);

CREATE TABLE IF NOT EXISTS roost_centroids (
    id BIGSERIAL PRIMARY KEY,
    scan_id BIGINT NOT NULL UNIQUE REFERENCES radar_scans(id) ON DELETE CASCADE,
    geom geometry(Point, 4326) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS roost_centroids_geom_gix ON roost_centroids USING GIST (geom);
