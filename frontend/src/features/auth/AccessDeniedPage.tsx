import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { ArrowLeft, ShieldAlert } from 'lucide-react';

export const AccessDeniedPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-[70vh] flex items-center justify-center p-4">
      <Card className="max-w-md w-full border-rose-200 bg-rose-50/30 text-center">
        <CardHeader>
          <div className="mx-auto w-12 h-12 bg-rose-100 text-rose-600 rounded-full flex items-center justify-center mb-2">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <CardTitle className="text-lg text-rose-950 font-bold">Access Denied</CardTitle>
          <CardDescription className="text-rose-700 text-xs mt-1">
            HTTP 403 — Insufficient Permissions
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-xs text-slate-600 leading-relaxed">
            You do not possess the required administrative roles (e.g. ADMIN or SECURITY_ADMIN) to access this platform feature.
          </p>
          <Button variant="outline" size="sm" onClick={() => navigate('/dashboard')} className="mt-2">
            <ArrowLeft className="w-3.5 h-3.5 mr-1.5" /> Back to Dashboard
          </Button>
        </CardContent>
      </Card>
    </div>
  );
};
