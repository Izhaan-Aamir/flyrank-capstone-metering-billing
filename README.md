# FlyRank Usage Metering & Billing Engine

A small, correctness-focused backend service for usage metering, quota enforcement, cost calculation, and Stripe test-mode subscription synchronization.

This project is being built as part of the FlyRank AI Backend Engineering internship capstone.

## Project Status

**Current stage: Stage 1 — Database Foundation completed**

Completed:

* Project structure and architecture design
* PostgreSQL database running through Docker Compose
* Initial database migration
* Tenant, plan, subscription, usage-event, and Stripe-event tables
* Database constraints and indexes
* Free and Pro plan seed data
* Two demo tenants
* Free subscriptions for both demo tenants
* Python virtual environment
* PostgreSQL seed script

Not implemented yet:

* FastAPI application
* Billable usage endpoint
* Idempotency handling at the API layer
* Quota enforcement
* Cost calculation
* Stripe Checkout
* Stripe webhook processing
* Background worker
* Automated test suite

These will be implemented incrementally in later stages.

---

## What This Service Will Do

The completed service will provide four core capabilities:

1. **Usage metering**

   * Record billable API calls and AI-token usage.
   * Attribute every usage event to a tenant.
   * Prevent duplicate metering through idempotency keys.

2. **Quota enforcement**

   * Compare current monthly usage plus requested usage against the tenant's plan.
   * Return `429 Too Many Requests` for exceeded usage quotas.
   * Return `402 Payment Required` where the plan/payment state requires an upgrade or payment.

3. **Cost calculation**

   * Calculate usage costs using integer-based money units.
   * Support API-call pricing.
   * Support AI token categories including input, cached input, output, and reasoning tokens.

4. **Stripe test-mode subscription integration**

   * Create a Pro Checkout flow.
   * Verify Stripe webhook signatures.
   * Deduplicate Stripe events.
   * Synchronize the tenant's subscription plan and status.

---

## Technology Stack

* Python
* FastAPI
* PostgreSQL
* Docker / Docker Compose
* psycopg
* Stripe test mode
* Stripe CLI
* pytest

The application is intentionally small. The capstone requires two plans, two usage types, and one dummy billable endpoint. AI token usage can be simulated; an actual AI model call is not required.

---

## Architecture

The planned architecture separates HTTP handling, business logic, and persistence.

```text
                         Client
                           |
                           v
                    +--------------+
                    |   FastAPI    |
                    |   HTTP/API   |
                    +--------------+
                           |
                           v
                    +--------------+
                    |   Services   |
                    | Billing Logic|
                    +--------------+
                           |
                           v
                    +--------------+
                    | Repositories |
                    | Data Access  |
                    +--------------+
                           |
                           v
                    +--------------+
                    | PostgreSQL   |
                    +--------------+
```

The database currently contains the persistence foundation for the future metering and billing services.

---

## Database

PostgreSQL runs through Docker Compose.

Current database tables:

```text
tenants
plans
subscriptions
usage_events
stripe_events
```

### `tenants`

Represents a customer organization.

Important fields:

* `id`
* `tenant_key`
* `name`
* `created_at`

`tenant_key` is unique.

### `plans`

Stores subscription plans and their monthly limits.

Current plans:

| Plan | API calls/month | AI tokens/month |
| ---- | --------------: | --------------: |
| Free |           1,000 |         100,000 |
| Pro  |          10,000 |       1,000,000 |

### `subscriptions`

Connects a tenant to a plan.

It also stores future Stripe identifiers and subscription status.

### `usage_events`

Stores individual billable usage records.

The table includes:

* tenant
* usage type
* quantity
* idempotency key
* input tokens
* cached input tokens
* output tokens
* reasoning tokens
* timestamps

The database enforces:

```text
(tenant_id, idempotency_key)
```

as a unique combination.

This provides the database-level foundation for exactly-once metering.

### `stripe_events`

Stores processed Stripe event IDs so repeated webhook deliveries can be ignored.

---

## Tenant Isolation

Every usage event references a tenant through a foreign key.

Subscriptions also belong to exactly one tenant.

This provides the database-level foundation for preventing one tenant's usage from being associated with another tenant.

Application-level tenant identification and authorization will be implemented in Stage 2.

---

## Local Setup

### 1. Clone the repository

```powershell
git clone <repository-url>
cd flyrank-capstone-metering-billing
```

### 2. Create the Python virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

The terminal should show:

```text
(.venv)
```

### 3. Install Python dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Create the local environment file

```powershell
Copy-Item .env.example .env
```

The real `.env` file must remain local and must not be committed to Git.

---

## Start PostgreSQL

Start the database:

```powershell
docker compose up -d db
```

Check its status:

```powershell
docker compose ps
```

The PostgreSQL container should report a healthy status.

---

## Apply the Database Schema

The initial migration is located at:

```text
migrations/001_initial_schema.sql
```

Docker Compose mounts the migration directory into PostgreSQL's initialization directory.

The migration creates:

```text
tenants
plans
subscriptions
usage_events
stripe_events
```

The PostgreSQL data is stored in a Docker volume so that restarting the container does not remove the database.

---

## Seed the Database

With the virtual environment activated:

```powershell
python scripts\seed.py --database-url "postgresql://capstone_user:change_me@localhost:5432/capstone_db"
```

The seed script creates or updates:

* Free plan
* Pro plan
* `tenant-001`
* `tenant-002`
* Free subscriptions for both tenants

The script is safe to run again because it uses conflict handling for existing records.

---

## Verify Seed Data

Check the plans:

```powershell
docker compose exec db psql -P pager=off -U capstone_user -d capstone_db -c "SELECT code, name, api_call_limit, ai_token_limit FROM plans ORDER BY code;"
```

Expected:

```text
 code | name | api_call_limit | ai_token_limit
------+------+----------------+---------------
 free | Free |           1000 |         100000
 pro  | Pro  |          10000 |        1000000
```

Check tenant subscriptions:

```powershell
docker compose exec db psql -P pager=off -U capstone_user -d capstone_db -c "SELECT t.tenant_key, t.name, p.code AS plan, s.status FROM subscriptions s JOIN tenants t ON t.id = s.tenant_id JOIN plans p ON p.id = s.plan_id ORDER BY t.tenant_key;"
```

Expected:

```text
 tenant_key |      name       | plan | status
------------+-----------------+------+--------
 tenant-001 | Demo Tenant One | free | active
 tenant-002 | Demo Tenant Two | free | active
```

---

## Current Database State

At the end of Stage 1:

```text
plans            = 2
tenants          = 2
subscriptions    = 2
usage_events     = 0
stripe_events    = 0
```

The zero usage and Stripe-event counts are expected because those features have not been implemented yet.

---

## Current Repository Structure

```text
flyrank-capstone-metering-billing/
│
├── app/
├── docs/
│   └── design.md
├── migrations/
│   └── 001_initial_schema.sql
├── scripts/
│   └── seed.py
├── tests/
├── worker/
│
├── .env.example
├── .gitignore
├── BUILDLOG.md
├── capstone.yaml
├── docker-compose.yml
├── Dockerfile
├── EVIDENCE.md
├── README.md
└── requirements.txt
```

The `.venv` directory is intentionally excluded from Git.

---

## Planned Build Stages

```text
Stage 0  Project Setup + Design             ✓
Stage 1  Database Foundation                ✓
Stage 2  Core API + Tenant Handling         →
Stage 3  Usage Metering + Idempotency
Stage 4  Quota Enforcement
Stage 5  Cost Calculation
Stage 6  Stripe Checkout
Stage 7  Stripe Webhooks + Subscription Sync
Stage 8  Background Worker
Stage 9  Testing + Evidence
Stage 10 README + BUILDLOG + capstone.yaml
Stage 11 Final Cleanup + GitHub Submission
```

---

## Limitations at Stage 1

This repository is **not yet a complete billing engine**.

In particular:

* The FastAPI application is not implemented yet.
* No billable API endpoint exists yet.
* Usage events are not created through an API yet.
* Quota enforcement is not implemented yet.
* Costs are not calculated yet.
* Stripe Checkout is not implemented yet.
* Stripe webhooks are not implemented yet.
* No background worker is implemented yet.
* Automated tests have not been completed yet.

The README will be updated as these capabilities are implemented.

---

## Security Notes

Secrets are stored through environment variables.

The real `.env` file must never be committed.

Stripe will use test mode only.

The repository should never contain:

```text
.env
.venv/
Stripe secret keys
Stripe webhook secrets
database credentials
```

---

## License

This project is an internship capstone project.
