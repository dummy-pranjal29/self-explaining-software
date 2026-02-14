import HealthGauge from "../components/HealthGauge";
import ExecutivePanel from "../components/ExecutivePanel";
import ForecastChart from "../components/ForecastChart";

export default function Dashboard() {
  return (
    <div className="min-h-screen bg-slate-950 text-white p-8 space-y-10">
      <h1 className="text-3xl font-bold tracking-tight">
        SELF-EVOLVING SOFTWARE
      </h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <HealthGauge />
        <ExecutivePanel />
      </div>

      <ForecastChart />
    </div>
  );
}
