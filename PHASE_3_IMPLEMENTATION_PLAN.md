# Phase 3 Implementation Plan

## Direction

Phase 3 should start with a regeneration-first RAG system. The goal is to make question regeneration semantically aware of past high-quality questions and ratings, while preserving the current full-generation behavior until the retrieval layer is proven stable.

This gives us a credible production architecture story without taking a chainsaw to the existing pipeline:

- Postgres remains the source of truth for applications, generated questions, ratings, and snapshots.
- Qdrant becomes the semantic retrieval layer for question examples.
- Celery handles indexing and backfill work asynchronously.
- Regeneration gets RAG context first.
- Full initial generation adopts the same retrieval service later, after regeneration is validated.

## Phase 3A Scope: Regeneration RAG

### Goals

- Replace the current lexical token-vector retrieval path for question regeneration with Qdrant semantic retrieval.
- Use past rated/generated questions to guide regeneration quality.
- Persist retrieval snapshots so every regenerated question can be explained and audited.
- Keep graceful fallback to the existing lexical retrieval if Qdrant is unavailable or empty.
- Avoid changing the current initial question generation behavior in this subphase.

### Non-Goals

- No D2C changes.
- No full-generation RAG yet.
- No LangChain or LangGraph unless a concrete need appears.
- No rewrite of report generation.
- No frontend redesign beyond small retrieval/status visibility if useful.

## Current Baseline

The repo already has the right shape for this:

- `app/prebuild_feedback.py` contains regeneration, ratings, and a lexical retrieval prototype.
- `VectorCorpusDocument` stores corpus text, metadata, and token vectors in Postgres.
- `QuestionGeneratedVersion` stores `retrieval_context_snapshot`.
- Rating tables exist for themes and generated question versions.
- Celery and Redis are now available for async jobs.

Phase 3 should evolve this into a real vector retrieval system rather than replacing the product flow.

## Architecture

### Source of Truth

Postgres remains canonical. Qdrant should be treated as a derived index that can be rebuilt.

### Retrieval Index

Qdrant stores embeddings for generated question versions. Each point should represent one reusable question example.

Suggested point ID:

- `question_generated_version.id`

Suggested payload:

- `application_id`
- `focus_area_id`
- `thread_id`
- `question_role`
- `theme_title`
- `theme_direction`
- `question_text`
- `why_this`
- `rating_avg`
- `rating_count`
- `generation_source`
- `created_at`

Theme-level documents can be added later, but the first useful system should index question versions only.

### Embeddings

Use the path of least resistance first:

- Add `qdrant-client[fastembed]` or `qdrant-client` plus `fastembed`.
- Use one fixed local embedding model.
- Store the embedding model name/version in Qdrant payloads and retrieval snapshots.

This avoids adding another paid dependency while still making the RAG system defensible.

### Async Indexing

Add Celery tasks for indexing:

- `index_question_version_task(version_id)`
- `backfill_question_vectors_task(limit=None)`

Trigger indexing after:

- Initial/generated question versions are created.
- A question is regenerated.
- Ratings are added or updated.

Rating changes should update payload metadata even if the vector itself does not need to change.

### Retrieval Service

Create a dedicated retrieval boundary, for example:

- `app/rag/question_retrieval.py`

Primary function:

- `retrieve_question_regeneration_examples(...)`

Query text should be built from:

- Current question text
- Question role
- Theme title
- Theme direction
- Focus area context

Retrieval filters should:

- Exclude the current application.
- Prefer same focus area when available.
- Prefer same question role when available.
- Prefer highly rated examples.
- Allow unrated examples with lower priority.

Return the top 3 examples to keep prompt behavior controlled.

### Fallback

If Qdrant is disabled, unavailable, or returns no useful matches:

- Fall back to the existing lexical retrieval path.
- Record the fallback reason in the retrieval snapshot.

This lets us ship the architecture safely without making Qdrant a single point of failure.

## Prompt Integration

Only the regeneration prompt should change in Phase 3A.

The prompt should receive retrieved examples as quality guidance, not as content to copy. It should explicitly preserve:

- The current theme.
- The question role.
- The evidence target.
- The application-specific grounding.
- The existing output schema.

Suggested instruction:

> Use the retrieved examples to understand what strong questions look like. Do not copy them. Preserve the applicant-specific evidence target and generate a fresh question for this application.

## Retrieval Snapshot

Each regenerated `QuestionGeneratedVersion` should persist:

- `strategy_version`
- `provider`
- `collection`
- `embedding_model`
- `query_text`
- Applied filters
- Returned point IDs
- Scores
- Payload summaries
- Fallback reason, if any

This matters for product debugging, demos, and resume credibility because the RAG path becomes inspectable.

## Testing Plan

### Unit Tests

Use a fake Qdrant client.

Cover:

- Indexing builds the correct payload.
- Retrieval excludes the current application.
- High-rated examples rank above low-rated examples.
- Retrieval falls back when Qdrant errors.
- Regeneration persists a retrieval snapshot.

### Integration Tests

Use Docker with Postgres, Redis, Celery, and Qdrant.

Cover:

- Upload PDF.
- Process through Celery.
- Generate initial questions.
- Rate one question/version highly.
- Index the version.
- Regenerate another question.
- Confirm the regenerated version has a Qdrant retrieval snapshot.

### Live Demo Test

Use the existing `demo-pdfs` flow:

- Upload at least two demo applications.
- Generate questions for both.
- Rate a strong question from one application.
- Regenerate a related question in the other application.
- Verify the retrieved examples came from Qdrant and did not include the same application.

## Exit Criteria

Phase 3A is complete when:

- Regeneration uses Qdrant retrieval when configured.
- The system falls back cleanly when Qdrant is unavailable.
- Retrieval snapshots are persisted on regenerated versions.
- Rating updates affect retrieval ranking or payload metadata.
- Backfill and single-version indexing tasks exist.
- The live demo upload and regeneration flow passes with Qdrant enabled.

## Phase 3B: Full Generation RAG

After Phase 3A is stable, reuse the same retrieval service for initial generation.

The least disruptive path:

- Keep the existing full-generation pipeline.
- Retrieve examples per theme or focus area before prompt construction.
- Add a compact `question_quality_examples` block to the generation prompt.
- Preserve all existing output schemas.
- Keep the retrieved examples as style and coverage guidance, not as required content.

This turns RAG from a regeneration-only feature into a generation quality layer without rewriting the product.

## Suggested Build Order

1. Add Qdrant config and client wrapper.
2. Add embedding service.
3. Add Qdrant collection setup/readiness checks.
4. Add question-version indexing task.
5. Add backfill indexing task.
6. Add retrieval service with Qdrant plus lexical fallback.
7. Wire retrieval into regeneration.
8. Persist richer retrieval snapshots.
9. Add fake-client unit tests.
10. Add Docker Qdrant integration path.
11. Run live demo regeneration test.
12. Decide whether to proceed to full-generation RAG.
