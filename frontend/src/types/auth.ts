export enum UserRole {
  ADMIN = 'ADMIN',
  SECURITY_ADMIN = 'SECURITY_ADMIN',
  BREAK_GLASS = 'BREAK_GLASS',
  STAFF = 'STAFF',
  STUDENT = 'STUDENT',
}

export enum Permission {
  READ_POLICY = 'READ_POLICY',
  WRITE_POLICY = 'WRITE_POLICY',
  DELETE_POLICY = 'DELETE_POLICY',
  READ_AUDIT = 'READ_AUDIT',
  RUN_SIMULATION = 'RUN_SIMULATION',
  EVALUATE_ACCESS = 'EVALUATE_ACCESS',
  VIEW_RISK = 'VIEW_RISK',
  READ_INCIDENTS = 'READ_INCIDENTS',
  MANAGE_INCIDENTS = 'MANAGE_INCIDENTS',
  REMEDIATE_INCIDENTS = 'REMEDIATE_INCIDENTS',
}

export const ROLE_PERMISSIONS: Record<UserRole, Permission[]> = {
  [UserRole.ADMIN]: [
    Permission.READ_POLICY,
    Permission.WRITE_POLICY,
    Permission.DELETE_POLICY,
    Permission.READ_AUDIT,
    Permission.RUN_SIMULATION,
    Permission.EVALUATE_ACCESS,
    Permission.VIEW_RISK,
    Permission.READ_INCIDENTS,
    Permission.MANAGE_INCIDENTS,
    Permission.REMEDIATE_INCIDENTS,
  ],
  [UserRole.SECURITY_ADMIN]: [
    Permission.READ_POLICY,
    Permission.WRITE_POLICY,
    Permission.DELETE_POLICY,
    Permission.READ_AUDIT,
    Permission.RUN_SIMULATION,
    Permission.EVALUATE_ACCESS,
    Permission.VIEW_RISK,
    Permission.READ_INCIDENTS,
    Permission.MANAGE_INCIDENTS,
    Permission.REMEDIATE_INCIDENTS,
  ],
  [UserRole.STAFF]: [
    Permission.READ_POLICY,
    Permission.EVALUATE_ACCESS,
    Permission.VIEW_RISK,
    Permission.READ_INCIDENTS,
  ],
  [UserRole.STUDENT]: [
    Permission.EVALUATE_ACCESS,
  ],
  [UserRole.BREAK_GLASS]: [
    Permission.READ_POLICY,
    Permission.EVALUATE_ACCESS,
    Permission.READ_INCIDENTS,
  ],
};

export interface AuthenticatedUser {
  user_id: string;
  username: string;
  email?: string;
  first_name?: string;
  last_name?: string;
  roles: UserRole[];
}

export type AuthLifecycleStatus =
  | 'INITIALIZING'
  | 'AUTHENTICATED'
  | 'UNAUTHENTICATED'
  | 'AUTHENTICATING'
  | 'LOGGING_OUT'
  | 'ERROR';

export interface AuthState {
  status: AuthLifecycleStatus;
  authenticated: boolean;
  loading: boolean;
  user: AuthenticatedUser | null;
  roles: UserRole[];
  token: string | null;
  error: string | null;
}
