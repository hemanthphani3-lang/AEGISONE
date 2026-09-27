import { useCallback, useEffect, useState } from 'react';
import { healthApi } from '@/services/api/healthApi';
import { HealthResponse } from '@/types/api';

export function useHealth(pollIntervalMs: number = 30000) {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const checkHealth = useCallback(async () => {
    setLoading(true);
    try {
      const data = await healthApi.checkHealth();
      setHealth(data);
      setError(null);
    } catch (err: any) {
      setHealth(null);
      setError(err.message || 'Backend service is unavailable.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkHealth();

    const interval = setInterval(() => {
      checkHealth();
    }, pollIntervalMs);

    return () => clearInterval(interval);
  }, [checkHealth, pollIntervalMs]);

  return { health, loading, error, refetch: checkHealth };
}
