# AWS Deployment Plan

## Purpose

This plan turns the current Docker-based AG Interview Standardiser stack into a managed AWS deployment while keeping the process learnable. Each AWS service should have a clear reason to exist, a local Docker equivalent, and a cost/security boundary.

The goal is a production-style cloud project, not just "the app is online."

## Current Step: Phase 0

Phase 0 is about preparation before creating AWS resources.

Why this matters:

- AWS has many services, and it is easy to create expensive infrastructure by accident.
- Infrastructure decisions become easier when every AWS resource maps to an existing local service.
- A clean repo checkpoint lets us safely experiment and roll back.
- Security and cost controls should exist before the first deployment, not after a surprise bill.

Phase 0 exit criteria:

- AWS readiness changes are committed.
- This deployment plan exists.
- AWS account has MFA enabled.
- AWS Budget alert is configured.
- AWS CLI is installed locally.
- Terraform is installed locally.
- An AWS region is selected.
- No long-lived AWS access keys are added to app `.env` files.

## Local-to-AWS Mapping

| Local component | AWS service | Why |
| --- | --- | --- |
| Backend API container | ECS Fargate service | Runs the FastAPI container without managing EC2 servers. |
| Celery worker container | ECS Fargate service | Runs background jobs separately from web requests. |
| Postgres container | RDS PostgreSQL | Managed relational database with backups and operational tooling. |
| Redis container | ElastiCache Redis | Managed queue/cache backend for Celery and coordination. |
| MinIO container | S3 | Durable object storage for PDFs, profile assets, and exports. |
| Docker image build | ECR | Private AWS container registry used by ECS. |
| `.env` secrets | Secrets Manager or SSM Parameter Store | Keeps secrets out of source code and task definitions. |
| Docker logs | CloudWatch Logs | Centralized service logs for API, worker, and migration tasks. |
| Local network | VPC and security groups | Controls what can talk to what. |
| Manual migration command | ECS one-off migration task | Runs Alembic safely against RDS before/after deployments. |
| Browser API URL | Application Load Balancer | Public HTTPS entry point for the backend API. |

## Recommended First Architecture

Use a cost-safe but credible ECS Fargate deployment:

- One ECR repository for the backend image.
- One S3 bucket for application assets.
- One ECS cluster.
- One API ECS service behind an Application Load Balancer.
- One worker ECS service with no public ingress.
- One migration ECS task definition.
- One RDS PostgreSQL instance.
- One Redis backend.
- CloudWatch log groups for API, worker, and migration.
- One ECS task execution role for pulling images and writing logs.
- One ECS app task role for S3 access.

Keep Qdrant Cloud, Langfuse Cloud, Grafana Cloud, WorkOS, and the LLM provider external.

## Region Choice

Default recommendation: `ap-south-1` because it is closest to India.

Tradeoff:

- `ap-south-1` should reduce latency for you and likely demo users in India.
- Some free-tier or new-service availability can differ by region.
- If a service is unavailable or unexpectedly expensive in `ap-south-1`, use `us-east-1` as the fallback.

Do not spread resources across multiple regions for the first deployment. Multi-region looks fancy but increases complexity and cost.

## Cost Guardrails

Do these before creating application infrastructure:

- Enable MFA on the AWS root account.
- Create an AWS Budget alert for a small monthly threshold.
- Enable billing alerts.
- Prefer free-tier-eligible RDS where available.
- Set CloudWatch log retention instead of infinite retention.
- Add S3 lifecycle rules for old objects later.
- Avoid NAT Gateway in the first version unless there is a concrete need.

Why avoid NAT Gateway initially:

- NAT Gateway is billed hourly.
- It also charges for data processed.
- A small learning project can accidentally spend more on NAT than on the app itself.

First version networking can be simpler:

- API tasks can run with public ingress through an ALB.
- Worker tasks should not be public.
- RDS and Redis should only allow traffic from ECS security groups.
- If we need private subnets and outbound internet later, add NAT intentionally as a hardening phase.

## Security Guardrails

Use IAM roles instead of static AWS keys wherever possible:

- ECS task execution role lets ECS pull from ECR and write CloudWatch logs.
- ECS application task role lets the app access only the required S3 bucket/prefix.
- The app should not receive AWS access keys in `.env`.
- Secrets should come from Secrets Manager or SSM.
- Security groups should be narrow:
  - ALB accepts public HTTP/HTTPS.
  - API accepts traffic only from ALB.
  - Worker accepts no public traffic.
  - RDS accepts traffic only from API/worker tasks.
  - Redis accepts traffic only from API/worker tasks.

## Infrastructure-as-Code Strategy

Use Terraform under `infra/aws`.

Start with a single starter stack before splitting into modules. This is easier to learn because the full system is visible in one place.

Suggested structure:

```text
infra/aws/
  README.md
  versions.tf
  variables.tf
  outputs.tf
  main.tf
  locals.tf
  ecr.tf
  s3.tf
  iam.tf
  logs.tf
  network.tf
  rds.tf
  redis.tf
  ecs.tf
  alb.tf
  terraform.tfvars.example
```

Do not commit real `terraform.tfvars`.

## Implementation Phases

### Phase 0: Preparation

Status: in progress.

Tasks:

- Commit AWS readiness changes.
- Add this deployment plan.
- Confirm AWS account access.
- Set budget alert.
- Install AWS CLI.
- Install Terraform.
- Select region.

### Phase 1: Foundation Infrastructure

Goal: create safe base resources that do not run the app yet.

Resources:

- ECR repository.
- S3 bucket.
- CloudWatch log groups.
- IAM roles and policies.
- Basic VPC/security group layout.

Learning focus:

- What Terraform state is.
- What ECR stores.
- Why IAM roles are better than access keys.
- How S3 bucket permissions work.

### Phase 2: Managed Data Services

Goal: create the app's managed data layer.

Resources:

- RDS PostgreSQL.
- Redis backend.
- Security group rules for ECS-to-database access.

Learning focus:

- RDS connection strings.
- Security groups as network firewalls.
- Why databases should not be public by default.
- Redis as Celery's queue backend.

### Phase 3: Container Deployment

Goal: run the backend on AWS.

Resources:

- ECS cluster.
- API task definition.
- Worker task definition.
- Migration task definition.
- API ECS service.
- Worker ECS service.
- Application Load Balancer.

Learning focus:

- Difference between image, task definition, task, and service.
- Why API and worker are separate services.
- How health checks keep services alive.
- How environment variables and secrets reach containers.

### Phase 4: CI/CD

Goal: deploy from GitHub instead of from a laptop.

Pipeline:

- Build backend image.
- Push image to ECR.
- Run migrations.
- Deploy API service.
- Deploy worker service.

Learning focus:

- GitHub Actions OIDC or AWS credentials.
- Immutable Docker image tags.
- Safe migration timing.
- Deployment rollback basics.

### Phase 5: Production Hardening

Goal: make the deployment safer and easier to operate.

Tasks:

- Add custom domain and HTTPS.
- Configure autoscaling.
- Add log retention.
- Add CloudWatch alarms.
- Configure RDS backups.
- Add S3 lifecycle policies.
- Tighten IAM policies.
- Review cost report.

## What We Should Not Do Yet

Avoid these in the first AWS pass:

- Multi-region deployment.
- Kubernetes/EKS.
- NAT Gateway unless needed.
- Complex blue/green deployment.
- Full private-subnet architecture before the simple version works.
- Replacing Qdrant Cloud with self-hosted vector DB.
- Moving frontend and backend at the same time if it slows learning.

## Immediate Next Commands To Prepare Locally

These are not run automatically because they depend on your local machine and AWS login state:

```powershell
aws --version
terraform -version
aws sts get-caller-identity
```

What they mean:

- `aws --version` checks whether AWS CLI is installed.
- `terraform -version` checks whether Terraform is installed.
- `aws sts get-caller-identity` verifies which AWS account/user your terminal is authenticated as.

## First Manual AWS Console Tasks

Do these before we run Terraform:

1. Enable MFA on the root account.
2. Create a budget alert.
3. Confirm the region to use.
4. Create or choose an IAM user/role for Terraform.
5. Configure AWS CLI locally.

## Success Definition

The AWS migration is successful when:

- The backend API runs on ECS Fargate.
- The Celery worker runs separately on ECS Fargate.
- Uploads go to S3.
- Postgres data lives in RDS.
- Celery uses Redis.
- Migrations can run as a repeatable ECS task.
- Logs are visible in CloudWatch.
- Qdrant, Langfuse, and Grafana still work.
- The frontend can call the AWS API successfully.
- No app secrets are committed to Git.
- Costs are bounded by budget alerts and intentionally selected resources.
