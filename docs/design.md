# Usage Metering & Billing Engine — Design Document

## 1. Project Goal

Build a backend service for a SaaS product that tracks customer usage, enforces monthly usage quotas, calculates usage costs, and synchronizes subscription plans with Stripe test mode.

The system will support two plans:

* **Free:** 1,000 API calls/month and 100,000 AI tokens/month.
* **Pro:** 10,000 API calls/month and 1,000,000 AI tokens/month.

The Pro limits are implementation choices and will also be documented in the README.

AI usage will be simulated. No real AI model API is required.

---

## 2. Technology Stack

* Python
* FastAPI
* PostgreSQL
* Docker
* Docker Compose
* Stripe Test Mode
* Stripe CLI
* pytest
* Git/GitHub

The application will use a layered architecture separating HTTP routes, business services, and database repositories.

---

## 3. Core Entities

### Tenant

Represents a customer organization.

Each tenant owns its own subscription and usage data.

### Plan

Represents a subscription plan and its monthly quotas.

Each plan contains:

* plan name
* API call limit
* AI token limit

### Subscription

Connects a tenant to a plan and stores subscription status and Stripe identifiers where applicable.

### Usage Event

Represents a billable action performed by a tenant.

A usage event will contain:

* tenant
* idempotency key
* timestamp
* API call quantity
* AI token quantity
* token breakdown required for cost calculation

The event will preserve the detailed token categories:

* input tokens
* cached input tokens
* output tokens
* reasoning tokens

### Stripe Event

Stores processed Stripe event identifiers so that webhook retries/replays do not cause duplicate processing.

---

## 4. Tenant Isolation

The initial API will identify the tenant using an `X-Tenant-ID` request header.

All database queries involving customer data will be scoped to the identified tenant.

A tenant must never be able to read or modify another tenant's usage or subscription information.

Authentication is intentionally kept outside the initial scope because the capstone brief requires tenant isolation but does not require a particular authentication provider.

---

## 5. Main API

The planned endpoints are:

* `GET /health`
* `POST /generate`
* `GET /usage`
* `POST /billing/checkout`
* `POST /webhooks/stripe`

### POST /generate

This is the dummy billable endpoint.

It will accept simulated token usage and will:

1. Identify the tenant.
2. Validate the request.
3. Check the idempotency key.
4. Check the tenant's quota.
5. Record usage if allowed.
6. Calculate the cost.
7. Return the result.

The request will use an `Idempotency-Key` header.

The same billable request using the same idempotency key must create exactly one usage event. A retry must return the original result instead of creating another usage event.

### GET /usage

Returns the tenant's monthly usage rollup, including:

* API calls used
* AI tokens used
* plan limits
* calculated cost

### POST /billing/checkout

Creates a Stripe Checkout session for upgrading the tenant to the Pro plan.

### POST /webhooks/stripe

Receives Stripe webhook events, verifies the Stripe signature, deduplicates events, and updates the tenant's subscription state.

---

## 6. Quota Enforcement

Before a billable action is allowed, the system will calculate:

`current usage + requested usage`

and compare it with the tenant's plan limit.

Requests within the limit are allowed.

Requests that exceed the documented quota boundary are rejected with the appropriate `429` or `402` response and a clear explanation.

The exact boundary behavior will be documented in the README and demonstrated in EVIDENCE.md.

---

## 7. Idempotency

Usage metering will use the tenant's idempotency key to prevent duplicate billing.

The database will enforce uniqueness so that concurrent or repeated requests cannot accidentally create duplicate usage events.

The application will check for an existing event and return the original result for a repeated idempotency key.

Idempotency will be tested explicitly.

---

## 8. Cost Calculation

The billing engine will support:

* API call pricing
* normal input token pricing
* cached input token pricing
* output token pricing
* reasoning token pricing

Cached input will use a cheaper rate.

Reasoning tokens will be treated as output tokens for pricing.

Token categories will not be blindly added together when calculating cost.

Pricing constants will be pinned in configuration and demonstrated in EVIDENCE.md.

Money will be represented using integer cents or micro-units rather than floating-point values.

---

## 9. Stripe Integration

Stripe will be used only in test mode.

The application will support:

* `checkout.session.completed`
* `customer.subscription.updated`
* `customer.subscription.deleted`

Stripe webhook signatures must be verified before processing.

Invalid signatures will return HTTP 400 and will not change subscription state.

Repeated delivery of the same valid Stripe event will be detected and ignored after the first successful processing.

Stripe is the source of payment truth, while the application database mirrors the subscription state using verified webhook events.

---

## 10. Background Job

The application will include at least one background worker for slow or bulk processing.

The selected job will be useful to the billing system and will run outside the main HTTP request path.

The worker will include retry handling and failure reporting/alerting as required by the capstone evaluation requirements.

The exact job implementation will be finalized during the implementation stage without adding unnecessary infrastructure.

---

## 11. Database Architecture

PostgreSQL will run through Docker Compose.

The database schema will be managed through migration files.

Planned core tables:

* `tenants`
* `plans`
* `subscriptions`
* `usage_events`
* `stripe_events`

Indexes and constraints will be added where necessary for:

* tenant isolation
* idempotency lookups
* Stripe event deduplication
* monthly usage queries
* foreign-key relationships

---

## 12. Layered Architecture

The request flow will follow:

Client
→ FastAPI route
→ Service layer
→ Repository/data-access layer
→ PostgreSQL

For billing:

Client
→ Metering service
→ Quota service
→ Cost service
→ Repository
→ PostgreSQL

For Stripe:

Stripe Checkout
→ Stripe
→ Signed webhook
→ Webhook route
→ Signature verification
→ Event deduplication
→ Subscription service
→ Repository
→ PostgreSQL

---

## 13. Security and Configuration

Secrets will be stored in `.env` and never committed to Git.

`.env.example` will contain only safe placeholders.

The project will use Stripe test credentials only.

Input validation will occur at the API boundary so invalid input produces an appropriate 4xx response rather than an unexpected server error.

---

## 14. Evidence and Documentation

The project will maintain:

* `README.md`
* `EVIDENCE.md`
* `BUILDLOG.md`
* `capstone.yaml`
* `.env.example`

EVIDENCE.md will contain reproducible proof for the major requirements, including:

1. Exactly-once usage metering.
2. Quota enforcement and boundary behavior.
3. Cost calculation.
4. Stripe Checkout and subscription synchronization.
5. Stripe signature verification.
6. Stripe webhook deduplication.

BUILDLOG.md will honestly record AI assistance, incorrect suggestions, corrections, and verification.

---

## 15. Scope

### Core scope

* Two plans.
* Two usage types.
* One dummy billable endpoint.
* PostgreSQL persistence.
* Usage metering.
* Idempotency.
* Quota enforcement.
* Cost calculation.
* Usage rollup.
* Stripe Checkout in test mode.
* Stripe webhook verification and deduplication.
* Tenant isolation.
* Background job.
* Required documentation and evidence.

### Out of scope for the initial implementation

* Real AI model integration.
* Real payments.
* Invoicing.
* Proration.
* Overage billing.

Stretch goals will only be considered after all core requirements are complete.
