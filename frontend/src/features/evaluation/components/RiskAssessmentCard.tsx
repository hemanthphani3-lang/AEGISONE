import React from 'react';
import { Badge } from '@/components/ui/Badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { AlertTriangle, Activity } from 'lucide-react';

interface RiskAssessmentCardProps {
  riskLevel?: string | null;
  riskFactors?: string[];
  riskTrace?: string | null;
}

export const RiskAssessmentCard: React.FC<RiskAssessmentCardProps> = ({
  riskLevel = 'LOW',
  riskFactors = [],
  riskTrace,
}) => {
  const level = (riskLevel || 'LOW').toUpperCase();

  const variants = {
    HIGH: { badge: 'danger' as const, bg: 'bg-rose-50/40 border-rose-200', text: 'text-rose-700' },
    MEDIUM: { badge: 'warning' as const, bg: 'bg-amber-50/40 border-amber-200', text: 'text-amber-700' },
    UNKNOWN: { badge: 'default' as const, bg: 'bg-slate-50 border-slate-200', text: 'text-slate-600' },
    LOW: { badge: 'success' as const, bg: 'bg-emerald-50/40 border-emerald-200', text: 'text-emerald-700' },
  };

  const current = variants[level as keyof typeof variants] || variants.LOW;

  return (
    <Card className={current.bg}>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-indigo-600" />
          <CardTitle className="text-sm font-semibold">Risk Assessment Engine</CardTitle>
        </div>
        <Badge variant={current.badge} className="px-3 py-0.5 font-bold text-xs">
          {level} RISK
        </Badge>
      </CardHeader>
      <CardContent className="space-y-3 pt-2 text-xs">
        {riskTrace && (
          <p className="p-2.5 bg-white border border-slate-200/60 rounded-md text-slate-700 font-mono text-[11px] leading-relaxed">
            {riskTrace}
          </p>
        )}

        {riskFactors.length > 0 ? (
          <div>
            <h4 className="font-semibold text-slate-700 mb-1.5 flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-500" /> Active Risk Factors:
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {riskFactors.map((factor) => (
                <Badge key={factor} variant="danger" className="font-mono text-[10px]">
                  {factor}
                </Badge>
              ))}
            </div>
          </div>
        ) : (
          <p className="text-slate-500 italic text-[11px]">
            No elevated risk factors detected in trusted context.
          </p>
        )}
      </CardContent>
    </Card>
  );
};
