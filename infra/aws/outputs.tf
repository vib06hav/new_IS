output "aws_region" {
  description = "AWS region used by this stack."
  value       = var.aws_region
}

output "backend_ecr_repository_url" {
  description = "ECR repository URL for the backend image."
  value       = aws_ecr_repository.backend.repository_url
}

output "assets_bucket_name" {
  description = "S3 bucket name for application assets."
  value       = aws_s3_bucket.assets.bucket
}

output "assets_s3_prefix" {
  description = "S3 prefix used by the application."
  value       = local.normalized_s3_prefix
}

output "ecs_task_execution_role_arn" {
  description = "IAM role used by ECS to pull images and write logs."
  value       = aws_iam_role.ecs_task_execution.arn
}

output "ecs_app_task_role_arn" {
  description = "IAM role used by application containers."
  value       = aws_iam_role.ecs_app_task.arn
}
