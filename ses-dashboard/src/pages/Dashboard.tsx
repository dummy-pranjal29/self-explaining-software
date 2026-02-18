import { useEffect, useState, useCallback } from "react";
import HealthGauge from "../components/HealthGauge";
import ExecutivePanel from "../components/ExecutivePanel";
import ForecastTimeline from "../components/ForecastTimeline/ForecastTimeline";
import LiveArchitectureGraph from "../components/LiveArchitectureGraph";
import ProjectSelector from "../components/ProjectSelector";
import AIChatPanel from "../components/AIChatPanel";

import { fetchForecast, fetchGraph, setProjectId } from "../services/api";

import type { ForecastResponse } from "../types/intelligence";
import type { GraphResponse } from "../types/intelligence";

export default function Dashboard() {
  const [forecastData, setForecastData] = useState<ForecastResponse | null>(
    null,
  );

  const [graphData, setGraphData] = useState<GraphResponse | null>(null);

  const [loadingGraph, setLoadingGraph] = useState(true);

  // Key to force refresh of health components when project changes
  const [healthRefreshKey, setHealthRefreshKey] = useState(0);

  // Function to fetch dashboard data
  const fetchDashboardData = useCallback(() => {
    // Reset data state
    setForecastData(null);
    setGraphData(null);
    setLoadingGraph(true);

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

  // Fetch data on mount - use ref to avoid lint warning
  const mounted = useCallback(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  useEffect(() => {
    mounted();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Handle project change from ProjectSelector
  const handleProjectChange = useCallback(
    (projectId?: string) => {
      // Update the global project ID for API calls
      if (projectId) {
        setProjectId(projectId);
      }
      // Force refresh of health components
      setHealthRefreshKey((prev) => prev + 1);
      // Fetch new data
      fetchDashboardData();
    },
    [fetchDashboardData],
  );

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 px-10 py-8">
      <div className="max-w-7xl mx-auto space-y-12">
        <header className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold tracking-tight">
            Self-Evolving Software
          </h1>
          <div className="flex items-center gap-4">
            <ProjectSelector onProjectChange={handleProjectChange} />
            <div className="text-sm text-neutral-500">
              Runtime Architecture Intelligence
            </div>
          </div>
        </header>

        {/* Health Overview */}
        <section className="grid grid-cols-1 xl:grid-cols-2 gap-8">
          <HealthGauge key={healthRefreshKey} />
          <ExecutivePanel key={healthRefreshKey + "exec"} />
        </section>

        {/* Live Architecture Graph */}
        <section>
          {loadingGraph ? (
            <div className="text-neutral-500">
              Loading architecture graph...
            </div>
          ) : graphData && graphData.nodes && graphData.nodes.length > 0 ? (
            <LiveArchitectureGraph data={graphData} />
          ) : (
            <div className="bg-slate-900 rounded-2xl p-8 shadow-xl border border-slate-800">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-white text-lg font-semibold">
                  Live Architecture Graph
                </h2>
              </div>
              <div className="h-[500px] flex items-center justify-center text-neutral-500">
                No architecture data available. Start tracing to see the graph.
              </div>
            </div>
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
              <div className="h-[280px] flex items-center justify-center text-neutral-500">
                No historical data available. Start tracing to see forecasts.
              </div>
            </div>
          )}
        </section>

        {/* AI Chat Panel */}
        <AIChatPanel />
      </div>
    </div>
  );
}
