# Evidence

This file contains reproducible evidence for the requirements implemented so far.

The official capstone requires one pasted proof for each completed requirement and states that claims without evidence should not be treated as complete.

---

# Stage 0 — Project Setup & Design

## Design

The initial architecture and implementation plan are documented in:

```text
docs/design.md
```

The design covers:

* Python + FastAPI
* PostgreSQL
* Docker
* Free and Pro plans
* API-call and AI-token usage
* Tenant isolation
* Usage events
* Idempotency
* Quota enforcement
* Cost calculation
* Stripe Checkout
* Stripe webhook verification and deduplication
* Background processing
* Required evidence and documentation

Stage 0 established the project structure and design before the main application implementation.

---

# Stage 1 — Database Foundation

## PostgreSQL Container

PostgreSQL was started through Docker Compose.

Command:

```powershell
docker compose up -d db
```

The PostgreSQL container reached a healthy state.

The database was verified using:

```powershell
docker compose ps
```

The container exposed PostgreSQL on:

```text
localhost:5432
```

---

## Database Tables

The initial migration created:

```text
plans
stripe_events
subscriptions
tenants
usage_events
```

The database was inspected with:

```powershell
docker compose exec db psql -U capstone_user -d capstone_db -c "\dt"
```

The required application tables were present.

---

## Database Constraints

The schema includes:

### Tenant isolation

`subscriptions.tenant_id` references `tenants.id`.

`usage_events.tenant_id` references `tenants.id`.

Both use cascading deletion when a tenant is deleted.

### Plan uniqueness

`plans.code` is unique.

### Subscription uniqueness

Each tenant has one subscription through the unique `tenant_id` constraint.

Stripe customer and subscription IDs are also unique.

### Usage validation

`usage_events.quantity` must be greater than zero.

`usage_events.usage_type` is restricted to:

```text
api_calls
ai_tokens
```

Cached input tokens cannot exceed input tokens.

### Idempotency

The following constraint prevents duplicate usage events for the same tenant and idempotency key:

```sql
UNIQUE (tenant_id, idempotency_key)
```

---

## Plans

The seeded plans were verified as:

```text
 code | name | api_call_limit | ai_token_limit
------+------+----------------+----------------
 free | Free |           1000 |         100000
 pro  | Pro  |          10000 |        1000000
```

The Free limits come from the official capstone.

The Pro limits are the implementation values selected for this project.

---

## Demo Tenants

The seeded tenant/subscription data was verified as:

```text
 tenant_key |      name       | plan | status
------------+-----------------+------+--------
 tenant-001 | Demo Tenant One | free | active
 tenant-002 | Demo Tenant Two | free | active
```

Initial usage event count:

```text
usage_events = 0
```

Initial Stripe event count:

```text
stripe_events = 0
```

---

# Stage 2 — Core API & Tenant Handling

## Health Endpoint

Endpoint:

```http
GET /health
```

Verified response:

```json
{
  "status": "ok"
}
```

---

## Tenant Endpoint

Endpoint:

```http
GET /tenants/me
```

Header:

```text
X-Tenant-Key: tenant-001
```

Verified tenant:

```text
tenant_key     : tenant-001
name           : Demo Tenant One
status         : active
plan_code      : free
plan_name      : Free
api_call_limit : 1000
ai_token_limit : 100000
```

---

## Missing Tenant Header

Request without:

```text
X-Tenant-Key
```

returns:

```text
400 Bad Request
```

with:

```json
{
  "detail": "X-Tenant-Key header is required."
}
```

---

## Unknown Tenant

Request using an unknown tenant key returns:

```text
404 Not Found
```

with:

```json
{
  "detail": "Tenant not found."
}
```

---

## Automated Tests

The Stage 2 test suite initially encountered:

```text
ModuleNotFoundError: No module named 'app'
```

The project was corrected by adding:

```ini
[pytest]
pythonpath = .
```

to `pytest.ini`.

After the correction:

```text
4 passed
```

The test suite covered:

* health
* tenant lookup
* missing tenant header
* unknown tenant

---

# Stage 3 — Usage Metering & Idempotency

## Requirement

The capstone requires a billable action to create exactly one usage event even when the request is retried.

The official design describes the metering flow as:

```text
Billable request
      ↓
Metering
      ↓
duplicate key?
   ↙       ↘
 yes        no
  ↓          ↓
return     store
original   usage event
result
```

The project implements this using the database uniqueness constraint:

```sql
UNIQUE (tenant_id, idempotency_key)
```

---

## Billable Endpoint

Current endpoint:

```http
POST /generate
```

Required headers:

```text
X-Tenant-Key
Idempotency-Key
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

The resulting metered quantity is:

```text
1000 + 500 + 100 = 1600
```

Cached input is stored separately and is not added a second time to the usage quantity.

Cost calculation is not part of this stage.

---

## Normal Usage Event

The first request creates a row in:

```text
usage_events
```

The event contains:

* tenant
* usage type
* quantity
* idempotency key
* input tokens
* cached input tokens
* output tokens
* reasoning tokens

For the manual proof, the stored usage type was:

```text
ai_tokens
```

and the quantity was:

```text
1600
```

---

## Automated Idempotency Test

Test:

```text
test_same_idempotency_key_returns_same_event
```

The test sends the same request twice with:

```text
X-Tenant-Key: tenant-001
Idempotency-Key: stage3-test-002
```

Result:

```text
9 passed
```

The second response matched the first response.

This verifies that the retry returns the existing metered result rather than producing a different event.

---

## Tenant-Scoped Idempotency Test

Test:

```text
test_idempotency_key_is_scoped_to_tenant
```

The same idempotency key was used independently by:

```text
tenant-001
tenant-002
```

The test verified that the two tenants received different usage event IDs.

This demonstrates that the uniqueness rule is:

```text
tenant + idempotency key
```

rather than simply:

```text
idempotency key
```

---

## Missing Idempotency Key

Test:

```text
test_missing_idempotency_key
```

A request without:

```text
Idempotency-Key
```

returns:

```text
400 Bad Request
```

with:

```json
{
  "detail": "Idempotency-Key header is required."
}
```

---

## Invalid Token Breakdown

Test:

```text
test_invalid_token_breakdown
```

A request where:

```text
cached_input_tokens > input_tokens
```

is rejected by boundary validation.

Expected result:

```text
422 Unprocessable Entity
```

This prevents invalid token data from reaching the database.

---

# Manual Exactly-Once Proof

A manual billable request was sent twice with:

```text
X-Tenant-Key: tenant-001
Idempotency-Key: manual-stage3-proof
```

The request contained:

```json
{
  "input_tokens": 1000,
  "cached_input_tokens": 200,
  "output_tokens": 500,
  "reasoning_tokens": 100
}
```

Both requests returned the **same `usage_event_id`**.

The database was then queried with:

```sql
SELECT
    tenant_id,
    usage_type,
    quantity,
    idempotency_key
FROM usage_events
WHERE idempotency_key = 'manual-stage3-proof';
```

Database output:

```text
              tenant_id               | usage_type | quantity |   idempotency_key
--------------------------------------+------------+----------+---------------------
 c7b4f338-d707-4383-a0dd-8fd3b809e1a9 | ai_tokens  |     1600 | manual-stage3-proof
(1 row)
```

### Result

Exactly **one database row** exists for the repeated request.

Therefore:

```text
2 HTTP requests
        ↓
same tenant
        ↓
same idempotency key
        ↓
1 usage event
```

This is the primary Stage 3 evidence for the capstone's exactly-once metering requirement.

---

# Stage 3 Automated Test Summary

Command:

```powershell
pytest -q
```

Result:

```text
.........                                                 [100%]

9 passed, 1 warning
```

The warning is the existing Starlette/HTTPX deprecation warning from the installed testing stack. It did not cause any test failure.

---

# Requirements Not Yet Proven

The following requirements are intentionally **not claimed complete yet**:

## Quota Enforcement

Not implemented yet.

Future evidence will prove:

* current usage + requested usage
* quota boundary behavior
* `429 Too Many Requests`
* `402 Payment Required`

---

## Cost Calculation

Not implemented yet.

Future evidence will prove:

* API-call cost
* input-token pricing
* cached-input pricing
* output pricing
* reasoning-token handling
* integer money representation
* pinned pricing constants

---

## Stripe Integration

Not implemented yet.

Future evidence will prove:

* Checkout
* Free → Pro synchronization
* webhook signature verification
* duplicate webhook handling
* subscription status updates

---

## Background Worker

Not implemented yet.

Future evidence will prove:

* background execution
* retries
* failure handling/alerting

---

# Evidence Policy

Each future requirement will be added here only after it has been implemented and verified.

Evidence may consist of:

* automated test output
* API transcript
* database query output
* Stripe CLI output
* relevant log output

The goal is for a reviewer to reproduce the result quickly rather than relying on unsupported claims.
