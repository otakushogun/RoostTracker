"""FastAPI endpoints for the KRAX alpha-test radar hour."""

from __future__ import annotations

import os
from datetime import timezone
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from backend.database import get_engine
from backend.ingest_one_hour import END_UTC, START_UTC

app = FastAPI(title="RoostTracker Alpha API")
allowed_origins = os.getenv(
    "FRONTEND_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins if origin.strip()],
    allow_methods=["GET"],
    allow_headers=["*"],
)


def _connection() -> Any:
    if not os.getenv("DATABASE_URL"):
        raise HTTPException(status_code=503, detail="DATABASE_URL is not configured")
    try:
        return get_engine()
    except (SQLAlchemyError, RuntimeError) as error:
        raise HTTPException(status_code=503, detail="Radar database is unavailable") from error


@app.get("/api/alpha/scans")
def scans() -> list[dict[str, Any]]:
    with _connection().connect() as connection:
        result = connection.execute(
            text(
                """
            SELECT id, scan_time, bio_gate_count
            FROM radar_scans
            WHERE station = 'KRAX' AND scan_time >= :start AND scan_time < :end
            ORDER BY scan_time
            """
            ),
            {"start": START_UTC, "end": END_UTC},
        )
        return [
            {
                "id": row.id,
                "timestamp": row.scan_time.astimezone(timezone.utc).isoformat(),
                "bio_gate_count": row.bio_gate_count,
            }
            for row in result
        ]


@app.get("/api/alpha/frame/{scan_id}")
def frame(scan_id: int) -> dict[str, Any]:
    with _connection().connect() as connection:
        result = connection.execute(
            text(
                """
            SELECT json_build_object(
                'type', 'FeatureCollection',
                'features', COALESCE(json_agg(json_build_object(
                    'type', 'Feature',
                    'geometry', ST_AsGeoJSON(geom)::json,
                    'properties', json_build_object(
                        'reflectivity', reflectivity,
                        'zdr', zdr,
                        'rhohv', rhohv
                    )
                )), '[]'::json)
            )
            FROM bio_gates
            WHERE scan_id = :scan_id
            """
            ),
            {"scan_id": scan_id},
        )
        return result.fetchone()[0]


@app.get("/api/alpha/roost")
def roost() -> dict[str, Any]:
    with _connection().connect() as connection:
        result = connection.execute(
            text(
                """
            SELECT json_build_object(
                'type', 'Feature',
                'geometry', ST_AsGeoJSON(c.geom)::json,
                'properties', json_build_object(
                    'scan_id', c.scan_id,
                    'timestamp', s.scan_time
                )
            )
            FROM roost_centroids AS c
            JOIN radar_scans AS s ON s.id = c.scan_id
            WHERE s.station = 'KRAX'
              AND s.scan_time >= :start AND s.scan_time < :end
            ORDER BY s.scan_time
            LIMIT 1
            """
            ),
            {"start": START_UTC, "end": END_UTC},
        ).fetchone()
        if result is None:
            raise HTTPException(status_code=404, detail="Roost centroid is not available")
        return result[0]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
