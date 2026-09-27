import React, { useEffect, useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { Permission } from '@/types/auth';
import {
  Incident,
  IncidentSummaryStats,
  incidentsApi,
} from '../../services/api/incidentsApi';
import { IncidentDetailModal } from './IncidentDetailModal';

export const SOCPage: React.FC = () => {
  const { hasPermission } = useAuth();
  const canRead = hasPermission(Permission.READ_INCIDENTS);
  const canManage = hasPermission(Permission.MANAGE_INCIDENTS);
  const canRemediate = hasPermission(Permission.REMEDIATE_INCIDENTS);

  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [stats, setStats] = useState<IncidentSummaryStats | null>(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [severityFilter, setSeverityFilter] = useState<string>('');
  const [assignedFilter, setAssignedFilter] = useState<string>('');

  // Modals
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Create Manual Incident Form
  const [newTitle, setNewTitle] = useState('');
  const [newDescription, setNewDescription] = useState('');
  const [newSeverity, setNewSeverity] = useState<'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'>('HIGH');
  const [newPolicyId, setNewPolicyId] = useState('');

  const loadData = async () => {
    if (!canRead) return;
    setLoading(true);
    setError(null);
    try {
      const [listRes, statsRes] = await Promise.all([
        incidentsApi.list({
          search: search.trim() || undefined,
          status: statusFilter || undefined,
          severity: severityFilter || undefined,
          assigned_to: assignedFilter.trim() || undefined,
          page,
          page_size: 20,
        }),
        incidentsApi.getStats(),
      ]);
      setIncidents(listRes.incidents);
      setTotal(listRes.total);
      setStats(statsRes);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to load SOC incidents.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [page, statusFilter, severityFilter, search, assignedFilter]);

  const handleSyncIntelligence = async () => {
    setSyncing(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const res = await incidentsApi.syncIntelligence();
      setSuccessMsg(`Intelligence sync complete. ${res.created_count} new incidents generated.`);
      loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Sync failed');
    } finally {
      setSyncing(false);
    }
  };

  const handleCreateManualIncident = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !newDescription.trim()) return;
    setLoading(true);
    setError(null);
    try {
      await incidentsApi.create({
        title: newTitle.trim(),
        description: newDescription.trim(),
        severity: newSeverity,
        status: 'OPEN',
        source_type: 'MANUAL',
        policy_id: newPolicyId.trim() || undefined,
      });
      setSuccessMsg('Manual incident created successfully.');
      setShowCreateModal(false);
      setNewTitle('');
      setNewDescription('');
      setNewPolicyId('');
      loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to create incident');
    } finally {
      setLoading(false);
    }
  };

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case 'CRITICAL':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-red-100 text-red-800 border border-red-300">CRITICAL</span>;
      case 'HIGH':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-orange-100 text-orange-800 border border-orange-300">HIGH</span>;
      case 'MEDIUM':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-300">MEDIUM</span>;
      default:
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-100 text-blue-800 border border-blue-300">LOW</span>;
    }
  };

  const getStatusBadge = (st: string) => {
    switch (st) {
      case 'OPEN':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-red-50 text-red-700 border border-red-200">OPEN</span>;
      case 'ACKNOWLEDGED':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-purple-50 text-purple-700 border border-purple-200">ACKNOWLEDGED</span>;
      case 'INVESTIGATING':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-50 text-blue-700 border border-blue-200">INVESTIGATING</span>;
      case 'RESOLVED':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">RESOLVED</span>;
      case 'DISMISSED':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-slate-100 text-slate-700 border border-slate-300">DISMISSED</span>;
      case 'REOPENED':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-50 text-amber-700 border border-amber-200">REOPENED</span>;
      default:
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-slate-100 text-slate-700">{st}</span>;
    }
  };

  if (!canRead) {
    return (
      <div className="p-8 text-center bg-white rounded-xl border border-slate-200 shadow-sm max-w-md mx-auto my-12">
        <h2 className="text-xl font-bold text-slate-800 mb-2">Access Restricted</h2>
        <p className="text-sm text-slate-600">You do not possess the required <code>READ_INCIDENTS</code> permission to access the SOC Console.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header & Main Actions */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Security Operations Center (SOC)</h1>
          <p className="text-sm text-slate-600">
            Real-time security incident tracking, investigation timeline, and OCC policy remediation workspace.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          {canManage && (
            <>
              <button
                disabled={syncing}
                onClick={handleSyncIntelligence}
                className="px-4 py-2 bg-blue-600 text-white font-semibold text-xs rounded-lg hover:bg-blue-700 shadow-sm transition-colors flex items-center space-x-1.5"
              >
                <span>{syncing ? 'Syncing...' : '⚡ Sync Intelligence Findings'}</span>
              </button>

              <button
                onClick={() => setShowCreateModal(true)}
                className="px-4 py-2 bg-slate-800 text-white font-semibold text-xs rounded-lg hover:bg-slate-900 shadow-sm transition-colors"
              >
                + Report Incident
              </button>
            </>
          )}
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg flex items-center justify-between">
          <div>⚠️ {error}</div>
          <button onClick={() => setError(null)} className="text-red-500 hover:text-red-800">✕</button>
        </div>
      )}

      {successMsg && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm rounded-lg flex items-center justify-between">
          <div>✅ {successMsg}</div>
          <button onClick={() => setSuccessMsg(null)} className="text-emerald-500 hover:text-emerald-800">✕</button>
        </div>
      )}

      {/* Overview Statistics Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">Total Incidents</span>
            <span className="text-2xl font-bold text-slate-900">{stats.total_incidents}</span>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm border-l-4 border-l-red-500">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">Open Incidents</span>
            <span className="text-2xl font-bold text-red-600">{stats.open_incidents}</span>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm border-l-4 border-l-red-700">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">Critical Severity</span>
            <span className="text-2xl font-bold text-red-800">{stats.critical_incidents}</span>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm border-l-4 border-l-orange-500">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">High Severity</span>
            <span className="text-2xl font-bold text-orange-600">{stats.high_incidents}</span>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm border-l-4 border-l-amber-500">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">Unassigned</span>
            <span className="text-2xl font-bold text-amber-600">{stats.unassigned_incidents}</span>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm border-l-4 border-l-purple-500">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">Policies at Risk</span>
            <span className="text-2xl font-bold text-purple-700">{stats.policies_at_risk_count}</span>
          </div>
        </div>
      )}

      {/* Filters & Search Toolbar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-3">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <input
            type="text"
            placeholder="Search title, description, or policy ID..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="p-2 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-blue-500"
          />

          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="p-2 border border-slate-300 rounded-lg text-xs bg-white focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Statuses</option>
            <option value="OPEN">OPEN</option>
            <option value="ACKNOWLEDGED">ACKNOWLEDGED</option>
            <option value="INVESTIGATING">INVESTIGATING</option>
            <option value="RESOLVED">RESOLVED</option>
            <option value="DISMISSED">DISMISSED</option>
            <option value="REOPENED">REOPENED</option>
          </select>

          <select
            value={severityFilter}
            onChange={(e) => {
              setSeverityFilter(e.target.value);
              setPage(1);
            }}
            className="p-2 border border-slate-300 rounded-lg text-xs bg-white focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Severities</option>
            <option value="CRITICAL">CRITICAL</option>
            <option value="HIGH">HIGH</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="LOW">LOW</option>
          </select>

          <input
            type="text"
            placeholder="Filter by Assignee..."
            value={assignedFilter}
            onChange={(e) => {
              setAssignedFilter(e.target.value);
              setPage(1);
            }}
            className="p-2 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Incident List Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-600">
            <thead className="bg-slate-50 text-slate-700 uppercase tracking-wider font-semibold border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">Severity</th>
                <th className="py-3 px-4">Incident Title</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Target Policy</th>
                <th className="py-3 px-4">Assigned To</th>
                <th className="py-3 px-4">Created</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500">
                    Loading security incidents...
                  </td>
                </tr>
              ) : incidents.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500">
                    No incidents found matching criteria.
                  </td>
                </tr>
              ) : (
                incidents.map((inc) => (
                  <tr
                    key={inc.id}
                    className="hover:bg-slate-50/80 cursor-pointer transition-colors"
                    onClick={() => setSelectedIncident(inc)}
                  >
                    <td className="py-3 px-4">{getSeverityBadge(inc.severity)}</td>
                    <td className="py-3 px-4">
                      <div className="font-semibold text-slate-900">{inc.title}</div>
                      <div className="text-[11px] text-slate-400 font-mono">{inc.id}</div>
                    </td>
                    <td className="py-3 px-4">{getStatusBadge(inc.status)}</td>
                    <td className="py-3 px-4 font-mono font-medium text-slate-800">
                      {inc.policy_id || 'Global'}
                    </td>
                    <td className="py-3 px-4 font-medium text-slate-700">
                      {inc.assigned_to || <span className="text-slate-400 font-normal">Unassigned</span>}
                    </td>
                    <td className="py-3 px-4 text-slate-500">
                      {new Date(inc.created_at).toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedIncident(inc);
                        }}
                        className="px-3 py-1 bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold rounded text-xs transition-colors"
                      >
                        Investigate
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Footer */}
        <div className="px-4 py-3 border-t border-slate-200 bg-slate-50 flex items-center justify-between text-xs text-slate-600">
          <div>
            Showing <strong>{incidents.length}</strong> of <strong>{total}</strong> incidents
          </div>
          <div className="flex space-x-2">
            <button
              disabled={page <= 1 || loading}
              onClick={() => setPage(page - 1)}
              className="px-3 py-1 bg-white border border-slate-300 rounded disabled:opacity-50 hover:bg-slate-100"
            >
              Previous
            </button>
            <span className="py-1 px-2 font-semibold">Page {page}</span>
            <button
              disabled={page * 20 >= total || loading}
              onClick={() => setPage(page + 1)}
              className="px-3 py-1 bg-white border border-slate-300 rounded disabled:opacity-50 hover:bg-slate-100"
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {/* Incident Detail Modal */}
      {selectedIncident && (
        <IncidentDetailModal
          incident={selectedIncident}
          onClose={() => setSelectedIncident(null)}
          onIncidentUpdated={loadData}
          canManage={canManage}
          canRemediate={canRemediate}
        />
      )}

      {/* Create Manual Incident Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl shadow-2xl border border-slate-200 max-w-lg w-full p-6 space-y-4">
            <div className="flex justify-between items-center border-b pb-3">
              <h3 className="text-lg font-bold text-slate-900">Report Manual Security Incident</h3>
              <button onClick={() => setShowCreateModal(false)} className="text-slate-400 hover:text-slate-600">✕</button>
            </div>

            <form onSubmit={handleCreateManualIncident} className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Incident Title *</label>
                <input
                  type="text"
                  required
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="e.g. Unrestricted Admin Target Role"
                  className="w-full p-2 border border-slate-300 rounded text-xs focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Severity *</label>
                <select
                  value={newSeverity}
                  onChange={(e: any) => setNewSeverity(e.target.value)}
                  className="w-full p-2 border border-slate-300 rounded text-xs bg-white"
                >
                  <option value="CRITICAL">CRITICAL</option>
                  <option value="HIGH">HIGH</option>
                  <option value="MEDIUM">MEDIUM</option>
                  <option value="LOW">LOW</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Associated Policy ID (Optional)</label>
                <input
                  type="text"
                  value={newPolicyId}
                  onChange={(e) => setNewPolicyId(e.target.value)}
                  placeholder="e.g. admin-mfa"
                  className="w-full p-2 border border-slate-300 rounded text-xs focus:ring-2 focus:ring-blue-500 font-mono"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Detailed Description *</label>
                <textarea
                  required
                  rows={4}
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  placeholder="Describe the security event, impact, and observations..."
                  className="w-full p-2 border border-slate-300 rounded text-xs focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-3 border-t">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 bg-slate-100 text-slate-700 rounded font-semibold hover:bg-slate-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 bg-slate-800 text-white rounded font-semibold hover:bg-slate-900"
                >
                  Create Incident
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
