import React, { useState } from 'react';
import { evaluationApi } from '@/services/api/evaluationApi';
import { AuthProtocol, PolicyDecision } from '@/types/policy';
import { UserRole } from '@/types/auth';
import { EvaluationResult, RequestContext } from '@/types/evaluation';
import { useAuth } from '@/hooks/useAuth';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorState } from '@/components/ui/ErrorState';

import { DecisionCard } from './components/DecisionCard';
import { RiskAssessmentCard } from './components/RiskAssessmentCard';
import { SecuritySignalsPanel } from './components/SecuritySignalsPanel';
import { PolicyTracePanel } from './components/PolicyTracePanel';
import { TechnicalDetails } from './components/TechnicalDetails';

import { AlertCircle, FileCheck, Play, ShieldAlert, UserCheck } from 'lucide-react';

export const EvaluationPage: React.FC = () => {
  const { user, roles } = useAuth();

  const [mode, setMode] = useState<'me' | 'test'>('me');
  const [result, setResult] = useState<EvaluationResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Test Context Form State
  const [userIdInput, setUserIdInput] = useState<string>('test-user-01');
  const [roleInput, setRoleInput] = useState<UserRole>(UserRole.STUDENT);
  const [protocolInput, setProtocolInput] = useState<AuthProtocol>(AuthProtocol.MODERN);
  const [mfaInput, setMfaInput] = useState<boolean>(false);
  const [deviceManaged, setDeviceManaged] = useState<boolean>(false);
  const [deviceCompliant, setDeviceCompliant] = useState<boolean>(false);
  const [locationInput, setLocationInput] = useState<string>('US');

  const handleEvaluateMe = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await evaluationApi.evaluateMe();
      setResult(data);
    } catch (err: any) {
      setError(err.message || 'Live evaluation request failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleEvaluateTestContext = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const context: RequestContext = {
      user_id: userIdInput.trim() || 'test-user',
      roles: [roleInput],
      role: roleInput,
      location: locationInput.trim() || 'UNKNOWN',
      authentication: {
        protocol: protocolInput,
        mfa_completed: mfaInput,
      },
      device: {
        managed: deviceManaged,
        compliant: deviceCompliant,
      },
    };

    try {
      const data = await evaluationApi.evaluate(context);
      setResult(data);
    } catch (err: any) {
      setError(err.message || 'Test context evaluation failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Policy Evaluation Engine</h2>
          <p className="text-xs text-slate-500 mt-1">
            Real-time zero-trust security decision visualization & explainability trace
          </p>
        </div>

        {/* Mode Switcher */}
        <div className="flex items-center p-1 bg-slate-200/80 rounded-xl self-start sm:self-auto">
          <button
            onClick={() => {
              setMode('me');
              setResult(null);
              setError(null);
            }}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
              mode === 'me' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Live User Evaluation
          </button>
          <button
            onClick={() => {
              setMode('test');
              setResult(null);
              setError(null);
            }}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
              mode === 'test' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Test Context Mode
          </button>
        </div>
      </div>

      {/* Mode Warning Banner */}
      {mode === 'me' ? (
        <div className="p-3 bg-indigo-50/70 border border-indigo-200 text-indigo-900 rounded-xl text-xs flex items-center gap-2.5">
          <UserCheck className="w-4 h-4 text-indigo-600 shrink-0" />
          <div>
            <span className="font-semibold">LIVE USER EVALUATION:</span> Evaluates real security signals derived from your authenticated Keycloak session (<strong className="font-mono">{user?.username}</strong>).
          </div>
        </div>
      ) : (
        <div className="p-3 bg-amber-50/70 border border-amber-200 text-amber-900 rounded-xl text-xs flex items-center gap-2.5">
          <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0" />
          <div>
            <span className="font-semibold">TEST CONTEXT EVALUATION:</span> Evaluates a custom simulated RequestContext payload. Does NOT alter backend identity or authentication.
          </div>
        </div>
      )}

      {/* Control Panel / Form */}
      {mode === 'me' ? (
        <Card>
          <CardContent className="p-6 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="space-y-1">
              <h3 className="text-sm font-bold text-slate-900">Evaluate Current Session Access</h3>
              <p className="text-xs text-slate-500">
                Triggers PolicyEvaluator against your active Keycloak session roles: ({roles.join(', ') || 'None'})
              </p>
            </div>
            <Button variant="primary" size="md" onClick={handleEvaluateMe} loading={loading} disabled={loading}>
              <Play className="w-4 h-4 mr-1.5" /> Evaluate My Access
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-semibold">Test Context Parameters</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleEvaluateTestContext} className="space-y-4 text-xs">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">User ID / Subject</label>
                  <input
                    type="text"
                    className="w-full p-2 border border-slate-300 rounded-md font-mono"
                    value={userIdInput}
                    onChange={(e) => setUserIdInput(e.target.value)}
                    required
                  />
                </div>

                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Target Role</label>
                  <select
                    className="w-full p-2 border border-slate-300 rounded-md bg-white font-medium"
                    value={roleInput}
                    onChange={(e) => setRoleInput(e.target.value as UserRole)}
                  >
                    {Object.values(UserRole).map((r: string) => (
                      <option key={r} value={r}>
                        {r}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Authentication Protocol</label>
                  <select
                    className="w-full p-2 border border-slate-300 rounded-md bg-white font-medium"
                    value={protocolInput}
                    onChange={(e) => setProtocolInput(e.target.value as AuthProtocol)}
                  >
                    <option value={AuthProtocol.MODERN}>MODERN</option>
                    <option value={AuthProtocol.LEGACY}>LEGACY</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
                <div className="flex items-center gap-2 pt-2">
                  <input
                    type="checkbox"
                    id="mfa-test-check"
                    className="rounded border-slate-300 text-indigo-600"
                    checked={mfaInput}
                    onChange={(e) => setMfaInput(e.target.checked)}
                  />
                  <label htmlFor="mfa-test-check" className="font-semibold text-slate-700 cursor-pointer">
                    MFA Completed
                  </label>
                </div>

                <div className="flex items-center gap-2 pt-2">
                  <input
                    type="checkbox"
                    id="dev-managed-check"
                    className="rounded border-slate-300 text-indigo-600"
                    checked={deviceManaged}
                    onChange={(e) => setDeviceManaged(e.target.checked)}
                  />
                  <label htmlFor="dev-managed-check" className="font-semibold text-slate-700 cursor-pointer">
                    Device Managed
                  </label>
                </div>

                <div className="flex items-center gap-2 pt-2">
                  <input
                    type="checkbox"
                    id="dev-compliant-check"
                    className="rounded border-slate-300 text-indigo-600"
                    checked={deviceCompliant}
                    onChange={(e) => setDeviceCompliant(e.target.checked)}
                  />
                  <label htmlFor="dev-compliant-check" className="font-semibold text-slate-700 cursor-pointer">
                    Device Compliant
                  </label>
                </div>
              </div>

              <div className="flex justify-end pt-2">
                <Button type="submit" variant="primary" size="md" loading={loading} disabled={loading}>
                  <Play className="w-4 h-4 mr-1.5" /> Evaluate Test Context
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Error Display */}
      {error && (
        <ErrorState
          title="Evaluation Request Failed"
          message={error}
          onRetry={mode === 'me' ? handleEvaluateMe : undefined}
        />
      )}

      {/* Loading Skeleton */}
      {loading && (
        <div className="p-8 bg-white border border-slate-200 rounded-xl text-center space-y-3">
          <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto" />
          <h3 className="text-sm font-semibold text-slate-900">Evaluating access against policy engine...</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            Aggregating security signals, computing risk factors, and evaluating conditional access policy hierarchy.
          </p>
        </div>
      )}

      {/* Results Section */}
      {!loading && result && (
        <div className="space-y-6 animate-in fade-in duration-200">
          {/* 1. Final Decision Card */}
          <DecisionCard decision={result.decision} reasons={result.reasons} />

          {/* 2. Risk Assessment Card */}
          <RiskAssessmentCard
            riskLevel={result.risk_level}
            riskFactors={result.risk_factors}
            riskTrace={result.risk_trace}
          />

          {/* 3. Security Signals Panel */}
          <SecuritySignalsPanel signals={result.evaluated_signals} />

          {/* 4. Policy Trace Panel */}
          <PolicyTracePanel policyTraces={result.policy_traces} />

          {/* 5. Technical Details & Correlation ID */}
          <TechnicalDetails
            correlationId={result.correlation_id}
            evaluatedAt={result.evaluated_at}
            matchedPolicies={result.matched_policies}
          />
        </div>
      )}

      {/* Empty State when no result exists */}
      {!loading && !result && !error && (
        <EmptyState
          title="No Evaluation Results"
          description="Run an evaluation to see how AegisOne would process the request and visualize the policy decision trace."
          icon={<FileCheck className="w-10 h-10 text-indigo-400" />}
        />
      )}
    </div>
  );
};
