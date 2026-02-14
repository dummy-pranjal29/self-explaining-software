import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { fetchHealth } from "../services/api";

interface HealthResponse {
  timestamp: string;
  health_score: number;
  stability_index: number;
  risk_label: string;
  confidence: number;
}

export default function HealthGauge() {
  const [data, setData] = useState<HealthResponse | null>(null);

  useEffect(() => {
    fetchHealth()
      .then((res) => {
        setData(res.data as HealthResponse);
      })
      .catch((err) => {
        console.error("Health fetch failed:", err);
      });
  }, []);

  if (!data) {
    return (
      <div className="bg-slate-900 p-8 rounded-2xl border border-slate-800">
        Loading...
      </div>
    );
  }

  const score = data.health_score;

  const color =
    score >= 80
      ? "text-emerald-400"
      : score >= 60
        ? "text-yellow-400"
        : "text-red-500";

  return (
    <div className="bg-slate-900 p-8 rounded-2xl border border-slate-800">
      <h2 className="text-lg text-gray-400 mb-6">Architecture Health</h2>

      <motion.div
        key={score}
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.4 }}
        className={`text-6xl font-bold ${color}`}
      >
        {score}
      </motion.div>

      <div className="mt-6 space-y-2 text-sm text-gray-400">
        <div>Stability Index: {data.stability_index}</div>
        <div>Risk Level: {data.risk_label}</div>
        <div>Confidence: {data.confidence}</div>
      </div>
    </div>
  );
}
