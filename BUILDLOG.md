# Build Log

## Usage Metering & Billing Engine

This build log records the development process for the FlyRank AI Usage Metering & Billing Engine capstone.

The purpose of this document is to show the progression of the implementation, important engineering decisions, problems encountered, corrections made, testing performed, and use of AI assistance during development.

---

# Stage 0 — Project Setup and Design

## Goal

Establish the project structure, define the capstone scope, identify the core database concepts, and prepare environment-based configuration.

## Work Completed

The project was structured around the following layers:

```text
app/
├── routes/
├── schemas/
├── services/
├── repositories/
└── database/configuration code

worker/
tests/
migrations/
scripts/
```

The required billing concepts were identified:

* tenants,
* plans,
* subscriptions,
* usage events,
* Stripe events.

The initial plan limits were defined as:

| Plan | API Calls / Month | AI Tokens / Month |
| ---- | ----------------: | ----------------: |
| Free |             1,000 |           100,000 |
| Pro  |            10,000 |         1,000,000 |

The main usage types were defined as:

```text
api_calls
ai_tokens
```

Environment configuration was prepared for:

* PostgreSQL,
* Stripe secret key,
* Stripe webhook secret,
* Stripe Pro price ID.

## AI Assistance

AI was used as a development partner to:

* break the capstone into manageable stages,
* explain architecture decisions,
* review implementation ideas,
* suggest beginner-friendly implementation approaches,
* explain errors and testing strategies.

The implementation was written and tested incrementally rather than treating AI output as automatically correct.

---

# Stage 1 — Database Foundation

## Goal

Create persistent PostgreSQL storage with migrations, relationships, constraints, and indexes.

## Work Completed

Created the PostgreSQL migration containing:

```text
tenants
plans
subscriptions
usage_events
stripe_events
```

Important constraints were added, including:

```text
tenant_key UNIQUE
plan.code UNIQUE
subscription.tenant_id UNIQUE
stripe_customer_id UNIQUE
stripe_subscription_id UNIQUE
(tenant_id, idempotency_key) UNIQUE
stripe_event_id UNIQUE
```

Token validation constraints were also added at the database level.

PostgreSQL was configured through Docker Compose with a named volume for persistence.

## Seed Data

The database was seeded with:

* Free plan,
* Pro plan,
* tenant-001,
* tenant-002,
* initial Free subscriptions.

## Verification

Database inspection confirmed the expected tables and initial rows.

---

# Stage 2 — Core API and Tenant Handling

## Goal

Create the FastAPI application foundation and tenant-aware request handling.

## Work Completed

Implemented:

```text
GET /health
GET /tenants/me
```

Tenant identification uses:

```http
X-Tenant-Key
```

The tenant dependency resolves the tenant and its subscription/plan information.

A local `.env` file was used for the PostgreSQL connection while `.env.example` remained safe for committing.

## Verification

Tests were added for:

* health endpoint,
* valid tenant,
* missing tenant header,
* unknown tenant.

---

# Stage 3 — Usage Metering and Idempotency

## Goal

Create the first billable endpoint and ensure every successful billable request creates exactly one usage event.

## Work Completed

Implemented:

```http
POST /generate
```

The request accepts:

```text
input_tokens
cached_input_tokens
output_tokens
reasoning_tokens
```

Validation ensures:

```text
cached_input_tokens <= input_tokens
```

and prevents an entirely zero-token request.

The usage repository creates the usage event in PostgreSQL.

## Idempotency

The endpoint requires:

```http
Idempotency-Key
```

The database constraint:

```text
UNIQUE (tenant_id, idempotency_key)
```

prevents duplicate usage events for the same tenant and key.

The repository uses conflict-safe insertion and retrieves the existing event when the key has already been used.

## Testing

The following behavior was verified:

* first request creates an event,
* repeated request returns the existing event,
* no duplicate event is created,
* the same key can be used by another tenant,
* missing idempotency key is rejected.

A manual database proof was also performed using a test idempotency key.

## AI Assistance

AI was used to explain database-level idempotency and to review the smallest implementation needed for the capstone requirement.

---

# Stage 4 — Quota Enforcement

## Goal

Prevent billable usage from exceeding the tenant's current monthly AI-token limit.

## Work Completed

Implemented a quota repository that calculates current-month AI-token usage.

The quota service compares:

```text
current usage + requested usage
```

against the tenant's plan limit.

When the limit would be exceeded, the API returns:

```text
429 Too Many Requests
```

No usage event is created for the rejected request.

## Testing

Tests were added for:

* usage below the limit,
* usage exactly at the limit,
* usage over the limit,
* rejected requests not creating usage events.

## Result

The Stage 4 test suite passed.

A Git checkpoint was created:

```text
Stage 4: quota enforcement
```

## AI Assistance

AI helped explain the difference between checking current usage and checking projected usage after the requested operation.

---

# Stage 5 — Cost Calculation

## Goal

Add deterministic usage cost calculation without using floating-point money values.

## Work Completed

Implemented the pricing service with integer constants:

```python
INPUT_PRICE = 1_000_000
CACHED_INPUT_PRICE = 250_000
OUTPUT_PRICE = 2_000_000
REASONING_PRICE = 2_000_000
```

The calculation returns:

```text
cost_micro_units
```

No floating-point arithmetic is used.

## Cached Input

A specific implementation detail was required to avoid double charging cached input.

The calculation first determines:

```text
regular_input_tokens =
    input_tokens - cached_input_tokens
```

The final cost therefore contains:

```text
regular input cost
+ cached input cost
+ output cost
+ reasoning cost
```

## Reasoning Tokens

Reasoning tokens are explicitly included in the cost calculation using the reasoning price.

## Testing

Pricing tests verified:

* normal input/output pricing,
* cached input,
* no double charging of cached input,
* reasoning token pricing,
* zero cached input.

Result:

```text
4 passed
```

## Result

The usage response was updated to include:

```text
cost_micro_units
```

A Git checkpoint was created:

```text
Stage 5: cost calculation
```

---

# Stage 6 — Stripe Checkout

## Goal

Connect the application to Stripe test/sandbox mode and create a Pro subscription Checkout Session.

## Work Completed

Stripe was installed and configured.

A Stripe Pro product and recurring test-mode price were created.

The application was configured using:

```text
STRIPE_SECRET_KEY
STRIPE_PRO_PRICE_ID
```

Implemented:

```http
POST /checkout/pro
```

The Checkout Session is created with:

```text
mode = subscription
```

The tenant ID is placed into both Checkout Session metadata and subscription metadata.

## Problem Encountered

The first Checkout request returned HTTP 500 because the local configuration still contained the placeholder Stripe secret.

## Correction

The placeholder was replaced with the real Stripe test-mode secret, the FastAPI application was restarted, and the Checkout flow was tested again.

The Checkout Session then created successfully.

## AI Assistance

AI was used to diagnose the configuration problem from the observed error rather than changing unrelated application code.

## Result

Stripe Checkout worked successfully in test/sandbox mode.

A Git checkpoint was created:

```text
Stage 6: Stripe checkout
```

---

# Stage 7 — Stripe Webhooks and Subscription Synchronization

## Goal

Verify Stripe webhook signatures, process required subscription events, deduplicate events, and synchronize local subscription state.

## Stripe CLI Setup

The Stripe CLI was installed and authenticated.

The webhook listener was configured with:

```powershell
stripe listen --events checkout.session.completed,customer.subscription.updated,customer.subscription.deleted --forward-to localhost:8000/webhooks/stripe
```

The generated webhook signing secret was stored only in the local `.env` file.

It was not committed to Git.

---

## Initial Stripe SDK Problem

During webhook implementation, Stripe event objects were treated like normal dictionaries.

This caused problems when handlers attempted dictionary-style operations directly on Stripe SDK event objects.

## Correction

The event objects were converted using:

```python
event.to_dict()
```

before the application accessed their fields.

This allowed the existing service logic to work with normal dictionaries.

---

## Stripe Account Alignment Problem

An earlier webhook replay failed because the Stripe event belonged to a different/previous test context and did not contain the expected tenant metadata.

## Correction

The FastAPI application and Stripe CLI were aligned to the same Stripe sandbox/test account.

A fresh Checkout Session was then created so that the correct tenant metadata was present.

The new event was processed successfully.

---

# Stripe Subscription Period Problem

During subscription update testing, the billing period fields were initially not being populated in the local database.

The initial implementation attempted to read the period values from the subscription object's top-level fields.

The Stripe subscription response used during testing contained the period values under the subscription item's data.

## Correction

The subscription handler was updated to read:

```text
items.data[0].current_period_start
items.data[0].current_period_end
```

The values were converted from Stripe timestamps into UTC datetime values before being stored.

---

# Stripe Webhook Deduplication

A `stripe_events` table was used to record successfully processed Stripe event IDs.

Before dispatching an event, the webhook checks whether the event ID has already been recorded.

Repeated events return a successful duplicate response rather than being processed again.

A Stripe CLI event was replayed to verify this behavior.

The duplicate event was recognized successfully.

---

# Subscription Event Handling

The following events were implemented:

```text
checkout.session.completed
customer.subscription.updated
customer.subscription.deleted
```

### Checkout Completed

Changes the tenant subscription to:

```text
plan = pro
status = active
```

and stores the Stripe customer/subscription identifiers.

### Subscription Updated

Synchronizes the Stripe subscription status and billing period.

Supported statuses include:

```text
active
trialing
past_due
canceled
```

### Subscription Deleted

Changes the local subscription to:

```text
plan = free
status = canceled
```

---

# Stripe Test Result

A real Stripe test-mode Checkout flow was completed.

The database showed the resulting Stripe customer and subscription information.

Stripe subscription updates were forwarded through the CLI and processed by the application.

The webhook endpoint returned successful responses.

---

# Stage 8 — Background Worker

## Goal

Add a small background processing abstraction for billing-related work.

## Work Completed

Created:

```text
worker/
├── __init__.py
├── jobs.py
└── worker.py
```

Implemented:

```text
BillingJob
BillingWorker
```

The worker supports:

```text
finalize_usage
```

and rejects unknown job types.

## Testing

Added worker tests for:

* processing a valid finalization job,
* rejecting an unknown job type.

## Implementation Decision

The worker was intentionally kept small.

It uses Python's in-process `Queue` rather than introducing an external queue system.

This was chosen to satisfy the background-job structure without unnecessarily expanding the capstone scope.

## Result

Worker tests passed.

A Git checkpoint was created:

```text
Stage 8: add background worker
```

---

# Stage 9 — Testing and Evidence

## Goal

Expand automated coverage around the core billing and Stripe behavior and produce evidence for the capstone requirements.

## Existing Test Coverage

The project already contained tests for:

* tenants,
* usage,
* idempotency,
* quota,
* pricing.

## Webhook Tests Added

A new:

```text
tests/test_webhooks.py
```

was created.

The tests cover:

1. invalid Stripe signature,
2. missing Stripe signature,
3. duplicate Stripe event,
4. valid checkout event dispatch.

## Initial Test Failure

The webhook dispatch test initially expected a hard-coded event ID that did not match the dynamically generated fake event ID.

The test failed because the assertion expected:

```text
evt_test_checkout_001
```

while the fake event actually used its generated ID.

## Correction

The assertion was changed to use:

```python
fake_event["id"]
```

This made the test verify the actual event returned by the mocked Stripe webhook parser rather than an unrelated hard-coded value.

## Verification

Webhook tests:

```text
4 passed
```

Usage tests:

```text
9 passed
```

Pricing tests:

```text
4 passed
```

The complete suite was then executed.

## Final Test Result

```text
23 passed, 1 warning
```

The warning is an existing Starlette/HTTPX deprecation warning and does not cause test failure.

---

# Documentation Finalization

After implementation and testing, the following documentation was prepared:

```text
README.md
EVIDENCE.md
BUILDLOG.md
capstone.yaml
```

The README documents:

* project purpose,
* architecture,
* stages,
* setup,
* endpoints,
* database structure,
* usage metering,
* quota enforcement,
* pricing,
* Stripe integration,
* worker,
* testing,
* project boundaries.

The evidence document records the actual verification performed for the capstone requirements.

The `capstone.yaml` provides evaluator-facing run, seed, test, base URL, endpoint, plan, Stripe, pricing, and worker information.

---

# Problems and Corrections Summary

| Problem                                         | Cause                                                      | Correction                                                  |
| ----------------------------------------------- | ---------------------------------------------------------- | ----------------------------------------------------------- |
| Stripe Checkout returned 500                    | Placeholder Stripe secret                                  | Configured real Stripe test-mode secret                     |
| Stripe event object handling failed             | SDK objects were not normal dictionaries                   | Used `to_dict()`                                            |
| Old Stripe event lacked tenant metadata         | Event belonged to earlier/different test context           | Used a fresh Checkout event from the aligned Stripe account |
| Subscription period remained empty              | Period fields were nested under subscription items         | Read `items.data[0]` period fields                          |
| Webhook test failed                             | Assertion used stale hard-coded event ID                   | Asserted against `fake_event["id"]`                         |
| Duplicate events needed protection              | Webhooks may be delivered repeatedly                       | Added `stripe_events` storage and event-ID deduplication    |
| Worker scope could become unnecessarily complex | Production queue systems were outside the core requirement | Implemented a small in-process worker abstraction           |

---

# AI Usage and Learning Process

AI assistance was used throughout development as a learning and debugging tool.

The main uses were:

* understanding FastAPI architecture,
* breaking the capstone into implementation stages,
* explaining PostgreSQL schema decisions,
* understanding idempotency,
* reviewing quota logic,
* explaining integer-based cost calculation,
* troubleshooting Stripe SDK behavior,
* diagnosing test failures,
* reviewing project structure,
* improving documentation.

When an error occurred, the actual terminal output, test result, or application behavior was used to identify the problem before applying a correction.

AI-generated suggestions were not treated as automatically correct. Code was tested locally and adjusted when the observed behavior differed from the expected behavior.

The project was intentionally implemented incrementally so that each major stage could be understood, tested, and checkpointed before moving forward.

---

# Git Checkpoints

Meaningful development checkpoints were created throughout the project.

Known stage checkpoints include:

```text
Stage 0: project setup and architecture design
Stage 1: database foundation
Stage 2: core API and tenant handling
Stage 3: usage metering and idempotency
Stage 4: quota enforcement
Stage 5: cost calculation
Stage 6: Stripe checkout
Stage 8: add background worker
```

The repository uses the `main` branch and the GitHub repository was used as the project submission repository.

Before final submission, the repository should be checked for:

* accidental `.env` files,
* secrets,
* virtual environments,
* generated files,
* unnecessary debug files,
* uncommitted changes.

---

# Final Verification

The final automated test command was:

```powershell
pytest -q
```

Final result:

```text
23 passed, 1 warning
```

The major integration path was also manually verified using Stripe test/sandbox mode.

The final implementation contains:

```text
Tenant handling
        ↓
Usage validation
        ↓
Quota enforcement
        ↓
Idempotent usage event
        ↓
Cost calculation
        ↓
Stripe subscription checkout
        ↓
Verified Stripe webhook
        ↓
Subscription synchronization
```

A background worker abstraction is also included for billing-related processing.

---

# Final Build Status

## Completed

* [x] Stage 0 — Project Setup and Design
* [x] Stage 1 — Database Foundation
* [x] Stage 2 — Core API and Tenant Handling
* [x] Stage 3 — Usage Metering and Idempotency
* [x] Stage 4 — Quota Enforcement
* [x] Stage 5 — Cost Calculation
* [x] Stage 6 — Stripe Checkout
* [x] Stage 7 — Stripe Webhooks and Subscription Synchronization
* [x] Stage 8 — Background Worker
* [x] Stage 9 — Testing and Evidence
* [x] Documentation — README, EVIDENCE, BUILDLOG, capstone.yaml

## Final Automated Result

```text
23 passed, 1 warning
```

The project is ready for the final repository cleanup and submission review.

```

That completes the **four core documentation files**: `README.md`, `EVIDENCE.md`, `capstone.yaml`, and `BUILDLOG.md`.
```
