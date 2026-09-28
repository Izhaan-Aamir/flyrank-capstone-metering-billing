# Build Log

This file records the development process, including AI assistance, implementation decisions, errors, corrections, and verification.

The official capstone specifically asks for an honest AI-usage log describing where AI helped, where it was wrong, and what was changed.

---

# Stage 0 — Project Setup & Design

## Date

2026-09-28

## Goal

Set up the separate capstone repository and design the Usage Metering & Billing Engine before implementing the main application.

## AI Assistance

AI assistance was used to:

* Analyze the official capstone requirements.
* Break the project into implementation stages.
* Propose the initial architecture.
* Identify the required database entities.
* Plan tenant isolation.
* Plan usage metering.
* Explain idempotency.
* Identify quota requirements.
* Identify pricing requirements.
* Plan Stripe Checkout and webhook synchronization.
* Plan the required evidence.
* Draft the initial documentation structure.

## Design Decisions

The project uses:

* Python
* FastAPI
* PostgreSQL
* Docker
* Docker Compose
* pytest
* Stripe test mode for the future payment stages

The selected plans are:

```text
Free
1,000 API calls/month
100,000 AI tokens/month

Pro
10,000 API calls/month
1,000,000 AI tokens/month
```

The Pro values are implementation choices.

Tenant identification was designed around:

```text
X-Tenant-Key
```

The initial database model contains:

```text
tenants
plans
subscriptions
usage_events
stripe_events
```

## Verification

The design was reviewed against the official capstone brief before implementation.

## Changes

No major application/business logic was implemented during the initial design stage.

---

# Stage 1 — Database Foundation

## Date

2026-09-28

## Goal

Create the PostgreSQL foundation required by the capstone.

## AI Assistance

AI assistance was used to:

* Translate the design into PostgreSQL tables.
* Explain foreign keys and tenant isolation.
* Design usage-event constraints.
* Design the idempotency uniqueness constraint.
* Create the initial migration.
* Create the seed script.
* Explain Docker Compose database setup.
* Suggest verification commands.

## Implementation

Created:

```text
migrations/001_initial_schema.sql
scripts/seed.py
docker-compose.yml
```

The database contains:

```text
tenants
plans
subscriptions
usage_events
stripe_events
```

The usage-event table includes:

```sql
UNIQUE (tenant_id, idempotency_key)
```

It also validates:

* positive quantities
* allowed usage types
* non-negative token values
* cached input not exceeding input

## Docker Issue

Initially, Docker commands could not connect because the Docker engine was not running.

### Problem

Docker Desktop had not been started.

### Correction

Docker Desktop was started.

The Docker engine then became available through the `desktop-linux` context.

### Verification

The PostgreSQL container started successfully:

```powershell
docker compose up -d db
```

The container became healthy.

---

## Database Verification

The database tables were inspected using:

```powershell
docker compose exec db psql -U capstone_user -d capstone_db -c "\dt"
```

The required tables were present.

Indexes and constraints were also inspected.

---

## Seed Verification

The seed script created:

```text
free
pro
```

and:

```text
tenant-001
tenant-002
```

Both demo tenants were initially assigned the Free plan.

The seed operation completed successfully.

---

# Stage 2 — Core API & Tenant Handling

## Date

2026-09-28

## Goal

Add the initial FastAPI application and tenant-aware HTTP layer.

## AI Assistance

AI assistance was used to:

* Design the initial FastAPI application structure.
* Separate configuration, dependencies, repositories, routes, and schemas.
* Implement tenant lookup.
* Implement the `/health` endpoint.
* Implement `/tenants/me`.
* Create initial tests.
* Diagnose test and configuration errors.

## Architecture

The Stage 2 application structure became:

```text
app/
├── main.py
├── config.py
├── db.py
├── dependencies.py
├── repositories/
│   └── tenant_repository.py
├── routes/
│   └── tenants.py
└── schemas/
    └── tenant.py
```

The tenant lookup path is:

```text
HTTP request
    ↓
X-Tenant-Key
    ↓
get_current_tenant
    ↓
tenant_repository
    ↓
PostgreSQL
```

---

## Application Startup Error

### Problem

The first attempt to start FastAPI produced a Pydantic settings error:

```text
ValidationError
database_url
Field required
```

### Cause

The local `.env` file did not exist.

### Correction

A local `.env` file was created with the required development database configuration.

The real `.env` remains ignored by Git.

---

## Health Verification

After the environment configuration was corrected:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

returned:

```text
status
------
ok
```

---

## Tenant Verification

The endpoint:

```http
GET /tenants/me
```

was tested using:

```text
X-Tenant-Key: tenant-001
```

The response correctly identified:

```text
tenant-001
Demo Tenant One
Free
active
```

and returned the expected limits:

```text
API calls: 1000
AI tokens: 100000
```

---

## Initial Test Error

### Problem

The first pytest run failed with:

```text
ModuleNotFoundError: No module named 'app'
```

### Correction

Added:

```ini
[pytest]
pythonpath = .
```

to:

```text
pytest.ini
```

### Verification

The test suite then passed:

```text
4 passed
```

The installed test stack also produced a Starlette/HTTPX deprecation warning. Since the tests were passing, the dependency stack was not changed just to remove the warning.

---

# Stage 3 — Usage Metering & Idempotency

## Date

2026-09-28

## Goal

Implement the first billable endpoint and ensure that retries cannot create duplicate usage events.

The official capstone requires a billable action to create exactly one usage event even under retries, with deduplication by idempotency key.

---

## AI Assistance

AI assistance was used to:

* Explain the idempotency requirement.
* Design the simulated `/generate` endpoint.
* Design request validation.
* Design the usage repository.
* Use the existing database uniqueness constraint.
* Implement duplicate-event handling.
* Create automated tests.
* Explain how to prove exactly-once behavior using PostgreSQL.

---

## Implementation

Added:

```text
app/schemas/usage.py
app/repositories/usage_repository.py
app/routes/usage.py
tests/test_usage.py
```

Updated:

```text
app/main.py
```

The new endpoint is:

```http
POST /generate
```

It accepts simulated AI-token usage:

```json
{
  "input_tokens": 1000,
  "cached_input_tokens": 200,
  "output_tokens": 500,
  "reasoning_tokens": 100
}
```

The metered quantity is:

```text
1000 + 500 + 100 = 1600
```

Cached input is stored separately because it will have separate pricing behavior later.

---

## Idempotency Implementation

The database already contains:

```sql
UNIQUE (tenant_id, idempotency_key)
```

The repository uses:

```sql
ON CONFLICT (tenant_id, idempotency_key)
DO NOTHING
```

When a request uses a new key:

```text
request
  ↓
INSERT succeeds
  ↓
usage event created
  ↓
return event
```

When the same tenant retries with the same key:

```text
request
  ↓
INSERT conflicts
  ↓
DO NOTHING
  ↓
SELECT existing event
  ↓
return existing event
```

Therefore:

```text
two requests
     ↓
one usage event
```

---

## Stage 3 Automated Tests

The following tests were added:

```text
test_generate_creates_usage_event
test_same_idempotency_key_returns_same_event
test_idempotency_key_is_scoped_to_tenant
test_missing_idempotency_key
test_invalid_token_breakdown
```

The full suite was then run.

Result:

```text
.........                                                 [100%]

9 passed, 1 warning
```

The warning was the same Starlette/HTTPX deprecation warning seen previously.

No test failures remained.

---

## Manual Testing Issue

### Problem

The first attempt to perform the manual idempotency test returned:

```text
Invoke-RestMethod : Unable to connect to the remote server
```

### Cause

The FastAPI development server was not running.

The test suite itself did not require Uvicorn to be running because it uses FastAPI's test client, but the manual HTTP request requires a live server.

### Correction

Uvicorn was started with:

```powershell
uvicorn app.main:app --reload
```

The manual requests were then repeated.

---

## Manual Idempotency Verification

The same request was sent twice with:

```text
X-Tenant-Key: tenant-001
Idempotency-Key: manual-stage3-proof
```

Both responses returned the exact same:

```text
usage_event_id
```

This showed that the second request returned the existing usage event.

---

## Database Verification

The database was queried with:

```sql
SELECT
    tenant_id,
    usage_type,
    quantity,
    idempotency_key
FROM usage_events
WHERE idempotency_key = 'manual-stage3-proof';
```

Result:

```text
              tenant_id               | usage_type | quantity |   idempotency_key
--------------------------------------+------------+----------+---------------------
 c7b4f338-d707-4383-a0dd-8fd3b809e1a9 | ai_tokens  |     1600 | manual-stage3-proof
(1 row)
```

The database therefore contained exactly one usage event for the repeated request.

This is the primary manual evidence for the Stage 3 exactly-once metering requirement.

---

## Current Stage 3 Result

Completed:

```text
✓ Billable /generate endpoint
✓ Simulated AI-token usage
✓ Idempotency-Key requirement
✓ Tenant-scoped idempotency
✓ Database-level duplicate protection
✓ Duplicate request returns existing event
✓ Token boundary validation
✓ Automated tests
✓ Manual database proof
```

Not yet implemented:

```text
○ Quota enforcement
○ Cost calculation
○ GET /usage
○ Stripe Checkout
○ Stripe webhooks
○ Background worker
```

These belong to later stages.

---

# Development Principle

The project is being implemented incrementally.

Each stage is tested before moving forward, and documentation is updated to describe only functionality that has actually been implemented and verified.

Future requirements will not be marked complete until corresponding implementation and evidence exist.
