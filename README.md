# RoostTracker

Replay a dawn bird roost/swarming event on radar, with real scan timestamps. First target: Purple Martin
roost dispersal around Kerr Lake, NC, using NOAA NEXRAD Level II data from the Raleigh/Durham radar (likely **KRAX**),
reportedly visible ~Aug 11–19, 2026 around daybreak.

> **Status: starter MVP.** Only a clearly labeled **synthetic demo** exists. **No NOAA data has been downloaded or
> verified.** That the Aug 2026 event appears in KRAX scans, and that Kerr Lake is well covered by the radar beam
> geometry, are **unconfirmed** and must be checked (archive inventory + coverage) in the real-data milestone.

## MVP scope
- Static browser viewer: event and date (UTC) selection, play/pause, prev/next, timeline slider, visible scan timestamp,
  **15 display fps** playback, missing-scan indicator.
- Event manifest contract ([docs/manifest.md](docs/manifest.md)) for scan identity, radar site, timestamps, fields,
  processing config/version, display assets and provenance.
- Small stdlib-only Python API (`/api/health`, `/api/events`, `/api/events/<id>/manifest`), localhost by default.
- Synthetic demo fixture generator.

**Not implemented:** NOAA ingest/rendering, eBird integration, PostgreSQL, candidate detection, scientific validation,
other species/radars. No biological classification is made or implied.

## Architecture
```
ingest adapters (future) ─▶ precomputed frames + manifest.json (outside git) ─▶ static viewer (web/)
                                                                └▶ optional API (src/roosttracker/server.py)
```
Adapters (NOAA, eBird…) are meant to be replaceable and only need to emit the manifest contract; the viewer/API
know nothing about vendor libraries (e.g. Py-ART). `web/playback.js` holds the pure playback/selection logic.

**15 fps is display playback, not radar sampling.** Each display frame shows one real scan; scans are minutes apart.
Real times are preserved and shown; gaps show "NO SCAN DATA" and are never filled or interpolated.

## Local run
```
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
roosttracker-demo                 # regenerate web/demo (committed fixture, already present)
python -m http.server -d web 8000 # viewer at http://localhost:8000/
roosttracker-api                  # optional API at http://127.0.0.1:8765/api/events
```
Config via environment (see `.env.example`); no secrets in the frontend.

## Tests
```
python -m pytest -q               # manifest validation + API routes
node --test tests/playback.test.js  # playback/selection logic (Node 18+)
```

## Deployment outline (`/roosttracker/`)
Nothing here touches any server. Suggested: copy `web/` (plus generated real data, kept out of git) to a
`roosttracker/` directory under the static site root; run the API on `127.0.0.1` under systemd with an env file;
reverse-proxy `/roosttracker/api/` to it. See `deploy/` for **examples only** — review against the real Nginx layout.
Do not expose PostgreSQL publicly; if used later, give RoostTracker its own database/least-privilege user.
Keep raw radar files and credentials outside the web root and out of git (`data/` is ignored).

## Data and provenance caveats
- Demo imagery is synthetic and carries no observations; don't cite it as evidence.
- Real NOAA data: record source object keys, scan times, fields, processing version; follow NOAA citation guidance;
  don't commit raw/large files.
- Radar echoes can include weather, insects and other birds; a dawn ring is only suggestive of roost departure.
- eBird (later): context only — not proof of species or exact roost location; keep API keys server-side, attribute,
  and respect eBird terms.

## Roadmap
1. Confirm KRAX archive inventory/coverage over Kerr Lake for the dates; define "daybreak" window.
2. NOAA ingest adapter + frame renderer for one morning; fixed color scale; manifest with real provenance.
3. Extend to Aug 11–19; per-day comparison.
4. eBird hotspot/observation context layer (server-side).
5. Optional candidate annotations with manual review and documented false positives.
6. Other species/radar sites via event configuration.
