# AWS Deployment And Teardown Evidence

This file preserves a non-secret record that the AG Interview Standardiser backend was deployed on AWS before the infrastructure was shut down.

## Snapshot

- Evidence captured: 2026-08-06, Asia/Calcutta
- AWS account used: `639163294145`
- AWS IAM principal used for operations: `arn:aws:iam::639163294145:user/agis_admin`
- Region: `ap-south-1`
- Git commit deployed: `2a6d914 Add LangGraph question generation workflow`
- Frontend production URL used during deployment: `https://interview-standardiser.vercel.app`
- Backend public ALB URL used during deployment: `http://agis-prod-api-1022908868.ap-south-1.elb.amazonaws.com`

## AWS Services Provisioned

Terraform-managed AWS resources included:

- Amazon ECS Fargate cluster: `agis-prod-cluster`
- ECS API service: `agis-prod-api`
- ECS Celery worker service: `agis-prod-worker`
- ECS task definitions for API, worker, and migration tasks
- Amazon ECR repository: `639163294145.dkr.ecr.ap-south-1.amazonaws.com/agis-prod-backend`
- Amazon RDS PostgreSQL instance: `agis-prod-postgres`
- Amazon ElastiCache Redis replication group: `agis-prod-redis`
- Amazon S3 asset bucket: `agis-prod-assets-639163294145-ap-south-1`
- Application Load Balancer: `agis-prod-api-1022908868.ap-south-1.elb.amazonaws.com`
- AWS Secrets Manager runtime secret: `agis-prod/app-env`
- CloudWatch log groups for API, worker, and migration tasks
- IAM execution/application task roles with scoped S3 access
- VPC, public subnets, route table, internet gateway, and security groups

## Final Deployment Verification

The final deployed backend image was pushed to ECR with:

- Image tags: `2a6d914`, `latest`
- Image digest: `sha256:961a7648d54191d4a9551c43c3777cd107fa290b3380e9f30f37fc36041e4467`
- Pushed at: `2026-07-20T02:16:24+05:30`

Before shutdown, ECS services had already been scaled down:

- `agis-prod-api`: desired `0`, running `0`
- `agis-prod-worker`: desired `0`, running `0`

The live deployment was previously verified through the Vercel API proxy readiness endpoint:

- `database`: ok
- `coordination`: ok, Redis backend
- `storage`: ok, S3 backend
- `llm_config`: ok, live calls enabled
- `task_queue`: ok, Redis-backed Celery queues
- `observability`: ok, OpenTelemetry and Langfuse configured

## CloudTrail Evidence

AWS CloudTrail Event History captured management events for this deployment, including ECS service updates and ECR image lookups. Example events visible on 2026-08-06:

- `UpdateService` on `ecs.amazonaws.com` for `agis-prod-api`
- `UpdateService` on `ecs.amazonaws.com` for `agis-prod-worker`
- `DescribeServices` on `ecs.amazonaws.com`
- `DescribeImages` on `ecr.amazonaws.com`
- `ConsoleLogin`, `CheckMfa`, and OAuth events for the AWS CLI session

CloudTrail Event History is useful as short-term AWS-side proof. AWS documents that Event History is available by default and provides a searchable, downloadable record of recent management events for 90 days.

## Other Durable Proof Sources

Even after teardown, proof remains in:

- Git history, including commits for AWS Terraform, AWS deployment, Vercel wiring, and LangGraph rollout.
- Terraform files under `infra/aws`, which define the deployed architecture as infrastructure-as-code.
- This evidence file.
- AWS Billing / Cost Explorer history, which can show historical service usage and cost.
- Any screenshots or downloaded CloudTrail event history captured before the 90-day Event History window expires.

## Teardown Intent

The purpose of teardown is cost control after a successful CV/demo deployment. The teardown should remove or stop cost-bearing infrastructure while preserving non-secret evidence of the implementation and deployment.
