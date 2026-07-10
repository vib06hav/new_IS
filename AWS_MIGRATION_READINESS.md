# AWS Migration Readiness

## Objective

Move the current Docker-based AG Interview Standardiser deployment to managed AWS infrastructure while preserving the existing product behavior: PDF upload, async parsing, question generation, question regeneration, final report creation, Qdrant-backed RAG, Langfuse tracing, and Grafana/OpenTelemetry export.

The migration goal is not just hosting. The target is a credible cloud-native deployment story with managed compute, database, cache/queue, object storage, secrets, logs, CI/CD, and infrastructure-as-code.

## Current Local/Production Shape

The application is already split into cloud-friendly service boundaries:

- Backend API runs as a containerized FastAPI service.
- Background work runs through Celery queues backed by Redis.
- Postgres stores users, applications, processing jobs, generated questions, feedback, final reports, and RAG corpus metadata.
- Object storage stores uploaded source PDFs, profile assets, and final report exports.
- Qdrant Cloud stores vector embeddings for question-version retrieval.
- Langfuse records LLM workflow traces.
- Grafana receives OpenTelemetry traces/metrics through OTLP.
- Alembic manages schema migrations.
- GitHub Actions already performs backend tests and Docker image builds.

## AWS Target Architecture

Recommended first AWS architecture:

- Amazon ECR for backend container images.
- Amazon ECS Fargate for the API service.
- A separate ECS Fargate service for the Celery worker.
- An ECS one-off task for Alembic migrations.
- Amazon RDS PostgreSQL for the relational database.
- Amazon ElastiCache Redis for Celery broker/result backend and distributed coordination.
- Amazon S3 for uploaded PDFs, generated exports, and application assets.
- AWS Secrets Manager or SSM Parameter Store for runtime secrets.
- CloudWatch Logs for API, worker, and migration task logs.
- Application Load Balancer for public API ingress.
- Qdrant Cloud remains external.
- Langfuse Cloud remains external.
- Grafana Cloud remains external.
- Frontend can remain on Vercel initially, then move to Amplify later if desired.

## What Is Already Ready

The backend image is suitable for ECS:

- The production Dockerfile builds a non-root Python container.
- The same image can run API, worker, or migration commands.
- The API exposes `/health` and `/readiness`.
- The app is configured through environment variables.
- Database URL, Redis URL, Qdrant URL, LLM keys, Langfuse keys, and OTLP settings are env-driven.
- Alembic can run as a standalone command.
- Celery already has explicit queues for processing, generation, maintenance, and default tasks.
- Request logging, request IDs, security headers, CORS, CSRF, and trusted host controls already exist.
- Production mode disables bearer-token auth.

## Readiness Changes Added

This readiness pass added first-class AWS storage support:

- `STORAGE_BACKEND=s3` is now a supported configuration mode.
- S3 bucket, region, optional prefix, and optional endpoint are validated through settings.
- The storage abstraction now has an S3 implementation matching the existing local/MinIO behavior.
- API readiness now recognizes S3 as a configured storage backend.
- The production env example includes AWS S3 variables.

This pass also aligned production worker execution:

- The production worker command now runs a real Celery worker with the expected queues.
- This matches the ECS deployment model where API and worker are separate services using the same image.

## Remaining Pre-Deployment Work

Before deploying to AWS, the repo still needs infrastructure and deployment assets:

- Terraform for ECR, ECS, RDS, Redis, S3, IAM, CloudWatch, security groups, VPC/subnets, and load balancer.
- GitHub Actions workflow for AWS image build, ECR push, and ECS deployment.
- A safe migration task pattern for running `alembic upgrade head`.
- Production secrets wiring through Secrets Manager or SSM.
- Final CORS/trusted-host values once AWS and frontend URLs are known.
- Cost guardrails and AWS budget alerts.

## Suggested AWS Learning Path

Use this migration as a learning project in this order:

1. Create an AWS account, IAM admin user, and budget alert.
2. Learn ECR by building and pushing the existing backend image.
3. Learn S3 by creating the asset bucket and testing `STORAGE_BACKEND=s3`.
4. Learn RDS by provisioning Postgres and running Alembic migrations.
5. Learn Redis/ElastiCache by connecting Celery to managed Redis.
6. Learn ECS Fargate by deploying the API service.
7. Learn ECS service separation by deploying the worker service.
8. Learn ALB by exposing only the API publicly.
9. Learn Secrets Manager/SSM by removing plain env secrets from task definitions.
10. Learn CI/CD by automating build, push, migration, and deploy from GitHub Actions.

## Cost-Safe First Deployment

For the first AWS pass, keep the architecture small:

- One small API Fargate service.
- One small worker Fargate service.
- One free-tier-eligible or smallest practical RDS Postgres instance.
- One small Redis option, preferably ElastiCache if credits cover it.
- One S3 bucket with lifecycle policy.
- Existing Qdrant, Langfuse, and Grafana Cloud integrations.

Avoid NAT gateways in the first version unless needed. NAT gateways can become a surprise cost. A simple public-subnet ECS setup with strict security groups is acceptable for a learning deployment, then private subnets/NAT can be added as a hardening phase.

## Resume-Relevant Technical Depth

The AWS migration will demonstrate:

- Containerized multi-service backend deployment.
- Async queue architecture with separate web and worker services.
- Managed relational database integration.
- Managed Redis-backed distributed job processing.
- S3 object storage abstraction.
- Infrastructure-as-code with Terraform.
- Cloud-native secret management.
- Production observability through CloudWatch, OpenTelemetry, Grafana, and Langfuse.
- Safe database migrations in deployment workflows.
- Security group/IAM boundary design.
- Cloud cost and reliability tradeoff awareness.

## Recommended Next Phase

The next implementation phase should create `infra/aws` with Terraform modules or a single starter stack for:

- ECR repository.
- S3 bucket.
- ECS cluster.
- CloudWatch log groups.
- IAM task execution role and application task role.
- RDS Postgres.
- Redis option.
- API task definition and service.
- Worker task definition and service.
- Migration task definition.
- Application Load Balancer.

After Terraform exists, do one manual deployment using AWS CLI commands so the moving parts are understandable before adding GitHub Actions automation.
