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
- This project currently assumes Docker for the backend stack.

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

Open `.env` and set a real JWT secret.

Replace:

```env
JWT_SECRET=<set-a-strong-random-secret-at-least-32-characters-long>
```

With something real, for example:

```env
JWT_SECRET=this-is-a-local-dev-secret-change-me-12345
```

Important:

- `JWT_SECRET` must be at least 32 characters long.
- Do not leave placeholder values in place.

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
- Ollama

When it works, the backend should be available at:

- `http://localhost:8000`
- health check: `http://localhost:8000/health`

## Important Ollama / GPU Note

The current `docker-compose.yml` includes an `ollama` container with an NVIDIA GPU reservation.

That means:

- if the machine has Docker and NVIDIA GPU support configured, this is the intended path
- if the machine does not have compatible NVIDIA GPU support, the current Docker setup may fail

So the safest statement is:

- this repo is easiest to run on a machine with Docker Desktop and working NVIDIA container support

If the machine does not have that, this repo may need a follow-up packaging change to make Ollama optional.

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
8. Optionally enable `DEV_BOOTSTRAP_ADMIN=true`
9. Run `docker compose up --build`
10. In a new terminal run `cd frontend`
11. Run `npm install`
12. Run `npm run dev`
13. Open `http://localhost:3000`

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

## Current Limitation

This project is not yet true one-click setup for a blank machine because:

- backend uses Docker
- frontend still runs through local Node.js
- current Ollama setup assumes NVIDIA GPU container support

If you want, the next improvement should be:

- dockerize the frontend too
- make Ollama optional
- reduce startup to one command

