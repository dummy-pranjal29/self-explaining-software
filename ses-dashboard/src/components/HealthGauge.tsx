import { useEffect, useState } from "react";
import { motion, useMotionValue, useTransform, animate } from "framer-motion";
import { fetchHealth } from "../services/api";
import type { HealthResponse } from "../types/intelligence";

const RADIUS = 90;
const STROKE = 14;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

export default function HealthGauge() {
  const [data, setData] = useState<HealthResponse | null>(null);
  const progress = useMotionValue(0);

  useEffect(() => {
    fetchHealth()
      .then((res) => {
        const health = res.data as HealthResponse;
        setData(health);

        // Use architecture_health_score from API or fall back to health_score
        const score =
          health.architecture_health_score ?? health.health_score ?? 0;
        animate(progress, score, {
          duration: 1.2,
          ease: "easeOut",
        });
      })
      .catch((err) => {
        console.error("Health fetch failed:", err);
      });
  }, []);

  const strokeDashoffset = useTransform(
    progress,
    (value) => CIRCUMFERENCE - (value / 100) * CIRCUMFERENCE,
  );

  if (!data) {
    return (
      <div className="bg-neutral-900 p-10 rounded-3xl border border-neutral-800 animate-pulse h-[320px]" />
    );
  }

  const riskColorMap: Record<string, string> = {
    LOW: "#10b981",
    MODERATE: "#f59e0b",
    HIGH: "#f97316",
    CRITICAL: "#ef4444",
  };

  const color = riskColorMap[data.risk_label ?? ""] ?? "#6366f1";

  // Calculate gradient colors based on health score
  const healthScore = data.architecture_health_score ?? data.health_score ?? 0;
  const getGradientColors = () => {
    if (healthScore >= 80) {
      return { start: "#10b981", end: "#059669" }; // Green
    } else if (healthScore >= 60) {
      return { start: "#22c55e", end: "#eab308" }; // Green to Yellow
    } else if (healthScore >= 40) {
      return { start: "#f59e0b", end: "#f97316" }; // Yellow to Orange
    } else {
      return { start: "#ef4444", end: "#dc2626" }; // Red
    }
  };
  const gradientColors = getGradientColors();

  return (
    <div className="bg-neutral-900 p-10 rounded-3xl border border-neutral-800 relative overflow-hidden">
      <div className="flex justify-between items-start mb-6">
        <h2 className="text-sm tracking-wide text-neutral-400">
          Architecture Health
        </h2>
        <span
          className="text-xs px-3 py-1 rounded-full border"
          style={{
            borderColor: color,
            color,
          }}
        >
          {data.risk_label}
        </span>
      </div>

      <div className="flex items-center justify-center relative">
        <svg width="240" height="240">
          <defs>
            <linearGradient
              id="healthGradient"
              x1="0%"
              y1="0%"
              x2="100%"
              y2="0%"
            >
              <stop offset="0%" stopColor={gradientColors.start} />
              <stop offset="100%" stopColor={gradientColors.end} />
            </linearGradient>
          </defs>
          <circle
            cx="120"
            cy="120"
            r={RADIUS}
            stroke="#1f2937"
            strokeWidth={STROKE}
            fill="transparent"
          />

          <motion.circle
            cx="120"
            cy="120"
            r={RADIUS}
            stroke="url(#healthGradient)"
            strokeWidth={STROKE}
            fill="transparent"
            strokeDasharray={CIRCUMFERENCE}
            style={{ strokeDashoffset }}
            strokeLinecap="round"
          />
        </svg>

        <motion.div
          className="absolute text-center"
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.6 }}
        >
          <div
            className="flex items-baseline justify-center"
            title={
              data.confidence_score !== undefined
                ? ""
                : "Calculated from historical data"
            }
          >
            <motion.div className="text-5xl font-semibold" style={{ color }}>
              {Math.round(
                Number(data.architecture_health_score ?? data.health_score) ||
                  0,
              )}
            </motion.div>
            <span className="text-lg ml-1" style={{ color }}>
              %
            </span>
          </div>
        </motion.div>
      </div>

      <div className="mt-8 space-y-3 text-sm text-neutral-400">
        <div className="flex justify-between">
          <span>Stability Index</span>
          <span>{(Number(data.stability_index) || 0).toFixed(2)}</span>
        </div>

        <div className="w-full bg-neutral-800 h-2 rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${(data.stability_index ?? 0) * 100}%` }}
            transition={{ duration: 1 }}
            className="h-full"
            style={{ backgroundColor: color }}
          />
        </div>
      </div>
    </div>
  );
}
