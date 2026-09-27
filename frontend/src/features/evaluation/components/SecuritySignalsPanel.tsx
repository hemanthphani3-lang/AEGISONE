import React from 'react';
import { SignalSummary } from '@/types/evaluation';
import { Badge } from '@/components/ui/Badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { AlertCircle, HelpCircle, Radio, ShieldCheck } from 'lucide-react';

interface SecuritySignalsPanelProps {
  signals?: SignalSummary[];
}

export const SecuritySignalsPanel: React.FC<SecuritySignalsPanelProps> = ({ signals = [] }) => {
  if (signals.length === 0) return null;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div className="flex items-center gap-2">
          <Radio className="w-4 h-4 text-indigo-600" />
          <CardTitle className="text-sm font-semibold">Evaluated Security Signals</CardTitle>
        </div>
        <span className="text-xs text-slate-500 font-mono">{signals.length} Signals Evaluated</span>
      </CardHeader>
      <CardContent className="pt-2">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider text-[10px] font-semibold border-b border-slate-200">
              <tr>
                <th className="px-3 py-2">Signal Name</th>
                <th className="px-3 py-2">Evaluated Value</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Source</th>
                <th className="px-3 py-2">Confidence</th>
                <th className="px-3 py-2">Signal Explanation</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {signals.map((sig) => {
                const isUnavailable = sig.status === 'UNAVAILABLE' || sig.status === 'UNKNOWN' || sig.status === 'ERROR';
                const formattedVal =
                  Array.isArray(sig.value) ? sig.value.join(', ') : sig.value !== null && sig.value !== undefined ? String(sig.value) : 'N/A';

                const explanation =
                  sig.metadata?.explanation ||
                  (isUnavailable ? 'No signal provider available for this signal' : 'Signal observed and verified');

                return (
                  <tr key={sig.name} className="hover:bg-slate-50/60 transition-colors">
                    <td className="px-3 py-2 font-mono text-[11px] font-semibold text-slate-800">
                      {sig.name}
                    </td>
                    <td className="px-3 py-2 font-mono text-[11px] text-slate-700">
                      {isUnavailable ? (
                        <span className="text-amber-600 font-medium italic">N/A (Unavailable)</span>
                      ) : (
                        <span className="font-semibold text-slate-900">{formattedVal}</span>
                      )}
                    </td>
                    <td className="px-3 py-2">
                      {isUnavailable ? (
                        <Badge variant="outline" className="gap-1 text-[10px] text-amber-700 bg-amber-50 border-amber-200">
                          <AlertCircle className="w-3 h-3 text-amber-500" /> {sig.status}
                        </Badge>
                      ) : (
                        <Badge variant="success" className="gap-1 text-[10px]">
                          <ShieldCheck className="w-3 h-3" /> {sig.status}
                        </Badge>
                      )}
                    </td>
                    <td className="px-3 py-2 font-mono text-[10px] text-slate-500">{sig.source}</td>
                    <td className="px-3 py-2 font-mono text-[10px] text-slate-500">{sig.confidence}</td>
                    <td className="px-3 py-2 text-[11px] text-slate-500 max-w-xs truncate">
                      {explanation}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
};

