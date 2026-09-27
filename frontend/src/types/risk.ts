import { RiskLevel } from './policy';

export interface RiskFactor {
  name: string;
  severity: RiskLevel;
  reason: string;
  details?: Record<string, unknown>;
}

export interface RiskAssessment {
  level: RiskLevel;
  factors: RiskFactor[];
  evaluated_at: string;
  confidence: string;
  trace: string;
}
