# chore-tracker-

Multi-tenant AI operations platform for service businesses (roofing, HVAC,
plumbing, general contracting). It automates document compliance, answers
incoming phone calls with a Claude-powered voice assistant, and drives routine
customer follow-up from a single tenant dashboard.

> **Status:** Phase 1 scaffolding only. Business logic is implemented in
> subsequent phases (see `/root/.claude/plans/you-are-a-senior-dynamic-aho.md`).

## Feature Summary

- **Document automation** — upload PDFs, scans, or photos; OCR + Claude extract
  company, subcontractor, policy number, doc type, expiration, missing
  signatures, and a confidence score.
- **Expiration alerts** — automatic email/SMS at 30 / 14 / 7 / 0 days.
- **AI voice assistant** — answers inbound calls, schedules appointments,
  answers invoice / status questions, transfers emergencies, and logs every
  transcript + summary.
- **Workflow automation** — reminder emails, SMS, internal tasks, escalations,
  and daily activity summaries.
- **Multi-tenant SaaS** — per-company isolation (Postgres RLS), roles
  (owner / admin / staff), Stripe subscriptions, 14-day trial, onboarding.

## Architecture

```
Next.js (Vercel) ──▶ FastAPI + Celery (Render/Railway)
                       ├─ Postgres 16 (Row-Level Security per tenant)
                       ├─ Redis (cache, rate limit, Celery broker)
                       ├─ S3 / MinIO (documents, call audio)
                       ├─ Claude API (extraction, voice brain, summaries)
                       ├─ Deepgram (STT / TTS)
                       ├─ Twilio (voice + SMS)
                       ├─ SendGrid (email)
                       └─ Stripe (subscriptions + billing portal)
```

## Repository Layout

```
backend/    FastAPI app, SQLAlchemy models, Alembic migrations, Celery workers
frontend/   Next.js 14 App Router dashboard + marketing site
infra/      Render + Vercel deploy manifests (Terraform optional later)
.github/    CI workflows
```

## Local Development

Prerequisites: Docker, Docker Compose, Python 3.12, Node 20 + pnpm 9.

```bash
# 1. clone + configure
cp .env.example .env

# 2. boot the stack
docker compose up -d postgres redis minio
cd backend && uv sync --all-extras
uv run alembic upgrade head
uv run uvicorn app.main:app --reload     # http://localhost:8000

# 3. frontend
cd ../frontend && pnpm install && pnpm dev  # http://localhost:3000

# 4. worker (separate shell)
cd backend && uv run celery -A app.workers.celery_app.celery worker -l info
```

OpenAPI docs: <http://localhost:8000/docs>
Health check: <http://localhost:8000/healthz>

## Phase Roadmap

| Phase | Scope | Status |
|-------|-------|--------|
| 1 | Architecture, schema, project structure | **this commit** |
| 2 | Backend: auth, uploads, AI processing, alerts | pending |
| 3 | Voice: Twilio + Deepgram + Claude pipeline | pending |
| 4 | Frontend dashboard, components, pages | pending |
| 5 | Stripe subscriptions, onboarding, billing portal | pending |
| 6 | Production deploy, scaling, runbook | pending |

## Security Principles

Bcrypt password hashing, JWT RS256 with short-lived access + rotating refresh
tokens, per-IP and per-tenant Redis rate limits, S3 server-side encryption,
Stripe + Twilio webhook signature verification, Postgres RLS on every tenant
table, structlog JSON audit log on every mutation, Sentry on both apps.
