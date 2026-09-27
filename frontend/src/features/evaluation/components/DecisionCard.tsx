import React from 'react';
import { PolicyDecision } from '@/types/policy';
import { Badge } from '@/components/ui/Badge';
import { Card, CardContent } from '@/components/ui/Card';
import { AlertCircle, CheckCircle2, ShieldX } from 'lucide-react';

interface DecisionCardProps {
  decision: PolicyDecision;
  reasons: string[];
}

export const DecisionCard: React.FC<DecisionCardProps> = ({ decision, reasons }) => {
  const configs = {
    [PolicyDecision.ALLOW]: {
      bg: 'bg-emerald-50/60 border-emerald-200',
      iconBg: 'bg-emerald-100 text-emerald-600',
      icon: <CheckCircle2 className="w-8 h-8" />,
      title: 'Access Decision: ALLOW',
      subtitle: 'The request satisfied applicable conditional access policies.',
      badgeVariant: 'success' as const,
    },
    [PolicyDecision.MFA_REQUIRED]: {
      bg: 'bg-amber-50/60 border-amber-200',
      iconBg: 'bg-amber-100 text-amber-600',
      icon: <AlertCircle className="w-8 h-8" />,
      title: 'Access Decision: MFA_REQUIRED',
      subtitle: 'Additional Multi-Factor Authentication is required to complete access.',
      badgeVariant: 'warning' as const,
    },
    [PolicyDecision.BLOCK]: {
      bg: 'bg-rose-50/60 border-rose-200',
      iconBg: 'bg-rose-100 text-rose-600',
      icon: <ShieldX className="w-8 h-8" />,
      title: 'Access Decision: BLOCK',
      subtitle: 'Access is blocked due to restrictive policy enforcement.',
      badgeVariant: 'danger' as const,
    },
  };

  const current = configs[decision] || configs[PolicyDecision.ALLOW];

  return (
    <Card className={`border-2 ${current.bg}`}>
      <CardContent className="p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className={`p-3 rounded-xl shrink-0 ${current.iconBg}`}>{current.icon}</div>
            <div>
              <div className="flex items-center gap-3">
                <h3 className="text-lg font-bold text-slate-900">{current.title}</h3>
                <Badge variant={current.badgeVariant} className="text-xs px-3 py-1 font-bold">
                  {decision}
                </Badge>
              </div>
              <p className="text-xs text-slate-600 mt-1">{current.subtitle}</p>
            </div>
          </div>
        </div>

        {reasons.length > 0 && (
          <div className="mt-4 pt-4 border-t border-slate-200/60 space-y-1.5">
            <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
              Evaluator Decision Reasons
            </h4>
            <ul className="space-y-1 pl-4 list-disc text-xs text-slate-700 font-mono">
              {reasons.map((reason, idx) => (
                <li key={idx}>{reason}</li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
