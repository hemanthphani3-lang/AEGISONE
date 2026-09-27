import React, { useState } from 'react';
import { simulationApi } from '@/services/api/simulationApi';
import { SimulationResult } from '@/types/simulation';
import { AuthProtocol, PolicyDecision, RiskLevel } from '@/types/policy';
import { UserRole } from '@/types/auth';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { ErrorState } from '@/components/ui/ErrorState';
import {
  ArrowRight,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Copy,
  FileSearch,
  FlaskConical,
  HelpCircle,
  Info,
  Layers,
  Play,
  RefreshCw,
  ShieldAlert,
  ShieldCheck,
  ShieldX,
  Zap,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const SimulationPage: React.FC = () => {
  const navigate = useNavigate();

  // Context Overrides State
  const [userIdInput, setUserIdInput] = useState<string>('simulated-user-01');
  const [roleOverride, setRoleOverride] = useState<string>('STAFF');
  const [protocolOverride, setProtocolOverride] = useState<string>('MODERN');
  const [mfaOverride, setMfaOverride] = useState<string>('false');
  const [locationOverride, setLocationOverride] = useState<string>('UNKNOWN');
  const [deviceCompliantOverride, setDeviceCompliantOverride] = useState<string>('');
  const [deviceManagedOverride, setDeviceManagedOverride] = useState<string>('');
  const [riskLevelOverride, setRiskLevelOverride] = useState<string>('');

  // Results & UI State
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedPolicies, setExpandedPolicies] = useState<Record<string, boolean>>({});
  const [copiedCid, setCopiedCid] = useState<boolean>(false);

  const handleRunSimulation = async () => {
    setLoading(true);
    setError(null);
    try {
      const overridesPayload: any = {};
      if (mfaOverride !== '') overridesPayload.mfa_completed = mfaOverride === 'true';
      if (protocolOverride !== '') overridesPayload.auth_protocol = protocolOverride as AuthProtocol;
      if (roleOverride !== '') overridesPayload.roles = [roleOverride as UserRole];
      if (locationOverride.trim()) overridesPayload.location = locationOverride.trim();
      if (deviceCompliantOverride !== '') overridesPayload.device_compliant = deviceCompliantOverride === 'true';
      if (deviceManagedOverride !== '') overridesPayload.device_managed = deviceManagedOverride === 'true';
      if (riskLevelOverride !== '') overridesPayload.risk_level = riskLevelOverride as RiskLevel;

      const data = await simulationApi.simulatePolicies({
        base_context: {
          user_id: userIdInput || 'simulated-user-01',
          role: (roleOverride || 'STAFF') as UserRole,
          roles: [(roleOverride || 'STAFF') as UserRole],
          location: locationOverride || 'UNKNOWN',
          authentication: {
            protocol: (protocolOverride || 'MODERN') as AuthProtocol,
            mfa_completed: mfaOverride === 'true',
          },
        },
        overrides: overridesPayload,
      });
      setResult(data);
    } catch (err: any) {
      setError(err.message || 'Policy simulation execution failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleResetOverrides = () => {
    setUserIdInput('simulated-user-01');
    setRoleOverride('STAFF');
    setProtocolOverride('MODERN');
    setMfaOverride('false');
    setLocationOverride('UNKNOWN');
    setDeviceCompliantOverride('');
    setDeviceManagedOverride('');
    setRiskLevelOverride('');
    setResult(null);
    setError(null);
  };

  const togglePolicyExpand = (policyId: string) => {
    setExpandedPolicies((prev) => ({
      ...prev,
      [policyId]: !prev[policyId],
    }));
  };

  const copyCorrelationId = (cid: string) => {
    navigator.clipboard.writeText(cid);
    setCopiedCid(true);
    setTimeout(() => setCopiedCid(false), 2000);
  };

  const getDecisionBadge = (decision: PolicyDecision) => {
    switch (decision) {
      case PolicyDecision.ALLOW:
        return (
          <Badge variant="success" className="px-3 py-1 text-xs font-bold gap-1 bg-emerald-100 text-emerald-800 border-emerald-300">
            <ShieldCheck className="w-3.5 h-3.5" /> ALLOW
          </Badge>
        );
      case PolicyDecision.MFA_REQUIRED:
        return (
          <Badge variant="warning" className="px-3 py-1 text-xs font-bold gap-1 bg-amber-100 text-amber-800 border-amber-300">
            <Zap className="w-3.5 h-3.5" /> MFA REQUIRED
          </Badge>
        );
      case PolicyDecision.BLOCK:
        return (
          <Badge variant="danger" className="px-3 py-1 text-xs font-bold gap-1 bg-rose-100 text-rose-800 border-rose-300">
            <ShieldX className="w-3.5 h-3.5" /> BLOCK
          </Badge>
        );
      default:
        return <Badge variant="outline">{decision}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white p-6 rounded-xl shadow-md border border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <FlaskConical className="w-5 h-5 text-indigo-400" />
            <h2 className="text-xl font-bold tracking-tight">Policy Decision Workspace & Simulator</h2>
          </div>
          <p className="text-xs text-slate-300 mt-1">
            Construct hypothetical access requests and evaluate them against the authoritative policy engine with full condition explainability
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={handleResetOverrides} disabled={loading} className="border-slate-700 text-slate-200 hover:bg-slate-800">
            <RefreshCw className="w-3.5 h-3.5 mr-1" /> Reset Scenario
          </Button>
        </div>
      </div>

      {/* Hypothetical Context Configuration */}
      <Card className="border-slate-200 shadow-sm">
        <CardHeader className="pb-3 border-b border-slate-100 bg-slate-50/50">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Layers className="w-4 h-4 text-indigo-600" /> Hypothetical Request Context Configuration
              </CardTitle>
              <CardDescription className="text-xs mt-0.5">
                Define the user identity, roles, environmental factors, and authentication attributes for the evaluation request
              </CardDescription>
            </div>
            <Badge variant="outline" className="text-[10px] font-mono">
              REAL ENGINE BACKED
            </Badge>
          </div>
        </CardHeader>

        <CardContent className="p-6 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* User ID Input */}
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-700">User Subject ID</label>
              <input
                type="text"
                placeholder="e.g. user-12345"
                className="w-full text-xs p-2 border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-indigo-500 font-mono"
                value={userIdInput}
                onChange={(e) => setUserIdInput(e.target.value)}
              />
            </div>

            {/* Role Override */}
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-700">Primary Assigned Role</label>
              <select
                className="w-full text-xs p-2 border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-indigo-500 font-semibold"
                value={roleOverride}
                onChange={(e) => setRoleOverride(e.target.value)}
              >
                <option value="STAFF">STAFF</option>
                <option value="STUDENT">STUDENT</option>
                <option value="ADMIN">ADMIN</option>
                <option value="SECURITY_ADMIN">SECURITY_ADMIN</option>
                <option value="BREAK_GLASS">BREAK_GLASS</option>
              </select>
            </div>

            {/* Auth Protocol */}
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-700">Authentication Protocol</label>
              <select
                className="w-full text-xs p-2 border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-indigo-500 font-semibold"
                value={protocolOverride}
                onChange={(e) => setProtocolOverride(e.target.value)}
              >
                <option value="MODERN">MODERN (OIDC / OAuth2 / PKCE)</option>
                <option value="LEGACY">LEGACY (Basic / NTLM / Legacy Auth)</option>
              </select>
            </div>

            {/* MFA Completed Status */}
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-700">MFA Completed Status</label>
              <select
                className="w-full text-xs p-2 border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-indigo-500 font-semibold"
                value={mfaOverride}
                onChange={(e) => setMfaOverride(e.target.value)}
              >
                <option value="false">MFA Incomplete (false)</option>
                <option value="true">MFA Completed (true)</option>
              </select>
            </div>

            {/* Location */}
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-700">Location / Network Context</label>
              <input
                type="text"
                placeholder="e.g. UNKNOWN, UNTRUSTED_LOCATION, INTERNAL_NETWORK"
                className="w-full text-xs p-2 border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-indigo-500 font-mono"
                value={locationOverride}
                onChange={(e) => setLocationOverride(e.target.value)}
              />
            </div>

            {/* Device Compliance */}
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-700">Device Compliance Status</label>
              <select
                className="w-full text-xs p-2 border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-indigo-500 font-semibold"
                value={deviceCompliantOverride}
                onChange={(e) => setDeviceCompliantOverride(e.target.value)}
              >
                <option value="">Default (Not Specified)</option>
                <option value="true">Device Compliant (true)</option>
                <option value="false">Non-Compliant Device (false)</option>
              </select>
            </div>

            {/* Device Management */}
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-700">Device Management Status</label>
              <select
                className="w-full text-xs p-2 border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-indigo-500 font-semibold"
                value={deviceManagedOverride}
                onChange={(e) => setDeviceManagedOverride(e.target.value)}
              >
                <option value="">Default (Not Specified)</option>
                <option value="true">Corporate Managed (true)</option>
                <option value="false">Unmanaged Device (false)</option>
              </select>
            </div>

            {/* Risk Level Override */}
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-700">Explicit Risk Level Override</label>
              <select
                className="w-full text-xs p-2 border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-indigo-500 font-semibold"
                value={riskLevelOverride}
                onChange={(e) => setRiskLevelOverride(e.target.value)}
              >
                <option value="">Auto-Calculate Risk</option>
                <option value="LOW">LOW Risk</option>
                <option value="MEDIUM">MEDIUM Risk</option>
                <option value="HIGH">HIGH Risk</option>
                <option value="CRITICAL">CRITICAL Risk</option>
              </select>
            </div>
          </div>

          <div className="pt-3 flex items-center justify-between border-t border-slate-100">
            <div className="text-[11px] text-slate-500 flex items-center gap-1.5">
              <Info className="w-3.5 h-3.5 text-indigo-600" />
              Executes through <span className="font-semibold text-slate-700">PolicyEvaluator.evaluate()</span> without modifying live production state.
            </div>
            <Button
              variant="primary"
              size="md"
              onClick={handleRunSimulation}
              loading={loading}
              className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold shadow-sm px-5"
            >
              <Play className="w-4 h-4 mr-2 fill-current" /> Evaluate Request
            </Button>
          </div>
        </CardContent>
      </Card>

      {error && <ErrorState title="Policy Simulation Failed" message={error} onRetry={handleRunSimulation} />}

      {/* Decision Results Workspace */}
      {result && (
        <div className="space-y-6">
          {/* Main Decision Banner */}
          <Card className="border-indigo-200 bg-white shadow-md overflow-hidden">
            <CardHeader className="bg-slate-900 text-white p-6 border-b border-slate-800">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono uppercase tracking-wider text-slate-400">EVALUATION RESULT</span>
                    {result.correlation_id && (
                      <Badge variant="outline" className="text-[10px] border-slate-700 text-slate-300 font-mono">
                        CID: {result.correlation_id}
                      </Badge>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-2xl font-black tracking-tight text-white">ACCESS DECISION:</span>
                    {getDecisionBadge(result.simulated_decision)}
                  </div>
                </div>

                <div className="flex items-center gap-3 bg-slate-800/80 p-3 rounded-xl border border-slate-700/60">
                  <div className="text-right">
                    <span className="text-[10px] text-slate-400 block font-mono">CALCULATED RISK LEVEL</span>
                    <span className="text-xs font-bold text-indigo-300 font-mono">{result.simulated_risk}</span>
                  </div>
                  {result.correlation_id && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyCorrelationId(result.correlation_id!)}
                      className="text-slate-300 hover:text-white h-8 text-xs"
                    >
                      <Copy className="w-3.5 h-3.5 mr-1" />
                      {copiedCid ? 'Copied!' : 'Copy CID'}
                    </Button>
                  )}
                </div>
              </div>
            </CardHeader>

            <CardContent className="p-6 space-y-6">
              {/* "Why?" Decision Explanation & Resolution Precedence */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Decision Reason */}
                <div className="lg:col-span-2 space-y-3 p-4 bg-slate-50 border border-slate-200 rounded-xl">
                  <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                    <HelpCircle className="w-4 h-4 text-indigo-600" /> Why Was This Decision Produced?
                  </h3>
                  <div className="text-xs text-slate-800 leading-relaxed font-mono bg-white p-3 border border-slate-200 rounded-lg">
                    {result.evaluation_result?.decision_precedence_trace ||
                      result.trace?.explanation ||
                      'Evaluated through authoritative policy engine.'}
                  </div>
                  {result.evaluation_result?.reasons && result.evaluation_result.reasons.length > 0 && (
                    <ul className="space-y-1 pl-4 list-disc text-xs text-slate-600">
                      {result.evaluation_result.reasons.map((r, idx) => (
                        <li key={idx}>{r}</li>
                      ))}
                    </ul>
                  )}
                </div>

                {/* Precedence Hierarchy Resolution */}
                <div className="p-4 bg-indigo-50/50 border border-indigo-100 rounded-xl space-y-3">
                  <h3 className="text-xs font-bold text-indigo-900 uppercase tracking-wider flex items-center gap-1.5">
                    <ShieldAlert className="w-4 h-4 text-indigo-600" /> Decision Resolution Hierarchy
                  </h3>
                  <div className="space-y-2 text-xs font-mono">
                    <div
                      className={`p-2.5 rounded-lg border flex items-center justify-between ${
                        result.simulated_decision === PolicyDecision.BLOCK
                          ? 'bg-rose-100 border-rose-300 font-bold text-rose-900 shadow-sm'
                          : 'bg-white border-slate-200 text-slate-400'
                      }`}
                    >
                      <span>1. BLOCK</span>
                      <span className="text-[10px]">HIGHEST PRECEDENCE</span>
                    </div>

                    <div className="flex justify-center text-slate-300">↓</div>

                    <div
                      className={`p-2.5 rounded-lg border flex items-center justify-between ${
                        result.simulated_decision === PolicyDecision.MFA_REQUIRED
                          ? 'bg-amber-100 border-amber-300 font-bold text-amber-900 shadow-sm'
                          : 'bg-white border-slate-200 text-slate-400'
                      }`}
                    >
                      <span>2. MFA_REQUIRED</span>
                      <span className="text-[10px]">INTERMEDIATE</span>
                    </div>

                    <div className="flex justify-center text-slate-300">↓</div>

                    <div
                      className={`p-2.5 rounded-lg border flex items-center justify-between ${
                        result.simulated_decision === PolicyDecision.ALLOW
                          ? 'bg-emerald-100 border-emerald-300 font-bold text-emerald-900 shadow-sm'
                          : 'bg-white border-slate-200 text-slate-400'
                      }`}
                    >
                      <span>3. ALLOW</span>
                      <span className="text-[10px]">DEFAULT FALLBACK</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Evaluated Policies Table */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                    <FileSearch className="w-4 h-4 text-indigo-600" /> Evaluated Policies Breakdown
                  </h3>
                  <span className="text-[11px] text-slate-500 font-mono">
                    Total Evaluated: {result.evaluation_result?.policy_traces?.length || 0}
                  </span>
                </div>

                <div className="border border-slate-200 rounded-xl overflow-hidden shadow-sm">
                  <div className="bg-slate-100 px-4 py-2.5 border-b border-slate-200 grid grid-cols-12 text-[11px] font-bold text-slate-700 uppercase tracking-wider">
                    <div className="col-span-4">Policy</div>
                    <div className="col-span-2">Action</div>
                    <div className="col-span-3">Evaluation Status</div>
                    <div className="col-span-3 text-right">Conditions Detail</div>
                  </div>

                  <div className="divide-y divide-slate-100 bg-white">
                    {result.evaluation_result?.policy_traces?.map((pt) => {
                      const isExpanded = !!expandedPolicies[pt.policy_id];

                      return (
                        <div key={pt.policy_id} className="text-xs">
                          <div
                            className="px-4 py-3 grid grid-cols-12 items-center hover:bg-slate-50/80 cursor-pointer transition-colors"
                            onClick={() => togglePolicyExpand(pt.policy_id)}
                          >
                            <div className="col-span-4 font-semibold text-slate-900">
                              <div>{pt.policy_name}</div>
                              <div className="text-[10px] font-mono text-slate-400">ID: {pt.policy_id}</div>
                            </div>
                            <div className="col-span-2">{getDecisionBadge(pt.action)}</div>
                            <div className="col-span-3">
                              {pt.matched ? (
                                <Badge variant="warning" className="bg-amber-50 text-amber-800 border-amber-200 text-[10px]">
                                  MATCHED
                                </Badge>
                              ) : pt.excluded ? (
                                <Badge variant="danger" className="bg-rose-50 text-rose-800 border-rose-200 text-[10px]">
                                  EXCLUDED ({pt.exclusion_reason})
                                </Badge>
                              ) : (
                                <Badge variant="outline" className="text-slate-500 text-[10px]">
                                  NO MATCH
                                </Badge>
                              )}
                            </div>
                            <div className="col-span-3 flex items-center justify-end text-slate-400 font-mono text-[11px]">
                              {isExpanded ? (
                                <span className="text-indigo-600 font-semibold flex items-center">
                                  Hide Details <ChevronDown className="w-3.5 h-3.5 ml-1" />
                                </span>
                              ) : (
                                <span className="hover:text-slate-600 flex items-center">
                                  Inspect Conditions ({pt.condition_details?.length || 0}) <ChevronRight className="w-3.5 h-3.5 ml-1" />
                                </span>
                              )}
                            </div>
                          </div>

                          {/* Expanded Conditions Breakdown Drawer */}
                          {isExpanded && (
                            <div className="bg-slate-50 p-4 border-t border-slate-100 space-y-2">
                              <h4 className="text-[11px] font-bold text-slate-700 uppercase tracking-wider">
                                Condition Evaluator Results ({pt.policy_name})
                              </h4>
                              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                                {pt.condition_details?.map((cd, idx) => (
                                  <div
                                    key={idx}
                                    className="p-2.5 bg-white border border-slate-200 rounded-lg flex items-start justify-between gap-3 text-[11px]"
                                  >
                                    <div className="space-y-0.5">
                                      <span className="font-bold text-slate-900 block font-mono">{cd.condition_type}</span>
                                      <span className="text-slate-600 block">{cd.reason}</span>
                                    </div>
                                    <Badge
                                      variant={cd.result === 'MATCH' ? 'success' : 'outline'}
                                      className="text-[9px] px-2 py-0.5"
                                    >
                                      {cd.result}
                                    </Badge>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>

              {/* Navigation Footer */}
              <div className="pt-4 flex items-center justify-between border-t border-slate-100">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate('/audit')}
                  className="text-xs text-slate-700"
                >
                  <FileSearch className="w-3.5 h-3.5 mr-1.5 text-indigo-600" /> View Security Audit Center Logs
                </Button>
                <span className="text-[11px] font-mono text-slate-400">
                  Simulation ID: {result.simulation_id}
                </span>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};
