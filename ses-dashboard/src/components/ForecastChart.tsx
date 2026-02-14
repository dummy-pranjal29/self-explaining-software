import { useEffect, useState } from "react";
import { fetchForecast } from "../services/api";

export default function ForecastChart() {
  const [raw, setRaw] = useState<unknown>(null);

  useEffect(() => {
    fetchForecast()
      .then((res) => {
        console.log("FORECAST RESPONSE:", res.data);
        setRaw(res.data);
      })
      .catch((err) => {
        console.error("Forecast fetch failed:", err);
      });
  }, []);

  return (
    <div className="bg-slate-900 p-8 rounded-2xl border border-slate-800">
      <h2 className="text-lg text-gray-400 mb-6">Forecast Debug</h2>

      <pre className="text-xs text-green-400 overflow-auto">
        {JSON.stringify(raw, null, 2)}
      </pre>
    </div>
  );
}
