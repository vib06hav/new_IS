# Production Deployment Guide — Vercel Frontend + VPS Backend

## What Was Fixed (Code Changes Already Applied)

| # | Severity | File | Problem | Fix Applied |
|---|----------|------|---------|-------------|
| 1 | **High** | `.env.production.example` + `.env.production` | `WORKOS_REDIRECT_URI` pointed to `api.example.com/auth/callback`. WorkOS redirects the **browser** there, setting the session cookie on the backend domain — which Vercel's frontend origin can never read. | Changed to `https://<vercel-domain>/api/auth/callback`. The `/api/*` Vercel rewrite proxies this to the backend, so the **cookie is set on the Vercel origin**. |
| 2 | **High** | `.env.production.example` + `.env.production` | `MINIO_SECURE=true` but the Docker network uses plain HTTP (`http://minio:9000`). All uploads/downloads would fail with TLS errors. | Set to `MINIO_SECURE=false`. |
| 3 | **Medium** | `.env.production.example` | `ENABLE_BACKGROUND_WORKERS=false` comment was misleading — made it look like job processing was off, but `docker-compose.prod.yml` always starts the `worker` container. | Added an explanatory comment clarifying that `worker` container = the actual job processor, this flag only governs the API process. |
| 4 | **Medium** | `.env.production.example` + `.env.production` | `BACKEND_PUBLIC_URL` is a dead variable — nothing in the repo reads it. `frontend/next.config.ts` reads `BACKEND_API_URL`. | Replaced with `BACKEND_API_URL`. |
| 5 | **Extra** | `.env.production` | `DATABASE_URL` still had the placeholder password instead of the real `POSTGRES_PASSWORD`. | Fixed to use the actual password. |
| 6 | **Extra** | `.env.production` | `JWT_ALGORITHM` was missing — `config.py` requires it and crashes startup without it. | Added `JWT_ALGORITHM=HS256`. |

---

## Architecture Overview

```
Browser
  │
  ├─ GET /admin/login  ──► Vercel Edge (frontend)
  ├─ GET /api/*        ──► Vercel Rewrite ──► VPS backend (FastAPI @ api.yourdomain.com)
  │
  └─ Auth flow:
       1. Browser → vercel.app/api/auth/login?portal=admin
       2. Vercel rewrites → api.yourdomain.com/auth/login
       3. Backend → redirect to WorkOS
       4. WorkOS → redirect to vercel.app/api/auth/callback  ← MUST be Vercel origin
       5. Vercel rewrites → api.yourdomain.com/auth/callback
       6. Backend sets session cookie on vercel.app origin ✓
       7. Backend → redirect to vercel.app/admin/reports
```

> [!IMPORTANT]
> The `WORKOS_REDIRECT_URI` **must** point to `https://<vercel-domain>/api/auth/callback`.  
> Never point it to the raw backend domain — the cookie would be set on the wrong origin.

---

## VPS Setup Runbook

### 1. Provision Your VPS

- Minimum: 2 vCPU, 4 GB RAM (for the full stack: API + worker + Postgres + Redis + MinIO + Caddy)
- Ubuntu 22.04 LTS recommended
- Open ports: 80, 443

### 2. Install Docker

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Log out and back in for group membership to take effect
docker --version
docker compose version
```

### 3. Clone the Repo

```bash
git clone <your-repo-url> /opt/ag-is
cd /opt/ag-is
```

### 4. Configure `.env.production`

Fill in these values before deploying:

```bash
# Required: Your actual domain
API_DOMAIN=api.yourdomain.com
FRONTEND_ORIGIN=https://your-project.vercel.app
BACKEND_API_URL=https://api.yourdomain.com   # Also set in Vercel env vars!
CORS_ALLOWED_ORIGINS=https://your-project.vercel.app
TRUSTED_HOSTS=api.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://your-project.vercel.app

# Required: Set your actual Postgres password
POSTGRES_PASSWORD=<generate-strong-password>
DATABASE_URL=postgresql+psycopg2://postgres:<same-password>@db:5432/ag_db

# Required: WorkOS — MUST use /api/auth/callback
WORKOS_REDIRECT_URI=https://your-project.vercel.app/api/auth/callback

# Required: Your real admin email
FOUNDER_ADMIN_EMAIL=you@yourdomain.com
```

> [!CAUTION]
> Double-check `MINIO_SECURE=false` is set. The Docker-internal MinIO uses plain HTTP — `true` will break all file operations.

### 5. Configure Caddyfile

The existing `Caddyfile` is already correct — it just needs your domain to match `API_DOMAIN`:

```caddy
api.yourdomain.com {
    encode gzip zstd
    reverse_proxy api:8000
}
```

Caddy auto-provisions TLS via Let's Encrypt. Your `API_DOMAIN` env var feeds into `{$API_DOMAIN}`.

### 6. Register WorkOS Redirect URI

In your [WorkOS Dashboard](https://dashboard.workos.com):
- Navigate to **Redirects**
- Add: `https://your-project.vercel.app/api/auth/callback`
- Remove any old `api.example.com` redirects

### 7. Deploy

```bash
cd /opt/ag-is
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

Check startup:

```bash
docker compose -f docker-compose.prod.yml logs -f api
docker compose -f docker-compose.prod.yml logs -f worker
```

Verify health:
```bash
curl https://api.yourdomain.com/health
# Expected: {"status":"ok","message":"...","coordination":"redis"}
```

---

## Vercel Setup

### 1. Import the Frontend

In the [Vercel dashboard](https://vercel.com/new):
- Select your repo
- Root directory: `frontend`
- Framework: Next.js (auto-detected)

### 2. Set Environment Variables (Build & Runtime)

| Variable | Value |
|----------|-------|
| `BACKEND_API_URL` | `https://api.yourdomain.com` |

> [!WARNING]
> `BACKEND_API_URL` is used at **build time** by `next.config.ts` to configure the rewrite destination. Set it before your first deploy and redeploy whenever the backend URL changes.

### 3. Deploy

Vercel auto-deploys on push to main. Trigger a manual redeploy if you just set env vars.

---

## DNS Configuration

| Record | Type | Value |
|--------|------|-------|
| `api.yourdomain.com` | A | `<your-vps-ip>` |

Caddy handles TLS automatically once DNS propagates.

---

## Post-Deploy Verification Checklist

- [ ] `curl https://api.yourdomain.com/health` returns `{"status":"ok"}`
- [ ] `docker compose logs api` shows no config errors
- [ ] `docker compose logs worker` shows worker polling loop
- [ ] Navigate to `https://your-project.vercel.app/admin/login` — click "Continue to sign in"
- [ ] WorkOS auth flow completes and redirects to `/admin/reports`
- [ ] Session cookie is present on the Vercel domain (DevTools → Application → Cookies)
- [ ] Upload a test PDF — verify it stores in MinIO (`docker exec -it <minio> mc ls local/ag-assets`)
- [ ] Trigger a pipeline job — verify worker picks it up in logs

---

## Remaining TODOs

> [!NOTE]
> These are **not** blocking for launch but should be addressed soon after.

1. **`FOUNDER_ADMIN_EMAIL` in `.env.production`** — currently `founder@example.com`. Update to your real email so the first admin account is created correctly.

2. **WorkOS API key** — currently `sk_test_*`. Switch to a production key (`sk_live_*`) in WorkOS dashboard before going live with real users.

3. **`TRUST_X_FORWARDED_FOR`** — currently `false`. If your VPS is behind a load balancer or Cloudflare proxy, set to `true` and populate `TRUSTED_PROXY_IPS` with the proxy IPs. Required for accurate rate limiting via `client_ip()`.

4. **MinIO external access** — MinIO is not exposed on any port in `docker-compose.prod.yml`. If you need direct browser access to stored files (e.g., profile image URLs), either expose MinIO port 9000 with Caddy TLS in front, or configure presigned URLs via the API. Currently file serving goes through the backend which is fine.

5. **Secrets rotation** — the JWT secret, MinIO keys, and WorkOS cookie password in `.env.production` are committed to the repo. Rotate them on the VPS and update the file, or move to a secrets manager.
