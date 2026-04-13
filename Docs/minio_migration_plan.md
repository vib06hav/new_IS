# MinIO Migration Plan

## Purpose

This document defines the initial MinIO migration for AG Interview Standardiser and the follow-up phases that should come after the first asset-storage rollout.

The immediate goal is not just to "add MinIO for PDFs". The real goal is to introduce a proper asset storage layer so the application stops depending on machine-local filesystem paths for important user content.

This is high-value now because:

- source PDFs are core application assets
- current storage is tied to local disk and container state
- profile image upload UI already exists conceptually but is blocked by missing storage infrastructure
- future async/background processing will be much cleaner once asset storage is abstracted

## Current State

Today the application stores uploaded PDFs directly on local disk:

- uploads are written to `UPLOAD_DIRECTORY`
- `Application.file_path` stores a raw filesystem path
- source PDF download reads directly from local disk
- deletion removes files with `os.remove`
- retry and deterministic processing reuse the same stored local path
- seed scripts copy PDFs into the local upload directory

This works for local development, but it creates architectural limits:

- uploaded assets are tied to one server/container filesystem
- storage is not portable across environments
- storage behavior is not abstracted behind a service boundary
- profile image uploads cannot be implemented cleanly without inventing a second asset strategy
- future workers would still depend on local path assumptions

## Target State

The target state is an application asset storage layer backed by MinIO.

MinIO will serve as an S3-compatible object store for binary assets such as:

- application source PDFs
- admin profile images
- interviewer profile images
- future generated exports and downloadable artifacts

The backend will own all storage interactions. Frontend clients will continue to call backend APIs rather than talking to MinIO directly.

### Core Design Principle

Do not spread MinIO-specific calls across routes, scripts, and services.

Instead:

1. Introduce a storage abstraction layer in the backend.
2. Provide two implementations:
   - local filesystem backend
   - MinIO backend
3. Route all asset operations through that abstraction.

This keeps the app simple during rollout and lets local mode remain available when needed.

## Phase 1 Scope

Phase 1 is the initial MinIO migration.

It should cover:

- backend storage abstraction
- MinIO configuration and local development setup
- source PDF storage through the abstraction
- source PDF download through the abstraction
- source PDF deletion through the abstraction
- seed script support through the abstraction
- profile image support in the storage design
- backend support for profile image upload and retrieval if feasible in the same pass

Phase 1 should not try to do everything at once.

It should not include:

- direct browser uploads to MinIO
- presigned URLs
- background worker migration
- full artifact storage migration
- aggressive schema renaming if that slows delivery
- CDN integration

## Recommended Phase 1 Architecture

### 1. Storage Abstraction

Create a backend storage service responsible for:

- saving uploads
- deleting objects
- opening asset streams for download
- materializing an object into a temporary local file when parser code needs a file path
- returning stable storage keys

The abstraction should be generic, not PDF-specific.

It should support multiple asset classes:

- `applications/source-pdfs`
- `profiles/users`
- future `reports/exports`

### 2. Storage Backends

Implement:

- `LocalStorageBackend`
- `MinioStorageBackend`

Selection should be configuration-driven, for example:

- `STORAGE_BACKEND=local`
- `STORAGE_BACKEND=minio`

This keeps rollout safer because the application can still run in local mode while MinIO support is introduced.

### 3. Object Key Strategy

Use predictable object keys. Recommended examples:

- `applications/{application_id}/source.pdf`
- `profiles/users/{user_id}/avatar.jpg`
- `reports/{application_id}/exports/{artifact_name}`

This gives:

- clean grouping by domain
- easier deletion logic
- easier debugging and inspection
- room for future lifecycle policies

### 4. Parser Compatibility

The deterministic parser and PDF tooling still expect a local file path.

Therefore, phase 1 should not attempt to parse directly from object storage.

Instead:

1. The canonical source PDF lives in MinIO.
2. When processing is needed, the backend downloads the object to a temporary local file.
3. The parser uses that temp file path.
4. The temp file is removed after use.

This is the safest bridge from current design to future distributed processing.

## Data Model Strategy

### Initial Strategy

For phase 1, it is acceptable to preserve the current `Application.file_path` column temporarily and repurpose its meaning.

In practice, its value would stop being a literal machine path and become a storage locator or object key.

This is acceptable only as a transitional choice if it reduces migration friction.

### Preferred Long-Term Strategy

The preferred future state is:

- rename `Application.file_path` to `source_pdf_key` or `storage_key`

This should happen after phase 1 stabilizes, not before, unless the implementation cost is very low.

### User/Profile Asset Fields

To support profile images properly, the `User` model will likely need asset fields such as:

- `profile_image_key`
- optionally `profile_image_content_type`
- optionally `profile_image_updated_at`

The document does not require the exact final schema now, but it does require that profile images be designed as first-class assets from the start.

## API and Flow Changes

### Application Source PDFs

The following flows should move to the storage abstraction:

- upload application PDF
- validate stored PDF
- run deterministic pipeline using a materialized temp file
- fetch source PDF for admin/interviewer views
- delete application queue items
- delete full applications
- retry failed processing
- seed dummy published report

### Profile Images

Profile image support should use the same storage abstraction rather than a separate path.

The intended behavior is:

- image upload endpoint saves asset in object storage
- user record stores the object key
- profile retrieval endpoint returns the image via backend
- later phases may support image replacement and cleanup

This ensures the current dead-end UI path becomes implementable on top of the same asset layer.

## Configuration Additions

Phase 1 should introduce storage-specific settings such as:

- `STORAGE_BACKEND`
- `MINIO_ENDPOINT`
- `MINIO_ACCESS_KEY`
- `MINIO_SECRET_KEY`
- `MINIO_BUCKET`
- `MINIO_SECURE`

Optional later settings may include:

- `MINIO_REGION`
- `MINIO_PUBLIC_BASE_URL`
- `MINIO_PRESIGNED_URL_EXPIRY_SECONDS`

The `.env.example`, local docs, and Docker Compose setup should be updated so MinIO local development is reproducible.

## Local Development Setup

Phase 1 should add MinIO to local infrastructure so the team can develop and test the storage layer consistently.

Recommended local stack additions:

- MinIO server container
- console/admin UI container or built-in console exposure
- bucket initialization step if necessary

This should be documented clearly enough that a new developer can run the full stack without inventing their own storage setup.

## Testing Expectations

Phase 1 is not complete without tests around the storage boundary.

At minimum, testing should cover:

- saving uploaded PDFs
- rejecting invalid PDF uploads as before
- retrieving source PDFs through backend routes
- deleting assets when queue items or applications are removed
- seed script behavior with the new storage layer
- local backend behavior
- mocked MinIO backend behavior

For profile images, testing should cover:

- allowed content types
- size constraints
- successful upload and retrieval
- replacement or removal behavior if implemented in phase 1

## Rollout Strategy

Recommended sequence:

1. Introduce storage abstraction with local backend first.
2. Switch application code to use the abstraction while still storing locally.
3. Add MinIO backend and config support.
4. Add MinIO service to local development.
5. Switch source PDF flows to object storage mode.
6. Add profile image support on top of the same abstraction.
7. Validate upload, retrieval, retry, and delete flows end to end.

This sequence keeps the migration controlled and avoids mixing architectural change with too many feature changes at once.

## Risks and Tradeoffs

### Added Infrastructure Complexity

MinIO adds a new service to local development and deployment.

This is acceptable because asset durability and portability are worth the added complexity.

### Transitional Naming Debt

Keeping `file_path` temporarily may be slightly misleading if it stores an object key instead of a real path.

This is acceptable as a short-term migration compromise, but should be cleaned up in a follow-up phase.

### Temp File Materialization

The parser will still need local temp files in phase 1.

This is not a flaw. It is a deliberate compatibility bridge that reduces migration risk.

### Scope Creep

It will be tempting to combine MinIO, background jobs, presigned URLs, and artifact migration into one large change.

That would increase risk significantly. Phase 1 should stay focused.

## Phase 1 Acceptance Criteria

Phase 1 should be considered complete when all of the following are true:

- application source PDFs are no longer dependent on permanent local server storage
- backend asset operations run through a storage abstraction
- MinIO-backed storage works in local development
- upload, source-PDF retrieval, retry, and deletion flows still work
- profile image uploads are unblocked architecturally and preferably implemented through the same asset layer
- documentation and environment setup are updated
- test coverage exists for the new storage boundary

## Follow-Up Roadmap

### Follow-Up 1: Store Generated Exports and Artifacts in MinIO

After source PDFs and profile images are stable, extend the same storage layer to generated artifacts such as:

- report exports
- downloadable packages
- future attachments or archival bundles

This avoids creating a split world where source assets use object storage but generated outputs still depend on local disk.

### Follow-Up 2: Background Processing Workers Pull PDFs from MinIO

Once storage is stable, move processing assumptions away from the API process.

Future workers should:

- receive an application ID or storage key
- fetch the PDF from MinIO
- materialize it to a worker-local temp file
- run deterministic and synthesis pipelines
- persist output normally

This is the natural next step before major async/background job adoption.

### Follow-Up 3: Presigned URLs for Direct File Serving

If direct file serving becomes desirable later, add presigned URL support.

This should remain optional in early phases because backend-mediated download is simpler and safer while the system is still evolving.

Use presigned URLs only when there is a real need such as:

- reducing backend bandwidth
- large file serving
- external sharing workflows

### Follow-Up 4: Rename `file_path` to `storage_key`

After the migration is stable, clean up the schema language.

Recommended rename:

- `Application.file_path` -> `Application.storage_key`

This makes the model truthful and avoids future confusion in API and service code.

If desired, profile image fields should use the same naming language from the start.

### Follow-Up 5: Image Normalization and Asset Hardening

Once image uploads are live, add quality and safety improvements such as:

- file type validation
- size limits
- resize/thumbnail generation
- metadata stripping where appropriate
- orphan cleanup on replacement

This is especially relevant for profile images because the current need is functional enablement first, polish second.

### Follow-Up 6: Asset Lifecycle Management

Introduce cleanup and lifecycle rules for:

- replaced profile images
- deleted applications
- obsolete exports
- failed uploads that left orphaned objects

This follow-up becomes more important as stored asset volume grows.

### Follow-Up 7: Observability and Operational Guardrails

Add monitoring around:

- upload failures
- MinIO connectivity failures
- asset retrieval failures
- worker fetch failures
- cleanup job outcomes

This should happen before the storage layer becomes heavily relied on in production workflows.

## Recommended Order After Phase 1

Recommended follow-up order:

1. generated exports/artifacts in MinIO
2. background workers pulling PDFs from MinIO
3. schema cleanup from `file_path` to `storage_key`
4. image normalization and asset hardening
5. presigned URLs if product needs justify them
6. lifecycle management and observability expansion

## Final Recommendation

MinIO should be implemented as the foundation of a general asset-storage layer, not as a narrow PDF-only patch.

That approach gives the highest return because one architectural change unlocks:

- durable source PDF storage
- portable deployment behavior
- cleaner future async processing
- real profile image uploads for admin and interviewer accounts
- a path for storing future exports and binary artifacts consistently

Phase 1 should stay focused, but the design should explicitly leave room for the follow-up roadmap documented here.
