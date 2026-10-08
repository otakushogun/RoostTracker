# RoostTracker

A geospatial tool to use NOAA NEXRAD Level II data to find and visualize flock behavior.
The Kerr Lake alpha processes the August 11, 2026 KRAX radar hour, stores filtered gate
footprints and a weighted roost estimate in PostGIS, and serves them to a MapLibre PWA.

See [SETUP.md](SETUP.md) for Ubuntu/PostGIS installation, ingestion, and development
instructions.
