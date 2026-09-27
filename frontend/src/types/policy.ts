import { UserRole } from './auth';

export enum PolicyDecision {
  ALLOW = 'ALLOW',
  MFA_REQUIRED = 'MFA_REQUIRED',
  BLOCK = 'BLOCK',
}

export enum AuthProtocol {
  MODERN = 'MODERN',
  LEGACY = 'LEGACY',
}

export enum RiskLevel {
  LOW = 'LOW',
  MEDIUM = 'MEDIUM',
  HIGH = 'HIGH',
  UNKNOWN = 'UNKNOWN',
}

export interface Policy {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  target_roles: UserRole[];
  target_protocols: AuthProtocol[];
  target_locations?: string[];
  target_device_managed?: boolean | null;
  target_device_compliant?: boolean | null;
  target_risk_level?: RiskLevel | null;
  action: PolicyDecision;
  exclusions: UserRole[];
  excluded_users: string[];
  version?: number;
}

export interface PolicyCreate {
  id: string;
  name: string;
  description?: string;
  enabled?: boolean;
  target_roles?: UserRole[];
  target_protocols?: AuthProtocol[];
  target_locations?: string[];
  target_device_managed?: boolean | null;
  target_device_compliant?: boolean | null;
  target_risk_level?: RiskLevel | null;
  action: PolicyDecision;
  exclusions?: UserRole[];
  excluded_users?: string[];
  version?: number;
}

export interface PolicyUpdate {
  name?: string;
  description?: string;
  enabled?: boolean;
  target_roles?: UserRole[];
  target_protocols?: AuthProtocol[];
  target_locations?: string[];
  target_device_managed?: boolean | null;
  target_device_compliant?: boolean | null;
  target_risk_level?: RiskLevel | null;
  action?: PolicyDecision;
  exclusions?: UserRole[];
  excluded_users?: string[];
  version?: number;
  expected_version?: number;
}

export interface PolicyValidationResponse {
  valid: boolean;
  warnings: string[];
  errors: string[];
}

export interface PolicyVersionSummary {
  id: string;
  policy_id: string;
  version: number;
  change_type: string;
  changed_by_user_id: string;
  changed_by_username?: string | null;
  changed_at: string;
  correlation_id: string;
}

export interface PolicyVersionDetail {
  id: string;
  policy_id: string;
  version: number;
  snapshot: Policy;
  change_type: string;
  changed_by_user_id: string;
  changed_by_username?: string | null;
  changed_at: string;
  correlation_id: string;
}

export interface PolicyVersionListResponse {
  versions: PolicyVersionSummary[];
}

export interface FieldDiff {
  previous: any;
  new: any;
}

export interface PolicyDiffResponse {
  policy_id: string;
  from_version: number;
  to_version: number;
  changed_fields: string[];
  field_diffs: Record<string, FieldDiff>;
  added_collection_items: Record<string, any[]>;
  removed_collection_items: Record<string, any[]>;
}

export interface PolicyRollbackRequest {
  target_version: number;
  expected_current_version?: number;
}
