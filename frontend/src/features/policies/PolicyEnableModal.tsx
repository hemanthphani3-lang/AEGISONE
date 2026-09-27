import React from 'react';
import { Policy } from '@/types/policy';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { Power, ShieldAlert } from 'lucide-react';

interface PolicyEnableModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => Promise<void>;
  policy: Policy | null;
  loading?: boolean;
}

export const PolicyEnableModal: React.FC<PolicyEnableModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  policy,
  loading = false,
}) => {
  if (!policy) return null;

  const isEnabling = !policy.enabled;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEnabling ? `Enable Policy: ${policy.name}` : `Disable Policy: ${policy.name}`}
      maxWidth="sm"
    >
      <div className="space-y-4 text-xs">
        <div
          className={`flex items-start gap-3 p-3 rounded-lg border ${
            isEnabling
              ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
              : 'bg-amber-50 border-amber-200 text-amber-900'
          }`}
        >
          <Power
            className={`w-5 h-5 shrink-0 mt-0.5 ${
              isEnabling ? 'text-emerald-600' : 'text-amber-600'
            }`}
          />
          <div className="space-y-1">
            <h4 className="font-semibold">
              Confirm Policy {isEnabling ? 'Activation' : 'Deactivation'}
            </h4>
            <p className="text-[11px] leading-relaxed">
              {isEnabling
                ? `Activating policy '${policy.name}' (v${policy.version || 1}) will cause it to be immediately evaluated against all matching zero-trust access requests.`
                : `Disabling policy '${policy.name}' (v${policy.version || 1}) will suspend its evaluation rules until re-enabled.`}
            </p>
            <div className="pt-1 font-mono text-[10px] opacity-80">
              Policy ID: {policy.id} | Action: {policy.action}
            </div>
          </div>
        </div>

        <div className="pt-2 flex justify-end gap-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button
            variant={isEnabling ? 'primary' : 'outline'}
            size="sm"
            onClick={onConfirm}
            loading={loading}
            className={!isEnabling ? 'text-amber-700 border-amber-300 hover:bg-amber-50' : ''}
          >
            {isEnabling ? 'Enable Policy' : 'Disable Policy'}
          </Button>
        </div>
      </div>
    </Modal>
  );
};
