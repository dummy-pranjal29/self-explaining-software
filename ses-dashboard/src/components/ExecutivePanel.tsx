import { useEffect, useState } from "react";
import { fetchExecutive } from "../services/api";

interface ExecutiveResponse {
  timestamp: string;
  summary: string;
  health_score?: number;
  trend_slope?: number;
  risk_count?: number;
  forecast_outlook?: unknown;
  risk_analysis?: unknown;
  historical_scores?: number[];
}

export default function ExecutivePanel() {
  const [data, setData] = useState<ExecutiveResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchExecutive()
      .then((res) => {
        setData(res.data as ExecutiveResponse);
      })
      .catch((err) => {
        console.error("Executive fetch failed:", err);
        setError("Failed to load executive summary");
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  // Calculate trend direction with detailed info
  const getTrendInfo = (slope: number) => {
    if (slope > 5)
      return {
        label: "🚀 Rapidly Improving",
        color: "text-emerald-400",
        bg: "bg-emerald-500/10",
        icon: "↑↑",
      };
    if (slope > 2)
      return {
        label: "📈 Improving",
        color: "text-green-400",
        bg: "bg-green-500/10",
        icon: "↑",
      };
    if (slope > 0)
      return {
        label: "↗️ Slightly Improving",
        color: "text-lime-400",
        bg: "bg-lime-500/10",
        icon: "↗",
      };
    if (slope === 0)
      return {
        label: "➡️ Stable",
        color: "text-yellow-400",
        bg: "bg-yellow-500/10",
        icon: "→",
      };
    if (slope > -2)
      return {
        label: "↘️ Slightly Declining",
        color: "text-orange-400",
        bg: "bg-orange-500/10",
        icon: "↘",
      };
    if (slope > -5)
      return {
        label: "📉 Declining",
        color: "text-red-400",
        bg: "bg-red-500/10",
        icon: "↓",
      };
    return {
      label: "⚠️ Rapidly Declining",
      color: "text-red-600",
      bg: "bg-red-600/10",
      icon: "↓↓",
    };
  };

  // Get health status with detailed info
  const getHealthInfo = (score: number) => {
    if (score >= 90)
      return {
        label: "Excellent",
        color: "text-emerald-400",
        bg: "bg-emerald-500/10",
        ring: "ring-emerald-500/30",
        status: "operational",
      };
    if (score >= 80)
      return {
        label: "Healthy",
        color: "text-green-400",
        bg: "bg-green-500/10",
        ring: "ring-green-500/30",
        status: "operational",
      };
    if (score >= 70)
      return {
        label: "Good",
        color: "text-lime-400",
        bg: "bg-lime-500/10",
        ring: "ring-lime-500/30",
        status: "warning",
      };
    if (score >= 60)
      return {
        label: "Fair",
        color: "text-yellow-400",
        bg: "bg-yellow-500/10",
        ring: "ring-yellow-500/30",
        status: "warning",
      };
    if (score >= 40)
      return {
        label: "Poor",
        color: "text-orange-400",
        bg: "bg-orange-500/10",
        ring: "ring-orange-500/30",
        status: "degraded",
      };
    return {
      label: "Critical",
      color: "text-red-500",
      bg: "bg-red-500/10",
      ring: "ring-red-500/30",
      status: "critical",
    };
  };

  // Get urgency level
  const getUrgencyInfo = (riskCount: number, healthScore: number) => {
    if (riskCount === 0 && healthScore >= 70)
      return {
        label: "Low",
        color: "text-emerald-400",
        bg: "bg-emerald-500/10",
        icon: "✓",
      };
    if (riskCount <= 2 && healthScore >= 60)
      return {
        label: "Minimal",
        color: "text-green-400",
        bg: "bg-green-500/10",
        icon: "○",
      };
    if (riskCount <= 5 && healthScore >= 50)
      return {
        label: "Moderate",
        color: "text-yellow-400",
        bg: "bg-yellow-500/10",
        icon: "◐",
      };
    if (riskCount <= 10 || healthScore < 50)
      return {
        label: "High",
        color: "text-orange-400",
        bg: "bg-orange-500/10",
        icon: "◑",
      };
    return {
      label: "Critical",
      color: "text-red-500",
      bg: "bg-red-500/10",
      icon: "✕",
    };
  };

  // Parse summary into bullet points
  const parseSummaryToBulletPoints = (summary: string): string[] => {
    // Split by common delimiters
    const points = summary
      .split(/(?<=[.!?])\s+/)
      .map((s) => s.trim())
      .filter((s) => s.length > 0);

    if (points.length <= 1) {
      // If it's a single paragraph, try to split by keywords
      const keywordSplits = summary.split(
        /(?=\b(?:However|Additionally|Furthermore|Also|Note|Therefore|Because|Since|While)\b)/i,
      );
      return keywordSplits.map((s) => s.trim()).filter((s) => s.length > 0);
    }
    return points;
  };

  if (loading) {
    return (
      <div className="bg-gradient-to-br from-slate-900 to-slate-800 p-8 rounded-3xl border border-slate-700/50 shadow-2xl">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-2xl font-bold text-white">Executive Summary</h2>
            <p className="text-slate-400 text-sm mt-1">
              Architecture Health Overview
            </p>
          </div>
          <div className="w-12 h-12 rounded-full border-2 border-t-transparent border-emerald-500 animate-spin"></div>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-slate-800/50 flex items-center justify-center">
              <span className="text-3xl animate-pulse">📊</span>
            </div>
            <p className="text-slate-400">
              Generating architecture insights...
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-gradient-to-br from-slate-900 to-slate-800 p-8 rounded-3xl border border-red-500/30 shadow-2xl">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-2xl bg-red-500/10 flex items-center justify-center">
            <span className="text-3xl">⚠️</span>
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">
              Unable to Load Summary
            </h2>
            <p className="text-red-400">
              {error || "No executive data available"}
            </p>
          </div>
        </div>
      </div>
    );
  }

  const trendInfo =
    data.trend_slope !== undefined
      ? getTrendInfo(data.trend_slope)
      : getTrendInfo(0);
  const healthInfo =
    data.health_score !== undefined
      ? getHealthInfo(data.health_score)
      : getHealthInfo(50);
  const urgencyInfo = getUrgencyInfo(
    data.risk_count || 0,
    data.health_score || 50,
  );
  const bulletPoints = parseSummaryToBulletPoints(
    data.summary || "No summary available.",
  );

  return (
    <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-8 rounded-3xl border border-slate-700/50 shadow-2xl relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-bl from-emerald-500/5 to-transparent rounded-full blur-3xl"></div>
      <div className="absolute bottom-0 left-0 w-48 h-48 bg-gradient-to-tr from-blue-500/5 to-transparent rounded-full blur-3xl"></div>

      {/* Header */}
      <div className="flex items-center justify-between mb-8 relative">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-3">
            <span className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center text-lg">
              📋
            </span>
            Executive Summary
          </h2>
          <p className="text-slate-400 text-sm mt-1">
            Architecture Health Overview
          </p>
        </div>
        <div
          className={`px-4 py-2 rounded-full ${healthInfo.bg} ${healthInfo.color} text-sm font-medium flex items-center gap-2`}
        >
          <span
            className={`w-2 h-2 rounded-full ${healthInfo.status === "operational" ? "bg-emerald-400 animate-pulse" : healthInfo.status === "warning" ? "bg-yellow-400" : "bg-red-500"}`}
          ></span>
          {healthInfo.label}
        </div>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-3 gap-4 mb-8 relative">
        {/* Health Score Card */}
        <div
          className={`bg-slate-800/60 backdrop-blur-sm p-6 rounded-2xl border ${healthInfo.ring} ring-1 transition-all hover:scale-[1.02] duration-300`}
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-slate-400 text-sm font-medium">
              Health Score
            </span>
            <span className="text-2xl">💚</span>
          </div>
          <div className="flex items-end gap-2">
            <span className={`text-5xl font-black ${healthInfo.color}`}>
              {data.health_score ?? "N/A"}
            </span>
            <span className="text-slate-500 mb-2">/100</span>
          </div>
          <div className="mt-3 h-2 bg-slate-700/50 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-1000 ${healthInfo.color.replace("text-", "bg-")}`}
              style={{ width: `${data.health_score || 0}%` }}
            ></div>
          </div>
        </div>

        {/* Trend Card */}
        <div
          className={`bg-slate-800/60 backdrop-blur-sm p-6 rounded-2xl border ${trendInfo.bg.replace("/10", "/30")} ring-1 transition-all hover:scale-[1.02] duration-300`}
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-slate-400 text-sm font-medium">Trend</span>
            <span className="text-2xl">{trendInfo.icon}</span>
          </div>
          <div
            className={`text-3xl font-bold ${trendInfo.color} flex items-center gap-2`}
          >
            {trendInfo.label}
          </div>
          <p className="text-slate-500 text-sm mt-2">
            Slope: {data.trend_slope?.toFixed(1) || "0.0"}
          </p>
        </div>

        {/* Risk Card */}
        <div
          className={`bg-slate-800/60 backdrop-blur-sm p-6 rounded-2xl border ${urgencyInfo.bg.replace("/10", "/30")} ring-1 transition-all hover:scale-[1.02] duration-300`}
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-slate-400 text-sm font-medium">
              Operational Urgency
            </span>
            <span className="text-2xl">{urgencyInfo.icon}</span>
          </div>
          <div
            className={`text-3xl font-bold ${urgencyInfo.color} flex items-center gap-2`}
          >
            {urgencyInfo.label}
          </div>
          <p className="text-slate-500 text-sm mt-2">
            {data.risk_count || 0} high-risk edges detected
          </p>
        </div>
      </div>

      {/* Summary Section with Bullet Points */}
      <div className="bg-slate-800/40 backdrop-blur-sm rounded-2xl p-6 border border-slate-700/50 relative">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <span className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-sm">
            📝
          </span>
          Key Insights
        </h3>
        <ul className="space-y-3">
          {bulletPoints.map((point, index) => (
            <li
              key={index}
              className="flex items-start gap-3 text-slate-300 leading-relaxed"
            >
              <span className="w-6 h-6 rounded-full bg-gradient-to-br from-emerald-500/20 to-cyan-500/20 flex items-center justify-center text-emerald-400 text-sm flex-shrink-0 mt-0.5">
                {index + 1}
              </span>
              <span className="flex-1">{point}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Footer */}
      <div className="mt-6 pt-4 border-t border-slate-700/50 flex items-center justify-between text-sm text-slate-500">
        <div className="flex items-center gap-2">
          <span>🕐</span>
          <span>
            Last updated:{" "}
            {data.timestamp ? new Date(data.timestamp).toLocaleString() : "N/A"}
          </span>
        </div>
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            Live
          </span>
        </div>
      </div>
    </div>
  );
}
