# Usage Metering & Billing Engine

Backend capstone project for the FlyRank AI internship.

This project implements a small multi-tenant usage metering and billing backend using **FastAPI, PostgreSQL, Docker, and Stripe Test Mode**.

The implementation follows the official capstone requirements and was developed incrementally through separate Git checkpoints.

The system covers:

* Usage metering
* Tenant isolation
* Monthly quota enforcement
* Idempotency
* Integer-based cost calculation
* Stripe Test Mode Checkout
* Stripe webhook verification
* Stripe event deduplication
* Subscription synchronization
* PostgreSQL persistence
* Background job processing
* Automated testing
* Reproducible evidence and documentation

AI usage is simulated. The application does not call a real AI model.

---

# Project Status

The main implementation stages are complete through Stage 9.

```text
Stage 0 — Project Setup & Design                 ✓
Stage 1 — Database Foundation                   ✓
Stage 2 — Core API & Tenant Handling            ✓
Stage 3 — Usage Metering & Idempotency          ✓
Stage 4 — Quota Enforcement                     ✓
Stage 5 — Cost Calculation                      ✓
Stage 6 — Stripe Checkout                       ✓
Stage 7 — Stripe Webhooks & Subscription Sync   ✓
Stage 8 — Background Worker                    ✓
Stage 9 — Testing & Evidence                    ✓
Stage 10 — Final Documentation                  ✓
Stage 11 — Final Cleanup & Submission           pending
```

Current automated test result:

```text
23 passed, 1 warning
```

The warning is an existing Starlette/HTTPX deprecation warning from the installed testing stack. It does not cause test failures.

---

# Project Goal

The capstone is a **Usage Metering & Billing Engine** for a small multi-tenant application.

The system is designed around two usage types:

```text
api_calls
ai_tokens
```

The main requirements are:

1. Usage metering
2. Quota enforcement
3. Cost calculation
4. Stripe subscription integration
5. Tenant isolation
6. Real PostgreSQL persistence
7. Idempotency
8. Background processing
9. Testing and evidence
10. Reproducible documentation

The project intentionally uses simulated AI-token usage instead of calling an external AI model. This keeps the implementation focused on metering and billing behavior.

---

# Plans

## Free Plan

```text
API calls:  1,000/month
AI tokens:  100,000/month
```

## Pro Plan

```text
API calls:  10,000/month
AI tokens: 1,000,000/month
```

The Free limits come from the official capstone requirements.

The Pro limits are implementation choices selected for this project.

---

# Technology Stack

* Python
* FastAPI
* PostgreSQL
* Docker
* Docker Compose
* psycopg
* Pydantic
* pytest
* HTTPX
* Stripe Test Mode
* Stripe CLI
* Git
* GitHub

---

# Architecture

The application follows a small layered architecture.

```text
Client
  |
  v
FastAPI Route
  |
  v
Dependency / Boundary Validation
  |
  v
Service Layer
  |
  v
Repository / Data Access
  |
  v
PostgreSQL
```

The project intentionally avoids unnecessary complexity while keeping HTTP handling, business logic, and database access separated.

---

# Project Structure

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
│   │   ├── quota_repository.py
│   │   ├── stripe_event_repository.py
│   │   ├── subscription_repository.py
│   │   ├── tenant_repository.py
│   │   └── usage_repository.py
│   │
│   ├── routes/
│   │   ├── checkout.py
│   │   ├── tenants.py
│   │   ├── usage.py
│   │   └── webhooks.py
│   │
│   ├── schemas/
│   │   ├── tenant.py
│   │   └── usage.py
│   │
│   └── services/
│       ├── pricing_service.py
│       ├── quota_service.py
│       ├── stripe_service.py
│       └── subscription_service.py
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
│   ├── test_pricing.py
│   ├── test_tenants.py
│   ├── test_usage.py
│   ├── test_webhooks.py
│   └── test_worker.py
│
├── worker/
│   ├── __init__.py
│   ├── jobs.py
│   └── worker.py
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
└── requirements.txt
```

---

# Database

PostgreSQL runs through Docker Compose.

The main tables are:

```text
tenants
plans
subscriptions
usage_events
stripe_events
```

## `tenants`

Stores tenant/customer information.

Important fields include:

* `id`
* `tenant_key`
* `name`
* `created_at`

Each tenant has its own subscription and usage records.

## `plans`

Stores plan definitions and quota limits.

Important fields include:

* `id`
* `code`
* `name`
* `api_call_limit`
* `ai_token_limit`
* `active`

## `subscriptions`

Connects a tenant to its current plan and Stripe subscription state.

Important fields include:

* `tenant_id`
* `plan_id`
* `status`
* `stripe_customer_id`
* `stripe_subscription_id`
* `current_period_start`
* `current_period_end`

Each tenant has one subscription.

## `usage_events`

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
* `occurred_at`
* `created_at`

The database enforces:

```sql
UNIQUE (tenant_id, idempotency_key)
```

This provides database-level protection against duplicate metering.

## `stripe_events`

Stores processed Stripe event IDs.

The unique Stripe event ID allows webhook processing to be safely deduplicated.

---

# Database Constraints and Indexes

The schema includes protections for:

* Unique tenant keys
* Unique plan codes
* One subscription per tenant
* Unique Stripe customer IDs
* Unique Stripe subscription IDs
* Valid subscription statuses
* Valid usage types
* Positive usage quantities
* Non-negative token values
* Cached input not exceeding total input
* Unique `(tenant_id, idempotency_key)`
* Unique Stripe event IDs

Indexes are provided for:

```text
subscriptions.plan_id
usage_events(tenant_id, occurred_at)
usage_events(tenant_id, usage_type, occurred_at)
stripe_events.event_type
```

These support tenant-scoped usage and subscription/event queries.

---

# Environment Configuration

Create a local `.env` file.

The real `.env` file must never be committed.

`.env.example` contains safe placeholders:

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

Real Stripe credentials and webhook secrets remain local.

---

# Running the Project

## 1. Start PostgreSQL

From the repository root:

```powershell
docker compose up -d db
```

Check the database container:

```powershell
docker compose ps
```

PostgreSQL should report a healthy status.

---

## 2. Activate the Python Virtual Environment

```powershell
.\.venv\Scripts\Activate.ps1
```

---

## 3. Seed the Database

Run:

```powershell
python scripts/seed.py --database-url "postgresql://capstone_user:change_me@localhost:5432/capstone_db"
```

The seed creates:

* Free plan
* Pro plan
* Demo Tenant One
* Demo Tenant Two
* Initial Free subscriptions

Expected output:

```text
Database seed completed successfully.
```

---

## 4. Start FastAPI

```powershell
uvicorn app.main:app --reload
```

The API is available at:

```text
http://127.0.0.1:8000
```

---

# API Endpoints

| Method | Endpoint           | Purpose                            |
| ------ | ------------------ | ---------------------------------- |
| `GET`  | `/health`          | Application health check           |
| `GET`  | `/tenants/me`      | Return the current tenant          |
| `POST` | `/generate`        | Record simulated AI-token usage    |
| `POST` | `/checkout/pro`    | Create Pro Stripe Checkout session |
| `POST` | `/webhooks/stripe` | Process verified Stripe events     |

---

# Tenant Handling

Tenant identification uses:

```text
X-Tenant-Key
```

Example:

```text
X-Tenant-Key: tenant-001
```

## Current Tenant

```http
GET /tenants/me
```

Example response:

```json
{
  "tenant_key": "tenant-001",
  "name": "Demo Tenant One",
  "status": "active",
  "plan_code": "free",
  "plan_name": "Free",
  "api_call_limit": 1000,
  "ai_token_limit": 100000
}
```

A missing tenant header returns:

```text
400 Bad Request
```

An unknown tenant returns:

```text
404 Not Found
```

---

# Stage 3 — Usage Metering & Idempotency

The main billable endpoint is:

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

The metered quantity is:

```text
input_tokens + output_tokens + reasoning_tokens
```

For the example:

```text
1000 + 500 + 100 = 1600
```

Cached input is stored separately for pricing and is not added a second time to the usage quantity.

## Idempotency

The database enforces:

```sql
UNIQUE (tenant_id, idempotency_key)
```

A new request:

```text
Request
   |
   v
Create usage event
   |
   v
Return result
```

A retry using the same tenant and idempotency key:

```text
Retry
   |
   v
Existing event
   |
   v
Return existing result
```

Therefore:

```text
2 requests
    |
    v
1 usage event
```

The idempotency key is tenant-scoped.

For example:

```text
tenant-001 + abc123 → event A
tenant-002 + abc123 → event B
```

The same key can therefore be independently used by different tenants.

---

# Stage 4 — Quota Enforcement

Before creating a new AI-token usage event, the application checks the tenant's current monthly usage.

The decision is based on:

```text
current monthly usage + requested usage
```

compared with the tenant's plan limit.

If the request would exceed the limit, the API returns:

```text
429 Too Many Requests
```

with:

```json
{
  "detail": "AI token quota exceeded."
}
```

The rejected request does not create a usage event.

The automated tests cover:

* Usage below the limit
* Usage exactly at the limit
* Usage above the limit
* Rejected requests not creating events

The current implementation does not return `402 Payment Required` for quota exhaustion. That behavior is not implemented.

---

# Stage 5 — Cost Calculation

Cost calculation is implemented using integer micro-units.

No floating-point money calculation is used.

Current pricing constants:

| Usage         |                             Price |
| ------------- | --------------------------------: |
| Regular input | 1,000,000 micro-units / 1M tokens |
| Cached input  |   250,000 micro-units / 1M tokens |
| Output        | 2,000,000 micro-units / 1M tokens |
| Reasoning     | 2,000,000 micro-units / 1M tokens |

The calculation separates regular input from cached input:

```text
regular_input_tokens =
    input_tokens - cached_input_tokens
```

Cached input therefore receives its lower price without being double-counted.

Reasoning tokens are charged at the same rate as output tokens.

The API response includes:

```text
cost_micro_units
```

The pricing tests cover:

* Basic cost calculation
* Cached-input pricing
* No double charging of cached input
* Reasoning-token pricing
* Zero cached input

---

# Stage 6 — Stripe Checkout

Stripe Test Mode is used for the Pro subscription flow.

The endpoint is:

```http
POST /checkout/pro
```

The backend creates a Stripe Checkout Session configured for a subscription.

The Pro Stripe Price ID is loaded from environment configuration:

```text
STRIPE_PRO_PRICE_ID
```

The tenant ID is stored in Stripe metadata so that the resulting webhook can identify the tenant.

The response contains:

```json
{
  "checkout_url": "...",
  "session_id": "..."
}
```

Real Stripe secret keys are never stored in source code.

---

# Stage 7 — Stripe Webhooks & Subscription Synchronization

Stripe sends subscription events to:

```http
POST /webhooks/stripe
```

Supported event types:

```text
checkout.session.completed
customer.subscription.updated
customer.subscription.deleted
```

## Signature Verification

The endpoint requires:

```text
Stripe-Signature
```

The payload is verified using the Stripe webhook signing secret.

Missing or invalid signatures return:

```text
400 Bad Request
```

The application does not process an unverified Stripe event.

## Event Deduplication

Processed Stripe event IDs are stored in:

```text
stripe_events
```

The database enforces:

```sql
UNIQUE (stripe_event_id)
```

If the same event is received again, the application returns a duplicate response instead of processing the event again.

## Subscription Synchronization

Verified Stripe events update the local subscription record.

The local database mirrors:

* Stripe customer ID
* Stripe subscription ID
* Plan
* Subscription status
* Current billing period

Stripe remains the source of truth for subscription state.

The database stores the verified mirrored state needed by the application.

---

# Stripe Local Development

After configuring Stripe Test Mode:

```powershell
stripe login
```

Start the webhook listener:

```powershell
stripe listen --events checkout.session.completed,customer.subscription.updated,customer.subscription.deleted --forward-to localhost:8000/webhooks/stripe
```

Stripe CLI prints a webhook signing secret.

That value belongs only in the local `.env`:

```env
STRIPE_WEBHOOK_SECRET=whsec_...
```

It must never be committed.

---

# Stage 8 — Background Worker

The project includes a small background worker implementation.

The worker contains:

```text
worker/jobs.py
worker/worker.py
```

A job is represented by:

```text
BillingJob
```

The worker currently supports the job type:

```text
finalize_usage
```

The basic processing flow is:

```text
BillingJob
    |
    v
Queue
    |
    v
BillingWorker
    |
    v
Process job
```

The worker tests verify:

* A `finalize_usage` job is processed successfully.
* Unknown job types are rejected.

This worker is intentionally minimal and in-memory. It is not intended to represent a production distributed job queue.

---

# Stage 9 — Testing

The project uses pytest.

Run all tests:

```powershell
pytest -q
```

Current result:

```text
23 passed, 1 warning
```

Test coverage includes:

### Tenant Tests

* Health endpoint
* Tenant lookup
* Missing tenant header
* Unknown tenant

### Usage Tests

* Usage event creation
* Same idempotency key returns the same event
* Idempotency scoped to tenant
* Missing idempotency key
* Invalid token breakdown
* Quota below limit
* Quota at limit
* Quota above limit
* Rejected quota request does not create an event

### Pricing Tests

* Basic pricing
* Cached-input pricing
* Cached input not double-counted
* Reasoning pricing

### Stripe Webhook Tests

* Missing signature
* Invalid signature
* Duplicate Stripe event
* Valid checkout event dispatch

### Worker Tests

* Successful `finalize_usage` job
* Unknown job rejection

---

# Stage 10 — Evidence

The capstone evidence is maintained in:

```text
EVIDENCE.md
```

Evidence includes:

* Database schema verification
* Seed verification
* Tenant isolation verification
* Usage metering tests
* Exactly-once idempotency proof
* Quota boundary tests
* Pricing tests
* Stripe webhook tests
* Stripe Test Mode verification
* Webhook deduplication
* Background worker tests
* Full test-suite results

The evidence document is intended to provide reproducible proof rather than unsupported claims.

---

# Security

The project follows these security practices:

* Real secrets are stored in `.env`.
* `.env` is excluded from Git.
* `.env.example` contains placeholders only.
* Stripe Test Mode is used.
* Stripe webhook signatures are verified.
* Tenant records are resolved server-side.
* Usage events are associated with tenant IDs.
* Idempotency is tenant-scoped.
* Database constraints provide duplicate protection.
* Stripe event IDs are deduplicated at the database level.

---

# Limitations

The following are intentionally documented limitations of the current implementation:

## Usage Rollup Endpoint

A dedicated:

```http
GET /usage
```

endpoint is not implemented.

Usage data can be queried from the PostgreSQL `usage_events` table and is used internally for quota enforcement.

## API-Call Metering

The database model supports:

```text
api_calls
```

but the primary billable demonstration endpoint currently records simulated AI-token usage.

## Payment-Required Quota Response

Quota exhaustion currently returns:

```text
429 Too Many Requests
```

The `402 Payment Required` upgrade flow is not implemented.

## Background Worker

The worker is a minimal in-memory implementation.

It demonstrates job submission and processing but is not a production distributed queue.

Production-grade retry infrastructure, persistent job storage, and external alerting are outside the current implementation.

## Billing Scope

The project intentionally does not implement:

* Invoicing
* Proration
* Overage billing
* Real payment capture outside Stripe Test Mode
* Real AI model execution

These are outside the intended core scope.

---

# Documentation

Additional project documentation:

* [Architecture & Design](docs/design.md)
* [Build Log](BUILDLOG.md)
* [Evidence](EVIDENCE.md)

---

# Git Development Checkpoints

The project was developed using separate Git checkpoints:

```text
Stage 0 — Project setup and architecture design
Stage 1 — Database foundation
Stage 2 — Core API and tenant handling
Stage 3 — Usage metering and idempotency
Stage 4 — Quota enforcement
Stage 5 — Cost calculation
Stage 6 — Stripe Checkout
Stage 7 — Stripe webhooks and subscription synchronization
Stage 8 — Background worker
Stage 9 — Testing and evidence
Stage 10 — Final documentation
```

Each major stage was tested before moving to the next stage.

---

# Final Verification

Before submission, the project should be checked with:

```powershell
git status
```

```powershell
pytest -q
```

```powershell
docker compose ps
```

The expected automated test result is:

```text
23 passed, 1 warning
```

The final repository should contain no committed secrets, local `.env` files, virtual-environment files, or generated development artifacts.

---

# Project Summary

This project demonstrates a complete small-scale backend workflow for usage metering and subscription-aware billing:

```text
Tenant
  |
  v
Plan / Subscription
  |
  v
Billable Request
  |
  v
Boundary Validation
  |
  v
Quota Check
  |
  +---- Exceeded ----> 429
  |
  v
Idempotent Usage Event
  |
  v
Cost Calculation
  |
  v
Usage + Cost Response
```

Stripe subscription synchronization operates alongside the application:

```text
Stripe Checkout
      |
      v
Stripe Subscription
      |
      v
Signed Webhook
      |
      v
Signature Verification
      |
      v
Event Deduplication
      |
      v
Subscription Synchronization
      |
      v
PostgreSQL
```

The project prioritizes clear boundaries, real persistence, tenant isolation, deterministic billing calculations, idempotent metering, verified Stripe events, automated tests, and reproducible evidence.
