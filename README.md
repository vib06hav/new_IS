# AG Interview Standardiser

Single-repo application for the interview standardisation system.

This repo contains:

- `app/`: FastAPI backend
- `frontend/`: Next.js frontend
- `alembic/`: database migrations
- `tests/`: backend tests
- `evals/`: evaluation fixtures and scripts
- `Docs/`: project documentation
- `scripts/`: helper scripts

`frontend/` is part of this same repository. It is not a separate Git repo.

## What A New Person Needs

If someone has only VS Code or Antigravity on a new Windows machine, they still need to install the tools below before this project can run.

Install these first:

1. `Git`
2. `Docker Desktop`
3. `Node.js LTS`
4. `VS Code` optional, but helpful

Notes:

- `npm` and `npx` come with `Node.js`. Do not install `npx` separately.
- `docker compose` comes with modern `Docker Desktop`.
- This project uses Docker for the backend stack and OpenRouter for LLM calls.

## Recommended Windows Setup

Install in this order:

1. Install Git
   Download and install Git for Windows.

2. Install Docker Desktop
   During setup, enable WSL2 integration if Docker asks.

3. Install Node.js LTS
   This gives you `node`, `npm`, and `npx`.

4. Restart the machine if Docker or Node asks you to.

## Verify Installs

Open PowerShell and run:

```powershell
git --version
docker --version
docker compose version
node --version
npm --version
npx --version
```

If all of those print versions, the machine is ready.

## Clone The Repo

In PowerShell:

```powershell
cd $HOME\Desktop
git clone https://github.com/vib06hav/new_IS.git AG_InterviewStandardiser
cd AG_InterviewStandardiser
```

You can also open this folder in VS Code:

```powershell
code .
```

## Create Environment Files

Create the backend env file:

```powershell
Copy-Item .env.example .env
```

Create the frontend env file:

```powershell
Copy-Item frontend\.env.example frontend\.env.local
```

## Edit `.env`

Open `.env` and set:

- a real `JWT_SECRET`
- your real `OPENROUTER` API key in `LLM_API_KEY`
- the OpenRouter model you want in `LLM_MODEL_NAME`

Here is a working starter template you can paste into `.env`:

```env
DATABASE_URL=postgresql+psycopg2://postgres:postgres_password@db:5432/ag_db
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
JWT_SECRET=this-is-a-local-dev-secret-change-me-12345
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
SESSION_COOKIE_NAME=agis_session
SESSION_COOKIE_SAMESITE=lax
CSRF_COOKIE_NAME=agis_csrf
CSRF_HEADER_NAME=X-CSRF-Token
CSRF_TRUSTED_ORIGINS=
LLM_PROVIDER=openrouter
LLM_ENDPOINT=https://openrouter.ai/api/v1/chat/completions
LLM_MODEL_NAME=openai/gpt-4.1-mini
LLM_API_KEY=sk-or-v1-your-real-openrouter-key
BRAINTRUST_API_KEY=
LLM_TIMEOUT_SECONDS=60
LLM_TEMPERATURE=0.0
LLM_JSON_MODE=true
LLM_PAYLOAD_MODE=full
UPLOAD_DIRECTORY=/app/uploads
MAX_UPLOAD_SIZE_MB=10
APP_ENV=development
LOG_LEVEL=DEBUG
DEV_BOOTSTRAP_ADMIN=true
DEV_ADMIN_EMAIL=admin@example.com
DEV_ADMIN_PASSWORD=AdminPass123!
DEV_ADMIN_NAME=Local Admin
LLM_DISABLE_LIVE_CALLS=false
```

Replace:

```env
JWT_SECRET=<set-a-strong-random-secret-at-least-32-characters-long>
LLM_PROVIDER=openrouter
LLM_ENDPOINT=https://openrouter.ai/api/v1/chat/completions
LLM_MODEL_NAME=<your-openrouter-model-slug>
LLM_API_KEY=<your-openrouter-api-key>
```

With something real, for example:

```env
JWT_SECRET=this-is-a-local-dev-secret-change-me-12345
LLM_PROVIDER=openrouter
LLM_ENDPOINT=https://openrouter.ai/api/v1/chat/completions
LLM_MODEL_NAME=openai/gpt-4.1-mini
LLM_API_KEY=sk-or-v1-your-real-openrouter-key
```

Important:

- `JWT_SECRET` must be at least 32 characters long.
- Do not leave placeholder values in place.
- `LLM_API_KEY` must be your real OpenRouter key.
- `LLM_PROVIDER` should stay `openrouter`.

## Easiest Local Admin Setup

If you want the app to create an admin user automatically on startup in development, set these in `.env`:

```env
DEV_BOOTSTRAP_ADMIN=true
DEV_ADMIN_EMAIL=admin@example.com
DEV_ADMIN_PASSWORD=AdminPass123!
DEV_ADMIN_NAME=Local Admin
```

This is the easiest setup for a first-time user.

## Start The Backend Stack

From the repo root:

```powershell
docker compose up --build
```

This starts:

- the API
- PostgreSQL

When it works, the backend should be available at:

- `http://localhost:8000`
- health check: `http://localhost:8000/health`

## Start The Frontend

Open a second PowerShell window.

Run:

```powershell
cd $HOME\Desktop\AG_InterviewStandardiser\frontend
npm install
npm run dev
```

When it works, the frontend should be available at:

- `http://localhost:3000`

The frontend is configured to call:

- `http://localhost:8000`

through:

- `frontend/.env.local`

## First Login

If you enabled:

- `DEV_BOOTSTRAP_ADMIN=true`

then use the admin credentials you put in `.env`.

Admin login page:

- `http://localhost:3000/admin/login`

Interviewer login page:

- `http://localhost:3000/interviewer/login`

## Full First-Time Run Checklist

Use this exact order:

1. Install `Git`
2. Install `Docker Desktop`
3. Install `Node.js LTS`
4. Clone the repo
5. Copy `.env.example` to `.env`
6. Copy `frontend/.env.example` to `frontend/.env.local`
7. Edit `.env` and set a valid `JWT_SECRET`
8. Set `LLM_API_KEY` to your OpenRouter key
9. Set `LLM_MODEL_NAME` to the OpenRouter model you want
10. Optionally enable `DEV_BOOTSTRAP_ADMIN=true`
11. Run `docker compose up --build`
12. In a new terminal run `cd frontend`
13. Run `npm install`
14. Run `npm run dev`
15. Open `http://localhost:3000`

## Useful Commands

Run backend stack:

```powershell
docker compose up --build
```

Stop backend stack:

```powershell
docker compose down
```

Start frontend:

```powershell
cd frontend
npm install
npm run dev
```

Run backend tests:

```powershell
pytest
```

Run frontend production build:

```powershell
cd frontend
npm run build
```

## Manual Admin Bootstrap

If automatic dev bootstrap is disabled, you can create an admin manually:

```powershell
python scripts/bootstrap_admin.py --name "Local Admin" --email "admin@example.com" --password "AdminPass123!"
```

This should be run from the repo root.

## Seed A Real Published Final Report

There is a reproducible seed for one fully completed final artifact that frontend work can use as a stable reference.

What this seed gives you:

- one real application record in the live dev database
- real Pages 1-3 review package data
- real final Pages 4-5 report data
- signal highlights and annotations in the writing and evidence views
- unassigned-by-default final artifact that works in any local environment
- a source PDF copied into the live uploads directory

This is meant for frontend development when someone needs to see the current published/interviewer behavior end to end instead of working only from design-lab mocks.

### Seed Command

Run this from the repo root after `docker compose up --build` is already running:

```powershell
docker exec ag_interviewstandardiser-api-1 python scripts/seed_dummy_published_report.py
```

This command is idempotent for the same seeded application ID. Running it again refreshes the same record instead of creating a new random one.

By default this creates a `COMPLETE` final artifact with no interviewer assignment.

If you want to test the interviewer-assigned flow too, pass an interviewer name or email explicitly:

```powershell
docker exec ag_interviewstandardiser-api-1 python scripts/seed_dummy_published_report.py --interviewer vib
```

### What It Seeds

The script creates or updates:

- application UUID: `11111111-1111-1111-1111-111111111111`
- display ID: `Dummy App (5)_v8_filled`
- default status: `COMPLETE`
- default interviewer state: unassigned
- final report version: `ROS_v1`

If `--interviewer <name-or-email>` is provided, the same artifact is switched into:

- status: `ASSIGNED`
- interviewer: the matched or created interviewer user

Source assets used by the seed:

- canonical data: `tests/pipeline_stages/11_canonical_assembled.json`
- final artifact data: `tests/stage17_fake_llm_output/09_final_ros.json`
- source PDF: `tests/pdfs/Dummy App (5)_v8_filled.pdf`

### Routes To Open

After seeding, use these routes to inspect the real current behavior:

- admin application detail:
  `http://localhost:3000/admin/applications/11111111-1111-1111-1111-111111111111`
- design-lab visual reference:
  `http://localhost:3000/design-lab/published-report`

If you seed with `--interviewer <name-or-email>`, you can also open:

- interviewer application detail:
  `http://localhost:3000/interviewer/applications/11111111-1111-1111-1111-111111111111`

### When To Use Which Route

Use the real application routes when:

- you are fixing production/frontend behavior
- you need to test the actual admin or interviewer shells
- you want to verify real report highlighting and assignment behavior

Use the default unassigned seed when:

- you need a universal final artifact any teammate can create
- you are mostly working on final-report rendering in admin flows
- you do not want setup to depend on a local interviewer account already existing

Use the optional `--interviewer` seed when:

- you are specifically working on interviewer-shell behavior
- you need the assigned/interviewer route
- you want to test hide/review interactions from the interviewer side

Use the design-lab route when:

- you only want the visual sandbox reference
- you are comparing presentation ideas quickly
- you do not need the actual backend-driven route context

### Modular Frontend Workflow

For a frontend contributor, the smallest useful workflow is:

1. Start the backend with `docker compose up --build`
2. Start the frontend with `cd frontend` then `npm install` and `npm run dev`
3. Seed the final artifact with:
   `docker exec ag_interviewstandardiser-api-1 python scripts/seed_dummy_published_report.py`
4. Open:
   `http://localhost:3000/admin/applications/11111111-1111-1111-1111-111111111111`
5. Make frontend changes against that real final report

If interviewer-flow work is needed too:

6. Re-run the seed with an explicit interviewer:
   `docker exec ag_interviewstandardiser-api-1 python scripts/seed_dummy_published_report.py --interviewer vib`
7. Open:
   `http://localhost:3000/interviewer/applications/11111111-1111-1111-1111-111111111111`

### Important Note About Universality

The seed script is on `main`, so any teammate can use it.

The seeded database record itself is not automatically shared across every environment. A teammate will only see the seeded artifact if they run the seed command in their own local or shared environment database.

So:

- the setup is universal
- the seeded data is reproducible
- but each environment must run the seed once

## Current Limitation

This project is not yet true one-click setup for a blank machine because:

- backend uses Docker
- frontend still runs through local Node.js
- OpenRouter requires a real API key in `.env`

If you want, the next improvement should be:

- dockerize the frontend too
- reduce startup to one command
