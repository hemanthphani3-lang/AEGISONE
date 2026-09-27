export const env = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  keycloakUrl: import.meta.env.VITE_KEYCLOAK_URL || 'http://localhost:8080',
  keycloakRealm: import.meta.env.VITE_KEYCLOAK_REALM || 'accessguard',
  keycloakClientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID || 'accessguard-frontend',
};
