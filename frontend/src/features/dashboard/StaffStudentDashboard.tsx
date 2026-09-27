import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Activity, FileCheck, Lock, ShieldCheck, UserCheck } from 'lucide-react';

export const StaffStudentDashboard: React.FC = () => {
  const { user, roles } = useAuth();
  const navigate = useNavigate();

  const isBreakGlass = roles.includes('BREAK_GLASS' as any);

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-gradient-to-r from-slate-800 via-slate-900 to-indigo-950 text-white p-6 rounded-xl shadow-md border border-slate-700">
        <div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            <h2 className="text-xl font-bold tracking-tight">Staff & Student Access Portal</h2>
          </div>
          <p className="text-xs text-slate-300 mt-1">
            Evaluate your real-time access policies, inspect session context signals, and verify security compliance
          </p>
        </div>
        <div className="flex items-center gap-2">
          {isBreakGlass ? (
            <Badge variant="danger" className="bg-rose-500/20 text-rose-200 border-rose-500/30 px-3 py-1 font-mono text-xs">
              BREAK-GLASS EMERGENCY SESSION
            </Badge>
          ) : (
            <Badge variant="success" className="bg-emerald-500/20 text-emerald-200 border-emerald-500/30 px-3 py-1 font-mono text-xs">
              USER ACCESS PORTAL
            </Badge>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* User Identity Card */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-semibold">User Identity Profile</CardTitle>
            <UserCheck className="w-4 h-4 text-emerald-600" />
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
              <span className="text-xs text-slate-500 pt-0.5">Assigned User Roles:</span>
              <div className="flex flex-wrap gap-1 justify-end max-w-[220px]">
                {roles.length > 0 ? (
                  roles.map((r) => (
                    <Badge key={r} variant={r === 'BREAK_GLASS' ? 'danger' : 'info'} className="text-[10px]">
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

        {/* Portal Information Card */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-semibold">Self-Service Access Tools</CardTitle>
            <ShieldCheck className="w-4 h-4 text-slate-600" />
          </CardHeader>
          <CardContent className="space-y-3 pt-2">
            <p className="text-xs text-slate-600 leading-relaxed">
              As a staff member or student, you can evaluate how your current sign-in context (IP location, device compliance, authentication protocol) evaluates against active organizational policies.
            </p>
            <div className="pt-2 flex gap-2">
              <Button variant="primary" size="sm" onClick={() => navigate('/evaluation')} className="w-full text-xs">
                <FileCheck className="w-3.5 h-3.5 mr-1" /> Run Access Evaluation
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Access Portal Feature Cards */}
      <div>
        <h3 className="text-sm font-semibold text-slate-900 mb-3">Available User Services</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <Card
            className="hover:border-emerald-400 transition-colors cursor-pointer group"
            onClick={() => navigate('/evaluation')}
          >
            <CardContent className="p-5 flex flex-col justify-between h-40">
              <div className="flex items-center justify-between">
                <div className="p-2.5 bg-emerald-50 text-emerald-600 rounded-lg group-hover:bg-emerald-100 transition-colors">
                  <FileCheck className="w-5 h-5" />
                </div>
                <Badge variant="success" className="text-[10px]">AVAILABLE</Badge>
              </div>
              <div>
                <h4 className="text-sm font-semibold text-slate-900 group-hover:text-emerald-600 transition-colors">
                  Policy Evaluation
                </h4>
                <p className="text-[11px] text-slate-500 mt-1">
                  Test your real-time sign-in context against active zero-trust policy rules
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
                <Badge variant="outline" className="text-[10px]">AVAILABLE</Badge>
              </div>
              <div>
                <h4 className="text-sm font-semibold text-slate-900 group-hover:text-amber-600 transition-colors">
                  Risk Level Assessment
                </h4>
                <p className="text-[11px] text-slate-500 mt-1">
                  Inspect environmental and protocol risk signal calculations
                </p>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-50/70 border-dashed border-slate-300 opacity-80">
            <CardContent className="p-5 flex flex-col justify-between h-40">
              <div className="flex items-center justify-between">
                <div className="p-2.5 bg-slate-200/60 text-slate-500 rounded-lg">
                  <Lock className="w-5 h-5" />
                </div>
                <Badge variant="default" className="text-[10px]">ADMIN ONLY</Badge>
              </div>
              <div>
                <h4 className="text-sm font-semibold text-slate-700">
                  Administrative Suite
                </h4>
                <p className="text-[11px] text-slate-500 mt-1">
                  Policy editing, audit logs, and what-if simulation require ADMIN or SECURITY_ADMIN role
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};
