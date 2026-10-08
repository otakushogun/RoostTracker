import copy
import json
from pathlib import Path

import pytest

from roosttracker import demo
from roosttracker.manifest import ManifestError, validate_manifest


@pytest.fixture
def good(tmp_path):
    return demo.build(tmp_path)


def test_demo_manifest_valid_and_labeled_synthetic(good):
    validate_manifest(good)
    assert good["synthetic"] is True
    assert good["event"]["verification"] == "synthetic"
    assert good["display"]["playback_fps"] == 15


def test_demo_has_explicit_missing_scans_without_assets(good):
    missing = [s for s in good["scans"] if s["status"] == "missing"]
    assert missing and all("asset" not in s for s in missing)


def test_committed_fixture_is_valid():
    p = Path(__file__).parent.parent / "web/demo/kerr-lake-demo.json"
    validate_manifest(json.loads(p.read_text()))


@pytest.mark.parametrize("mutate,msg", [
    (lambda m: m.update(schema_version="2"), "schema_version"),
    (lambda m: m["scans"][1].update(time_utc=m["scans"][0]["time_utc"]), "increasing"),
    (lambda m: m["scans"][0].update(time_utc="2026-08-12T09:30:00"), "timezone"),
    (lambda m: m["scans"][0].pop("asset"), "asset is required"),
    (lambda m: m["scans"][14].update(asset="x.svg"), "absent for missing"),
    (lambda m: m["display"].update(playback_fps=0), "playback_fps"),
    (lambda m: m["display"].update(bounds=[1, 1, 0, 0]), "bounds"),
    (lambda m: m["event"].update(verification="verified"), "synthetic"),
    (lambda m: m.update(scans=[]), "scans"),
    (lambda m: m["scans"][1].update(id=m["scans"][0]["id"]), "duplicated"),
])
def test_invalid_manifests_rejected(good, mutate, msg):
    m = copy.deepcopy(good)
    mutate(m)
    with pytest.raises(ManifestError) as e:
        validate_manifest(m)
    assert msg in str(e.value)
