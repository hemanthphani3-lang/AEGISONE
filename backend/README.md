# AegisOne - Backend (Iteration 12)

AegisOne is a zero-cost Conditional Access Policy Lab / Simulator designed to simulate, test, and audit zero-trust security policies and conditional access evaluation.

> **Important Architecture Principle**: Simulation never modifies real identity, policy, authentication, database state, or security evaluation history.

---

## Architecture Overview (Iteration 12)

```
                 Keycloak
                    │
                    ▼
              Authentication
                    │
                    ▼
               Authorization
                    │
                    ▼
             Real SecurityContext
                    │
                    ▼
            ┌───────────────┐
            │   Simulation  │
            │    Overlay    │
            └───────┬───────┘
                    │
                    ▼
          Simulated SecurityContext
                    │
             ┌──────┴──────┐
             ▼             ▼
       RiskEvaluator   PolicyEvaluator
             │             │
             ▼             │
      RiskAssessment       │
             │             │
             └──────┬──────┘
                    ▼
            SimulationResult
                    │
                    ▼
                 Response
```

---

## Policy Simulation & What-If Evaluation (Iteration 12)

### Core Capabilities
- **What-If Analysis**: Authorized users can evaluate hypothetical context changes (e.g. "What if MFA becomes complete?", "What if protocol changes to MODERN?", "What if risk becomes HIGH?") without altering production state.
- **Zero-Side-Effect Guarantee**: Base security context is deep-cloned before applying overrides. Simulation never mutates PostgreSQL policies, Keycloak identity, user roles, MFA status, or production audit trails.
- **Recomputed Simulated Risk**: When signals influencing risk (e.g., MFA completion or auth protocol) are overridden, `RiskEvaluator` dynamically recalculates the simulated `RiskAssessment`.
- **Explainability**: Reports `base_decision`, `simulated_decision`, `decision_changed`, `base_risk`, `simulated_risk`, `risk_changed`, policy match diffs (`matched -> not_matched` / `not_matched -> matched`), and structured non-LLM text explanations.

### Supported Simulation Overrides (`SimulationOverrides`)
- `roles`: `list[UserRole]`
- `auth_protocol`: `AuthProtocol` (`MODERN`, `LEGACY`)
- `mfa_completed`: `bool`
- `device_compliant`: `bool`
- `device_managed`: `bool`
- `location`: `str`
- `network_type`: `str`
- `risk_level`: `RiskLevel` (`LOW`, `MEDIUM`, `HIGH`, `UNKNOWN`)

### Authorization & Security Boundaries
- **Access Control**: Simulation endpoints require `ADMIN` or `SECURITY_ADMIN` role.
- **Denial**: `STAFF`, `STUDENT`, `BREAK_GLASS` (alone), or unauthenticated callers receive `403 Forbidden` / `401 Unauthorized`.
- **Authorization Boundary**: Authorization occurs *before* simulation. Caller roles determine permission to simulate; simulated roles in payload apply exclusively to hypothetical context evaluation.
- **Input Validation**: Unknown override fields and arbitrary user impersonation attempts are rejected (`HTTP 422`).

---

## Normalized Security Signal & Risk Abstraction

### Key Abstractions
- **`SecuritySignal`**: Normalized security input with `name`, `value`, `source`, `status`, `confidence`, `timestamp`, and `metadata`.
- **`SecurityContext`**: Map of normalized signals evaluated against policies.
- **`RiskEvaluator`**: Deterministic risk scoring engine deriving `LOW`, `MEDIUM`, `HIGH`, or `UNKNOWN` risk levels from trusted signals (`PrivilegedMfaMissingRule`, `LegacyAuthenticationRule`, `UnknownAuthStateRule`, `MockDeviceUnknownRule`).
- **`ConditionRegistry`**: Pluggable registry mapping condition keys to evaluators (`RoleConditionEvaluator`, `AuthProtocolConditionEvaluator`, `MfaConditionEvaluator`, `RiskConditionEvaluator`, etc.).

---

## Controlled Audit Event System & Decision Traceability

- **Event Types**: `AUTHENTICATION_SUCCESS`, `AUTHENTICATION_FAILURE`, `AUTHORIZATION_DENIED`, `POLICY_CREATED`, `POLICY_UPDATED`, `POLICY_ENABLED`, `POLICY_DISABLED`, `POLICY_DELETED`, `POLICY_EVALUATED`, `POLICY_SIMULATED`.
- **Precedence**: `BLOCK` > `MFA_REQUIRED` > `ALLOW`.
- **Data Sanitization**: Secrets, access tokens, refresh tokens, passwords, API keys, and authorization headers are strictly redacted (`[REDACTED]`).

---

## Available API Endpoints

1. `GET /api/v1/health`
2. `GET /api/v1/policies`
3. `GET /api/v1/policies/{policy_id}`
4. `POST /api/v1/policies`
5. `PATCH /api/v1/policies/{policy_id}`
6. `DELETE /api/v1/policies/{policy_id}`
7. `POST /api/v1/evaluate`
8. `GET /api/v1/auth/me`
9. `POST /api/v1/evaluate/me`
10. `GET /api/v1/audit/events`
11. `POST /api/v1/simulate/evaluate/me`
12. `POST /api/v1/simulate/evaluate`

---

## Database Migrations & Environment Setup

Create `.env` using `.env.example`:

```env
APP_ENV=development
KEYCLOAK_URL=https://aegisone-keycloak.onrender.com
KEYCLOAK_REALM=accessguard
KEYCLOAK_CLIENT_ID=accessguard-backend
DATABASE_URL=postgresql+asyncpg://accessguard:accessguard_pass@localhost:5432/accessguard_db
KEYCLOAK_CLIENT_SECRET=accessguard-secret-dev
```

Run database migrations:

```bash
alembic upgrade head
```

---

## Running Tests

Run the complete test suite:

```bash
pytest
```
ET /api/v1/audit/events`

---

## Database Migrations & Environment Setup

Create `.env` using `.env.example`:

```env
APP_ENV=development
KEYCLOAK_URL=https://aegisone-keycloak.onrender.com
KEYCLOAK_REALM=accessguard
KEYCLOAK_CLIENT_ID=accessguard-backend
DATABASE_URL=postgresql+asyncpg://accessguard:accessguard_pass@localhost:5432/accessguard_db
KEYCLOAK_CLIENT_SECRET=accessguard-secret-dev
```

Run database migrations:

```bash
alembic upgrade head
```

---

## Running Tests

Run the complete test suite:

```bash
pytest
```


