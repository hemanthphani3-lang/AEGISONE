import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import React from 'react';
import { PolicyDecision } from '@/types/policy';
import { DecisionCard } from '@/features/evaluation/components/DecisionCard';
import { RiskAssessmentCard } from '@/features/evaluation/components/RiskAssessmentCard';
import { SecuritySignalsPanel } from '@/features/evaluation/components/SecuritySignalsPanel';
import { PolicyTracePanel } from '@/features/evaluation/components/PolicyTracePanel';
import { TechnicalDetails } from '@/features/evaluation/components/TechnicalDetails';

describe('Evaluation UI Visualization Components', () => {
  it('renders DecisionCard for ALLOW decision', () => {
    render(
      <DecisionCard
        decision={PolicyDecision.ALLOW}
        reasons={['No restrictive policy matched.']}
      />
    );
    expect(screen.getByText(/Access Decision: ALLOW/i)).toBeInTheDocument();
    expect(screen.getByText(/No restrictive policy matched./i)).toBeInTheDocument();
  });

  it('renders DecisionCard for MFA_REQUIRED decision', () => {
    render(
      <DecisionCard
        decision={PolicyDecision.MFA_REQUIRED}
        reasons={["Policy 'admin-mfa' triggered decision: MFA_REQUIRED."]}
      />
    );
    expect(screen.getByText(/Access Decision: MFA_REQUIRED/i)).toBeInTheDocument();
  });

  it('renders DecisionCard for BLOCK decision', () => {
    render(
      <DecisionCard
        decision={PolicyDecision.BLOCK}
        reasons={["Policy 'block-legacy-auth' triggered decision: BLOCK."]}
      />
    );
    expect(screen.getByText(/Access Decision: BLOCK/i)).toBeInTheDocument();
  });

  it('renders RiskAssessmentCard with active factors', () => {
    render(
      <RiskAssessmentCard
        riskLevel="HIGH"
        riskFactors={['PrivilegedMfaMissingRule']}
        riskTrace="HIGH risk determined due to missing MFA for Admin"
      />
    );
    expect(screen.getAllByText(/HIGH RISK/i)[0]).toBeInTheDocument();
    expect(screen.getByText(/PrivilegedMfaMissingRule/i)).toBeInTheDocument();
  });

  it('renders SecuritySignalsPanel with UNKNOWN signal status handling', () => {
    const signals = [
      { name: 'auth.protocol', value: 'MODERN', source: 'LOCAL', status: 'AVAILABLE', confidence: 'HIGH' },
      { name: 'device.managed', value: null, source: 'LOCAL', status: 'UNKNOWN', confidence: 'MEDIUM' },
    ];
    render(<SecuritySignalsPanel signals={signals} />);
    expect(screen.getByText('auth.protocol')).toBeInTheDocument();
    expect(screen.getByText('device.managed')).toBeInTheDocument();
    expect(screen.getByText(/Signal Unavailable/i)).toBeInTheDocument();
    expect(screen.getByText('UNKNOWN')).toBeInTheDocument();
  });

  it('renders PolicyTracePanel with matched and unmatched policy items', () => {
    const traces = [
      {
        policy_id: 'admin-mfa',
        policy_name: 'Require MFA for Admins',
        enabled: true,
        matched: true,
        action: PolicyDecision.MFA_REQUIRED,
        target_roles: [],
        target_protocols: [],
      },
      {
        policy_id: 'block-legacy-auth',
        policy_name: 'Block Legacy Auth',
        enabled: true,
        matched: false,
        action: PolicyDecision.BLOCK,
        target_roles: [],
        target_protocols: [],
      },
    ];
    render(<PolicyTracePanel policyTraces={traces} />);
    expect(screen.getByText('Require MFA for Admins')).toBeInTheDocument();
    expect(screen.getByText('MATCHED')).toBeInTheDocument();
    expect(screen.getByText('NOT MATCHED')).toBeInTheDocument();
  });

  it('renders TechnicalDetails metadata and correlation ID', () => {
    render(
      <TechnicalDetails
        correlationId="test-correlation-12345"
        evaluatedAt="2026-09-26T20:00:00Z"
        matchedPolicies={['admin-mfa']}
      />
    );
    expect(screen.getByText(/Technical Evaluation Metadata/i)).toBeInTheDocument();
  });
});
