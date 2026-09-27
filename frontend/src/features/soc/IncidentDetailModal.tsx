import React, { useState } from 'react';
import {
  Incident,
  IncidentEvent,
  IncidentStatus,
  incidentsApi,
} from '../../services/api/incidentsApi';
import { policyApi } from '../../services/api/policyApi';
import { Policy } from '../../types/policy';

interface IncidentDetailModalProps {
  incident: Incident | null;
  onClose: () => void;
  onIncidentUpdated: () => void;
  canManage: boolean;
  canRemediate: boolean;
}

export const IncidentDetailModal: React.FC<IncidentDetailModalProps> = ({
  incident,
  onClose,
  onIncidentUpdated,
  canManage,
  canRemediate,
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [commentText, setCommentText] = useState('');
  const [assigneeInput, setAssigneeInput] = useState('');
  const [resolutionSummary, setResolutionSummary] = useState('');
  const [dismissReason, setDismissReason] = useState('');
  const [remediationReason, setRemediationReason] = useState('Remediation executed via SOC Incident Console');
  const [expectedVersionInput, setExpectedVersionInput] = useState<string>('');
  const [targetVersionInput, setTargetVersionInput] = useState<string>('');
  const [showResolveInput, setShowResolveInput] = useState(false);
  const [showDismissInput, setShowDismissInput] = useState(false);
  const [policyDetail, setPolicyDetail] = useState<Policy | null>(null);
  const [loadingPolicy, setLoadingPolicy] = useState(false);

  if (!incident) return null;

  const fetchPolicy = async () => {
    if (!incident.policy_id) return;
    setLoadingPolicy(true);
    try {
      const pol = await policyApi.getPolicy(incident.policy_id);
      setPolicyDetail(pol);
      if (pol.version) {
        setExpectedVersionInput(pol.version.toString());
      }
    } catch (err: any) {
      console.warn('Failed to load associated policy detail:', err);
    } finally {
      setLoadingPolicy(false);
    }
  };

  React.useEffect(() => {
    if (incident?.policy_id) {
      fetchPolicy();
    }
  }, [incident?.id]);

  const handleAction = async (actionFn: () => Promise<any>, successText: string) => {
    setLoading(true);
    setError(null);
    setSuccessMsg(null);
    try {
      await actionFn();
      setSuccessMsg(successText);
      onIncidentUpdated();
      setShowResolveInput(false);
      setShowDismissInput(false);
    } catch (err: any) {
      const msg = err.response?.data?.detail?.message || err.response?.data?.detail || err.message || 'Operation failed';
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setLoading(false);
    }
  };

  const handleAcknowledge = () => handleAction(() => incidentsApi.acknowledge(incident.id), 'Incident acknowledged.');
  const handleAssign = () => handleAction(() => incidentsApi.assign(incident.id, assigneeInput.trim() || undefined), 'Assignee updated.');
  const handleResolve = () => {
    if (!resolutionSummary.trim()) {
      setError('Resolution summary is required.');
      return;
    }
    handleAction(() => incidentsApi.resolve(incident.id, resolutionSummary.trim()), 'Incident marked as RESOLVED.');
  };
  const handleDismiss = () => {
    if (!dismissReason.trim()) {
      setError('Dismissal reason is required.');
      return;
    }
    handleAction(() => incidentsApi.dismiss(incident.id, dismissReason.trim()), 'Incident DISMISSED.');
  };
  const handleReopen = () => handleAction(() => incidentsApi.reopen(incident.id), 'Incident REOPENED.');
  const handleAddComment = () => {
    if (!commentText.trim()) return;
    handleAction(async () => {
      await incidentsApi.comment(incident.id, commentText.trim());
      setCommentText('');
    }, 'Comment added to timeline.');
  };

  const handleRemediateDisable = () => {
    const expVer = expectedVersionInput ? parseInt(expectedVersionInput, 10) : undefined;
    handleAction(
      () =>
        incidentsApi.remediate(incident.id, {
          action: 'DISABLE_POLICY',
          expected_version: expVer,
          reason: remediationReason.trim() || 'Disabling policy due to critical security incident',
        }),
      `Policy ${incident.policy_id} disabled successfully.`
    );
  };

  const handleRemediateRollback = () => {
    const targetVer = parseInt(targetVersionInput, 10);
    if (isNaN(targetVer)) {
      setError('Target version is required for rollback remediation.');
      return;
    }
    const expVer = expectedVersionInput ? parseInt(expectedVersionInput, 10) : undefined;
    handleAction(
      () =>
        incidentsApi.remediate(incident.id, {
          action: 'ROLLBACK_POLICY',
          target_version: targetVer,
          expected_version: expVer,
          reason: remediationReason.trim() || `Rollback policy to v${targetVer} due to incident`,
        }),
      `Policy ${incident.policy_id} rolled back to v${targetVer}.`
    );
  };

  const getSeverityBadgeClass = (sev: string) => {
    switch (sev) {
      case 'CRITICAL':
        return 'bg-red-100 text-red-800 border border-red-300';
      case 'HIGH':
        return 'bg-orange-100 text-orange-800 border border-orange-300';
      case 'MEDIUM':
        return 'bg-amber-100 text-amber-800 border border-amber-300';
      default:
        return 'bg-blue-100 text-blue-800 border border-blue-300';
    }
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'OPEN':
        return 'bg-red-50 text-red-700 border border-red-200';
      case 'ACKNOWLEDGED':
        return 'bg-purple-50 text-purple-700 border border-purple-200';
      case 'INVESTIGATING':
        return 'bg-blue-50 text-blue-700 border border-blue-200';
      case 'RESOLVED':
        return 'bg-emerald-50 text-emerald-700 border border-emerald-200';
      case 'DISMISSED':
        return 'bg-slate-100 text-slate-700 border border-slate-300';
      case 'REOPENED':
        return 'bg-amber-50 text-amber-700 border border-amber-200';
      default:
        return 'bg-slate-100 text-slate-700';
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-white rounded-xl shadow-2xl border border-slate-200 max-w-4xl w-full max-h-[90vh] flex flex-col overflow-hidden">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <div className="flex items-center space-x-3">
            <span className="text-xs font-mono font-bold text-slate-500 bg-slate-200 px-2 py-1 rounded">
              {incident.id}
            </span>
            <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full ${getSeverityBadgeClass(incident.severity)}`}>
              {incident.severity}
            </span>
            <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full ${getStatusBadgeClass(incident.status)}`}>
              {incident.status}
            </span>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-200 transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg flex items-start justify-between">
              <div>⚠️ {error}</div>
              <button onClick={() => setError(null)} className="text-red-500 hover:text-red-800 ml-2">✕</button>
            </div>
          )}

          {successMsg && (
            <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm rounded-lg flex items-start justify-between">
              <div>✅ {successMsg}</div>
              <button onClick={() => setSuccessMsg(null)} className="text-emerald-500 hover:text-emerald-800 ml-2">✕</button>
            </div>
          )}

          {/* Incident Overview Card */}
          <div className="space-y-2">
            <h2 className="text-xl font-bold text-slate-900">{incident.title}</h2>
            <div className="p-4 bg-slate-50 rounded-lg border border-slate-200 text-sm text-slate-700 whitespace-pre-wrap font-sans">
              {incident.description}
            </div>
          </div>

          {/* Key Incident Attributes Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 bg-slate-50 p-4 rounded-lg border border-slate-200 text-xs">
            <div>
              <span className="text-slate-500 block font-medium">Target Policy ID</span>
              <span className="font-mono font-semibold text-slate-800">{incident.policy_id || 'Global'}</span>
            </div>
            <div>
              <span className="text-slate-500 block font-medium">Created Timestamp</span>
              <span className="text-slate-800 font-medium">{new Date(incident.created_at).toLocaleString()}</span>
            </div>
            <div>
              <span className="text-slate-500 block font-medium">Assigned Administrator</span>
              <span className="text-slate-800 font-medium">{incident.assigned_to || 'Unassigned'}</span>
            </div>
            <div>
              <span className="text-slate-500 block font-medium">Correlation ID</span>
              <span className="font-mono text-slate-600 truncate block">{incident.correlation_id}</span>
            </div>
          </div>

          {/* Policy Information & Version Context */}
          {incident.policy_id && (
            <div className="p-4 bg-blue-50/50 border border-blue-200 rounded-lg space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-blue-900 uppercase tracking-wider">Associated Policy Context</span>
                {policyDetail && (
                  <span className="text-xs font-semibold px-2 py-0.5 rounded bg-blue-100 text-blue-800">
                    Current v{policyDetail.version} ({policyDetail.enabled ? 'Enabled' : 'Disabled'})
                  </span>
                )}
              </div>
              {loadingPolicy ? (
                <div className="text-xs text-slate-500">Loading policy state...</div>
              ) : policyDetail ? (
                <div className="text-xs text-slate-700 space-y-1">
                  <div><strong className="font-semibold text-slate-900">Name:</strong> {policyDetail.name}</div>
                  <div><strong className="font-semibold text-slate-900">Action:</strong> <span className="font-bold text-blue-700">{policyDetail.action}</span></div>
                </div>
              ) : (
                <div className="text-xs text-slate-500">Policy details available on management dashboard.</div>
              )}
            </div>
          )}

          {/* Status Controls & Action Bar */}
          {canManage && (
            <div className="p-4 bg-slate-100 rounded-lg border border-slate-200 space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">Incident State Management</h3>
              <div className="flex flex-wrap gap-2">
                {incident.status === 'OPEN' && (
                  <button
                    disabled={loading}
                    onClick={handleAcknowledge}
                    className="px-3 py-1.5 text-xs font-semibold bg-purple-600 text-white rounded-lg hover:bg-purple-700 shadow-sm transition-colors"
                  >
                    Acknowledge Incident
                  </button>
                )}

                {(incident.status === 'OPEN' || incident.status === 'ACKNOWLEDGED' || incident.status === 'INVESTIGATING' || incident.status === 'REOPENED') && (
                  <>
                    <button
                      disabled={loading}
                      onClick={() => {
                        setShowResolveInput(!showResolveInput);
                        setShowDismissInput(false);
                      }}
                      className="px-3 py-1.5 text-xs font-semibold bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 shadow-sm transition-colors"
                    >
                      Resolve Incident...
                    </button>

                    <button
                      disabled={loading}
                      onClick={() => {
                        setShowDismissInput(!showDismissInput);
                        setShowResolveInput(false);
                      }}
                      className="px-3 py-1.5 text-xs font-semibold bg-slate-600 text-white rounded-lg hover:bg-slate-700 shadow-sm transition-colors"
                    >
                      Dismiss Incident...
                    </button>
                  </>
                )}

                {(incident.status === 'RESOLVED' || incident.status === 'DISMISSED') && (
                  <button
                    disabled={loading}
                    onClick={handleReopen}
                    className="px-3 py-1.5 text-xs font-semibold bg-amber-600 text-white rounded-lg hover:bg-amber-700 shadow-sm transition-colors"
                  >
                    Reopen Incident
                  </button>
                )}
              </div>

              {/* Resolve Form */}
              {showResolveInput && (
                <div className="p-3 bg-white border border-emerald-200 rounded-lg space-y-2">
                  <label className="text-xs font-medium text-slate-700 block">Resolution Summary (Required)</label>
                  <textarea
                    value={resolutionSummary}
                    onChange={(e) => setResolutionSummary(e.target.value)}
                    placeholder="Describe how the policy or incident was remediated..."
                    className="w-full text-xs p-2 border border-slate-300 rounded focus:ring-2 focus:ring-emerald-500"
                    rows={2}
                  />
                  <button
                    disabled={loading || !resolutionSummary.trim()}
                    onClick={handleResolve}
                    className="px-3 py-1 text-xs font-semibold bg-emerald-600 text-white rounded hover:bg-emerald-700"
                  >
                    Confirm Resolution
                  </button>
                </div>
              )}

              {/* Dismiss Form */}
              {showDismissInput && (
                <div className="p-3 bg-white border border-slate-300 rounded-lg space-y-2">
                  <label className="text-xs font-medium text-slate-700 block">Dismissal Reason (Required)</label>
                  <textarea
                    value={dismissReason}
                    onChange={(e) => setDismissReason(e.target.value)}
                    placeholder="State why this incident is being dismissed..."
                    className="w-full text-xs p-2 border border-slate-300 rounded focus:ring-2 focus:ring-slate-500"
                    rows={2}
                  />
                  <button
                    disabled={loading || !dismissReason.trim()}
                    onClick={handleDismiss}
                    className="px-3 py-1 text-xs font-semibold bg-slate-700 text-white rounded hover:bg-slate-800"
                  >
                    Confirm Dismissal
                  </button>
                </div>
              )}

              {/* Assignment Selector */}
              <div className="flex items-center space-x-2 text-xs pt-2 border-t border-slate-200">
                <label className="font-semibold text-slate-600">Assign To:</label>
                <input
                  type="text"
                  placeholder="Username / Administrator ID"
                  value={assigneeInput}
                  onChange={(e) => setAssigneeInput(e.target.value)}
                  className="p-1.5 border border-slate-300 rounded text-xs focus:ring-2 focus:ring-blue-500"
                />
                <button
                  disabled={loading}
                  onClick={handleAssign}
                  className="px-2.5 py-1.5 bg-blue-600 text-white font-semibold rounded hover:bg-blue-700"
                >
                  Save Assignee
                </button>
              </div>
            </div>
          )}

          {/* Incident Remediation Workspace */}
          {canRemediate && incident.policy_id && (
            <div className="p-4 bg-red-50/70 border border-red-200 rounded-lg space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-red-900">Policy Remediation Console</h3>
              <p className="text-xs text-red-700">
                Safely mutate or rollback policy <strong>{incident.policy_id}</strong> using authoritative server-side OCC concurrency checks.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Expected Current Version (OCC Check)</label>
                  <input
                    type="number"
                    value={expectedVersionInput}
                    onChange={(e) => setExpectedVersionInput(e.target.value)}
                    placeholder="e.g. 1"
                    className="w-full p-2 border border-slate-300 rounded text-xs bg-white"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Target Version (For Rollback)</label>
                  <input
                    type="number"
                    value={targetVersionInput}
                    onChange={(e) => setTargetVersionInput(e.target.value)}
                    placeholder="e.g. 1"
                    className="w-full p-2 border border-slate-300 rounded text-xs bg-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Remediation Rationale / Reason</label>
                <input
                  type="text"
                  value={remediationReason}
                  onChange={(e) => setRemediationReason(e.target.value)}
                  className="w-full p-2 border border-slate-300 rounded text-xs bg-white"
                />
              </div>

              <div className="flex flex-wrap gap-2 pt-2">
                <button
                  disabled={loading}
                  onClick={handleRemediateDisable}
                  className="px-3 py-1.5 bg-red-600 text-white text-xs font-bold rounded hover:bg-red-700 shadow-sm"
                >
                  🛑 Disable Policy {incident.policy_id}
                </button>
                <button
                  disabled={loading || !targetVersionInput}
                  onClick={handleRemediateRollback}
                  className="px-3 py-1.5 bg-amber-600 text-white text-xs font-bold rounded hover:bg-amber-700 shadow-sm"
                >
                  ↺ Rollback Policy to v{targetVersionInput || '?'}
                </button>
              </div>
            </div>
          )}

          {/* Activity & Investigation Timeline */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">Investigation Timeline</h3>
              <span className="text-xs text-slate-500 font-medium">{incident.events?.length || 0} events recorded</span>
            </div>

            {/* Comment Input Box */}
            {canManage && (
              <div className="flex gap-2">
                <input
                  type="text"
                  value={commentText}
                  onChange={(e) => setCommentText(e.target.value)}
                  placeholder="Add investigation note or observation..."
                  className="flex-1 text-xs p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
                <button
                  disabled={loading || !commentText.trim()}
                  onClick={handleAddComment}
                  className="px-3 py-2 bg-slate-800 text-white text-xs font-semibold rounded-lg hover:bg-slate-900"
                >
                  Post Note
                </button>
              </div>
            )}

            {/* Event Timeline List */}
            <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
              {incident.events && incident.events.length > 0 ? (
                incident.events.map((ev: IncidentEvent) => (
                  <div key={ev.id} className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-800">{ev.event_type}</span>
                      <span className="text-slate-400 font-mono">{new Date(ev.timestamp).toLocaleString()}</span>
                    </div>
                    <div className="text-slate-600">
                      By <strong className="text-slate-700">{ev.actor_username || ev.actor_user_id}</strong> (Correlation ID: <span className="font-mono text-slate-500">{ev.correlation_id}</span>)
                    </div>
                    {ev.metadata && Object.keys(ev.metadata).length > 0 && (
                      <div className="p-2 bg-white rounded border border-slate-200 text-slate-600 font-mono text-[11px] whitespace-pre-wrap">
                        {JSON.stringify(ev.metadata, null, 2)}
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <div className="text-xs text-slate-500 py-2">No activity events recorded yet.</div>
              )}
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-4 border-t border-slate-200 bg-slate-50 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-200 text-slate-700 font-semibold text-xs rounded-lg hover:bg-slate-300 transition-colors"
          >
            Close Workspace
          </button>
        </div>
      </div>
    </div>
  );
};
