import React from "react";
import { createRoot } from "react-dom/client";
import mapLibreStyles from "maplibre-gl/dist/maplibre-gl.css?url";
import { useRegisterSW } from "virtual:pwa-register/react";
import App from "./App.jsx";
import "./style.css";

const mapStyleSheet = document.createElement("link");
mapStyleSheet.rel = "stylesheet";
mapStyleSheet.href = mapLibreStyles;
document.head.append(mapStyleSheet);

function Root() {
  const { offlineReady, needRefresh, updateServiceWorker } = useRegisterSW();

  return (
    <>
      {(offlineReady || needRefresh) && (
        <div className="fixed bottom-4 left-4 z-10 rounded-lg bg-slate-900 p-3 text-sm text-white shadow-lg">
          <span>{offlineReady ? "App ready to use offline." : "An update is ready."}</span>
          {needRefresh && (
            <button
              className="ml-3 font-semibold underline"
              onClick={() => updateServiceWorker(true)}
            >
              Reload
            </button>
          )}
        </div>
      )}
      <App />
    </>
  );
}

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <Root />
  </React.StrictMode>,
);
