import { apiClient } from './apiClient';
import { EvaluationResult, RequestContext } from '@/types/evaluation';

export const evaluationApi = {
  evaluate: (context: RequestContext): Promise<EvaluationResult> => {
    return apiClient.post<EvaluationResult>('/evaluate', context);
  },

  evaluateMe: (clientData?: Record<string, unknown>): Promise<EvaluationResult> => {
    return apiClient.post<EvaluationResult>('/evaluate/me', clientData || {});
  },
};
