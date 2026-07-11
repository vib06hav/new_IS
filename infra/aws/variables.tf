variable "project_name" {
  description = "Short project name used in AWS resource names."
  type        = string
  default     = "agis"
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
  default     = "prod"
}

variable "aws_region" {
  description = "AWS region for all resources in this stack."
  type        = string
  default     = "ap-south-1"
}

variable "owner" {
  description = "Owner tag for cost and resource tracking."
  type        = string
  default     = "vibha"
}

variable "s3_bucket_name" {
  description = "Globally unique S3 bucket name for application assets. Leave empty to derive one from account/region."
  type        = string
  default     = ""
}

variable "s3_prefix" {
  description = "Application object prefix inside the S3 bucket."
  type        = string
  default     = "prod"
}

variable "cloudwatch_log_retention_days" {
  description = "Number of days to retain CloudWatch logs."
  type        = number
  default     = 14
}

variable "vpc_cidr" {
  description = "CIDR block for the application VPC."
  type        = string
  default     = "10.40.0.0/20"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets. Use at least two for future ECS/ALB high availability."
  type        = list(string)
  default     = ["10.40.0.0/24", "10.40.1.0/24"]
}

variable "backend_image_tag" {
  description = "Backend image tag to use in ECS task definitions."
  type        = string
  default     = "latest"
}

variable "api_container_port" {
  description = "Port exposed by the FastAPI container."
  type        = number
  default     = 8000
}

variable "api_task_cpu" {
  description = "API task CPU units for future Fargate runs. This does not bill until a task/service runs."
  type        = number
  default     = 512
}

variable "api_task_memory" {
  description = "API task memory in MiB for future Fargate runs. This does not bill until a task/service runs."
  type        = number
  default     = 1024
}

variable "worker_task_cpu" {
  description = "Worker task CPU units for future Fargate runs. This does not bill until a task/service runs."
  type        = number
  default     = 1024
}

variable "worker_task_memory" {
  description = "Worker task memory in MiB for future Fargate runs. This does not bill until a task/service runs."
  type        = number
  default     = 2048
}

variable "api_desired_count" {
  description = "Number of API tasks to run behind the load balancer."
  type        = number
  default     = 1
}

variable "worker_desired_count" {
  description = "Number of Celery worker tasks to run."
  type        = number
  default     = 1
}

variable "frontend_public_url" {
  description = "Public browser-facing frontend URL. Set to the Vercel/custom-domain URL when the frontend is deployed."
  type        = string
  default     = ""
}

variable "db_name" {
  description = "PostgreSQL database name for the application."
  type        = string
  default     = "agis"
}

variable "db_username" {
  description = "PostgreSQL admin username for the application database."
  type        = string
  default     = "agis_admin"
}

variable "rds_instance_class" {
  description = "RDS instance class. Keep tiny for the short-lived CV deployment."
  type        = string
  default     = "db.t4g.micro"
}

variable "redis_node_type" {
  description = "ElastiCache Redis OSS node type. Keep tiny for the short-lived CV deployment."
  type        = string
  default     = "cache.t4g.micro"
}

variable "app_secret_overrides" {
  description = "Sensitive app env overrides loaded into AWS Secrets Manager, usually generated locally from .env."
  type        = map(string)
  sensitive   = true
  default     = {}
}
