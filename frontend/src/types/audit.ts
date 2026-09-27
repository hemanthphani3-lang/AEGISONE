export enum AuditEventType {
  AUTHENTICATION_SUCCESS = 'AUTHENTICATION_SUCCESS',
  AUTHENTICATION_FAILURE = 'AUTHENTICATION_FAILURE',
  AUTHORIZATION_DENIED = 'AUTHORIZATION_DENIED',
  POLICY_CREATED = 'POLICY_CREATED',
  POLICY_UPDATED = 'POLICY_UPDATED',
  POLICY_ENABLED = 'POLICY_ENABLED',
  POLICY_DISABLED = 'POLICY_DISABLED',
  POLICY_DELETED = 'POLICY_DELETED',
  POLICY_EVALUATED = 'POLICY_EVALUATED',
  POLICY_SIMULATED = 'POLICY_SIMULATED',
}

export enum AuditOutcome {
  SUCCESS = 'SUCCESS',
  FAILURE = 'FAILURE',
  DENIED = 'DENIED',
}

export interface AuditEvent {
  id: string;
  timestamp: string;
  actor_user_id: string;
  actor_username?: string | null;
  actor_roles: string[];
  event_type: AuditEventType;
  action: string;
  resource_type: string;
  resource_id?: string | null;
  outcome: AuditOutcome;
  metadata: Record<string, unknown>;
  correlation_id?: string | null;
}
