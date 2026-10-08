const test = require("node:test");
const assert = require("node:assert");
const P = require("../web/playback.js");

const scans = [
  { time_utc: "2026-08-12T09:30:00Z", status: "available" },
  { time_utc: "2026-08-12T09:35:00Z", status: "missing" },
  { time_utc: "2026-08-13T09:30:00Z", status: "available" },
];

test("15 fps interval", () => {
  assert.strictEqual(P.DISPLAY_FPS, 15);
  assert.ok(Math.abs(P.frameIntervalMs(15) - 66.6667) < 0.01);
  assert.throws(() => P.frameIntervalMs(0));
});
test("nextIndex steps one scan per frame, stops or loops at end", () => {
  assert.strictEqual(P.nextIndex(0, 3, false), 1);
  assert.strictEqual(P.nextIndex(2, 3, false), 2);
  assert.strictEqual(P.nextIndex(2, 3, true), 0);
  assert.strictEqual(P.nextIndex(0, 0, true), -1);
});
test("clampIndex", () => {
  assert.strictEqual(P.clampIndex(-5, 3), 0);
  assert.strictEqual(P.clampIndex(9, 3), 2);
});
test("date selection", () => {
  assert.deepStrictEqual(P.datesOf(scans), ["2026-08-12", "2026-08-13"]);
  assert.strictEqual(P.selectDate(scans, "2026-08-12").length, 2);
  assert.strictEqual(P.selectDate(scans, "").length, 3);
});
test("gaps and missing counts use real timestamps", () => {
  assert.strictEqual(P.minutesBetween(scans[0], scans[1]), 5);
  assert.strictEqual(P.countMissing(scans), 1);
  assert.strictEqual(P.formatTime(scans[0]), "2026-08-12 09:30:00 UTC");
});
