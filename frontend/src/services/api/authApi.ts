import { apiClient } from './apiClient';
import { AuthenticatedUser } from '@/types/auth';

export const authApi = {
  getMe: async (): Promise<AuthenticatedUser> => {
    return apiClient.get<AuthenticatedUser>('/auth/me');
  },
  sendMfaOtp: async (email?: string): Promise<{ success: boolean; delivery_status: string; cooldown_seconds: number; message: string }> => {
    return apiClient.post('/auth/mfa/send-otp', { email });
  },
  verifyMfaOtp: async (otp_code: string): Promise<{ success: boolean; mfa_completed: boolean; access_token?: string; message: string }> => {
    return apiClient.post('/auth/mfa/verify-otp', { otp_code });
  },
};

