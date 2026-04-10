# AG Interview Standardiser

Single-repo application for the interview standardisation system.

## Repo Layout

- `app/`: FastAPI backend
- `frontend/`: Next.js frontend
- `alembic/`: database migrations
- `tests/`: backend tests
- `evals/`: evaluation fixtures and scripts
- `Docs/`: project documentation
- `scripts/`: helper scripts

`frontend/` is part of this same repository. It is not a separate Git repo.

## Run Locally

Backend stack:

```powershell
docker compose up --build
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

## Environment Files

- Copy `.env.example` to `.env`
- Copy `frontend/.env.example` to `frontend/.env.local`
