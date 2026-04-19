# Sellable

Multi-tenant AI operations platform for service businesses (roofing, HVAC,
plumbing, general contracting). It automates document compliance, answers
incoming phone calls with a Claude-powered voice assistant, and drives routine
customer follow-up from a single tenant dashboard.

## Features

- **Document automation** — upload PDFs, scans, or photos; OCR + Claude extract
  company, subcontractor, policy number, doc type, expiration, missing
  signatures, and a confidence score.
- **Expiration alerts** — scheduled 30 / 14 / 7 / 0-day alerts delivered by
  email or SMS via a Celery beat worker that dispatches every 5 minutes.
- **AI voice assistant** — answers inbound calls (Twilio `<Gather>` + Claude
  turn-by-turn), records the transcript, writes a summary, and auto-creates
  follow-up tasks.
- **Workflow automation** — reminder emails, SMS, internal tasks, and
  cross-tenant audit log on every mutation.
- **Multi-tenant SaaS** — per-company isolation via Postgres Row-Level
  Security, roles (owner / admin / staff), Stripe subscriptions, 14-day trial,
  self-service invites.

## Architecture

```
Next.js (Vercel) ──▶ FastAPI API (Render web)
                       ├──▶ Celery worker  (Render worker)
                       ├──▶ Celery beat    (Render worker)
                       ├──▶ Postgres 16    (Render managed DB, RLS per tenant)
                       ├──▶ Redis 7        (Render managed, cache + broker)
                       ├──▶ S3 / MinIO     (documents, call audio)
                       ├──▶ Claude API     (extraction, voice brain, summaries)
                       ├──▶ Twilio         (voice + SMS, TwiML <Gather> STT)
                       ├──▶ SendGrid       (email)
                       └──▶ Stripe         (subscriptions + billing portal)
```

## Repository Layout

```
backend/    FastAPI app, SQLAlchemy models, Alembic migrations, Celery workers
frontend/   Next.js 14 App Router dashboard + marketing site
infra/      Render + Vercel deploy manifests
.github/    CI workflows
```

## Local Development

Prerequisites: Docker + Docker Compose, Python 3.12, Node 20 + pnpm 9.

```bash
# 1. configure
cp .env.example .env

# 2. boot infra
docker compose up -d postgres redis minio

# 3. backend
cd backend
uv sync --all-extras
uv run alembic upgrade head
uv run uvicorn app.main:app --reload                # http://localhost:8000

# 4. worker + beat (separate shells)
uv run celery -A app.workers.celery_app.celery worker -l info
uv run celery -A app.workers.celery_app.celery beat   -l info

# 5. frontend
cd ../frontend && pnpm install && pnpm dev          # http://localhost:3000
```

OpenAPI docs: <http://localhost:8000/docs> · Liveness: `/healthz` · Readiness
(DB + Redis): `/readyz`

### Running checks

```bash
cd backend
uv run ruff check .
uv run mypy app
uv run pytest -q

cd ../frontend
pnpm lint && pnpm typecheck && pnpm build
```

## Production Deploy

### Backend + workers (Render)

1. Connect the repo to Render, then apply the blueprint:
   ```bash
   render blueprint apply infra/render.yaml
   ```
   This provisions `sellable-api` (web), `sellable-worker`, `sellable-beat`, a
   managed `sellable-redis`, and a managed `sellable-db` (Postgres 16).
2. Fill the `sellable-shared` env-var group with real values for
   `ANTHROPIC_API_KEY`, `STRIPE_*`, `TWILIO_*`, `SENDGRID_API_KEY`,
   `S3_*`, and `SENTRY_DSN`. `JWT_SECRET` auto-generates; `CORS_ALLOW_ORIGINS`
   and the public URLs are pinned in the blueprint.
3. Run Alembic on first deploy:
   ```bash
   render run alembic upgrade head -s sellable-api
   ```
   (The blueprint also sets `preDeployCommand: alembic upgrade head`, so
   subsequent deploys migrate automatically.)

### Frontend (Vercel)

Import the repo into Vercel with these settings (already encoded in
`infra/vercel.json`):

- Root directory: `frontend`
- Build: `pnpm build` · Install: `pnpm install --frozen-lockfile`
- Env: `NEXT_PUBLIC_API_URL=https://api.sellable.app`,
  `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=...`

### Third-party webhooks

- **Stripe** → `https://api.sellable.app/api/v1/webhooks/stripe`; subscribe to
  `customer.subscription.{created,updated,deleted}` and
  `checkout.session.completed`. Copy the signing secret into
  `STRIPE_WEBHOOK_SECRET`.
- **Twilio** → voice number webhook `https://api.sellable.app/api/v1/webhooks/twilio/voice`
  (POST), status callback `/api/v1/webhooks/twilio/voice/status`. Each tenant
  configures their purchased Twilio number via Settings → Company.

## Security

- Bcrypt(12) password hashing; JWT HS256 access (15 min) + refresh (30 d) in
  httpOnly cookies; tokens rotate on refresh.
- Postgres Row-Level Security on every tenant table; `app.current_tenant` is
  bound from the JWT on every request before any query runs.
- Stripe + Twilio webhook signature verification; rate limits per-IP (120/min)
  and per-tenant (600/min) in Redis.
- S3 server-side encryption + presigned POSTs only; uploads stream directly
  from the browser to S3.
- Structured JSON audit log (append-only) on every mutation; Sentry on both
  apps; JSON logs → stdout.

## Operations runbook

### On-call checks

- `GET /readyz` — returns 200 only when DB + Redis are both reachable. Render
  uses this for healthchecks.
- `celery -A app.workers.celery_app.celery inspect active` — verify workers
  are processing tasks.
- `render logs -s sellable-worker --tail 200` — scan for task failures.

### Common incidents

| Symptom | Likely cause | Fix |
|---|---|---|
| Alerts not sending | `sellable-beat` is down | Restart the beat worker; check `celery beat -l info` logs for scheduler errors |
| Upload stuck at `pending` | Celery worker down or OCR/Claude failing | Check `sellable-worker` logs; reprocess via `POST /api/v1/documents/{id}/reprocess` |
| 5xx on `/api/v1/auth/login` | DB connection pool exhausted | Inspect `pg_stat_activity`; scale API dynos; check `/readyz` |
| Stripe webhook signature fails | Wrong `STRIPE_WEBHOOK_SECRET` | Rotate in Stripe dashboard + Render env group |
| Twilio call says "sorry…" | Tenant missing `twilio_phone_number` or auth token wrong | Confirm the tenant's `twilio_phone_number` in Settings; verify Render env vars |

### DB migrations

Always deploy the migration with the code that needs it. `preDeployCommand`
runs `alembic upgrade head` before the new API container takes traffic, so
zero-downtime column adds are safe. For destructive changes, ship the
additive migration first, deploy, then ship the removal in a follow-up
release.

### Backups

Render managed Postgres provides daily snapshots with point-in-time restore
on the `standard` plan. Test restores quarterly to a staging DB.

## Phase roadmap

| Phase | Scope | Status |
|---|---|---|
| 1 | Architecture, schema, project scaffold | shipped |
| 2 | Auth, uploads, Claude extraction, alerts | shipped |
| 3 | Twilio voice assistant + call summaries | shipped |
| 4 | Next.js dashboard wired to backend APIs | shipped |
| 5 | Stripe subscriptions + billing portal | shipped |
| 6 | Production deploy, observability, runbook | shipped |
