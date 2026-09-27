import { UserRole } from './auth';
import { AuthProtocol, PolicyDecision } from './policy';

export interface AuthenticationContext {
  protocol: AuthProtocol;
  mfa_completed: boolean;
}

export interface DeviceContext {
  managed?: boolean | null;
  compliant?: boolean | null;
}

export interface RequestContext {
  user_id: string;
  role?: UserRole | null;
  roles?: UserRole[];
  location?: string;
  authentication: AuthenticationContext;
  device?: DeviceContext;
  risk?: string;
}

export interface SignalSummary {
  name: string;
  value?: any;
  source: string;
  status: string;
  confidence: string;
  metadata?: Record<string, any>;
}

export interface ConditionDetail {
  condition_type: string;
  result: string;
  reason: string;
}

export interface PolicyTraceSummary {
  policy_id: string;
  policy_name: string;
  enabled: boolean;
  matched: boolean;
  excluded?: boolean;
  exclusion_reason?: string | null;
  action: PolicyDecision;
  target_roles: UserRole[];
  target_protocols: AuthProtocol[];
  target_risk_level?: string | null;
  condition_details?: ConditionDetail[];
}

export interface EvaluationResult {
  decision: PolicyDecision;
  matched_policies: string[];
  reasons: string[];
  risk_level?: string | null;
  risk_factors?: string[];
  risk_trace?: string | null;
  evaluated_signals?: SignalSummary[];
  policy_traces?: PolicyTraceSummary[];
  decision_precedence_trace?: string | null;
  evaluated_at?: string;
  correlation_id?: string | null;
}
