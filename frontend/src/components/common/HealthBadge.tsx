import React from 'react';
import { useHealth } from '@/hooks/useHealth';
import { RefreshCw, Server } from 'lucide-react';

export const HealthBadge: React.FC = () => {
  const { health, loading, error, refetch } = useHealth(30000);

  const isConnected = !!health && health.status === 'ok';

  return (
    <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-100/80 border border-slate-200 rounded-lg text-xs font-medium">
      <Server className="w-3.5 h-3.5 text-slate-500" />
      <span className="text-slate-600">Backend:</span>
      {loading ? (
        <span className="flex items-center gap-1.5 text-slate-500">
          <span className="w-2 h-2 rounded-full bg-slate-400 animate-pulse"></span>
          Checking...
        </span>
      ) : isConnected ? (
        <span className="flex items-center gap-1.5 text-emerald-700 font-semibold">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          Connected
        </span>
      ) : (
        <span className="flex items-center gap-1.5 text-rose-700 font-semibold" title={error || 'Unavailable'}>
          <span className="w-2 h-2 rounded-full bg-rose-500"></span>
          Unavailable
        </span>
      )}
      <button
        onClick={() => refetch()}
        className="ml-1 text-slate-400 hover:text-slate-700 p-0.5 rounded transition-colors"
        title="Check Backend Health"
      >
        <RefreshCw className={`w-3 h-3 ${loading ? 'animate-spin' : ''}`} />
      </button>
    </div>
  );
};
