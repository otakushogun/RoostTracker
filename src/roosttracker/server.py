"""Tiny read-only JSON API (stdlib only). Binds to localhost by default.

GET /api/health, /api/events, /api/events/<id>/manifest
Configuration comes from the environment (see .env.example).
"""
from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .manifest import ID_RE, ManifestError, validate_manifest


def load_manifest(data_dir: Path, event_id: str) -> dict | None:
    if not ID_RE.match(event_id):
        return None
    path = data_dir / f"{event_id}.json"
    if not path.is_file():
        return None
    m = json.loads(path.read_text())
    validate_manifest(m)
    return m


def list_events(data_dir: Path) -> list[dict]:
    out = []
    for path in sorted(data_dir.glob("*.json")):
        if path.name == "events.json" or not ID_RE.match(path.stem):
            continue
        try:
            m = json.loads(path.read_text())
            validate_manifest(m)
        except (ValueError, OSError):
            continue
        out.append({"id": m["event"]["id"], "title": m["event"]["title"],
                    "synthetic": m["synthetic"], "manifest": path.name})
    return out


def route(data_dir: Path, path: str) -> tuple[int, dict]:
    path = path.split("?", 1)[0].rstrip("/")
    if path == "/api/health":
        return 200, {"status": "ok"}
    if path == "/api/events":
        return 200, {"events": list_events(data_dir)}
    parts = path.split("/")
    if len(parts) == 5 and parts[:3] == ["", "api", "events"] and parts[4] == "manifest":
        try:
            m = load_manifest(data_dir, parts[3])
        except (ManifestError, ValueError):
            return 500, {"error": "invalid manifest on server"}
        return (200, m) if m else (404, {"error": "not found"})
    return 404, {"error": "not found"}


def make_handler(data_dir: Path):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            status, body = route(data_dir, self.path)
            raw = json.dumps(body).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

    return Handler


def main() -> None:
    host = os.environ.get("ROOSTTRACKER_HOST", "127.0.0.1")
    port = int(os.environ.get("ROOSTTRACKER_PORT", "8765"))
    data_dir = Path(os.environ.get("ROOSTTRACKER_DATA_DIR", "web/demo")).resolve()
    server = ThreadingHTTPServer((host, port), make_handler(data_dir))
    print(f"RoostTracker API on http://{host}:{port} (data: {data_dir})")
    server.serve_forever()


if __name__ == "__main__":
    main()
