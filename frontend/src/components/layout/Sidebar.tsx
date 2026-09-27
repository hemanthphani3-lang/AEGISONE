import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { UserRole } from '@/types/auth';
import {
  Activity,
  FileCheck,
  FlaskConical,
  History,
  LayoutDashboard,
  Lock,
  Shield,
  ShieldAlert,
} from 'lucide-react';

interface NavItem {
  name: string;
  path: string;
  icon: React.ReactNode;
  allowedRoles?: UserRole[];
}

export const Sidebar: React.FC = () => {
  const { hasAnyRole } = useAuth();

  const navItems: NavItem[] = [
    {
      name: 'Dashboard',
      path: '/dashboard',
      icon: <LayoutDashboard className="w-4 h-4" />,
    },
    {
      name: 'Security Ops (SOC)',
      path: '/incidents',
      icon: <ShieldAlert className="w-4 h-4" />,
      allowedRoles: [UserRole.ADMIN, UserRole.SECURITY_ADMIN, UserRole.STAFF, UserRole.BREAK_GLASS],
    },
    {
      name: 'Policy Engine',
      path: '/policies',
      icon: <Shield className="w-4 h-4" />,
      allowedRoles: [UserRole.ADMIN, UserRole.SECURITY_ADMIN],
    },
    {
      name: 'Evaluation',
      path: '/evaluation',
      icon: <FileCheck className="w-4 h-4" />,
    },
    {
      name: 'Risk & Signals',
      path: '/risk',
      icon: <Activity className="w-4 h-4" />,
    },
    {
      name: 'Audit Trace',
      path: '/audit',
      icon: <History className="w-4 h-4" />,
      allowedRoles: [UserRole.ADMIN, UserRole.SECURITY_ADMIN],
    },
    {
      name: 'What-If Simulation',
      path: '/simulation',
      icon: <FlaskConical className="w-4 h-4" />,
      allowedRoles: [UserRole.ADMIN, UserRole.SECURITY_ADMIN],
    },
    {
      name: 'User Directory',
      path: '/users',
      icon: <Lock className="w-4 h-4" />,
      allowedRoles: [UserRole.ADMIN, UserRole.SECURITY_ADMIN],
    },
  ];

  return (
    <aside className="w-64 bg-slate-900 text-slate-300 min-h-[calc(100vh-4rem)] p-4 flex flex-col justify-between shrink-0">
      <div className="space-y-6">
        <div>
          <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider px-3 mb-2">
            Navigation
          </div>
          <nav className="space-y-1">
            {navItems.map((item) => {
              const isAllowed = !item.allowedRoles || hasAnyRole(item.allowedRoles);

              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    `flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-colors ${
                      isActive
                        ? 'bg-indigo-600 text-white shadow-xs'
                        : isAllowed
                        ? 'text-slate-300 hover:bg-slate-800 hover:text-white'
                        : 'text-slate-500 hover:bg-slate-800/50 hover:text-slate-400'
                    }`
                  }
                >
                  <div className="flex items-center gap-3">
                    {item.icon}
                    <span>{item.name}</span>
                  </div>
                  {!isAllowed && (
                    <span title="Requires Administrative Role">
                      <Lock className="w-3.5 h-3.5 text-slate-500" />
                    </span>
                  )}
                </NavLink>
              );
            })}
          </nav>
        </div>

        <div className="px-3 py-3 bg-slate-800/60 rounded-xl border border-slate-700/50 text-xs">
          <div className="flex items-center gap-2 text-slate-300 font-semibold mb-1">
            <Activity className="w-3.5 h-3.5 text-indigo-400" />
            <span>Zero-Trust Engine</span>
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Deterministic policy & risk evaluation. Backend is authoritative.
          </p>
        </div>
      </div>

      <div className="px-3 py-2 text-[10px] text-slate-500 border-t border-slate-800 font-mono">
        AegisOne v0.1.0 (Iter 13)
      </div>
    </aside>
  );
};
