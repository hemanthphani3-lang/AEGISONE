import React from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AppShell } from '@/components/layout/AppShell';
import { UserRole } from '@/types/auth';

import { ProtectedRoute } from './ProtectedRoute';
import { AccessDeniedPage } from '@/features/auth/AccessDeniedPage';
import { LoginPage } from '@/features/auth/LoginPage';
import { DashboardPage } from '@/features/dashboard/DashboardPage';
import { PoliciesPage } from '@/features/policies/PoliciesPage';
import { EvaluationPage } from '@/features/evaluation/EvaluationPage';
import { AuditPage } from '@/features/audit/AuditPage';
import { SimulationPage } from '@/features/simulation/SimulationPage';
import { RiskPage } from '@/features/risk/RiskPage';
import { SOCPage } from '@/features/soc/SOCPage';
import { UserManagementPage } from '@/features/users/UserManagementPage';

export const AppRouter: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/access-denied" element={<AccessDeniedPage />} />

        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <AppShell>
                <DashboardPage />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/incidents"
          element={
            <ProtectedRoute allowedRoles={[UserRole.ADMIN, UserRole.SECURITY_ADMIN, UserRole.STAFF, UserRole.BREAK_GLASS]}>
              <AppShell>
                <SOCPage />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route path="/security" element={<Navigate to="/incidents" replace />} />

        <Route
          path="/policies"
          element={
            <ProtectedRoute allowedRoles={[UserRole.ADMIN, UserRole.SECURITY_ADMIN]}>
              <AppShell>
                <PoliciesPage />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/evaluation"
          element={
            <ProtectedRoute>
              <AppShell>
                <EvaluationPage />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/users"
          element={
            <ProtectedRoute allowedRoles={[UserRole.ADMIN, UserRole.SECURITY_ADMIN]}>
              <AppShell>
                <UserManagementPage />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/risk"
          element={
            <ProtectedRoute>
              <AppShell>
                <RiskPage />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/audit"
          element={
            <ProtectedRoute allowedRoles={[UserRole.ADMIN, UserRole.SECURITY_ADMIN]}>
              <AppShell>
                <AuditPage />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/simulation"
          element={
            <ProtectedRoute allowedRoles={[UserRole.ADMIN, UserRole.SECURITY_ADMIN]}>
              <AppShell>
                <SimulationPage />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
};
