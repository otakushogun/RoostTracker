import { useEffect, useRef, useState } from "react";
import { Map, NavigationControl } from "maplibre-gl";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const EMPTY_FRAME = { type: "FeatureCollection", features: [] };

function formatTime(timestamp) {
  return new Intl.DateTimeFormat("en-US", {
    hour: "numeric",
    minute: "2-digit",
    timeZone: "America/New_York",
    timeZoneName: "short",
  }).format(new Date(timestamp));
}

export default function App() {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const frameRef = useRef(EMPTY_FRAME);
  const centroidRef = useRef(null);
  const [scans, setScans] = useState([]);
  const [scanIndex, setScanIndex] = useState(0);
  const [frame, setFrame] = useState(EMPTY_FRAME);
  const [centroid, setCentroid] = useState(null);
  const [playing, setPlaying] = useState(false);
  const [error, setError] = useState("");
  const selectedScan = scans[scanIndex];

  useEffect(() => {
    let active = true;
    fetch(`${API_URL}/api/alpha/scans`)
      .then((response) => {
        if (!response.ok) throw new Error("Radar scans are unavailable.");
        return response.json();
      })
      .then((data) => {
        if (active) {
          setScans(data);
          if (data.length === 0) setError("No radar scans have been ingested yet.");
        }
      })
      .catch((reason) => active && setError(reason.message));

    fetch(`${API_URL}/api/alpha/roost`)
      .then((response) => (response.ok ? response.json() : null))
      .then((feature) => {
        if (active) {
          centroidRef.current = feature;
          setCentroid(feature);
        }
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!mapContainer.current || map.current) return undefined;

    map.current = new Map({
      container: mapContainer.current,
      style: "https://demotiles.maplibre.org/style.json",
      center: [-78.35, 36.55],
      zoom: 9,
      minZoom: 7,
      maxZoom: 15,
    });
    map.current.addControl(new NavigationControl(), "top-right");
    map.current.on("load", () => {
      map.current.addSource("radar", { type: "geojson", data: EMPTY_FRAME });
      map.current.addLayer({
        id: "bio-gates",
        type: "fill",
        source: "radar",
        paint: {
          "fill-color": [
            "interpolate",
            ["linear"],
            ["get", "reflectivity"],
            5,
            "#fde047",
            20,
            "#f97316",
            35,
            "#dc2626",
          ],
          "fill-opacity": 0.65,
          "fill-outline-color": "#7c2d12",
        },
      });
      map.current.getSource("radar").setData(frameRef.current);
      map.current.addSource("roost", {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
      });
      map.current.addLayer({
        id: "roost-point",
        type: "circle",
        source: "roost",
        paint: {
          "circle-radius": 9,
          "circle-color": "#2563eb",
          "circle-stroke-color": "#fff",
          "circle-stroke-width": 3,
        },
      });
      map.current.getSource("roost").setData({
        type: "FeatureCollection",
        features: centroidRef.current ? [centroidRef.current] : [],
      });
    });
    return () => {
      map.current?.remove();
      map.current = null;
    };
  }, []);

  useEffect(() => {
    if (!selectedScan) return undefined;
    let active = true;
    fetch(`${API_URL}/api/alpha/frame/${selectedScan.id}`)
      .then((response) => {
        if (!response.ok) throw new Error("Could not load this radar frame.");
        return response.json();
      })
      .then((data) => {
        if (active) {
          frameRef.current = data;
          setFrame(data);
        }
      })
      .catch((reason) => active && setError(reason.message));
    return () => {
      active = false;
    };
  }, [selectedScan]);

  useEffect(() => {
    const source = map.current?.getSource("radar");
    if (source) source.setData(frame);
  }, [frame]);

  useEffect(() => {
    const source = map.current?.getSource("roost");
    if (source) {
      source.setData({
        type: "FeatureCollection",
        features: centroid ? [centroid] : [],
      });
    }
  }, [centroid]);

  useEffect(() => {
    if (!playing || scans.length < 2) return undefined;
    const timer = window.setInterval(
      () => setScanIndex((index) => (index + 1) % scans.length),
      900,
    );
    return () => window.clearInterval(timer);
  }, [playing, scans.length]);

  return (
    <main className="flex min-h-screen flex-col bg-sky-50 text-slate-900">
      <header className="flex flex-wrap items-center justify-between gap-2 bg-sky-950 px-5 py-4 text-white">
        <div>
          <h1 className="text-xl font-bold">Kerr Lake Purple Martin Tracker</h1>
          <p className="text-sm text-sky-200">KRAX · August 11, 2026 · 6–7 AM EDT</p>
        </div>
        <p className="text-sm text-sky-200">Biological dual-pol gates · 0.5° sweep</p>
      </header>

      <section className="grid flex-1 grid-rows-[minmax(50vh,1fr)_auto]">
        <div ref={mapContainer} className="min-h-[50vh] w-full" aria-label="Radar map" />
        <div className="mx-auto w-full max-w-5xl space-y-3 p-5">
          <div className="flex flex-wrap items-center gap-3">
            <button
              className="rounded bg-sky-800 px-4 py-2 font-semibold text-white disabled:opacity-50"
              disabled={scans.length < 2}
              onClick={() => setPlaying((value) => !value)}
            >
              {playing ? "Pause" : "Play"}
            </button>
            <input
              className="min-w-48 flex-1 accent-sky-700"
              type="range"
              min="0"
              max={Math.max(0, scans.length - 1)}
              value={scanIndex}
              aria-label="Radar scan time"
              disabled={scans.length === 0}
              onChange={(event) => setScanIndex(Number(event.target.value))}
            />
            <span className="min-w-32 text-right font-medium">
              {selectedScan ? formatTime(selectedScan.timestamp) : "No scan selected"}
            </span>
          </div>
          <div className="flex justify-between text-sm text-slate-600">
            <span>{selectedScan?.bio_gate_count ?? 0} filtered gates</span>
            <span>{centroid ? "Roost emergence estimate available" : "Roost estimate pending"}</span>
          </div>
          {error && <p role="status" className="text-sm text-rose-700">{error}</p>}
        </div>
      </section>
    </main>
  );
}
