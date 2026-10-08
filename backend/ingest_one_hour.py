"""Download and filter the KRAX Level II volume data for the alpha test hour."""

from __future__ import annotations

import argparse
import math
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

STATION = "KRAX"
START_UTC = datetime(2026, 8, 11, 10, 0, tzinfo=timezone.utc)
END_UTC = datetime(2026, 8, 11, 11, 0, tzinfo=timezone.utc)
BOUNDING_BOX = (-78.6, 36.3, -78.1, 36.8)
RHOHV_RANGE = (0.35, 0.85)
ZDR_MIN = 2.0
REFLECTIVITY_RANGE = (5.0, 35.0)
GATE_SPACING_METERS = 250.0
SCAN_KEY_PATTERN = re.compile(r"KRAX(?P<date>\d{8})_(?P<time>\d{6})")


def scan_time_from_key(key: str) -> datetime | None:
    """Parse a Level II object key and return its UTC scan time."""
    match = SCAN_KEY_PATTERN.search(Path(key).name)
    if not match:
        return None
    return datetime.strptime(
        match.group("date") + match.group("time"), "%Y%m%d%H%M%S"
    ).replace(tzinfo=timezone.utc)


def biological_gate_mask(rhohv: Any, zdr: Any, reflectivity: Any) -> Any:
    import numpy as np

    rhohv = np.ma.filled(np.ma.asarray(rhohv, dtype=float), np.nan)
    zdr = np.ma.filled(np.ma.asarray(zdr, dtype=float), np.nan)
    reflectivity = np.ma.filled(np.ma.asarray(reflectivity, dtype=float), np.nan)
    return (
        (rhohv >= RHOHV_RANGE[0])
        & (rhohv <= RHOHV_RANGE[1])
        & (zdr >= ZDR_MIN)
        & (reflectivity >= REFLECTIVITY_RANGE[0])
        & (reflectivity <= REFLECTIVITY_RANGE[1])
        & np.isfinite(rhohv)
        & np.isfinite(zdr)
        & np.isfinite(reflectivity)
    )


def list_scan_objects(s3: Any) -> list[tuple[str, datetime]]:
    prefix = f"{START_UTC:%Y/%m/%d}/{STATION}/"
    paginator = s3.get_paginator("list_objects_v2")
    scans: list[tuple[str, datetime]] = []
    for page in paginator.paginate(Bucket="noaa-nexrad-level2", Prefix=prefix):
        for item in page.get("Contents", []):
            key = item["Key"]
            timestamp = scan_time_from_key(key)
            if timestamp is not None and START_UTC <= timestamp < END_UTC:
                scans.append((key, timestamp))
    return sorted(scans, key=lambda item: item[1])


def _gate_polygons(
    longitude: Iterable[float],
    latitude: Iterable[float],
    spacing_meters: float = GATE_SPACING_METERS,
) -> list[str | None]:
    """Build WGS84 gate footprints that intersect the alpha bbox."""
    west, south, east, north = BOUNDING_BOX
    polygons = []
    for lon, lat in zip(longitude, latitude):
        lat_delta = spacing_meters / 111_320.0 / 2
        lon_delta = lat_delta / max(math.cos(math.radians(lat)), 0.01)
        if (
            lon + lon_delta <= west
            or lon - lon_delta >= east
            or lat + lat_delta <= south
            or lat - lat_delta >= north
        ):
            polygons.append(None)
            continue
        coordinates = (
            (lon - lon_delta, lat - lat_delta),
            (lon + lon_delta, lat - lat_delta),
            (lon + lon_delta, lat + lat_delta),
            (lon - lon_delta, lat + lat_delta),
            (lon - lon_delta, lat - lat_delta),
        )
        polygons.append(
            "POLYGON(("
            + ", ".join(f"{x:.7f} {y:.7f}" for x, y in coordinates)
            + "))"
        )
    return polygons


def _database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL must be set before running ingestion")
    return url


def _insert_scan(connection: Any, key: str, scan_time: datetime, radar: Any) -> None:
    import numpy as np

    from pyart.config import get_field_name

    sweep = int(np.argmin(np.abs(radar.fixed_angle["data"] - 0.5)))
    reflectivity_field = get_field_name("reflectivity")
    zdr_field = get_field_name("differential_reflectivity")
    rhohv_field = get_field_name("cross_correlation_ratio")
    for field in (reflectivity_field, zdr_field, rhohv_field):
        if field not in radar.fields:
            raise ValueError(f"Required dual-pol field is missing: {field}")

    start = int(radar.sweep_start_ray_index["data"][sweep])
    end = int(radar.sweep_end_ray_index["data"][sweep]) + 1
    reflectivity = radar.fields[reflectivity_field]["data"][start:end]
    zdr = radar.fields[zdr_field]["data"][start:end]
    rhohv = radar.fields[rhohv_field]["data"][start:end]
    mask = biological_gate_mask(rhohv, zdr, reflectivity)

    gate_longitude, gate_latitude = radar.get_gate_longitude_latitude(sweep)
    longitudes = gate_longitude["data"]
    latitudes = gate_latitude["data"]
    gate_indices = np.argwhere(mask)
    selected_polygons = _gate_polygons(
        longitudes[mask].tolist(), latitudes[mask].tolist()
    )
    rows = []
    for (ray, gate), polygon in zip(gate_indices, selected_polygons):
        if polygon is not None:
            rows.append(
                (
                    float(reflectivity[ray, gate]),
                    float(zdr[ray, gate]),
                    float(rhohv[ray, gate]),
                    polygon,
                )
            )

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO radar_scans (station, scan_time, source_key, bio_gate_count)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (station, scan_time) DO UPDATE
            SET source_key = EXCLUDED.source_key,
                bio_gate_count = EXCLUDED.bio_gate_count
            RETURNING id
            """,
            (STATION, scan_time, key, len(rows)),
        )
        scan_id = cursor.fetchone()[0]
        cursor.execute("DELETE FROM bio_gates WHERE scan_id = %s", (scan_id,))
        if rows:
            west, south, east, north = BOUNDING_BOX
            cursor.executemany(
                """
                WITH footprint AS (
                    SELECT ST_SetSRID(ST_GeomFromText(%s), 4326) AS geom
                ), clipped AS (
                    SELECT ST_Intersection(
                        geom, ST_MakeEnvelope(%s, %s, %s, %s, 4326)
                    ) AS geom
                    FROM footprint
                )
                INSERT INTO bio_gates (scan_id, reflectivity, zdr, rhohv, geom)
                SELECT %s, %s, %s, %s, geom
                FROM clipped
                WHERE NOT ST_IsEmpty(geom) AND ST_Area(geom) > 0
                """,
                [
                    (
                        polygon,
                        west,
                        south,
                        east,
                        north,
                        scan_id,
                        reflectivity_value,
                        zdr_value,
                        rhohv_value,
                    )
                    for reflectivity_value, zdr_value, rhohv_value, polygon in rows
                ],
            )
    connection.commit()


def ingest() -> int:
    import boto3
    import pyart
    import psycopg
    from botocore import UNSIGNED
    from botocore.config import Config

    s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED))
    scans = list_scan_objects(s3)
    if not scans:
        raise RuntimeError(
            f"No {STATION} Level II scans found from {START_UTC.isoformat()} "
            f"through {END_UTC.isoformat()}"
        )

    inserted = 0
    with psycopg.connect(_database_url()) as connection, tempfile.TemporaryDirectory() as temp:
        for key, scan_time in scans:
            local_file = Path(temp) / Path(key).name
            s3.download_file("noaa-nexrad-level2", key, str(local_file))
            radar = pyart.io.read_nexrad_archive(str(local_file))
            _insert_scan(connection, key, scan_time, radar)
            inserted += 1
            local_file.unlink(missing_ok=True)
    return inserted


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    print(f"Ingested {ingest()} KRAX scans for the alpha test hour.")


if __name__ == "__main__":
    main()
