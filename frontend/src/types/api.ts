export interface ApiError {
  status: number;
  message: string;
  detail?: string | Record<string, unknown>;
  correlationId?: string;
}

export interface HealthResponse {
  status: string;
  database: string;
  timestamp: string;
}
