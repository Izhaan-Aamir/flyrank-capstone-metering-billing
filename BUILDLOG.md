# Build Log

This document records how the project was built, including where AI assistance was used, mistakes encountered, and corrections made.

The purpose is to keep the development process transparent and explainable.

---

# Stage 0 — Project Setup + Design

## Work Completed

* Created the dedicated capstone repository.
* Established the project directory structure.
* Reviewed the official capstone requirements.
* Chose Python + FastAPI.
* Chose PostgreSQL with Docker.
* Chose Stripe test mode for subscription integration.
* Designed the tenant, plan, subscription, usage-event, and Stripe-event concepts.
* Defined the staged implementation roadmap.
* Created initial documentation files.

## AI Assistance

AI was used as a learning and planning assistant to:

* break the capstone into manageable stages;
* explain backend architecture decisions;
* help design the initial database schema;
* suggest a development/testing sequence;
* provide PowerShell commands and Git checkpoints.

All implementation decisions were reviewed manually.

---

# Stage 1 — Database Foundation

## Goal

Create the real PostgreSQL persistence foundation before implementing the FastAPI application.

## Work Completed

### PostgreSQL

Created a Docker Compose PostgreSQL service using:

```text
postgres:16-alpine
```

Added:

* persistent Docker volume;
* PostgreSQL health check;
* local port mapping;
* migration directory mount.

### Database Migration

Created:

```text
migrations/001_initial_schema.sql
```

The migration creates:

```text
tenants
plans
subscriptions
usage_events
stripe_events
```

It also adds:

* primary keys;
* foreign keys;
* unique constraints;
* check constraints;
* indexes.

### Seed Script

Created:

```text
scripts/seed.py
```

The script seeds:

```text
Free plan
Pro plan

tenant-001
tenant-002

Free subscription for each tenant
```

The seed operation uses conflict handling so that it can be safely rerun.

---

## Initial Problem — Docker Daemon

### Problem

The first attempt to start PostgreSQL failed because the Docker Desktop daemon was not running.

### Correction

Started Docker Desktop and verified:

```powershell
docker info
```

Docker then reported a working Linux engine.

After that:

```powershell
docker compose up -d db
```

successfully created the PostgreSQL container.

### Lesson

When Docker commands fail before reaching the container, first verify that the Docker daemon/Desktop engine is running.

---

## Database Verification

Verified the PostgreSQL container:

```text
healthy
```

Verified the database tables:

```text
plans
stripe_events
subscriptions
tenants
usage_events
```

Verified the plan seed:

```text
free | Free | 1000  | 100000
pro  | Pro  | 10000 | 1000000
```

Verified tenant subscriptions:

```text
tenant-001 | Demo Tenant One | free | active
tenant-002 | Demo Tenant Two | free | active
```

---

## Python Virtual Environment

Created the local Python environment:

```powershell
python -m venv .venv
```

Activated it with:

```powershell
.\.venv\Scripts\Activate.ps1
```

Installed project dependencies from:

```text
requirements.txt
```

The virtual environment is excluded from Git.

---

## AI Assistance During Stage 1

AI was used to:

* explain PostgreSQL/Docker setup;
* create and explain the initial migration;
* create and explain the seed script;
* explain PostgreSQL constraints and indexes;
* diagnose the Docker daemon issue;
* explain the PostgreSQL pager behavior;
* provide verification queries;
* review the Stage 1 database structure.

The developer reviewed the resulting SQL and command output and verified the database directly.

---

# Corrections and Decisions

## Docker

Initial Docker startup failed because the Docker daemon was not running.

Corrected by starting Docker Desktop.

## PostgreSQL Pager

Some `psql` schema output opened in the terminal pager.

This was normal PostgreSQL behavior rather than a database error.

Using:

```powershell
psql -P pager=off
```

made verification output easier to read.

## Python Environment

A project-local `.venv` was added before continuing with Python application development.

The environment is intentionally not committed to Git.

---

# Stage 1 Completion

Stage 1 is complete when:

* PostgreSQL is running;
* the migration exists and has been applied;
* required tables exist;
* constraints and indexes exist;
* plans are seeded;
* tenants are seeded;
* subscriptions are seeded;
* the Python virtual environment is configured;
* evidence is recorded.

Next stage:

```text
Stage 2 — Core API + Tenant Handling
```

No Stage 2 application code is included in this Stage 1 checkpoint.
