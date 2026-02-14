export interface HealthScore {
  timestamp: string;
  health_score: number;
}

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
