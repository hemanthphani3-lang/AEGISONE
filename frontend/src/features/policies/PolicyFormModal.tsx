import React, { useEffect, useState } from 'react';
import { AuthProtocol, Policy, PolicyCreate, PolicyDecision, PolicyUpdate, PolicyValidationResponse, RiskLevel } from '@/types/policy';
import { UserRole } from '@/types/auth';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { policyApi } from '@/services/api/policyApi';
import { AlertTriangle, CheckCircle2, ShieldAlert } from 'lucide-react';

interface PolicyFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: PolicyCreate | PolicyUpdate) => Promise<void>;
  initialPolicy?: Policy | null;
  loading?: boolean;
}

export const PolicyFormModal: React.FC<PolicyFormModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  initialPolicy,
  loading = false,
}) => {
  const isEditing = !!initialPolicy;

  const [id, setId] = useState<string>('');
  const [name, setName] = useState<string>('');
  const [description, setDescription] = useState<string>('');
  const [action, setAction] = useState<PolicyDecision>(PolicyDecision.MFA_REQUIRED);
  const [enabled, setEnabled] = useState<boolean>(true);
  const [targetRoles, setTargetRoles] = useState<UserRole[]>([]);
  const [targetProtocols, setTargetProtocols] = useState<AuthProtocol[]>([]);
  const [targetRiskLevel, setTargetRiskLevel] = useState<RiskLevel | ''>('');
  const [exclusions, setExclusions] = useState<UserRole[]>([]);
  const [excludedUsersStr, setExcludedUsersStr] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  // Validation state
  const [validationResult, setValidationResult] = useState<PolicyValidationResponse | null>(null);
  const [validating, setValidating] = useState<boolean>(false);

  useEffect(() => {
    if (initialPolicy) {
      setId(initialPolicy.id);
      setName(initialPolicy.name);
      setDescription(initialPolicy.description || '');
      setAction(initialPolicy.action);
      setEnabled(initialPolicy.enabled);
      setTargetRoles(initialPolicy.target_roles || []);
      setTargetProtocols(initialPolicy.target_protocols || []);
      setTargetRiskLevel(initialPolicy.target_risk_level || '');
      setExclusions(initialPolicy.exclusions || []);
      setExcludedUsersStr((initialPolicy.excluded_users || []).join(', '));
    } else {
      setId('');
      setName('');
      setDescription('');
      setAction(PolicyDecision.MFA_REQUIRED);
      setEnabled(true);
      setTargetRoles([]);
      setTargetProtocols([]);
      setTargetRiskLevel('');
      setExclusions([]);
      setExcludedUsersStr('');
    }
    setError(null);
    setValidationResult(null);
  }, [initialPolicy, isOpen]);

  const getPayload = (): PolicyCreate | PolicyUpdate => {
    const excludedUsers = excludedUsersStr
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean);

    return {
      ...(isEditing ? { expected_version: initialPolicy?.version } : { id: id.trim() }),
      name: name.trim(),
      description: description.trim(),
      action,
      enabled,
      target_roles: targetRoles,
      target_protocols: targetProtocols,
      target_risk_level: targetRiskLevel ? (targetRiskLevel as RiskLevel) : null,
      exclusions,
      excluded_users: excludedUsers,
    };
  };

  const handleValidate = async () => {
    setValidating(true);
    setError(null);
    try {
      const payload = getPayload();
      const res = isEditing
        ? await policyApi.validateExistingPolicy(initialPolicy.id, payload)
        : await policyApi.validatePolicy(payload);
      setValidationResult(res);
    } catch (err: any) {
      setError(err.message || 'Validation request failed.');
    } finally {
      setValidating(false);
    }
  };

  const toggleRole = (role: UserRole, targetState: UserRole[], setter: (val: UserRole[]) => void) => {
    if (targetState.includes(role)) {
      setter(targetState.filter((r) => r !== role));
    } else {
      setter([...targetState, role]);
    }
    setValidationResult(null);
  };

  const toggleProtocol = (proto: AuthProtocol) => {
    if (targetProtocols.includes(proto)) {
      setTargetProtocols(targetProtocols.filter((p) => p !== proto));
    } else {
      setTargetProtocols([...targetProtocols, proto]);
    }
    setValidationResult(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!isEditing && (!id.trim() || !/^[a-z0-9-]+$/.test(id.trim()))) {
      setError('Policy ID is required and must contain lowercase letters, numbers, or hyphens (e.g. admin-mfa).');
      return;
    }

    if (!name.trim()) {
      setError('Policy Name is required.');
      return;
    }

    const payload = getPayload();

    try {
      await onSubmit(payload);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to save policy.');
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={
        isEditing
          ? `Edit Policy: ${initialPolicy?.name} (v${initialPolicy?.version || 1})`
          : 'Create New Conditional Access Policy'
      }
      maxWidth="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-4 text-xs">
        {error && (
          <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 rounded-lg font-medium flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 shrink-0 text-rose-600" />
            <span>{error}</span>
          </div>
        )}

        {validationResult && (
          <div className="space-y-2">
            {validationResult.valid ? (
              <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-900 rounded-lg font-medium flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                <span>Policy definition is valid.</span>
              </div>
            ) : (
              <div className="p-3 bg-rose-50 border border-rose-200 text-rose-900 rounded-lg space-y-1">
                <div className="font-semibold flex items-center gap-1.5 text-rose-700">
                  <ShieldAlert className="w-4 h-4 shrink-0" />
                  Validation Errors Found:
                </div>
                <ul className="list-disc list-inside space-y-0.5 text-rose-800">
                  {validationResult.errors.map((err, idx) => (
                    <li key={idx}>{err}</li>
                  ))}
                </ul>
              </div>
            )}

            {validationResult.warnings.length > 0 && (
              <div className="p-3 bg-amber-50 border border-amber-200 text-amber-900 rounded-lg space-y-1">
                <div className="font-semibold flex items-center gap-1.5 text-amber-800">
                  <AlertTriangle className="w-4 h-4 shrink-0" />
                  Safety Warnings:
                </div>
                <ul className="list-disc list-inside space-y-0.5 text-amber-800">
                  {validationResult.warnings.map((warn, idx) => (
                    <li key={idx}>{warn}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label className="font-semibold text-slate-700 block mb-1">
              Policy ID {!isEditing && <span className="text-rose-500">*</span>}
            </label>
            <input
              type="text"
              className="w-full p-2 border border-slate-300 rounded-md disabled:bg-slate-100 font-mono"
              placeholder="e.g. block-legacy-auth"
              value={id}
              onChange={(e) => {
                setId(e.target.value);
                setValidationResult(null);
              }}
              disabled={isEditing || loading}
            />
          </div>

          <div>
            <label className="font-semibold text-slate-700 block mb-1">
              Action <span className="text-rose-500">*</span>
            </label>
            <select
              className="w-full p-2 border border-slate-300 rounded-md bg-white font-medium"
              value={action}
              onChange={(e) => {
                setAction(e.target.value as PolicyDecision);
                setValidationResult(null);
              }}
              disabled={loading}
            >
              <option value={PolicyDecision.MFA_REQUIRED}>MFA_REQUIRED</option>
              <option value={PolicyDecision.BLOCK}>BLOCK</option>
              <option value={PolicyDecision.ALLOW}>ALLOW</option>
            </select>
          </div>
        </div>

        <div>
          <label className="font-semibold text-slate-700 block mb-1">
            Policy Name <span className="text-rose-500">*</span>
          </label>
          <input
            type="text"
            className="w-full p-2 border border-slate-300 rounded-md"
            placeholder="e.g. Require MFA for Administrators"
            value={name}
            onChange={(e) => {
              setName(e.target.value);
              setValidationResult(null);
            }}
            disabled={loading}
          />
        </div>

        <div>
          <label className="font-semibold text-slate-700 block mb-1">Description</label>
          <textarea
            className="w-full p-2 border border-slate-300 rounded-md h-16"
            placeholder="Briefly describe the security objective of this policy"
            value={description}
            onChange={(e) => {
              setDescription(e.target.value);
              setValidationResult(null);
            }}
            disabled={loading}
          />
        </div>

        <div className="flex items-center gap-2 pt-1">
          <input
            type="checkbox"
            id="policy-enabled"
            className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
            checked={enabled}
            onChange={(e) => {
              setEnabled(e.target.checked);
              setValidationResult(null);
            }}
            disabled={loading}
          />
          <label htmlFor="policy-enabled" className="font-semibold text-slate-800 cursor-pointer">
            Enable Policy (Active for evaluation)
          </label>
        </div>

        <div className="border-t border-slate-100 pt-3 space-y-3">
          <h4 className="font-semibold text-slate-800">Target Match Criteria</h4>

          <div>
            <label className="text-slate-600 block mb-1.5 font-medium">Target Roles:</label>
            <div className="flex flex-wrap gap-2">
              {Object.values(UserRole).map((role) => (
                <label key={role} className="flex items-center gap-1.5 text-xs bg-slate-50 border px-2 py-1 rounded cursor-pointer">
                  <input
                    type="checkbox"
                    checked={targetRoles.includes(role)}
                    onChange={() => toggleRole(role, targetRoles, setTargetRoles)}
                    disabled={loading}
                  />
                  <span>{role}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="text-slate-600 block mb-1.5 font-medium">Target Protocols:</label>
              <div className="flex gap-2">
                {Object.values(AuthProtocol).map((proto) => (
                  <label key={proto} className="flex items-center gap-1.5 text-xs bg-slate-50 border px-2 py-1 rounded cursor-pointer">
                    <input
                      type="checkbox"
                      checked={targetProtocols.includes(proto)}
                      onChange={() => toggleProtocol(proto)}
                      disabled={loading}
                    />
                    <span>{proto}</span>
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label className="text-slate-600 block mb-1 font-medium">Target Risk Level:</label>
              <select
                className="w-full p-2 border border-slate-300 rounded-md bg-white"
                value={targetRiskLevel}
                onChange={(e) => {
                  setTargetRiskLevel(e.target.value as RiskLevel | '');
                  setValidationResult(null);
                }}
                disabled={loading}
              >
                <option value="">Any Risk Level</option>
                <option value={RiskLevel.HIGH}>HIGH Risk</option>
                <option value={RiskLevel.MEDIUM}>MEDIUM Risk</option>
                <option value={RiskLevel.LOW}>LOW Risk</option>
                <option value={RiskLevel.UNKNOWN}>UNKNOWN Risk</option>
              </select>
            </div>
          </div>
        </div>

        <div className="border-t border-slate-100 pt-3 space-y-3">
          <h4 className="font-semibold text-slate-800">Exclusion Criteria</h4>

          <div>
            <label className="text-slate-600 block mb-1.5 font-medium">Excluded Roles:</label>
            <div className="flex flex-wrap gap-2">
              {Object.values(UserRole).map((role) => (
                <label key={role} className="flex items-center gap-1.5 text-xs bg-slate-50 border px-2 py-1 rounded cursor-pointer">
                  <input
                    type="checkbox"
                    checked={exclusions.includes(role)}
                    onChange={() => toggleRole(role, exclusions, setExclusions)}
                    disabled={loading}
                  />
                  <span>{role}</span>
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="text-slate-600 block mb-1 font-medium">Excluded User IDs (comma-separated):</label>
            <input
              type="text"
              className="w-full p-2 border border-slate-300 rounded-md font-mono"
              placeholder="e.g. bg-user-01, sys-admin-02"
              value={excludedUsersStr}
              onChange={(e) => {
                setExcludedUsersStr(e.target.value);
                setValidationResult(null);
              }}
              disabled={loading}
            />
          </div>
        </div>

        <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleValidate}
            loading={validating}
            disabled={loading || validating}
          >
            Validate Definition
          </Button>

          <div className="flex items-center gap-2">
            <Button type="button" variant="outline" size="sm" onClick={onClose} disabled={loading}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="sm" loading={loading}>
              {isEditing ? 'Save Changes' : 'Create Policy'}
            </Button>
          </div>
        </div>
      </form>
    </Modal>
  );
};
