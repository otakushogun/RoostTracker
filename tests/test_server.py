from roosttracker import demo
from roosttracker.server import route


def test_routes(tmp_path):
    demo.build(tmp_path)
    assert route(tmp_path, "/api/health") == (200, {"status": "ok"})
    s, body = route(tmp_path, "/api/events")
    assert s == 200 and body["events"][0]["id"] == demo.EVENT_ID
    s, body = route(tmp_path, f"/api/events/{demo.EVENT_ID}/manifest")
    assert s == 200 and body["synthetic"] is True
    assert route(tmp_path, "/api/events/nope/manifest")[0] == 404
    assert route(tmp_path, "/api/events/..%2Fx/manifest")[0] == 404
    assert route(tmp_path, "/api/events/../manifest")[0] == 404
