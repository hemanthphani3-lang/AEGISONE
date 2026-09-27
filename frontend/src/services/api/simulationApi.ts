import { apiClient } from './apiClient';
import { SimulationRequest, SimulationResult } from '@/types/simulation';

export const simulationApi = {
  simulatePolicies: (request: SimulationRequest): Promise<SimulationResult> => {
    return apiClient.post<SimulationResult>('/policies/simulate', request);
  },

  simulateEvaluate: (request: SimulationRequest): Promise<SimulationResult> => {
    return apiClient.post<SimulationResult>('/simulate/evaluate', request);
  },

  simulateEvaluateMe: (request: SimulationRequest): Promise<SimulationResult> => {
    return apiClient.post<SimulationResult>('/simulate/evaluate/me', request);
  },
};
