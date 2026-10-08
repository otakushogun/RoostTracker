# RoostTracker alpha setup

This alpha processes the KRAX Level II scans from **August 11, 2026, 10:00–11:00 UTC**
(6:00–7:00 AM EDT). Only the first 0.5° sweep is used. The biological gate filter is
`0.35 <= RHOHV <= 0.85`, `ZDR >= 2 dB`, and `5 <= reflectivity <= 35 dBZ`.
Gate footprints are clipped to longitude -78.6 to -78.1 and latitude 36.3 to 36.8.

## PostgreSQL and PostGIS

On Ubuntu 24.04, install PostgreSQL and PostGIS with apt:

```bash
sudo apt-get update
sudo apt-get install -y postgresql postgresql-contrib postgis postgresql-16-postgis-3
sudo -u postgres createuser --pwprompt roosttracker
sudo -u postgres createdb --owner=roosttracker roosttracker
```

Set the connection environment for the following commands:

```bash
cp .env.example .env
# Replace `change-me` in .env with the password set during database user creation.
set -a
source .env
set +a
```

Initialize the schema (the script enables PostGIS in the selected database):

```bash
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f backend/db/init.sql
```

## Python backend and ingestion

Python 3.10+ is required. `arm_pyart` and NumPy handle Level II volume processing;
S3 access uses unsigned public requests. The compressed radar files are downloaded
to a temporary directory and removed after processing.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m backend.ingest_one_hour
python -m backend.roost_locator
```

The ingest script is intentionally fixed to the alpha-test hour and station. It is
safe to rerun: scans are upserted and their prior gate rows replaced. The locator
selects the earliest scan with filtered gates from 10:15 through 10:30 UTC and stores
a reflectivity-intensity-weighted center. It prints a message and exits without
writing a centroid if no eligible scan exists.

## API and frontend

In one terminal, start the API with the same `DATABASE_URL`:

```bash
source .venv/bin/activate
set -a
source .env
set +a
uvicorn backend.api:app --reload
```

In another terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open <http://localhost:5173>. The map displays scan footprints and the stored roost
point; use Play or the slider to navigate the available scans. The API is available
at <http://localhost:8000>:

- `GET /api/alpha/scans` — alpha-hour scan IDs and timestamps
- `GET /api/alpha/frame/{scan_id}` — a GeoJSON FeatureCollection of filtered gates
- `GET /api/alpha/roost` — the stored roost point (404 until a centroid is available)

The Vite PWA plugin generates the service worker and precaches the built app shell.
The basemap style is hosted by MapLibre's public demo tiles, so map backgrounds still
require network access when offline. For a deployed frontend, set `VITE_API_URL`
before `npm run build` to the reachable API origin and set `FRONTEND_ORIGINS` on the
API to the frontend's origin (comma-separated when there are multiple origins).
