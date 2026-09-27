import { apiClient } from './apiClient';

export type IncidentStatus =
  | 'OPEN'
  | 'ACKNOWLEDGED'
  | 'INVESTIGATING'
  | 'RESOLVED'
  | 'DISMISSED'
  | 'REOPENED';

export type IncidentSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export type IncidentEventType =
  | 'INCIDENT_CREATED'
  | 'INCIDENT_ACKNOWLEDGED'
  | 'INCIDENT_ASSIGNED'
  | 'INCIDENT_STATUS_CHANGED'
  | 'INCIDENT_RESOLVED'
  | 'INCIDENT_DISMISSED'
  | 'INCIDENT_COMMENTED'
  | 'INCIDENT_REOPENED'
  | 'INCIDENT_REMEDIATED';

export type RemediationAction =
  | 'DISABLE_POLICY'
  | 'ENABLE_POLICY'
  | 'ROLLBACK_POLICY';

export interface IncidentEvent {
  id: string;
  incident_id: string;
  event_type: IncidentEventType;
  actor_user_id: string;
  actor_username?: string;
  timestamp: string;
  correlation_id: string;
  metadata?: Record<string, any>;
}

export interface Incident {
  id: string;
  title: string;
  description: string;
  severity: IncidentSeverity;
  status: IncidentStatus;
  source_type: string;
  source_id?: string;
  policy_id?: string;
  finding_id?: string;
  fingerprint?: string;
  created_at: string;
  updated_at: string;
  created_by: string;
  assigned_to?: string;
  assigned_at?: string;
  assigned_by?: string;
  resolved_at?: string;
  resolved_by?: string;
  resolution_summary?: string;
  correlation_id: string;
  events?: IncidentEvent[];
}

export interface IncidentSummaryStats {
  total_incidents: number;
  open_incidents: number;
  critical_incidents: number;
  high_incidents: number;
  unassigned_incidents: number;
  policies_at_risk_count: number;
}

export interface RemediationRequest {
  action: RemediationAction;
  expected_version?: number;
  target_version?: number;
  reason: string;
}

export interface RemediationResponse {
  incident_id: string;
  remediation_action: RemediationAction;
  success: boolean;
  policy_id: string;
  message: string;
  timestamp: string;
}

export interface IncidentFilterParams {
  status?: string;
  severity?: string;
  policy_id?: string;
  assigned_to?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

export const incidentsApi = {
  async list(params?: IncidentFilterParams): Promise<{ incidents: Incident[]; total: number; page: number; page_size: number }> {
    const query = new URLSearchParams();
    if (params?.status) query.set('status', params.status);
    if (params?.severity) query.set('severity', params.severity);
    if (params?.policy_id) query.set('policy_id', params.policy_id);
    if (params?.assigned_to) query.set('assigned_to', params.assigned_to);
    if (params?.search) query.set('search', params.search);
    if (params?.page) query.set('page', params.page.toString());
    if (params?.page_size) query.set('page_size', params.page_size.toString());

    const queryString = query.toString();
    return apiClient.get<{ incidents: Incident[]; total: number; page: number; page_size: number }>(
      `/incidents${queryString ? `?${queryString}` : ''}`
    );
  },

  async getStats(): Promise<IncidentSummaryStats> {
    return apiClient.get<IncidentSummaryStats>('/incidents/stats');
  },

  async syncIntelligence(): Promise<{ success: boolean; created_count: number; created_incident_ids: string[] }> {
    return apiClient.post<{ success: boolean; created_count: number; created_incident_ids: string[] }>('/incidents/sync-intelligence', {});
  },

  async getById(id: string): Promise<Incident> {
    return apiClient.get<Incident>(`/incidents/${id}`);
  },

  async create(data: Partial<Incident>): Promise<Incident> {
    return apiClient.post<Incident>('/incidents', data);
  },

  async acknowledge(id: string): Promise<Incident> {
    return apiClient.post<Incident>(`/incidents/${id}/acknowledge`, {});
  },

  async assign(id: string, assignedTo?: string): Promise<Incident> {
    const url = assignedTo ? `/incidents/${id}/assign?assigned_to=${encodeURIComponent(assignedTo)}` : `/incidents/${id}/assign`;
    return apiClient.post<Incident>(url, {});
  },

  async resolve(id: string, summary: string): Promise<Incident> {
    return apiClient.post<Incident>(`/incidents/${id}/resolve?resolution_summary=${encodeURIComponent(summary)}`, {});
  },

  async dismiss(id: string, reason: string): Promise<Incident> {
    return apiClient.post<Incident>(`/incidents/${id}/dismiss?reason=${encodeURIComponent(reason)}`, {});
  },

  async reopen(id: string): Promise<Incident> {
    return apiClient.post<Incident>(`/incidents/${id}/reopen`, {});
  },

  async comment(id: string, text: string): Promise<Incident> {
    return apiClient.post<Incident>(`/incidents/${id}/comment?comment=${encodeURIComponent(text)}`, {});
  },

  async getEvents(id: string): Promise<IncidentEvent[]> {
    return apiClient.get<IncidentEvent[]>(`/incidents/${id}/events`);
  },

  async remediate(id: string, request: RemediationRequest): Promise<RemediationResponse> {
    return apiClient.post<RemediationResponse>(`/incidents/${id}/remediate`, request);
  },
};
