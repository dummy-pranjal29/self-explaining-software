import { useEffect, useRef } from "react";
import * as d3 from "d3";
import type { ForecastResponse } from "../../types/intelligence";

interface Props {
  data: ForecastResponse;
}

export default function ForecastTimeline({ data }: Props) {
  const svgRef = useRef<SVGSVGElement | null>(null);

  type HistoryItem = {
    timestamp: string;
    health_score: number;
    stability_index?: number;
  };
  type MappedHistoryItem = {
    timestamp: Date;
    health: number;
    stability: number | null;
  };
  const history: MappedHistoryItem[] =
    data?.history?.map((v: HistoryItem) => ({
      timestamp: new Date(v.timestamp),
      health: v.health_score,
      stability: v.stability_index ?? null,
    })) ?? [];

  // Handle missing or error forecast data
  const forecastData =
    data?.forecast?.status === "success" ? data.forecast : null;

  const lastActual = history[history.length - 1]?.health ?? 0;
  const forecastValue = forecastData?.forecast_next ?? 0;
  const delta = forecastValue - lastActual;

  const slopeIcon = delta > 0.05 ? "↑" : delta < -0.05 ? "↓" : "→";

  const slopeColor =
    delta > 0.05
      ? "text-emerald-400"
      : delta < -0.05
        ? "text-red-400"
        : "text-neutral-400";

  const volatilityColor =
    forecastData?.volatility === "low"
      ? "text-emerald-400 border-emerald-400/30 bg-emerald-400/10"
      : forecastData?.volatility === "medium"
        ? "text-yellow-400 border-yellow-400/30 bg-yellow-400/10"
        : "text-red-400 border-red-400/30 bg-red-400/10";

  const hasData = forecastData && history.length > 0;

  useEffect(() => {
    if (!svgRef.current || !hasData) return;

    const svgEl = svgRef.current;
    const svg = d3.select(svgEl);
    svg.selectAll("*").remove();

    const width = svgEl.clientWidth;
    const height = svgEl.clientHeight;

    const margin = { top: 40, right: 40, bottom: 60, left: 80 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    // Create clip path to prevent line from crossing axes
    svg
      .append("defs")
      .append("clipPath")
      .attr("id", "chart-clip")
      .append("rect")
      .attr("width", innerWidth)
      .attr("height", innerHeight);

    // Main chart group (for axes - not clipped)
    const g = svg
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    // Clipped group for chart content (line)
    const chartArea = g.append("g").attr("clip-path", "url(#chart-clip)");

    // 24-hour domain
    const now = new Date();
    const start24h = new Date(now.getTime() - 24 * 60 * 60 * 1000);

    const xScale = d3
      .scaleTime()
      .domain([start24h, now])
      .range([0, innerWidth]);

    const yMin = d3.min(history, (d) => d.health) ?? 0;
    const yMax = d3.max(history, (d) => d.health) ?? 100;
    const yScale = d3
      .scaleLinear()
      .domain([yMin - 1, yMax + 1])
      .range([innerHeight, 0]);

    // GRID
    g.append("g")
      .call(
        d3
          .axisLeft(yScale)
          .ticks(5)
          .tickSize(-innerWidth)
          .tickFormat(() => ""),
      )
      .selectAll("line")
      .attr("stroke", "#1a1a1a");

    // Y AXIS
    g.append("g")
      .call(d3.axisLeft(yScale).ticks(5))
      .selectAll("text")
      .attr("fill", "#aaa")
      .style("font-size", "11px");

    g.append("text")
      .attr("transform", "rotate(-90)")
      .attr("x", -innerHeight / 2)
      .attr("y", -60)
      .attr("fill", "#666")
      .style("text-anchor", "middle")
      .style("font-size", "12px")
      .text("Architecture Health");

    // X AXIS (24h clean)
    g.append("g")
      .attr("transform", `translate(0, ${innerHeight})`)
      .call(
        d3
          .axisBottom(xScale)
          .ticks(6)
          .tickFormat((d) => d3.timeFormat("%H:%M")(d as Date)),
      )
      .selectAll("text")
      .attr("fill", "#888")
      .style("font-size", "11px");

    g.append("text")
      .attr("x", innerWidth / 2)
      .attr("y", innerHeight + 45)
      .attr("fill", "#666")
      .style("text-anchor", "middle")
      .style("font-size", "12px")
      .text("Last 24 Hours");

    // LINE (in clipped chart area)
    const line = d3
      .line<(typeof history)[0]>()
      .x((d) => xScale(d.timestamp))
      .y((d) => yScale(d.health))
      .curve(d3.curveMonotoneX);

    chartArea
      .append("path")
      .datum(history)
      .attr("fill", "none")
      .attr("stroke", "#6366f1")
      .attr("stroke-width", 3)
      .attr("d", line);

    // HOVER
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

    const tooltip = d3
      .select(svgEl.parentElement)
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
      const hoveredTime = xScale.invert(mouseX);

      const closest = history.reduce((a, b) =>
        Math.abs(b.timestamp.getTime() - hoveredTime.getTime()) <
        Math.abs(a.timestamp.getTime() - hoveredTime.getTime())
          ? b
          : a,
      );

      focusCircle
        .attr("cx", xScale(closest.timestamp))
        .attr("cy", yScale(closest.health))
        .attr("opacity", 1);

      tooltip
        .style("opacity", 1)
        .style("left", event.pageX + 15 + "px")
        .style("top", event.pageY - 50 + "px").html(`
          <div style="font-weight:600;margin-bottom:6px;">
            ${d3.timeFormat("%Y-%m-%d %H:%M")(closest.timestamp)}
          </div>
          <div>Health: <strong>${closest.health.toFixed(2)}</strong></div>
          <div>Stability: ${
            closest.stability !== null
              ? closest.stability.toFixed(2)
              : "<span style='opacity:0.6;'>Not Available</span>"
          }</div>
        `);
    });

    overlay.on("mouseleave", function () {
      focusCircle.attr("opacity", 0);
      tooltip.style("opacity", 0);
    });
  }, [data]);

  return (
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

        <div className="flex gap-3 text-xs">
          <span
            className="px-3 py-1 rounded-full border border-neutral-700 text-neutral-300"
            title="Model confidence based on residual variance and forecast error."
          >
            Confidence{" "}
            {forecastData
              ? `${(forecastData.confidence_score * 100).toFixed(1)}%`
              : "N/A"}
          </span>

          <span
            className={`px-3 py-1 rounded-full border ${volatilityColor}`}
            title="Volatility measures how unstable recent architectural changes are."
          >
            Volatility {forecastData?.volatility ?? "N/A"}
          </span>
        </div>
      </div>

      <div
        className={`flex items-center gap-4 text-sm ${hasData ? slopeColor : "text-neutral-400"}`}
      >
        <span className="text-xl font-semibold">
          {hasData ? slopeIcon : "—"}
        </span>
        <span title="Difference between last recorded health and predicted next health.">
          {hasData
            ? `Δ Forecast vs Last: ${delta >= 0 ? "+" : ""}${delta.toFixed(2)}`
            : "No data available"}
        </span>
      </div>

      <div className="h-[420px] w-full relative">
        {hasData ? (
          <svg ref={svgRef} className="w-full h-full" />
        ) : (
          <div className="flex items-center justify-center h-full text-neutral-500">
            No historical data available. Start tracing to see forecasts.
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-sm">
        <div
          className="bg-neutral-900/60 border border-neutral-800 rounded-xl p-4"
          title="Predicted next architecture health score."
        >
          <div className="text-xs text-neutral-500">Forecast</div>
          <div className="text-lg font-medium text-neutral-100 mt-1">
            {hasData ? forecastValue.toFixed(2) : "N/A"}
          </div>
        </div>

        <div
          className="bg-neutral-900/60 border border-neutral-800 rounded-xl p-4"
          title="Lower and upper bounds within which the forecast is expected to fall."
        >
          <div className="text-xs text-neutral-500">Confidence Interval</div>
          <div className="text-neutral-100 mt-1">
            {forecastData?.confidence_interval
              ? `[${forecastData.confidence_interval.lower.toFixed(2)}, ${forecastData.confidence_interval.upper.toFixed(2)}]`
              : "N/A"}
          </div>
        </div>

        <div
          className="bg-neutral-900/60 border border-neutral-800 rounded-xl p-4"
          title="Root Mean Squared Error of forecast model."
        >
          <div className="text-xs text-neutral-500">RMSE</div>
          <div className="text-neutral-100 mt-1">
            {forecastData?.rmse?.toFixed(3) ?? "N/A"}
          </div>
        </div>

        <div
          className="bg-neutral-900/60 border border-neutral-800 rounded-xl p-4"
          title="Variance of forecast residuals indicating uncertainty."
        >
          <div className="text-xs text-neutral-500">Residual Variance</div>
          <div className="text-neutral-100 mt-1">
            {forecastData?.residual_variance?.toFixed(3) ?? "N/A"}
          </div>
        </div>
      </div>
    </div>
  );
}
