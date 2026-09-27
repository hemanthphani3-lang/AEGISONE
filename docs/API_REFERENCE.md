# AEGISONE — REST API REFERENCE

All endpoints require JWT Bearer Authentication header unless noted otherwise.

## 1. Authentication & System
- `POST /api/v1/auth/login`: Exchange OIDC authorization code for JWT tokens.
- `GET /health`: Public health check endpoint.

## 2. Policy Management
- `GET /api/v1/policies`: List policies with optional filtering.
- `POST /api/v1/policies`: Create a new policy rule.
- `GET /api/v1/policies/{id}`: Retrieve policy details by ID.
- `PUT /api/v1/policies/{id}`: Update an existing policy (requires `expected_version` header for OCC).
- `POST /api/v1/policies/{id}/toggle`: Enable or disable a policy.
- `GET /api/v1/policies/{id}/versions`: Fetch immutable version history for a policy.
- `POST /api/v1/policies/{id}/diff`: Compare two versions of a policy.
- `POST /api/v1/policies/{id}/rollback`: Rollback a policy to a target historical version.

## 3. Policy Evaluation & Simulation
- `POST /api/v1/policies/evaluate`: Evaluate an authentication request payload against active policies.
- `GET /api/v1/policies/evaluate/me`: Evaluate the current authenticated user context.
- `POST /api/v1/policies/simulate`: Dry-run simulation workspace (no state mutation).

## 4. Security Telemetry & Audit Logs
- `GET /api/v1/audit/logs`: Query sanitized security audit events with correlation ID filtering.

## 5. Policy Intelligence & Health Scoring
- `GET /api/v1/intelligence/analysis`: Run policy intelligence engines (shadowing, duplicate, conflict, lockout risk).

## 6. SOC Incident Management
- `GET /api/v1/incidents`: List security incidents.
- `POST /api/v1/incidents`: Create a new security incident.
- `GET /api/v1/incidents/{id}`: Get incident details with immutable event timeline.
- `POST /api/v1/incidents/{id}/assign`: Assign incident to an analyst.
- `POST /api/v1/incidents/{id}/status`: Transition incident state (`OPEN` $\rightarrow$ `ACKNOWLEDGED` $\rightarrow$ `INVESTIGATING` $\rightarrow$ `RESOLVED`).
- `POST /api/v1/incidents/{id}/remediate`: 1-click policy remediation from SOC console.
