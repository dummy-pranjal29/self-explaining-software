import { useEffect, useRef } from "react";
import * as d3 from "d3";
import type { ForecastResponse } from "../../types/intelligence";

interface Props {
  data: ForecastResponse;
}

export default function ForecastTimeline({ data }: Props) {
  const svgRef = useRef<SVGSVGElement | null>(null);

  useEffect(() => {
    if (!data || !svgRef.current) return;
    if (!data.history || data.history.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const width = svgRef.current.clientWidth;
    const height = svgRef.current.clientHeight;

    const margin = { top: 20, right: 30, bottom: 30, left: 50 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    const g = svg
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    const history = data.history.map(
      (entry: { health_score: number }, i: number) => ({
        x: i,
        y: entry.health_score,
        predicted: false,
      }),
    );

    const forecastPoint = {
      x: history.length,
      y: data.forecast.forecast_next,
      predicted: true,
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

    // Y Axis
    g.append("g")
      .call(d3.axisLeft(yScale).ticks(5))
      .attr("color", "#737373")
      .selectAll("text")
      .attr("fill", "#a3a3a3")
      .style("font-size", "10px");

    // Grid
    g.append("g")
      .call(
        d3
          .axisLeft(yScale)
          .ticks(5)
          .tickSize(-innerWidth)
          .tickFormat(() => ""),
      )
      .selectAll("line")
      .attr("stroke", "#262626")
      .attr("stroke-opacity", 0.3);

    // Confidence Band
    g.append("rect")
      .attr("x", xScale(forecastPoint.x) - 10)
      .attr("width", 20)
      .attr("y", yScale(data.forecast.confidence_interval.upper))
      .attr(
        "height",
        yScale(data.forecast.confidence_interval.lower) -
          yScale(data.forecast.confidence_interval.upper),
      )
      .attr("fill", "#6366f1")
      .attr("opacity", 0.15);

    const line = d3
      .line<{ x: number; y: number }>()
      .x((d) => xScale(d.x))
      .y((d) => yScale(d.y))
      .curve(d3.curveMonotoneX);

    // Historical Line
    g.append("path")
      .datum(history)
      .attr("fill", "none")
      .attr("stroke", "#818cf8")
      .attr("stroke-width", 2)
      .attr("d", line);

    // Forecast Extension
    g.append("path")
      .datum([history[history.length - 1], forecastPoint])
      .attr("fill", "none")
      .attr("stroke", "#a5b4fc")
      .attr("stroke-width", 2)
      .attr("stroke-dasharray", "6,4")
      .attr("d", line);

    // Forecast Boundary
    g.append("line")
      .attr("x1", xScale(history.length - 1))
      .attr("x2", xScale(history.length - 1))
      .attr("y1", 0)
      .attr("y2", innerHeight)
      .attr("stroke", "#444")
      .attr("stroke-dasharray", "4,4")
      .attr("opacity", 0.6);

    // Hover Elements
    const focusLine = g
      .append("line")
      .attr("stroke", "#888")
      .attr("stroke-dasharray", "4,4")
      .attr("opacity", 0);

    const focusCircle = g
      .append("circle")
      .attr("r", 5)
      .attr("fill", "#ffffff")
      .attr("opacity", 0);

    const tooltip = d3
      .select(svgRef.current.parentElement)
      .append("div")
      .style("position", "absolute")
      .style("background", "#111")
      .style("color", "#fff")
      .style("padding", "6px 10px")
      .style("border", "1px solid #333")
      .style("border-radius", "6px")
      .style("font-size", "12px")
      .style("pointer-events", "none")
      .style("opacity", 0);

    svg.on("mousemove", function (event) {
      const [mouseX] = d3.pointer(event);
      const x0 = xScale.invert(mouseX - margin.left);
      const index = Math.round(x0);

      if (index < 0 || index >= fullData.length) return;

      const d = fullData[index];

      focusLine
        .attr("x1", xScale(d.x))
        .attr("x2", xScale(d.x))
        .attr("y1", 0)
        .attr("y2", innerHeight)
        .attr("opacity", 0.6);

      focusCircle
        .attr("cx", xScale(d.x))
        .attr("cy", yScale(d.y))
        .attr("opacity", 1);

      tooltip
        .style("opacity", 1)
        .style("left", event.pageX + 10 + "px")
        .style("top", event.pageY - 30 + "px")
        .html(
          `<strong>${d.predicted ? "Predicted" : "Historical"}</strong><br/>
           Health: ${d.y.toFixed(2)}`,
        );
    });

    svg.on("mouseleave", function () {
      focusLine.attr("opacity", 0);
      focusCircle.attr("opacity", 0);
      tooltip.style("opacity", 0);
    });
  }, [data]);

  return (
    <div className="relative bg-neutral-900 border border-neutral-800 rounded-3xl p-8 space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-sm tracking-wide text-neutral-400 uppercase">
          Health Forecast
        </h2>
        <div className="text-xs text-neutral-300">
          Confidence {(data.forecast.confidence_score * 100).toFixed(1)}%
        </div>
      </div>

      <div className="h-[320px] w-full relative">
        <svg ref={svgRef} className="w-full h-full" />
      </div>
    </div>
  );
}
