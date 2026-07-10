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
