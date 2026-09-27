import React from 'react';
import { useToast } from '@/hooks/useToast';
import { AlertCircle, CheckCircle2, Info, X, XCircle } from 'lucide-react';

export const ToastContainer: React.FC = () => {
  const { toasts, removeToast } = useToast();

  if (toasts.length === 0) return null;

  const icons = {
    success: <CheckCircle2 className="w-5 h-5 text-emerald-500" />,
    error: <XCircle className="w-5 h-5 text-rose-500" />,
    warning: <AlertCircle className="w-5 h-5 text-amber-500" />,
    info: <Info className="w-5 h-5 text-blue-500" />,
  };

  const borders = {
    success: 'border-emerald-200 bg-emerald-50/90 text-emerald-950',
    error: 'border-rose-200 bg-rose-50/90 text-rose-950',
    warning: 'border-amber-200 bg-amber-50/90 text-amber-950',
    info: 'border-blue-200 bg-blue-50/90 text-blue-950',
  };

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`flex items-start p-4 rounded-xl border shadow-lg backdrop-blur-xs transition-all duration-200 pointer-events-auto ${
            borders[toast.type]
          }`}
        >
          <div className="shrink-0 mr-3 mt-0.5">{icons[toast.type]}</div>
          <div className="flex-1">
            <h4 className="text-xs font-semibold">{toast.title}</h4>
            {toast.message && <p className="text-xs mt-1 opacity-90">{toast.message}</p>}
          </div>
          <button
            onClick={() => removeToast(toast.id)}
            className="ml-3 shrink-0 text-slate-400 hover:text-slate-600 p-0.5 rounded"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      ))}
    </div>
  );
};
