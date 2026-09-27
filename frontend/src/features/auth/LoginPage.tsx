import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Skeleton } from '@/components/ui/Skeleton';
import { LogIn, ShieldCheck } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const { status, authenticated, login } = useAuth();

  if (status === 'INITIALIZING') {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
        <Card className="max-w-md w-full border-slate-800 bg-slate-900 text-white shadow-2xl p-6 space-y-4">
          <Skeleton className="h-12 w-12 rounded-xl mx-auto bg-slate-800" />
          <Skeleton className="h-6 w-48 mx-auto bg-slate-800" />
          <Skeleton className="h-20 w-full bg-slate-800" />
          <Skeleton className="h-10 w-full bg-slate-800" />
        </Card>
      </div>
    );
  }

  if (authenticated || status === 'AUTHENTICATED') {
    console.log('[AUTH] User is already authenticated, navigating from /login to /dashboard');
    return <Navigate to="/dashboard" replace />;
  }

  const isAuthenticating = status === 'AUTHENTICATING';

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
      <Card className="max-w-md w-full border-slate-800 bg-slate-900 text-white shadow-2xl">
        <CardHeader className="text-center border-slate-800 pb-2">
          <div className="mx-auto w-12 h-12 bg-indigo-600 rounded-xl flex items-center justify-center text-white mb-3 shadow-md">
            <ShieldCheck className="w-7 h-7" />
          </div>
          <CardTitle className="text-xl text-white font-bold">AegisOne</CardTitle>
          <CardDescription className="text-slate-400 text-xs mt-1">
            Zero-Cost Conditional Access Policy Lab & Simulator
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6 pt-4">
          <div className="p-4 bg-slate-800/80 rounded-lg border border-slate-700/60 text-xs text-slate-300 leading-relaxed">
            AegisOne enforces Zero-Trust authentication and conditional access policies via a centralized backend security engine and Keycloak OIDC identity server.
          </div>

          <Button
            variant="primary"
            size="lg"
            className="w-full justify-center bg-indigo-600 hover:bg-indigo-500 py-3 text-sm font-semibold"
            onClick={() => login()}
            disabled={isAuthenticating}
            loading={isAuthenticating}
          >
            <LogIn className="w-4 h-4 mr-2" />
            {isAuthenticating ? 'Redirecting to Keycloak...' : 'Single Sign-On with Keycloak'}
          </Button>

          <p className="text-[11px] text-center text-slate-500">
            Protected by Keycloak OIDC + Bearer Token Validation
          </p>
        </CardContent>
      </Card>
    </div>
  );
};
