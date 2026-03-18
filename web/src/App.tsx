import React, { useState } from "react";
import { TimeTraveler } from "./components/TimeTraveler.tsx";
import { ParameterExplorer } from "./components/ParameterExplorer.tsx";
import { PlayableUniverse } from "./components/PlayableUniverse.tsx";
import { AnomalyMap } from "./components/AnomalyMap.tsx";

type Tab = "timeline" | "explorer" | "playable" | "anomalies";

export function App() {
  const [tab, setTab] = useState<Tab>("timeline");

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <header style={{
        padding: "16px 32px",
        background: "linear-gradient(135deg, #0d1117 0%, #161b22 100%)",
        borderBottom: "1px solid #30363d",
        display: "flex",
        alignItems: "center",
        gap: 24,
      }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, letterSpacing: 2 }}>
          ARCHEON <span style={{ color: "#58a6ff", fontWeight: 400 }}>Observatory</span>
        </h1>
        <nav style={{ display: "flex", gap: 4, marginLeft: 32 }}>
          {([
            ["timeline", "Cosmic Time Machine"],
            ["explorer", "Parameter Explorer"],
            ["playable", "Playable Universe"],
            ["anomalies", "Anomaly Map"],
          ] as const).map(([id, label]) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              style={{
                padding: "8px 16px",
                borderRadius: 6,
                border: "none",
                background: tab === id ? "#1f6feb" : "transparent",
                color: tab === id ? "#fff" : "#8b949e",
                cursor: "pointer",
                fontSize: 14,
                fontWeight: tab === id ? 600 : 400,
                transition: "all 0.15s",
              }}
            >
              {label}
            </button>
          ))}
        </nav>
      </header>

      <main style={{ flex: 1, padding: 32 }}>
        {tab === "timeline" && <TimeTraveler />}
        {tab === "explorer" && <ParameterExplorer />}
        {tab === "playable" && <PlayableUniverse />}
        {tab === "anomalies" && <AnomalyMap />}
      </main>
    </div>
  );
}
