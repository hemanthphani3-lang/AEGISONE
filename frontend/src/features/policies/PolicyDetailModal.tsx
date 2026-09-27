import React from 'react';
import { Policy } from '@/types/policy';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { Shield } from 'lucide-react';

interface PolicyDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  policy: Policy | null;
}

export const PolicyDetailModal: React.FC<PolicyDetailModalProps> = ({
  isOpen,
  onClose,
  policy,
}) => {
  if (!policy) return null;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Policy Details" maxWidth="lg">
      <div className="space-y-4 text-xs">
        <div className="flex items-center justify-between p-3 bg-slate-50 border border-slate-200 rounded-lg">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-indigo-50 text-indigo-600 rounded-md">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <span>{policy.name}</span>
                <span className="text-[11px] font-mono text-indigo-700 bg-indigo-50 border border-indigo-200 px-1.5 py-0.5 rounded">
                  v{policy.version || 1}
                </span>
              </h4>
              <p className="font-mono text-[11px] text-slate-500">{policy.id}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={policy.enabled ? 'success' : 'outline'}>
              {policy.enabled ? 'Enabled' : 'Disabled'}
            </Badge>
            <Badge
              variant={
                policy.action === 'BLOCK'
                  ? 'danger'
                  : policy.action === 'MFA_REQUIRED'
                  ? 'warning'
                  : 'success'
              }
            >
              {policy.action}
            </Badge>
          </div>
        </div>

        <div>
          <label className="font-semibold text-slate-700 block mb-1">Description</label>
          <p className="text-slate-600 p-2.5 bg-slate-50 rounded-md border border-slate-100">
            {policy.description || 'No description provided.'}
          </p>
        </div>

        <div className="space-y-3 pt-2">
          <h4 className="font-semibold text-slate-800 border-b border-slate-100 pb-1">
            Target Conditions
          </h4>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="text-slate-500 block mb-1">Target Roles:</label>
              <div className="flex flex-wrap gap-1">
                {policy.target_roles && policy.target_roles.length > 0 ? (
                  policy.target_roles.map((r) => (
                    <Badge key={r} variant="info" className="font-mono">
                      {r}
                    </Badge>
                  ))
                ) : (
                  <span className="text-slate-400 italic">All Roles</span>
                )}
              </div>
            </div>

            <div>
              <label className="text-slate-500 block mb-1">Target Protocols:</label>
              <div className="flex flex-wrap gap-1">
                {policy.target_protocols && policy.target_protocols.length > 0 ? (
                  policy.target_protocols.map((p) => (
                    <Badge key={p} variant="outline" className="font-mono">
                      {p}
                    </Badge>
                  ))
                ) : (
                  <span className="text-slate-400 italic">All Protocols</span>
                )}
              </div>
            </div>

            <div>
              <label className="text-slate-500 block mb-1">Target Risk Level:</label>
              {policy.target_risk_level ? (
                <Badge variant="warning" className="font-mono">
                  {policy.target_risk_level}
                </Badge>
              ) : (
                <span className="text-slate-400 italic">Any Risk Level</span>
              )}
            </div>
          </div>
        </div>

        <div className="space-y-3 pt-2">
          <h4 className="font-semibold text-slate-800 border-b border-slate-100 pb-1">
            Exclusions
          </h4>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="text-slate-500 block mb-1">Excluded Roles:</label>
              <div className="flex flex-wrap gap-1">
                {policy.exclusions && policy.exclusions.length > 0 ? (
                  policy.exclusions.map((r) => (
                    <Badge key={r} variant="danger" className="font-mono">
                      {r}
                    </Badge>
                  ))
                ) : (
                  <span className="text-slate-400 italic">None</span>
                )}
              </div>
            </div>

            <div>
              <label className="text-slate-500 block mb-1">Excluded Users:</label>
              <div className="flex flex-wrap gap-1">
                {policy.excluded_users && policy.excluded_users.length > 0 ? (
                  policy.excluded_users.map((u) => (
                    <Badge key={u} variant="outline" className="font-mono">
                      {u}
                    </Badge>
                  ))
                ) : (
                  <span className="text-slate-400 italic">None</span>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="pt-4 flex justify-end">
          <Button variant="outline" size="sm" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </Modal>
  );
};
