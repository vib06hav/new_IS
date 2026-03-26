# Backend Handoff

## Final Backend Contract

### Statuses
- `UPLOADED`
- `PROCESSING`
- `READY`
- `FAILED`
- `ASSIGNED`
- `DRAFT`
- `PUBLISHED`

### Core Tables
- `users`
- `applications`
- `canonical_records`
- `assignments`
- `drafts`

### Endpoints

#### Auth
- `POST /auth/register`
- `POST /auth/login`

#### Admin
- `POST /applications/upload`
- `GET /applications`
- `GET /applications/{id}`
- `POST /applications/{id}/retry`
- `POST /applications/{id}/assign`
- `PUT /applications/{id}/assign`
- `GET /assignments`
- `GET /users/interviewers`
- `DELETE /users/{id}`

#### Interviewer
- `GET /me/applications`
- `POST /applications/{id}/generate`
- `POST /applications/{id}/publish`

## Response Rules
- Admin detail returns canonical Pages 1-3 once available.
- Admin detail returns Pages 4-5 only after publish.
- Interviewer detail returns canonical Pages 1-3 and the latest draft when assigned.
- Lists expose assignment/interviewer summaries, not raw internal persistence details.

## Migration / Tooling Notes
- Inside Docker/Compose, the app uses `.env` `DATABASE_URL` with host `db`.
- Host-side Alembic should be run through the API container because the Docker-internal hostname is not resolvable from Windows host tooling:

```powershell
docker compose run --rm --no-deps api alembic upgrade head
docker compose run --rm --no-deps api alembic current
```

## Non-Goals
- No real frontend implementation.
- No MinIO migration yet; current file storage remains path-based.
- No attempt to preserve old `synthesis_records` semantics.
