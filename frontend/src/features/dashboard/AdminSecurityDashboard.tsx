import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { useHealth } from '@/hooks/useHealth';
import { intelligenceApi, PolicyIntelligenceReport } from '@/services/api/intelligenceApi';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { ErrorState } from '@/components/ui/ErrorState';
import { Skeleton } from '@/components/ui/Skeleton';
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  FileCheck,
  FlaskConical,
  History,
  Lock,
  RefreshCw,
  Server,
  Shield,
  ShieldAlert,
  ShieldCheck,
  UserCheck,
} from 'lucide-react';

export const AdminSecurityDashboard: React.FC = () => {
  const { user, roles } = useAuth();
  const { health, loading: healthLoading, error: healthError, refetch: refetchHealth } = useHealth();
  const [intelReport, setIntelReport] = useState<PolicyIntelligenceReport | null>(null);
  const [intelLoading, setIntelLoading] = useState<boolean>(true);
  const navigate = useNavigate();

  const loadIntelligence = async () => {
    try {
      setIntelLoading(true);
      const data = await intelligenceApi.getReport();
      setIntelReport(data);
    } catch (err) {
      console.warn('[DASHBOARD] Failed to load intelligence report:', err);
    } finally {
      setIntelLoading(false);
    }
  };

  useEffect(() => {
    loadIntelligence();
  }, []);

  return (
    <div className="space-y-6">
      {/* Top Banner / Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white p-6 rounded-xl shadow-md border border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-indigo-400" />
            <h2 className="text-xl font-bold tracking-tight">Admin & Security Operations Dashboard</h2>
          </div>
          <p className="text-xs text-slate-300 mt-1">
            Zero-Trust policy engine control, real-time audit event telemetry, and what-if simulation lab
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="info" className="bg-indigo-500/20 text-indigo-200 border-indigo-500/30 px-3 py-1 font-mono text-xs">
            ADMINISTRATIVE CONSOLE
          </Badge>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Authenticated Principal Card */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-semibold">Security Administrator Principal</CardTitle>
            <UserCheck className="w-4 h-4 text-indigo-600" />
          </CardHeader>
          <CardContent className="space-y-3 pt-2">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <span className="text-xs text-slate-500">Username:</span>
              <span className="text-xs font-semibold text-slate-900 font-mono">
                {user?.username || 'anonymous'}
              </span>
            </div>
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <span className="text-xs text-slate-500">User ID (Subject):</span>
              <span className="text-[11px] font-mono text-slate-700 truncate max-w-[200px]" title={user?.user_id}>
                {user?.user_id || 'unauthenticated'}
              </span>
            </div>
            <div className="flex items-start justify-between">
              <span className="text-xs text-slate-500 pt-0.5">Authoritative Roles:</span>
              <div className="flex flex-wrap gap-1 justify-end max-w-[220px]">
                {roles.length > 0 ? (
                  roles.map((r) => (
                    <Badge key={r} variant="info" className="text-[10px]">
                      {r}
                    </Badge>
                  ))
                ) : (
                  <span className="text-xs text-slate-400">No roles assigned</span>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* System Health Card */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-semibold">Backend Infrastructure & Storage</CardTitle>
            <Server className="w-4 h-4 text-slate-600" />
          </CardHeader>
          <CardContent className="space-y-3 pt-2">
            {healthLoading ? (
              <div className="space-y-2">
                <Skeleton className="h-5 w-full" />
                <Skeleton className="h-5 w-full" />
              </div>
            ) : healthError ? (
              <ErrorState
                title="Backend API Service Unavailable"
                message={healthError}
                onRetry={refetchHealth}
              />
            ) : (
              <>
                <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                  <span className="text-xs text-slate-500">FastAPI Engine Gateway:</span>
                  <Badge variant="success" className="gap-1">
                    <CheckCircle2 className="w-3 h-3" /> Operational
                  </Badge>
                </div>
                <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                  <span className="text-xs text-slate-500">PostgreSQL Policy Store:</span>
                  <Badge
                    variant={health?.database === 'connected' ? 'success' : 'warning'}
                    className="gap-1 font-mono text-[10px]"
                  >
                    {health?.database || 'unknown'}
                  </Badge>
                </div>
                <div className="flex items-center justify-between pt-1">
                  <span className="text-[11px] text-slate-400 font-mono">
                    Updated: {health?.timestamp ? new Date(health.timestamp).toLocaleTimeString() : 'N/A'}
                  </span>
                  <Button variant="ghost" size="sm" onClick={() => refetchHealth()} className="h-7 text-xs">
                    <RefreshCw className="w-3 h-3 mr-1" /> Refresh
                  </Button>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Policy Intelligence & Health Overview */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-slate-900 text-white border-slate-800">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-slate-400 font-medium">Total Policy Store</p>
              <h4 className="text-2xl font-bold mt-1">
                {intelLoading ? '...' : intelReport?.total_policies || 0}
              </h4>
              <p className="text-[10px] text-slate-400 mt-1">
                {intelReport?.enabled_policies || 0} active / {intelReport?.disabled_policies || 0} disabled
              </p>
            </div>
            <div className="p-3 bg-indigo-500/20 text-indigo-400 rounded-lg">
              <Shield className="w-6 h-6" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-emerald-950/30 border-emerald-800/40 text-emerald-950 dark:text-emerald-100">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-emerald-700 dark:text-emerald-300 font-medium">Safe Health Score</p>
              <h4 className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">
                {intelLoading ? '...' : intelReport?.health_counts.SAFE || 0}
              </h4>
              <p className="text-[10px] text-emerald-600/80 dark:text-emerald-400/80 mt-1">Policies with 0 critical findings</p>
            </div>
            <div className="p-3 bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 rounded-lg">
              <ShieldCheck className="w-6 h-6" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-amber-950/20 border-amber-800/30 text-amber-950 dark:text-amber-100">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-amber-700 dark:text-amber-300 font-medium">Needs Review / Warnings</p>
              <h4 className="text-2xl font-bold text-amber-600 dark:text-amber-400 mt-1">
                {intelLoading ? '...' : (intelReport?.health_counts.REVIEW || 0) + (intelReport?.health_counts.WARNING || 0)}
              </h4>
              <p className="text-[10px] text-amber-600/80 dark:text-amber-400/80 mt-1">Broad scope or duplicate rules</p>
            </div>
            <div className="p-3 bg-amber-500/20 text-amber-600 dark:text-amber-400 rounded-lg">
              <AlertTriangle className="w-6 h-6" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-rose-950/20 border-rose-800/30 text-rose-950 dark:text-rose-100">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-rose-700 dark:text-rose-300 font-medium">Critical Findings</p>
              <h4 className="text-2xl font-bold text-rose-600 dark:text-rose-400 mt-1">
                {intelLoading ? '...' : intelReport?.health_counts.CRITICAL || 0}
              </h4>
              <p className="text-[10px] text-rose-600/80 dark:text-rose-400/80 mt-1">Conflict or lockout risk detected</p>
            </div>
            <div className="p-3 bg-rose-500/20 text-rose-600 dark:text-rose-400 rounded-lg">
              <ShieldAlert className="w-6 h-6" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Admin Operations Grid */}
      <div>
        <h3 className="text-sm font-semibold text-slate-900 mb-3">Administrative Control Modules</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card
            className="hover:border-indigo-400 transition-colors cursor-pointer group"
            onClick={() => navigate('/policies')}
          >
            <CardContent className="p-5 flex flex-col justify-between h-40">
              <div className="flex items-center justify-between">
                <div className="p-2.5 bg-indigo-50 text-indigo-600 rounded-lg group-hover:bg-indigo-100 transition-colors">
                  <Shield className="w-5 h-5" />
                </div>
                <Badge variant="success" className="text-[10px]">FULL WRITE ACCESS</Badge>
              </div>
              <div>
                <h4 className="text-sm font-semibold text-slate-900 group-hover:text-indigo-600 transition-colors">
                  Policy Management
                </h4>
                <p className="text-[11px] text-slate-500 mt-1">
                  Create, edit, toggle, and delete zero-trust access policies
                </p>
              </div>
            </CardContent>
          </Card>

          <Card
            className="hover:border-blue-400 transition-colors cursor-pointer group"
            onClick={() => navigate('/audit')}
          >
            <CardContent className="p-5 flex flex-col justify-between h-40">
              <div className="flex items-center justify-between">
                <div className="p-2.5 bg-blue-50 text-blue-600 rounded-lg group-hover:bg-blue-100 transition-colors">
                  <History className="w-5 h-5" />
                </div>
                <Badge variant="info" className="text-[10px]">SYSTEM TELEMETRY</Badge>
              </div>
              <div>
                <h4 className="text-sm font-semibold text-slate-900 group-hover:text-blue-600 transition-colors">
                  Audit Events
                </h4>
                <p className="text-[11px] text-slate-500 mt-1">
                  Query structured decision history and security audit records
                </p>
              </div>
            </CardContent>
          </Card>

          <Card
            className="hover:border-purple-400 transition-colors cursor-pointer group"
            onClick={() => navigate('/simulation')}
          >
            <CardContent className="p-5 flex flex-col justify-between h-40">
              <div className="flex items-center justify-between">
                <div className="p-2.5 bg-purple-50 text-purple-600 rounded-lg group-hover:bg-purple-100 transition-colors">
                  <FlaskConical className="w-5 h-5" />
                </div>
                <Badge variant="warning" className="text-[10px]">SIMULATION LAB</Badge>
              </div>
              <div>
                <h4 className="text-sm font-semibold text-slate-900 group-hover:text-purple-600 transition-colors">
                  What-If Simulation
                </h4>
                <p className="text-[11px] text-slate-500 mt-1">
                  Simulate hypothetical access scenarios without affecting live state
                </p>
              </div>
            </CardContent>
          </Card>

          <Card
            className="hover:border-amber-400 transition-colors cursor-pointer group"
            onClick={() => navigate('/risk')}
          >
            <CardContent className="p-5 flex flex-col justify-between h-40">
              <div className="flex items-center justify-between">
                <div className="p-2.5 bg-amber-50 text-amber-600 rounded-lg group-hover:bg-amber-100 transition-colors">
                  <Activity className="w-5 h-5" />
                </div>
                <Badge variant="outline" className="text-[10px]">RISK ANALYTICS</Badge>
              </div>
              <div>
                <h4 className="text-sm font-semibold text-slate-900 group-hover:text-amber-600 transition-colors">
                  Risk Assessment
                </h4>
                <p className="text-[11px] text-slate-500 mt-1">
                  Inspect environmental and protocol risk signal calculations
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};
