import React from 'react';
import { useAuth } from '@/hooks/useAuth';
import { UserRole } from '@/types/auth';
import { AdminSecurityDashboard } from './AdminSecurityDashboard';
import { StaffStudentDashboard } from './StaffStudentDashboard';
import { AccessDeniedPage } from '@/features/auth/AccessDeniedPage';

export const DashboardPage: React.FC = () => {
  const { roles, hasAnyRole } = useAuth();

  // Priority 1: ADMIN or SECURITY_ADMIN -> AdminSecurityDashboard
  const isAdminGroup = hasAnyRole([UserRole.ADMIN, UserRole.SECURITY_ADMIN]);
  if (isAdminGroup) {
    return <AdminSecurityDashboard />;
  }

  // Priority 2: STAFF, STUDENT, or BREAK_GLASS -> StaffStudentDashboard
  const isUserGroup = hasAnyRole([UserRole.STAFF, UserRole.STUDENT, UserRole.BREAK_GLASS]);
  if (isUserGroup) {
    return <StaffStudentDashboard />;
  }

  // Priority 3: Unknown or missing authoritative role -> Access Denied
  return <AccessDeniedPage />;
};
