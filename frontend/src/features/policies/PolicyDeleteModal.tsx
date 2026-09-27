import React from 'react';
import { Policy } from '@/types/policy';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { AlertTriangle } from 'lucide-react';

interface PolicyDeleteModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => Promise<void>;
  policy: Policy | null;
  loading?: boolean;
}

export const PolicyDeleteModal: React.FC<PolicyDeleteModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  policy,
  loading = false,
}) => {
  if (!policy) return null;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Confirm Policy Deletion" maxWidth="sm">
      <div className="space-y-4 text-xs">
        <div className="flex items-start gap-3 p-3 bg-rose-50 border border-rose-200 text-rose-900 rounded-lg">
          <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h4 className="font-semibold text-rose-950">Are you sure you want to delete this policy?</h4>
            <p className="text-rose-800 text-[11px]">
              This action will permanently remove policy <strong className="font-mono">{policy.id}</strong> ({policy.name}) from the backend database repository.
            </p>
            <div className="pt-1 flex items-center gap-2 font-mono text-[10px] text-rose-700">
              <span>Version: v{policy.version || 1}</span>
              <span>•</span>
              <span>Status: {policy.enabled ? 'Active' : 'Disabled'}</span>
            </div>
          </div>
        </div>

        <div className="pt-2 flex justify-end gap-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button variant="danger" size="sm" onClick={onConfirm} loading={loading}>
            Delete Policy
          </Button>
        </div>
      </div>
    </Modal>
  );
};
