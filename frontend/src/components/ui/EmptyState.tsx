import React from 'react';
import { FolderX } from 'lucide-react';
import { Button } from './Button';

export interface EmptyStateProps {
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  icon?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  actionLabel,
  onAction,
  icon = <FolderX className="w-10 h-10 text-slate-400" />,
}) => {
  return (
    <div className="flex flex-col items-center justify-center text-center p-8 bg-slate-50 border border-dashed border-slate-200 rounded-xl my-4">
      <div className="p-3 bg-white rounded-full shadow-xs mb-3">{icon}</div>
      <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
      <p className="text-xs text-slate-500 mt-1 max-w-sm">{description}</p>
      {actionLabel && onAction && (
        <Button size="sm" onClick={onAction} className="mt-4">
          {actionLabel}
        </Button>
      )}
    </div>
  );
};
