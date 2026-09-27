import React, { useEffect, useState } from 'react';
import { policyApi } from '@/services/api/policyApi';
import { Policy, PolicyVersionDetail, PolicyVersionSummary } from '@/types/policy';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { GitCompare, RotateCcw, Clock, User, Eye, ShieldCheck } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { UserRole } from '@/types/auth';
import { PolicyDetailModal } from './PolicyDetailModal';

interface PolicyHistoryModalProps {
  isOpen: boolean;
  onClose: () => void;
  policy: Policy | null;
  onOpenDiff: (fromVersion: number, toVersion: number) => void;
  onOpenRollback: (targetVersion: number, currentVersion: number) => void;
}

export const PolicyHistoryModal: React.FC<PolicyHistoryModalProps> = ({
  isOpen,
  onClose,
  policy,
  onOpenDiff,
  onOpenRollback,
}) => {
  const [versions, setVersions] = useState<PolicyVersionSummary[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Snapshot detail state
  const [selectedSnapshotPolicy, setSelectedSnapshotPolicy] = useState<Policy | null>(null);
  const [snapshotLoading, setSnapshotLoading] = useState<boolean>(false);

  const { hasAnyRole } = useAuth();
  const canWritePolicy = hasAnyRole([UserRole.ADMIN, UserRole.SECURITY_ADMIN]);

  useEffect(() => {
    if (isOpen && policy) {
      fetchHistory();
    } else {
      setVersions([]);
    }
  }, [isOpen, policy]);

  const fetchHistory = async () => {
    if (!policy) return;
    setLoading(true);
    setError(null);
    try {
      const res = await policyApi.getPolicyVersions(policy.id);
      setVersions(res.versions || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load policy version history.');
    } finally {
      setLoading(false);
    }
  };

  const handleViewSnapshot = async (versionNumber: number) => {
    if (!policy) return;
    setSnapshotLoading(true);
    try {
      const detail: PolicyVersionDetail = await policyApi.getPolicyVersionDetail(policy.id, versionNumber);
      setSelectedSnapshotPolicy(detail.snapshot);
    } catch (err: any) {
      alert(err.message || 'Failed to load version snapshot detail.');
    } finally {
      setSnapshotLoading(false);
    }
  };

  const getChangeBadgeVariant = (changeType: string) => {
    switch (changeType.toUpperCase()) {
      case 'CREATE':
        return 'success';
      case 'UPDATE':
        return 'info';
      case 'ENABLE':
        return 'success';
      case 'DISABLE':
        return 'warning';
      case 'ROLLBACK':
        return 'danger';
      default:
        return 'outline';
    }
  };

  if (!policy) return null;

  return (
    <>
      <Modal
        isOpen={isOpen}
        onClose={onClose}
        title={`Version History Timeline: ${policy.name}`}
        maxWidth="lg"
      >
        <div className="space-y-4 text-slate-800">
          <div className="flex items-center justify-between pb-3 border-b border-slate-200">
            <div>
              <span className="text-xs font-mono text-slate-500">Policy ID: {policy.id}</span>
              <p className="text-xs text-slate-600 mt-0.5">
                Current Active Version:{' '}
                <span className="font-mono font-bold text-indigo-600">v{policy.version || 1}</span>
              </p>
            </div>
            <Button variant="outline" size="sm" onClick={fetchHistory} disabled={loading}>
              Refresh History
            </Button>
          </div>

          {loading ? (
            <div className="space-y-3 py-4">
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
            </div>
          ) : error ? (
            <ErrorState title="History Load Failed" message={error} onRetry={fetchHistory} />
          ) : versions.length === 0 ? (
            <p className="text-xs text-slate-500 py-6 text-center">
              No historical version snapshots recorded for this policy yet.
            </p>
          ) : (
            <div className="relative pl-6 space-y-5 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
              {versions.map((ver, idx) => {
                const isCurrent = ver.version === (policy.version || 1);
                const prevVer = versions[idx + 1]?.version;

                return (
                  <div key={ver.id} className="relative group">
                    <div
                      className={`absolute -left-6 top-1.5 w-5 h-5 rounded-full border-2 flex items-center justify-center bg-white ${
                        isCurrent
                          ? 'border-indigo-600 text-indigo-600 font-bold shadow-xs'
                          : 'border-slate-300 text-slate-400'
                      }`}
                    >
                      <div
                        className={`w-2 h-2 rounded-full ${
                          isCurrent ? 'bg-indigo-600 animate-pulse' : 'bg-slate-300'
                        }`}
                      />
                    </div>

                    <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 hover:border-slate-300 transition-colors">
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-sm font-bold text-slate-900">
                            v{ver.version}
                          </span>
                          <Badge variant={getChangeBadgeVariant(ver.change_type)}>
                            {ver.change_type}
                          </Badge>
                          {isCurrent && (
                            <span className="text-[10px] font-semibold text-indigo-700 bg-indigo-100 border border-indigo-200 px-2 py-0.5 rounded-full flex items-center gap-1">
                              <ShieldCheck className="w-3 h-3 text-indigo-600" />
                              CURRENT ACTIVE
                            </span>
                          )}
                        </div>

                        <div className="flex flex-wrap items-center gap-1.5">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleViewSnapshot(ver.version)}
                            disabled={snapshotLoading}
                            className="h-7 text-xs text-slate-700 hover:bg-slate-200"
                            title="View Historical Snapshot"
                          >
                            <Eye className="w-3.5 h-3.5 mr-1 text-slate-500" />
                            View
                          </Button>

                          {prevVer && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => onOpenDiff(prevVer, ver.version)}
                              className="h-7 text-xs text-slate-700 hover:bg-slate-200"
                              title={`Compare v${prevVer} against v${ver.version}`}
                            >
                              <GitCompare className="w-3.5 h-3.5 mr-1 text-slate-500" />
                              Compare v{prevVer}
                            </Button>
                          )}

                          {canWritePolicy && !isCurrent && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() =>
                                onOpenRollback(ver.version, policy.version || 1)
                              }
                              className="h-7 text-xs text-rose-700 border-rose-200 hover:bg-rose-50 font-medium"
                              title={`Rollback policy to v${ver.version}`}
                            >
                              <RotateCcw className="w-3.5 h-3.5 mr-1" />
                              Rollback
                            </Button>
                          )}
                        </div>
                      </div>

                      <div className="mt-2 flex flex-wrap items-center gap-4 text-xs text-slate-500">
                        <div className="flex items-center gap-1">
                          <User className="w-3.5 h-3.5 text-slate-400" />
                          <span>
                            Actor:{' '}
                            <strong className="text-slate-700 font-mono">
                              {ver.changed_by_username || ver.changed_by_user_id}
                            </strong>
                          </span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5 text-slate-400" />
                          <span>{new Date(ver.changed_at).toLocaleString()}</span>
                        </div>
                        <div className="font-mono text-[10px] text-slate-400">
                          CID: {ver.correlation_id.substring(0, 8)}...
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div className="mt-6 pt-4 border-t border-slate-200 flex justify-end">
          <Button variant="outline" size="sm" onClick={onClose}>
            Close History
          </Button>
        </div>
      </Modal>

      {/* Historical Snapshot Detail View Modal */}
      <PolicyDetailModal
        isOpen={!!selectedSnapshotPolicy}
        onClose={() => setSelectedSnapshotPolicy(null)}
        policy={selectedSnapshotPolicy}
      />
    </>
  );
};
