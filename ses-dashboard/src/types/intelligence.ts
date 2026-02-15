// -----------------------------
// HEALTH HISTORY
// -----------------------------

export interface HealthScore {
  timestamp: string;
  health_score: number;
}

// -----------------------------
// FORECAST
// -----------------------------

export interface ForecastResult {
  status: string;
  forecast_next: number;
  confidence_interval: {
    lower: number;
    upper: number;
  };
  rmse: number;
  residual_variance: number;
  confidence_score: number;
  volatility: string;
}

export interface ForecastResponse {
  timestamp: string;
  history: HealthScore[];
  forecast: ForecastResult;
}

// -----------------------------
// HEALTH RESPONSE
// -----------------------------

export interface HealthResponse {
  timestamp: string;
  health_score?: number;
  architecture_health_score?: number;
  status?: string;
  risk_label?: string;
  stability_index?: number;
  confidence_score?: number;
  [key: string]: unknown;
}

// -----------------------------
// GRAPH TYPES (NEW)
// -----------------------------

export interface GraphNode {
  id: string;
}

export interface GraphEdge {
  source: string;
  target: string;
  call_count: number;
  avg_duration: number;
}

export interface GraphResponse {
  timestamp: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
}
