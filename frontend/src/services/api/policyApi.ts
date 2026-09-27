import { apiClient } from './apiClient';
import {
  Policy,
  PolicyCreate,
  PolicyUpdate,
  PolicyValidationResponse,
  PolicyVersionListResponse,
  PolicyVersionDetail,
  PolicyDiffResponse,
  PolicyRollbackRequest,
} from '@/types/policy';

export const policyApi = {
  getPolicies: async (): Promise<Policy[]> => {
    const response = await apiClient.get<Policy[] | { policies: Policy[] }>('/policies');
    if (Array.isArray(response)) {
      return response;
    }
    if (response && Array.isArray((response as any).policies)) {
      return (response as any).policies;
    }
    return [];
  },

  getPolicy: (id: string): Promise<Policy> => {
    return apiClient.get<Policy>(`/policies/${id}`);
  },

  createPolicy: (data: PolicyCreate): Promise<Policy> => {
    return apiClient.post<Policy>('/policies', data);
  },

  updatePolicy: (id: string, data: PolicyUpdate): Promise<Policy> => {
    return apiClient.patch<Policy>(`/policies/${id}`, data);
  },

  deletePolicy: (id: string): Promise<{ message: string }> => {
    return apiClient.delete<{ message: string }>(`/policies/${id}`);
  },

  validatePolicy: (data: Partial<Policy>): Promise<PolicyValidationResponse> => {
    return apiClient.post<PolicyValidationResponse>('/policies/validate', data);
  },

  validateExistingPolicy: (id: string, data: Partial<Policy>): Promise<PolicyValidationResponse> => {
    return apiClient.post<PolicyValidationResponse>(`/policies/${id}/validate`, data);
  },

  getPolicyVersions: (id: string): Promise<PolicyVersionListResponse> => {
    return apiClient.get<PolicyVersionListResponse>(`/policies/${id}/versions`);
  },

  getPolicyVersionDetail: (id: string, version: number): Promise<PolicyVersionDetail> => {
    return apiClient.get<PolicyVersionDetail>(`/policies/${id}/versions/${version}`);
  },

  getPolicyVersionDiff: (
    id: string,
    version: number,
    againstVersion?: number
  ): Promise<PolicyDiffResponse> => {
    const params = againstVersion ? `?against_version=${againstVersion}` : '';
    return apiClient.get<PolicyDiffResponse>(`/policies/${id}/versions/${version}/diff${params}`);
  },

  rollbackPolicy: (id: string, data: PolicyRollbackRequest): Promise<Policy> => {
    return apiClient.post<Policy>(`/policies/${id}/rollback`, data);
  },
};

