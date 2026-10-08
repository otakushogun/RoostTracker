"""Estimate and store the first dual-pol gate centroid during emergence."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import os


def locate_roost() -> int | None:
    import psycopg

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL must be set before locating a roost")

    window_start = datetime(2026, 8, 11, 10, 15, tzinfo=timezone.utc)
    window_end = window_start + timedelta(minutes=15)
    with psycopg.connect(database_url) as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT s.id
            FROM radar_scans AS s
            WHERE s.station = 'KRAX'
              AND s.scan_time >= %s
              AND s.scan_time <= %s
              AND EXISTS (SELECT 1 FROM bio_gates AS g WHERE g.scan_id = s.id)
            ORDER BY s.scan_time
            LIMIT 1
            """,
            (window_start, window_end),
        )
        result = cursor.fetchone()
        if result is None:
            return None

        scan_id = result[0]
        cursor.execute(
            """
            WITH weighted AS (
                SELECT
                    SUM(ST_X(ST_Centroid(geom)) * POWER(10.0, reflectivity / 10.0))
                        / SUM(POWER(10.0, reflectivity / 10.0)) AS longitude,
                    SUM(ST_Y(ST_Centroid(geom)) * POWER(10.0, reflectivity / 10.0))
                        / SUM(POWER(10.0, reflectivity / 10.0)) AS latitude
                FROM bio_gates
                WHERE scan_id = %s
            )
            INSERT INTO roost_centroids (scan_id, geom)
            SELECT %s, ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
            FROM weighted
            WHERE longitude IS NOT NULL AND latitude IS NOT NULL
            ON CONFLICT (scan_id) DO UPDATE SET geom = EXCLUDED.geom
            """,
            (scan_id, scan_id),
        )
        connection.commit()
        return scan_id


if __name__ == "__main__":
    scan_id = locate_roost()
    if scan_id is None:
        print("No biological gates found between 10:15 and 10:30 UTC.")
    else:
        print(f"Stored reflectivity-weighted roost centroid for scan {scan_id}.")
