import React from 'react';
import { useAuth } from '@/hooks/useAuth';
import { HealthBadge } from '@/components/common/HealthBadge';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { LogIn, LogOut, ShieldCheck, User } from 'lucide-react';

export const Header: React.FC = () => {
  const { authenticated, user, roles, logout, login } = useAuth();

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between sticky top-0 z-30 shadow-2xs">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-indigo-600 text-white rounded-lg shadow-sm">
          <ShieldCheck className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-sm font-bold text-slate-900 tracking-tight">AegisOne</h1>
          <p className="text-[10px] text-slate-500 font-mono">Conditional Access Lab</p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <HealthBadge />

        {authenticated && user ? (
          <div className="flex items-center gap-3 pl-3 border-l border-slate-200">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-600 text-xs font-semibold">
                <User className="w-4 h-4" />
              </div>
              <div className="text-left hidden sm:block">
                <div className="text-xs font-semibold text-slate-900 leading-none">
                  {user.username}
                </div>
                <div className="flex items-center gap-1 mt-1">
                  {roles.length > 0 ? (
                    roles.slice(0, 2).map((r) => (
                      <Badge key={r} variant="info" className="text-[9px] px-1.5 py-0 font-mono">
                        {r}
                      </Badge>
                    ))
                  ) : (
                    <span className="text-[10px] text-slate-400">No roles</span>
                  )}
                </div>
              </div>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={() => logout()}
              title="Logout from Keycloak"
              className="text-xs"
            >
              <LogOut className="w-3.5 h-3.5 mr-1" /> Logout
            </Button>
          </div>
        ) : (
          <Button variant="primary" size="sm" onClick={() => login()} className="text-xs">
            <LogIn className="w-3.5 h-3.5 mr-1" /> Keycloak Login
          </Button>
        )}
      </div>
    </header>
  );
};
