import { useEffect, useState } from "react";
import HealthGauge from "../components/HealthGauge";
import ExecutivePanel from "../components/ExecutivePanel";
import ForecastTimeline from "../components/ForecastTimeline/ForecastTimeline";
import LiveArchitectureGraph from "../components/LiveArchitectureGraph";

import { fetchForecast, fetchGraph } from "../services/api";

import type { ForecastResponse } from "../types/intelligence";
import type { GraphResponse } from "../types/intelligence";

export default function Dashboard() {
  const [forecastData, setForecastData] = useState<ForecastResponse | null>(
    null,
  );

  const [graphData, setGraphData] = useState<GraphResponse | null>(null);

  const [loadingGraph, setLoadingGraph] = useState(true);

  useEffect(() => {
    // Fetch forecast
    fetchForecast()
      .then((res) => {
        setForecastData(res.data);
      })
      .catch((err) => {
        console.error("Forecast fetch failed:", err);
      });

    // Fetch graph
    fetchGraph()
      .then((res) => {
        setGraphData(res.data);
      })
      .catch((err) => {
        console.error("Graph fetch failed:", err);
      })
      .finally(() => {
        setLoadingGraph(false);
      });
  }, []);

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 px-10 py-8">
      <div className="max-w-7xl mx-auto space-y-12">
        <header className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold tracking-tight">
            Self-Evolving Software
          </h1>
          <div className="text-sm text-neutral-500">
            Runtime Architecture Intelligence
          </div>
        </header>

        {/* Health Overview */}
        <section className="grid grid-cols-1 xl:grid-cols-2 gap-8">
          <HealthGauge />
          <ExecutivePanel />
        </section>

        {/* Live Architecture Graph */}
        <section>
          {loadingGraph ? (
            <div className="text-neutral-500">
              Loading architecture graph...
            </div>
          ) : graphData ? (
            <LiveArchitectureGraph data={graphData} />
          ) : (
            <div className="text-red-500">Failed to load graph.</div>
          )}
        </section>

        {/* Forecast Section */}
        <section>
          {forecastData ? (
            <ForecastTimeline data={forecastData} />
          ) : (
            <div className="text-neutral-500">Loading forecast...</div>
          )}
        </section>
      </div>
    </div>
  );
}
