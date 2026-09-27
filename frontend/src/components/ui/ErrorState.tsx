import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from './Button';

export interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  status?: number;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Failed to load data',
  message,
  onRetry,
  status,
}) => {
  return (
    <div className="flex flex-col items-center justify-center text-center p-8 bg-rose-50/50 border border-rose-200 rounded-xl my-4">
      <div className="p-3 bg-rose-100 text-rose-600 rounded-full mb-3">
        <AlertTriangle className="w-6 h-6" />
      </div>
      <h3 className="text-sm font-semibold text-rose-900">
        {status ? `[${status}] ${title}` : title}
      </h3>
      <p className="text-xs text-rose-700 mt-1 max-w-md">{message}</p>
      {onRetry && (
        <Button variant="outline" size="sm" onClick={onRetry} className="mt-4 border-rose-300 text-rose-800 hover:bg-rose-100">
          <RefreshCw className="w-3.5 h-3.5 mr-1.5" /> Retry
        </Button>
      )}
    </div>
  );
};
