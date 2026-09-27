import { UserRole } from './auth';
import { RequestContext } from './evaluation';
import { AuthProtocol, PolicyDecision, RiskLevel } from './policy';

export interface SimulationOverrides {
  roles?: UserRole[];
  auth_protocol?: AuthProtocol;
  mfa_completed?: boolean;
  device_compliant?: boolean;
  device_managed?: boolean;
  location?: string;
  network_type?: string;
  risk_level?: RiskLevel;
}

export interface SimulationRequest {
  base_context?: RequestContext;
  client_data?: Record<string, unknown>;
  overrides?: SimulationOverrides;
  policy_ids?: string[];
}

export interface PolicyChangeTrace {
  policy_id: string;
  policy_name: string;
  base_matched: boolean;
  simulated_matched: boolean;
  change_summary: string;
}

export interface SimulationTrace {
  base_decision: PolicyDecision;
  simulated_decision: PolicyDecision;
  decision_changed: boolean;
  base_risk: RiskLevel;
  simulated_risk: RiskLevel;
  risk_changed: boolean;
  overrides_applied: Record<string, unknown>;
  policy_changes: PolicyChangeTrace[];
  explanation: string;
}

import { EvaluationResult } from './evaluation';

export interface SimulationResult {
  simulation_id: string;
  correlation_id?: string | null;
  created_at: string;
  base_decision: PolicyDecision;
  simulated_decision: PolicyDecision;
  decision_changed: boolean;
  base_risk: RiskLevel;
  simulated_risk: RiskLevel;
  risk_changed: boolean;
  overrides_applied: SimulationOverrides;
  trace: SimulationTrace;
  evaluation_result?: EvaluationResult | null;
}
