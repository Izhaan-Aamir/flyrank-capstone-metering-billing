# Build Log

This document records the development process for the FlyRank AI Usage Metering & Billing Engine capstone.

The capstone encourages AI-assisted development but requires the developer to document where AI helped, where it was wrong, and what was changed.

---

# Stage 0 — Project Setup + Architecture Design

## Work completed

Created the dedicated capstone repository:

```text
flyrank-capstone-metering-billing
```

Established the project structure and documented the architecture before implementing the application.

Technology choices:

* Python
* FastAPI
* PostgreSQL
* Docker
* Docker Compose
* Stripe test mode
* pytest
* Git/GitHub

The design established:

* Free and Pro plans
* API-call and AI-token usage types
* tenant-based data ownership
* usage events
* idempotency strategy
* quota enforcement
* cost calculation
* Stripe Checkout
* Stripe webhooks
* background processing
* evidence-driven development

The project was intentionally divided into stages so each major area could be implemented and tested independently.

---

# Stage 1 — Database Foundation

## Work completed

Implemented the PostgreSQL foundation using Docker Compose.

Created:

```text
migrations/001_initial_schema.sql
scripts/seed.py
```

Database tables:

```text
tenants
plans
subscriptions
usage_events
stripe_events
```

Added:

* primary keys
* foreign keys
* uniqueness constraints
* usage validation constraints
* tenant-scoped idempotency uniqueness
* indexes for expected query paths

Seeded:

```text
Free plan
Pro plan
tenant-001
tenant-002
```

Both demo tenants initially use the Free plan.

## Development issue — Docker daemon

Initial attempt to start PostgreSQL failed because the Docker daemon was not running.

Observed problem:

```text
Docker daemon was unavailable.
```

Correction:

Started Docker Desktop and verified:

```powershell
docker info
```

After Docker Desktop was running:

```powershell
docker compose up -d db
```

successfully created and started the PostgreSQL container.

## Development issue — PostgreSQL pager

Some `psql` output opened in the terminal pager.

This was resolved by using:

```powershell
-P pager=off
```

when necessary.

## Python environment

Created a local Python virtual environment:

```text
.venv/
```

Installed project dependencies from:

```text
requirements.txt
```

The virtual environment and `.env` are ignored by Git.

---

# Stage 2 — Core API + Tenant Handling

## Work completed

Added the initial FastAPI application structure:

```text
app/
├── main.py
├── config.py
├── db.py
├── dependencies.py
├── repositories/
├── routes/
└── schemas/
```

Implemented:

* FastAPI application
* environment-based configuration
* PostgreSQL connection function
* tenant repository
* tenant dependency
* tenant response schema
* `/health`
* `/tenants/me`

The application now follows a basic layered structure:

```text
HTTP route
    ↓
dependency / validation
    ↓
repository
    ↓
database connection
    ↓
PostgreSQL
```

---

## Configuration issue — Missing DATABASE_URL

Initial attempt to start Uvicorn produced:

```text
pydantic_core.ValidationError

database_url
Field required
```

The cause was that the application expected:

```text
DATABASE_URL
```

from the local `.env` file, but the variable was not available.

Correction:

Created the local `.env` file using the development PostgreSQL connection:

```text
postgresql://capstone_user:change_me@localhost:5432/capstone_db
```

The distinction between `localhost` and the Docker service hostname `db` was important:

* FastAPI is currently running directly on Windows.
* PostgreSQL is running inside Docker.
* Therefore the host-side FastAPI application connects through `localhost:5432`.

After the correction, FastAPI started successfully.

---

## Tenant handling

Implemented tenant identification through:

```text
X-Tenant-Key
```

The dependency:

1. Checks whether the header exists.
2. Looks up the tenant.
3. Rejects unknown tenants.
4. Provides the resolved tenant to the route.

Current behavior:

```text
Missing header → 400
Unknown tenant → 404
Known tenant   → 200
```

The tenant repository joins:

```text
tenants
subscriptions
plans
```

so the API can return the tenant's current plan and limits.

---

# Automated Testing

Added:

```text
tests/test_tenants.py
```

Tests cover:

```text
health endpoint
tenant lookup
missing tenant header
unknown tenant
```

Also added:

```text
pytest.ini
```

to make the project root available to pytest.

---

## Testing issue — pytest could not import app

Initial command:

```powershell
pytest -q
```

failed during test collection:

```text
ModuleNotFoundError: No module named 'app'
```

The API itself could already be launched with:

```powershell
uvicorn app.main:app --reload
```

so the issue was specific to pytest's module import path.

Correction:

Created:

```text
pytest.ini
```

with:

```ini
[pytest]
pythonpath = .
```

After the correction:

```text
4 passed
```

---

## Test result

Final Stage 2 test execution:

```text
pytest -q

....                                                      [100%]

4 passed, 1 warning
```

The warning is a Starlette/FastAPI test-client deprecation warning concerning the current `httpx` integration. It did not cause test failure, so no dependency change was made at this checkpoint.

---

# AI Assistance

AI assistance was used throughout the project for:

* breaking the capstone into implementation stages
* explaining the requirements
* suggesting the database schema structure
* reviewing implementation decisions
* generating initial code drafts
* explaining PostgreSQL and Docker behavior
* diagnosing command-line and Python errors
* suggesting tests
* preparing documentation structure

The developer reviewed the generated code, executed the commands, inspected actual results, and corrected issues based on those results.

AI-generated suggestions were not treated as automatically correct.

Examples of corrections during development include:

1. Docker daemon needed to be started before PostgreSQL could run.
2. PostgreSQL host configuration needed to use `localhost` when FastAPI was running on Windows outside Docker.
3. Pytest required an explicit project-root Python path through `pytest.ini`.
4. The Starlette/httpx warning was recognized as a warning rather than incorrectly treating it as a test failure.

---

# Current Status

Completed:

```text
Stage 0 — Project Setup + Design
Stage 1 — Database Foundation
Stage 2 — Core API + Tenant Handling
```

Next:

```text
Stage 3 — Usage Metering + Idempotency
```

Stage 3 will introduce the actual billable usage path and the requirement that:

```text
same request + same idempotency key
→ exactly one usage event
```

Future stages will add quota enforcement, cost calculation, Stripe integration, background processing, final evidence, and submission cleanup.

---

# Development Principle

The project is being built incrementally.

A stage is treated as complete only after:

1. implementation exists,
2. the behavior is tested,
3. errors encountered during development are understood,
4. documentation reflects the actual state,
5. and a Git checkpoint is created.
