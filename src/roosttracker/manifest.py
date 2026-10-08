"""Event manifest contract and validation. See docs/manifest.md.

Deliberately independent of any radar/vendor library: ingest adapters produce
manifests; this module only checks the structure.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

SCHEMA_VERSION = "1"
SCAN_STATUSES = ("available", "missing")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


class ManifestError(ValueError):
    """Raised with all problems found in a manifest."""

    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__("; ".join(problems))


def parse_utc(value: Any) -> datetime:
    """Parse an ISO-8601 timestamp that must carry an explicit UTC offset."""
    if not isinstance(value, str):
        raise ValueError("timestamp must be a string")
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("timestamp must include a timezone (use Z for UTC)")
    return dt.astimezone(timezone.utc)


def validate_manifest(m: Any) -> None:
    """Raise ManifestError if the manifest violates the contract."""
    p: list[str] = []
    if not isinstance(m, dict):
        raise ManifestError(["manifest must be an object"])
    if m.get("schema_version") != SCHEMA_VERSION:
        p.append(f"schema_version must be {SCHEMA_VERSION!r}")
    if not isinstance(m.get("synthetic"), bool):
        p.append("synthetic must be a boolean")

    ev = m.get("event")
    if not isinstance(ev, dict):
        p.append("event must be an object")
    else:
        if not (isinstance(ev.get("id"), str) and ID_RE.match(ev["id"])):
            p.append("event.id must match [a-z0-9][a-z0-9-]{0,63}")
        for k in ("title", "radar_site", "verification"):
            if not isinstance(ev.get(k), str) or not ev.get(k):
                p.append(f"event.{k} must be a non-empty string")
        if m.get("synthetic") is True and ev.get("verification") != "synthetic":
            p.append("synthetic manifests must have event.verification == 'synthetic'")

    disp = m.get("display")
    if not isinstance(disp, dict):
        p.append("display must be an object")
    else:
        fps = disp.get("playback_fps")
        if not isinstance(fps, (int, float)) or isinstance(fps, bool) or fps <= 0:
            p.append("display.playback_fps must be a positive number")
        b = disp.get("bounds")
        if not (isinstance(b, list) and len(b) == 4 and all(isinstance(x, (int, float)) for x in b)):
            p.append("display.bounds must be [west, south, east, north]")
        elif not (b[0] < b[2] and b[1] < b[3]):
            p.append("display.bounds must satisfy west<east and south<north")

    if not isinstance(m.get("processing"), dict):
        p.append("processing must be an object")
    if not isinstance(m.get("provenance"), dict):
        p.append("provenance must be an object")

    scans = m.get("scans")
    if not isinstance(scans, list) or not scans:
        p.append("scans must be a non-empty list")
    else:
        prev = None
        seen: set[str] = set()
        for i, s in enumerate(scans):
            w = f"scans[{i}]"
            if not isinstance(s, dict):
                p.append(f"{w} must be an object")
                continue
            sid = s.get("id")
            if not isinstance(sid, str) or not sid:
                p.append(f"{w}.id must be a non-empty string")
            elif sid in seen:
                p.append(f"{w}.id {sid!r} is duplicated")
            else:
                seen.add(sid)
            try:
                t = parse_utc(s.get("time_utc"))
                if prev is not None and t <= prev:
                    p.append(f"{w}.time_utc must be strictly increasing")
                prev = t
            except ValueError as e:
                p.append(f"{w}.time_utc invalid: {e}")
            status = s.get("status")
            if status not in SCAN_STATUSES:
                p.append(f"{w}.status must be one of {SCAN_STATUSES}")
            elif status == "available":
                if not s.get("asset") or not isinstance(s.get("asset"), str):
                    p.append(f"{w}.asset is required for available scans")
                if not isinstance(s.get("source"), dict):
                    p.append(f"{w}.source is required for available scans")
            elif s.get("asset"):
                p.append(f"{w}.asset must be absent for missing scans")
    if p:
        raise ManifestError(p)
