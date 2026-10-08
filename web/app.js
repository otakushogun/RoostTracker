(function () {
  "use strict";
  // Static data location. Override with ?data=<relative url>/ (e.g. when assets are generated elsewhere).
  const DATA = new URLSearchParams(location.search).get("data") || "demo/";
  const $ = (id) => document.getElementById(id);
  const P = window.Playback;
  let manifest = null, scans = [], idx = 0, timer = null;

  async function getJSON(u) {
    const r = await fetch(u);
    if (!r.ok) throw new Error(u + ": HTTP " + r.status);
    return r.json();
  }
  function stop() { if (timer) { clearInterval(timer); timer = null; } $("play").textContent = "▶ Play"; }
  function play() {
    if (timer || !scans.length) return;
    if (idx >= scans.length - 1) idx = 0;
    $("play").textContent = "⏸ Pause";
    timer = setInterval(() => {
      const n = P.nextIndex(idx, scans.length, false);
      if (n === idx) { stop(); return; }
      show(n);
    }, P.frameIntervalMs(manifest.display.playback_fps || P.DISPLAY_FPS));
  }
  function show(i) {
    idx = P.clampIndex(i, scans.length);
    const s = scans[idx];
    $("slider").value = idx;
    $("time").textContent = P.formatTime(s);
    $("pos").textContent = (idx + 1) + "/" + scans.length;
    const miss = s.status === "missing";
    $("missing").hidden = !miss;
    $("img").style.visibility = miss ? "hidden" : "visible";
    if (!miss) $("img").src = DATA + s.asset;
    let st = miss ? "MISSING scan" : "";
    if (idx > 0) st += (st ? " · " : "") + P.minutesBetween(scans[idx - 1], s).toFixed(1) + " min since previous listed scan";
    $("status").textContent = st;
  }
  function loadDate() {
    stop();
    scans = P.selectDate(manifest.scans, $("date").value);
    $("slider").max = Math.max(scans.length - 1, 0);
    show(0);
  }
  async function loadEvent(entry) {
    stop();
    manifest = await getJSON(DATA + entry.manifest);
    const b = $("banner");
    b.textContent = manifest.synthetic
      ? "SYNTHETIC DEMO FIXTURE – not NOAA data. The Aug 2026 Kerr Lake event is not verified here."
      : manifest.event.title + " – verification: " + manifest.event.verification;
    b.className = "banner" + (manifest.synthetic ? "" : " real");
    const dates = P.datesOf(manifest.scans);
    $("date").innerHTML = dates.map((d) => `<option>${d}</option>`).join("");
    const miss = P.countMissing(manifest.scans);
    $("meta").textContent = `Radar ${manifest.event.radar_site} · ${manifest.scans.length} listed scans, ${miss} missing · processing ${manifest.processing.name} ${manifest.processing.version || ""}`;
    loadDate();
  }
  async function init() {
    try {
      const index = await getJSON(DATA + "events.json");
      $("event").innerHTML = index.events.map((e, i) => `<option value="${i}"></option>`).join("");
      index.events.forEach((e, i) => { $("event").options[i].textContent = e.title; });
      $("event").onchange = () => loadEvent(index.events[$("event").value]);
      await loadEvent(index.events[0]);
    } catch (e) { $("banner").textContent = "Failed to load data: " + e.message; }
  }
  $("play").onclick = () => (timer ? stop() : play());
  $("prev").onclick = () => { stop(); show(idx - 1); };
  $("next").onclick = () => { stop(); show(idx + 1); };
  $("slider").oninput = (e) => { stop(); show(+e.target.value); };
  $("date").onchange = loadDate;
  init();
})();
