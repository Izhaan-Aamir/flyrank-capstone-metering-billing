# Usage Metering & Billing Engine

Backend capstone project for the FlyRank AI internship.

This project implements a small multi-tenant usage metering and billing backend using FastAPI and PostgreSQL. The system is being built incrementally according to the official capstone requirements.

## Current Status

**Stage 3 — Usage Metering + Idempotency**

Completed stages:

* Stage 0 — Project setup and architecture design
* Stage 1 — Database foundation
* Stage 2 — Core API and tenant handling
* Stage 3 — Usage metering and idempotency

Current functionality includes:

* PostgreSQL persistence
* Tenant identification through `X-Tenant-Key`
* Tenant information endpoint
* Health endpoint
* Simulated AI-token usage metering
* Required idempotency keys
* Tenant-scoped idempotency
* Duplicate-request protection
* Boundary validation for token usage
* Automated tests

Not implemented yet:

* Quota enforcement
* Cost calculation
* Monthly usage rollups
* Stripe Checkout
* Stripe webhook processing
* Background worker

These will be implemented in later stages.

---

## Project Goal

The capstone is a Usage Metering & Billing Engine.

The official project requires the backend to handle:

1. Usage metering
2. Quota enforcement
3. Cost calculation
4. Stripe subscription integration
5. Tenant isolation
6. Real persistence
7. Idempotency
8. Background processing
9. Evidence and documentation

The capstone intentionally uses simulated AI-token usage rather than calling a real AI model. This keeps the project focused on metering and billing behavior.

The official brief specifies two usage types:

* API calls
* AI tokens

The Free plan provides:

* 1,000 API calls/month
* 100,000 AI tokens/month

The Pro plan limits used by this implementation are:

* 10,000 API calls/month
* 1,000,000 AI tokens/month

The Pro values are implementation choices and are documented here as required.

---

## Technology Stack

* Python
* FastAPI
* PostgreSQL
* Docker
* Docker Compose
* psycopg
* Pydantic
* pytest
* HTTPX
* Git/GitHub
* Stripe Test Mode — planned
* Stripe CLI — planned

---

## Architecture

The application is being kept intentionally small and layered.

```text
Client
  │
  ▼
FastAPI HTTP Route
  │
  ▼
Dependency / Boundary Validation
  │
  ▼
Repository
  │
  ▼
PostgreSQL
```

The current usage path is:

```text
POST /generate
      │
      ▼
Identify tenant
      │
      ▼
Validate request
      │
      ▼
Validate Idempotency-Key
      │
      ▼
Check tenant + idempotency key
      │
      ├── Existing event ──► return existing result
      │
      └── New event ───────► create usage event
```

The planned final billing path is:

```text
Client
  │
  ▼
Billable API request
  │
  ▼
Metering
  │
  ▼
Quota Check
  │
  ├── rejected
  │
  └── allowed
        │
        ▼
   Cost Calculation
        │
        ▼
      Usage
```

Stripe will later provide the subscription/payment synchronization path.

---

## Project Structure

```text
flyrank-capstone-metering-billing/
│
├── app/
│   ├── main.py
│   ├── config.py
│   ├── db.py
│   ├── dependencies.py
│   │
│   ├── repositories/
│   │   ├── tenant_repository.py
│   │   └── usage_repository.py
│   │
│   ├── routes/
│   │   ├── tenants.py
│   │   └── usage.py
│   │
│   └── schemas/
│       ├── tenant.py
│       └── usage.py
│
├── docs/
│   └── design.md
│
├── migrations/
│   └── 001_initial_schema.sql
│
├── scripts/
│   └── seed.py
│
├── tests/
│   ├── test_tenants.py
│   └── test_usage.py
│
├── worker/
│
├── .env.example
├── .gitignore
├── BUILDLOG.md
├── capstone.yaml
├── docker-compose.yml
├── Dockerfile
├── EVIDENCE.md
├── pytest.ini
├── README.md
├── requirements.txt
└── ...
```

---

## Database

PostgreSQL runs through Docker Compose.

The current schema contains:

### `tenants`

Stores customer/tenant information.

Important fields include:

* `id`
* `tenant_key`
* `name`
* `created_at`

### `plans`

Stores plan definitions and quota limits.

Important fields include:

* `id`
* `code`
* `name`
* `api_call_limit`
* `ai_token_limit`
* `active`

### `subscriptions`

Connects each tenant to a plan.

Important fields include:

* `tenant_id`
* `plan_id`
* `status`
* `stripe_customer_id`
* `stripe_subscription_id`
* billing period fields

### `usage_events`

Stores billable usage.

Important fields include:

* `tenant_id`
* `usage_type`
* `quantity`
* `idempotency_key`
* `input_tokens`
* `cached_input_tokens`
* `output_tokens`
* `reasoning_tokens`
* timestamps

The database has a unique constraint on:

```text
(tenant_id, idempotency_key)
```

This is the database-level protection against duplicate metering.

### `stripe_events`

Reserved for Stripe webhook deduplication.

Stripe integration will be implemented in a later stage.

---

## Environment Variables

Create a local `.env` file.

Do not commit the real `.env` file.

Example:

```env
APP_ENV=development

POSTGRES_DB=capstone_db
POSTGRES_USER=capstone_user
POSTGRES_PASSWORD=change_me
DATABASE_URL=postgresql://capstone_user:change_me@localhost:5432/capstone_db

STRIPE_SECRET_KEY=sk_test_replace_me
STRIPE_WEBHOOK_SECRET=whsec_replace_me
STRIPE_PRO_PRICE_ID=price_replace_me
```

The repository contains `.env.example` with safe placeholder values.

---

## Running PostgreSQL

Start the database:

```powershell
docker compose up -d db
```

Check the container:

```powershell
docker compose ps
```

The PostgreSQL container should report a healthy status.

---

## Seeding the Database

The seed script creates:

* Free plan
* Pro plan
* Demo Tenant One
* Demo Tenant Two
* Free subscriptions for the demo tenants

From the activated Python virtual environment:

```powershell
python scripts/seed.py --database-url "postgresql://capstone_user:change_me@localhost:5432/capstone_db"
```

Expected result:

```text
Database seed completed successfully.
```

---

## Running the API

Activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Start FastAPI:

```powershell
uvicorn app.main:app --reload
```

The API runs at:

```text
http://127.0.0.1:8000
```

---

## API Endpoints

### Health

```http
GET /health
```

Example response:

```json
{
  "status": "ok"
}
```

---

### Current Tenant

```http
GET /tenants/me
```

Required header:

```text
X-Tenant-Key: tenant-001
```

Example response:

```json
{
  "id": "c7b4f338-d707-4383-a0dd-8fd3b809e1a9",
  "tenant_key": "tenant-001",
  "name": "Demo Tenant One",
  "status": "active",
  "plan_code": "free",
  "plan_name": "Free",
  "api_call_limit": 1000,
  "ai_token_limit": 100000
}
```

Missing tenant header returns:

```text
400 Bad Request
```

Unknown tenant returns:

```text
404 Not Found
```

---

## Simulated AI Usage

### Generate

```http
POST /generate
```

Required headers:

```text
X-Tenant-Key: tenant-001
Idempotency-Key: unique-request-key
```

Example request:

```json
{
  "input_tokens": 1000,
  "cached_input_tokens": 200,
  "output_tokens": 500,
  "reasoning_tokens": 100
}
```

The current metering quantity is:

```text
input_tokens
+
output_tokens
+
reasoning_tokens
=
1600
```

Cached input is stored separately because the later cost-calculation stage needs to price cached input differently.

Reasoning tokens are stored separately because the later cost-calculation stage must treat them according to the capstone's pricing rules.

No money calculation is performed yet.

No quota check is performed yet.

---

## Idempotency

Every billable request requires an `Idempotency-Key`.

The database enforces:

```text
UNIQUE (tenant_id, idempotency_key)
```

Therefore:

```text
Tenant A
+
key abc123
+
request
      ↓
one usage event
```

A retry using the same tenant and key:

```text
Tenant A
+
key abc123
+
same request
      ↓
existing usage event returned
```

No second usage event is created.

The idempotency key is tenant-scoped, so the same key can independently be used by different tenants.

For example:

```text
tenant-001 + abc123 → event A

tenant-002 + abc123 → event B
```

---

## Testing

Run the complete test suite:

```powershell
pytest -q
```

Current Stage 3 result:

```text
9 passed, 1 warning
```

The tests currently cover:

* Health endpoint
* Tenant lookup
* Missing tenant header
* Unknown tenant
* Normal usage event creation
* Duplicate idempotency requests
* Tenant-scoped idempotency
* Missing idempotency key
* Invalid token breakdown

The current HTTP test suite reports a Starlette/HTTPX deprecation warning. It does not cause the tests to fail.

---

## Stage 3 Idempotency Proof

A manual request was sent twice using:

```text
Tenant:
tenant-001

Idempotency-Key:
manual-stage3-proof
```

Both requests returned the same `usage_event_id`.

The database was then queried using:

```sql
SELECT
    tenant_id,
    usage_type,
    quantity,
    idempotency_key
FROM usage_events
WHERE idempotency_key = 'manual-stage3-proof';
```

The result contained exactly one row:

```text
tenant_id                              | usage_type | quantity | idempotency_key
---------------------------------------+------------+----------+--------------------
c7b4f338-d707-4383-a0dd-8fd3b809e1a9   | ai_tokens  | 1600     | manual-stage3-proof
```

This demonstrates that repeating the billable request with the same tenant and idempotency key did not create a duplicate usage event.

---

## Planned Next Stages

### Stage 4 — Quota Enforcement

Add:

* Current monthly usage calculation
* Requested usage calculation
* Plan-limit checks
* Boundary behavior
* `429 Too Many Requests`
* `402 Payment Required`

### Stage 5 — Cost Calculation

Add:

* API-call pricing
* AI-token pricing
* Cached-input pricing
* Reasoning-token handling
* Integer money units
* Pinned pricing constants

### Stage 6 — Stripe Checkout

Add:

* Stripe test-mode Checkout
* Pro subscription flow

### Stage 7 — Stripe Webhooks

Add:

* Signature verification
* Event deduplication
* Subscription synchronization
* Free → Pro plan updates

### Stage 8 — Background Worker

Add the required background processing with retry/failure handling.

### Stage 9 — Testing and Evidence

Expand automated tests and complete evidence for the remaining requirements.

### Stage 10 — Final Documentation

Finalize:

* README
* BUILDLOG
* EVIDENCE
* `capstone.yaml`

### Stage 11 — Final Cleanup

Perform a clean-machine-style verification and final GitHub submission review.

---

## Limitations at Current Stage

The current implementation is intentionally incomplete because the project is being built incrementally.

Currently:

* Quotas are not enforced.
* Costs are not calculated.
* `/usage` has not been implemented.
* Stripe Checkout has not been implemented.
* Stripe webhooks have not been implemented.
* Background processing has not been implemented.
* The simulated `/generate` endpoint records AI-token usage only.
* The current health endpoint reports application health but does not yet perform the database health response described in the later design.

These limitations will be removed or updated as later stages are completed.

---

## Security Notes

* Real secrets belong in `.env`.
* `.env` is ignored by Git.
* `.env.example` contains placeholders only.
* Stripe will use test mode only.
* Tenant IDs are resolved server-side from the request header and database.
* Usage events are always associated with a tenant.
* Idempotency is enforced per tenant.

---

## Documentation

* [Architecture & Design](docs/design.md)
* [Build Log](BUILDLOG.md)
* [Evidence](EVIDENCE.md)

---

## Git Checkpoints

The project is developed in staged Git checkpoints.

Current completed checkpoints:

```text
Stage 0 — Project setup and architecture design
Stage 1 — Database foundation
Stage 2 — Core API and tenant handling
Stage 3 — Usage metering and idempotency
```

Future stages will be committed separately.
