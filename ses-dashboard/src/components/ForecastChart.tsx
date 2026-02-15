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

    // Create clip path to prevent line from crossing axes
    svg
      .append("defs")
      .append("clipPath")
      .attr("id", "forecast-chart-clip")
      .append("rect")
      .attr("width", innerWidth)
      .attr("height", innerHeight);

    // Main chart group (for axes - not clipped)
    const chartArea = g
      .append("g")
      .attr("clip-path", "url(#forecast-chart-clip)");

    const history = data.history.map(
      (
        entry: { health_score: number; stability_index?: number },
        i: number,
      ) => ({
        x: i,
        y: entry.health_score,
        stability: entry.stability_index ?? null,
      }),
    );

    const forecastPoint: { x: number; y: number; stability: null } = {
      x: history.length,
      y: data.forecast.forecast_next,
      stability: null,
    };

    type DataPoint = { x: number; y: number; stability: number | null };
    const fullData: DataPoint[] = [...history, forecastPoint];

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

    chartArea
      .append("path")
      .datum(history)
      .attr("fill", "none")
      .attr("stroke", "#818cf8")
      .attr("stroke-width", 2)
      .attr("d", line);

    // Forecast extension (dashed)
    chartArea
      .append("path")
      .datum([history[history.length - 1], forecastPoint])
      .attr("fill", "none")
      .attr("stroke", "#a5b4fc")
      .attr("stroke-width", 2)
      .attr("stroke-dasharray", "6,4")
      .attr("d", line);

    // Forecast point
    chartArea
      .append("circle")
      .attr("cx", xScale(forecastPoint.x))
      .attr("cy", yScale(forecastPoint.y))
      .attr("r", 5)
      .attr("fill", "#6366f1");

    // Hover overlay
    const overlay = g
      .append("rect")
      .attr("width", innerWidth)
      .attr("height", innerHeight)
      .attr("fill", "transparent");

    const focusCircle = g
      .append("circle")
      .attr("r", 6)
      .attr("fill", "#fff")
      .attr("opacity", 0);

    const tooltipParent = svgRef.current?.parentElement;
    if (!tooltipParent) return;

    const tooltip = d3
      .select(tooltipParent)
      .append("div")
      .style("position", "absolute")
      .style("background", "rgba(15,15,15,0.96)")
      .style("color", "#fff")
      .style("padding", "12px 16px")
      .style("border", "1px solid #222")
      .style("border-radius", "12px")
      .style("font-size", "12px")
      .style("box-shadow", "0 10px 40px rgba(0,0,0,0.6)")
      .style("pointer-events", "none")
      .style("opacity", 0);

    overlay.on("mousemove", function (event) {
      const [mouseX] = d3.pointer(event);
      const index = Math.round(xScale.invert(mouseX));

      if (index < 0 || index >= fullData.length) return;

      const d = fullData[index];

      focusCircle
        .attr("cx", xScale(d.x))
        .attr("cy", yScale(d.y))
        .attr("opacity", 1);

      tooltip
        .style("opacity", 1)
        .style("left", event.pageX + 15 + "px")
        .style("top", event.pageY - 50 + "px").html(`
          <div style="font-weight:600;margin-bottom:6px;">
            ${index === history.length ? "Forecast" : `Snapshot ${index + 1}`}
          </div>
          <div>Health: <strong>${d.y.toFixed(2)}</strong></div>
          ${
            d.stability !== undefined
              ? `<div>Stability: ${d.stability !== null ? d.stability.toFixed(2) : "N/A"}</div>`
              : ""
          }
        `);
    });

    overlay.on("mouseleave", function () {
      focusCircle.attr("opacity", 0);
      tooltip.style("opacity", 0);
    });
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
