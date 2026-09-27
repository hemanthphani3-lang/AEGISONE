import { apiClient } from './apiClient';

export interface IntelligenceFinding {
  finding_type: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  reason: string;
  affected_policy_ids: string[];
  recommendation: string;
}

export interface PolicyHealthSummary {
  policy_id: string;
  status: 'SAFE' | 'REVIEW' | 'WARNING' | 'CRITICAL';
  score: number;
  findings: IntelligenceFinding[];
}

export interface PolicyIntelligenceReport {
  total_policies: number;
  enabled_policies: number;
  disabled_policies: number;
  health_counts: {
    SAFE: number;
    REVIEW: number;
    WARNING: number;
    CRITICAL: number;
  };
  findings_count: number;
  policy_health_summaries: PolicyHealthSummary[];
  global_findings: IntelligenceFinding[];
}

export const intelligenceApi = {
  async getReport(): Promise<PolicyIntelligenceReport> {
    return apiClient.get<PolicyIntelligenceReport>('/policies/intelligence');
  },

  async getPolicyHealth(policyId: string): Promise<PolicyHealthSummary> {
    return apiClient.get<PolicyHealthSummary>(`/policies/${policyId}/health`);
  },

  async getPolicyConflicts(policyId: string): Promise<IntelligenceFinding[]> {
    return apiClient.get<IntelligenceFinding[]>(`/policies/${policyId}/conflicts`);
  },

  async getPolicyShadowed(policyId: string): Promise<IntelligenceFinding[]> {
    return apiClient.get<IntelligenceFinding[]>(`/policies/${policyId}/shadowed`);
  },
};
