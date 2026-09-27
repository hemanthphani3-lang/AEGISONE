import React, { createContext, useContext, useEffect, useState } from 'react';
import { keycloakService } from '@/services/auth/keycloakService';
import { authApi } from '@/services/api/authApi';
import { AuthenticatedUser, AuthLifecycleStatus, Permission, ROLE_PERMISSIONS, UserRole } from '@/types/auth';

interface AuthContextType {
  status: AuthLifecycleStatus;
  authenticated: boolean;
  loading: boolean;
  user: AuthenticatedUser | null;
  roles: UserRole[];
  token: string | null;
  error: string | null;
  login: () => Promise<void>;
  logout: () => Promise<void>;
  refetchUser: () => Promise<void>;
  hasRole: (role: UserRole) => boolean;
  hasAnyRole: (roles: UserRole[]) => boolean;
  hasAllRoles: (roles: UserRole[]) => boolean;
  hasPermission: (permission: Permission) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [status, setStatus] = useState<AuthLifecycleStatus>('INITIALIZING');
  const [authenticated, setAuthenticated] = useState<boolean>(false);
  const [user, setUser] = useState<AuthenticatedUser | null>(null);
  const [roles, setRoles] = useState<UserRole[]>([]);
  const [token, setToken] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const syncBackendUser = async (isMounted = true): Promise<boolean> => {
    try {
      let meUser: AuthenticatedUser | null = null;
      try {
        meUser = await authApi.getMe();
        console.log('[AUTH] auth/me response:', meUser);
      } catch (err: any) {
        if (err?.status === 401) {
          console.warn('[AUTH] /auth/me returned 401, attempting 1 controlled token refresh');
          const refreshed = await keycloakService.updateToken(30);
          if (refreshed) {
            meUser = await authApi.getMe();
            console.log('[AUTH] auth/me response after retry:', meUser);
          } else {
            throw err;
          }
        } else {
          // Backend offline or unreachable — fallback to Keycloak token claims
          console.warn('[AUTH] /auth/me unreachable, using token claims fallback:', err?.message || err);
          meUser = keycloakService.getUser();
        }
      }

      if (isMounted && meUser) {
        setUser(meUser);
        setRoles(meUser.roles || []);
        setToken(keycloakService.getToken());
        setAuthenticated(true);
        setStatus('AUTHENTICATED');
        return true;
      }
    } catch (err: any) {
      console.warn('[AUTH] Backend identity synchronization failed:', err?.message || err);
      if (isMounted) {
        const kcUser = keycloakService.getUser();
        if (kcUser) {
          setUser(kcUser);
          setRoles(kcUser.roles || []);
          setToken(keycloakService.getToken());
          setAuthenticated(true);
          setStatus('AUTHENTICATED');
          return true;
        } else {
          setUser(null);
          setRoles([]);
          setToken(null);
          setAuthenticated(false);
          setStatus('UNAUTHENTICATED');
          return false;
        }
      }
    }
    return false;
  };

  useEffect(() => {
    let isMounted = true;

    const initAuth = async () => {
      try {
        const isAuth = await keycloakService.init(async (authResult) => {
          if (!isMounted) return;

          if (authResult) {
            await syncBackendUser(isMounted);
          } else {
            setUser(null);
            setRoles([]);
            setToken(null);
            setAuthenticated(false);
            setStatus('UNAUTHENTICATED');
          }
        });

        if (isMounted) {
          if (isAuth) {
            await syncBackendUser(isMounted);
          } else {
            setUser(null);
            setRoles([]);
            setToken(null);
            setAuthenticated(false);
            setStatus('UNAUTHENTICATED');
          }
        }
      } catch (err: any) {
        if (isMounted) {
          console.error('[AUTH] Authentication initialization error:', err);
          setError(err.message || 'Authentication initialization failed');
          setStatus('ERROR');
        }
      }
    };

    initAuth();

    return () => {
      isMounted = false;
    };
  }, []);

  const login = async () => {
    if (status === 'AUTHENTICATING' || status === 'LOGGING_OUT') {
      console.log('[AUTH] login call ignored (operation in progress)');
      return;
    }
    if (authenticated) {
      console.log('[AUTH] login skipped because already authenticated');
      return;
    }

    try {
      setStatus('AUTHENTICATING');
      await keycloakService.login();
    } catch (err: any) {
      console.error('[AUTH] Login error:', err);
      setStatus('UNAUTHENTICATED');
      setError(err.message || 'Login failed');
    }
  };

  const logout = async () => {
    try {
      setStatus('LOGGING_OUT');
      await keycloakService.logout();
    } finally {
      setAuthenticated(false);
      setUser(null);
      setRoles([]);
      setToken(null);
      setStatus('UNAUTHENTICATED');
    }
  };

  const refetchUser = async () => {
    await syncBackendUser(true);
  };

  const hasRole = (role: UserRole): boolean => {
    return roles.includes(role);
  };

  const hasAnyRole = (requiredRoles: UserRole[]): boolean => {
    if (requiredRoles.length === 0) return true;
    return requiredRoles.some((r) => roles.includes(r));
  };

  const hasAllRoles = (requiredRoles: UserRole[]): boolean => {
    if (requiredRoles.length === 0) return true;
    return requiredRoles.every((r) => roles.includes(r));
  };

  const hasPermission = (permission: Permission): boolean => {
    const userPermissions = new Set<Permission>();
    for (const role of roles) {
      const perms = ROLE_PERMISSIONS[role] || [];
      for (const p of perms) {
        userPermissions.add(p);
      }
    }
    return userPermissions.has(permission);
  };

  const loading = status === 'INITIALIZING';

  return (
    <AuthContext.Provider
      value={{
        status,
        authenticated,
        loading,
        user,
        roles,
        token,
        error,
        login,
        logout,
        refetchUser,
        hasRole,
        hasAnyRole,
        hasAllRoles,
        hasPermission,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
