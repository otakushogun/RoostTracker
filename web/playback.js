// Pure playback/selection helpers (no DOM). Works in browsers and Node (tests).
(function (root) {
  "use strict";
  const DISPLAY_FPS = 15;

  function frameIntervalMs(fps) {
    if (!(fps > 0)) throw new Error("fps must be positive");
    return 1000 / fps;
  }
  // Each display frame shows exactly one scan entry (no interpolation or holding).
  function nextIndex(i, n, loop) {
    if (n <= 0) return -1;
    if (i + 1 < n) return i + 1;
    return loop ? 0 : i;
  }
  function clampIndex(i, n) {
    if (n <= 0) return -1;
    return Math.min(Math.max(i, 0), n - 1);
  }
  function utcDate(scan) { return scan.time_utc.slice(0, 10); }
  function datesOf(scans) {
    return Array.from(new Set(scans.map(utcDate))).sort();
  }
  function selectDate(scans, date) {
    return date ? scans.filter((s) => utcDate(s) === date) : scans.slice();
  }
  function minutesBetween(a, b) {
    return (Date.parse(b.time_utc) - Date.parse(a.time_utc)) / 60000;
  }
  function countMissing(scans) {
    return scans.filter((s) => s.status === "missing").length;
  }
  function formatTime(scan) {
    const d = new Date(scan.time_utc);
    return d.toISOString().replace("T", " ").replace(".000Z", " UTC");
  }
  const api = { DISPLAY_FPS, frameIntervalMs, nextIndex, clampIndex, utcDate,
                datesOf, selectDate, minutesBetween, countMissing, formatTime };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.Playback = api;
})(typeof self !== "undefined" ? self : this);
