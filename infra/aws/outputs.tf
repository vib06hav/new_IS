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

output "vpc_id" {
  description = "Application VPC ID."
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "Public subnet IDs prepared for future ECS and load balancer resources."
  value       = aws_subnet.public[*].id
}

output "api_security_group_id" {
  description = "Security group ID for future API tasks."
  value       = aws_security_group.api.id
}

output "worker_security_group_id" {
  description = "Security group ID for future worker tasks."
  value       = aws_security_group.worker.id
}

output "database_security_group_id" {
  description = "Security group ID for future RDS PostgreSQL."
  value       = aws_security_group.database.id
}

output "redis_security_group_id" {
  description = "Security group ID for future Redis."
  value       = aws_security_group.redis.id
}

output "alb_dns_name" {
  description = "Public DNS name for the API application load balancer."
  value       = aws_lb.api.dns_name
}

output "api_url" {
  description = "HTTP base URL for the deployed API."
  value       = "http://${aws_lb.api.dns_name}"
}

output "ecs_cluster_name" {
  description = "ECS cluster name."
  value       = aws_ecs_cluster.main.name
}

output "api_task_definition_arn" {
  description = "API ECS task definition ARN."
  value       = aws_ecs_task_definition.api.arn
}

output "worker_task_definition_arn" {
  description = "Worker ECS task definition ARN."
  value       = aws_ecs_task_definition.worker.arn
}

output "migration_task_definition_arn" {
  description = "Migration ECS task definition ARN."
  value       = aws_ecs_task_definition.migration.arn
}

output "api_service_name" {
  description = "ECS service name running the API."
  value       = aws_ecs_service.api.name
}

output "worker_service_name" {
  description = "ECS service name running the Celery worker."
  value       = aws_ecs_service.worker.name
}

output "postgres_endpoint" {
  description = "Private RDS PostgreSQL endpoint."
  value       = aws_db_instance.postgres.address
}

output "redis_endpoint" {
  description = "Private ElastiCache Redis endpoint."
  value       = aws_elasticache_replication_group.redis.primary_endpoint_address
}

output "app_env_secret_arn" {
  description = "Secrets Manager ARN used by ECS tasks for runtime environment variables."
  value       = aws_secretsmanager_secret.app_env.arn
}
