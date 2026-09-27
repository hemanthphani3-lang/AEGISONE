import React from 'react';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { AlertTriangle, RefreshCw, XCircle } from 'lucide-react';

interface ConcurrencyConflictModalProps {
  isOpen: boolean;
  onClose: () => void;
  policyId: string | null;
  expectedVersion: number | null;
  currentVersion: number | null;
  onReloadLatest: () => void;
}

export const ConcurrencyConflictModal: React.FC<ConcurrencyConflictModalProps> = ({
  isOpen,
  onClose,
  policyId,
  expectedVersion,
  currentVersion,
  onReloadLatest,
}) => {
  if (!policyId) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="409 Policy Concurrency Conflict"
      maxWidth="md"
    >
      <div className="space-y-4 text-slate-800 text-xs">
        <div className="flex items-start gap-3 p-3 bg-amber-50 border border-amber-200 rounded-lg text-amber-900">
          <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <span className="font-bold text-sm">Concurrent Modification Detected</span>
            <p>
              Another administrator updated policy <strong className="font-mono">{policyId}</strong>{' '}
              while you were making changes.
            </p>
            <p className="text-[11px] text-amber-800">
              To prevent accidental overwrites of remote changes, your submission was blocked by server-side optimistic concurrency control.
            </p>
          </div>
        </div>

        <div className="bg-slate-50 p-3 rounded-lg border border-slate-200 grid grid-cols-2 gap-3 text-center font-mono">
          <div className="p-2 bg-white rounded border border-slate-200">
            <span className="text-[10px] text-slate-500 uppercase block font-sans font-semibold">
              Your Form Version
            </span>
            <span className="text-sm font-bold text-amber-600">v{expectedVersion ?? 1}</span>
          </div>

          <div className="p-2 bg-white rounded border border-slate-200">
            <span className="text-[10px] text-slate-500 uppercase block font-sans font-semibold">
              Server Active Version
            </span>
            <span className="text-sm font-bold text-indigo-600">v{currentVersion ?? '?'}</span>
          </div>
        </div>

        <p className="text-slate-600">
          Your un-saved form inputs are currently preserved. Choose <strong className="text-slate-800">Reload Latest</strong> to discard local changes and repopulate the editor with server version <strong className="font-mono">v{currentVersion}</strong>, or <strong className="text-slate-800">Cancel</strong> to close.
        </p>

        <div className="pt-4 border-t border-slate-200 flex items-center justify-end gap-2">
          <Button variant="outline" size="sm" onClick={onClose}>
            <XCircle className="w-3.5 h-3.5 mr-1" />
            Cancel
          </Button>
          <Button variant="primary" size="sm" onClick={onReloadLatest}>
            <RefreshCw className="w-3.5 h-3.5 mr-1" />
            Reload Latest (v{currentVersion})
          </Button>
        </div>
      </div>
    </Modal>
  );
};
