# AWS Infrastructure

This directory contains Terraform for deploying AG Interview Standardiser on AWS.

## Learning Model

Terraform is infrastructure-as-code. Instead of clicking AWS console buttons manually, we describe cloud resources in `.tf` files. Terraform then compares the files to real AWS and creates/updates resources.

Important Terraform commands:

```powershell
terraform init
terraform fmt
terraform validate
terraform plan
terraform apply
```

What they mean:

- `terraform init` downloads the AWS provider plugin.
- `terraform fmt` formats `.tf` files.
- `terraform validate` checks syntax and provider-level configuration.
- `terraform plan` previews what AWS resources would be created.
- `terraform apply` actually creates or changes AWS resources.

Do not run `terraform apply` until the plan has been reviewed.

## Current Scope

The first foundation stack creates low-risk supporting resources:

- ECR repository for backend Docker images.
- S3 bucket for uploaded PDFs, profile assets, and generated exports.
- CloudWatch log groups for API, worker, and migration tasks.
- ECS task execution role.
- ECS application task role with scoped S3 permissions.
- VPC, public subnets, route table, and security groups.
- ECS cluster and task definitions for API, worker, and migration.

This does not yet create running ECS services, RDS, Redis, load balancers, NAT gateways, or public app ingress.

Task definitions are recipes. They do not run containers or bill Fargate until an ECS task/service is started.

## Files

- `versions.tf` pins Terraform/provider versions.
- `variables.tf` defines configurable inputs.
- `locals.tf` centralizes naming and tags.
- `ecr.tf` creates the container registry.
- `s3.tf` creates object storage.
- `logs.tf` creates log groups.
- `iam.tf` creates ECS IAM roles and policies.
- `network.tf` creates the VPC/subnets/security groups.
- `ecs.tf` creates the ECS cluster and task definitions.
- `outputs.tf` prints useful resource names/ARNs after apply.
- `terraform.tfvars.example` shows safe example values.

## Best-Practice Defaults

- S3 public access is blocked.
- S3 server-side encryption is enabled.
- ECR image scanning is enabled.
- CloudWatch log retention is finite.
- ECS app role gets access only to the configured S3 bucket/prefix.
- ECS Container Insights is disabled by default to avoid extra observability cost.
- No NAT Gateway is created in the foundation layer.
- No ECS service is created in the foundation layer, so no Fargate compute runs yet.
- Common tags are applied for ownership and cost tracking.

## Before First Apply

1. Configure AWS CLI.
2. Confirm account identity:

```powershell
aws sts get-caller-identity
```

3. Create a private `terraform.tfvars` from the example.
4. Run:

```powershell
terraform init
terraform fmt
terraform validate
terraform plan
```

5. Review the plan before applying.
