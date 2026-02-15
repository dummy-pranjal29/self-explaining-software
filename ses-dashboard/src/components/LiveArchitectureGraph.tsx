import { useEffect, useRef, useState } from "react";
import * as d3 from "d3";

interface Node {
  id: string;
}

interface Edge {
  source: string | Node;
  target: string | Node;
  call_count: number;
  avg_duration: number;
  stability_index: number;
  anomaly_flag: boolean;
}

interface GraphData {
  nodes: Node[];
  edges: Edge[];
}

// D3 simulation node type with position properties
interface SimNode extends d3.SimulationNodeDatum {
  id: string;
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
  // Enhanced properties for visualization
  call_count?: number;
  avg_duration?: number;
  stability_index?: number;
  anomaly_flag?: boolean;
}

// D3 simulation link type (for internal D3 use)
type SimLink = d3.SimulationLinkDatum<SimNode> & {
  call_count: number;
  avg_duration: number;
  stability_index: number;
  anomaly_flag: boolean;
};

// Color palette - professional tech aesthetic
const COLORS = {
  // Stability-based colors (gradient from red to green)
  stable: "#10b981", // emerald green
  moderate: "#f59e0b", // amber
  unstable: "#ef4444", // red
  // Anomaly highlight
  anomaly: "#f43f5e", // rose
  // Node colors
  nodeBase: "#3b82f6", // blue
  nodeHighlight: "#06b6d4", // cyan
  // Edge colors
  edgeDefault: "#475569", // slate
  edgeActive: "#818cf8", // indigo
};

// Get stability color based on index
function getStabilityColor(stability: number): string {
  if (stability > 0.85) return COLORS.stable;
  if (stability > 0.6) return COLORS.moderate;
  return COLORS.unstable;
}

// Get edge color based on multiple factors
function getEdgeColor(d: SimLink): string {
  if (d.anomaly_flag) return COLORS.anomaly;
  return getStabilityColor(d.stability_index);
}

// Calculate edge opacity based on call count
function getEdgeOpacity(callCount: number, maxCalls: number): number {
  const minOpacity = 0.3;
  const maxOpacity = 1;
  return minOpacity + (callCount / maxCalls) * (maxOpacity - minOpacity);
}

// Calculate node size based on connections
function getNodeSize(
  degree: number,
  minSize: number = 8,
  maxSize: number = 20,
): number {
  return Math.min(maxSize, minSize + degree * 2);
}

export default function LiveArchitectureGraph({ data }: { data: GraphData }) {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 500 });

  // Calculate node degrees for sizing
  const nodeDegrees = new Map<string, number>();
  data.nodes.forEach((n) => nodeDegrees.set(n.id, 0));
  data.edges.forEach((e) => {
    const sourceId =
      typeof e.source === "string" ? e.source : (e.source as Node).id;
    const targetId =
      typeof e.target === "string" ? e.target : (e.target as Node).id;
    nodeDegrees.set(sourceId, (nodeDegrees.get(sourceId) || 0) + 1);
    nodeDegrees.set(targetId, (nodeDegrees.get(targetId) || 0) + 1);
  });

  // Find max call count for normalization
  const maxCallCount = Math.max(...data.edges.map((e) => e.call_count), 1);

  useEffect(() => {
    if (!data || !svgRef.current) return;

    // Responsive dimensions
    const container = svgRef.current.parentElement;
    const width = container?.clientWidth || 800;
    const height = 500;
    setDimensions({ width, height });

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    // Create definitions for gradients and filters
    const defs = svg.append("defs");

    // Glow filter for nodes
    const glowFilter = defs
      .append("filter")
      .attr("id", "nodeGlow")
      .attr("x", "-50%")
      .attr("y", "-50%")
      .attr("width", "200%")
      .attr("height", "200%");

    glowFilter
      .append("feGaussianBlur")
      .attr("stdDeviation", "3")
      .attr("result", "coloredBlur");

    const feMerge = glowFilter.append("feMerge");
    feMerge.append("feMergeNode").attr("in", "coloredBlur");
    feMerge.append("feMergeNode").attr("in", "SourceGraphic");

    // Edge glow filter
    const edgeGlow = defs
      .append("filter")
      .attr("id", "edgeGlow")
      .attr("x", "-50%")
      .attr("y", "-50%")
      .attr("width", "200%")
      .attr("height", "200%");

    edgeGlow
      .append("feGaussianBlur")
      .attr("stdDeviation", "2")
      .attr("result", "coloredBlur");

    const edgeMerge = edgeGlow.append("feMerge");
    edgeMerge.append("feMergeNode").attr("in", "coloredBlur");
    edgeMerge.append("feMergeNode").attr("in", "SourceGraphic");

    // Gradient for nodes
    const nodeGradient = defs
      .append("radialGradient")
      .attr("id", "nodeGradient")
      .attr("cx", "30%")
      .attr("cy", "30%");

    nodeGradient
      .append("stop")
      .attr("offset", "0%")
      .attr("stop-color", COLORS.nodeHighlight)
      .attr("stop-opacity", 1);

    nodeGradient
      .append("stop")
      .attr("offset", "100%")
      .attr("stop-color", COLORS.nodeBase)
      .attr("stop-opacity", 1);

    // Create container groups
    const linkGroup = svg.append("g").attr("class", "links");
    const nodeGroup = svg.append("g").attr("class", "nodes");
    const labelGroup = svg.append("g").attr("class", "labels");

    // Enhanced simulation with multiple forces
    const simulation = d3
      .forceSimulation<SimNode>(data.nodes as SimNode[])
      // Link force with custom distance based on call frequency
      .force(
        "link",
        d3
          .forceLink<SimNode, SimLink>(data.edges as SimLink[])
          .id((d) => d.id)
          .distance((d) => 150 - Math.log(d.call_count + 1) * 15) // More calls = shorter distance
          .strength(0.5),
      )
      // Repulsion between nodes
      .force("charge", d3.forceManyBody().strength(-400))
      // Collision detection to prevent overlap
      .force(
        "collision",
        d3
          .forceCollide<SimNode>()
          .radius((d) => getNodeSize(nodeDegrees.get(d.id) || 0) + 10),
      )
      // Center force
      .force("center", d3.forceCenter(width / 2, height / 2))
      // Additional radial force to spread nodes evenly
      .force(
        "radial",
        d3
          .forceRadial(Math.min(width, height) / 3, width / 2, height / 2)
          .strength(0.1),
      );

    // Create edges with animated dash pattern
    const link = linkGroup
      .selectAll<SVGLineElement, SimLink>("line")
      .data(data.edges as SimLink[])
      .enter()
      .append("line")
      .attr("stroke", (d) => getEdgeColor(d))
      .attr("stroke-opacity", (d) => getEdgeOpacity(d.call_count, maxCallCount))
      .attr("stroke-width", (d) =>
        Math.max(1, Math.log(d.call_count + 1) * 1.5),
      )
      .attr("stroke-linecap", "round")
      .style("filter", (d) => (d.anomaly_flag ? "url(#edgeGlow)" : "none"));

    // Add animated dash pattern for "data flow" effect
    link
      .attr("stroke-dasharray", "8,4")
      .style("animation", "dash 20s linear infinite");

    // Create nodes with gradient fill and glow
    const node = nodeGroup
      .selectAll<SVGCircleElement, SimNode>("circle")
      .data(data.nodes as SimNode[])
      .enter()
      .append("circle")
      .attr("r", (d) => getNodeSize(nodeDegrees.get(d.id) || 0))
      .attr("fill", "url(#nodeGradient)")
      .style("filter", "url(#nodeGlow)")
      .style("cursor", "pointer")
      .call(
        d3
          .drag<SVGCircleElement, SimNode>()
          .on("start", dragstarted)
          .on("drag", dragged)
          .on("end", dragended),
      );

    // Add outer ring for high-activity nodes
    node
      .filter((d) => (nodeDegrees.get(d.id) || 0) > 3)
      .append("circle")
      .attr("r", (d) => getNodeSize(nodeDegrees.get(d.id) || 0) + 4)
      .attr("fill", "none")
      .attr("stroke", COLORS.nodeHighlight)
      .attr("stroke-width", 1.5)
      .attr("stroke-opacity", 0.5);

    // Create labels with coder font for readability - using node names directly
    const label = labelGroup
      .selectAll<SVGTextElement, SimNode>("text")
      .data(data.nodes as SimNode[])
      .enter()
      .append("text")
      .text((d) => d.id)
      .attr("font-size", 11)
      .attr(
        "font-family",
        "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
      )
      .attr("font-weight", "600")
      .attr("fill", "#ffffff")
      .attr("text-anchor", "middle")
      .attr("dy", 4)
      .style("pointer-events", "none")
      .style(
        "text-shadow",
        "0 0 8px rgba(59, 130, 246, 0.8), 0 2px 4px rgba(0,0,0,0.5)",
      )
      .style("animation", "float 3s ease-in-out infinite");

    // Add tooltip functionality
    const tooltip = d3
      .select("body")
      .append("div")
      .attr("class", "graph-tooltip")
      .style("position", "absolute")
      .style("visibility", "hidden")
      .style("background", "rgba(15, 23, 42, 0.95)")
      .style("color", "#e2e8f0")
      .style("padding", "8px 12px")
      .style("border-radius", "6px")
      .style("font-size", "12px")
      .style("border", "1px solid #475569")
      .style("box-shadow", "0 4px 12px rgba(0,0,0,0.3)")
      .style("z-index", "1000");

    node
      .on("mouseover", function (_event, d) {
        const degree = nodeDegrees.get(d.id) || 0;
        const incomingCalls = data.edges
          .filter(
            (e) =>
              (typeof e.target === "string" ? e.target : e.target.id) === d.id,
          )
          .reduce((sum, e) => sum + e.call_count, 0);

        tooltip.style("visibility", "visible").html(`
            <div style="font-weight: 600; margin-bottom: 4px;">${d.id}</div>
            <div>Connections: ${degree}</div>
            <div>Incoming calls: ${incomingCalls}</div>
          `);

        d3.select(this)
          .transition()
          .duration(200)
          .attr("r", getNodeSize(degree) * 1.3);
      })
      .on("mousemove", function (event) {
        tooltip
          .style("top", event.pageY - 10 + "px")
          .style("left", event.pageX + 10 + "px");
      })
      .on("mouseout", function (_event, d) {
        tooltip.style("visibility", "hidden");
        const degree = nodeDegrees.get(d.id) || 0;
        d3.select(this)
          .transition()
          .duration(200)
          .attr("r", getNodeSize(degree));
      });

    // Simulation tick with smooth animation
    simulation.on("tick", () => {
      link
        .attr("x1", (d) => (d.source as SimNode).x ?? 0)
        .attr("y1", (d) => (d.source as SimNode).y ?? 0)
        .attr("x2", (d) => (d.target as SimNode).x ?? 0)
        .attr("y2", (d) => (d.target as SimNode).y ?? 0);

      node.attr("cx", (d) => d.x ?? 0).attr("cy", (d) => d.y ?? 0);

      label.attr("x", (d) => (d.x ?? 0) + 15).attr("y", (d) => (d.y ?? 0) + 4);
    });

    // Drag functions
    function dragstarted(
      event: d3.D3DragEvent<SVGCircleElement, SimNode, SimNode>,
      d: SimNode,
    ) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(
      event: d3.D3DragEvent<SVGCircleElement, SimNode, SimNode>,
      d: SimNode,
    ) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragended(
      event: d3.D3DragEvent<SVGCircleElement, SimNode, SimNode>,
      d: SimNode,
    ) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }

    // Cleanup
    return () => {
      tooltip.remove();
    };
  }, [data]);

  // Add keyframe animations
  useEffect(() => {
    const style = document.createElement("style");
    style.textContent = `
      @keyframes dash {
        to {
          stroke-dashoffset: -1000;
        }
      }
      @keyframes float {
        0%, 100% {
          transform: translateY(0px);
          opacity: 0.7;
        }
        50% {
          transform: translateY(-8px);
          opacity: 0.9;
        }
      }
      .links line {
        animation: dash 30s linear infinite;
      }
      .labels text {
        animation: float 3s ease-in-out infinite;
      }
      .labels text:nth-child(2) {
        animation-delay: -1s;
      }
      .labels text:nth-child(3) {
        animation-delay: -2s;
      }
    `;
    document.head.appendChild(style);
    return () => {
      document.head.removeChild(style);
    };
  }, []);

  return (
    <div className="bg-slate-900 rounded-2xl p-4 shadow-xl">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-white text-lg font-semibold">
          Live Architecture Graph
        </h2>
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-emerald-500"></span>
            <span className="text-slate-400">Stable ({">"}85%)</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-amber-500"></span>
            <span className="text-slate-400">Moderate (60-85%)</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-red-500"></span>
            <span className="text-slate-400">Unstable ({"<"}60%)</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-rose-500"></span>
            <span className="text-slate-400">Anomaly</span>
          </div>
        </div>
      </div>
      <svg
        ref={svgRef}
        width={dimensions.width}
        height={dimensions.height}
        style={{ overflow: "visible" }}
      ></svg>
    </div>
  );
}
