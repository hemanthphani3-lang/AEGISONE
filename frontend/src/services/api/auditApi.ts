import { apiClient } from './apiClient';
import { AuditEvent } from '@/types/audit';

export interface AuditQueryFilter {
  event_type?: string;
  actor_user_id?: string;
  resource_type?: string;
  resource_id?: string;
  outcome?: string;
  correlation_id?: string;
  limit?: number;
  offset?: number;
}

export interface AuditEventListResponse {
  events: AuditEvent[];
  total: number;
  limit: number;
  offset: number;
}

export const auditApi = {
  queryEvents: async (filter?: AuditQueryFilter): Promise<AuditEventListResponse> => {
    const params = new URLSearchParams();
    if (filter) {
      if (filter.event_type) params.append('event_type', filter.event_type);
      if (filter.actor_user_id) params.append('actor_user_id', filter.actor_user_id);
      if (filter.resource_type) params.append('resource_type', filter.resource_type);
      if (filter.resource_id) params.append('resource_id', filter.resource_id);
      if (filter.outcome) params.append('outcome', filter.outcome);
      if (filter.correlation_id) params.append('correlation_id', filter.correlation_id);
      if (filter.limit !== undefined) params.append('limit', filter.limit.toString());
      if (filter.offset !== undefined) params.append('offset', filter.offset.toString());
    }

    const queryString = params.toString();
    const path = queryString ? `/audit/events?${queryString}` : '/audit/events';
    const response = await apiClient.get<AuditEventListResponse | AuditEvent[]>(path);
    if (Array.isArray(response)) {
      return { events: response, total: response.length, limit: filter?.limit || 50, offset: filter?.offset || 0 };
    }
    return response;
  },
};
