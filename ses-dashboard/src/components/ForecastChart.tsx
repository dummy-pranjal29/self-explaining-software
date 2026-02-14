import { useEffect, useRef, useState } from "react";
import * as d3 from "d3";
import { fetchForecast } from "../services/api";
import type { ForecastResponse } from "../types/intelligence";

export default function ForecastChart() {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [data, setData] = useState<ForecastResponse | null>(null);

  useEffect(() => {
    fetchForecast()
      .then((res) => {
        console.log("FORECAST RESPONSE:", res.data);
        setData(res.data);
      })
      .catch((err) => {
        console.error("Forecast fetch failed:", err);
      });
  }, []);

  useEffect(() => {
    if (!data || !svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const width = svgRef.current.clientWidth;
    const height = svgRef.current.clientHeight;

    const margin = { top: 20, right: 30, bottom: 30, left: 40 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    const g = svg
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    const history = data.history.map(
      (entry: { health_score: number }, i: number) => ({
        x: i,
        y: entry.health_score,
      }),
    );

    const forecastPoint = {
      x: history.length,
      y: data.forecast.forecast_next,
    };

    const fullData = [...history, forecastPoint];

    const xScale = d3
      .scaleLinear()
      .domain([0, fullData.length - 1])
      .range([0, innerWidth]);

    const yMin = d3.min(fullData, (d) => d.y) ?? 0;
    const yMax = d3.max(fullData, (d) => d.y) ?? 100;

    const yScale = d3
      .scaleLinear()
      .domain([yMin - 5, yMax + 5])
      .range([innerHeight, 0]);

    // Historical line
    const line = d3
      .line<{ x: number; y: number }>()
      .x((d) => xScale(d.x))
      .y((d) => yScale(d.y))
      .curve(d3.curveMonotoneX);

    g.append("path")
      .datum(history)
      .attr("fill", "none")
      .attr("stroke", "#818cf8")
      .attr("stroke-width", 2)
      .attr("d", line);

    // Forecast extension (dashed)
    g.append("path")
      .datum([history[history.length - 1], forecastPoint])
      .attr("fill", "none")
      .attr("stroke", "#a5b4fc")
      .attr("stroke-width", 2)
      .attr("stroke-dasharray", "6,4")
      .attr("d", line);

    // Forecast point
    g.append("circle")
      .attr("cx", xScale(forecastPoint.x))
      .attr("cy", yScale(forecastPoint.y))
      .attr("r", 5)
      .attr("fill", "#6366f1");
  }, [data]);

  if (!data) {
    return (
      <div className="bg-neutral-900 border border-neutral-800 rounded-3xl p-8">
        <div className="h-[320px] w-full flex items-center justify-center text-neutral-400">
          Loading forecast...
        </div>
      </div>
    );
  }

  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-3xl p-8 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-sm tracking-wide text-neutral-400 uppercase">
            Health Forecast
          </h2>
          <p className="text-xs text-neutral-500 mt-1">
            Predictive trajectory with confidence interval
          </p>
        </div>

        <div className="flex gap-4 text-xs">
          <span className="px-3 py-1 rounded-full border border-neutral-700 text-neutral-300">
            Confidence {(data.forecast.confidence_score * 100).toFixed(1)}%
          </span>

          <span className="px-3 py-1 rounded-full border border-neutral-700 text-neutral-300">
            Volatility {data.forecast.volatility}
          </span>
        </div>
      </div>

      {/* Chart */}
      <div className="h-[320px] w-full">
        <svg ref={svgRef} className="w-full h-full" />
      </div>

      {/* Footer */}
      <div className="grid grid-cols-4 gap-6 text-sm text-neutral-400">
        <div>
          <div className="text-xs text-neutral-500">Forecast</div>
          <div className="text-lg text-neutral-100">
            {data.forecast.forecast_next.toFixed(2)}
          </div>
        </div>

        <div>
          <div className="text-xs text-neutral-500">Confidence Interval</div>
          <div className="text-neutral-100">
            [{data.forecast.confidence_interval.lower.toFixed(2)},{" "}
            {data.forecast.confidence_interval.upper.toFixed(2)}]
          </div>
        </div>

        <div>
          <div className="text-xs text-neutral-500">RMSE</div>
          <div className="text-neutral-100">
            {data.forecast.rmse.toFixed(3)}
          </div>
        </div>

        <div>
          <div className="text-xs text-neutral-500">Residual Variance</div>
          <div className="text-neutral-100">
            {data.forecast.residual_variance.toFixed(3)}
          </div>
        </div>
      </div>
    </div>
  );
}
