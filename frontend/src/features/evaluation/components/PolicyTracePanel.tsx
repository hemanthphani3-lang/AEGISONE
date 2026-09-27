import React from 'react';
import { PolicyTraceSummary } from '@/types/evaluation';
import { Badge } from '@/components/ui/Badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { CheckCircle2, FileCheck, XCircle } from 'lucide-react';

interface PolicyTracePanelProps {
  policyTraces?: PolicyTraceSummary[];
}

export const PolicyTracePanel: React.FC<PolicyTracePanelProps> = ({ policyTraces = [] }) => {
  if (policyTraces.length === 0) return null;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div className="flex items-center gap-2">
          <FileCheck className="w-4 h-4 text-indigo-600" />
          <CardTitle className="text-sm font-semibold">Policy Evaluation Trace</CardTitle>
        </div>
        <span className="text-xs text-slate-500 font-mono">
          {policyTraces.filter((p) => p.matched).length} / {policyTraces.length} Policies Matched
        </span>
      </CardHeader>
      <CardContent className="pt-2 space-y-3">
        {policyTraces.map((trace) => (
          <div
            key={trace.policy_id}
            className={`p-3.5 rounded-lg border text-xs transition-colors ${
              trace.matched
                ? 'bg-amber-50/40 border-amber-200'
                : 'bg-slate-50/50 border-slate-200 opacity-80'
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                {trace.matched ? (
                  <CheckCircle2 className="w-4 h-4 text-amber-600 shrink-0" />
                ) : (
                  <XCircle className="w-4 h-4 text-slate-400 shrink-0" />
                )}
                <div>
                  <h4 className="font-semibold text-slate-900">{trace.policy_name}</h4>
                  <p className="font-mono text-[10px] text-slate-500">{trace.policy_id}</p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <Badge variant={trace.matched ? 'warning' : 'outline'}>
                  {trace.matched ? 'MATCHED' : 'NOT MATCHED'}
                </Badge>
                <Badge
                  variant={
                    trace.action === 'BLOCK'
                      ? 'danger'
                      : trace.action === 'MFA_REQUIRED'
                      ? 'warning'
                      : 'success'
                  }
                >
                  Action: {trace.action}
                </Badge>
              </div>
            </div>

            <div className="mt-2 pt-2 border-t border-slate-200/60 flex flex-wrap gap-2 text-[10px] font-mono text-slate-600">
              {trace.target_roles.length > 0 && (
                <span>Roles: {trace.target_roles.join(', ')}</span>
              )}
              {trace.target_protocols.length > 0 && (
                <span>Protocols: {trace.target_protocols.join(', ')}</span>
              )}
              {trace.target_risk_level && <span>Target Risk: {trace.target_risk_level}</span>}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
};
