# AEGISONE — END-TO-END DEMO GUIDE

Follow this step-by-step workflow for a complete demonstration of AegisOne capabilities:

1. **Login**: Authenticate through Keycloak OIDC PKCE flow into the AegisOne Portal.
2. **Dashboard**: Inspect the security posture dashboard, active policy count, and risk health score.
3. **Signal Table**: View the Evaluated Security Signals table demonstrating explicit `AVAILABLE` vs `UNAVAILABLE` statuses for location and device posture.
4. **Policy Management**: Navigate to Policy Management to view active and disabled rules.
5. **Create Policy**: Click "Create Policy" and create an admin MFA policy ("Require MFA for Admins").
6. **Validation**: Test input validation with invalid conditions (e.g. empty target roles) to demonstrate error prevention.
7. **Evaluate Request**: Execute a real-time policy evaluation request for an `ADMIN` user logging in without MFA.
8. **Verify MFA Precedence**: Observe the decision returning `MFA_REQUIRED`.
9. **Email OTP Challenge**: Trigger Email OTP dispatch (`POST /api/v1/auth/mfa/send-otp`) and verify the 6-digit OTP code to upgrade session state (`auth.mfa_completed = true`).
10. **Re-evaluate Request**: Re-evaluate access and verify decision transitions to `ALLOW`.
11. **User Directory**: Navigate to User Directory (`/users`) to view Keycloak realm users, create a user account, and assign RBAC roles.
12. **What-If Simulation**: Navigate to the Simulation Workspace and run dry-run tests without mutating live database state.
13. **Policy Intelligence**: Run Policy Intelligence analysis to detect broad rules or lockout risks.
14. **SOC Incident**: View auto-generated security incidents triggered by policy intelligence findings.
15. **Remediate Policy**: Execute 1-click remediation ("Disable Risky Policy") directly from the SOC Incident Console.
16. **Version History & Rollback**: Compare Policy Diff versions and execute 1-click Rollback.
