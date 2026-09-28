# Evidence

## 1. Purpose

This document provides the evidence for the Usage Metering & Billing Engine capstone.

The evidence is organized around the capstone requirements and records:

* what was implemented,
* how it was verified,
* the relevant endpoint, database, test, or manual proof,
* and any important limitations or implementation notes.

The project uses FastAPI, PostgreSQL, Stripe test/sandbox mode, and a small background worker abstraction.

---

# 2. Evidence Summary

| Requirement Area                | Implementation                                                     | Verification                          |
| ------------------------------- | ------------------------------------------------------------------ | ------------------------------------- |
| Project setup and configuration | Environment-based configuration, Docker Compose, project structure | Manual inspection                     |
| Persistent database             | PostgreSQL with migrations and indexes                             | Database inspection                   |
| Tenant isolation                | `X-Tenant-Key` dependency and tenant-scoped queries                | Automated tests                       |
| Plans and subscriptions         | Free/Pro plans and subscription records                            | Database inspection                   |
| Usage metering                  | AI-token usage events                                              | Automated tests + database inspection |
| Idempotency                     | Unique `(tenant_id, idempotency_key)` constraint                   | Automated tests + database inspection |
| Quota enforcement               | Current-month AI-token quota check                                 | Automated tests                       |
| Cost calculation                | Integer micro-unit calculation                                     | Automated tests                       |
| Stripe Checkout                 | Pro subscription Checkout Session                                  | Manual Stripe test                    |
| Stripe webhooks                 | Signature verification and required event handling                 | Automated tests + Stripe CLI          |
| Stripe event deduplication      | `stripe_events` table and event ID uniqueness                      | Automated tests + manual replay       |
| Subscription synchronization    | Stripe events update local subscription state                      | Manual Stripe test                    |
| Background worker               | `BillingWorker` + `BillingJob`                                     | Automated tests                       |
| Final automated test suite      | 23 passing tests                                                   | `pytest -q`                           |

---

# 3. Stage 0 — Project Setup and Design

## Requirement

The project must have a clear structure, environment-based configuration, documented scope, and the required capstone supporting files.

## Evidence

The project contains separate application layers for:

* routes,
* schemas,
* services,
* repositories,
* database access,
* worker jobs,
* tests,
* migrations.

Environment-specific values are loaded through configuration rather than being hard-coded into the application.

The repository includes:

```text
.env.example
README.md
EVIDENCE.md
BUILDLOG.md
capstone.yaml
docker-compose.yml
migrations/
app/
tests/
worker/
```

The `.env.example` file contains placeholders only and does not contain real Stripe credentials or other secrets.

## Verification

Manual repository inspection confirmed that:

* secrets are not stored in source files,
* Stripe credentials are supplied through environment variables,
* PostgreSQL configuration is environment-based,
* the project has a documented implementation structure.

---

# 4. Stage 1 — Database Foundation

## Requirement

The application must use real persistent storage with the required billing concepts, constraints, indexes, and tenant isolation.

## Evidence

PostgreSQL is used as the persistent database.

The migration creates the following tables:

```text
tenants
plans
subscriptions
usage_events
stripe_events
```

### `tenants`

Stores:

* tenant UUID,
* tenant key,
* tenant name,
* creation timestamp.

`tenant_key` is unique.

### `plans`

Stores:

* plan code,
* plan name,
* API call limit,
* AI token limit,
* active status.

### `subscriptions`

Stores:

* tenant,
* plan,
* subscription status,
* Stripe customer ID,
* Stripe subscription ID,
* current billing period,
* timestamps.

Each tenant has one subscription record.

### `usage_events`

Stores:

* tenant,
* usage type,
* quantity,
* idempotency key,
* input tokens,
* cached input tokens,
* output tokens,
* reasoning tokens,
* timestamps.

The database enforces:

```text
quantity > 0
input_tokens >= 0
cached_input_tokens >= 0
cached_input_tokens <= input_tokens
output_tokens >= 0
reasoning_tokens >= 0
```

The database also enforces:

```text
UNIQUE (tenant_id, idempotency_key)
```

### `stripe_events`

Stores:

* Stripe event ID,
* event type,
* processing timestamp.

The Stripe event ID is unique.

## Seeded Plans

The database was seeded with:

| Plan | API Calls / Month | AI Tokens / Month |
| ---- | ----------------: | ----------------: |
| Free |             1,000 |           100,000 |
| Pro  |            10,000 |         1,000,000 |

Two test tenants were also seeded:

```text
tenant-001
tenant-002
```

Both were initially assigned the Free plan.

## Verification

Database inspection confirmed the expected tables, plans, tenants, subscriptions, and constraints.

---

# 5. Stage 2 — Core API and Tenant Handling

## Requirement

The API must identify the current tenant and prevent usage from being handled without a valid tenant context.

## Evidence

The application exposes:

```text
GET /health
GET /tenants/me
```

Tenant identification is performed using:

```http
X-Tenant-Key
```

The dependency responsible for tenant lookup retrieves the tenant and its subscription/plan information.

## Verification

Automated tenant tests cover:

* health endpoint,
* valid tenant lookup,
* missing tenant header,
* unknown tenant key.

The test suite confirms that requests without a valid tenant context are rejected.

---

# 6. Stage 3 — Usage Metering

## Requirement

Every billable action must create one usage event containing the relevant usage information.

## Evidence

The dummy billable endpoint is:

```http
POST /generate
```

The endpoint accepts:

```json
{
  "input_tokens": 100,
  "cached_input_tokens": 20,
  "output_tokens": 50,
  "reasoning_tokens": 10
}
```

The application calculates:

```text
quantity =
    input_tokens
    + output_tokens
    + reasoning_tokens
```

The resulting usage event is stored in PostgreSQL.

The response includes:

```text
usage_event_id
tenant_key
usage_type
quantity
input_tokens
cached_input_tokens
output_tokens
reasoning_tokens
cost_micro_units
```

## Validation

The request model rejects invalid token breakdowns.

For example:

```text
cached_input_tokens > input_tokens
```

is rejected.

A request where all token quantities are zero is also rejected.

## Verification

`tests/test_usage.py` verifies:

* usage event creation,
* token validation,
* successful generation requests,
* idempotency behavior,
* tenant scoping,
* quota interaction.

---

# 7. Stage 3 — Idempotency

## Requirement

The same tenant making the same billable request with the same idempotency key must not create multiple usage events.

## Evidence

The endpoint requires:

```http
Idempotency-Key: <unique-key>
```

Requests without the header return:

```text
400 Bad Request
```

Keys longer than 255 characters are rejected.

The database enforces:

```sql
UNIQUE (tenant_id, idempotency_key)
```

The usage repository uses conflict-safe insertion.

When the same tenant sends the same idempotency key again, the existing usage event is returned rather than creating another event.

## Verification

Automated tests confirm that:

1. The first request creates one usage event.
2. The second request using the same key does not create another event.
3. The response represents the same usage event.
4. The same idempotency key can be used independently by different tenants.

A database proof was also performed using a manual idempotency key.

The database contained only one corresponding usage event after the repeated request.

---

# 8. Stage 4 — Quota Enforcement

## Requirement

Usage must be checked against the tenant's current plan quota before a new usage event is created.

## Evidence

The quota service calculates current-month AI-token usage from PostgreSQL.

The relevant usage is restricted to:

```text
usage_type = 'ai_tokens'
```

and the current calendar month.

The quota check uses:

```text
current_usage + requested_tokens
```

If this value is greater than the tenant's plan limit, the request is rejected.

The API returns:

```text
429 Too Many Requests
```

with:

```text
AI token quota exceeded.
```

No usage event is created for the rejected request.

## Verification

`tests/test_usage.py` verifies:

* usage below the limit,
* usage exactly at the limit,
* usage exceeding the limit,
* rejection when the request would exceed the quota,
* no usage event being created for a quota-rejected request.

---

# 9. Stage 5 — Cost Calculation

## Requirement

Usage cost must be calculated deterministically using integer arithmetic rather than floating-point money values.

## Evidence

The pricing service uses integer constants:

```python
INPUT_PRICE = 1_000_000
CACHED_INPUT_PRICE = 250_000
OUTPUT_PRICE = 2_000_000
REASONING_PRICE = 2_000_000
```

The calculation uses integer arithmetic and returns:

```text
cost_micro_units
```

No floating-point arithmetic is used for the cost calculation.

## Cached Input Handling

Cached input is treated as a subset of total input.

The regular input amount is calculated as:

```text
regular_input_tokens =
    input_tokens - cached_input_tokens
```

Therefore cached input is not charged twice.

The calculation is conceptually:

```text
regular input × INPUT_PRICE
+
cached input × CACHED_INPUT_PRICE
+
output × OUTPUT_PRICE
+
reasoning × REASONING_PRICE
```

## Reasoning Tokens

Reasoning tokens are separately represented and charged using:

```text
REASONING_PRICE
```

They are therefore included in the final billable token cost rather than being silently ignored.

## Verification

`tests/test_pricing.py` contains four pricing tests covering:

* basic pricing,
* cached input without double charging,
* reasoning token charging,
* zero cached input.

Result:

```text
4 passed
```

---

# 10. Stage 6 — Stripe Checkout

## Requirement

The application must provide a Stripe test-mode subscription Checkout flow for upgrading a tenant to Pro.

## Evidence

The endpoint is:

```http
POST /checkout/pro
```

The endpoint uses the current tenant context and creates a Stripe Checkout Session configured for:

```text
mode = subscription
```

The configured Pro Stripe Price ID is loaded from:

```text
STRIPE_PRO_PRICE_ID
```

The tenant ID is included in both:

```text
Checkout Session metadata
Subscription metadata
```

The endpoint returns:

```json
{
  "checkout_url": "...",
  "session_id": "..."
}
```

## Manual Verification

A real Stripe test/sandbox product and recurring Pro price were created.

A real test-mode Stripe secret key and Pro price ID were configured locally.

A Checkout Session was successfully created through:

```text
POST /checkout/pro
```

The returned Stripe Checkout URL was opened successfully and produced the expected subscription flow.

---

# 11. Stage 7 — Stripe Webhooks

## Requirement

Stripe subscription state must be synchronized through verified webhook events.

The required events are:

```text
checkout.session.completed
customer.subscription.updated
customer.subscription.deleted
```

## Evidence

The webhook endpoint is:

```http
POST /webhooks/stripe
```

The endpoint:

1. Reads the raw request body.
2. Requires the `Stripe-Signature` header.
3. Verifies the Stripe signature.
4. Rejects invalid webhook payloads.
5. Checks whether the Stripe event was already processed.
6. Dispatches supported events to the subscription service.
7. Records successfully processed event IDs.

## Signature Verification

A missing signature returns:

```text
400 Bad Request
```

with:

```text
Stripe-Signature header is required.
```

An invalid signature returns:

```text
400 Bad Request
```

with:

```text
Invalid Stripe webhook.
```

The event is not processed when signature verification fails.

## Automated Verification

`tests/test_webhooks.py` contains four tests covering:

* invalid signature rejection,
* missing signature rejection,
* duplicate event handling,
* valid checkout event dispatch.

Result:

```text
4 passed
```

---

# 12. Stripe Event Deduplication

## Requirement

Repeated delivery of the same Stripe event must not cause the subscription update to be applied repeatedly.

## Evidence

Processed Stripe events are stored in:

```text
stripe_events
```

The table enforces:

```sql
UNIQUE (stripe_event_id)
```

Before processing an event, the webhook checks whether its event ID already exists.

If it has already been processed, the endpoint returns a successful duplicate response without dispatching the event again.

Example response:

```json
{
  "received": true,
  "duplicate": true,
  "event_id": "..."
}
```

## Manual Verification

A Stripe CLI event was replayed after the original event had already been processed.

The webhook endpoint returned HTTP 200 and recognized the event as a duplicate.

The duplicate delivery did not create another Stripe event record or apply another subscription transition.

---

# 13. Stripe Subscription Synchronization

## Requirement

Verified Stripe events must update the local subscription mirror.

Stripe remains the external source of truth, while PostgreSQL stores the synchronized local state.

## Evidence

The subscription service handles:

```text
checkout.session.completed
customer.subscription.updated
customer.subscription.deleted
```

### Checkout Completed

The checkout session provides:

```text
tenant_id
Stripe customer ID
Stripe subscription ID
```

The local tenant subscription is changed to:

```text
plan = pro
status = active
```

### Subscription Updated

The Stripe subscription status is mapped to the application's supported statuses:

```text
active
trialing
past_due
canceled
```

The current billing period timestamps are also synchronized.

### Subscription Deleted

The local subscription is changed to:

```text
plan = free
status = canceled
```

The Stripe subscription identifier remains available for identifying the Stripe subscription involved in the event.

## Manual Verification

A real Stripe Checkout flow was completed for the test tenant.

The local database reflected the resulting Stripe customer and subscription identifiers.

A subsequent Stripe subscription update was forwarded through the Stripe CLI listener.

The application received the webhook successfully and synchronized the subscription state.

The implementation also reads billing period timestamps from the subscription item's period data.

---

# 14. Stripe CLI Verification

The Stripe CLI was used to forward test-mode events to the local FastAPI application.

The listener was configured for:

```powershell
stripe listen --events checkout.session.completed,customer.subscription.updated,customer.subscription.deleted --forward-to localhost:8000/webhooks/stripe
```

The CLI listener generated a webhook signing secret which was stored only in the local `.env` file.

The secret was not committed to Git.

Stripe CLI login was completed against the same Stripe sandbox/test account used by the FastAPI application.

---

# 15. Stage 8 — Background Worker

## Requirement

The application should have a background processing abstraction for billing-related work.

## Evidence

The project contains:

```text
worker/
├── __init__.py
├── jobs.py
└── worker.py
```

A `BillingJob` contains:

```text
job_id
tenant_id
job_type
payload
```

The `BillingWorker` provides:

```text
submit()
get_next_job()
process_next_job()
run_once()
```

The currently supported job type is:

```text
finalize_usage
```

The worker returns a confirmation when this job is processed.

Unknown job types raise a `ValueError`.

## Verification

`tests/test_worker.py` verifies:

* successful processing of a `finalize_usage` job,
* rejection of an unknown job type.

The worker tests passed as part of the complete test suite.

## Implementation Note

The current worker is intentionally a small in-process queue abstraction.

It is not intended to represent a production distributed queue such as Celery, RabbitMQ, Kafka, or a cloud-managed job system.

---

# 16. Stage 9 — Automated Testing

## Final Test Result

The complete test suite was executed using:

```powershell
pytest -q
```

Result:

```text
23 passed, 1 warning
```

The warning is an existing Starlette/HTTPX deprecation warning and does not cause test failure.

## Test Coverage

### Tenant Tests

Cover:

* health endpoint,
* valid tenant lookup,
* missing tenant header,
* unknown tenant.

### Usage Tests

Cover:

* usage event creation,
* idempotency,
* tenant-scoped idempotency,
* missing idempotency key,
* token validation,
* quota below limit,
* quota at limit,
* quota over limit,
* rejected quota request not creating an event.

Result:

```text
9 passed
```

### Pricing Tests

Cover:

* normal pricing,
* cached input,
* reasoning tokens,
* zero cached input.

Result:

```text
4 passed
```

### Webhook Tests

Cover:

* missing signature,
* invalid signature,
* duplicate Stripe event,
* valid checkout event dispatch.

Result:

```text
4 passed
```

### Worker Tests

Cover:

* valid finalization job,
* unknown job type.

---

# 17. Tenant Isolation Evidence

Tenant information is resolved through the `X-Tenant-Key` header.

Database queries use the resolved tenant ID when reading or creating usage records.

The usage idempotency constraint is:

```text
(tenant_id, idempotency_key)
```

This means an idempotency key is scoped to a tenant rather than globally shared across all tenants.

The automated tests include a tenant-scope idempotency case.

This verifies that two different tenants can use the same idempotency key without being treated as the same usage event.

---

# 18. Persistence Evidence

The application does not use an in-memory dictionary as its primary billing store.

Persistent billing information is stored in PostgreSQL.

The database contains:

```text
tenants
plans
subscriptions
usage_events
stripe_events
```

Usage events survive application restarts because they are persisted in PostgreSQL.

The Docker Compose configuration also provides a named PostgreSQL volume:

```text
postgres_data
```

---

# 19. Secrets and Configuration Evidence

Secrets are provided through environment variables.

The application configuration includes values such as:

```text
DATABASE_URL
STRIPE_SECRET_KEY
STRIPE_WEBHOOK_SECRET
STRIPE_PRO_PRICE_ID
```

The repository contains `.env.example` with placeholders.

The real `.env` file is local-only and is not intended to be committed.

Stripe test/sandbox credentials were used during manual integration testing.

No live production Stripe credentials are required by this project.

---

# 20. API Evidence Summary

The main implemented endpoints are:

| Method | Endpoint           | Purpose                                |
| ------ | ------------------ | -------------------------------------- |
| GET    | `/health`          | Application health check               |
| GET    | `/tenants/me`      | Resolve current tenant                 |
| POST   | `/generate`        | Billable AI-token usage endpoint       |
| POST   | `/checkout/pro`    | Create Pro Stripe Checkout Session     |
| POST   | `/webhooks/stripe` | Receive verified Stripe webhook events |

The application also exposes FastAPI's automatic API documentation during local development.

---

# 21. Database State Evidence

The initial seeded database contained:

```text
Plans:          2
Tenants:        2
Subscriptions: 2
Usage events:   0
Stripe events:  0
```

During testing and manual verification, usage and Stripe event records were subsequently created as expected.

The subscription table was also updated during the Stripe Checkout/webhook integration test.

---

# 22. Required Behavior Verification

## Idempotent Usage

Verified.

Same tenant + same idempotency key does not create a second usage event.

## Quota Boundary

Verified.

Requests within the quota are accepted.

Requests that would make:

```text
current usage + requested usage > plan limit
```

are rejected with HTTP 429.

## Invalid Token Breakdown

Verified.

Cached input cannot exceed total input.

## Cost Calculation

Verified.

Integer arithmetic is used and cached input is not double charged.

## Stripe Checkout

Verified manually in Stripe test/sandbox mode.

## Invalid Stripe Signature

Verified automatically.

Invalid signatures return HTTP 400.

## Duplicate Stripe Event

Verified automatically and through Stripe CLI replay.

Duplicate events are ignored.

## Stripe Subscription Synchronization

Verified manually through Stripe test-mode Checkout and subscription webhook delivery.

---

# 23. Evidence Files and Supporting Material

The repository contains the following supporting project documentation:

```text
README.md
EVIDENCE.md
BUILDLOG.md
capstone.yaml
```

The evidence in this document should be read together with:

* the source code,
* database migrations,
* automated tests,
* Stripe CLI integration results,
* and the project build log.

---

# 24. Implementation Boundaries

The following items are intentionally outside the implemented core scope:

* real AI model execution,
* production payment processing,
* production invoice generation,
* proration,
* overage billing,
* complex subscription lifecycle management,
* distributed queue infrastructure,
* production-grade worker orchestration.

The `/generate` endpoint simulates AI usage by accepting token quantities from the request.

The background worker is a minimal in-process implementation intended to demonstrate background job structure rather than production queue infrastructure.

---

# 25. Final Verification

The final automated verification command was:

```powershell
pytest -q
```

Final result:

```text
23 passed, 1 warning
```

The implementation therefore has automated coverage for the core usage metering, tenant handling, quota enforcement, cost calculation, Stripe webhook validation/deduplication, and background worker behavior.

Manual Stripe test-mode verification additionally confirmed the Checkout and webhook integration path.

---

# 26. Final Evidence Status

### Completed and Verified

* [x] Project structure and environment configuration
* [x] PostgreSQL persistence
* [x] Database migrations
* [x] Plans and subscriptions
* [x] Tenant handling
* [x] Usage metering
* [x] Idempotency
* [x] Quota enforcement
* [x] Integer cost calculation
* [x] Stripe Checkout
* [x] Stripe webhook signature verification
* [x] Stripe event deduplication
* [x] Stripe subscription synchronization
* [x] Background worker
* [x] Automated test suite
* [x] Manual Stripe test-mode verification

### Final Automated Result

```text
23 passed, 1 warning
```

The warning does not represent a failing test.
