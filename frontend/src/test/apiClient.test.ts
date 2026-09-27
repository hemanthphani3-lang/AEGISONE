import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiClient } from '@/services/api/apiClient';

describe('ApiClient Centralized HTTP Layer', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('parses 200 OK responses correctly', async () => {
    const mockData = { status: 'ok', database: 'connected', timestamp: '2026-09-26' };
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockData,
    }));

    const res = await apiClient.get('/health');
    expect(res).toEqual(mockData);
  });

  it('normalizes 401 Unauthorized errors correctly', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      headers: new Headers({ 'X-Correlation-ID': 'corr-123' }),
      json: async () => ({ detail: 'Authentication credentials were not provided.' }),
    }));

    try {
      await apiClient.get('/protected');
      expect.fail('Should have thrown ApiError');
    } catch (err: any) {
      expect(err.status).toBe(401);
      expect(err.message).toBe('Authentication credentials were not provided.');
      expect(err.correlationId).toBe('corr-123');
    }
  });

  it('normalizes 403 Forbidden errors correctly', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      status: 403,
      headers: new Headers({ 'X-Correlation-ID': 'corr-456' }),
      json: async () => ({ detail: 'Insufficient permissions to perform this action.' }),
    }));

    try {
      await apiClient.get('/admin-only');
      expect.fail('Should have thrown ApiError');
    } catch (err: any) {
      expect(err.status).toBe(403);
      expect(err.message).toBe('Insufficient permissions to perform this action.');
    }
  });

  it('normalizes 422 Unprocessable Entity validation errors correctly', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      status: 422,
      headers: new Headers(),
      json: async () => ({ detail: 'Unknown override field' }),
    }));

    try {
      await apiClient.post('/simulate/evaluate', { bad_field: true });
      expect.fail('Should have thrown ApiError');
    } catch (err: any) {
      expect(err.status).toBe(422);
      expect(err.message).toBe('Unknown override field');
    }
  });

  it('handles network failure cleanly', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('Failed to fetch')));

    try {
      await apiClient.get('/health');
      expect.fail('Should have thrown ApiError');
    } catch (err: any) {
      expect(err.status).toBe(0);
      expect(err.message).toContain('Network connection failed');
    }
  });
});
