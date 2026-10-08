# Event manifest contract (schema_version "1")

One JSON file per event (`<event-id>.json`), plus `events.json` listing events (`{"events":[{id,title,synthetic,manifest}]}`).
Validated by `roosttracker.manifest.validate_manifest`. Ingest adapters (NOAA, other radars/sources) should
*produce* this format; the viewer and API only consume it, so no vendor library is required downstream.

| Field | Meaning |
|---|---|
| `schema_version` | Must be `"1"`. |
| `synthetic` | `true` for fixtures. Synthetic manifests must set `event.verification` to `"synthetic"`. |
| `event.id` | Lowercase slug `[a-z0-9][a-z0-9-]{0,63}`. |
| `event.title`, `event.radar_site` | Display title; radar site ID (e.g. `KRAX`). |
| `event.verification` | Free-text status, e.g. `synthetic`, `unverified`, `reviewed`. Never imply verification that has not happened. |
| `display.playback_fps` | Display frames per second (15). This is *playback* rate, unrelated to radar sampling. |
| `display.bounds` | `[west, south, east, north]` in WGS84 degrees for the frame images. |
| `processing` | Object: `name`, `version`, `config` (fields, thresholds, color scale) used to make assets. |
| `provenance` | Object: `sources` (list of source scan/file identities, citations, licences) and statements. |
| `scans[]` | Strictly increasing by `time_utc`. |
| `scans[].id` | Unique ID (for real data: source object key / file name). |
| `scans[].time_utc` | Actual scan time, ISO-8601 with timezone. Never rewritten to a regular grid. |
| `scans[].status` | `available` or `missing`. |
| `scans[].asset` | Display asset path relative to the data dir; required if available, forbidden if missing. |
| `scans[].source` | Object identifying the source (required if available), e.g. `{kind, uri, checksum}`. |
| `scans[].fields` | Radar fields rendered (e.g. `reflectivity`). |

Missing scans are listed explicitly (when an expected scan is known to be absent) and rendered as "NO SCAN DATA";
the viewer never repeats or interpolates frames to fill them.

Planned (not implemented) layers: eBird hotspot/observation context. It is context only, not proof of species
identity or roost location.
