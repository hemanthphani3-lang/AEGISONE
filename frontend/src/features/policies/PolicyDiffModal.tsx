import React, { useEffect, useState } from 'react';
import { policyApi } from '@/services/api/policyApi';
import { PolicyDiffResponse } from '@/types/policy';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { Skeleton } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { Badge } from '@/components/ui/Badge';
import { GitCompare, PlusCircle, MinusCircle, CheckCircle2, ArrowRight } from 'lucide-react';

interface PolicyDiffModalProps {
  isOpen: boolean;
  onClose: () => void;
  policyId: string | null;
  fromVersion: number | null;
  toVersion: number | null;
}

export const PolicyDiffModal: React.FC<PolicyDiffModalProps> = ({
  isOpen,
  onClose,
  policyId,
  fromVersion,
  toVersion,
}) => {
  const [diff, setDiff] = useState<PolicyDiffResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && policyId && fromVersion !== null && toVersion !== null) {
      fetchDiff();
    } else {
      setDiff(null);
    }
  }, [isOpen, policyId, fromVersion, toVersion]);

  const fetchDiff = async () => {
    if (!policyId || fromVersion === null || toVersion === null) return;
    setLoading(true);
    setError(null);
    try {
      const res = await policyApi.getPolicyVersionDiff(policyId, fromVersion, toVersion);
      setDiff(res);
    } catch (err: any) {
      setError(err.message || 'Failed to compute policy version diff.');
    } finally {
      setLoading(false);
    }
  };

  if (!policyId || fromVersion === null || toVersion === null) return null;

  const hasScalarChanges = diff && diff.changed_fields.length > 0;
  const hasAddedItems = diff && Object.keys(diff.added_collection_items).length > 0;
  const hasRemovedItems = diff && Object.keys(diff.removed_collection_items).length > 0;
  const hasAnyChanges = hasScalarChanges || hasAddedItems || hasRemovedItems;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Deterministic Policy Diff: v${fromVersion} → v${toVersion}`}
      maxWidth="lg"
    >
      <div className="space-y-4 text-slate-800 text-xs">
        <div className="flex items-center gap-2 p-3 bg-indigo-50 border border-indigo-200 rounded-lg text-indigo-900">
          <GitCompare className="w-4 h-4 text-indigo-600 shrink-0" />
          <span>
            Comparing Policy <strong className="font-mono">{policyId}</strong> from base version{' '}
            <strong className="font-mono bg-indigo-100 px-1.5 py-0.5 rounded">v{fromVersion}</strong> to version{' '}
            <strong className="font-mono bg-indigo-100 px-1.5 py-0.5 rounded">v{toVersion}</strong>.
          </span>
        </div>

        {loading ? (
          <div className="space-y-3 py-4">
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-24 w-full" />
          </div>
        ) : error ? (
          <ErrorState title="Diff Calculation Failed" message={error} onRetry={fetchDiff} />
        ) : !hasAnyChanges ? (
          <div className="py-8 text-center text-slate-500 space-y-2 border border-dashed border-slate-200 rounded-lg bg-slate-50">
            <CheckCircle2 className="w-6 h-6 text-emerald-500 mx-auto" />
            <p className="font-semibold text-slate-700">No Policy Definition Changes</p>
            <p className="text-[11px]">
              Version <span className="font-mono">v{fromVersion}</span> and version{' '}
              <span className="font-mono">v{toVersion}</span> have identical definitions.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Modified Scalar & Field Diffs */}
            {hasScalarChanges && (
              <div className="border border-slate-200 rounded-lg overflow-hidden">
                <div className="bg-slate-100 px-3 py-2 font-semibold text-slate-700 border-b border-slate-200 flex items-center justify-between">
                  <span>Modified Fields</span>
                  <Badge variant="info">{diff.changed_fields.length} Changed</Badge>
                </div>
                <div className="divide-y divide-slate-200">
                  {diff.changed_fields.map((field) => {
                    const fieldDiff = diff.field_diffs[field];
                    if (!fieldDiff) return null;

                    return (
                      <div key={field} className="p-3 flex flex-col gap-1.5 bg-white">
                        <span className="font-mono font-bold text-indigo-700">{field}</span>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                          <div className="p-2 bg-rose-50/70 border border-rose-200 rounded text-rose-900 font-mono text-[11px] overflow-x-auto">
                            <span className="font-bold text-rose-700 block text-[10px] uppercase mb-0.5">
                              Previous (v{fromVersion}):
                            </span>
                            {JSON.stringify(fieldDiff.previous ?? null, null, 2)}
                          </div>
                          <div className="p-2 bg-emerald-50/70 border border-emerald-200 rounded text-emerald-900 font-mono text-[11px] overflow-x-auto">
                            <span className="font-bold text-emerald-700 block text-[10px] uppercase mb-0.5">
                              New (v{toVersion}):
                            </span>
                            {JSON.stringify(fieldDiff.new ?? null, null, 2)}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Added Collection Items */}
            {hasAddedItems && (
              <div className="border border-emerald-200 rounded-lg overflow-hidden bg-emerald-50/40">
                <div className="bg-emerald-100 px-3 py-2 font-semibold text-emerald-900 border-b border-emerald-200 flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <PlusCircle className="w-4 h-4 text-emerald-600 shrink-0" />
                    Added Scope & Exclusion Items
                  </span>
                  <Badge variant="success">Added</Badge>
                </div>
                <div className="p-3 space-y-2">
                  {Object.entries(diff.added_collection_items).map(([colKey, items]) => (
                    <div key={colKey} className="flex flex-col sm:flex-row sm:items-center gap-1.5 font-mono">
                      <span className="font-bold text-slate-700 min-w-32">{colKey}:</span>
                      <div className="flex flex-wrap gap-1">
                        {items.map((item, idx) => (
                          <span
                            key={idx}
                            className="bg-emerald-200 text-emerald-900 border border-emerald-300 px-2 py-0.5 rounded text-[11px] font-semibold"
                          >
                            + {String(item)}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Removed Collection Items */}
            {hasRemovedItems && (
              <div className="border border-rose-200 rounded-lg overflow-hidden bg-rose-50/40">
                <div className="bg-rose-100 px-3 py-2 font-semibold text-rose-900 border-b border-rose-200 flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <MinusCircle className="w-4 h-4 text-rose-600 shrink-0" />
                    Removed Scope & Exclusion Items
                  </span>
                  <Badge variant="danger">Removed</Badge>
                </div>
                <div className="p-3 space-y-2">
                  {Object.entries(diff.removed_collection_items).map(([colKey, items]) => (
                    <div key={colKey} className="flex flex-col sm:flex-row sm:items-center gap-1.5 font-mono">
                      <span className="font-bold text-slate-700 min-w-32">{colKey}:</span>
                      <div className="flex flex-wrap gap-1">
                        {items.map((item, idx) => (
                          <span
                            key={idx}
                            className="bg-rose-200 text-rose-900 border border-rose-300 px-2 py-0.5 rounded text-[11px] font-semibold"
                          >
                            - {String(item)}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="mt-6 pt-4 border-t border-slate-200 flex justify-end">
        <Button variant="outline" size="sm" onClick={onClose}>
          Close Diff
        </Button>
      </div>
    </Modal>
  );
};
