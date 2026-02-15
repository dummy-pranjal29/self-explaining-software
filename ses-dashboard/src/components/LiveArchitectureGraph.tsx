import { useEffect, useRef } from "react";
import * as d3 from "d3";

interface Node {
  id: string;
}

interface Edge {
  source: string | Node;
  target: string | Node;
  call_count: number;
  avg_duration: number;
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
}

// D3 simulation link type (for internal D3 use)
type SimLink = d3.SimulationLinkDatum<SimNode> & {
  call_count: number;
  avg_duration: number;
};

export default function LiveArchitectureGraph({ data }: { data: GraphData }) {
  const svgRef = useRef<SVGSVGElement | null>(null);

  useEffect(() => {
    if (!data || !svgRef.current) return;

    const width = 800;
    const height = 500;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const simulation = d3
      .forceSimulation(data.nodes as SimNode[])
      .force(
        "link",
        d3
          .forceLink(data.edges as unknown as d3.SimulationLinkDatum<SimNode>[])
          .id((d) => (d as SimNode).id)
          .distance(120),
      )
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2));

    const link = svg
      .append("g")
      .selectAll<SVGLineElement, SimLink>("line")
      .data(data.edges as SimLink[])
      .enter()
      .append("line")
      .attr("stroke", "#94a3b8")
      .attr("stroke-width", (d) => Math.max(1, Math.log(d.call_count + 1)));

    const node = svg
      .append("g")
      .selectAll<SVGCircleElement, SimNode>("circle")
      .data(data.nodes as SimNode[])
      .enter()
      .append("circle")
      .attr("r", 10)
      .attr("fill", "#3b82f6")
      .call(
        d3
          .drag<SVGCircleElement, SimNode>()
          .on("start", dragstarted)
          .on("drag", dragged)
          .on("end", dragended),
      );

    const label = svg
      .append("g")
      .selectAll<SVGTextElement, SimNode>("text")
      .data(data.nodes as SimNode[])
      .enter()
      .append("text")
      .text((d) => d.id)
      .attr("font-size", 10)
      .attr("fill", "#e2e8f0");

    simulation.on("tick", () => {
      link
        .attr("x1", (d) => (d.source as SimNode).x ?? 0)
        .attr("y1", (d) => (d.source as SimNode).y ?? 0)
        .attr("x2", (d) => (d.target as SimNode).x ?? 0)
        .attr("y2", (d) => (d.target as SimNode).y ?? 0);

      node.attr("cx", (d) => d.x ?? 0).attr("cy", (d) => d.y ?? 0);

      label.attr("x", (d) => (d.x ?? 0) + 12).attr("y", (d) => (d.y ?? 0) + 4);
    });

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
  }, [data]);

  return (
    <div className="bg-slate-900 rounded-2xl p-4 shadow-xl">
      <h2 className="text-white mb-4 text-lg font-semibold">
        Live Architecture Graph
      </h2>
      <svg ref={svgRef} width={800} height={500}></svg>
    </div>
  );
}
