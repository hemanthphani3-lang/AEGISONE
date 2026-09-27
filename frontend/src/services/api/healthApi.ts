import { apiClient } from './apiClient';
import { HealthResponse } from '@/types/api';

export const healthApi = {
  checkHealth: (): Promise<HealthResponse> => {
    return apiClient.get<HealthResponse>('/health');
  },
};
