import { useEffect, useState } from "react";
import { fetchExecutive } from "../services/api";

interface ExecutiveResponse {
  timestamp: string;
  summary: string;
  forecast_outlook?: unknown;
  risk_analysis?: unknown;
}

export default function ExecutivePanel() {
  const [data, setData] = useState<ExecutiveResponse | null>(null);

  useEffect(() => {
    fetchExecutive()
      .then((res) => {
        setData(res.data as ExecutiveResponse);
      })
      .catch((err) => {
        console.error("Executive fetch failed:", err);
      });
  }, []);

  if (!data) {
    return (
      <div className="bg-slate-900 p-8 rounded-2xl border border-slate-800">
        Loading...
      </div>
    );
  }

  return (
    <div className="bg-slate-900 p-8 rounded-2xl border border-slate-800">
      <h2 className="text-lg text-gray-400 mb-6">Executive Summary</h2>

      <p className="text-gray-300 leading-relaxed">
        {data.summary ?? "No summary available."}
      </p>
    </div>
  );
}
