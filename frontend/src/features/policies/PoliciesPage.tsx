import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { policyApi } from '@/services/api/policyApi';
import { intelligenceApi, PolicyHealthSummary } from '@/services/api/intelligenceApi';
import { Policy, PolicyCreate, PolicyDecision, PolicyUpdate } from '@/types/policy';
import { useAuth } from '@/hooks/useAuth';
import { useToast } from '@/hooks/useToast';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorState } from '@/components/ui/ErrorState';
import { Skeleton } from '@/components/ui/Skeleton';
import { PolicyDetailModal } from './PolicyDetailModal';
import { PolicyFormModal } from './PolicyFormModal';
import { PolicyDeleteModal } from './PolicyDeleteModal';
import { PolicyEnableModal } from './PolicyEnableModal';
import { PolicyHistoryModal } from './PolicyHistoryModal';
import { PolicyDiffModal } from './PolicyDiffModal';
import { PolicyRollbackModal } from './PolicyRollbackModal';
import { ConcurrencyConflictModal } from './ConcurrencyConflictModal';
import { Eye, Edit2, Plus, Power, RefreshCw, Search, Shield, Play, Trash2, Filter, History, ShieldAlert, ShieldCheck } from 'lucide-react';
import { UserRole } from '@/types/auth';

export const PoliciesPage: React.FC = () => {
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [healthMap, setHealthMap] = useState<Record<string, PolicyHealthSummary>>({});
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Search & Filters
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'ENABLED' | 'DISABLED'>('ALL');
  const [actionFilter, setActionFilter] = useState<'ALL' | PolicyDecision>('ALL');

  // Modal states
  const [selectedDetailPolicy, setSelectedDetailPolicy] = useState<Policy | null>(null);
  const [isFormOpen, setIsFormOpen] = useState<boolean>(false);
  const [editingPolicy, setEditingPolicy] = useState<Policy | null>(null);
  const [deletingPolicy, setDeletingPolicy] = useState<Policy | null>(null);
  const [toggleStatusPolicy, setToggleStatusPolicy] = useState<Policy | null>(null);
  const [historyPolicy, setHistoryPolicy] = useState<Policy | null>(null);
  const [diffState, setDiffState] = useState<{
    isOpen: boolean;
    policyId: string | null;
    fromVersion: number | null;
    toVersion: number | null;
  }>({ isOpen: false, policyId: null, fromVersion: null, toVersion: null });
  const [rollbackState, setRollbackState] = useState<{
    isOpen: boolean;
    policy: Policy | null;
    targetVersion: number | null;
    currentVersion: number | null;
  }>({ isOpen: false, policy: null, targetVersion: null, currentVersion: null });
  const [conflictState, setConflictState] = useState<{
    isOpen: boolean;
    policyId: string | null;
    expectedVersion: number | null;
    currentVersion: number | null;
  }>({ isOpen: false, policyId: null, expectedVersion: null, currentVersion: null });

  const [formLoading, setFormLoading] = useState<boolean>(false);
  const [deleteLoading, setDeleteLoading] = useState<boolean>(false);
  const [toggleLoading, setToggleLoading] = useState<boolean>(false);

  const { addToast } = useToast();
  const { hasAnyRole } = useAuth();
  const navigate = useNavigate();

  const canWritePolicy = hasAnyRole([UserRole.ADMIN, UserRole.SECURITY_ADMIN]);

  const fetchPolicies = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await policyApi.getPolicies();
      setPolicies(Array.isArray(data) ? data : []);

      try {
        const intel = await intelligenceApi.getReport();
        const map: Record<string, PolicyHealthSummary> = {};
        for (const s of intel.policy_health_summaries) {
          map[s.policy_id] = s;
        }
        setHealthMap(map);
      } catch (e) {
        console.warn('Failed to load intelligence report:', e);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch policies from backend.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPolicies();
  }, []);

  const handleOpenCreate = () => {
    setEditingPolicy(null);
    setIsFormOpen(true);
  };

  const handleOpenEdit = (policy: Policy) => {
    setEditingPolicy(policy);
    setIsFormOpen(true);
  };

  const handleFormSubmit = async (data: PolicyCreate | PolicyUpdate) => {
    setFormLoading(true);
    try {
      if (editingPolicy) {
        await policyApi.updatePolicy(editingPolicy.id, data as PolicyUpdate);
        addToast('success', 'Policy Updated', `Policy '${data.name}' saved successfully.`);
      } else {
        await policyApi.createPolicy(data as PolicyCreate);
        addToast('success', 'Policy Created', `Policy '${data.name}' created successfully.`);
      }
      await fetchPolicies();
      setIsFormOpen(false);
    } catch (err: any) {
      if (err.status === 409 || err.code === 'POLICY_CONCURRENCY_CONFLICT' || (err.message && err.message.includes('409'))) {
        setIsFormOpen(false);
        const expVer = (data as PolicyUpdate).expected_version ?? editingPolicy?.version ?? 1;
        const srvVer = err.detail?.current_version ?? (expVer + 1);
        setConflictState({
          isOpen: true,
          policyId: editingPolicy?.id || (data as PolicyCreate).id,
          expectedVersion: expVer,
          currentVersion: srvVer,
        });
      } else if (err.status === 404) {
        addToast('error', 'Policy Deleted', 'This policy no longer exists on the server.');
        setIsFormOpen(false);
        await fetchPolicies();
      } else if (err.status === 403) {
        addToast('error', 'Permission Denied', 'You do not have permission to modify policies.');
      } else {
        addToast('error', 'Operation Failed', err.message || 'Failed to save policy.');
      }
      throw err;
    } finally {
      setFormLoading(false);
    }
  };

  const handleConfirmToggleEnable = async () => {
    if (!toggleStatusPolicy) return;
    setToggleLoading(true);
    try {
      const updated = await policyApi.updatePolicy(toggleStatusPolicy.id, {
        enabled: !toggleStatusPolicy.enabled,
        expected_version: toggleStatusPolicy.version,
      });
      addToast(
        'success',
        toggleStatusPolicy.enabled ? 'Policy Disabled' : 'Policy Enabled',
        `Policy '${updated.name}' (v${updated.version || 1}) is now ${
          updated.enabled ? 'Enabled' : 'Disabled'
        }.`
      );
      setToggleStatusPolicy(null);
      await fetchPolicies();
    } catch (err: any) {
      if (err.status === 409 || err.code === 'POLICY_CONCURRENCY_CONFLICT' || (err.message && err.message.includes('409'))) {
        setToggleStatusPolicy(null);
        const srvVer = err.detail?.current_version ?? ((toggleStatusPolicy.version || 1) + 1);
        setConflictState({
          isOpen: true,
          policyId: toggleStatusPolicy.id,
          expectedVersion: toggleStatusPolicy.version || 1,
          currentVersion: srvVer,
        });
      } else if (err.status === 404) {
        addToast('error', 'Policy Deleted', 'This policy no longer exists on the server.');
        setToggleStatusPolicy(null);
        await fetchPolicies();
      } else {
        addToast('error', 'Update Failed', err.message || 'Failed to update policy status.');
      }
    } finally {
      setToggleLoading(false);
    }
  };

  const handleDeleteConfirm = async () => {
    if (!deletingPolicy) return;
    setDeleteLoading(true);
    try {
      await policyApi.deletePolicy(deletingPolicy.id);
      addToast('success', 'Policy Deleted', `Policy '${deletingPolicy.name}' deleted.`);
      setDeletingPolicy(null);
      await fetchPolicies();
    } catch (err: any) {
      if (err.status === 404) {
        addToast('info', 'Policy Already Deleted', 'This policy was already removed.');
        setDeletingPolicy(null);
        await fetchPolicies();
      } else {
        addToast('error', 'Deletion Failed', err.message || 'Failed to delete policy.');
      }
    } finally {
      setDeleteLoading(false);
    }
  };

  const handleReloadLatestConflict = async () => {
    if (!conflictState.policyId) return;
    setConflictState({ ...conflictState, isOpen: false });
    await fetchPolicies();
    try {
      const latest = await policyApi.getPolicy(conflictState.policyId);
      setEditingPolicy(latest);
      setIsFormOpen(true);
      addToast('info', 'Policy Reloaded', `Loaded active server version v${latest.version || 1}.`);
    } catch (err: any) {
      if (err.status === 404) {
        addToast('error', 'Policy Deleted', 'The policy was deleted by another administrator.');
      } else {
        addToast('error', 'Reload Failed', err.message || 'Failed to load latest policy version.');
      }
    }
  };

  // Filter policies
  const filteredPolicies = policies.filter((p) => {
    const matchesSearch =
      !searchTerm ||
      p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.description.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus =
      statusFilter === 'ALL'
        ? true
        : statusFilter === 'ENABLED'
        ? p.enabled
        : !p.enabled;

    const matchesAction = actionFilter === 'ALL' ? true : p.action === actionFilter;

    return matchesSearch && matchesStatus && matchesAction;
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <span>Policy Management</span>
            <span className="text-xs font-mono text-indigo-700 bg-indigo-50 border border-indigo-200 px-2 py-0.5 rounded-full">
              {policies.length} Policies
            </span>
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Authoritative zero-trust access policies with server-side validation and version control
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={fetchPolicies} disabled={loading}>
            <RefreshCw className={`w-3.5 h-3.5 mr-1 ${loading ? 'animate-spin' : ''}`} /> Refresh
          </Button>
          {canWritePolicy && (
            <Button variant="primary" size="sm" onClick={handleOpenCreate}>
              <Plus className="w-3.5 h-3.5 mr-1" /> Create Policy
            </Button>
          )}
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 p-3 bg-slate-50 border border-slate-200 rounded-lg">
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            className="w-full pl-9 pr-3 py-1.5 text-xs border border-slate-300 rounded-md focus:ring-1 focus:ring-indigo-500 bg-white"
            placeholder="Search policies by ID, name, or description..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <div className="flex items-center gap-1.5 text-xs text-slate-600 shrink-0">
            <Filter className="w-3.5 h-3.5 text-slate-500" />
            <span className="font-semibold">Filter:</span>
          </div>

          <select
            className="text-xs border border-slate-300 rounded-md p-1.5 bg-white font-medium"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as any)}
          >
            <option value="ALL">All Statuses</option>
            <option value="ENABLED">Enabled</option>
            <option value="DISABLED">Disabled</option>
          </select>

          <select
            className="text-xs border border-slate-300 rounded-md p-1.5 bg-white font-medium"
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value as any)}
          >
            <option value="ALL">All Actions</option>
            <option value={PolicyDecision.MFA_REQUIRED}>MFA_REQUIRED</option>
            <option value={PolicyDecision.BLOCK}>BLOCK</option>
            <option value={PolicyDecision.ALLOW}>ALLOW</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="space-y-3">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
        </div>
      ) : error ? (
        <ErrorState title="Policy Retrieval Failed" message={error} onRetry={fetchPolicies} />
      ) : filteredPolicies.length === 0 ? (
        <EmptyState
          title="No Matching Policies Found"
          description={
            policies.length === 0
              ? 'There are currently no conditional access policies configured.'
              : 'No policies match your search and filter criteria.'
          }
          actionLabel={policies.length === 0 && canWritePolicy ? 'Create First Policy' : undefined}
          onAction={policies.length === 0 && canWritePolicy ? handleOpenCreate : undefined}
        />
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {filteredPolicies.map((policy) => (
            <Card key={policy.id} className="hover:border-slate-300 transition-colors">
              <CardHeader className="flex flex-row items-center justify-between pb-3">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
                    <Shield className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <CardTitle className="text-sm font-semibold">{policy.name}</CardTitle>
                      <span className="text-[10px] font-mono text-indigo-700 bg-indigo-50 border border-indigo-200 px-1.5 py-0.2 rounded">
                        v{policy.version || 1}
                      </span>
                    </div>
                    <CardDescription className="text-xs font-mono">{policy.id}</CardDescription>
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

                  {healthMap[policy.id] && (
                    <Badge
                      variant={
                        healthMap[policy.id].status === 'SAFE'
                          ? 'success'
                          : healthMap[policy.id].status === 'REVIEW'
                          ? 'info'
                          : healthMap[policy.id].status === 'WARNING'
                          ? 'warning'
                          : 'danger'
                      }
                      className="font-mono text-[10px]"
                      title={healthMap[policy.id].findings.map((f) => f.reason).join(' | ') || 'Policy is safe'}
                    >
                      HEALTH: {healthMap[policy.id].status} ({healthMap[policy.id].score})
                    </Badge>
                  )}

                  <div className="flex items-center gap-1 pl-2 border-l border-slate-200">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => navigate('/admin/simulation')}
                      title="Simulate Policy Impact"
                      className="h-8 w-8 p-0 text-indigo-600 hover:bg-indigo-50"
                    >
                      <Play className="w-3.5 h-3.5" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setHistoryPolicy(policy)}
                      title="View Version History & Diff"
                      className="h-8 w-8 p-0 text-slate-700 hover:bg-slate-100"
                    >
                      <History className="w-3.5 h-3.5" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setSelectedDetailPolicy(policy)}
                      title="View Policy Details"
                      className="h-8 w-8 p-0"
                    >
                      <Eye className="w-3.5 h-3.5" />
                    </Button>

                    {canWritePolicy && (
                      <>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleOpenEdit(policy)}
                          title="Edit Policy"
                          className="h-8 w-8 p-0"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setToggleStatusPolicy(policy)}
                          title={policy.enabled ? 'Disable Policy' : 'Enable Policy'}
                          className={`h-8 w-8 p-0 ${
                            policy.enabled
                              ? 'text-amber-600 hover:bg-amber-50'
                              : 'text-emerald-600 hover:bg-emerald-50'
                          }`}
                        >
                          <Power className="w-3.5 h-3.5" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setDeletingPolicy(policy)}
                          title="Delete Policy"
                          className="h-8 w-8 p-0 text-rose-600 hover:bg-rose-50"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </Button>
                      </>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-0 text-xs text-slate-600 space-y-2">
                <p>{policy.description}</p>
                <div className="flex flex-wrap gap-2 pt-1 font-mono text-[10px]">
                  {policy.target_roles && policy.target_roles.length > 0 && (
                    <span className="bg-slate-100 px-2 py-0.5 rounded text-slate-700">
                      Roles: {policy.target_roles.join(', ')}
                    </span>
                  )}
                  {policy.target_protocols && policy.target_protocols.length > 0 && (
                    <span className="bg-slate-100 px-2 py-0.5 rounded text-slate-700">
                      Protocols: {policy.target_protocols.join(', ')}
                    </span>
                  )}
                  {policy.target_risk_level && (
                    <span className="bg-amber-50 text-amber-800 border border-amber-200 px-2 py-0.5 rounded">
                      Target Risk: {policy.target_risk_level}
                    </span>
                  )}
                  {policy.exclusions && policy.exclusions.length > 0 && (
                    <span className="bg-rose-50 text-rose-800 border border-rose-200 px-2 py-0.5 rounded">
                      Exclusions: {policy.exclusions.join(', ')}
                    </span>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Modals */}
      <PolicyDetailModal
        isOpen={!!selectedDetailPolicy}
        onClose={() => setSelectedDetailPolicy(null)}
        policy={selectedDetailPolicy}
      />

      <PolicyFormModal
        isOpen={isFormOpen}
        onClose={() => setIsFormOpen(false)}
        onSubmit={handleFormSubmit}
        initialPolicy={editingPolicy}
        loading={formLoading}
      />

      <PolicyEnableModal
        isOpen={!!toggleStatusPolicy}
        onClose={() => setToggleStatusPolicy(null)}
        onConfirm={handleConfirmToggleEnable}
        policy={toggleStatusPolicy}
        loading={toggleLoading}
      />

      <PolicyDeleteModal
        isOpen={!!deletingPolicy}
        onClose={() => setDeletingPolicy(null)}
        onConfirm={handleDeleteConfirm}
        policy={deletingPolicy}
        loading={deleteLoading}
      />

      <PolicyHistoryModal
        isOpen={!!historyPolicy}
        onClose={() => setHistoryPolicy(null)}
        policy={historyPolicy}
        onOpenDiff={(fromVersion, toVersion) => {
          if (historyPolicy) {
            setDiffState({
              isOpen: true,
              policyId: historyPolicy.id,
              fromVersion,
              toVersion,
            });
          }
        }}
        onOpenRollback={(targetVersion, currentVersion) => {
          if (historyPolicy) {
            setRollbackState({
              isOpen: true,
              policy: historyPolicy,
              targetVersion,
              currentVersion,
            });
          }
        }}
      />

      <PolicyDiffModal
        isOpen={diffState.isOpen}
        onClose={() => setDiffState({ ...diffState, isOpen: false })}
        policyId={diffState.policyId}
        fromVersion={diffState.fromVersion}
        toVersion={diffState.toVersion}
      />

      <PolicyRollbackModal
        isOpen={rollbackState.isOpen}
        onClose={() => setRollbackState({ ...rollbackState, isOpen: false })}
        policy={rollbackState.policy}
        targetVersion={rollbackState.targetVersion}
        currentVersion={rollbackState.currentVersion}
        onSuccess={async () => {
          await fetchPolicies();
          setHistoryPolicy(null);
        }}
        onConflict={(expected, current) => {
          if (rollbackState.policy) {
            setConflictState({
              isOpen: true,
              policyId: rollbackState.policy.id,
              expectedVersion: expected,
              currentVersion: current,
            });
          }
        }}
      />

      <ConcurrencyConflictModal
        isOpen={conflictState.isOpen}
        onClose={() => setConflictState({ ...conflictState, isOpen: false })}
        policyId={conflictState.policyId}
        expectedVersion={conflictState.expectedVersion}
        currentVersion={conflictState.currentVersion}
        onReloadLatest={handleReloadLatestConflict}
      />
    </div>
  );
};
