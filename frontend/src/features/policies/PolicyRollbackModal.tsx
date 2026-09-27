import React, { useEffect, useState } from 'react';
import { policyApi } from '@/services/api/policyApi';
import { Policy, PolicyVersionDetail } from '@/types/policy';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { Skeleton } from '@/components/ui/Skeleton';
import { useToast } from '@/hooks/useToast';
import { RotateCcw, AlertTriangle, ShieldCheck, ArrowRight } from 'lucide-react';

interface PolicyRollbackModalProps {
  isOpen: boolean;
  onClose: () => void;
  policy: Policy | null;
  targetVersion: number | null;
  currentVersion: number | null;
  onSuccess: () => void;
  onConflict: (expected: number, current: number) => void;
}

export const PolicyRollbackModal: React.FC<PolicyRollbackModalProps> = ({
  isOpen,
  onClose,
  policy,
  targetVersion,
  currentVersion,
  onSuccess,
  onConflict,
}) => {
  const [loading, setLoading] = useState<boolean>(false);
  const [targetDetail, setTargetDetail] = useState<PolicyVersionDetail | null>(null);
  const [fetchLoading, setFetchLoading] = useState<boolean>(false);
  const { addToast } = useToast();

  useEffect(() => {
    if (isOpen && policy && targetVersion !== null) {
      loadSnapshotPreview();
    } else {
      setTargetDetail(null);
    }
  }, [isOpen, policy, targetVersion]);

  const loadSnapshotPreview = async () => {
    if (!policy || targetVersion === null) return;
    setFetchLoading(true);
    try {
      const detail = await policyApi.getPolicyVersionDetail(policy.id, targetVersion);
      setTargetDetail(detail);
    } catch (err: any) {
      addToast('error', 'Snapshot Load Failed', err.message || 'Failed to preview target version.');
    } finally {
      setFetchLoading(false);
    }
  };

  if (!policy || targetVersion === null) return null;

  const activeVer = currentVersion ?? policy.version ?? 1;
  const newVerNumber = activeVer + 1;

  const handleRollback = async () => {
    setLoading(true);
    try {
      const restored = await policyApi.rollbackPolicy(policy.id, {
        target_version: targetVersion,
        expected_current_version: activeVer,
      });

      addToast(
        'success',
        'Policy Rolled Back Successfully',
        `Policy '${restored.name}' restored from v${targetVersion} as new active version v${restored.version}.`
      );
      onSuccess();
      onClose();
    } catch (err: any) {
      if (err.status === 409 || err.code === 'POLICY_CONCURRENCY_CONFLICT' || (err.message && err.message.includes('409'))) {
        onClose();
        const conflictServerVer = err.detail?.current_version ?? (activeVer + 1);
        onConflict(activeVer, conflictServerVer);
      } else {
        addToast('error', 'Rollback Failed', err.message || 'Failed to rollback policy.');
      }
    } finally {
      setLoading(false);
    }
  };

  const snapshot = targetDetail?.snapshot;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Confirm Policy Rollback: ${policy.name}`}
      maxWidth="md"
    >
      <div className="space-y-4 text-slate-800 text-xs">
        <div className="flex items-start gap-3 p-3 bg-amber-50 border border-amber-200 rounded-lg text-amber-900">
          <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <span className="font-bold text-sm">Immutable Policy Rollback Notice</span>
            <p>
              Rolling back will restore definition snapshot <strong className="font-mono bg-amber-100 px-1 py-0.5 rounded">v{targetVersion}</strong> and issue it as a <strong>brand new active version v{newVerNumber}</strong>.
            </p>
            <p className="text-[11px] text-amber-800">
              Historical records (v1 through v{activeVer}) remain strictly immutable and will not be overwritten, deleted, or modified.
            </p>
          </div>
        </div>

        <div className="bg-slate-50 p-3 rounded-lg border border-slate-200 space-y-2">
          <div className="flex items-center justify-between font-mono">
            <span className="text-slate-500 font-sans">Policy ID:</span>
            <span className="font-bold">{policy.id}</span>
          </div>

          <div className="flex items-center justify-between font-mono">
            <span className="text-slate-500 font-sans">Version Lifecycle:</span>
            <div className="flex items-center gap-2">
              <span className="font-bold text-slate-700">v{activeVer}</span>
              <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
              <span className="font-bold text-indigo-600 bg-indigo-50 border border-indigo-200 px-1.5 py-0.2 rounded">
                v{newVerNumber} (New Active)
              </span>
            </div>
          </div>
        </div>

        {/* Snapshot Preview */}
        {fetchLoading ? (
          <Skeleton className="h-24 w-full" />
        ) : snapshot ? (
          <div className="border border-slate-200 rounded-lg p-3 bg-white space-y-2">
            <div className="font-semibold text-slate-800 flex items-center justify-between border-b border-slate-100 pb-1.5">
              <span>Restored Snapshot Definition (v{targetVersion})</span>
              <span
                className={`font-mono text-[10px] px-2 py-0.5 rounded font-bold ${
                  snapshot.action === 'BLOCK'
                    ? 'bg-rose-100 text-rose-800'
                    : snapshot.action === 'MFA_REQUIRED'
                    ? 'bg-amber-100 text-amber-800'
                    : 'bg-emerald-100 text-emerald-800'
                }`}
              >
                {snapshot.action}
              </span>
            </div>
            <div>
              <span className="text-slate-500 block text-[11px]">Name:</span>
              <span className="font-semibold text-slate-800">{snapshot.name}</span>
            </div>
            {snapshot.description && (
              <div>
                <span className="text-slate-500 block text-[11px]">Description:</span>
                <p className="text-slate-700 italic">{snapshot.description}</p>
              </div>
            )}
            <div className="flex flex-wrap gap-1.5 pt-1 font-mono text-[10px]">
              {snapshot.target_roles?.length > 0 && (
                <span className="bg-slate-100 px-2 py-0.5 rounded">
                  Roles: {snapshot.target_roles.join(', ')}
                </span>
              )}
              {snapshot.target_protocols?.length > 0 && (
                <span className="bg-slate-100 px-2 py-0.5 rounded">
                  Protocols: {snapshot.target_protocols.join(', ')}
                </span>
              )}
              {snapshot.exclusions?.length > 0 && (
                <span className="bg-rose-50 text-rose-800 px-2 py-0.5 rounded">
                  Exclusions: {snapshot.exclusions.join(', ')}
                </span>
              )}
            </div>
          </div>
        ) : null}

        <div className="pt-4 border-t border-slate-200 flex items-center justify-end gap-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button variant="danger" size="sm" onClick={handleRollback} loading={loading}>
            <RotateCcw className="w-3.5 h-3.5 mr-1" />
            Confirm Rollback to v{targetVersion}
          </Button>
        </div>
      </div>
    </Modal>
  );
};
