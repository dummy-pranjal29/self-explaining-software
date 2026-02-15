import { useEffect, useState } from "react";
import HealthGauge from "../components/HealthGauge";
import ExecutivePanel from "../components/ExecutivePanel";
import ForecastTimeline from "../components/ForecastTimeline/ForecastTimeline";
import LiveArchitectureGraph from "../components/LiveArchitectureGraph";
import ProjectSelector from "../components/ProjectSelector";

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
          <div className="flex items-center gap-4">
            <ProjectSelector />
            <div className="text-sm text-neutral-500">
              Runtime Architecture Intelligence
            </div>
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
            <div className="relative bg-gradient-to-b from-neutral-900 to-neutral-950 border border-neutral-800 rounded-3xl p-8 space-y-8">
              <div className="flex justify-between items-start">
                <div>
                  <h2 className="text-sm tracking-wide text-neutral-400 uppercase">
                    Health Forecast
                  </h2>
                  <p className="text-xs text-neutral-500 mt-1">
                    Predictive trajectory with uncertainty modeling
                  </p>
                </div>
              </div>
              <div className="h-[420px] flex items-center justify-center text-neutral-500">
                No historical data available. Start tracing to see forecasts.
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
