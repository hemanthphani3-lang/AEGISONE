import React, { useState } from 'react';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Check, ChevronDown, ChevronRight, Copy, Terminal } from 'lucide-react';

interface TechnicalDetailsProps {
  correlationId?: string | null;
  evaluatedAt?: string;
  matchedPolicies?: string[];
}

export const TechnicalDetails: React.FC<TechnicalDetailsProps> = ({
  correlationId,
  evaluatedAt,
  matchedPolicies = [],
}) => {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);

  const handleCopyCorrelationId = () => {
    if (correlationId) {
      navigator.clipboard.writeText(correlationId);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <Card className="border-slate-200">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-6 py-3 bg-slate-50 flex items-center justify-between text-xs font-semibold text-slate-700 hover:bg-slate-100 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-slate-500" />
          <span>Technical Evaluation Metadata</span>
        </div>
        {isOpen ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
      </button>

      {isOpen && (
        <CardContent className="p-4 bg-slate-900 text-slate-200 font-mono text-xs space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <span className="text-slate-400">Correlation ID:</span>
            <div className="flex items-center gap-2">
              <span className="text-indigo-300 font-bold">{correlationId || 'N/A'}</span>
              {correlationId && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleCopyCorrelationId}
                  className="h-6 text-[10px] text-slate-300 hover:bg-slate-800 hover:text-white"
                >
                  {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                  {copied ? 'Copied' : 'Copy'}
                </Button>
              )}
            </div>
          </div>

          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <span className="text-slate-400">Evaluated Timestamp:</span>
            <span className="text-slate-300">{evaluatedAt ? new Date(evaluatedAt).toISOString() : 'N/A'}</span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-slate-400">Matched Policy IDs:</span>
            <span className="text-slate-300">
              {matchedPolicies.length > 0 ? matchedPolicies.join(', ') : 'None'}
            </span>
          </div>
        </CardContent>
      )}
    </Card>
  );
};
