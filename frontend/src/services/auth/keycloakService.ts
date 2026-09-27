import Keycloak from 'keycloak-js';
import { env } from '@/app/config/env';
import { AuthenticatedUser, UserRole } from '@/types/auth';

class KeycloakService {
  private keycloak: Keycloak | null = null;
  private isInitialized = false;
  private initPromise: Promise<boolean> | null = null;
  private listeners: Set<(authenticated: boolean) => void> = new Set();

  public getInstance(): Keycloak {
    if (!this.keycloak) {
      this.keycloak = new Keycloak({
        url: env.keycloakUrl,
        realm: env.keycloakRealm,
        clientId: env.keycloakClientId,
      });
    }
    return this.keycloak;
  }

  public subscribe(listener: (authenticated: boolean) => void): () => void {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }

  private notifyListeners(authenticated: boolean): void {
    this.listeners.forEach((listener) => {
      try {
        listener(authenticated);
      } catch (err) {
        console.warn('[AUTH] Error in auth listener:', err);
      }
    });
  }

  public async init(onAuthenticatedChange?: (authenticated: boolean) => void): Promise<boolean> {
    if (onAuthenticatedChange) {
      this.subscribe(onAuthenticatedChange);
    }

    if (this.isInitialized) {
      const isAuth = !!this.keycloak?.authenticated;
      if (onAuthenticatedChange) {
        onAuthenticatedChange(isAuth);
      }
      return isAuth;
    }

    if (this.initPromise) {
      return this.initPromise;
    }

    console.log('[AUTH] init started');
    console.log('[AUTH] window.location.href:', window.location.href);

    this.initPromise = (async () => {
      const kc = this.getInstance();

      kc.onReady = (authenticated) => {
        console.log(`[AUTH] init completed (authenticated = ${authenticated})`);
      };

      kc.onAuthSuccess = () => {
        console.log('[AUTH] auth success');
        if (kc.token) {
          console.log('[AUTH] token acquired');
        }
        this.notifyListeners(true);
      };

      kc.onAuthError = (errorData) => {
        console.warn('[AUTH] auth error:', errorData);
        this.notifyListeners(false);
      };

      kc.onAuthRefreshSuccess = () => {
        console.log('[AUTH] token acquired (refresh success)');
        this.notifyListeners(true);
      };

      kc.onAuthRefreshError = () => {
        console.warn('[AUTH] token refresh error');
        this.notifyListeners(false);
      };

      kc.onAuthLogout = () => {
        console.log('[AUTH] auth logout');
        this.notifyListeners(false);
      };

      kc.onTokenExpired = () => {
        kc.updateToken(30).catch(() => {
          console.warn('[AUTH] Failed to refresh expired token, logging out.');
          this.logout();
        });
      };

      try {
        // Deterministic initialization without silent check-sso iframe cookie race
        const authenticated = await kc.init({
          pkceMethod: 'S256',
          checkLoginIframe: false,
        });

        this.isInitialized = true;
        console.log(`[AUTH] init completed (authenticated = ${authenticated})`);
        console.log('[AUTH] keycloak.authenticated:', kc.authenticated);
        console.log('[AUTH] keycloak.tokenParsed.preferred_username:', kc.tokenParsed?.preferred_username);
        console.log('[AUTH] keycloak.tokenParsed.sub:', kc.tokenParsed?.sub);

        this.notifyListeners(authenticated);
        return authenticated;
      } catch (error) {
        console.warn('[AUTH] Keycloak initialization failed:', error);
        this.isInitialized = true;
        this.notifyListeners(false);
        return false;
      }
    })();

    return this.initPromise;
  }

  public async login(): Promise<void> {
    console.log('[AUTH] login requested');
    const kc = this.getInstance();

    if (kc.authenticated) {
      console.log('[AUTH] login skipped because already authenticated');
      console.log('[AUTH] redirecting to dashboard');
      window.location.href = window.location.origin + '/dashboard';
      return;
    }

    console.log('[AUTH] redirecting to Keycloak authorization endpoint');
    await kc.login({ redirectUri: window.location.origin + '/dashboard' });
  }

  public async logout(): Promise<void> {
    console.log('[AUTH] logout requested');
    const kc = this.getInstance();
    this.isInitialized = false;
    this.initPromise = null;

    if (kc.authenticated) {
      await kc.logout({ redirectUri: window.location.origin + '/login' });
    } else {
      window.location.href = window.location.origin + '/login';
    }
  }

  public async updateToken(minValidity = 30): Promise<boolean> {
    const kc = this.getInstance();
    if (!kc.authenticated) return false;
    try {
      const refreshed = await kc.updateToken(minValidity);
      if (refreshed) {
        console.log('[AUTH] token acquired');
      }
      return true;
    } catch (error) {
      console.warn('[AUTH] Controlled token refresh failed:', error);
      return false;
    }
  }

  public getToken(): string | null {
    return this.keycloak?.token || null;
  }

  public isAuthenticated(): boolean {
    return !!this.keycloak?.authenticated;
  }

  public getUser(): AuthenticatedUser | null {
    if (!this.keycloak?.authenticated || !this.keycloak.tokenParsed) {
      return null;
    }

    const token = this.keycloak.tokenParsed as Record<string, any>;
    const realmAccess = token.realm_access || { roles: [] };

    const parsedRoles = (realmAccess.roles || [])
      .map((r: string) => r.toUpperCase())
      .filter((r: string) => Object.values(UserRole).includes(r as UserRole)) as UserRole[];

    return {
      user_id: token.sub || 'unknown',
      username: token.preferred_username || token.sub || 'user',
      email: token.email,
      first_name: token.given_name,
      last_name: token.family_name,
      roles: parsedRoles,
    };
  }

  public getRoles(): UserRole[] {
    const user = this.getUser();
    return user ? user.roles : [];
  }
}

export const keycloakService = new KeycloakService();
