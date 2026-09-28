# FlyRank AI — Usage Metering & Billing Engine

A small backend service for usage metering, quota enforcement, cost calculation, and Stripe test-mode subscription synchronization.

This project is the FlyRank AI Backend Engineering capstone. The system is being developed incrementally so that each stage has a working, testable checkpoint.

## Current Implementation Status

The project has completed:

* Stage 0 — Project Setup + Architecture Design
* Stage 1 — Database Foundation
* Stage 2 — Core API + Tenant Handling

Currently implemented:

* FastAPI application
* PostgreSQL database running through Docker Compose
* Environment-based application configuration
* Database connection layer
* Repository/data-access layer
* Tenant identification through `X-Tenant-Key`
* Tenant and subscription lookup
* Basic API health check
* Automated API tests
* Boundary validation for missing and unknown tenants

Not yet implemented:

* Usage metering
* Idempotency processing for billable actions
* Quota enforcement
* Cost calculation
* Stripe Checkout
* Stripe webhook processing
* Background worker
* Final usage reporting

These will be implemented in later stages.

---

## Capstone Scope

The final system is intentionally small.

The capstone requires:

* 2 plans: Free and Pro
* 2 usage types: API calls and AI tokens
* 1 dummy billable endpoint
* Usage events attributed to tenants
* Idempotency for billable requests
* Quota enforcement
* Cost calculation
* Stripe test-mode Checkout
* Verified and deduplicated Stripe webhooks
* Tenant isolation
* Real PostgreSQL persistence
* Background work
* Evidence for each completed requirement

The capstone explicitly keeps invoicing, proration, and overage billing outside the core scope.

AI token usage may be simulated; a real AI model call is not required.

---

## Architecture

The application follows a layered structure:

```text
Client
  │
  │ HTTP request
  ▼
FastAPI Routes
  │
  ▼
Dependencies / Validation
  │
  ▼
Repository Layer
  │
  ▼
PostgreSQL
```

Current tenant request flow:

```text
Client
  │
  │ X-Tenant-Key
  ▼
GET /tenants/me
  │
  ▼
Tenant Dependency
  │
  ▼
Tenant Repository
  │
  ├── tenants
  ├── subscriptions
  └── plans
```

The planned final metering flow is:

```text
Client
  │
  ▼
Billable API Request
  │
  ▼
Metering
  │
  ├── duplicate idempotency key?
  │       └── return original result
  │
  ├── quota check
  │
  ├── create usage event
  │
  └── calculate cost
  │
  ▼
Response
```

The planned Stripe flow is:

```text
Stripe Checkout
      │
      ▼
Stripe Subscription
      │
      │ signed webhook
      ▼
/webhooks/stripe
      │
      ├── verify signature
      ├── deduplicate event
      └── update subscription/plan
```

---

## Project Structure

```text
flyrank-capstone-metering-billing/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── db.py
│   ├── dependencies.py
│   │
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── tenant_repository.py
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   └── tenants.py
│   │
│   └── schemas/
│       ├── __init__.py
│       └── tenant.py
│
├── docs/
│   └── design.md
├── migrations/
│   └── 001_initial_schema.sql
├── scripts/
│   └── seed.py
├── tests/
│   └── test_tenants.py
├── worker/
│
├── .env.example
├── .gitignore
├── BUILDLOG.md
├── capstone.yaml
├── Dockerfile
├── docker-compose.yml
├── EVIDENCE.md
├── pytest.ini
├── README.md
└── requirements.txt
```

---

## Plans

The Free plan follows the capstone's specified limits:

| Plan | API calls/month | AI tokens/month |
| ---- | --------------: | --------------: |
| Free |           1,000 |         100,000 |
| Pro  |          10,000 |       1,000,000 |

The Pro limits are the implementation choices documented for this project.

---

## Database

PostgreSQL is used for persistent application data.

Current tables:

```text
tenants
plans
subscriptions
usage_events
stripe_events
```

The database is created from:

```text
migrations/001_initial_schema.sql
```

The database includes constraints and indexes for:

* tenant uniqueness
* plan uniqueness
* tenant/subscription relationships
* usage type validation
* positive usage quantities
* token validation
* tenant + idempotency-key uniqueness
* Stripe event uniqueness
* tenant usage queries

---

## Local Development

### Prerequisites

* Python
* Docker Desktop
* Git

The project uses a Python virtual environment.

### 1. Create/activate the virtual environment

From the project root:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Create `.env`

Copy `.env.example` to `.env` and use local development values.

The local PostgreSQL connection currently uses:

```env
DATABASE_URL=postgresql://capstone_user:change_me@localhost:5432/capstone_db
```

The real `.env` file is ignored by Git.

### 4. Start PostgreSQL

```powershell
docker compose up -d db
```

Check the database:

```powershell
docker compose ps
```

The PostgreSQL container should report a healthy status.

### 5. Seed the database

Because the seed script runs from the host while PostgreSQL is exposed on port `5432`, use:

```powershell
python scripts/seed.py --database-url "postgresql://capstone_user:change_me@localhost:5432/capstone_db"
```

The seed creates:

* Free plan
* Pro plan
* `tenant-001`
* `tenant-002`
* active Free subscriptions for both demo tenants

### 6. Start FastAPI

```powershell
uvicorn app.main:app --reload
```

The API is available at:

```text
http://127.0.0.1:8000
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

---

## Current API Endpoints

### Health

```http
GET /health
```

Example response:

```json
{
  "status": "ok",
  "database": "ok"
}
```

### Current Tenant

```http
GET /tenants/me
X-Tenant-Key: tenant-001
```

Example response:

```json
{
  "id": "tenant-uuid",
  "tenant_key": "tenant-001",
  "name": "Demo Tenant One",
  "status": "active",
  "plan_code": "free",
  "plan_name": "Free",
  "api_call_limit": 1000,
  "ai_token_limit": 100000
}
```

Current boundary behavior:

```text
Missing X-Tenant-Key → 400 Bad Request
Unknown tenant       → 404 Not Found
Known tenant         → 200 OK
```

---

## Testing

Run the automated test suite:

```powershell
pytest -q
```

The current Stage 2 suite covers:

* health endpoint
* tenant lookup
* missing tenant header
* unknown tenant

---

## Tenant Isolation

Tenant information is resolved using the `X-Tenant-Key` request header.

The application looks up the tenant in PostgreSQL and joins the tenant's subscription and plan.

Later billable operations will use the resolved tenant identity when creating and querying usage events.

The database also enforces tenant relationships through foreign keys and the usage-event idempotency constraint:

```text
UNIQUE (tenant_id, idempotency_key)
```

This is part of the foundation for tenant isolation and safe retry handling.

---

## Environment Variables

The project uses environment variables for configuration.

Required application configuration includes:

```text
APP_ENV
DATABASE_URL
STRIPE_SECRET_KEY
STRIPE_WEBHOOK_SECRET
STRIPE_PRO_PRICE_ID
```

Stripe values currently use placeholders during development because Stripe integration has not yet been implemented.

Real secrets must never be committed to Git.

---

## Development Roadmap

```text
Stage 0  Project setup + design                 DONE
Stage 1  Database foundation                    DONE
Stage 2  Core API + tenant handling             DONE
Stage 3  Usage metering + idempotency           NEXT
Stage 4  Quota enforcement
Stage 5  Cost calculation
Stage 6  Stripe Checkout
Stage 7  Stripe webhooks + subscription sync
Stage 8  Background worker
Stage 9  Testing + evidence
Stage 10 README + BUILDLOG + capstone.yaml
Stage 11 Final cleanup + GitHub submission
```

---

## Limitations

At the current stage:

* There is no billable `/generate` endpoint yet.
* Usage events are not yet created by the API.
* Idempotency handling for billable requests is not yet implemented.
* Quotas are not yet enforced by the API.
* Cost calculation is not yet implemented.
* Stripe Checkout is not yet implemented.
* Stripe webhook verification and synchronization are not yet implemented.
* The background worker is not yet implemented.
* Final `/usage` reporting is not yet implemented.

These limitations are intentional because the project is being built in stages.

---

## Documentation

* `docs/design.md` — architecture and design decisions
* `BUILDLOG.md` — development history, AI assistance, errors, and corrections
* `EVIDENCE.md` — implementation evidence and test proofs
* `capstone.yaml` — evaluator run/seed/test configuration

---

## Security Notes

* `.env` is ignored by Git.
* Stripe secrets are not committed.
* SQL queries use parameterized values.
* Tenant relationships are enforced by database foreign keys.
* Billable idempotency will be enforced using a tenant-scoped idempotency key.
* Stripe integration will use test mode only.

---

## Current Checkpoint

Stage 2 is complete when:

```text
FastAPI starts
PostgreSQL connection works
/health works
/tenants/me works
tenant validation works
automated tests pass
```

The next implementation stage is **Stage 3 — Usage Metering + Idempotency**.
