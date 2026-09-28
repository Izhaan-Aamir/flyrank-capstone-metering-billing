# Evidence

This document records concrete evidence for the FlyRank Usage Metering & Billing Engine capstone.

Evidence is added incrementally as each requirement is implemented.

---

# Stage 1 — Database Foundation

## Evidence 1 — PostgreSQL Container

### Requirement

The project requires real persistent database storage.

### Verification

Command:

```powershell
docker compose ps
```

Observed result:

```text
flyrank-capstone-db
postgres:16-alpine
Up
healthy
0.0.0.0:5432->5432/tcp
```

### Result

PostgreSQL 16 is running through Docker Compose and reports a healthy status.

---

## Evidence 2 — Database Tables

### Requirement

The database must contain the core persistence model for tenants, plans, subscriptions, and usage events.

### Verification

Command:

```powershell
docker compose exec db psql -P pager=off -U capstone_user -d capstone_db -c "\dt"
```

Observed tables:

```text
plans
stripe_events
subscriptions
tenants
usage_events
```

### Result

The required core tables exist in PostgreSQL.

A `stripe_events` table is also present to provide database-level support for future Stripe webhook deduplication.

---

## Evidence 3 — Plans and Quotas

### Verification

Command:

```powershell
docker compose exec db psql -P pager=off -U capstone_user -d capstone_db -c "SELECT code, name, api_call_limit, ai_token_limit FROM plans ORDER BY code;"
```

Observed:

```text
 code | name | api_call_limit | ai_token_limit
------+------+----------------+---------------
 free | Free |           1000 |         100000
 pro  | Pro  |          10000 |        1000000
(2 rows)
```

### Result

Both required plans exist.

Free:

* 1,000 API calls/month
* 100,000 AI tokens/month

Pro:

* 10,000 API calls/month
* 1,000,000 AI tokens/month

---

## Evidence 4 — Tenant Subscriptions

### Verification

Command:

```powershell
docker compose exec db psql -P pager=off -U capstone_user -d capstone_db -c "SELECT t.tenant_key, t.name, p.code AS plan, s.status FROM subscriptions s JOIN tenants t ON t.id = s.tenant_id JOIN plans p ON p.id = s.plan_id ORDER BY t.tenant_key;"
```

Observed:

```text
 tenant_key |      name       | plan | status
------------+-----------------+------+--------
 tenant-001 | Demo Tenant One | free | active
 tenant-002 | Demo Tenant Two | free | active
(2 rows)
```

### Result

Two demo tenants exist and each has an active Free subscription.

---

## Evidence 5 — Tenant Isolation Constraints

### Requirement

Usage and subscription records must be associated with the correct tenant.

### Database design

`subscriptions.tenant_id` references:

```text
tenants.id
```

`usage_events.tenant_id` references:

```text
tenants.id
```

Both relationships use foreign keys.

The `subscriptions` table also enforces one subscription per tenant through a unique constraint on `tenant_id`.

### Result

The database prevents subscription and usage records from referencing nonexistent tenants.

Application-level tenant request handling will be implemented in Stage 2.

---

## Evidence 6 — Usage Idempotency Constraint

### Requirement

The completed system must prevent duplicate usage events when the same request is retried with the same idempotency key.

### Database design

`usage_events` contains:

```text
CONSTRAINT uq_usage_events_tenant_idempotency
UNIQUE (tenant_id, idempotency_key)
```

### Result

The database provides a uniqueness guarantee for a tenant's idempotency key.

The actual API retry behavior will be implemented and tested in Stage 3.

---

## Evidence 7 — Usage Validation Constraints

The `usage_events` table contains database checks including:

```text
quantity > 0
input_tokens >= 0
cached_input_tokens >= 0
cached_input_tokens <= input_tokens
output_tokens >= 0
reasoning_tokens >= 0
```

The `usage_type` field is restricted to:

```text
api_calls
ai_tokens
```

### Result

Invalid usage values are rejected at the database boundary.

---

## Evidence 8 — Database Indexes

Indexes were created for the expected lookup patterns.

Current indexes include:

```text
idx_subscriptions_plan_id

idx_usage_events_tenant_occurred_at

idx_usage_events_tenant_usage_type_occurred_at

idx_stripe_events_event_type
```

Unique indexes also exist for:

```text
tenant_key
plan code
stripe customer ID
stripe subscription ID
stripe event ID
tenant + idempotency key
```

### Result

The database has indexes supporting tenant usage queries, subscription lookups, plan lookups, and Stripe event deduplication.

---

## Evidence 9 — Seeded Database Row Counts

Expected Stage 1 baseline:

```text
plans            = 2
tenants          = 2
subscriptions    = 2
usage_events     = 0
stripe_events    = 0
```

The zero usage-event and Stripe-event counts are expected because those application features have not yet been implemented.

---

# Requirements Not Yet Implemented

The following evidence will be added during later stages.

## Metering

* Exactly-once billable usage recording
* Idempotent API retry demonstration

## Quotas

* Monthly quota calculation
* Boundary test
* `429` response
* `402` response where applicable

## Cost Calculation

* API-call cost
* AI token cost
* Cached-input pricing
* Reasoning-token pricing
* Integer money calculations

## Stripe

* Checkout flow
* `checkout.session.completed`
* `customer.subscription.updated`
* `customer.subscription.deleted`
* Webhook signature verification
* Forged webhook rejection
* Duplicate event handling
* Subscription/plan synchronization

## Background Worker

* Background job
* Retry behavior
* Failure handling

## Final Testing

* Full automated test suite
* Evaluator probe results
* Final end-to-end evidence
